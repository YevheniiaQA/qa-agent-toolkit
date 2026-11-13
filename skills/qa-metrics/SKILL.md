---
name: qa-metrics
description: Assembles QA metrics and trends for a retrospective or a quality review — escaped defects, where defects were caught, coverage movement, suite stability and runtime, requirement quality signals — with the reasoning behind each number rather than a dashboard. Use this skill before a retrospective, when the user asks how testing went this sprint, when preparing a quality summary for management, or when deciding where to invest QA effort next. Also use it to check whether a process change actually helped.
---

# QA Metrics

A retrospective runs on evidence or on opinions, and without this skill it runs
on opinions. The goal is a short, honest set of numbers with their reasoning — not
a dashboard, and emphatically not a scoreboard for individuals.

## The numbers come from `qa-metrics`, never from memory

Run it in the workspace first and build everything on its output:

```bash
qa-metrics                    # readable summary
qa-metrics --json             # the same, for a report or a comparison
qa-metrics --since 2026-10-01 # one sprint or release
```

It computes every metric below from files: `05-metrics/events.jsonl`, `bugs/*.md`, the
requirement and scenario JSON under `02-analysis/`, `TRACEABILITY.json` under `03-tests/`,
session sheets under `04-results/*/sessions/`, and the current hashes of artefacts the
pipeline recorded. Each number carries its numerator, denominator and source. A metric with
no data prints `n/a` and what would produce it: report it as missing, never estimate it.
If a number looks wrong, fix the input (a defect file, a missing event), not the output.

`events.jsonl` is written only by `qa-event`, `qa-gate --write` and the `qa-stage-gate`
hook, each from a file (a Playwright report, a gate file, a transcript). Append-only for the
same reason `test_data.yaml` is: a correction is a new line naming the one it replaces. A
metrics file somebody can rewrite is a metrics file nobody can cite. In a workspace that
still has older `05-metrics/*.jsonl` files, run `qa-event migrate` once: it copies them and
the Playwright reports under `03-tests/` into events and keeps the originals;
`qa-metrics` then cross-checks the old summaries against the raw reports.

Release comparison is two runs of `qa-metrics --since` (or two `--json` outputs) side by
side — coverage movement, defect severity shifting, runtime growing. Those comparisons are
the point; a single run's numbers are almost never interesting on their own.

## One page per metric

The definitions live in one place, `metrics/catalog.json` in the toolkit: for each metric
what it is, why it matters, the formula, how the toolkit computes it, what feeds it, when
to look at it, how to read it and its traps. `qa-metrics --html` turns the catalogue and this
workspace's numbers into `05-metrics/index.html` and one `<metric>.html` per metric, with
the value here, the rows behind it and, where there is one, its history. A metric with no
data shows what would produce it. Regenerate the pages after a run, at the end of a stage R
and before a retrospective (`--since <sprint start>`); never edit them by hand.

Each metric has a cadence — when its number means something:

| Cadence | Examples |
|---|---|
| after every run | test execution time |
| across runs | automation reliability, flaky test rate |
| per ticket / after a stage | requirement and risk coverage, critical user journeys, mutation score, stage cost, critic disagreements |
| end of sprint or release | escaped defects, DDP, leakage, critical rate, customer-impacting defects, incidents, MTTR, regression effectiveness, release quality |

A new metric is a catalogue entry plus a function with the same id in
`bin/qa_metric_values.py`; `test_metric_catalog.py` fails until both exist.

## What feeds the metrics

| Fact | Where it is written |
|---|---|
| a defect, its severity and where it was caught | `bugs/<ID>.md`: `Severity`, `Status` (`Open, found <date> by <stage, suite or test>`), `Phase` when "found by" is not obvious |
| it reached users / it is a regression | `bugs/<ID>.md`: `Customer impact \| yes — <what>`, `Regression \| yes` |
| a defect changed state | `qa-event defect <ID> --state fixed\|verified\|closed\|rejected\|reopened [--at <when>]` |
| a production incident | `qa-event incident <ID> --state open\|resolved --severity sevN [--customer-impact] --at <when>` |
| a release, its rollback or hotfixes | `qa-event release <VERSION> --at <date> [--rollback] [--hotfixes N]` |
| a test run | `qa-event run <playwright.json>`; every unexpected failure classified with `qa-event triage` |
| a mutation pass | `qa-event mutation --suite S --mutants N --killed K` (each round, with `--ticket`) |
| an exploratory session | `qa-event session <sheet.md>` |
| an engineer's answer to an open question | `Answer (engineer, <date>): …` under it in `OPEN_QUESTIONS.md`, or `qa-event decision <Q> --by engineer` |
| product risks and critical user journeys | `01-docs/test-plan/*.md`: `## Risks` with `ID` and `Covered by`, `## Critical user journeys` (`test-plan`) |
| stage cost, gate results, artefact hashes | the `qa-stage-gate` hook and `qa-gate --write`, automatically |

While no production defect, incident or release is recorded, DDP is an upper bound and the
production metrics are `n/a`: say so, never fill them in. A recorded fact that was wrong is
fixed with a correction line, not by editing `events.jsonl`. `qa-event recompute-durations`
rewrites, by correction, stage durations recorded before active time was measured.

**Cycle time from ready-for-QA to QA-approved** measures the loop, not the person; it needs
the tracker's transition dates and stays out of `qa-metrics` until a ticket source provides them.

## What not to measure

Tests written per person. Defects found per tester. Pass rate as a target. Each
of these produces exactly the behaviour it rewards: more shallow tests, more
trivial defects, and assertions weakened until they pass. If someone asks for
them, say what they will cause rather than refusing flatly.

Pass rate deserves a specific warning: in a pipeline that deliberately asserts
requirements the product violates, a low pass rate means the suite is doing its
job. Reporting it as a quality score inverts the incentive completely.

## Retrospective summary

Short, specific, and about the process rather than about people. Every number is quoted
from `qa-metrics`; `n/a` stays `n/a` with its reason:

```markdown
# QA retrospective — sprint 34

## Numbers
Stories tested 6 · scenarios 142 · defects found 19 (2 critical, 7 major)
Escaped to production: 1 · DDP 95% (18/19) · rejection 5% (1/20) · reopen 0% (0/7)
Requirement coverage: 94% with a scenario, up from 91%
Suite: 312 tests · smoke 3m40s · 19 of 20 nightly runs clean · false failures 2% (1/48)
Mutation score api 92% (46/50) · first-pass gate rate 80% (8/10) · stage cost $3.10
Defects caught at requirements stage: 4 — before any code was written
Open questions acted on without an answer: 3 of 11 (Q-04, Q-07, Q-09)

## What worked
Four contradictions were caught during decomposition and returned to the analyst.
Three of those would have become defects; one would have shipped.

## What did not
The escaped defect (PROD-88) came from a scenario we waived as low risk in sprint
32. The waiver had no revisit date. Every waiver now carries one.

## Where the time went
20% requirements · 25% scenario design · 35% automation · 20% debugging.
Debugging is up from 14% — the shared test environment accounts for most of it.

## One change to try
Move test execution to a dedicated instance. Three read-after-write tests are
unstable solely because of the shared host, and it costs roughly four hours a
sprint in re-runs and triage.
```

One change per retrospective. Three changes means no change, because nothing gets
followed through far enough to know whether it worked.

## Self-check before reporting completion

1. **Every number in the summary appears in the `qa-metrics` output it was taken from**, with
   the same numerator and denominator; keep that output next to the summary.
2. **Every `n/a` is reported as `n/a` with its reason**, never estimated or left out silently.
3. **No metric names or ranks a person.**
4. **DDP and leakage are called an upper bound** while no production defect is filed in the
   workspace.
5. **The previous change is reported first, and one change is proposed**, not three.

## Closing the loop

Next retrospective, report on the previous change before anything else, with the same
`qa-metrics` figure before and after. A change nobody measures is indistinguishable from a
change nobody made, and the habit of checking is worth more than any individual improvement.
