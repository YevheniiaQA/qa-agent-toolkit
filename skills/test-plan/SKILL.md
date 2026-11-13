---
name: test-plan
description: Writes the test plan for a release, an epic or a project — scope, approach per layer, environments and data, entry and exit criteria, risks and what will not be tested. Use this skill at the start of a release or an epic, when a client or manager asks for a test plan or a test strategy document, when a team needs agreed exit criteria before a release, or when scope needs stating in writing. Also use it to revise a plan when scope changes mid-release.
---

# Test Plan

The document that exists between the working agreement (how we work) and the
test report (what happened). Teams skip it, then argue at the end of the release
about whether something was in scope.

Keep it short. A test plan nobody reads has the same value as no test plan, and
length is the main reason they go unread. Two pages for a release, half a page
for an epic.

## Structure

```markdown
# Test plan — Platform release 2.4

**Scope** Confluence integration, bulk export, login rework (PLAT-118, 112, 104)
**Period** 9–20 September 2026 · **Prepared by** Alex T. · **v1.1**

## Approach by layer
| Layer | Approach | Owner |
|---|---|---|
| API | Automated, Playwright, per requirement | QA, automated |
| UI | Automated for core paths, manual for states and accessibility | QA |
| Database | State assertions where the API does not expose the outcome | QA |
| Integration | Contract tests between admin and item-service | QA + backend |
| Performance | Load at expected peak after functional sign-off | QA |
| Security | Authorisation boundaries and OWASP API classes | QA |
| Exploratory | Four charters, one per risk area | QA |

## Not in scope
- Mobile clients — no QA coverage this release, owned by the mobile team
- Load above 50 concurrent users — no requirement stated
- Penetration testing — out of scope for QA; no external engagement booked

## Environments and data
Staging, shared with the backend team. Deploys at 09:00 daily — do not test then.
Test accounts: superuser, operator, viewer. Created by DevOps, recorded in
`01-docs/process/ENVIRONMENTS.md`. Database access is read-only.

## Entry criteria
- Ticket in Ready for QA with acceptance criteria present
- Build deployed to staging and reachable
- Open questions blocking the acceptance criteria answered

## Exit criteria
- Every requirement covered by an asserting test or an explicit waiver
- No open critical or major defect without an accepted mitigation
- Scenario-to-code match at or above 90%
- Suite green across three consecutive runs, excluding known-defect tests
- Performance thresholds met, or the breach accepted in writing

## Risks
| ID | Risk | Likelihood | Impact | Response | Covered by |
|---|---|---|---|---|---|
| R-1 | A refund is paid twice when the provider retries | Medium | High | Idempotency tests on the refund API | F-PAY-BE-07, AC-PAY-04 |
| R-2 | Card data reaches the logs | Low | High | Log scan in the security pass | NF-PAY-02 |
| | Shared staging instability affects read-after-write tests | High | Medium | Dedicated instance requested (Q-07); meanwhile tests are marked environment-sensitive | |
| | Analyst unavailable from 15 Sep | Medium | High | Open questions front-loaded; defaults proposed for each | |

## Critical user journeys
| ID | Journey | Requirements |
|---|---|---|
| J-1 | Customer requests a refund and receives it once | F-PAY-BE-05, F-PAY-BE-07, F-PAY-FE-03 |
| J-2 | Support agent finds a payment by order number | F-PAY-BE-11, F-PAY-FE-08 |

## Deliverables
Scenarios and RTM · manual cases in TestRail · automated suites and a pull
request · HTML test report · defect records
```

## The two sections that earn the document

**Not in scope**, with reasons. Everything else in the plan is a commitment;
this is the only section that prevents an argument. "Mobile — owned by the
mobile team" settles in advance what would otherwise be discovered after release.

**Exit criteria**, agreed before testing starts. Criteria written at the end are
written to match what happened. Agreed up front, they are the thing that makes
"are we ready?" answerable rather than a matter of nerve.

Make every criterion checkable. "Sufficient testing has been performed" is not a
criterion; "every requirement covered by an asserting test or an explicit waiver"
is, and `automation-compare` can evaluate it.

## Risks, not worries

A risk entry needs a response, otherwise it is a worry with a table around it.
The response is what someone will actually do — request the instance, front-load
the questions, book the review.

A **product risk** (what breaks for users if this goes wrong) gets an `ID` (`R-n`) and
`Covered by`: the requirement, acceptance-criterion or test IDs that exercise it. A
**project risk** (staffing, environments, dates) has neither. `qa-metrics` computes risk
coverage from the product risks only, so a missing link shows as an uncovered risk, not as
a gap nobody sees.

**Critical user journeys** are the five to ten paths without which the business stops
(pay, book, sign in). Each lists the requirement IDs along it; `qa-metrics` reports a
journey green only when every one of them has an automated test that was as expected in
the last run, and a known defect on the path keeps it red.

## Keep it current

Scope changes mid-release. Revise the plan, bump the version, note what changed
and when. A plan that silently diverges from reality is worse than none, because
the exit criteria it carries are then being evaluated against the wrong scope.

## Self-check

1. Every ticket in scope is named; everything excluded has a stated reason.
2. Every exit criterion is mechanically checkable.
3. Every risk has a response naming an action and, where relevant, a person; every product
   risk has an `R-n` ID and `Covered by` IDs, or says why it is not covered.
4. Environments, accounts and data access are stated with where credentials live.
5. The plan carries a version and a date.
6. Critical user journeys are listed (`J-n`, journey, requirement IDs), five to ten of them.
