---
name: ci-setup
description: Creates or repairs GitHub Actions workflows that run the generated Playwright suites, publish reports, and push results back to TestRail. Use this skill when a test repository has no CI, when the user asks to run tests on every pull request or nightly, when CI is failing for environment or secret reasons, or as the step after the first test PR is merged. Also use it to split a slow suite into a fast smoke gate and a full nightly run.
---

# CI Setup (GitHub Actions)

Tests that only run on someone's laptop stop running. CI is what turns a generated
suite into a standing safety net.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for the CI host (`github`) and the TMS it reports to: read `INTEGRATIONS`, skip a
system that is not listed, report it as `➖ <system> disabled for this project`, never route
around a `qa-guard` block.

**Local alternative:** write the workflow files into the repository and validate them locally (`actionlint` where available). Do not push, create secrets or call the API. A results-publishing step for a TMS that is disabled stays out of the workflow.

## The two-tier pattern

One workflow is the wrong shape. Split by purpose:

| Workflow | Trigger | Scope | Target duration |
|---|---|---|---|
| Smoke gate | Pull request, push to main | `@smoke` tag only | under 5 minutes |
| Full regression | Nightly schedule, manual dispatch | Everything | however long it takes |

A suite that adds ten minutes to every pull request gets disabled within a month.
A five-minute gate plus a nightly full run keeps both the feedback loop and the
coverage.

## Smoke gate workflow

```yaml
name: QA smoke
on:
  pull_request:
  push: { branches: [main] }

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npx playwright test --grep @smoke
        env:
          API_BASE_URL: ${{ vars.API_BASE_URL }}
          UI_BASE_URL: ${{ vars.UI_BASE_URL }}
          QA_ADMIN_PASSWORD: ${{ secrets.QA_ADMIN_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

`if: ${{ !cancelled() }}` on the report upload is the detail people forget — when
the run fails, which is exactly when the report matters, the default `on: success`
throws it away.

## Full regression workflow

Add sharding once the suite is long enough to need it:

```yaml
on:
  schedule: [{ cron: '0 2 * * 1-5' }]
  workflow_dispatch:

jobs:
  regression:
    strategy:
      fail-fast: false
      matrix: { shard: [1, 2, 3, 4] }
    steps:
      - run: npx playwright test --shard=${{ matrix.shard }}/4
```

`fail-fast: false` matters: one shard failing should not cancel the other three
and hide the rest of the results.

## Secrets and variables

Non-secret configuration (base URLs, environment names) goes in repository
*variables*; credentials go in *secrets*. Keep the names identical to the local
`.env` so a test that runs locally runs in CI unchanged — mismatched variable
names between local and CI is the most common cause of "it works on my machine"
in generated suites.

Never write a secret into a workflow file, a report, or a log line. When a test
needs to log a request for debugging, redact `authorization` and `cookie` headers.

## Publishing results to TestRail

After the run, push results back so the TMS reflects reality without anyone
updating it by hand. The mapping comes from `TMS_MAPPING.json`, produced by
`tms-uploader`:

```yaml
      - name: Publish results to TestRail
        if: ${{ !cancelled() }}
        run: node scripts/publish-testrail.mjs results/junit.xml
        env:
          TESTRAIL_TOKEN: ${{ secrets.TESTRAIL_TOKEN }}
```

Create a run per CI execution rather than overwriting one — execution history is
the evidence trail, and overwriting it destroys the thing the TMS is for.

## Environment gating

Test environments get deployed to, and a suite running mid-deploy produces
failures that mean nothing. Where the team has a deployment schedule, schedule the
nightly run outside it, and add a health check as the first step so the run fails
fast with a clear message instead of producing forty confusing failures:

```yaml
      - name: Check environment
        run: curl --fail --max-time 10 "$API_BASE_URL/health"
```

## Flakiness visibility

Keep retries at 1. Then surface what retried — a test that passes only on retry is
a defect in the test, and without a report nobody ever fixes it. Publish the
retry count weekly alongside the pass rate; a suite where the retry count is
climbing is a suite on its way to being ignored.
