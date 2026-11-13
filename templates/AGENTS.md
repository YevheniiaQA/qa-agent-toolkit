# <Project name> — QA workspace

QA project profile: `<project>` (see `.qa-project`, settings in `~/.qa-agent/projects/<project>/profile.env`).
Load env with: `source ~/.qa-agent/bin/qa-env.sh && qa_load`

<!-- This file holds the project's rules for every agent. Cursor reads it directly;
     CLAUDE.md contains only "@AGENTS.md" so Claude Code reads the same text.
     Keep project rules here, never in IDE-specific rule files. -->

## Integrations
`INTEGRATIONS` = <the list from the profile, or "empty">. Every other system is disabled on
purpose, and `qa-guard` blocks it in both IDEs.
- Requirements come from: <Jira project / Linear team / local markdown in this workspace>.
- "File a bug" / "заведи баг" means: <create an issue in ..., after one confirmation per
  ticket / write `bugs/<id>.md` here>.
- Test cases go to: <TMS project and section / CSV or XLSX export from manual-test-cases>.
- Skills that need a disabled system are skipped or use their local alternative; in
  access-preflight they are "➖ disabled for this project", not ❌.
- Never read another project's files under `~/.qa-agent/projects/`.

## Environment
<How to start it (command), where the API and UI live, which database role agents use and
which role needs the engineer's approval for a write.>

## Rules that need the engineer
<Destructive or outward-facing actions that must be confirmed first, and anything an agent
must never do in this project.>
