---
name: tms-uploader
description: Publishes scenario JSON as test cases into TestRail (or Zephyr Scale, Xray, qTest) with the agreed section hierarchy, priorities, labels, and requirement links, then writes the case IDs back into the automated tests so code and TMS stay linked. Use this skill whenever the user wants generated test cases in their test management system, whenever they ask to sync scenarios with TestRail, or as the delivery stage of the QA pipeline. Also use it to update previously uploaded cases without creating duplicates.
---

# TMS Uploader

The TMS is where the rest of the organisation sees QA work. Uploading is a
projection of the scenario JSON into the TMS structure, done idempotently so
re-runs update rather than duplicate.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for the test management system (`testrail`, `zephyr`, `xray`, `qtest`): read `INTEGRATIONS`, skip a
system that is not listed, report it as `➖ <system> disabled for this project`, never route
around a `qa-guard` block.

**Local alternative:** export the cases with manual-test-cases (CSV or XLSX in the format the TMS imports) and stop. Do not write case IDs back into the tests: there are none yet, and invented IDs are worse than missing ones.

## Before uploading

**Refuse scenarios that have not passed the generator's quality gate.** Cases with
placeholder data, missing expected results, or no traceability create mess that
someone cleans up by hand later, and they undermine trust in everything the
pipeline produces.

**Confirm the section hierarchy first.** Use `TMS_ROOT_SECTION` from the project
profile and the structure recorded in the working agreement. Generating a
hierarchy the team did not agree to means someone drags two hundred cases between
sections by hand. Three levels is the usual shape:

```
Platform / Auth / User login
Platform / Integrations / Connect Confluence
```

## Mapping (TestRail)

| Scenario field | TestRail field |
|---|---|
| `testSuite.name` | Section (created if absent) |
| `testCase.id` | Custom field `external_id` — the idempotency key |
| `testCase.name` | Title |
| `priority` | Priority |
| `level`, `technique` | Custom labels: `api`, `ui`, `boundary-value` |
| `preconditions` | Preconditions, one per line |
| `testSteps[]` | Steps: step / test data / expected result |
| `traceability.requirementIds` | Refs field |
| `traceability.userStory` | Refs field, Jira key |
| automated? | Type = Automated, else Manual |

Preserve step granularity. Collapsing six steps into a paragraph destroys exactly
the detail that made generating scenarios worth doing, and it is what manual QA
under time pressure used to lose.

For Zephyr Scale, Xray, or qTest the field names change but the mapping and the
idempotency rule do not. Read the target from `TMS_PROJECT` and adapt.

## API upload or file import

Two routes into a TMS, and they are not interchangeable:

- **API upload** — this skill. Idempotent, writes IDs back into the code, keeps
  execution history. Use it whenever a token and network access exist.
- **File import** — `manual-test-cases`. Produces a CSV or XLSX someone imports by
  hand. Use it when there is no API access, when the team wants to review before
  anything lands, or when the cases are manual-only and no automation exists.

When both are in play, the API is the writer and the CSV is a review artefact.
Importing a file for cases the API already created produces duplicates, because
the file import path has no idempotency key unless the target supports an
external ID column.

## Use the catalogue, do not re-derive

`automation-api` and `automation-ui` emit `TEST_CATALOGUE.md` — one row per test
with its data, expected result, requirement and defect reference. Read case text
from there rather than re-rendering it from the scenario JSON.

Two renderings of the same thing drift, and when they do the TMS and the
catalogue disagree about what a case checks, with no way to tell which is right.
One source, two destinations.

Where the catalogue lacks a field the TMS needs, take it from the scenario JSON
by ID — do not paraphrase.

## Idempotency

Key on `external_id` (`TC-283-API-001`):
- exists and unchanged → skip
- exists and changed → update in place, preserving execution history
- new → create
- in TMS but no longer in scenarios → flag for review, never auto-delete

Auto-deletion is the one operation to refuse outright. Execution history is audit
evidence, and a scenario disappearing from a generation run is not sufficient
grounds to destroy it.

## Write the IDs back

Annotate the automated tests so a CI result maps to a TMS case with no lookup:

```ts
test('TC-283-API-001 connects with valid url and token @smoke @C4412', async ({ api }) => {
```

Emit `TMS_MAPPING.json` (scenario ID → TestRail case ID → test file:line). This is
what `ci-setup` uses to publish results back automatically.

## Credentials

Read the API token from an environment variable. Never write it into a config
file, a report, or the conversation. If the token is missing, stop and name the
variable that needs setting rather than asking for the value.

## Report

```markdown
# TestRail upload — DEVAI-283
Created 31 · Updated 5 · Skipped 2 (unchanged) · Flagged 1
Section: Platform / Integrations / Confluence
Flagged: C3981 "legacy connect flow" — no longer in scenarios, left in place for review
```
