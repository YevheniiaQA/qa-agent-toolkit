---
name: selectors-collector
description: Collects and validates resilient Playwright locators from the live DOM and emits a typed page-object map for UI test generation. Use this skill before generating any Playwright UI tests, whenever UI tests break because selectors changed, whenever the user asks how to target an element reliably, or when a test uses brittle CSS or XPath that should be replaced. Also use it to audit an existing suite for fragile locator patterns and to identify where test IDs should be added to the application.
---

# Selectors Collector

Locator quality determines suite lifespan. A suite built on CSS paths dies at the
next refactor; a suite built on roles and test IDs survives redesigns.

## Locator priority

Use the first strategy that uniquely identifies the element:

1. **`getByTestId`** — `data-testid` on elements the tests depend on. The only
   locator the application explicitly promises to keep stable.
2. **`getByRole` with an accessible name** — `getByRole('button', { name: 'Connect' })`.
   Doubles as an accessibility assertion: if this locator cannot find the element,
   a screen reader user cannot find it either.
3. **`getByLabel`** for form controls — likewise ties the test to a real
   accessibility contract.
4. **`getByPlaceholder` / `getByText`** — acceptable when the copy is stable and
   the app is single-locale.
5. **CSS scoped to a semantic container** — a last resort, and only with a comment
   explaining why nothing better was available.

Never generate: absolute XPath, `nth-child` chains, class names that look
generated (`css-1x2y3z`, Tailwind utility stacks), or text matching against copy
that the design marks as provisional.

## Never anchor on visible text in a localised application

Check the rendered language before writing a single locator. `<html lang="ru">`
means every text-based locator you write from an English mental model will match
nothing — and the failure is silent in the worst way: a negative assertion passes
because the element was never found.

This is not hypothetical. A validation check written against "Username and
password do not match" finds nothing on a screen reading
«Имя пользователя и пароль не совпадают», and a `toBeHidden()` assertion on that
locator passes while the error is plainly displayed.

Rules:

- **Read `document.documentElement.lang` and record it** in `SELECTORS.json`
  before collecting anything. If it is not the language you assumed, stop and say so.
- **Locators use `data-testid`, ARIA role, or structure** — never the visible
  string, in any language. `getByRole('button', { name: … })` is also
  text-dependent when the accessible name comes from visible copy; prefer a test
  id where the interface is localised or the copy is still in flux.
- **Where the assertion genuinely is about the text** — an error message, a
  confirmation — put the expected string in a locale fixture keyed by language,
  never inline in the test. Then a second locale is a data change, not a rewrite.
- **Verify every locator against the live DOM in the language the tests will run
  in.** A locator validated against an English build proves nothing about a
  Russian one.

Record the interface language in the report. Nobody reading a failing suite
thinks to check it, and it explains a whole class of failures at once.

## Session authentication

Where the application uses session cookies rather than a token header, capture
the session once and reuse it — but treat it as perishable, because it is.

```ts
// global.setup.ts — runs once, before every project that depends on it
await page.goto(process.env.ADMIN_BASE_URL + '/login');
await page.getByTestId('login-username').fill(process.env.ADMIN_USER!);
await page.getByTestId('login-password').fill(process.env.ADMIN_PASSWORD!);
await page.getByTestId('login-submit').click();
await page.waitForURL('**/dashboard');
await page.context().storageState({ path: '.auth/admin.json' });
```

**Sessions expire, and a long run will cross the boundary.** A two-hour session
against a suite that takes ninety minutes fails somewhere in the middle, and the
failure looks exactly like flakiness: some tests pass, later ones do not, and a
re-run "fixes" it. Defend against this explicitly:

- **Record the session's lifetime** in the project profile
  (`SESSION_TTL_MINUTES`) and the capture timestamp alongside the state file.
- **Check freshness before the run.** If the state is older than half the
  lifetime, re-authenticate rather than hoping. Half, not all — a run that starts
  at 110 minutes into a 120-minute session will still fail.
- **Fail loudly on an expired session.** A redirect to the login page must
  produce a clear error naming session expiry, not a cascade of element-not-found
  failures that someone spends an afternoon debugging.
- **Never commit `storageState`.** It contains a live session cookie for a real
  account. Add `.auth/` to `.gitignore` in the generated project, and say so in
  the README you produce. This is the same class of mistake as committing a token.

Where several targets need different sessions — a public site and an admin panel,
or two roles — capture one state file per target and name them by target and role:
`.auth/admin-superuser.json`, `.auth/landing-anonymous.json`.

## When nothing stable exists

Do not invent a fragile locator to unblock generation. Record the gap:

```markdown
## Test ID requests for DEVAI-283
- Integration card container — no role, no stable text (cards are user-named)
  - Proposed: `data-testid="integration-card"` with `data-integration-id={id}`
  - Blocks: TC-283-UI-004, TC-283-UI-007
  - File: src/components/IntegrationCard.tsx:24
```

Sending this list to the developers is normal, healthy QA work and usually takes
them minutes. It is a far better outcome than a suite that goes red every sprint.

## Validation, not just collection

A collected locator is a hypothesis until it resolves against the live DOM. For
each locator:
- assert it resolves to exactly one element (strict mode catches this)
- record the resolved accessible name and role
- mark `validated: true` with a timestamp

Re-running the skill revalidates and updates only locators that now fail — do not
churn entries that still resolve.

## Output

`03-tests/ui/<target>/src/pages/<feature>.ts` — typed, not JSON, so the compiler catches
renames:

```ts
import { type Page, type Locator } from '@playwright/test';

export class ConnectConfluencePage {
  readonly url: Locator;
  readonly token: Locator;
  readonly connect: Locator;
  readonly error: Locator;

  constructor(private readonly page: Page) {
    this.url = page.getByLabel('Confluence URL');
    this.token = page.getByLabel('API token');
    this.connect = page.getByRole('button', { name: 'Connect' });
    this.error = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/settings/integrations');
  }

  async connectWith(url: string, token: string) {
    await this.url.fill(url);
    await this.token.fill(token);
    await this.connect.click();
  }
}
```

Alongside it write `SELECTORS.json` with validation metadata (locator strategy,
resolved role and name, validation timestamp, source file) so `automation-ui` and
future refresh runs can reason about them.

## Page object discipline

Page objects hold locators and low-level interactions. They hold no assertions
and no test logic — assertions belong in the test, where the failure message can
name the requirement being violated. A page object with `expect` inside it makes
every failure look the same.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event counts selectors-collector locators=<n> validated=<n> blocked=<n>
failed=<n> testids=<n> --suite <target> --source <the selector map you wrote>`.

