---
name: test-estimation
description: Produces QA effort estimates and testability risk assessments for sprint planning — how long testing a story will take, what makes it risky, and what would have to be true before it can be tested at all. Use this skill during sprint planning or backlog refinement, whenever the user asks how long testing something will take, whenever a team needs QA capacity for a sprint, or when deciding whether a story is ready to commit to. Also use it to flag stories that cannot be tested as written.
---

# Test Estimation

Sprint planning is where QA either gets time or gets blamed later for not having
had any. The skill here is not producing a number — it is producing a number
somebody can argue with, because an estimate whose reasoning is invisible gets
halved in the room.

## Estimate from the decomposition, not the title

A story title carries no information about test effort. Run
`requirements-decomposer` first, or estimate from an existing decomposition. The
requirement count, the number of input classes, and the number of open questions
predict effort far better than story points do.

```markdown
## PLAT-118 — QA estimate

**Scenarios expected**: 22–28
  12 functional requirements × ~1.6 scenarios (positive + negative + boundary)
  3 non-functional requirements requiring their own setup

**Effort**
| Activity | Hours | Basis |
|---|---|---|
| Requirements analysis and questions | 1.5 | 12 requirements, 4 already ambiguous |
| Scenario design | 3 | 25 scenarios, 2 needing decision tables |
| API automation | 5 | 18 API scenarios, existing fixtures reusable |
| UI automation | 7 | 7 UI scenarios, 4 new page objects, 3 test IDs to request |
| Debugging and stabilisation | 4 | ~30% of authoring time, from the last three stories |
| **Total** | **20.5** | |

**Confidence**: medium. Rises to high once Q-02 and Q-05 are answered.
```

The basis column is what survives challenge. "Five hours" invites a haggle;
"eighteen scenarios against existing fixtures" invites a conversation about scope.

## Calibrate against your own history

After each story, record actual against estimated. Three stories in, the
debugging multiplier stops being a guess. Keep it in the project folder:

```markdown
| Story | Scenarios | Estimated | Actual | Note |
|---|---|---|---|---|
| PLAT-101 | 18 | 14h | 19h | Two endpoints changed mid-sprint |
| PLAT-109 | 24 | 20h | 21h | |
```

Estimating without history is guessing with a table around it. Say which it is.

## Testability risk assessment

More valuable than the estimate, and the part teams skip. For each story, flag
what would make testing hard or impossible, before it is committed to:

| Risk | Why it matters | Ask for |
|---|---|---|
| No stable locators on new UI | Suite breaks on next restyle | Test IDs, named in the story |
| Behaviour depends on a third-party system | Cannot be tested deterministically | A stub, or an explicit decision not to test it |
| No way to observe the outcome | Assertion is impossible | An API, a log, or a database field |
| Time-dependent behaviour | Flaky by construction | Injectable clock |
| Requirements contradict each other | Scenarios cannot be written | The decomposer's open questions, answered |
| Test data cannot be created | Fixtures impossible | A seeding route, or production-like data |

A story with three of these is not a story with a large estimate — it is a story
that is not ready. Say that plainly in planning rather than absorbing the
consequence silently in the sprint.

## Capacity

When asked for sprint capacity, state what the QA time covers and what it does
not. Regression, flakiness maintenance, and re-testing after fixes are real work
that disappears from plans because nobody itemises it:

```markdown
**Sprint 34 QA capacity**: 32h available
  New story testing        20.5h  (PLAT-118)
  Regression maintenance    4h    (suite upkeep, flaky triage)
  Re-testing after fixes    4h    (5 defects open from sprint 33)
  Refinement and planning   3h
  Unallocated               0.5h
```

Zero unallocated is a warning, not an achievement. Say so.
