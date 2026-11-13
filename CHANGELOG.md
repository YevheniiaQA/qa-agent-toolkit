# Changelog

Every change to a skill, agent, rule, hook or script gets a line here and a commit.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow [Semantic Versioning](https://semver.org/) as described in
[CONTRIBUTING.md](CONTRIBUTING.md).

## [Unreleased]

## [1.1.0] — 2026-11-13

### Added
- `install.sh --project DIR`: installs skills, agents and hooks into `DIR/.claude` only,
  for one project, without touching `~/.claude`, `~/.cursor` or `~/.qa-agent/bin`;
  `--uninstall` removes exactly what it installed.
- `bin/qa-check-isolation`: a fingerprint of the user-level setup to compare before and
  after, and a report of name clashes (`SHADOWED`, `DOUBLE`, `STALE`) for a project.
- `hooks/qa-path`: SessionStart hook of a project install that puts the toolkit's `bin/`
  on `PATH` for that project's sessions; `hooks/register.py --project DIR`.

### Changed
- `qa-env.sh` honours `QA_AGENT_HOME`, as the hooks already did.

## [1.0.0] — 2026-11-13

First public release.

### Added
- 35 skills covering the QA pipeline from a ticket to a report: project setup and access
  preflight, ticket fetch, requirements decomposition, scenario design, Playwright API and
  UI automation, manual cases and execution, debugging, reconciliation, TMS upload, PR
  delivery, reporting and metrics, plus contract, performance, security and exploratory
  testing, test plans, estimation and team agreements.
- 14 stage subagents (`qa-*`), one source each, built for Claude Code and Cursor by
  `bin/qa-build-agents`; shared text in `agents/_partials/`.
- Quality gates: `qa-gate` (every stage check), `qa-pipeline` (the only writer of pipeline
  state), `qa-critic` with rubrics for requirements and code.
- Hooks: `qa-guard` (integration boundary), `qa-stage-gate` (no stage done without its gate
  file) and `qa-test-lint` (generated test files checked on write).
- Metrics: `qa-event`, `qa-metrics` and a catalogue of 29 metrics with an HTML page each.
- JSON Schemas for gate files, pipeline state, critic verdicts, artefacts and metric events.
- Cursor rules, workspace templates (`AGENTS.md`, `CLAUDE.md`), `install.sh` and a
  pre-commit hook (`skill-lint`, agent build check).

[Unreleased]: https://github.com/YevheniiaQA/qa-agent-toolkit/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/YevheniiaQA/qa-agent-toolkit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/YevheniiaQA/qa-agent-toolkit/releases/tag/v1.0.0
