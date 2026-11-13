# Project shape, config, base URLs, the target repository

Read this when creating the test project or adding to one, and before writing the config or a client.

## Project shape

```
03-tests/api/
├── playwright.config.ts
├── src/
│   ├── clients/            Typed API clients, one per service
│   ├── schemas/            Zod schemas mirroring response contracts
│   ├── fixtures/           Auth, data provisioning, cleanup
│   └── types/
└── specs/
    └── <feature>/          Grouped by feature, never by ticket
        └── <area>.spec.ts
```

One project for every API test in the product. A new ticket adds spec files to
it — it never creates a second project. Ten tickets with ten Playwright configs
means ten sets of duplicated fixtures, ten things to upgrade, and no way to run
"the API regression" as one command.

Tests are filed by feature because they outlive the ticket that created them.
Traceability to the ticket lives in the test title and the scenario reference, not
in the path.

## Config baseline

```ts
export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['html'], ['junit', { outputFile: 'results/junit.xml' }], ['list']],
  use: {
    baseURL: process.env.API_BASE_URL,
    extraHTTPHeaders: { Accept: 'application/json' },
    trace: 'retain-on-failure',
  },
});
```

Keep retries at 1 in CI and no higher. Retries hide flakiness; a suite on three
retries is a suite whose failures nobody believes any more.

## The baseURL trap

`new URL(path, base)` discards the base path when the path starts with a slash.
This costs a full run the first time it happens, and the failure is disguised:

```
new URL('/items', 'https://h/api/v3')    -> https://h/items         base path lost
new URL('items',  'https://h/api/v3')    -> https://h/api/items     last segment lost
new URL('items',  'https://h/api/v3/')   -> https://h/api/v3/items  correct
```

So: **base URL ends with a slash, paths do not start with one.** Assert it in the
client constructor rather than hoping:

```ts
constructor(private readonly base: string) {
  if (!base.endsWith('/')) throw new Error('API_BASE_URL must end with "/"');
}
```

The reason this matters more than a typo normally would: every request returns
404, and a 404 satisfies a loose negative assertion. An expected failure written
as "should be 4xx" will report **"expected to fail, but passed"** — two tests
reporting a correct result for an entirely wrong reason. Assert the specific
status code, never a class.

## Read the target repo before generating

If `API_TESTS_REPO` already contains a framework, read it first: existing
fixtures, HTTP clients, helpers, tsconfig paths, lint rules, naming conventions.
Reuse what is there instead of generating a parallel set of helpers that does the
same thing slightly differently. A suite that matches the repo's existing patterns
survives review; one that looks foreign gets rewritten by the team.

Where the repo uses a different stack — the project profile's `API_TEST_STACK` is
`python-pytest` rather than `typescript-playwright` — keep every rule in this
skill and change only the syntax. The mapping is direct: `test()` becomes a
`test_` function, fixtures become pytest fixtures, Zod schemas become Pydantic
models, `expect(res.status())` becomes `assert response.status_code ==`, tags
become `@pytest.mark`, and `test.fail()` becomes `@pytest.mark.xfail(strict=True)`.
Strict xfail matters — without it a fixed defect goes unnoticed.
