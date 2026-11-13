---
name: artifact-retention
description: Keeps the QA working repository small by retaining only the last few runs of heavy artefacts per service and target, while preserving the small derived history that trends and baselines depend on. Use this skill when the repository is growing, before committing run output, when the user asks about cleaning up test results or disk usage, or as a periodic maintenance step. Also use it to set up retention on a new project so the problem never starts.
---

# Artifact Retention

A QA repository grows by tens of megabytes per run and nobody notices until a
clone takes four minutes. The fix is not deleting history — it is separating two
kinds of output that look similar and behave completely differently.

## The two classes

**Disposable run artefacts.** Large, reproducible, only interesting while
investigating a specific failure. Traces, videos, screenshots, raw reporter JSON,
HAR captures, k6 raw output, scanner output, mutation backups. **Retain the last
three runs per target. Never commit them.**

**Durable derived records.** Small, irreplaceable, the basis of every trend and
comparison the pipeline can make. One summary line per run, baselines, scenario
JSON, RTM, the generated report, evidence attached to an open defect. **Keep
indefinitely, commit them.**

The distinction is not about age or size. It is about whether the thing can be
regenerated: a trace can be produced again by re-running; the fact that the p95
was 840 ms on 14 August cannot.

Deleting durable records to save space is a bad trade at any scale — a year of
metrics history is smaller than one Playwright video.

## Retain per target, not per project

A project has several services and interfaces: an API, a landing page, an admin
panel, maybe a second API. "Keep the last three runs" is ambiguous across them,
and in practice a noisy target evicts a quiet one's artefacts — the admin suite
runs twenty times a day, the landing suite twice a week, and last week's landing
trace disappears because of runs that have nothing to do with it.

Namespace by target, and count per target:

```
.runs/
├── api/
│   ├── 2026-09-14T0912/     traces, raw json, videos
│   ├── 2026-09-13T1740/
│   └── 2026-09-13T0930/     ← third; the next run evicts this one
├── ui-admin/
│   └── …
├── ui-landing/
│   └── …
├── perf/
│   └── …
└── security/
    └── …
```

Target names come from the project profile — `UI_TARGETS`, plus one per API
service. A target that appears in artefacts but not in the profile is a signal
the profile is out of date; say so rather than pruning it silently.

## What is never pruned, regardless of age

Four exceptions, and they matter more than the rule:

1. **Evidence attached to an open defect.** The reproduction for a defect
   somebody still has to fix. Pruned when the defect closes, not before.
2. **The current performance baseline.** Comparison is meaningless without it.
3. **The last known-good run per target.** When something breaks, the most useful
   artefact is the last one where it worked.
4. **Anything referenced by a published report.** A report linking to evidence
   that no longer exists is worse than one with no link.

Read these from `DISCREPANCIES.md`, `05-metrics/events.jsonl` and the report manifest
before pruning. A prune that silently removes an open defect's evidence costs far
more than the disk it saved.

## Never commit the disposable class

The stronger fix is upstream: these files should never enter git at all. Every
generated QA repository gets this in `.gitignore`:

```gitignore
.runs/
**/playwright-report/
**/test-results/
**/*.webm
**/*.zip
**/trace.zip
.auth/
k6-raw-*.json
zap-report-*.json
*.har
node_modules/
.env
.env.*
!.env.example
```

Pruning a repository that never accumulated the files is free. If heavy files are
already committed, say so plainly: removing them from history requires a rewrite,
and that is the engineer's decision, not something to do unasked.

## Procedure

1. **Read the exceptions first** — open defects, current baseline, last known-good
   run, report references. Build the keep-list before looking at anything else.
2. **Group by target**, sort by run timestamp descending.
3. **Keep the newest three per target**, plus everything on the keep-list.
4. **Report before deleting**: what will be removed, per target, with the space
   reclaimed. Then delete.
5. **Append a line to the run index** so a missing artefact is explicable later:
   the run existed, its summary is a `run` event in `05-metrics/events.jsonl`, its trace
   was pruned. Record a report with `qa-event run` before pruning it if it is not recorded yet.

Never delete a directory the profile does not know about. An unrecognised target
is a question, not rubbish.

## Retention is configurable

Default three. Some projects want more, and two situations genuinely need it:

```bash
RETAIN_RUNS=3                 # default
RETAIN_RUNS_perf=5            # baselines shift slowly; more comparison points help
RETAIN_RUNS_security=10       # findings are audited later, sometimes months later
```

Security artefacts deserve the longest retention and the most care: they may
contain sensitive request and response data, so they are both worth keeping and
worth keeping out of the repository. Store them locally with a longer retention
and never commit them.

## Report

```markdown
# Retention — 2026-09-14
Retained 3 runs per target · exceptions honoured

| Target | Kept | Pruned | Reclaimed |
|---|---|---|---|
| api | 3 | 11 | 240 MB |
| ui-admin | 3 | 7 | 1.2 GB |
| ui-landing | 3 | 0 | — |
| perf | 5 | 2 | 18 MB |

Kept beyond the limit:
- api/2026-08-22T1130 — evidence for DEF-PLAT-04, still open
- perf/2026-08-14T0900 — current baseline
- ui-admin/2026-09-02T1420 — last known-good run

Total reclaimed: 1.46 GB. Derived history untouched: 214 summary lines retained.
```

That last line is deliberate. It is what tells the engineer that trends survived
the cleanup, which is the thing they would otherwise worry about.
