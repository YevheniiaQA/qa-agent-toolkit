"""qa_metric_values — one value per metric of metrics/catalog.json, from the qa-metrics result and the files.

  ratio(num, den, note)            {"value": percent or None, "num", "den", "note"}
  catalog_values(root, events, m)  {metric id: {"value", "num", "den", "note", "table", "history", "sources"}}

Every function in VALUES takes a Ctx and returns that dict. `value` is the display string, or None
when there is no data, and then `note` says what would produce it. test_metric_catalog.py checks
that VALUES and metrics/catalog.json name the same metrics.
"""
import csv, datetime, io, json, re, statistics
from collections import Counter, defaultdict
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent.parent
CATALOG = TOOLKIT / "metrics" / "catalog.json"
WINDOW = 10                      # runs per suite for flakiness, runtime and reliability
TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
FIXED = ("fixed", "verified", "closed")


def ratio(num, den, note=""):
    if not den:
        return {"value": None, "num": num, "den": den, "note": note}
    return {"value": round(100.0 * num / den, 1), "num": num, "den": den, "note": note}


def load_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def _load(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def pct(r):
    return None if r["value"] is None else f"{r['value']}%"


def V(value=None, num=None, den=None, note="", columns=None, rows=None, hist_cols=None, hist_rows=None, sources=()):
    return {"value": value, "num": num, "den": den, "note": note,
            "table": {"columns": columns, "rows": rows} if columns and rows else None,
            "history": {"columns": hist_cols, "rows": hist_rows} if hist_cols and hist_rows else None,
            "sources": sorted(set(sources))}


NOTES_UK = {  # notes qa-metrics writes in English for its text report
    "no defect is recorded as found in production": "продакшен-дефектів не записано: це верхня межа, доки їх не заносять "
                                                    "(bugs/<ID>.md | Phase | production | або qa-event defect --phase production)",
    "artefacts changed after the pipeline": "артефакти, змінені після того, як пайплайн їх записав (людиною або "
                                            "інструментом поза пайплайном)",
    "no artefact hashes recorded": "хешів артефактів ще не записано (хук qa-stage-gate)",
    "open questions whose proposed default": "питання, чий запропонований дефолт уже стверджують сценарії, без відповіді інженера",
    "no open question acted on": "жодне питання ще не вплинуло на сценарії",
    "no stage agent has stopped": "жоден агент етапу ще не зупинявся (хук qa-stage-gate)",
    "no `qa-gate": "жодного запуску qa-gate … --write ще не записано",
    "no defect has been fixed yet": "жоден дефект ще не виправлено",
}


def uk(note):
    for en, text in NOTES_UK.items():
        if (note or "").startswith(en):
            return text
    return note or ""


def from_ratio(r, **kw):
    return V(pct(r), r["num"], r["den"], uk(r.get("note")), **kw)


def secs(s):
    if s is None:
        return "—"
    s = float(s)
    if s < 60:
        return f"{s:.1f} с"
    m, s = divmod(int(round(s)), 60)
    return f"{m} хв {s:02d} с" if m < 60 else f"{m // 60} год {m % 60:02d} хв"


def hours(h):
    return f"{h:.1f} год" if h < 48 else f"{h / 24:.1f} дн"


def _dt(s):
    if not s:
        return None
    try:
        d = datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


# ---------------------------------------------------------------- context: files read once

class Ctx:
    def __init__(self, root, events, m):
        self.root, self.events, self.m = Path(root), events, m
        self.defects = [d for d in m["defects"].get("items", []) if d.get("state") != "rejected"]
        self.runs = defaultdict(list)
        for ev in events:
            if ev.get("kind") == "run":
                self.runs[ev["suite"]].append(ev)
        for rs in self.runs.values():
            rs.sort(key=lambda e: e.get("ts") or "")
        self.triage = {}
        for ev in events:                       # the latest classification of each test wins
            if ev.get("kind") == "triage":
                self.triage[ev["test"]] = ev["class"]
        self.trace = self._traceability()
        self.manual = self._manual_cases()
        self.req_ids = set()
        for f in self.root.glob("02-analysis/*/requirements/_index.json"):
            self.req_ids.update(r["id"] for r in (_load(f, {}) or {}).get("requirements", []) if isinstance(r, dict) and r.get("id"))

    def window(self, suite):
        """The last WINDOW full runs of a suite. "Full" is the usual test count (the most common one in the
        last 3×WINDOW runs, the latest on a tie): a run of a few spec files, or a stress run that repeats
        tests, is not compared with the whole suite."""
        recent = self.runs[suite][-3 * WINDOW:]
        if not recent:
            return []
        counts = Counter(r.get("tests") or 0 for r in recent)
        usual = max(counts, key=lambda n: (counts[n], max(i for i, r in enumerate(recent) if (r.get("tests") or 0) == n)))
        return [r for r in recent if abs((r.get("tests") or 0) - usual) <= 0.1 * usual][-WINDOW:]

    def _traceability(self):
        rows = []
        for f in sorted(self.root.glob("03-tests/**/TRACEABILITY.json")):
            if "node_modules" in f.parts:
                continue
            for row in _load(f, []) or []:
                if isinstance(row, dict):
                    m = TOKEN.match(row.get("testTitle") or "")
                    rows.append(dict(row, testId=row.get("scenarioId") or (m.group(0) if m else row.get("testTitle")),
                                     source=str(f.relative_to(self.root))))
        return rows

    def _manual_cases(self):
        out = {}
        for f in sorted(self.root.glob("03-tests/manual/**/TEST_CASES.csv")):
            try:
                text = f.read_text(encoding="utf-8-sig")
            except OSError:
                continue
            for row in csv.DictReader(io.StringIO(text)):
                cid = row.get("Custom_external_id") or row.get("ID") or row.get("Case ID")
                if cid:
                    out.setdefault(cid, set()).update(TOKEN.findall(" ".join(
                        row.get(k) or "" for k in ("References", "Scenario ID", "Refs"))))
        return out

    def last_outcomes(self):
        """test id -> status in the last full run of its suite (only tests that were not as expected)."""
        out = {}
        for suite in self.runs:
            w = self.window(suite)
            if w:
                out.update(w[-1].get("outcomes") or {})
        return out

    def covered(self, token):
        """Is a requirement / AC / test id exercised by an automated test or a manual case?"""
        for row in self.trace:
            if token == row["testId"] or token in (row.get("requirementIds") or []) or token in (row.get("acceptanceCriteria") or []):
                return True
        return any(token == cid or token in refs for cid, refs in self.manual.items())


def md_tables(text, heading):
    """Rows (dicts, lower-case keys) of the first table under `## <heading>`."""
    m = re.search(rf"^##\s+{heading}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    if not m:
        return None
    lines = [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return []
    head = [c.strip().lower() for c in lines[0].strip("|").split("|")]
    return [dict(zip(head, [c.strip() for c in l.strip("|").split("|")])) for l in lines[2:]]


def plan_rows(ctx, heading):
    rows, sources = [], []
    for f in sorted(ctx.root.glob("01-docs/test-plan/*.md")):
        t = md_tables(f.read_text(encoding="utf-8"), heading)
        if t is not None:
            sources.append(str(f.relative_to(ctx.root)))
            rows += t
    return rows, sources


# ---------------------------------------------------------------- defects

def escaped_defects(ctx):
    prod = [d for d in ctx.defects if d.get("phase") == "production"]
    rows = [[d["id"], d.get("severity") or "—", d.get("found") or "—", "так" if d.get("customerImpact") else "—"] for d in prod]
    note = "" if prod else ("продакшен-дефектів не записано: bugs/<ID>.md з | Phase | production | "
                            "або qa-event defect <ID> --phase production")
    return V(str(len(prod)), note=note, columns=["Дефект", "Severity", "Знайдено", "Вплив на клієнтів"], rows=rows,
             sources=[d["source"] for d in prod])


def ddp(ctx):
    d = ctx.m["defects"]
    before = d["ddp"]["num"]
    return from_ratio(d["ddp"], columns=["До релізу", "Після релізу (production)", "Усього валідних"],
                      rows=[[before, (d["ddp"]["den"] or 0) - before, d["ddp"]["den"]]], sources=d["sources"])


def leakage(ctx):
    d = ctx.m["defects"]
    return from_ratio(d["leakage"], sources=d["sources"])


def regression_effectiveness(ctx):
    reg = [d for d in ctx.defects if d.get("regression")]
    caught = [d for d in reg if d.get("phase") != "production"]
    r = ratio(len(caught), len(reg), "" if reg else
              "жоден дефект не позначено як регресію: | Regression | yes | у bugs/<ID>.md або qa-event defect --regression")
    return from_ratio(r, columns=["Дефект", "Фаза", "Severity"],
                      rows=[[d["id"], d.get("phase") or "—", d.get("severity") or "—"] for d in reg])


def test_effectiveness(ctx):
    by_tests = [d for d in ctx.defects if d.get("phase") in ("automation", "manual")]
    r = ratio(len(by_tests), len(ctx.defects), "" if ctx.defects else "дефектів не записано (bugs/*.md)")
    ms = mutation_score(ctx)
    note = r["note"] or (f"поруч mutation score: {ms['value']} ({ms['num']}/{ms['den']})" if ms["value"] else "")
    return V(pct(r), r["num"], r["den"], note, columns=["Знайдено тестами", "Іншим способом", "Усього"],
             rows=[[len(by_tests), len(ctx.defects) - len(by_tests), len(ctx.defects)]] if ctx.defects else None)


def where_caught(ctx):
    c = Counter(d.get("phase") or "невідомо" for d in ctx.defects)
    total = sum(c.values())
    if not total:
        return V(note="дефектів не записано (bugs/*.md)")
    top, n = c.most_common(1)[0]
    return V(f"{top}: {n} з {total}", columns=["Фаза", "Дефектів", "Частка"],
             rows=[[k, v, f"{round(100 * v / total, 1)}%"] for k, v in c.most_common()])


def critical_defect_rate(ctx):
    c = Counter(d.get("severity") or "невідомо" for d in ctx.defects)
    r = ratio(c.get("critical", 0), len(ctx.defects), "" if ctx.defects else "дефектів не записано (bugs/*.md)")
    return from_ratio(r, columns=["Severity", "Дефектів"], rows=[[k, v] for k, v in c.most_common()])


def customer_impacting(ctx):
    prod = [d for d in ctx.defects if d.get("phase") == "production"]
    ci = [d for d in prod if d.get("customerImpact")]
    if not prod:
        return V(note="продакшен-дефектів не записано; вплив позначається | Customer impact | yes | або --customer-impact")
    r = ratio(len(ci), len(prod))
    return V(f"{len(ci)} ({r['value']}%)", len(ci), len(prod), columns=["Дефект", "Severity"],
             rows=[[d["id"], d.get("severity") or "—"] for d in ci])


def incidents(ctx):
    out = {}
    for ev in sorted((e for e in ctx.events if e.get("kind") == "incident"), key=lambda e: e.get("ts") or ""):
        i = out.setdefault(ev["id"], {"id": ev["id"], "opened": None, "resolved": None})
        for k in ("severity", "customerImpact"):
            if ev.get(k) is not None:
                i[k] = ev[k]
        if ev["state"] == "open" and not i["opened"]:
            i["opened"] = ev["ts"]
        if ev["state"] == "resolved" and not i["resolved"]:
            i["resolved"] = ev["ts"]
    return list(out.values())


def production_incidents(ctx):
    inc = incidents(ctx)
    if not inc:
        return V(note="інцидентів не записано: qa-event incident <ID> --state open|resolved --severity S")
    rows = []
    for i in inc:
        a, b = _dt(i["opened"]), _dt(i["resolved"])
        rows.append([i["id"], i.get("severity") or "—", (i["opened"] or "—")[:16], (i["resolved"] or "відкритий")[:16],
                     hours((b - a).total_seconds() / 3600) if a and b else "—", "так" if i.get("customerImpact") else "—"])
    months = Counter((i["opened"] or "")[:7] for i in inc if i["opened"])
    still = sum(1 for i in inc if not i["resolved"])
    return V(str(len(inc)), note=f"відкрито зараз: {still}", columns=["Інцидент", "Severity", "Почався", "Вирішено",
                                                                     "Тривалість", "Вплив на клієнтів"], rows=rows,
             hist_cols=["Місяць", "Інцидентів"], hist_rows=[[k, v] for k, v in sorted(months.items())])


# ---------------------------------------------------------------- automation

def automation_reliability(ctx):
    rows, good, known, unknown = [], 0, 0, 0
    for suite in sorted(ctx.runs):
        g = f = u = 0
        for r in ctx.window(suite):
            bad = {t: s for t, s in (r.get("outcomes") or {}).items() if s in ("unexpected", "flaky")}
            classes = [("flaky" if s == "flaky" else ctx.triage.get(t)) for t, s in bad.items()]
            if not bad or all(c == "product-defect" for c in classes):
                g += 1
            elif any(c in ("test-bug", "environment", "data", "flaky") for c in classes):
                f += 1
            else:
                u += 1
        rows.append([suite, g + f + u, g, f, u])
        good, known, unknown = good + g, known + g + f, unknown + u
    if not rows:
        return V(note="прогонів не записано: qa-event run <playwright.json>")
    ff = ctx.m["automation"]["falseFailureRate"]
    note = (f"без вердикту (некласифіковані падіння, qa-event triage): {unknown} прогон(ів). " if unknown else "") + \
        (f"Хибні падіння на рівні тестів: {ff['value']}% ({ff['num']}/{ff['den']})." if ff["value"] is not None else "")
    r = ratio(good, known)
    return V(pct(r), good, known, note.strip(), columns=["Набір", f"Прогонів (останні {WINDOW})", "Правдивих",
                                                         "Хибних", "Без вердикту"], rows=rows)


def flaky_test_rate(ctx):
    rows, flaky_all, total = [], 0, 0
    for suite in sorted(ctx.runs):
        w = ctx.window(suite)
        if len(w) < 2:
            rows.append([suite, len(w), w[-1].get("tests") if w else 0, "—", "потрібно ≥ 2 прогони"])
            continue
        bad = defaultdict(int)
        flagged = set()
        for r in w:
            for t, s in (r.get("outcomes") or {}).items():
                if s in ("unexpected", "flaky"):
                    bad[t] += 1
                if s == "flaky":
                    flagged.add(t)
        flaky = sorted(t for t in set(bad) | flagged
                       if (t in flagged or bad[t] < len(w)) and ctx.triage.get(t) != "product-defect")
        n = w[-1].get("tests") or 0
        rows.append([suite, len(w), n, len(flaky), ", ".join(flaky) or "—"])
        flaky_all, total = flaky_all + len(flaky), total + n
    if not rows:
        return V(note="прогонів не записано: qa-event run <playwright.json>")
    r = ratio(flaky_all, total, "" if total else "у кожного набору менше двох повних прогонів")
    return from_ratio(r, columns=["Набір", "Прогонів у вікні", "Тестів", "Нестабільних", "Які"], rows=rows)


def test_execution_time(ctx):
    rows, hist = [], []
    for suite in sorted(ctx.runs):
        w = ctx.window(suite)
        d = [r.get("durationS") for r in w if r.get("durationS") is not None]
        if not d:
            continue
        rows.append([suite, w[-1].get("tests"), secs(d[-1]), secs(statistics.median(d)), f"{secs(d[0])} → {secs(d[-1])}"])
        hist += [[suite, (r.get("ts") or "")[:16], r.get("tests"), secs(r.get("durationS")), r.get("source") or "—"] for r in w]
    if not rows:
        return V(note="прогонів не записано: qa-event run <playwright.json>")
    return V(" · ".join(f"{r[0]} {r[2]}" for r in rows), note=f"останній повний прогін кожного набору; медіана — за останні {WINDOW}",
             columns=["Набір", "Тестів", "Останній", "Медіана", "Перший → останній у вікні"], rows=rows,
             hist_cols=["Набір", "Коли", "Тестів", "Тривалість", "Звіт"], hist_rows=hist)


def mutation_passes(events):
    """suite -> killed, mutants, rounds: every mutation event of each ticket (a ticket's pass may come in
    rounds and on several days, each on other tests); events with no ticket count by day."""
    groups = defaultdict(list)
    for e in events:
        if e.get("kind") == "mutation":
            groups[(e["suite"], e.get("ticket") or (e.get("ts") or "")[:10])].append(e)
    out = {}
    for (suite, key), es in sorted(groups.items()):
        s = out.setdefault(suite, {"killed": 0, "mutants": 0, "rounds": 0, "tickets": []})
        s["killed"] += sum(e["killed"] for e in es)
        s["mutants"] += sum(e["mutants"] for e in es)
        s["rounds"] += len(es)
        s["tickets"].append(key)
    return out


def mutation_score(ctx):
    evs = [e for e in ctx.events if e.get("kind") == "mutation"]
    if not evs:
        return V(note="проходу мутацій не записано: test-debugger, qa-event mutation --suite S --mutants N --killed K")
    last = mutation_passes(ctx.events)
    k, n = sum(e["killed"] for e in last.values()), sum(e["mutants"] for e in last.values())
    r = ratio(k, n)
    return V(pct(r), k, n, "усі раунди мутацій кожного тікета",
             columns=["Набір", "Тікети / дні", "Раундів", "Убито", "Мутантів", "Оцінка"],
             rows=[[s, ", ".join(e["tickets"]), e["rounds"], e["killed"], e["mutants"],
                    f"{ratio(e['killed'], e['mutants'])['value']}%"] for s, e in sorted(last.items())],
             hist_cols=["Коли", "Набір", "Убито / мутантів", "Тікет"],
             hist_rows=[[(e.get("ts") or "")[:16], e["suite"], f"{e['killed']}/{e['mutants']}", e.get("ticket") or "—"] for e in evs])


# ---------------------------------------------------------------- speed

def mttr(ctx):
    rows, hrs = [], []
    for d in ctx.m["defects"].get("items", []):
        a, b = _dt(d.get("opened") or d.get("found")), _dt(d.get("fixedAt"))
        if a and b and b >= a:
            h = (b - a).total_seconds() / 3600
            hrs.append(h)
            rows.append(["дефект", d["id"], d.get("severity") or "—", hours(h)])
    for i in incidents(ctx):
        a, b = _dt(i["opened"]), _dt(i["resolved"])
        if a and b and b >= a:
            h = (b - a).total_seconds() / 3600
            hrs.append(h)
            rows.append(["інцидент", i["id"], i.get("severity") or "—", hours(h)])
    if not hrs:
        return V(note="жодного виправленого дефекту чи вирішеного інциденту: qa-event defect <ID> --state fixed, "
                      "qa-event incident <ID> --state resolved")
    return V(hours(statistics.mean(hrs)), note=f"медіана {hours(statistics.median(hrs))}, виправлень: {len(hrs)}",
             columns=["Що", "ID", "Severity", "Від відкриття до виправлення"], rows=rows)


def defect_ageing(ctx):
    a = ctx.m["defects"]["openAgeDays"]
    if not a:
        return V(note="відкритих дефектів із датою знаходження немає")
    oldest = max(v["maxDays"] for v in a.values())
    return V(f"найстаріший {oldest} дн", columns=["Severity", "Відкритих", "Найстаріший, дн", "Медіана, дн"],
             rows=[[k, v["open"], v["maxDays"], v["medianDays"]] for k, v in sorted(a.items())])


# ---------------------------------------------------------------- coverage

def risk_coverage(ctx):
    rows, sources = plan_rows(ctx, "Risks")
    risks = [r for r in rows if re.match(r"^[A-Z]+-\d+$", r.get("id", ""))]
    if not risks:
        why = ("у тест-плані немає таблиці ## Risks" if not sources else
               "ризики в тест-плані без колонки ID (R-n): це ризики проєкту; ризики продукту пишуться з ID, Impact і Covered by")
        return V(note=why, sources=sources)
    out, cov, high, high_cov = [], 0, 0, 0
    for r in risks:
        links = TOKEN.findall(r.get("covered by") or r.get("requirements") or r.get("tests") or "")
        hit = [t for t in links if ctx.covered(t)]
        ok = bool(hit)
        is_high = (r.get("impact") or "").lower().startswith("high")
        cov, high, high_cov = cov + ok, high + is_high, high_cov + (ok and is_high)
        out.append([r["id"], r.get("risk") or "—", r.get("impact") or "—", ", ".join(links) or "—", "так" if ok else "ні"])
    rr = ratio(cov, len(risks))
    note = f"high-impact: {high_cov} з {high}" if high else ""
    return V(pct(rr), cov, len(risks), note, columns=["ID", "Ризик", "Impact", "Covered by", "Покрито"], rows=out,
             sources=sources)


def critical_user_journeys(ctx):
    rows, sources = plan_rows(ctx, "Critical user journeys")
    js = [r for r in rows if re.match(r"^[A-Z]+-\d+$", r.get("id", ""))]
    if not js:
        return V(note="у тест-плані немає таблиці ## Critical user journeys (| ID | Journey | Requirements |)",
                 sources=sources)
    outcomes = ctx.last_outcomes()
    out, green = [], 0
    for j in js:
        reqs = TOKEN.findall(j.get("requirements") or j.get("covered by") or "")
        tests = [row for row in ctx.trace if set(row.get("requirementIds") or []) & set(reqs)]
        missing = [q for q in reqs if not any(q in (row.get("requirementIds") or []) for row in ctx.trace)]
        red = [row["testId"] for row in tests if outcomes.get(row["testId"]) in ("unexpected", "flaky")]
        known = [row["testId"] for row in tests if row.get("expectedToFail")]
        if missing or not reqs:
            state = "не покрито: " + (", ".join(missing) or "у шляху немає вимог")
        elif red:
            state = "червоний: " + ", ".join(red)
        elif known:
            state = "відомий дефект: " + ", ".join(known)
        else:
            state = "зелений"
        green += state == "зелений"
        out.append([j["id"], j.get("journey") or "—", len(reqs), len(tests), state])
    r = ratio(green, len(js))
    return V(pct(r), green, len(js), "зелений = усі вимоги шляху мають автотест і в останньому прогоні все як очікувано",
             columns=["ID", "Шлях", "Вимог", "Тестів", "Стан"], rows=out, sources=sources)


def requirement_coverage(ctx):
    t, per = ctx.m["totals"], ctx.m["tickets"]
    if not t.get("requirements"):
        return V(note="вимог не знайдено (02-analysis/<T>/requirements/_index.json)")
    ws, au = ratio(t["withScenario"], t["requirements"]), ratio(t["automated"], t["requirements"])
    return V(f"{ws['value']}% зі сценарієм · {au['value']}% з автотестом", t["automated"], t["requirements"],
             f"waived: {t.get('waived', 0)}",
             columns=["Тікет", "Вимог", "Зі сценарієм", "З автотестом", "Waived", "Без сценарію і waiver"],
             rows=[[k, r["requirements"], f"{r['withScenario']['value']}%", f"{r['automated']['value']}%", r["waived"],
                    ", ".join(r["uncovered"]) or "—"] for k, r in per.items()])


# ---------------------------------------------------------------- release

def release_quality(ctx):
    rel = {}
    for ev in sorted((e for e in ctx.events if e.get("kind") == "release"), key=lambda e: e.get("ts") or ""):
        r = rel.setdefault(ev["version"], {"version": ev["version"], "ts": ev["ts"], "rollback": False, "hotfixes": 0})
        r["rollback"] = r["rollback"] or bool(ev.get("rollback"))
        r["hotfixes"] = max(r["hotfixes"], ev.get("hotfixes") or 0)
    if not rel:
        return V(note="релізів не записано: qa-event release <VERSION> --at <дата> [--rollback] [--hotfixes N]")
    order = sorted(rel.values(), key=lambda r: r["ts"])
    inc = incidents(ctx)
    rows, clean = [], 0
    for i, r in enumerate(order):
        a, b = r["ts"][:10], order[i + 1]["ts"][:10] if i + 1 < len(order) else "9999"
        prod = [d for d in ctx.defects if d.get("phase") == "production" and a <= (d.get("found") or "") < b]
        bad_sev = [d["id"] for d in prod if d.get("severity") in ("critical", "major", "blocker")]
        ins = [x for x in inc if a <= (x["opened"] or "")[:10] < b]
        big = [x["id"] for x in ins if str(x.get("severity") or "").lower() in ("sev1", "sev2", "critical", "major", "p1", "p2")]
        problems = (["rollback"] if r["rollback"] else []) + ([f"hotfix ×{r['hotfixes']}"] if r["hotfixes"] else []) + \
            ([f"critical/major: {', '.join(bad_sev)}"] if bad_sev else []) + ([f"інциденти: {', '.join(big)}"] if big else [])
        clean += not problems
        rows.append([r["version"], a, len(prod), len(ins), "так" if r["rollback"] else "—", r["hotfixes"],
                     "чистий" if not problems else "з проблемами: " + "; ".join(problems)])
    return V(f"{clean} з {len(order)} чисті", clean, len(order), "", columns=[
        "Версія", "Дата", "Продакшен-дефектів", "Інцидентів", "Rollback", "Hotfix", "Підсумок"], rows=rows)


# ---------------------------------------------------------------- process

def rejection_rate(ctx):
    return from_ratio(ctx.m["defects"]["rejectionRate"])


def reopen_rate(ctx):
    return from_ratio(ctx.m["defects"]["reopenRate"])


def open_questions(ctx):
    t, per = ctx.m["totals"], ctx.m["tickets"]
    if not t.get("stories"):
        return V(note="історій не знайдено (02-analysis/<T>/requirements/_index.json)")
    c = ctx.m.get("consent") or {}
    ans = ratio(c.get("answered", 0), t.get("questions", 0))
    return V(f"{round(t['questions'] / t['stories'], 2)} на історію", t["questions"], t["stories"],
             f"з відповіддю: {ans['value'] if ans['value'] is not None else 0}% ({c.get('answered', 0)}/{t.get('questions', 0)})",
             columns=["Тікет", "Історій", "Питань", "На історію"],
             rows=[[k, r["stories"], r["openQuestions"], r["questionsPerStory"]] for k, r in per.items()])


def exploratory(ctx):
    x = ctx.m["manual"]
    if not x.get("sessions"):
        return V(note="аркушів сесій немає: exploratory-testing пише 04-results/<T>/sessions/*.md, qa-event session")
    split = x.get("split") or {}
    return V(f"{x['sessions']} сесій, {x['hours']} год", note=f"знахідок на сесію: {x['findingsPerSession']}",
             columns=["Частина часу", "Частка"], rows=[[k, f"{v['value']}%"] for k, v in split.items()])


# ---------------------------------------------------------------- AI pipeline

def first_pass(ctx):
    return from_ratio(ctx.m["pipeline"]["firstPassGateRate"])


def mechanical(ctx):
    return from_ratio(ctx.m["pipeline"]["mechanicalFirstRunPass"])


def stage_cost(ctx):
    sc = ctx.m["pipeline"]["stageCost"]
    if "note" in sc:
        return V(note="жоден агент із транскриптом ще не зупинявся (хук qa-stage-gate)")
    total = round(sum(c["costUsd"] for c in sc.values()), 2)
    rows = [[s, c["runs"], f"${c['costUsd']}", f"${c['costPerRun']}", secs(c["medianDurationS"]), c["model"] or "—",
             f"{c['tokensIn']:,} / {c['tokensOut']:,}".replace(",", " ")] for s, c in sorted(sc.items(), key=lambda x: -x[1]["costUsd"])]
    return V(f"${total}", note="API-еквівалент за цінами hooks/prices.json; на підписці це не рахунок",
             columns=["Етап(и)", "Запусків", "Вартість", "За запуск", "Медіана активного часу", "Модель", "Токени in / out"],
             rows=rows)


def human_edit(ctx):
    p = ctx.m["pipeline"]
    return from_ratio(p["humanEditRate"], columns=["Змінений артефакт"], rows=[[x] for x in p["editedArtefacts"]])


def silent_consent(ctx):
    rows = [[t, ", ".join(r["silentConsent"])] for t, r in ctx.m["tickets"].items() if r["silentConsent"]]
    return from_ratio(ctx.m["pipeline"]["silentConsent"], columns=["Тікет", "Питання без відповіді, на які спираються сценарії"],
                      rows=rows)


def critic_disagreement(ctx):
    rows, dis, answered, total_d, resolved = [], 0, 0, 0, 0
    for f in sorted(ctx.root.glob("02-analysis/*/_gates/*.critic.json")):
        d = _load(f, {}) or {}
        items = [i for i in d.get("items") or [] if isinstance(i, dict)]
        n_dis = sum(i.get("result") == "disagree" for i in items)
        n_ans = sum(i.get("result") in ("agree", "disagree") for i in items)
        ds = [x for x in d.get("disagreements") or [] if isinstance(x, dict)]
        n_res = sum(1 for x in ds if x.get("resolution"))
        dis, answered, total_d, resolved = dis + n_dis, answered + n_ans, total_d + len(ds), resolved + n_res
        rows.append([d.get("ticket") or f.parts[-3], d.get("stage") or f.stem, d.get("rubric") or "—", f"{n_dis}/{n_ans}",
                     f"{n_res}/{len(ds)}", d.get("independence") or "—", (d.get("critic") or {}).get("model") or "—"])
    if not rows:
        return V(note="рецензій критика немає (_gates/<stage>.critic.json): агент qa-critic після гейтів 1 і 3")
    r = ratio(dis, answered)
    return V(pct(r), dis, answered, f"вирішено розбіжностей: {resolved} з {total_d}",
             columns=["Тікет", "Етап", "Рубрика", "Disagree / пунктів", "Вирішено", "Незалежність", "Модель критика"],
             rows=rows)


VALUES = {
    "escaped-defects": escaped_defects, "defect-detection-rate": ddp, "defect-leakage": leakage,
    "regression-effectiveness": regression_effectiveness, "test-effectiveness": test_effectiveness,
    "where-caught": where_caught, "critical-defect-rate": critical_defect_rate,
    "customer-impacting-defects": customer_impacting, "production-incidents": production_incidents,
    "automation-reliability": automation_reliability, "flaky-test-rate": flaky_test_rate,
    "test-execution-time": test_execution_time, "mutation-score": mutation_score, "mttr": mttr,
    "defect-ageing": defect_ageing, "risk-coverage": risk_coverage, "critical-user-journeys": critical_user_journeys,
    "requirement-coverage": requirement_coverage, "release-quality": release_quality,
    "defect-rejection-rate": rejection_rate, "defect-reopen-rate": reopen_rate,
    "open-questions-per-story": open_questions, "exploratory-sessions": exploratory,
    "first-pass-gate-rate": first_pass, "mechanical-first-run-pass": mechanical, "stage-cost": stage_cost,
    "human-edit-rate": human_edit, "silent-consent": silent_consent, "critic-disagreement-rate": critic_disagreement,
}


def catalog_values(root, events, m):
    ctx = Ctx(root, events, m)
    out = {}
    for mid, fn in VALUES.items():
        try:
            out[mid] = fn(ctx)
        except Exception as e:  # one broken input must not hide every other metric
            out[mid] = V(note=f"не вдалося порахувати: {type(e).__name__}: {e}")
    return out
