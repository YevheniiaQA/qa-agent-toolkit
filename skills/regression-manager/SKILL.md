---
name: regression-manager
description: Manages the regression suite over time — verifying fixes, removing expected-failure markers when defects are resolved, merging new tests into the regression set with the right tags, retiring obsolete tests, and triaging flakiness before it erodes trust. Use this skill when a defect has been fixed and needs re-verification, when new tests should join the regression suite, when the suite is getting slow or unreliable, or when the user asks what to run before a release. Also use it to audit an inherited suite for dead and duplicated tests.
---

# Regression Manager

Everything upstream produces tests. This skill is about what happens to them
afterwards — which is where most suites quietly die, not from being badly written
but from never being maintained.

## Verifying a fix

When a defect is reported fixed, the test that proved it already exists and is
marked as an expected failure. Do not write a new one.

1. **Run the existing test.** A strict expected failure reports "expected to fail,
   but passed" when the defect is resolved. That message is the verification.
2. **Confirm the pass is for the right reason.** Probe directly, outside the
   suite, exactly as the debugging stage does. An expected failure can flip to
   passing because the environment broke in a way that happens to satisfy the
   assertion — this has happened before and will happen again.
3. **Remove the marker**, keep the test, and record the defect ID and the date in
   a comment. The test now guards the fix.
4. **Check for adjacent regressions.** A validation fix frequently breaks the
   happy path. Run the whole requirement's scenarios, not just the one test.
5. **Update the traceability**: requirement moves from `Covered (failing)` back to
   `Covered`; the defect closes with the verifying run referenced.

Never close a defect on a passing test alone without step 2.

## Merging new tests into the regression suite

New tests arrive per ticket. The regression suite is not "all tests ever written"
— that is how a suite reaches four hours and gets switched off.

Tag on entry:

| Tag | Runs | Criteria |
|---|---|---|
| `@smoke` | Every pull request | Core paths; fails if the feature is fundamentally broken. Keep the whole set under 5 minutes |
| `@regression` | Nightly | Everything else that is stable and meaningful |
| `@slow` | Nightly, separate job | Long-running by nature |
| `@quarantine` | Reported, not gating | Known-unstable, with an owner and a date |

Promote to `@smoke` sparingly. One test per acceptance criterion at most, and only
where its failure would stop a release.

Before merging, check for duplication against the existing suite. Two tests
asserting the same thing through different paths cost twice and catch once.

## Retiring tests

Tests are removed for exactly three reasons, each requiring a record:

- **The requirement was removed.** The test goes with it; note the ticket.
- **It is a duplicate**, and the surviving test is named.
- **It asserts behaviour that was deliberately changed**, with the deciding ticket.

"It keeps failing" is never a reason. Neither is "nobody knows what it does" — that
is a reason to find out, and if nobody can, the test is evidence of a gap in the
requirements, not something to delete quietly.

## Flakiness triage

Track per-test failure frequency across runs. A test that fails one run in twenty
is not noise; it is a defect somewhere, and the only question is whose.

| Rate | Action |
|---|---|
| Below 1 in 50 | Record, watch |
| 1 in 10 to 1 in 50 | Investigate this sprint, classify cause |
| Above 1 in 10 | Quarantine with an owner and a date, fix or delete within two weeks |

Quarantine is a holding pattern with an expiry, not a graveyard. A quarantined
test with no owner after a month should be deleted — it is providing nothing and
implying coverage that does not exist.

Never resolve flakiness with a retry. The instruction bears repeating at this
level because the pressure is different here: a flaky test in a regression suite
is annoying every single day, and a retry makes the annoyance stop without making
the problem stop.

## Suite health report

```markdown
# Regression suite — sprint 34
Tests: 312 (smoke 24 · regression 271 · slow 12 · quarantine 5)
Runtime: smoke 3m40s · full 28m
Stability: 19 of 20 nightly runs clean
Flaky: 3 tests above 1 in 50 — TC-104 (owner: Alex, due 09-27), TC-188, TC-201
Fixes verified: 4 defects closed, 4 expected-failure markers removed
Added: 22 · Retired: 3 (2 duplicates, 1 requirement removed)
Coverage: 94% of active requirements have an asserting test
```

Runtime is on this report deliberately. A suite that grows 10% slower each sprint
has a deadline nobody has noticed.
