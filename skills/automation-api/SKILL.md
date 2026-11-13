---
name: automation-api
description: Generates a runnable TypeScript API test project from scenario JSON using Playwright's APIRequestContext, with typed clients, fixtures, schema validation, and full traceability back to requirement IDs. Use this skill whenever the user wants API tests automated, whenever scenarios exist for backend endpoints, whenever they ask for Playwright API testing or request-level tests, or as the API branch of the QA pipeline. Also use it to add API-level coverage to a project that only has UI tests.
---

# Automation API (TypeScript + Playwright)

Generate tests a senior engineer would approve in review — typed, isolated, assertive,
traceable — not code that merely runs.

## Project shape

One Playwright project for every API test in the product, `03-tests/api/`, with typed clients,
Zod response schemas and fixtures under `src/`, and specs under `specs/<feature>/` — by feature,
never by ticket; a new ticket adds spec files, it never creates a second project. Read
`references/project-and-config.md` before creating or extending the project: the layout, the
config baseline, the base-URL trap, and what to read in a target repository first.

## Generation pipeline

**Phase 1 — setup.** Load the scenario JSON, the relevant API files from the
global context, and resolved test data. Load only the service contracts this
ticket touches; loading the whole context degrades output quality.

**Phase 2 — generate.** One `test()` per scenario. The test title carries the
scenario ID so a CI failure maps to a requirement without a lookup.

**Phase 3 — debug.** Hand off to `test-debugger`. Do not declare completion on
code that has never executed.

**Phase 4 — report.** Emit `DEBUG_REPORT.md` with pass/skip/expected-failure
counts and every classification decision.

## Code standard

```ts
import { test, expect } from '../src/fixtures';
import { ConnectResponse } from '../src/schemas/integrations';

test.describe('US-001 Connect a Confluence workspace', () => {
  test('TC-283-API-001 connects with valid url and token @smoke', async ({ api }) => {
    const res = await api.post('/api/v1/integrations/confluence/connect', {
      data: { url: process.env.CONFLUENCE_URL!, token: process.env.CONFLUENCE_TOKEN! },
    });

    expect(res.status(), 'connect should return 200').toBe(200);

    const body = ConnectResponse.parse(await res.json());
    expect(body.success).toBe(true);
    expect(body.integrationId).toMatch(/^[0-9a-f-]{36}$/);
  });

  test('TC-283-API-011 rejects a domain longer than 50 characters', async ({ api }) => {
    const res = await api.post('/api/v1/integrations/confluence/connect', {
      data: { url: `https://${'a'.repeat(51)}.atlassian.net`, token: 'valid-token' },
    });

    expect(res.status()).toBe(400);
    expect((await res.json()).error).toBe('VALIDATION_ERROR');
  });
});
```

### Rules the generator follows

**Validate the whole response shape, not one field.** Parsing through a Zod schema
catches contract drift — a renamed field, a number that became a string, a
nullable that stopped being nullable — that a `status === 200` check never will.

**Assert status explicitly, always.** A test that only checks the body will pass
against a 500 that happens to return JSON.

**Every test carries a message on its primary assertion.** `expect(res.status(),
'connect should return 200')` turns a CI failure into a sentence instead of a
diff.

**No shared mutable state between tests.** Each test provisions what it needs
through a fixture and cleans up. This is what makes `fullyParallel: true` safe —
and parallelism is where API suites get their speed advantage.

**No conditional assertions.** `if (res.status() === 200) expect(...)` is a test
that passes when the feature is broken. Branch in fixtures, never in assertions.

**Negative cases assert the error shape, not just the code.** A 400 with the wrong
error code is still a bug.

**Tag for selection**: `@smoke`, `@regression`, `@slow`, `@security`. CI needs to
run a five-minute subset on every push and the full suite nightly.

## Traceability

Every spec file opens with a comment block mapping tests to requirements, and the
suite title names the story. Emit `TRACEABILITY.json` mapping test title → test
case ID → requirement IDs, which `automation-compare` and RTM regeneration consume.

## Non-production data belongs to someone

Default to read-only on any environment the team or the client owns. Write
operations need a reason and, where the environment is shared, the engineer's
approval before the first generated test performs one.

Where writes are necessary: unique run-scoped identifiers, obviously synthetic
values, cleanup in fixture teardown, and a list of writing tests in the report so
whoever owns the environment can see what touched it. Never generate a test that
deletes or modifies a record it did not create.

## Read the scenario's handoff fields, do not re-derive intent

Scenarios arrive with their outcome already decided. Honour it rather than
inferring it from the system's current behaviour.

| Scenario field | What to generate |
|---|---|
| `status: ready` | An ordinary test asserting the expected result |
| `status: known-defect`, `expectedOutcome: fail` | The same assertion, marked as an expected failure, with `defectRef` in a comment |
| `status: undecided` | **Nothing.** Skip it and list it in the report as blocked |

For an expected failure, use the strict form so a fix cannot pass unnoticed:

```ts
// Known defect Q-03 — API returns 200 and stores the record.
// Asserting the ticket's rule deliberately; do not relax. See scenario TC-013.
test.fail('TC-DEMO-1-API-013 registering without a name is rejected', async ({ api }) => {
  const res = await api.post('/items', { data: { imageUrls: ['https://example.invalid/p.png'] } });
  expect(res.status(), 'missing name should be rejected').toBe(400);
});
```

When `doNotRelax` is set, the assertion is deliberate and stays as written. If it
fails, that is the scenario working. Never adjust the expected value to match
observed behaviour, and never convert the test to `skip` — skipping loses the
signal that the defect still exists.

A scenario marked `undecided` that reaches you is an upstream error: report it back,
never fill the gap with a plausible assertion.

## Environments, performance, reports

- **Shared or foreign environment** (assume shared unless told otherwise): parse foreign records
  loosely and your own strictly, never assert length, order or absence in a shared collection. Timing assertions run in their
  own project with `workers: 1`. Read `references/environments-and-performance.md` for both.
- **`RUN_REPORT.md` (every condition to reproduce the run) and `TEST_CATALOGUE.md` (readable
  without TypeScript) are required outputs**: read `references/reports.md` first.

## Stability is measured, not felt

One green run proves nothing. Before reporting a suite as complete, run it at
least three times and report per-test failure frequency:

```bash
for i in 1 2 3; do npx playwright test --project=api --reporter=json \
  > "results/run-$i.json"; done
```

`3/3 green` and `2/3 green` are different levels of trust and must be visibly
different in the report. A test that failed once is a finding to investigate, not
noise to average away — and it will not get investigated if the report only shows
the last run.

## Self-check before reporting completion

Mechanically checkable. Run each; do not estimate.

1. **`npx tsc --noEmit` passes** with zero errors.
2. **`npx playwright test --list` discovers every generated test**, and the count
   matches the number of non-`undecided` scenarios.
3. **Every test has at least one assertion.** A test whose body contains no
   `expect` is a test that cannot fail.
4. **No `test.only`, no commented-out tests, no `waitForTimeout`.**
5. **Every expected failure fails for its own recorded reason.** Presence of
   `test.fail()` is not enough. Compare each one's actual failure against the
   scenario's `observedBehaviour`: same status code, same message. An expected
   failure that passes, or fails differently, is masking something — a 404 from a
   broken base URL satisfies "should be 4xx" and reports success. This gate is
   cheap to automate and catches the quietest class of error there is.
6. **No scenario marked `undecided` produced a test.** These are listed as blocked
   in the report instead.
7. **Every test title carries its scenario ID**, so a CI failure maps to a
   requirement without a lookup.
8. **No credential or environment-specific URL is hardcoded.** Grep for `http://`
   and `https://` outside config; each hit should be an env var.
9. **Every test that creates data cleans it up**, in a fixture teardown rather
   than at the end of the test body — a failing test skips its own last lines.
10. **`TRACEABILITY.json` was written** and every entry resolves to a real test.
11. **`TEST_CATALOGUE.md` was generated from the scenario JSON**, with one row per
    test and no rows for tests that do not exist.
12. **Timing tests run in their own project** and do not gate functional ones.
13. **The suite ran at least three times**, with per-test failure frequency in the
    report.

Report each gate's result. A suite that compiles but has three assertion-free
tests is not a passing run.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event run <API_TEST_DIR>/results/run-<n>.json` for every run of the
stability gate (Playwright JSON reporter).
