"""qa_events — the one writer and reader of <workspace>/05-metrics/events.jsonl.

Every metric event goes through append(): it fills ts and project, validates the line
against schemas/metric-event.schema.json and appends it under a lock. Nothing else writes
the file, and nothing writes it from memory: callers pass numbers read from a file (a
Playwright report, a gate file, a transcript) and name that file in `source`.

  find_root(start)           workspace root (a .qa-project above start) or None
  append(root, event)        validated, appended event dict; ValueError if invalid
  read(root)                 (events, number of unreadable lines)
  hashes(root, paths)        {workspace-relative path: sha256} of the files that exist
  transcript_usage(path)     tokens, model, duration and cost of a Claude Code transcript
  parse_session(path)        an exploratory session sheet: id, start, duration, time split
"""
import datetime, fcntl, hashlib, json, os, re
from pathlib import Path

import qa_schema

EVENTS = Path("05-metrics") / "events.jsonl"
TOOLKIT = Path(os.path.realpath(__file__)).parent.parent
PRICES = TOOLKIT / "hooks" / "prices.json"


def find_root(start):
    d = Path(start or os.getcwd()).resolve()
    for p in [d, *d.parents]:
        if (p / ".qa-project").exists():
            return p
    return None


def project_of(root):
    lines = (Path(root) / ".qa-project").read_text(encoding="utf-8").split()
    return lines[0] if lines else Path(root).name


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes(root, paths):
    out = {}
    for p in paths or []:
        f = Path(root) / p
        if f.is_file():
            out[str(f.relative_to(root)) if f.is_absolute() and str(f).startswith(str(root)) else str(p)] = sha256(f)
    return out


def append(root, event):
    root = Path(root)
    ev = {"ts": now(), "project": project_of(root)}
    ev.update({k: v for k, v in event.items() if v is not None})
    errs = qa_schema.validate(ev, qa_schema.load("metric-event"))
    if errs:
        raise ValueError("; ".join(errs[:5]))
    path = root / EVENTS
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(json.dumps(ev, ensure_ascii=False, sort_keys=False) + "\n")
        fcntl.flock(fh, fcntl.LOCK_UN)
    return ev


def read(root):
    path = Path(root) / EVENTS
    events, bad = [], 0
    if not path.exists():
        return events, bad
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                bad += 1
                continue
            events.append(ev) if isinstance(ev, dict) else None
    # A correction replaces the line it names: same ts, same kind, and the same runId / suite / id where
    # the correction has one. One agent stop writes several stage events in the same instant, so when
    # several lines match, only those of the correction's own stage are replaced; a correction that
    # changes a line's stage matches no line of its stage and replaces what it names. A line never
    # corrects itself.
    def matches(c, ev):
        return ev is not c and ev.get("ts") == c["corrects"] != c.get("ts") and ev.get("kind") == c.get("kind") and \
            all(ev.get(k) == c.get(k) for k in ("runId", "suite", "id") if c.get(k))
    replaced = set()
    for c in (ev for ev in events if ev.get("corrects")):
        hit = [i for i, ev in enumerate(events) if matches(c, ev)]
        same = [i for i in hit if events[i].get("stage") == c.get("stage")]
        replaced.update(same or hit)
    kept = [ev for i, ev in enumerate(events) if i not in replaced]
    # several corrections of the same line: the last one stands
    key = lambda c: (c["corrects"], c.get("kind"), *(c.get(k) for k in ("runId", "stage", "suite", "id")))
    last = {key(c): i for i, c in enumerate(kept) if c.get("corrects")}
    return [ev for i, ev in enumerate(kept) if not ev.get("corrects") or last[key(ev)] == i], bad


def _ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


IDLE_GAP_S = 900   # a longer gap between transcript lines is a pause (rate limit, waiting), not work


def transcript_usage(path, until=None):
    """Sum the usage of every assistant message in a Claude Code transcript (JSONL), up to
    `until` (a datetime) if given. A streamed message appears on several lines with the same
    id: the last one counts. durationS is active time: gaps over IDLE_GAP_S are left out."""
    if not path or not os.path.exists(path):
        return None
    per_msg, prev, active = {}, None, 0.0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            t = _ts(rec.get("timestamp"))
            if t and until and t > until:
                break
            if t:
                if prev and 0 < (t - prev).total_seconds() <= IDLE_GAP_S:
                    active += (t - prev).total_seconds()
                prev = t if not prev or t > prev else prev
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            if rec.get("type") == "assistant" and isinstance(msg.get("usage"), dict) \
                    and not str(msg.get("model") or "").startswith("<"):   # <synthetic>: an error notice, no tokens
                per_msg[msg.get("id") or len(per_msg)] = (msg.get("model"), msg["usage"])
    if not per_msg:
        return None
    tokens = {"in": 0, "out": 0, "cacheRead": 0, "cacheWrite": 0}
    cost, priced, models = 0.0, True, {}
    prices = json.loads(PRICES.read_text()).get("models", {}) if PRICES.exists() else {}
    for model, u in per_msg.values():
        n = lambda k: u.get(k) if isinstance(u.get(k), int) else 0
        cw = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
        w1h = cw.get("ephemeral_1h_input_tokens") or 0
        part = {"in": n("input_tokens"), "out": n("output_tokens"), "cacheRead": n("cache_read_input_tokens"),
                "cacheWrite": n("cache_creation_input_tokens")}
        for k in tokens:
            tokens[k] += part[k]
        models[model] = models.get(model, 0) + part["out"]
        p = prices.get(model or "")
        if not p:
            priced = False
            continue
        cost += (part["in"] * p["in"] + part["out"] * p["out"] + part["cacheRead"] * p["cacheRead"]
                 + (part["cacheWrite"] - w1h) * p["cacheWrite"] + w1h * p.get("cacheWrite1h", 2 * p["in"])) / 1e6
    return {"tokens": tokens, "model": max(models, key=models.get) if models else None,
            "costUsd": round(cost, 4) if priced else None,
            "durationS": round(active, 1) if prev else None}


def parse_session(path):
    text = Path(path).read_text(encoding="utf-8")
    head = re.search(r"^#\s*Session\s+(\S+)\s+—\s+(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})", text, re.M)
    if not head:
        raise ValueError("no '# Session <id> — <date> <start>–<end>' header")
    sid, day, start, end = head.groups()
    t0, t1 = (datetime.datetime.fromisoformat(f"{day}T{x.zfill(5)}") for x in (start, end))
    split = {}
    sec = re.search(r"^##\s*Time split\s*\n(.+)", text, re.M)
    for label, minutes in re.findall(r"([A-Za-z][A-Za-z ]*?)\s+(\d+)\s*m\b", sec.group(1) if sec else ""):
        key = "setup" if "setup" in label.lower() else "bug" if re.search(r"bug|finding|report|writ", label, re.I) else "test"
        split[key] = split.get(key, 0) + int(minutes)
    found = len(re.findall(r"^- F\d+", text, re.M))
    return dict(kind="session", id=sid, ts=t0.isoformat(), durationS=(t1 - t0).total_seconds(),
                split=split or None, counts={"findings": found}, source=str(path))
