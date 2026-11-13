---
name: manual-test-cases
description: Writes manual test cases in the field structure test management systems expect, and exports them as CSV or XLSX ready to import into TestRail, Xray, Zephyr Scale, qTest or Azure Test Plans. Use this skill whenever the user asks for manual test cases, a test case document, cases to import into a TMS, or cases for a tester who will execute them by hand. Also use it when a feature needs manual coverage before or instead of automation, when converting scenarios or an API specification into executable cases, and when existing cases need restructuring to import cleanly.
---

# Manual Test Cases

A manual test case is written for a person who has never seen the feature,
executing it under time pressure, who must be able to say "pass" or "fail"
without asking anyone a question. Everything below follows from that.

This skill produces two things: a readable document, and an import file whose
columns match the target TMS. Both come from the same source, so they cannot
disagree.

## Manual cases are a peer of automation, not a by-product

Write these in the design phase, alongside the automated suites — not afterwards
as an export of what was automated. Three reasons this ordering matters:

- A manual tester usually needs cases **before** automation exists, and on many
  projects automation never arrives at all
- Cases derived from automated code inherit its shape, and automated tests skip
  things a human should check: layout, wording, perceived speed, whether the flow
  makes sense
- `manual-test-cases`, `automation-api` and `automation-ui` are three **projections
  of the same scenario JSON**. None of them is the source for the others, and
  deriving one from another is how they drift

Generate manual cases for everything, then mark which are automated. A case
covered by automation stays in the catalogue with `Automation status: Automated`
— it is still the documentation of what is verified, and it is what somebody
executes when the suite is unavailable or the result is disputed.

## Where the content comes from

In order of preference. Use the highest available and say which you used.

1. **Scenario JSON** from `scenarios-generator` — already has steps, data,
   expected results, traceability and defect references. Convert, do not rewrite.
2. **Decomposed requirements** — acceptance criteria become cases directly.
3. **The global context** — business specification for flows and roles, API
   specification for endpoints, request shapes and error codes, database schema
   for constraints and boundaries.
4. **The ticket alone** — workable, but say so in the output, because coverage
   derived from a ticket without a contract will have gaps nobody can see.

Never invent a value, a limit, an error message or a status code. If the source
does not state it, the case says what to observe and a question goes to the
analyst — the same rule the decomposer follows, and for the same reason.

## Field structure

Every major TMS uses a variation of this set. Produce all of it; mapping to a
specific tool happens at export.

| Field | Rule |
|---|---|
| **ID** | Stable, external, never renumbered. `TC-<TICKET>-<LAYER>-<NN>` |
| **Title** | Action and expected outcome in one line. "Register an item without a name is rejected", not "Negative test 3" |
| **Section / suite** | Three levels: `Product / Feature / Sub-feature`. Agreed with the team before the first import |
| **Type** | Functional, Regression, Smoke, Security, Usability, Performance, Compatibility, Accessibility |
| **Priority** | Critical, High, Medium, Low — from business impact, not from how hard the case was to write |
| **Preconditions** | System state and data that must exist before step 1. One per line |
| **Steps** | Numbered. One action each. See below |
| **Test data** | Concrete values, or a named reference for secrets |
| **Expected result** | Per step, and an overall result for the case |
| **Postconditions** | What must be true afterwards, including cleanup |
| **Automation status** | Not automated, Automated, To be automated |
| **References** | Requirement IDs, ticket key, defect ID |
| **Estimate** | Execution time in minutes — capacity planning needs it |
| **Labels** | `api`, `ui`, `boundary`, `negative`, `known-defect` |

## Writing the steps

**One action per step.** "Open the form, fill in the name and submit" is three
steps. A tester who fails at the second cannot report which one broke.

**Every step has its own expected result**, or explicitly none. A step with no
observable outcome is setup and belongs in preconditions.

**Concrete data, never descriptive.** Not "enter a valid email" — `qa.test@example.com`.
Not "a long name" — `51 characters: aaa…a`. The tester should not be making
decisions that change what the case verifies.

**Expected results are observable and unambiguous.** "The system works correctly"
cannot be judged. "An inline error appears under the Name field reading *Name is
required*, and the record is not created" can.

**No implied knowledge.** "Log in as admin" assumes the tester knows which admin,
where, and with what password. Put the account in preconditions with a reference
to where the credentials live.

**Say where to look.** A message in a toast, in a field, on a new page and in a
log are four different results. Name the location.

```markdown
| # | Step | Test data | Expected result |
|---|---|---|---|
| 1 | Open Settings → Integrations | — | The Integrations page loads and shows the Connect button |
| 2 | Click Connect Confluence | — | A dialog opens with URL and API token fields, and a disabled Connect button |
| 3 | Enter the workspace URL | `https://acme.atlassian.net` | The field accepts the value; the button stays disabled |
| 4 | Enter the API token | `{{TEST_DATA: confluence_token_valid}}` | The Connect button becomes enabled |
| 5 | Click Connect | — | The dialog closes within 3 seconds and the workspace appears in the list with status Connected |
```

## Cases for known defects

A case covering behaviour the system currently gets wrong still belongs in the
TMS. It states the **required** behaviour, carries the defect ID in References,
and is labelled `known-defect`.

Do not rewrite it to match what the system does today. A case that documents a
bug as expected behaviour is how a defect becomes a requirement, and it is much
harder to undo than to prevent. Add a note in the case so an executing tester is
not surprised:

> Known defect DEF-DEMO-01 — the system currently returns 200 and stores the
> record. This case is expected to fail until the defect is resolved.

## Coverage

Derive from acceptance criteria first, then add what criteria routinely omit:

- one positive case per criterion
- one negative case per distinct failure mode
- boundary cases for every bounded input, sourced from the spec or schema
- authorisation cases wherever a permission boundary exists
- state-dependent cases: empty state, first item, maximum items
- interruption cases: browser back after submit, double submission, session
  expiry mid-flow
- read-back cases wherever a write is validated differently from a read

Mark each case with the technique that produced it. It tells a reviewer whether
coverage is adequate rather than merely plentiful.

## Export

Write both files to `03-tests/manual/<feature>/` — by feature, not by ticket,
because cases outlive the ticket and become regression:

- `TEST_CASES.md` — the readable document, tables as above
- `TEST_CASES.csv` — import file for the target TMS

See `formats.md` in this skill folder for the exact column names and the
multi-row step convention each system expects. Two rules apply everywhere:

**Steps use one row per step**, with the case-level fields on the first row and
blank on continuation rows. Every major TMS reads this shape; a single cell
containing all steps imports as one unreadable block.

**UTF-8 with BOM**, comma-separated, all fields quoted. Without the BOM, Excel
mangles non-ASCII on open, and the person importing will not realise until the
cases are already in the system.

An acceptance criterion that deliberately gets no manual case (covered only by an
automated contract check, or not executable by hand) is listed in `TEST_CASES.md` under
`## Not covered manually`, one line each: `- AC-<id>: <reason>`. `qa-gate manual <TICKET>`
counts those as waived; any other criterion without a case fails gate 2M.

Never put a credential in the CSV. Use the `{{TEST_DATA: key}}` reference and
record where the value lives in the preconditions.

## Self-check before reporting completion

1. **Every acceptance criterion maps to at least one case.**
2. **Every case has an ID, a section, a priority, and at least one reference.**
3. **No step contains more than one action.** Scan for "and" and "then".
4. **No expected result is unobservable.** Scan for "works", "correctly",
   "successfully", "as expected".
5. **No test data is descriptive rather than concrete**, except `{{TEST_DATA:}}`
   references.
6. **No credential appears in any file.**
7. **Every known-defect case states the required behaviour**, not the observed
   behaviour, and carries its defect ID.
8. **The CSV parses**: consistent column count on every row, quoting correct,
   BOM present. Re-read the file you wrote rather than assuming.
9. **Section paths match the agreed hierarchy** — check against the working
   agreement before exporting.
10. **Every case could be executed by someone who has never seen the feature.**
    The one gate that is judgement rather than script: read three cases as if you
    knew nothing, and check you never have to guess.
