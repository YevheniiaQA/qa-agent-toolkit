---
name: scenario-data-fix
description: Resolves missing test data placeholders in generated scenarios by looking them up in the project global context first and asking the engineer only for what genuinely cannot be derived. Use this skill whenever scenarios contain unresolved data placeholders, whenever the user asks what test data a feature needs, whenever tests fail because of missing users, tokens, or seed records, or before generating automation code from scenarios. Supports an auto mode that resolves everything derivable and batches the remainder into a single question list.
---

# Scenario Data Fix

Scenarios written with invented data compile into tests that fail for reasons
unrelated to the feature. This skill closes the gap between "a scenario that
reads well" and "a scenario that can actually run".

## Two placeholder categories

`scenarios-generator` emits two kinds, and they are resolved differently.

**`{{TEST_DATA: key}}`** — static data that should already exist. This skill
resolves it by lookup, following the order below, and asks the engineer for
whatever remains.

**`{{GENERATED: key}}`** — values created fresh on each run. **These are not
yours to resolve.** Do not look them up, do not substitute a fixed value, and do
not ask the engineer for one. Verify instead that each carries a complete
generation rule — `rule`, `scope`, `reuse`, and `cleanup` where it creates data —
and pass it through untouched for the automation stage to implement as a fixture.

A `{{GENERATED: ...}}` placeholder that has been replaced with a concrete value is
a bug: it turns a per-run unique value into a shared constant, and the suite will
pass serially and collide under parallel workers.

If a placeholder uses neither notation, that is an upstream gap. Report it rather
than inventing a third convention.

## Resolution order

Work through sources in this order and stop at the first that answers:

1. **Global context** — `01-docs/context/test-data.yaml` and
   `environments.yaml`. Existing test users, tenants, tokens, seed records.
2. **Derivable from contracts** — if the API spec constrains a field
   (`min: 8`, `format: email`, enum values), generate a conforming value and
   record how it was derived.
3. **Derivable from the design** — texts and limits captured in `FIGMA_DATA.json`.
4. **Generatable at runtime** — data the test can create in a fixture (a new user,
   a new workspace). Prefer this over static data wherever the API allows it;
   self-provisioned data is what makes a suite runnable in parallel and in CI.
5. **Ask the engineer** — only what remains.

## Auto mode

In `--auto`, resolve everything from sources 1-4 without interruption, then
present the remainder as one consolidated list rather than a stream of questions.
Interrupting an engineer eleven times costs more than the data is worth.

```markdown
## Test data needed for DEVAI-283 — 3 items

1. **Valid Confluence API token** for the staging workspace
   - Used by: TC-283-API-001, TC-283-API-004, TC-283-UI-002
   - Proposed: store in CI secret `CONFLUENCE_TOKEN_STAGING`, read via env
2. **A workspace that already has an integration** (for the 409 case)
   - Proposed: create in fixture via POST, then assert the duplicate attempt
3. **A user without `integrations:write` scope** (for the 403 case)
   - Not found in test-data.yaml — does such a role exist?
```

## Secrets rule

Never write credentials, tokens, or personal data into scenario JSON, test code,
or any committed file. Reference an environment variable name and record it in
`environments.yaml`. When the engineer supplies a secret in conversation, use the
variable reference in the artefacts and tell them where to set the real value —
do not paste it into a file.

## Prefer fixtures over fixed data

Static seeded records rot: another test mutates them, a reset wipes them, two
parallel workers collide on them. The healthier pattern in a TypeScript/Playwright
project is a fixture that provisions what the test needs and cleans up after:

```ts
export const test = base.extend<{ connectedWorkspace: Workspace }>({
  connectedWorkspace: async ({ api }, use) => {
    const ws = await api.createWorkspace({ name: `qa-${randomUUID()}` });
    await api.connectConfluence(ws.id);
    await use(ws);
    await api.deleteWorkspace(ws.id);
  },
});
```

Flag scenarios that depend on shared mutable state as a risk in the output — they
are the seed of the flakiness that shows up three sprints later.

## Output

Update the scenario JSON files in place, replacing placeholders with either a
concrete value, an env-var reference, or a fixture reference. Write a summary to
`02-analysis/<TICKET-ID>/scenarios/DATA_RESOLUTION.md` recording what was resolved,
from which source, and what is still outstanding. Idempotent: re-running skips
already-resolved placeholders.
