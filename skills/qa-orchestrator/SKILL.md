---
name: qa-orchestrator
description: Coordinates the full QA pipeline from a ticket URL to merged automated tests. Use this skill whenever the user asks to "test a feature", "cover ticket X with tests", "run the QA pipeline", mentions a Jira/Linear ticket that needs QA, or asks about the status of an in-flight QA task. Also use it when the user wants several QA stages chained together, or when they are unsure which QA skill to run next. This skill never does the work itself — it delegates to the specialised QA skills and enforces quality gates between stages.
---

# QA Orchestrator

You are the coordinator of a multi-stage QA pipeline. Your value is sequencing,
delegation, and quality control — not doing the work.

## Core rules

1. **Never execute a stage yourself.** Delegate each heavy stage to its stage
   agent (see *Delegation*), each in its own context window, and run independent
   stages in parallel. Long pipelines degrade badly when one agent carries all
   the context: one run that kept every stage in a single conversation reached
   553k tokens of context by stage 3 and re-sent ~137M tokens in total.
2. **Never skip a quality gate.** A bad artefact at stage N produces garbage at
   every stage after it. Catching it early costs minutes; catching it at the MR
   stage costs a day.
3. **Always be able to answer "where are we?"** Keep `02-analysis/<TICKET-ID>/_pipeline.json`
   with each stage's state (`pending | running | passed | failed | skipped | blocked`), and
   change it only with `qa-pipeline set <TICKET> <STAGE> <status>`: it fills the timestamps
   and the gate file, validates the file, and refuses `passed` unless `qa-gate check-stage
   --require-passed` accepts the stage. Every stage the ticket goes through gets an entry,
   on both tracks, including the ones that end `blocked` or `skipped`.
4. **Stop and ask on ambiguity.** Auto-resolve only what the priority rules in
   `discrepancies-fix` allow. Anything else goes to the engineer.

## Before any pipeline can run

A project needs `project-setup` (profile), `access-preflight` (verified
connections) and `global-context-builder` (context) completed once. If
`.env.<project>` is missing or preflight has never passed, say so and route to
those skills instead of starting a run that will fail at stage 3.

`team-agreements` is not technically blocking, but delivering artefacts into a
team that has not agreed who reviews them wastes everyone's time — flag it if the
working agreement does not exist.

## Pipeline

```
Stage 0  global-context-builder   (once per project, refresh on major changes)
            ↓
Stage 1  ticket-fetch → requirements-decomposer
         GATE 1: 6 checks
            ↓
         CRITIC 1: qa-critic on requirements-decomposer (rubrics/requirements.md)
            ↓
Stage 2  figma-analyzer (UI tickets only) ∥ scenarios-generator (api + ui agents)
         GATE 2: 6 checks
            ↓                                   manual track, from the same scenarios
            ↓                          Stage 2M manual-test-cases      GATE 2M: qa-gate manual
            ↓                          Stage E  test-execution         GATE E:  qa-gate execution
            ↓                                   (a round needs a tester: blocked until it ran)
Stage 2.5 selectors-collector      (UI tickets only)
         GATE: SELECTORS validated against live DOM
            ↓
Stage 3  automation-api ∥ automation-ui
         GATE 3: 14 checks (API) / 16 checks (UI)
         CRITIC 3: qa-critic on each (rubrics/code.md)
            ↓
Stage 4  test-debugger             (functional debug → mutation pass)
         GATE 4: no unexplained failures, mutation score ≥ threshold
            ↓
Stage 5  automation-compare → scenario-data-fix → discrepancies-fix
         GATE 5: scenario↔code match ≥ 90%
            ↓
Stage R  test-report → qa-metrics           (both tracks: automated runs + the manual round)
         GATE R: qa-gate report — the report's numbers recomputed from the raw run reports
            ↓
Stage 6  tms-uploader ∥ pr-creator

On request: contract-testing, performance-testing, security-testing (qa-special).
```

## Delegation

Heavy stages run in stage agents, the `qa-*` subagents: started with the Agent tool in
Claude Code, or as a subagent by name in Cursor. Both IDEs get the same agents, built
from `~/.qa-agent/toolkit/agents/` into `~/.claude/agents` and `~/.cursor/agents`. Each
agent loads its skill (preloaded in Claude Code, read first in Cursor), starts with a
clean context, writes a gate file and returns a report of 25 lines or fewer. Stages that
need the engineer, or are too small to justify a cold start, stay in this conversation.

| Stage | Runs in | Model |
|---|---|---|
| preflight | `qa-preflight` | haiku |
| 0 global context | `qa-context` | inherit |
| 1 ticket-fetch → requirements-decomposer | `qa-requirements` (one agent, both skills) | inherit |
| 2 scenarios-generator | `qa-scenarios` (one agent per ticket; RTM spans all levels) | inherit |
| 2 figma-analyzer | this conversation, in parallel with the scenarios agent | — |
| 2.5 selectors-collector | `qa-selectors` | inherit |
| 3 automation-api ∥ automation-ui | `qa-automation-api` ∥ `qa-automation-ui`, launched in one message | inherit |
| 4 test-debugger | `qa-debugger` (one per test project) | inherit |
| 5 automation-compare → scenario-data-fix | `qa-sync` | inherit |
| 5 discrepancies-fix | **this conversation**: decisions belong to the engineer | — |
| critic after Gate 1 and Gate 3 | `qa-critic` (or `qa-critic run --backend …`, see *Independent review*) | sonnet |
| 2M manual-test-cases, E test-execution | `qa-manual` (`step: cases` after Gate 2, `step: execution` when a round ran) | inherit |
| R test-report → qa-metrics | `qa-report` | inherit |
| contract, performance, security | `qa-special`, only on request, naming the skill | inherit |
| 6 tms-uploader, pr-creator | **this conversation**: outward-facing, confirm first | — |
| close: artifact-retention, workspace-index | `qa-housekeeping` | haiku |
| ad hoc: db-validator, test-estimation, etc. | this conversation | — |

**Delegation prompt.** Pass paths and decisions, never artefact contents:

```
Ticket: <TICKET>   Workspace: <absolute root>   Mode: <pipeline|resume|...>
Inputs: <paths the skill reads, e.g. 02-analysis/<T>/requirements/_index.json>
Engineer decisions so far: <Q-id → answer, one line each, or "none">
Scope: <level/target/test dir if limited, else "all">
```

**Record every decision.** Each answer the engineer gives goes under its question in
`OPEN_QUESTIONS.md` (`Answer (engineer, <date>): …`) and into `qa-event decision <Q-id>
--by engineer`; a stage resumed on a proposed default without an answer records `--by
default`. `qa-metrics` reports the share of decisions taken by silent consent.

**Subagents cannot ask the engineer.** A stage that needs an answer returns
`blocked` with `needsEngineer`. Batch every open question from the stages that
have returned into one round of questions (AskUserQuestion in Claude Code, one
message in Cursor), then resume the blocked stage with
a new agent that gets the answers in *Engineer decisions so far*. A
`discrepancy:` item from `qa-sync` goes to `discrepancies-fix`, here.

**Single-skill fan-out.** For `single_skill` mode (40+ scenarios), split by suite
file or spec directory, one agent per slice, and run the stage's `qa-gate` once
after all slices return. Parallel `qa-scenarios` agents write only their suite;
the RTM and Gate 2 run once every level is done.

**No subagents available?** Run each stage in this conversation, then tell the
engineer to start a new chat (`/clear` in Claude Code) and continue with mode `resume`. `_pipeline.json` and the
gate files give the same isolation, one stage per session.

## Execution modes

| Mode | What it does | When to use |
|---|---|---|
| `pipeline` | Full cycle with dependency ordering | New feature arrives for testing |
| `parallel_types` | API and UI tracks simultaneously | Full-stack ticket |
| `single_skill` | N agents on one stage | 40+ scenarios to automate |
| `batch_issues` | Several tickets at once | Sprint-wide regression prep |
| `resume` | Continue from last passed gate | Pipeline failed midway |
| `degraded` | Run only stages that need no environment access | Access requests still pending |
| `verify` | Stages check artefacts that already exist (a generator's output, hand-written or inherited work) instead of producing them: mechanical gate, self-check, gate file | A generator or a person produced the artefacts; an inherited suite |

**Generators are producers, not a way around the gates.** A script that renders requirements
or scenarios (a project's `_generator/`, a converter) ends by running the stage's `qa-gate …
--write <stage>` and `qa-pipeline set <TICKET> <stage> running --note "generated by <script>"`.
The stage becomes `passed` only after its agent ran in mode `verify` and wrote the gate file.

## Skills report their own gates — verify they did

Nineteen skills carry a `Self-check before reporting completion` section, and each of
them writes a gate file whenever it runs as a stage, in a stage agent or here:

| Track | Skills with a self-check |
|---|---|
| setup | `access-preflight` |
| automated | `global-context-builder`, `requirements-decomposer`, `scenarios-generator`, `automation-api`, `automation-ui`, `test-debugger`, `automation-compare`, `discrepancies-fix`, `contract-testing` |
| manual | `manual-test-cases`, `test-execution`, `exploratory-testing` |
| release | `test-plan`, `test-report`, `qa-metrics`, `performance-testing`, `security-testing` |
| review | `critic-review` (its output is the critic file, checked with `check-stage <T> <STAGE>.critic`) |

A skill without the section (for example `ticket-fetch`, `scenario-data-fix`,
`selectors-collector`) still writes a gate file; its `selfCheck` lists the skill's
completion criteria instead.

Each stage writes its results to `02-analysis/<TICKET>/_gates/<stage>.json`, where
`<stage>` is the skill name (project-scoped stages: `02-analysis/_project/_gates/`):
`status`, `selfCheck` with one entry per skill gate plus evidence, and `mechanical`
from `qa-gate`. Keys of `stages` in `_pipeline.json` are skill names too, so the gate
file can be found without a `gateFile` field. Both files follow `toolkit/schemas/`.

**The hooks already enforce part of this.** When a `qa-*` stage agent stops,
`qa-stage-gate` runs `qa-gate check-stage` on the gate file its report names and sends
the agent back (up to three times) if the file is missing or incomplete. When this
conversation stops, the same hook runs `qa-gate check-pipeline` and refuses to end while a
stage marked `passed` has a gate file that fails. The hooks are a floor, not the review:
verify every stage before you mark it `passed` in `_pipeline.json`:

1. **The gate file is complete and honest.** Run
   `qa-gate check-stage <TICKET> <STAGE> --rerun --require-passed`. It checks the schema,
   one `selfCheck` entry per item of the skill's self-check, that status agrees with the
   results (one failure is never `passed`), that the mechanical gate was recorded, and
   re-runs `mechanical.*.tool` to compare exit codes. A stage that says "done" without
   saying which checks it ran has not been checked, and the two most expensive errors
   found so far in this pipeline were both caught by a gate that someone remembered to
   run. Re-delegate with the failing check named; do not accept the summary.
2. **Read the failures, not only the exit code.** `check-stage` prints one line per check;
   name the failing ones to the engineer when a stage cannot be fixed by re-delegation.
3. **Read only the gate file and the report.** Open an artefact itself only when
   a gate fails or the engineer asks about it. Reading artefacts "to check" puts
   back into this context exactly what delegation kept out.

| Gate | Mechanical command |
|---|---|
| 1 | `qa-gate reqs <TICKET>` |
| 2 | `qa-gate scenarios <TICKET>` |
| 3 | `qa-gate code <TEST_DIR> --ticket <TICKET>` (add `--ui` for UI) |
| 4 | `qa-gate code ...` again after debugging; mutation results come from the gate file |
| 2M | `qa-gate manual <TICKET>` |
| E | `qa-gate execution <TICKET>` |
| R | `qa-gate report <TICKET>` |
| critic | `qa-gate check-stage <TICKET> <STAGE>.critic` |
| any stage | `qa-gate check-stage <TICKET> <STAGE> --rerun --require-passed` before marking it passed |
| whole run | `qa-gate check-pipeline <TICKET>` before the final message |

`qa-gate` covers only what a script can decide. It does not replace the skill's
self-check, and its `skip` (for example ESLint with no config in the project) is
reported as a skip, never as a pass.

A stage reporting "nine of ten gates passed" is a failure that needs a decision,
not a pass with a footnote. Surface it to the engineer with the failing gate
named.

## Quality gates

**Gate 1 — requirements decomposed**
- Every User Story has acceptance criteria in Given/When/Then
- Every requirement has a stable ID (`F-<TICKET>-<LAYER>-<NN>`)
- Non-functional requirements are present or explicitly marked N/A
- Attachments were parsed, not just listed
- Open questions are recorded in `OPEN_QUESTIONS.md`, not silently guessed
- `_index.json` is valid and machine-readable

**Gate 2 — scenarios generated**
- Valid against the scenario JSON schema
- Every scenario traces to at least one requirement ID
- Every requirement traces to at least one scenario (or is explicitly waived)
- Each step has action + input data + expected result — no placeholders
- Priorities assigned, no duplicate scenarios
- Both positive and negative cases exist for each acceptance criterion

**Gate 3 — automation generated**
- TypeScript compiles with zero errors (`tsc --noEmit`)
- ESLint passes
- No test without at least one assertion
- No hardcoded waits (`waitForTimeout`), no `test.only`, no commented-out tests
- Fixtures resolve; no import cycles
- Playwright config valid, projects and reporters declared
- Each test file maps to a scenario suite and carries the scenario ID in the title

**Gate 4 — tests debugged**
- Every failure is classified: test bug / product defect / environment / data
- Test bugs fixed; product defects marked `test.fail()` and linked to a ticket
- Mutation pass run — tests that survive inverted assertions are rejected

**Gate 5 — scenarios and code in sync**
- Scenario-to-code match ≥ 90%
- RTM regenerated and coverage reported

**Gate 2M — manual cases**
- Every acceptance criterion has a manual case, or a line under `## Not covered manually`
- The CSV imports: UTF-8 with BOM, one column count, ID / title / expected / reference columns
- Every case has an ID, a priority and a reference; no credential anywhere

**Gate E — manual execution**
- Every case in the round's pack has a result: pass, fail, fail (expected), blocked, skipped
- Every unexpected failure has an evidence file and a time
- No result is recorded for a case nobody executed

**Gate R — report**
- `summary`, per-test runs, stability and defect severities match the raw run reports and
  `bugs/`; the HTML loads nothing from the network

## Independent review

After Gate 1 and Gate 3 passed their own checks, a critic reviews the stage's artefacts against
`toolkit/rubrics/<requirements|code>.md`, before the stage is marked `passed`:

1. **Pick the most independent critic available.** A model of another vendor first: the
   `qa-critic` subagent in Cursor with `cursorModel` set to one, or `qa-critic run --backend
   codex|gemini|cursor-agent` when the profile's `INTEGRATIONS` has `llm-review`; then a local
   model (`--backend ollama`); otherwise the `qa-critic` subagent here (another Claude model in a
   fresh context, recorded as `same-vendor`). Never review in this conversation.
2. **Every disagreement is the engineer's decision.** `qa-critic record` puts each one in the
   stage's `needsEngineer`; batch them with the other open questions into one round. Record
   each answer: `qa-critic resolve <TICKET> <STAGE> <CR-n> --answer "…"`. An engineer who
   accepts the proposed default has still decided (`--by engineer`, the default); `--by default`
   is only for a default applied without an answer, which `qa-metrics` counts as silent consent. If an answer changes the work, re-delegate the stage
   with the answer in *Engineer decisions so far*, then run the critic again.
3. **The stage is `passed` only with no open disagreement**: `check-stage --require-passed`
   (G10) refuses it otherwise.

## Running without full access

Access requests routinely take days. Requirements decomposition and scenario
generation need nothing but the ticket and the global context, so run them while
the rest is pending rather than waiting. State clearly in the status report which
stages are deferred and on what.

## Status reporting

When the engineer asks for status, run `qa-pipeline status <TICKET>` and answer from it: it
reads `_pipeline.json`, the gate files' status, `counts` and `needsEngineer`, and the critic
files, grouped by track. Do not re-read artefacts for a status. The shape:

```
TICKET-123 — 7 of 11 stages passed · mode pipeline
  automated
    ✓ requirements-decomposer  passed · requirements 12 · openQuestions 4 · critic agree, 0 disagreement(s)
    ✓ scenarios-generator      passed · scenarios 38 · rtm 100%
    ⋯ automation-ui            running · tests 9/16
  manual
    ✓ manual-test-cases        passed · cases 41 · acCovered 10/10
    ⏸ test-execution           blocked · round 1 pack ready, waiting for a tester
  release
    · test-report              pending
  Needs you:
    - test-execution: who runs round 1, and on which build?
```

## What to hand back to the engineer, always

Never close a pipeline silently. The final message lists artefact paths, the
coverage number, anything marked as a suspected product defect, and every open
question. The engineer owns the decision; you own the preparation.
