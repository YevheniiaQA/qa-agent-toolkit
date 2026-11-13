---
name: automation-ui
description: Generates a runnable TypeScript Playwright UI test project from scenario JSON and validated page objects, with API-based setup, web-first assertions, accessibility checks, and requirement traceability. Use this skill whenever the user wants UI or end-to-end tests automated, whenever UI scenarios and selectors are ready, whenever they ask for Playwright browser tests, or as the UI branch of the QA pipeline. Also use it to rewrite an existing flaky UI suite onto stable patterns.
---

# Automation UI (TypeScript + Playwright)

UI tests fail for two reasons: the feature broke, or the test was written badly.
The entire craft is minimising the second category, because a suite that cries
wolf stops being read.

## Project shape

```
03-tests/ui/<target>/
├── playwright.config.ts
├── src/
│   ├── pages/              Page objects from selectors-collector
│   ├── fixtures/           Auth state, seeded data, page object injection
│   └── helpers/
└── specs/
    └── <feature>/
        └── <area>.spec.ts

One project per UI **target**, not per ticket. An admin panel and a public site
differ in base URL, authentication and page objects, so each gets its own project
under `03-tests/ui/<target>/`. Every ticket touching the admin panel adds specs to
`03-tests/ui/admin/` — never a new project.
```

## Non-negotiable patterns

**Set up through the API, assert through the UI.** Logging in via the form in
every test is slow and turns one broken login into a hundred red tests. Use
`storageState` for authentication and API calls for data provisioning; reserve UI
interaction for the thing under test.

```ts
// playwright.config.ts — auth once, reuse everywhere
projects: [
  { name: 'setup', testMatch: /global\.setup\.ts/ },
  { name: 'chromium', use: { ...devices['Desktop Chrome'], storageState: 'state.json' },
    dependencies: ['setup'] },
]
```

**Web-first assertions only.** `await expect(locator).toBeVisible()` retries until
the timeout; `expect(await locator.isVisible()).toBe(true)` samples once and is
the single largest source of flakiness in generated suites.

**Never `waitForTimeout`.** Wait for the condition that actually matters: a
response, a URL, an element state. A hardcoded sleep is either too short (flaky)
or too long (slow), and usually both across a suite.

```ts
// wait for the thing, not for the clock
const connect = page.waitForResponse(r =>
  r.url().includes('/integrations/confluence/connect') && r.request().method() === 'POST');
await connectPage.connectWith(url, token);
await connect;
await expect(page.getByText('Connected')).toBeVisible();
```

**One user-visible outcome per test.** A test that walks through six screens
reports "something in the flow broke" — which is barely more useful than a user
complaint. Keep the arc short and the failure diagnostic.

**No test depends on another test's state.** Playwright parallelises by file;
order-dependent tests fail in CI and pass locally, which is the worst failure mode
to debug.

## Generated test shape

```ts
import { test, expect } from '../src/fixtures';

test.describe('US-001 Connect a Confluence workspace', () => {
  test('TC-283-UI-002 shows an inline error for invalid credentials @regression',
    async ({ connectPage, page }) => {
      await connectPage.goto();
      await connectPage.connectWith('https://acme.atlassian.net', 'wrong-token');

      await expect(connectPage.error).toBeVisible();
      await expect(connectPage.error).toHaveText('Invalid credentials');
      await expect(page.getByText('Connected')).toBeHidden();
    });

  test('TC-283-UI-005 keeps the connect button disabled until both fields are filled',
    async ({ connectPage }) => {
      await connectPage.goto();
      await expect(connectPage.connect).toBeDisabled();

      await connectPage.url.fill('https://acme.atlassian.net');
      await expect(connectPage.connect).toBeDisabled();

      await connectPage.token.fill('valid-token');
      await expect(connectPage.connect).toBeEnabled();
    });
});
```

Note the distinction the design analysis produced: `toBeDisabled` and `toBeHidden`
are different assertions describing different product behaviour. Getting this
wrong means the test passes while the UI is wrong.

## Accessibility coverage

Where a non-functional accessibility requirement exists, generate a real check
rather than a comment:

```ts
import AxeBuilder from '@axe-core/playwright';

test('NF-283-FE-01 integrations page has no serious accessibility violations', async ({ page }) => {
  await page.goto('/settings/integrations');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();
  const serious = results.violations.filter(v => ['serious', 'critical'].includes(v.impact ?? ''));
  expect(serious, JSON.stringify(serious.map(v => v.id))).toEqual([]);
});
```

Keyboard operability deserves its own explicit test — `page.keyboard.press('Tab')`
through the form and assert focus order, because axe cannot detect a focus trap.

## Visual regression, used sparingly

Screenshot assertions catch layout regressions no functional test will, and they
also produce the most false failures of anything in a suite. Apply them to a small
set of stable, high-value views, mask dynamic regions, and never snapshot a whole
page containing timestamps or user-generated content.

```ts
await expect(page).toHaveScreenshot('integrations-empty.png', {
  mask: [page.getByTestId('last-synced-at')],
  maxDiffPixelRatio: 0.01,
});
```

## Config baseline

```ts
export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['html'], ['junit', { outputFile: 'results/junit.xml' }]],
  use: {
    baseURL: process.env.UI_BASE_URL,
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
});
```

Traces are what make a CI failure debuggable without reproducing it locally — keep
them on, always.

## Traceability

Same contract as the API skill: scenario ID in every test title, requirement map
in `TRACEABILITY.json`, suite title naming the story.

## Read the target repo before generating

If `UI_TESTS_REPO` already has a framework, read its page objects, fixtures, auth
setup, and config before writing anything. Extend the existing base classes rather
than introducing a second hierarchy. Two competing page-object patterns in one
repo is a maintenance problem that outlives whoever created it.

For a `python-pytest` target, the same rules apply with
`playwright.sync_api` / `pytest-playwright`: `expect(locator).to_be_visible()`
is still the web-first assertion, `page.wait_for_timeout` is still banned,
`storageState` still handles authentication, and `@pytest.mark.xfail(strict=True)`
replaces `test.fail()`.

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

A scenario marked `undecided` that reaches you anyway is an upstream error. Do
not fill in the gap with a plausible assertion; report it back.

## Self-check before reporting completion

1. **`npx tsc --noEmit` passes.**
2. **Every test discovered by `--list`**, count matching the non-`undecided`
   scenarios.
3. **Every test has at least one web-first assertion** (`await expect(locator)`),
   not a sampled boolean.
4. **No `waitForTimeout`, no `test.only`, no commented-out tests.**
5. **No locator uses absolute XPath, `nth-child` chains, or generated class
   names.** Grep for these patterns directly.
6. **Authentication happens through `storageState`**, not through the login form
   in each test.
7. **Data setup happens through the API**, not through UI interaction, except
   where the setup itself is what is under test.
8. **Expected failures are strict and carry their `defectRef`.**
9. **Every test title carries its scenario ID.**
10. **Every test that creates data cleans it up in teardown.**

Report each gate's result.

## Sessions and non-production data

**Session freshness is checked, not assumed.** Where authentication is
cookie-based, verify the stored state before the run and re-authenticate when it
is past half its lifetime. An expired session mid-run produces failures that look
like flakiness and waste an afternoon each time. Fail with a message naming
session expiry rather than letting element-not-found errors cascade.

**`storageState` never enters the repository.** It holds a live session for a real
account. `.auth/` goes in `.gitignore`, and the generated README says why.

**On a client or company non-production environment, default to read-only.**
A public demo API is a sandbox nobody owns; a staging environment is someone's working
system, with data other people depend on that day. Before generating any test
that creates, modifies or deletes a record:

- prefer assertions against data that already exists
- where a test must create data, it must clean up in fixture teardown, use an
  unmistakably synthetic name with a run-scoped prefix, and be listed in the
  report as a writing test
- deleting data the test did not create requires explicit approval, asked for in
  chat, naming what would be deleted

A destructive test against a shared non-production environment can block a team
for a day. The cost is not symmetric with the value of the extra coverage.

## Shared environments, stability, and the catalogue

The same three rules as the API skill, and they matter more here because UI tests
are slower and flakier by nature.

**Assume the environment is shared.** Never assert on list length, ordering, or
the absence of elements you did not create. Scope every assertion to a record
identified by a run-scoped name or test id.

**Clean up in fixture teardown**, never at the end of the test body — a failing
test never reaches its last lines.

**Run the suite at least three times before reporting it complete**, and report
per-test failure frequency. `2/3 green` is a finding, not noise. UI suites that
are declared stable after one run are the single most common source of a suite
nobody trusts six weeks later.

**Generate `TEST_CATALOGUE.md`** alongside the code: one row per test with what it
does, the data, the expected result, the requirement, and whether it is an
expected failure. A manual tester should be able to execute any row by hand.

Timing assertions, if any, live in their own project with `workers: 1` and never
gate functional results.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event run <UI_TEST_DIR>/results/run-<n>.json` for every run of the
stability gate (Playwright JSON reporter).

