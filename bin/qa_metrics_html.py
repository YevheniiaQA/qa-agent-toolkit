"""qa_metrics_html — the pages of `qa-metrics --html`: index.html and one <metric id>.html per catalogue entry.

  write_pages(out_dir, m, catalog)   -> (written paths, removed stale paths)

Texts come from metrics/catalog.json, numbers from m["catalog"] (qa_metric_values). Pages are
self-contained (no external script, font or stylesheet). A page carries the GENERATOR meta tag;
only such pages are replaced or removed, never a file somebody else put in the folder.
"""
import html
from pathlib import Path

GENERATOR = "qa-metrics --html"
DIRECTION = {"lower": "Чим менше, тим краще", "higher": "Чим більше, тим краще",
             "context": "Оцінюється в контексті: важливіший тренд, ніж рівень"}

CSS = """
:root{--bg:#f7f7f5;--surface:#fff;--ink:#1d1d1b;--muted:#5f5e5a;--line:#e3e2dd;--accent:#2f5d8a;
--accent-soft:#e6eef6;--na:#8a6d1f;--na-soft:#f7f0dc;--code:#f1f0ec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#171716;--surface:#1f1f1e;--ink:#ecebe6;
--muted:#a6a59f;--line:#34332f;--accent:#8db6df;--accent-soft:#22313f;--na:#e0c071;--na-soft:#3a321c;--code:#2a2a28}}
:root[data-theme="dark"]{--bg:#171716;--surface:#1f1f1e;--ink:#ecebe6;--muted:#a6a59f;--line:#34332f;--accent:#8db6df;
--accent-soft:#22313f;--na:#e0c071;--na-soft:#3a321c;--code:#2a2a28}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px 48px}
a{color:var(--accent)}
h1{font-size:26px;line-height:1.25;margin:4px 0 2px}
h2{font-size:17px;margin:28px 0 8px}
h3{font-size:15px;margin:0 0 6px}
.en{color:var(--muted);margin:0 0 12px}
.crumb{font-size:13px;color:var(--muted)}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 16px}
.badge{font-size:12px;padding:2px 8px;border-radius:999px;background:var(--accent-soft);color:var(--accent)}
.badge.muted{background:var(--code);color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px}
.value{font-size:30px;font-weight:650;line-height:1.2}
.value.na{font-size:18px;color:var(--na)}
.frac{color:var(--muted);font-size:14px;margin-top:4px}
.note{font-size:14px;margin-top:8px}
.na-box{background:var(--na-soft);border-radius:8px;padding:8px 10px;margin-top:8px;font-size:14px}
code,.formula{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;background:var(--code);border-radius:6px}
code{padding:1px 5px}
.formula{display:block;padding:10px 12px;white-space:pre-wrap}
ul{padding-left:20px;margin:6px 0}
li{margin:3px 0}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;background:var(--code)}
tr:last-child td{border-bottom:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.grid .card{display:flex;flex-direction:column;gap:4px;text-decoration:none;color:inherit}
.grid .card:hover{border-color:var(--accent)}
.grid .value{font-size:20px}
.grid .value.na{font-size:14px}
.grid .badge{align-self:flex-start;margin-top:auto}
.grid .hint{font-size:12px;color:var(--muted);margin-bottom:6px}
.legend{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;font-size:13px}
.legend .card{padding:12px}
.q{color:var(--muted);margin:-4px 0 10px;font-size:14px}
footer{margin-top:36px;font-size:12px;color:var(--muted)}
"""


def e(x):
    return html.escape("" if x is None else str(x))


def page(title, body, project):
    return (f'<!doctype html>\n<html lang="uk"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="generator" content="{GENERATOR}"><title>{e(title)}</title><style>{CSS}</style></head>'
            f'<body><main>{body}</main></body></html>\n')


def table(t):
    if not t:
        return ""
    head = "".join(f"<th>{e(c)}</th>" for c in t["columns"])
    rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in t["rows"])
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def value_block(v):
    if v["value"] is None:
        return (f'<div class="value na">немає даних</div>'
                f'<div class="na-box"><strong>Що потрібно:</strong> {e(v["note"])}</div>')
    frac = f'<div class="frac">{e(v["num"])} з {e(v["den"])}</div>' if v.get("den") not in (None, 0) and v.get("num") is not None else ""
    note = f'<div class="note">{e(v["note"])}</div>' if v.get("note") else ""
    return f'<div class="value">{e(v["value"])}</div>{frac}{note}'


def footer(m):
    window = f"з {m['since']}" if m.get("since") else "увесь час"
    return (f'<footer>Згенеровано <code>{GENERATOR}</code> · {e(m["project"])} · {e(m["generatedAt"][:16])} UTC · '
            f'період: {e(window)}. Не редагуйте вручну: тексти — у <code>metrics/catalog.json</code> тулкіта, '
            f'значення — з файлів воркспейсу.</footer>')


def metric_page(d, v, cat, m, names):
    group = next(g for g in cat["groups"] if g["id"] == d["group"])
    cad = cat["cadences"][d["cadence"]]
    feeds = "".join(f"<li><code>{e(f)}</code></li>" for f in d["feeds"])
    pits = "".join(f"<li>{e(p)}</li>" for p in d["pitfalls"])
    rel = ", ".join(f'<a href="{e(r)}.html">{e(names.get(r, r))}</a>' for r in d.get("related") or [])
    src = "".join(f"<li><code>{e(s)}</code></li>" for s in v.get("sources") or [])
    body = (
        f'<div class="crumb"><a href="index.html">QA-метрики</a> · {e(group["title"])}</div>'
        f'<h1>{e(d["title"])}</h1><p class="en">{e(d["name"])}</p>'
        f'<div class="badges"><span class="badge">{e(cad["title"])}</span><span class="badge muted">{e(group["title"])}</span>'
        f'<span class="badge muted">{e(DIRECTION[d["direction"]])}</span></div>'
        f'<div class="card"><h3>Значення тут</h3>{value_block(v)}</div>'
        f'<h2>Що це</h2><p>{e(d["what"])}</p>'
        f'<h2>Навіщо</h2><p>{e(d["why"])}</p>'
        f'<h2>Як рахується</h2><span class="formula">{e(d["formula"])}</span>'
        f'<p>{e(d["computed"])}</p>'
        f'<p><strong>Приклад.</strong> {e(d["example"])}</p>'
        f'<h2>Коли дивитися</h2><p><strong>{e(cad["title"])}.</strong> {e(cad["when"])}</p>'
        f'<h2>Звідки дані</h2><ul>{feeds}</ul>'
        + (f'<h2>Деталізація</h2>{table(v["table"])}' if v.get("table") else "")
        + (f'<h2>Історія</h2>{table(v["history"])}' if v.get("history") else "")
        + f'<h2>Як читати</h2><p>{e(DIRECTION[d["direction"]])}. Орієнтир: {e(d["target"])}.</p>'
        f'<h2>Пастки</h2><ul>{pits}</ul>'
        + (f'<h2>Повʼязані метрики</h2><p>{rel}</p>' if rel else "")
        + (f'<h2>Джерела цього значення</h2><ul>{src}</ul>' if src else "")
        + footer(m))
    return page(f'{d["title"]} — QA-метрики', body, m["project"])


def index_page(cat, m):
    legend = "".join(f'<div class="card"><h3>{e(c["title"])}</h3>{e(c["when"])}</div>' for c in cat["cadences"].values())
    groups = ""
    for g in cat["groups"]:
        cards = ""
        for d in (x for x in cat["metrics"] if x["group"] == g["id"]):
            v = m["catalog"][d["id"]]
            val = (f'<div class="value">{e(v["value"])}</div>' if v["value"] is not None
                   else '<div class="value na">немає даних</div>')
            if v.get("note"):
                hint = v["note"].split(":")[0] if v["value"] is None else v["note"]
                val += f'<div class="hint">{e(hint if len(hint) <= 110 else hint[:107] + "…")}</div>'
            cards += (f'<a class="card" href="{e(d["id"])}.html"><h3>{e(d["title"])}</h3>'
                      f'<span class="en">{e(d["name"])}</span>{val}'
                      f'<span class="badge">{e(cat["cadences"][d["cadence"]]["title"])}</span></a>')
        groups += f'<h2>{e(g["title"])}</h2><p class="q">{e(g["question"])}</p><div class="grid">{cards}</div>'
    have = sum(1 for v in m["catalog"].values() if v["value"] is not None)
    body = (f'<h1>QA-метрики — {e(m["project"])}</h1>'
            f'<p class="en">{have} з {len(cat["metrics"])} метрик мають дані. Кожна сторінка пояснює, що це, '
            f'як рахується і що потрібно, щоб зʼявилося значення.</p>'
            f'<h2>Як часто дивитися</h2><div class="legend">{legend}</div>{groups}' + footer(m))
    return page(f'QA-метрики — {m["project"]}', body, m["project"])


def generated(path):
    try:
        return f'content="{GENERATOR}"' in path.read_text(encoding="utf-8", errors="replace")[:600]
    except OSError:
        return False


def write_pages(out, m, cat):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    names = {d["id"]: d["title"] for d in cat["metrics"]}
    pages = {"index.html": index_page(cat, m)}
    for d in cat["metrics"]:
        pages[f'{d["id"]}.html'] = metric_page(d, m["catalog"][d["id"]], cat, m, names)
    written = []
    for name, text in pages.items():
        p = out / name
        if p.exists() and not generated(p):
            raise SystemExit(f"qa-metrics: {p} exists and was not generated by {GENERATOR}; not overwriting it")
        p.write_text(text, encoding="utf-8")
        written.append(p)
    removed = [p for p in out.glob("*.html") if p.name not in pages and generated(p)]
    for p in removed:
        p.unlink()
    return written, removed
