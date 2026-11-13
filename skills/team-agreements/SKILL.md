---
name: team-agreements
description: Produces the written working agreement between the QA engineer and the product team — ticket flow, artefact review responsibilities, defect handling, communication cadence — and the half-page document that gets signed off. Use this skill during onboarding onto a new project, before the first pipeline run delivers artefacts to anyone else, whenever the user asks how to set expectations with a team, or when friction appears over who reviews what. Also use it to revise agreements after the pilot period.
---

# Team Agreements

The most underrated setup step. A perfectly configured agent delivering artefacts
into a team with no agreed process creates more chaos than value — fifty scenarios
land in someone's review queue unannounced, nobody knows who owns the defect
triage, and by week three the team has quietly stopped reading them.

This is an organisational skill, not a technical one. Its output is a half-page
document sent to the team lead.

## Why this working format needs explaining

A QA engineer operating with an agent works differently from an embedded tester,
and the team will notice. Say it up front rather than letting them discover it:

- Attends key testing-related sessions, not every standup and planning
- Does not investigate root causes — finds and documents defects; the team
  diagnoses and fixes
- Does not deep-dive each microservice — works from the global context and
  documentation
- Covers several projects simultaneously, which is only possible because of the
  above

Framing matters here. This is not a lighter version of QA; it is a different
distribution of work, and the team gets more test coverage in exchange for
handling their own root-cause analysis.

## What to agree

**1. Ticket flow and entry criteria**

```
Analyst writes requirements in Jira
   → ticket reaches "Ready for QA"
   → QA runs the pipeline
   → scenarios + automated tests
   → review
   → PR into the test repository
```

Agree the exact status that signals readiness. Agree that incomplete requirements
come back to the analyst with the specific questions the decomposer produced —
this is the single highest-value loop in the whole arrangement, and it only works
if the team expects it rather than experiencing it as pushback.

**2. Artefact review**

| Artefact | Reviewer | When |
|---|---|---|
| Requirements decomposition (US/Tasks) | Analyst | After generation, before scenarios |
| Test scenarios | Analyst + team lead | After generation, before automation |
| Automated tests (PR) | Developer | Standard code review |
| Test cases in TestRail | QA | Final check before upload |

Reviewing the decomposition is not a formality. Hearing "this is not what we
meant" before fifty test cases exist is the difference between a ten-minute
correction and a day of rework.

**3. Defect handling**

The skill chain does most of this. Set the expectation of who does what:
- Discrepancies are logged automatically during generation and automation
- `discrepancies-fix` auto-closes unambiguous ones by source priority
- Suspected defects are shown to the QA engineer with reproduction steps; after
  confirmation the ticket is created and affected tests marked as expected failures
- The QA engineer confirms "yes, this is a bug" — the developer establishes cause
- When the fix lands, the expected-failure marker is removed

**4. Main point of contact**

Usually the analyst. They answer business-logic questions raised during
decomposition, confirm scenarios match intent rather than only the letter of the
requirement, and classify contradictions between requirements and implementation
as bug or as-designed.

**5. Communication**

- A shared channel for operational questions
- A short weekly testing status, five minutes
- The test environment deployment schedule, so runs do not collide with deploys

**6. TestRail structure**

Agree the folder hierarchy before the first upload. If the team has a convention,
follow it. Retrofitting two hundred cases into a different structure by hand is a
miserable afternoon that is entirely avoidable.

## Output

`01-docs/process/WORKING_AGREEMENT.md` — half a page, sent to the team lead:

```markdown
# QA working agreement — Platform — 2026-09-12

**QA**: <name>, supported by an AI QA assistant. Covers several projects.

**In scope**: requirements analysis, test design, test cases in TestRail,
API and UI automation, defect reporting, release test reports.
**Out of scope**: root-cause investigation, fixing defects, production monitoring.

**Entry criteria**: ticket in "Ready for QA" with acceptance criteria present.
Incomplete requirements return to the analyst with specific questions.

**Review**: analyst reviews decomposition and scenarios; developer reviews the
test PR. Turnaround target: one working day.

**Defects**: QA files them with reproduction steps and evidence. The team
establishes cause. Tests for known defects stay in the suite as expected failures.

**Contact**: <analyst> for business logic, <team lead> for priorities.
**Cadence**: weekly status, Thursday, 5 minutes.
**TestRail root**: Platform / <service> / <feature>

Agreed: <team lead>, <analyst>, <QA>
```

Write it down because nobody remembers a call a week later, and "we did not agree
to that" is a conversation the document makes short.
