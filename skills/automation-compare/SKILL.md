---
name: automation-compare
description: Verifies that generated Playwright tests actually implement the scenarios they claim to, step by step, and reports a match percentage plus a regenerated requirements traceability matrix. Use this skill after automation code is generated or changed, whenever the user asks what the automated suite really covers, whenever test cases in the TMS and the code have drifted apart, or before uploading cases to a TMS. Also use it to audit an inherited suite whose coverage nobody can vouch for.
---

# Automation Compare

The classic decay: test cases live in the TMS, tests live in the repo, and after
three sprints nobody knows which describes reality. This skill is the guard
against that drift — scenario JSON is the source of truth, and code is checked
back against it.

## What to compare

For every test case in the scenario JSON, locate its implementation (by scenario
ID in the test title) and check, step by step:

| Scenario element | Check against code |
|---|---|
| Preconditions | Present as fixture, setup call, or `beforeEach` |
| Each step's action | The corresponding request or interaction exists, same method/endpoint/element |
| Each step's input data | Same values, or a documented equivalent (env var, fixture) |
| Each step's expected result | A real assertion exists for it — not an adjacent one |
| Postconditions | Verified, or explicitly waived with a reason |
| Priority | Reflected in the tag (`@smoke` for HIGH) |

An expected result with no corresponding assertion is the most common and most
consequential gap: the step executes, nothing is checked, the test passes forever.

## Scoring

```
step coverage   = asserted steps / total steps
case coverage   = implemented cases / total cases
suite match     = weighted mean, HIGH priority cases weighted 2×
```

Report per suite and overall. Below 90% suite match, hand the gaps back to the
automation skill for a targeted regeneration pass rather than a full rewrite —
regenerating everything discards the debugging work already invested.

## Report

`COMPARISON_REPORT.md`:

```markdown
# Scenario ↔ code comparison — DEVAI-283

Suite match: 92% (api 96%, ui 87%)

## Fully implemented — 33 of 38

## Partially implemented — 4
- **TC-283-UI-009** (step 3) — scenario expects "the folder disappears from the list";
  code asserts only that the dialog closed. Missing assertion on list state.
- **TC-283-API-014** (postcondition) — duplicate integration not verified absent after 409.

## Not implemented — 1
- **TC-283-UI-016** — keyboard-only navigation through the form. No test found.

## In code but not in scenarios — 2
- `integrations.spec.ts:112` "handles empty response" — undocumented.
  Either add a scenario for it or remove it; untraced tests cannot be defended.
```

That last section matters as much as the others. Tests that exist without a
scenario are invisible to the TMS, to the RTM, and to anyone deciding whether a
release is safe.

## Regenerate the RTM

Recompute requirement coverage from the *code side* this time, not the scenario
side, and diff against the scenario-side RTM. A requirement that reads "Covered"
in the scenario RTM but has no asserting test is exactly the blind spot this
pipeline exists to eliminate.

```markdown
| Requirement       | Scenarios | Implemented | Asserted | Real coverage |
|-------------------|-----------|-------------|----------|---------------|
| F-DEVAI-283-BE-01 | 4         | 4           | 4        | 100%          |
| F-DEVAI-283-FE-03 | 2         | 2           | 1        | 50%  ⚠        |
| NF-DEVAI-283-FE-01| 1         | 0           | 0        | 0%   ⚠        |
```

## Feeding fixes back

Emit a machine-readable `GAPS.json` listing each gap with its scenario ID, step
number, and gap type, so `automation-api` and `automation-ui` can patch precisely
what is missing. Then re-run compare — the loop closes when the score clears the
threshold or the remaining gaps are explicitly accepted by the engineer.

## Self-check before reporting completion

1. **Every scenario in the suite was looked for in the code**, including ones
   expected to fail — an absent expected-failure test is a silent coverage loss.
2. **Every expected result was checked for a corresponding assertion**, not merely
   for a corresponding step. A step that executes without asserting is the most
   common and most consequential gap.
3. **Tests present in code but absent from scenarios are listed.** Untraceable
   tests cannot be defended in a release review.
4. **The code-side RTM was computed from the code**, and diffed against the
   scenario-side RTM rather than copied from it.
5. **`GAPS.json` was written** and every entry names a scenario ID and step
   number precise enough to patch without re-analysis.
6. **The match score is weighted as documented**, not an unweighted mean.

Report each gate's result.
