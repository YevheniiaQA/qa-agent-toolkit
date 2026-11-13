# Contributing

## Workflow

1. Edit the source here — `skills/`, `agents/`, `rules/`, `hooks/`, `bin/` — never the copies
   in an IDE folder.
2. Run the checks (the pre-commit hook installed by `install.sh` runs them too):

   ```bash
   bin/skill-lint
   bin/qa-build-agents
   ```

3. Add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
4. Open a pull request against `main`; CI runs the same checks.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <summary in the imperative, ≤ 72 chars>

<optional body: what and why, wrapped at 72>
```

| Type | Use for |
|---|---|
| `feat` | a new skill, agent, gate, check or command |
| `fix` | a bug fix |
| `docs` | README, CHANGELOG, skill wording that changes no behaviour |
| `refactor` | restructuring without a behaviour change |
| `ci` | `.github/` workflows |
| `chore` | tooling, ignore rules, housekeeping |

Scopes: `skills`, `agents`, `hooks`, `bin`, `rules`, `rubrics`, `schemas`, `metrics`,
`templates`, `install`, or a single skill/agent name (`feat(test-report): …`).
A change to an artefact contract (file names, JSON fields, gate IDs) is a breaking change:
add `!` after the scope and a `BREAKING CHANGE:` footer.

## Versioning

[Semantic Versioning](https://semver.org/), tagged `vX.Y.Z`:
major — a changed artefact contract; minor — a new skill, agent, gate or check;
patch — wording and fixes.

## Never commit

Tokens, `.env` files, project profiles or run output. Project data lives in
`~/.qa-agent/projects/<project>/`, outside this repository.
