---
name: test-execution
description: Prepares everything a manual tester needs to run a set of test cases, and records what happened — an execution pack with environment, accounts, build and ordered cases, then results with evidence, defects captured during the run, and a handoff back to the pipeline. Use this skill when manual cases are ready to run, when a tester asks what to test or how to start, when recording the outcome of a manual pass, or when a regression round needs organising. Also use it to produce a run sheet for someone unfamiliar with the feature.
---

# Test Execution

The gap this fills: scenarios and cases exist, automation exists, and a manual
tester still has to assemble the environment, the accounts, the build number and
the right subset by hand before they can start. That assembly is the same work
every time, and getting it wrong is why a round of testing produces results
nobody can interpret.

## The execution pack

Write `04-results/<TICKET>/EXECUTE.md`. One page, everything needed to start,
nothing else. This file is the manual tester's front door: the root README and the
ticket README both point here.

```markdown
# Execute — PLAT-118 · Connect a Confluence workspace

**Build** 2026.09.14-a4f21 · **Environment** staging · **Estimated** 55 minutes

## Before you start
- URL: https://admin.platform.test.acme.com
- Accounts: `qa.admin@example.com` (superuser) · `qa.viewer@example.com` (viewer)
  Passwords are in 1Password → QA → Platform staging
- VPN required: yes
- Do not run between 09:00 and 09:30 — staging deploys then

## Known defects — these cases are expected to fail
| Case | Defect | What you will see |
|---|---|---|
| TC-13 | DEF-PLAT-01 | Returns 200 and stores the record; the ticket requires rejection |
| TC-19 | DEF-PLAT-04 | Overwrites silently; the ticket requires 409 |

Mark them failed as normal — the record is what proves the defect is still open.

## Order
1. **Smoke** TC-01, TC-06 — if these fail, stop and report. Nothing else is meaningful.
2. **Core** TC-02 … TC-12 — the acceptance criteria
3. **Edge and negative** TC-13 … TC-24

## Open questions that affect what you see
- **Q-05** Whether category is mandatory is undecided. If the form lets you submit
  without it, record what happened — do not judge it pass or fail.

## How to report
Record results in `04-results/PLAT-118/executions/`. For anything unexpected, capture: what you did, what
you expected, what happened, a screenshot, and the time. Do not file the ticket
yourself — hand it back and it goes through the defect flow with evidence attached.
```

The "known defects" block is what stops a tester spending twenty minutes
investigating something already known, and the ordering block is what stops them
running twenty cases against a broken build.

## Ordering matters

**Smoke first, and stop on failure.** If registration is broken, results for the
twenty cases that depend on it carry no information, and running them wastes an
hour and produces a confusing report.

**Group by setup, not by requirement ID.** Cases needing the same precondition run
together. Sequence is a tester's time, and reshuffling state is most of it.

**Destructive cases last.** Anything that deletes or changes shared state goes at
the end, so it cannot invalidate cases that have not run yet.

## Recording results

One record per execution round, in `04-results/<TICKET>/executions/`:

```markdown
# Execution — PLAT-118 — 2026-09-14 — Alex T.
Build 2026.09.14-a4f21 · staging · 51 minutes

| Case | Result | Note |
|---|---|---|
| TC-01 | Pass | |
| TC-06 | Pass | |
| TC-09 | **Fail** | Unexpected — see DEF-draft-07 |
| TC-13 | Fail (expected) | DEF-PLAT-01, unchanged |
| TC-17 | Blocked | Q-05 undecided; recorded observation only |
| TC-21 | Skipped | Needs a second workspace; none available on staging |

**Unexpected failures** 1 · **Expected** 2 · **Blocked** 1 · **Skipped** 1

## TC-09 — what happened
Submitted with a 60-character workspace name. Expected the field to reject it;
the form accepted it and the record was created with the name truncated to 50
characters with no warning. Evidence: evidence/TC-09-truncation.png, 14:22.
```

Four outcomes, and they are not interchangeable. **Blocked** means it could not be
run and the reason is external. **Skipped** means a decision was made not to run
it. Collapsing either into "fail" corrupts the coverage figure; collapsing them
into "pass" is worse.

**An expected failure that passes is a finding.** It may mean the defect was
fixed. Record it and hand it to `regression-manager` for verification rather than
assuming.

## Handing back

After a round, pass the results to:
- `discrepancies-fix` for unexpected failures, which drafts defects with your
  evidence attached and asks before filing anything
- `regression-manager` for expected failures that passed
- `test-report` to fold the round into the HTML report
- `workspace-index` to update the ticket state

Never file a defect directly from an execution record. The drafting step is where
reproduction gets narrowed and severity gets reasoned about, and skipping it
produces tickets a developer sends back.

## Self-check

1. Every case in the pack exists in `03-tests/manual/<feature>/TEST_CASES.md`.
2. Known-defect cases are listed with what the tester will see.
3. Environment, accounts and build are stated, and credentials are referenced
   rather than written out.
4. The order starts with smoke and ends with destructive cases.
5. Every result is one of pass, fail, blocked or skipped — never blank.
6. Every unexpected failure has evidence and a timestamp.
7. The ticket state was updated.
