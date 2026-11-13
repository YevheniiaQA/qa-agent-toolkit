# RUN_REPORT.md and TEST_CATALOGUE.md

Read this before writing either report.

## RUN_REPORT.md must be reproducible

A report without its conditions means nothing a month later. Record:

```markdown
# Run report — DEMO-1 — 2026-09-13 14:22 UTC
Host:          https://api.example.com/v1 (shared public instance)
Contract:      openapi.json infoVersion 1.0.27
Dataset:       search?status=available returned 1266 records / 109 KB
Node:          20.11.1 · Playwright: 1.47.2
Runs:          3 · Results: 21/21, 21/21, 20/21 (TC-014 failed once)
```

The dataset size is what makes "the 2-second budget is eroding" a meaningful
observation rather than an anecdote. On a shared host it is also the single
number most likely to explain a change in timing between runs.

## TEST_CATALOGUE.md is a required output

The suite is TypeScript; most of the people who need to know what is covered do
not read TypeScript. Generate a human-readable catalogue alongside the code, and
treat it as mandatory rather than a nicety.

```markdown
| ID | What it does | Data | Expected | Requirement | Defect | Expected to fail |
|---|---|---|---|---|---|---|
| TC-001 | Register an item with all fields | name, category Books, 1 image URL, status available | 200, body.id is int64, echoes fields | F-DEMO-1-BE-01 | — | no |
| TC-013 | Register without a name | imageUrls only, status available | 400/422 naming the field | F-DEMO-1-BE-03 | DEF-DEMO-01 | yes |
```

It serves three audiences at once: a manual tester can execute any row by hand, an
analyst can read coverage without opening code, and `tms-uploader` has a single
source for case text instead of re-deriving it from JSON.

Generate it from the scenario JSON, never by hand — a catalogue that drifts from
the suite is worse than none, because people will trust it.
