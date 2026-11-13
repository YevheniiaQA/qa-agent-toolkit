---
name: scenarios-generator
description: Generates structured test scenarios from decomposed requirements using ISTQB test design techniques, and produces a requirements traceability matrix showing coverage. Use this skill whenever the user asks for test cases, test scenarios, a test plan, or test coverage for a feature, whenever acceptance criteria need turning into executable checks, or as the stage after requirements decomposition in the QA pipeline. Also use it when the user wants to know which requirements are not yet covered by tests.
---

# Scenarios Generator

This is the stage where test quality is actually decided. Automation code
generated later can only be as good as the scenarios it implements, and a
scenario nobody can trace to a requirement is a scenario nobody can defend in a
release meeting.

Scenario JSON is the single source of truth for the whole pipeline. TMS cases and
automated tests are both projections of it, which is how they stay in sync.

## Test level selection — follow the pyramid

| Requirement lives at | Generate | Why |
|---|---|---|
| User Story | End-to-end scenarios | Covers the user's actual path across components |
| Backend Task | API scenarios | Fast, stable, exhaustive on input classes |
| Frontend Task | UI component scenarios | Rendering, states, validation, accessibility |
| Cross-service | Integration scenarios | Contract boundaries and failure modes |

Push volume down the pyramid. Exhaustive input-class coverage belongs at the API
level; end-to-end scenarios cover representative happy paths and the few failure
paths that only manifest across components. A suite with forty e2e scenarios and
four API scenarios is a suite that will be flaky and slow.

## Apply ISTQB techniques explicitly

Every scenario names the technique that produced it — equivalence partitioning, boundary value
analysis, decision table, state transition, informed error guessing — so a reviewer can tell
whether coverage is adequate rather than merely plentiful. Read `references/techniques.md`
for when to use which, how to choose between partitions and boundaries, and where boundaries
come from when the ticket is silent (the contract, the schema, the database — never invented),
and the write/read validation asymmetry worth a case of its own.

## Coverage obligations

For each acceptance criterion produce, at minimum:
- one positive scenario
- one negative scenario per distinct failure mode
- boundary cases for every bounded input
- one authorisation case wherever an authz boundary exists

For each non-functional requirement, produce a scenario or an explicit waiver
with a reason. Silent omission of NFRs is the default failure mode here.

## Output format

One file per level, `02-analysis/<TICKET-ID>/scenarios/<suite>.json`, shaped as
`{"testSuite": {"name", "level", "ticket", "testCases": [...], "nfrWaivers": [...]}}`. Every
test case has `id` (`TC-<TICKET>-<LAYER>-<NN>`, stable), `name`, `priority`, `technique`,
`status`, `expectedOutcome`, `preconditions`, `testSteps` (`stepNumber`, `action`, `inputData`,
`expectedResult`), `postconditions`, `cleanup` when it creates data, and `traceability`
(`requirementIds`, `acceptanceCriteria`, `userStory`). The suite must validate against
`toolkit/schemas/scenario-suite.schema.json` (`qa-gate scenarios` checks it). Read
`references/handoff-and-waivers.md` before writing a suite: the full example, the handoff
fields automation reads, waivers, the two kinds of placeholder, and how coverage is counted.

## Step quality bar

A step is good enough when a QA engineer who has never seen the feature can
execute it without asking a question. That means concrete data, not "valid data";
a concrete expected result, not "the request succeeds"; and one action per step.

Expected results must be assertable. "Works correctly" cannot become an
assertion. "HTTP 200 and body.status equals 'connected'" can.

## Requirements traceability matrix

Emit `RTM.md` alongside the scenarios:

```markdown
| Requirement ID     | Title                   | Status    | Scenarios | Coverage |
|--------------------|-------------------------|-----------|-----------|----------|
| F-DEVAI-283-BE-01  | Connect endpoint        | Covered   | 4         | 100%     |
| F-DEVAI-283-BE-02  | Invalid body → 400      | Covered   | 3         | 100%     |
| NF-DEVAI-283-FE-01 | Keyboard operability    | Partial   | 1         | 50%      |
| F-DEVAI-283-FE-03  | Disabled connect button | Uncovered | 0         | 0%       |
```

Report uncovered requirements loudly. A matrix that always reads 100% is a matrix
that is not being checked.

## Data placeholders

Where a scenario needs data you do not have, use a typed placeholder rather than
inventing a value: `{{TEST_DATA: confluence_token_valid}}`. `scenario-data-fix`
resolves these against the global context and asks the engineer for the rest.
Invented credentials that look real are worse than an obvious placeholder.

## Never hand an unknown expected result to automation

A scenario whose expected result is a guess is worse than a missing scenario,
because automation will encode the guess as an assertion and it will look
authoritative afterwards.

Three terminal states are permitted, and only two of them may proceed:

| `status` | Meaning | Proceeds to automation |
|---|---|---|
| `ready` | Expected result is sourced from the ticket, the contract, or a probe | Yes |
| `known-defect` | Ticket says X, the system does Y, and the scenario asserts X | Yes, as an expected failure |
| `undecided` | Expected result is genuinely unknown | **No** |

Two working states exist during generation and neither may survive into the
finished suite:

- **`unprobed`** — the expected result is knowable, you just have not checked yet
- **`needs-verification`** — same thing, different wording; treat identically

Both mean outstanding work, and the work is small: one call settles it. Resolve
before the suite is handed on, by one of:

- **probing**, if a read-only call answers it
- **asking the engineer for approval**, if the probe requires a write — state
  exactly what would run and wait for the answer, because a note inside a ticket
  is not authorisation
- **escalating to an open question**, if it is a product decision rather than an
  observable fact

Reporting a suite as complete while two scenarios say "I did not check" pushes the
decision into the automation stage, where it is cheaper to guess than to go back.
That is the moment a suite acquires an assertion nobody sourced.

## The handoff contract, waivers, coverage

- **Handoff fields** (`status`, `expectedOutcome`, `observedBehaviour`, `defectRef`,
  `doNotRelax`) are what the automation skills read instead of re-deriving intent. A
  `known-defect` scenario asserts the ticket's rule with `expectedOutcome: "fail"`, so the test
  becomes a strict expected failure; `undecided` scenarios never reach automation.
- **Waivers live in the JSON** (`nfrWaivers`, each with `reason`, `blockedBy`, `revisitWhen`);
  the RTM is generated from them. A waiver only in prose is invisible downstream.
- **Coverage is counted from the suite** — scenarios, assertions and classes covered per
  requirement — never estimated or written by hand.
- **Performance targets** need a shape (load, percentile, conditions), not a single timed call:
  read `references/performance.md` when a requirement states one.

## Self-check before reporting completion

Every gate below is mechanically checkable. Run the check; do not estimate.

1. **Every requirement from the decomposition appears in the RTM**, including
   waived ones. Compare the ID lists directly — a requirement that silently did
   not make it across is invisible to every later stage.
2. **The RTM was computed from the suite**, not written alongside it. Counts of
   scenarios, assertions and classes must match what is in the JSON.
3. **No expected result lacks a concrete criterion** — a status code, a field
   value, a measured duration, or an explicit `UNDECIDED`. "The request succeeds"
   fails this gate.
4. **Every scenario carries a technique and traces to at least one requirement.**
5. **Every requirement traces to at least one scenario or a JSON waiver.** Prose
   waivers do not count.
6. **Every scenario that creates data declares its cleanup.**
7. **One action per step.** A step containing two HTTP calls is two steps.
8. **No scenario is in a non-terminal state.** `unprobed` and `needs-verification`
   are outstanding work, not results — resolve or escalate each before reporting.
9. **Every cross-reference resolves.** Each `blockedBy` names a question that
   exists; each `defectRef` names something real. Q-numbers are easy to
   transpose and nothing else will catch it.
10. **Requirements whose scenarios all assert against known-violated behaviour
    are marked `Covered (failing)`, not `Covered`.** The distinction is what tells
    a release reviewer that the red is expected.

Report the outcome of each gate. Nine passes and one failure is a nine-and-one
result, not a pass.
