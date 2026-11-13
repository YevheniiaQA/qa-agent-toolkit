---
name: access-preflight
description: Verifies every credential, token, endpoint, and network path the QA pipeline needs before a run starts, and reports exactly what is missing and who grants it. Use this skill before the first pipeline run on a project, whenever a stage fails with an auth, connection, or permission error, whenever the user asks "why can't the agent reach X", or as a periodic health check after token rotation. Also use it to generate the access request list for a new team member or a new project.
---

# Access Preflight

A pipeline that fails at stage 4 because a token expired has wasted everything
before it. Check first, fail fast, and fail with the name of the person who can
unblock it.

## The checklist

Run each check, report pass/fail with the specific error, and never guess at a
cause when the error text names one.

| System | Check | Scope needed | Who grants |
|---|---|---|---|
| Network / VPN | Reach the test environment | — | IT / ServiceDesk |
| Jira | Fetch a known ticket | read issues, create issues | Jira admin / project lead |
| Confluence | Fetch the documentation space | read space | Space admin |
| GitHub | Clone source repos, push a branch, open a PR | `repo`, `workflow` | Org owner / team lead |
| TestRail | List projects, read a section | read + write cases, manage sections | TestRail admin |
| API test env | `GET /health` returns 200 | — | DevOps |
| UI test env | Page loads, login succeeds | test accounts per role | DevOps / team |
| PostgreSQL | Connect read-only, run `SELECT 1` | read-only role, network path | DBA + security |
| Figma | Resolve a known file through MCP | view access to the project | Design lead |
| CI | Read workflow runs, read secret names | Actions read | DevOps |
| Integration guard | `qa-guard --check <a host of each disabled system>` prints `deny`; `--check $API_BASE_URL` prints `allow`; a declared source passes only as a read: `--check <a GC_SOURCE_REPOS url> --read` prints `allow`, without `--read` it prints `deny` by design | — | the engineer (`toolkit/install.sh`) |

## Check the object, not the credential

A token that authenticates is not access to the thing you need. "Jira reachable"
and "project SI readable" are different facts, and only the second one predicts
whether the pipeline can run. Every check resolves a **specific named object**
taken from the project profile:

| Instead of | Check |
|---|---|
| Jira token is valid | A known issue in the project's `JIRA_PROJECT` can be fetched, and a test issue can be created in the sandbox project |
| Figma token is valid | The file in `FIGMA_FILE_KEY` resolves and its pages can be listed |
| The admin panel is up | Login succeeds with the test account **and** the expected first screen renders |
| GitHub token works | The specific repositories in `GC_SOURCE_REPOS` clone, and a branch can be pushed to the test repo |
| The API is up | `/health` returns 200 **and** one real endpoint from the context returns the expected shape |

The failure this catches is the common one: everything authenticates, and the one
project you actually need is not in the token's scope.

## Keep the checks as scripts

Write each check as a small executable in `~/.qa-agent/bin/`, one per system,
parameterised by the project profile. Two reasons this is better than re-deriving
the check each time:

- **Re-runnable by anyone.** The engineer runs `qa-check-jira SI` after a token
  rotation without involving the agent at all.
- **They accumulate.** A check that once caught a real problem stays caught.

Keep them small, read-only, and silent on success — exit 0 with nothing, exit
non-zero with a message naming the object and the reason. A check that prints on
success gets ignored when it matters.

```bash
# ~/.qa-agent/bin/qa-check-jira — usage: qa-check-jira SI   (run inside the project's workspace)
set -euo pipefail
source "$HOME/.qa-agent/bin/qa-env.sh" && qa_load   # literal parse; never `source` an .env
qa_enabled jira || exit 0                            # disabled for this project: nothing to check
key="${1:?project key required}"
code=$(curl -s -o /dev/null -w '%{http_code}' -u "$JIRA_EMAIL:$JIRA_TOKEN"   "$JIRA_URL/rest/api/3/project/$key")
[ "$code" = 200 ] || { echo "Jira project $key not accessible (HTTP $code)"; exit 1; }
```

Never print a token, and never write one into a script file — read from the
environment every time.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations*. For a preflight that means: a system that is
not in `INTEGRATIONS` is reported as `➖ disabled for this project`, not ❌, and is not probed, not
even to check that a token works. The whole point of the list is that an agent on a training
project cannot reach a work tracker.

## Report format

```markdown
# Access preflight — PLAT — 2026-09-11 14:02

✅ Jira            PLAT-1 fetched, 0.4s
✅ GitHub          3 repos readable; push to platform-api-tests OK
✅ TestRail        project "Platform" found, 2 sections
❌ API environment https://api.platform.test.acme.com — connection timed out
   → Likely VPN. Check the tunnel; if connected, ask DevOps whether the host is
     allowlisted for the QA subnet.
⚠️  PostgreSQL     connected, but the role has write permission
   → Request a read-only role. Write access on a shared test DB is one bad query
     away from blocking the whole team.
❌ Figma           MCP server not responding
   → Reconnect the Figma MCP server in settings, then re-run.

**Verdict**: cannot run UI stages or live checks. Requirements decomposition and
scenario generation can proceed against the existing global context.
```

Always end with a verdict that names what can still run. "Blocked" without that
line sends the engineer away for a day that could have been productive.

## Rules

**Never print a token value**, not even partially, not even in a debug report.
Report the variable name and whether it resolved.

**Distinguish missing from expired.** A 401 on a token that worked yesterday is a
rotation event, not a permissions problem, and the fix is different.

**Read-only is the default for the database.** If the connection turns out to have
write permission, say so as a warning rather than accepting it quietly. A QA agent
with write access to a shared test database is an unnecessary risk.

**Do not request access yourself.** Produce the exact request text the engineer
can paste into a service desk ticket, including the scope and a one-line
justification — security teams ask for the justification every time, and having
it ready saves a round trip.

## Self-check before reporting completion

One entry per row of *The checklist*, in its order, then the two rules. A system that
is not in `INTEGRATIONS` is `n/a` with "disabled for this project" as evidence, never
`fail`; a system that is enabled and fails its check is `fail`.

1. **Network / VPN**: the test environment is reachable.
2. **Jira**: a known ticket is fetched and a sandbox issue can be created.
3. **Confluence**: the documentation space is read.
4. **GitHub**: the repositories in `GC_SOURCE_REPOS` are readable; push and PR where enabled.
5. **TestRail**: projects are listed and a section is read.
6. **API test env**: `GET /health` returns 200 and one real endpoint has the expected shape.
7. **UI test env**: the page loads, the expected first screen renders, login works if required.
8. **PostgreSQL**: connects as the read-only role, `SELECT 1` works, no write grants.
9. **Figma**: `FIGMA_FILE_KEY` resolves through MCP.
10. **CI**: workflow runs and secret names are readable.
11. **Integration guard**: every disabled system's host is denied, the API host is allowed, and
    each declared source is allowed with `--read` (and denied without it).
12. **No token value** was printed or written anywhere, and missing is told apart from expired.
13. **The verdict names what can still run.**
