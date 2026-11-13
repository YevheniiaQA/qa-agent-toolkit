---
name: test-report
description: Builds a self-contained HTML report from a test run that non-engineers can read — requirement coverage, deliberate failures with their defect references, a manual-executable test catalogue, stability across runs, and the environment the numbers came from. Use this skill after any test execution, whenever the user asks for a readable report, wants to show results to an analyst or team lead, asks what the suite actually covers, or says the raw output is hard to read. Also use it to produce a release readiness summary.
---

# Test Report

A Playwright HTML report answers "which tests failed". It does not answer the
questions a team actually asks: what is covered, which failures are deliberate,
what can a manual tester execute, and is the suite trustworthy.

This skill produces one self-contained `REPORT.html` — no server, no build step,
no network. Double-click and it opens.

## Inputs

| Source | Provides |
|---|---|
| `results/run-*.json` (Playwright JSON reporter) | Per-test outcomes of each run: steps, errors, attachments |
| `05-metrics/events.jsonl` via `qa-metrics --json` | Stability across runs (`automation.suites.<suite>`: runs, clean runs, inconsistent tests, runtime), false failure rate, mutation score, defect counts |
| `02-analysis/<TICKET>/scenarios/api.json`, `ui.json` | Scenario text, data, expectations, defect refs |
| `02-analysis/<TICKET>/scenarios/RTM.md` or the suite's waiver block | Requirement coverage |
| `03-tests/*/TEST_CATALOGUE.md` | Human-readable case text |
| `RUN_REPORT.md` | Environment, contract version, dataset size |

Missing inputs degrade the report rather than blocking it — render the sections
you have and mark the others as unavailable with the reason. A report that
refuses to build because one file is absent is a report nobody gets.

## Building it

Use `report-template.html` in this skill folder. Do not write HTML from scratch:
a consistent report is one people learn to read quickly, and a regenerated layout
each time defeats that.

The template contains a single `<script id="report-data" type="application/json">`
block. Replace its contents with the data object below, write the result to
`REPORT.html`, and change nothing else.

The data object has ten top-level keys: `meta`, `verdict`, `scope`, `summary`,
`defectSummary`, `defects`, `requirements`, `stability`, `tests`,
`openQuestions`, `recommendations`, `limitations`. Sections with no data are
omitted from the rendered report automatically.

```json
{
  "meta": {
    "title": "Item registration — test report",
    "ticket": "DEMO-1",
    "release": "Example API 1.0.0",
    "reportVersion": "v1.0",
    "testPeriod": "11–13 September 2026",
    "reportDate": "13 September 2026",
    "build": "openapi.json 1.0.27",
    "environment": "Shared public sandbox",
    "preparedBy": "Alex T., Senior QA Engineer",
    "reviewedBy": "—",
    "cleanup": "Confirmed — no test records remain on the host",
    "title": "Add a new item to the store",
    "generated": "2026-09-13T14:22:00Z",
    "host": "https://api.example.com/v1",
    "hostNote": "shared public instance",
    "contract": "openapi.json infoVersion 1.0.27",
    "dataset": "search?status=available — 1266 records / 109 KB",
    "runtime": "Node 20.11.1 · Playwright 1.47.2",
    "runs": 3
  },
  "verdict": {
    "status": "no-go",
    "statement": "Five defects are open, two critical and both causing silent data loss.",
    "conditions": ["DEF-DEMO-03 and DEF-DEMO-04 fixed and re-verified"]
  },
  "scope": {
    "included": ["Item registration via POST /items — all validation rules stated"],
    "excluded": ["Authorisation — the system exposes no permission boundary to test"]
  },
  "stability": {
    "runs": 13, "cleanRuns": 11, "rate": "1 run in 6",
    "classification": "environment",
    "reasoning": "Sequentially consistent; fails only under four parallel callers against a shared instance.",
    "affected": ["TC-010", "TC-014", "TC-016"],
    "remediation": "Run against a dedicated instance. A retry would hide the signal rather than fix it.",
    "mutationScore": "12 of 12 mutations killed"
  },
  "defectSummary": { "critical": 2, "major": 3 },
  "recommendations": ["Fix DEF-DEMO-03 and DEF-DEMO-04 before release."],
  "limitations": ["Testing ran against a shared sandbox that third parties write to concurrently."],
  "summary": {
    "passed": 12, "expectedFailures": 11, "unexpectedFailures": 0,
    "blocked": 1, "flaky": 1, "total": 24
  },
  "requirements": [
    { "id": "F-DEMO-1-BE-01", "title": "Register an item", "status": "covered",
      "scenarios": 4, "assertions": 9, "classes": "4 of 4" },
    { "id": "F-DEMO-1-BE-03", "title": "Name is mandatory", "status": "covered-failing",
      "scenarios": 2, "assertions": 3, "classes": "2 of 2", "defect": "DEF-DEMO-01" },
    { "id": "NF-DEMO-1-BE-02", "title": "Authorisation", "status": "waived",
      "reason": "No authorisation boundary exists in the system",
      "revisitWhen": "Authentication is introduced" }
  ],
  "defects": [
    { "id": "DEF-DEMO-03", "severity": "critical", "silent": true,
      "title": "Any status value is accepted and stored",
      "callerSees": "200 OK",
      "detail": "A case variant such as AVAILABLE is stored but never returned by search, so the record is unreachable through the only search path the feature offers.",
      "tests": ["TC-009", "TC-010", "TC-012"] }
  ],
  "tests": [
    { "id": "TC-013", "name": "Register without a name",
      "data": "imageUrls only, status available",
      "expected": "400 or 422 naming the field",
      "requirement": "F-DEMO-1-BE-03", "defect": "DEF-DEMO-01",
      "expectedToFail": true, "runs": ["fail", "fail", "fail"],
      "manual": true }
  ],
  "openQuestions": [
    { "id": "Q-06", "text": "No name length limit is stated anywhere",
      "blocks": ["NF-DEMO-1-BE-03"], "proposed": "Adopt the OpenAPI schema limit" }
  ]
}
```

## Performance and security blocks

Performance and security runs land in the same report the client already reads,
as two optional blocks. One document, not three attachments nobody opens together.

```json
"performance": {
  "profile": "Load test · ramp to 50 VUs over 16 minutes",
  "conditions": "Staging, single node, 8,410 records, no other traffic. Figures are indicative of this environment only.",
  "operations": [
    { "name": "POST /items", "p50": "310 ms", "p95": "1,310 ms", "p99": "4,700 ms",
      "throughput": "39 rps", "errorRate": "0.3%", "deltaP95": "+56%" }
  ],
  "thresholds": [
    { "name": "http_req_duration p95", "target": "< 2,000 ms", "actual": "1,310 ms",
      "passed": true, "source": "ticket §AC ¶6" }
  ],
  "saturation": "Error rate rises above 1% beyond 68 concurrent users",
  "doesNotEstablish": "Production behaviour behind a load balancer, or sustained load beyond 16 minutes"
},
"security": {
  "scope": "QA security testing covering authorisation boundaries and known risk classes on the API and frontend. Not a penetration test and not a security audit.",
  "counts": { "critical": 1, "medium": 2 },
  "findings": [
    { "id": "SEC-04", "severity": "critical", "category": "API1:2023 BOLA",
      "surface": "Backend API · GET /api/v1/orders/{id}",
      "title": "Any authenticated user can read another user's order",
      "impact": "Order identifiers are sequential, so enumeration is trivial. Delivery addresses and partial card numbers are exposed.",
      "fix": "Verify ownership server-side on every request, not only authentication.",
      "evidence": "04-results/<T>/evidence/SEC-04.http — headers redacted" }
  ],
  "notTested": ["Infrastructure and network layer", "Source code review", "Social engineering"],
  "tooling": ["OWASP ZAP baseline", "gitleaks", "npm audit"]
}
```

Two rules specific to these blocks:

**The performance conditions line renders above the numbers**, not below them.
A latency figure read without its environment gets quoted as a production
capability within a week.

**The security scope statement renders before any finding.** It is what keeps the
report honest about what it does and does not assure, and putting it at the
bottom means nobody reads it.

**Never put a working exploit, a token, or real user data in the report.** The
evidence field names a file; the file itself is redacted and is not attached to a
client deliverable without asking.

## Client-facing sections

A report an engineer reads and a report a client reads differ in what comes
first. These sections make the difference, and all of them are mandatory when the
report leaves the team.

**Verdict, at the top.** `go` / `conditional` / `no-go`, one sentence of plain
reasoning, and — for anything other than `go` — the specific conditions that would
change it. A client who reads only the first screen should come away with the
right decision. Never hedge this into meaninglessness: "some issues were found"
helps nobody.

**Dates and identity.** Test period (from–to, not just the report date), report
date, report version, build or contract version, environment, who prepared it.
Without these the document is unciteable three weeks later, and a client cannot
tell whether it describes the build they are about to ship.

**Scope, in two halves.** What was tested and — more important — **what was not**,
with the reason. Untested areas discovered after release are how a report destroys
trust. "Authorisation: not tested, because the system exposes no permission
boundary" is a finding in itself.

**Defect impact in business terms.** Alongside the technical detail, say what it
means for someone using the product. "One user can destroy another user's data by
chance, with no audit trail" lands where "duplicate id returns 200" does not.

**Limitations.** Shared environment, indicative timings, sample sizes, what could
not be determined from outside the system. A report that states its own limits is
more credible, not less, and it protects you when someone later asks why an issue
was missed.

**Recommendations.** Ordered actions, each tied to a defect or a question.

**Confirmation that test data was cleaned up.** On a shared or client-owned
environment this is the first thing an operations team wants to know.

## What the report must make obvious

**Deliberate failures are not problems.** Eleven red tests look like a broken
suite to anyone who does not know better. The report separates *expected
failures* (the ticket says X, the system does Y, we assert X) from *unexpected
failures* (something is wrong with the test or the environment) and gives the
first group a calm colour, not a red one. Getting this wrong makes the report
actively harmful — a team that reads "11 failed" stops reading.

**Silent defects come first.** A defect where the caller receives success is
worse than one that errors, because nobody will report it. Those get their own
block above everything else, with what the caller sees stated plainly.

**Coverage shows classes, not just a percentage.** "1 of 3 classes" is honest;
"50%" is a number that can mean anything.

**Stability is visible per test.** `2/3` and `3/3` are different levels of trust.

**Every number carries its conditions.** A p95 measured against a shared host
with 1266 records is evidence, not a gate, and the report says so where the
number appears rather than in a footnote.

## Audiences

The same file serves three, so the layout puts each one's answer near the top of
its own section:

- **Team lead** — the summary strip: is this shippable, what is blocking
- **Analyst** — requirement coverage and open questions, no code anywhere
- **Manual tester** — the catalogue, with data and expected result per row,
  filterable to rows marked `manual`

## Numbers come from qa-metrics, not from a recount

Before building, record every run the report covers (`qa-event run <report.json>`, already
recorded ones are skipped), then take the `stability`, `defectSummary` and mutation figures
from `qa-metrics --json`. The report and the retrospective then quote the same number from
the same events, and a figure in `REPORT.html` can be traced to the report file it came from.
Apart from those `qa-event run` lines the report writes nothing to `05-metrics/`; there is no
separate history file.

## Self-check before reporting completion

1. **`REPORT.html` opens with no network access** — no CDN links, no external
   fonts, no absolute file paths.
2. **Every test in the suite appears**, including expected failures and blocked
   scenarios.
3. **Expected and unexpected failures are visually distinct**, and the summary
   counts them separately.
4. **Every defect lists the tests that demonstrate it**, and each of those tests
   exists in the catalogue.
5. **Every waived requirement shows its reason**, not just the word "waived".
6. **The environment block is present**, including dataset size where timing
   figures appear anywhere in the report.
7. **The verdict states a decision**, not a description. "Not ready to release"
   with named conditions, not "several issues were identified".
8. **Scope lists what was not tested**, each with a reason.
9. **Test period and build identity are present.** A report without them cannot be
   matched to a release.
10. **Every defect states its impact in business terms**, not only its technical
    symptom.
11. **Test data cleanup is confirmed** where the environment is shared or owned
    by someone else.
12. **The report prints cleanly** — check it renders to PDF without clipping,
    since that is how most clients will file it.
13. **No raw stack traces in the main view** — they belong behind a disclosure, if
   at all. This report is read by people who will not act on a stack trace.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event run <report.json>` for each run the report covers that is not
recorded yet (`qa-event list --kind run` shows what is; a report already recorded is skipped).

