# QA agent toolkit

[![CI](https://github.com/YevheniiaQA/qa-agent-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/YevheniiaQA/qa-agent-toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

35 skills and 14 stage subagents that turn **Claude Code** and **Cursor** into a QA
engineer's pipeline: from a ticket URL to requirements, scenarios, Playwright API/UI tests,
manual cases, a readable report and metrics, with a quality gate between every stage.

Nothing here belongs to one project: every project selects its own settings at run time
(see *Projects* below), and no secrets or project data live in this repository.

## Quick start

Requirements: macOS or Linux, `bash`, `git`, Python 3.9+ (standard library only), and
Claude Code and/or Cursor.

```bash
git clone https://github.com/YevheniiaQA/qa-agent-toolkit.git ~/.qa-agent/toolkit
~/.qa-agent/toolkit/install.sh --dry-run    # see what would change
~/.qa-agent/toolkit/install.sh              # symlink skills, agents, rules and bin; register hooks
```

Then, in a QA workspace, ask the agent to *"run the QA pipeline for <ticket URL>"* —
`qa-orchestrator` takes it from there. On a new project start with `project-setup`.

## Skills

| Skill | What it does |
|---|---|
| [`access-preflight`](skills/access-preflight/SKILL.md) | Verifies every credential, token, endpoint, and network path the QA pipeline needs before a run starts, and reports exactly what is missing and who grants it |
| [`artifact-retention`](skills/artifact-retention/SKILL.md) | Keeps the QA working repository small by retaining only the last few runs of heavy artefacts per service and target, while preserving the small derived history that trends and baselines depend on |
| [`automation-api`](skills/automation-api/SKILL.md) | Generates a runnable TypeScript API test project from scenario JSON using Playwright's APIRequestContext, with typed clients, fixtures, schema validation, and full traceability back to requirement IDs |
| [`automation-compare`](skills/automation-compare/SKILL.md) | Verifies that generated Playwright tests actually implement the scenarios they claim to, step by step, and reports a match percentage plus a regenerated requirements traceability matrix |
| [`automation-ui`](skills/automation-ui/SKILL.md) | Generates a runnable TypeScript Playwright UI test project from scenario JSON and validated page objects, with API-based setup, web-first assertions, accessibility checks, and requirement traceability |
| [`ci-setup`](skills/ci-setup/SKILL.md) | Creates or repairs GitHub Actions workflows that run the generated Playwright suites, publish reports, and push results back to TestRail |
| [`contract-testing`](skills/contract-testing/SKILL.md) | Sets up and maintains consumer-driven or bi-directional contract tests between services using Pact, plus schema-level contract checks against an OpenAPI document, and wires can-i-deploy as a release gate |
| [`critic-review`](skills/critic-review/SKILL.md) | Reviews one QA pipeline stage's artefacts against a fixed rubric (toolkit/rubrics/*.md) as an independent critic, and records the verdict and every disagreement with evidence, so the engineer decides each one |
| [`db-validator`](skills/db-validator/SKILL.md) | Prepares test data and verifies system state directly in PostgreSQL — seeding preconditions, asserting postconditions the API does not expose, and diagnosing failures that look like application bugs but are data problems |
| [`discrepancies-fix`](skills/discrepancies-fix/SKILL.md) | Classifies and resolves contradictions between requirements, designs, API contracts, and actual system behaviour, auto-closing the unambiguous ones by source-priority rules and escalating real defects to the engineer with a ready-made bug report |
| [`exploratory-testing`](skills/exploratory-testing/SKILL.md) | Plans and records session-based exploratory testing — time-boxed charters aimed at what scripted cases cannot cover, with session notes, findings and coverage of the areas explored |
| [`figma-analyzer`](skills/figma-analyzer/SKILL.md) | Reads Figma designs through MCP and extracts UI elements, states, texts, and constraints into structured data that UI scenario generation and selector collection can consume |
| [`global-context-builder`](skills/global-context-builder/SKILL.md) | Builds, updates, cleans, and rolls back the project knowledge base that every other QA skill reads from — service map, test data, business specification, technical requirements, API specs, and frontend map — assembled automatically from source repositories, live OpenAPI endpoints, and Confluence |
| [`manual-test-cases`](skills/manual-test-cases/SKILL.md) | Writes manual test cases in the field structure test management systems expect, and exports them as CSV or XLSX ready to import into TestRail, Xray, Zephyr Scale, qTest or Azure Test Plans |
| [`performance-testing`](skills/performance-testing/SKILL.md) | Builds and runs k6 performance tests — smoke, load, stress, spike, soak and breakpoint — with thresholds as pass/fail gates, and produces a performance report with percentiles, saturation point and regression against a baseline |
| [`pr-creator`](skills/pr-creator/SKILL.md) | Integrates a generated Playwright test project into the target automation repository and opens a pull request, resolving fixture conflicts, dependency mismatches, and config drift first |
| [`project-setup`](skills/project-setup/SKILL.md) | Onboards the QA agent onto a new project by creating its cascading environment profile, discovering repositories and documentation sources, and producing a readiness checklist |
| [`qa-conventions`](skills/qa-conventions/SKILL.md) | Conventions every QA skill shares — where run output goes and how runs are recorded, how a disabled integration is handled, how a lesson is recorded |
| [`qa-metrics`](skills/qa-metrics/SKILL.md) | Assembles QA metrics and trends for a retrospective or a quality review — escaped defects, where defects were caught, coverage movement, suite stability and runtime, requirement quality signals — with the reasoning behind each number rather than a dashboard |
| [`qa-orchestrator`](skills/qa-orchestrator/SKILL.md) | Coordinates the full QA pipeline from a ticket URL to merged automated tests |
| [`regression-manager`](skills/regression-manager/SKILL.md) | Manages the regression suite over time — verifying fixes, removing expected-failure markers when defects are resolved, merging new tests into the regression set with the right tags, retiring obsolete tests, and triaging flakiness before it erodes trust |
| [`requirements-decomposer`](skills/requirements-decomposer/SKILL.md) | Turns raw ticket text into structured User Stories and Tasks with atomic functional requirements, non-functional requirements, and Given/When/Then acceptance criteria, each carrying a stable ID for traceability |
| [`scenario-data-fix`](skills/scenario-data-fix/SKILL.md) | Resolves missing test data placeholders in generated scenarios by looking them up in the project global context first and asking the engineer only for what genuinely cannot be derived |
| [`scenarios-generator`](skills/scenarios-generator/SKILL.md) | Generates structured test scenarios from decomposed requirements using ISTQB test design techniques, and produces a requirements traceability matrix showing coverage |
| [`security-testing`](skills/security-testing/SKILL.md) | Runs QA-level security testing across the API, backend, frontend and the test suite itself — authorisation boundaries from the OWASP API Security Top 10, common web risks, dependency and secret exposure — and produces a findings report with evidence and severity |
| [`selectors-collector`](skills/selectors-collector/SKILL.md) | Collects and validates resilient Playwright locators from the live DOM and emits a typed page-object map for UI test generation |
| [`team-agreements`](skills/team-agreements/SKILL.md) | Produces the written working agreement between the QA engineer and the product team — ticket flow, artefact review responsibilities, defect handling, communication cadence — and the half-page document that gets signed off |
| [`test-debugger`](skills/test-debugger/SKILL.md) | Debugs generated or failing Playwright tests in two passes — a functional pass that classifies each failure as test bug, product defect, environment, or data issue, and a mutation pass that inverts assertions to catch tests which assert nothing |
| [`test-estimation`](skills/test-estimation/SKILL.md) | Produces QA effort estimates and testability risk assessments for sprint planning — how long testing a story will take, what makes it risky, and what would have to be true before it can be tested at all |
| [`test-execution`](skills/test-execution/SKILL.md) | Prepares everything a manual tester needs to run a set of test cases, and records what happened — an execution pack with environment, accounts, build and ordered cases, then results with evidence, defects captured during the run, and a handoff back to the pipeline |
| [`test-plan`](skills/test-plan/SKILL.md) | Writes the test plan for a release, an epic or a project — scope, approach per layer, environments and data, entry and exit criteria, risks and what will not be tested |
| [`test-report`](skills/test-report/SKILL.md) | Builds a self-contained HTML report from a test run that non-engineers can read — requirement coverage, deliberate failures with their defect references, a manual-executable test catalogue, stability across runs, and the environment the numbers came from |
| [`ticket-fetch`](skills/ticket-fetch/SKILL.md) | Pulls a ticket and everything attached to it out of Jira, Linear, or Confluence and turns it into clean local markdown the rest of the QA pipeline can read |
| [`tms-uploader`](skills/tms-uploader/SKILL.md) | Publishes scenario JSON as test cases into TestRail (or Zephyr Scale, Xray, qTest) with the agreed section hierarchy, priorities, labels, and requirement links, then writes the case IDs back into the automated tests so code and TMS stay linked |
| [`workspace-index`](skills/workspace-index/SKILL.md) | Generates and refreshes the navigation layer of the QA workspace — the root README that explains where everything lives, a README per ticket routing each role to what they need, and an audit for artefacts nothing links to |

## Stage subagents

Each pipeline stage runs in its own isolated context, so a long run does not exhaust the
main conversation. Sources live in `agents/`; `bin/qa-build-agents` writes a Claude Code and
a Cursor build of each to `build/`.

| Agent | What it does |
|---|---|
| [`qa-automation-api`](agents/qa-automation-api.md) | Runs automation-api in an isolated context: generates the Playwright API test project from scenario JSON |
| [`qa-automation-ui`](agents/qa-automation-ui.md) | Runs automation-ui in an isolated context: generates the Playwright UI test project from scenario JSON and validated page objects |
| [`qa-context`](agents/qa-context.md) | Runs global-context-builder in an isolated context: builds, refreshes or rolls back the project knowledge base under 01-docs/context |
| [`qa-critic`](agents/qa-critic.md) | Independent critic for one QA pipeline stage: reviews its artefacts cold against toolkit/rubrics/*.md and records agree / disagree per item, with every disagreement as a question for the engineer |
| [`qa-debugger`](agents/qa-debugger.md) | Runs test-debugger in an isolated context: classifies failures of a generated suite and runs the mutation pass |
| [`qa-housekeeping`](agents/qa-housekeeping.md) | Runs artifact-retention or workspace-index in an isolated context — the mechanical end-of-run upkeep of the QA workspace |
| [`qa-manual`](agents/qa-manual.md) | Runs manual-test-cases then test-execution in one isolated context: turns scenarios into manual cases with a TMS import file, then prepares the execution pack and records the results of a round |
| [`qa-preflight`](agents/qa-preflight.md) | Runs access-preflight in an isolated context: verifies credentials, endpoints and network paths for the QA pipeline and reports what is missing |
| [`qa-report`](agents/qa-report.md) | Runs test-report then qa-metrics in one isolated context: builds the self-contained REPORT.html for a ticket from the recorded runs and the manual round, and the metrics summary next to it |
| [`qa-requirements`](agents/qa-requirements.md) | Runs ticket-fetch then requirements-decomposer in one isolated context: turns a ticket into structured stories, requirements and acceptance criteria |
| [`qa-scenarios`](agents/qa-scenarios.md) | Runs scenarios-generator in an isolated context: produces scenario JSON and the RTM from decomposed requirements |
| [`qa-selectors`](agents/qa-selectors.md) | Runs selectors-collector in an isolated context: collects and validates Playwright locators against the live DOM and writes page objects |
| [`qa-special`](agents/qa-special.md) | Runs one of contract-testing, performance-testing or security-testing in an isolated context, the one the delegation prompt names |
| [`qa-sync`](agents/qa-sync.md) | Runs automation-compare and scenario-data-fix in one isolated context: checks scenario↔code match, regenerates the RTM and resolves data placeholders |

## Layout

| Folder | Holds | Connected to |
|---|---|---|
| `skills/` | one folder per skill, `SKILL.md` + optional `references/` | `~/.cursor/skills/<name>`, `~/.claude/skills/<name>` (symlinks) |
| `agents/` | stage agents (`qa-*`), one source each; `bin/qa-build-agents` writes a Claude and a Cursor build to `build/` | `~/.claude/agents`, `~/.cursor/agents` (symlinks to `build/<ide>/agents/`) |
| `rules/` | IDE rules (`.mdc`) | `~/.cursor/rules` |
| `hooks/` | `qa-guard` (integration boundary) + `integrations.json`, `prices.json` (stage cost), `qa-stage-gate` (no stage done without its gate file), `qa-test-lint` (test files checked on write), `register.py` | `~/.claude/settings.json`, `~/.cursor/hooks.json` (registered by `install.sh`) |
| `bin/` | `qa-gate`, `qa-pipeline`, `qa-critic`, `qa-guard`, `qa-build-agents`, `skill-lint`, `qa-event`, `qa-metrics`, `qa-env.sh`, `qa-check-*`, `qa-prune` | `~/.qa-agent/bin` (symlink, on `PATH`) |
| `templates/` | `AGENTS.md` and `CLAUDE.md` for a new workspace | copied by project-setup |
| `schemas/` | JSON Schemas for gate files, pipeline state, artefacts, metric events | read by `qa-gate` |
| `metrics/` | `catalog.json`: every metric's description, formula and cadence | read by `qa-metrics --html` |
| `rubrics/` | review rubrics for the critic (`requirements.md`, `code.md`) | read by `qa-critic` and the `qa-critic` agent |
| `githooks/` | `pre-commit`: skill-lint, `qa-build-agents --check` | `core.hooksPath` (set by `install.sh`) |

An agent is edited in `agents/`, never in an IDE folder: Claude Code gets the frontmatter as
written (preloaded `skills`, `disallowedTools`); Cursor gets `name`, `description`, `model`
(`haiku` becomes `fast`) and a first instruction to read each skill's `SKILL.md`, since it
does not preload skills. Run `install.sh` (or `qa-build-agents`) after a change;
`qa-build-agents --check` fails while a build is out of date.

## Gates

| When | What runs | Effect |
|---|---|---|
| a test file is written | `qa-test-lint` | `.only`, `waitForTimeout`, status ranges, weakened assertions reported to the agent at once |
| a `qa-*` stage agent stops | `qa-stage-gate` → `qa-gate check-stage` | sent back (up to 3 times) while its gate file is missing or incomplete |
| the session stops | `qa-stage-gate` → `qa-gate check-pipeline` | cannot end while a stage marked passed fails its gate |
| the orchestrator marks a stage passed | `qa-pipeline set <T> <S> passed` → `qa-gate check-stage --require-passed` | refused while the gate file fails or a critic disagreement is open |
| Gate 1 or 3 has passed | the `qa-critic` agent (or `qa-critic run` on another vendor) against `rubrics/` | each disagreement becomes a question for the engineer (`qa-critic resolve`) |
| a toolkit commit | `githooks/pre-commit` | refused while skill-lint, the agent build or a test fails |

Every rule lives in `qa-gate`, so a hook, an agent and a person run the same check.
`qa-pipeline status <T>` shows every stage by track, critic results and what waits on the engineer.

## Metrics

One file per workspace, `05-metrics/events.jsonl`, append-only and validated against
`schemas/metric-event.schema.json`. Only three things write it, each from a file:

| Writer | Event | From |
|---|---|---|
| `qa-stage-gate` hook | `stage`: attempt, gate decision, status, artefact hashes, tokens, cost, duration | the gate file and the subagent transcript |
| `qa-gate … --write <stage>` | `gate`: command, exit code, check counts | its own result |
| `qa-event` | `run`, `mutation`, `triage`, `defect`, `decision`, `session`, `counts` | a Playwright report, a session sheet, a defect file… |

```bash
qa-event migrate      # once per workspace: older 05-metrics/*.jsonl and Playwright reports -> events
qa-metrics            # defects (DDP, leakage, rejection, reopen), coverage, SBTM, stability,
                      # false failure rate, mutation score, first-pass gate rate, stage cost,
                      # human edit rate, decisions by silent consent
qa-metrics --json     # the same, plus every catalogue metric, for test-report and comparisons
qa-metrics --html [--since 2026-11-01]   # 05-metrics/index.html + one page per metric
```

`metrics/catalog.json` is the one description of every metric (29: escaped defects, DDP,
leakage, regression and test effectiveness, critical and customer-impacting defects,
incidents, automation reliability, flaky rate, execution time, mutation score, MTTR, ageing,
risk and journey coverage, release quality, process and pipeline metrics): what it is, the
formula, how it is computed here, its cadence (after a run, across runs, per ticket, per
sprint or release), how to read it and its traps. `--html` renders it with this workspace's
values; `bin/qa_metric_values.py` holds one function per metric. Production facts come in
through `qa-event defect … --phase production [--customer-impact] [--regression]`,
`qa-event incident` and `qa-event release`.

A metric without data prints `n/a` and what would produce it. Prices in `hooks/prices.json`
are API list prices; on a subscription the cost is the API equivalent.

## The integration boundary

`qa-guard` runs before every shell command, web fetch and MCP call in both IDEs. In a
workspace with a `.qa-project` it allows only local hosts and registries, the systems in
the profile's `INTEGRATIONS`, the environments the profile names, read-only access to
`GC_SOURCE_REPOS` / `GC_SOURCE_DOCS`, and `NET_ALLOW`; a host of a known system that is not
enabled is always denied. Outside a QA workspace it does nothing.

```bash
qa-guard --check https://acme.atlassian.net/browse/X-1     # what would happen here, and why
~/.qa-agent/toolkit/hooks/register.py --remove             # take the hooks out of both IDEs
```

Denials are logged (hosts and systems only, never the command) to
`~/.qa-agent/logs/qa-guard.jsonl`. New system: add it to `hooks/integrations.json` with its
hosts, profile variables, CLI commands and MCP keywords.

It reads command lines, so a script file that calls a tracker on its own is not seen.
Not giving a project the token stays the real boundary.

## Install on a machine

See *Quick start* above.

If an IDE does not pick up symlinked skills, use `install.sh --copy` and re-run it
after every change. `install.sh` never deletes: whatever is in the way goes to
`~/.qa-agent/backups/install-<timestamp>/`.

## Projects

Project-specific data never goes into this repository:

| What | Where |
|---|---|
| project settings, `INTEGRATIONS` | `~/.qa-agent/projects/<project>/profile.env` |
| project tokens | `~/.qa-agent/projects/<project>/secrets.env` (chmod 600) |
| which project a workspace is | `<workspace>/.qa-project` (one line) |
| project rules for the agent | `<workspace>/CLAUDE.md` / `AGENTS.md` |
| shared non-secret defaults | `~/.qa-agent/.env` |

Skills use examples (ticket keys, endpoints) for illustration only; anything a run
depends on comes from the loaded profile (`source ~/.qa-agent/bin/qa-env.sh && qa_load`).

## Changing the toolkit

1. Edit the file here (the IDE folders point here, so the change is live in both).
2. Add a line under `## [Unreleased]` in `CHANGELOG.md`.
3. Commit following [CONTRIBUTING.md](CONTRIBUTING.md) (Conventional Commits, e.g.
   `feat(skills): add contract-testing`).
4. Release: move the Unreleased lines under a new version and `git tag vX.Y.Z`.
   Major: a changed artefact contract (file names, JSON fields, gate IDs).
   Minor: a new skill, agent, gate or check. Patch: wording and fixes.

## License

[MIT](LICENSE)
