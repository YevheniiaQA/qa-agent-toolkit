---
name: test-debugger
description: Debugs generated or failing Playwright tests in two passes — a functional pass that classifies each failure as test bug, product defect, environment, or data issue, and a mutation pass that inverts assertions to catch tests which assert nothing. Use this skill whenever generated tests fail, whenever the user asks why a test is flaky or red, whenever they need to know if a failure is a real bug, or after any automation generation stage. Also use it to audit an existing suite for tests that always pass regardless of product behaviour.
---

# Test Debugger

Generated tests are a draft until they have run. This skill turns a draft into a
suite worth trusting, in two passes that answer two different questions: *does the
test run correctly* and *does the test check anything*.

## Pass 1 — functional debugging

Run each test in isolation first (`--workers=1`, one file at a time). Isolation
separates genuine failures from interference, and interference is itself a finding.

Classify every failure before changing anything. Fixing without classifying is how
real defects get "fixed" out of the suite.

| Class | Signals | Action |
|---|---|---|
| **Test bug** | Wrong endpoint, wrong payload shape, bad locator, missing await, wrong expected value | Fix the test |
| **Product defect** | Test matches the contract and the requirement; system disagrees | Do not fix. Log to `DISCREPANCIES.md`, mark `test.fail()` |
| **Environment** | Connection refused, 502, expired cert, missing env var, wrong base URL | Fix config, do not weaken the test |
| **Data** | Missing user, stale record, conflicting leftover state | Move provisioning into a fixture |
| **Flakiness** | Passes on retry; timing, animation, or race dependent | Fix the wait strategy — never add a retry to hide it |

### Scenarios that were always meant to fail

Before classifying anything, check the scenario's handoff fields. A test whose
scenario carries `status: known-defect` and `doNotRelax: true` was written to
fail. Its failure is not a finding to investigate — it is the finding, already
investigated and recorded upstream with its evidence.

For those, the only correct actions are: confirm the failure matches the recorded
`observedBehaviour`, and confirm the expected-failure marker is present and
strict. If the test now *passes*, that is the interesting case — the defect may
have been fixed, and the marker should be removed. Say so explicitly rather than
letting a passing expected-failure sit quietly.

Do not re-litigate these as test bugs. A debugging pass that "fixes" eight
deliberate failures by matching them to observed behaviour has undone the most
valuable work the pipeline did.

### Classification discipline

The tempting failure mode is relaxing an assertion until the test goes green. A
test changed from `toBe(400)` to `toBeGreaterThanOrEqual(400)` because the API
returned 500 has not been fixed; it has been disarmed. When you weaken an
assertion, you must be able to point to the contract that justifies the weaker
form — otherwise you are looking at a defect.

### Marking known defects

```ts
test.fail('TC-283-API-011 rejects a domain longer than 50 characters', async ({ api }) => {
  // Known defect DEVAI-301 — API returns 201 instead of 400
  ...
});
```

`test.fail()` keeps the suite green while keeping the check alive: when the fix
lands, the test fails as "expected failure did not occur" and tells you to remove
the annotation. Skipping the test instead loses that signal entirely.

## Pass 2 — mutation check

A test that passes is not necessarily a test that checks anything. Once a test is
green, invert its primary assertion and re-run:

```ts
// original
expect(res.status()).toBe(200);
// mutation — must fail
expect(res.status()).toBe(400);
```

If the mutated test still passes, the original asserts nothing real. Common causes
worth naming, because they recur:

- the assertion sits after an unawaited promise, so it runs before the action
- the locator matches nothing and the assertion is a negative one (`toBeHidden`
  passes trivially against a non-existent element)
- the test asserts on mocked data it set up itself
- the assertion is inside an untaken `if` branch
- the API call failed silently and the test asserted on an empty object

### Mutation hygiene

**Mutate per test, not per line.** Parameterised tests and templated loops share
an assertion line. Inverting that line once and reporting a single result hides
every test but the first — a suite of twelve can report "12 killed" while two of
them were never independently checked. Where an assertion is shared, mutate and
run each consuming test separately, and say in the report that you did.

**Leave the tree exactly as you found it.** Back up before mutating, restore
after, and verify the restore by byte comparison rather than by inspection. Then
confirm the project still compiles. A mutation pass that leaves one inverted
assertion behind produces a permanently red test that everyone eventually
disables, and it is nearly impossible to trace back to its cause weeks later.

**Do not mutate tests that are already expected to fail.** Their assertions do
not execute to completion, so inversion proves nothing. Say so explicitly rather
than omitting them silently — an unexplained gap between suite size and mutation
count reads as an oversight.

Record a mutation score per suite. Tests that survive mutation get rewritten, not
deleted — the scenario they came from still needs coverage.

## Flakiness diagnosis

When a test passes on retry, do not move on. Open the trace and identify the class:

### Negative assertions satisfied by the wrong cause

The quietest failure class in the whole pipeline, and it appears in two disguises:

- A broken base URL returns 404 everywhere; an expected failure asserting "should
  be 4xx" is satisfied and reports **"expected to fail, but passed"**
- A record vanishes between write and read on a shared host; a read-back assertion
  of `toBe(404)` is satisfied by the disappearance rather than by the rejection it
  was written to detect

In both cases the test reports a correct-looking result for entirely the wrong
reason. The defence is the same: **an expected failure asserts the specific
recorded behaviour — exact status code plus a body marker — never a class.** If a
scenario's assertion could be satisfied by an unrelated failure mode, that is a
scenario defect to send back, not a debugging problem to work around.

When an expected failure flips to "expected to fail, but passed", never assume the
defect was fixed. Verify with a direct probe outside the suite before concluding
anything. Probing each expected failure independently of the suite is the only way
to know it fails for its own reason.

| Cause | Fix |
|---|---|
| Assertion ran before the state settled | Web-first assertion, or wait for the response |
| Animation or transition | Wait for a stable state, not a sleep |
| Test order / shared data | Fixture-provisioned, uniquely named data |
| Network timing | `waitForResponse` on the specific call |
| Locator matches multiple elements | Tighter locator, scoped to a container |
| Time or timezone dependence | Freeze the clock, use fixed offsets |

Never resolve flakiness with a longer timeout or another retry. Both convert a
loud problem into a quiet one that slows every future run.

**Environment instability is a finding, not noise.** When a suite is stable
sequentially and unstable under parallelism against a shared host, that is
evidence the target is unsuitable for the class of assertion being made — and
read-after-write assertions are the usual casualty. Report the observation with
its supporting numbers (sequential pass rate, parallel failure rate, how many runs)
and name the fix as an environment change, not a test change.

Making a weaker claim than the evidence supports is correct here. Root cause
inside a system you cannot observe is not determinable from outside it, and saying
so is more useful than a confident guess that sends someone down the wrong path.

## Output

`DEBUG_REPORT.md`:

```markdown
# Debug report — DEVAI-283

## Summary
38 tests · 34 passed · 3 expected failures (known defects) · 1 rewritten after mutation

## Product defects found
- DEVAI-301 — domain length validation missing (TC-283-API-011) — reported, test.fail()
- DEVAI-302 — 409 returned as 500 on duplicate connect (TC-283-API-014) — reported

## Test bugs fixed
- TC-283-UI-004 — locator matched two cards; scoped to the card container
- TC-283-API-007 — missing await on the provisioning call

## Mutation results
- 37/38 tests failed under mutation (good)
- TC-283-UI-009 survived — asserted on a locator that matched nothing; rewritten
```

The "product defects found" section is the part the engineer actually reads first.
Put it above the fold.

## Self-check before reporting completion

1. **Every failure has a classification** — none left as "investigating".
2. **Every classification cites evidence**: the contract line for a product
   defect, the specific code error for a test bug, the connection error for an
   environment issue.
3. **No assertion was weakened without citing the contract that justifies the
   weaker form.** List every assertion you changed and why. This is the gate that
   matters most; it is also the easiest to skip.
4. **Scenarios carrying `doNotRelax` were not modified.**
5. **Every product defect is either already recorded upstream or newly reported**,
   with the affected tests marked as strict expected failures.
6. **The mutation pass ran on every passing test**, with per-test results, not a
   summary figure.
7. **Every test that survived mutation was rewritten**, not deleted — the scenario
   it came from still needs coverage.
8. **No flakiness was resolved by adding a retry or extending a timeout.** If
   either appears in your diff, the underlying cause was not found.

Report each gate's result.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event run <report.json>` for every run, `qa-event triage <TEST-ID> --class
product-defect|test-bug|environment|data [--defect <ID>]` for every failure you classify,
and after the mutation pass `qa-event mutation --suite <suite> --mutants <n> --killed <n>`
(or `--source <file>` with those two numbers). False failure rate and mutation score in
`qa-metrics` come only from these events.

