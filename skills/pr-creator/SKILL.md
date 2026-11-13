---
name: pr-creator
description: Integrates a generated Playwright test project into the target automation repository and opens a pull request, resolving fixture conflicts, dependency mismatches, and config drift first. Use this skill as the final delivery stage of the QA pipeline, whenever the user wants generated tests merged into their repo, or whenever they ask to open a PR with new tests. Also use it to check whether a generated suite is compatible with an existing framework before attempting integration.
---

# MR Creator

Generated tests land in a repository that already has conventions, fixtures, and a
CI pipeline. Dropping files in and opening a PR that fails to compile wastes a
reviewer's afternoon and teaches the team to distrust the whole pipeline.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for the git host (`github`, `gitlab`, `bitbucket`): read `INTEGRATIONS`, skip a
system that is not listed, report it as `➖ <system> disabled for this project`, never route
around a `qa-guard` block.

**Local alternative:** run the compatibility analysis and validation as usual, commit on a local branch, and write the PR description to `PR_DESCRIPTION.md` in the test project. Never push. The engineer opens the PR, or enables the integration.

## Compatibility analysis first

Before copying a single file, compare the generated project against the target
repository and report conflicts:

| Check | What goes wrong |
|---|---|
| Fixture names | Generated `api` fixture collides with an existing one of different shape |
| Base classes / page objects | Target already has a `BasePage`; generated code has its own |
| Config | Target's `playwright.config.ts` defines projects, reporters, baseURL — generated config must merge, not replace |
| Dependencies | Version mismatch on `@playwright/test`, `zod`, `@axe-core/playwright` |
| Env vars | Names differ (`API_BASE_URL` vs `BASE_API_URL`) |
| tsconfig | Path aliases, `strict` mode, target ES version |
| Lint rules | Target ESLint config may reject patterns the generator produced |
| Directory convention | Target uses `e2e/` not `03-tests/ui/<target>/` |

Adapt the generated code to the target's conventions. The repository's existing
patterns win — a suite that looks foreign gets rewritten by the team anyway.

## Validate before pushing

Run in the target repo, with the generated tests in place:

```bash
npm ci
npx tsc --noEmit
npx eslint .
npx playwright test --list        # tests are discoverable and collide with nothing
npx playwright test --grep @smoke # the fast subset actually passes
```

A PR that does not compile should never be opened. If validation fails and cannot
be resolved automatically, stop, report, and leave the branch unpushed.

## Branch and PR

Branch: `qa/<TICKET-ID>-<short-slug>`, e.g. `qa/DEVAI-283-confluence-connect`.

PR description template:

```markdown
## Automated tests for DEVAI-283 — Connect a Confluence workspace

**Scope**: 22 API tests, 16 UI tests
**Coverage**: 12 of 12 functional requirements, 3 of 4 non-functional
**Scenario ↔ code match**: 92%

### Known defects — tests marked test.fail()
- DEVAI-301 — domain length validation missing (TC-283-API-011)
- DEVAI-302 — duplicate connect returns 500 instead of 409 (TC-283-API-014)

### Not covered
- NF-DEVAI-283-FE-02 — load behaviour above 500 concurrent users; needs a k6 suite

### Needs review from the team
- Requested `data-testid="integration-card"` on IntegrationCard.tsx:24 —
  currently located by scoped CSS, which will break on restyling

### How to run
`npm run test:api -- --grep @smoke` · `npm run test:ui`
TMS cases: Zephyr folder Integrations / Confluence / DEVAI-283
```

Reviewers care most about what is *not* covered and what needs their action. Put
those above the statistics.

## Idempotency

If the branch already exists, update it incrementally: fetch, rebase onto the
target branch, apply only changed files, amend the PR description. Do not force
push over review commits — a reviewer's fix disappearing is a fast way to lose
the team's cooperation.

## Permission boundary

Opening a pull request is a visible action on a shared repository. Confirm with
the engineer before pushing the branch and before opening the PR, and never merge
it — approval and merge are human decisions.
