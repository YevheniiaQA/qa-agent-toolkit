---
name: project-setup
description: Onboards the QA agent onto a new project by creating its cascading environment profile, discovering repositories and documentation sources, and producing a readiness checklist. Use this skill as the very first action on any project the agent has not worked on before, whenever the user says "set up a new project", "onboard me onto X", "I have a new project to test", or when a pipeline run fails because no project profile exists. Also use it to add a sub-product profile to a project that already has one.
---

# Project Setup

The first skill to run on any new project. Everything downstream reads the
profile this skill creates, so a wrong value here surfaces as a confusing failure
three stages later.

The profile itself takes twenty minutes to write. Finding out what goes in it is
the actual work, and it is mostly asking people questions. Do that asking
efficiently: gather every unknown into one message rather than discovering them
one at a time over three days.

## Cascading configuration

Nothing is shared between projects except non-secret defaults. A token belongs to
the project it was issued for. A global Jira token lets an agent working on project B
file tickets in project A, and one wrong "file a bug" then lands in a real tracker.

```
~/.qa-agent/.env                              shared NON-secret defaults only — never tokens
  └── projects/<project>/profile.env          project settings, INTEGRATIONS list (no secrets)
        ├── projects/<project>/secrets.env    this project's tokens only (chmod 600), optional
        └── projects/<project>/profile.<sub>.env   sub-product overrides
```

The workspace selects its project with a one-line `.qa-project` file. A ticket key
(`PLAT-42` → `plat`) is the fallback when no `.qa-project` file is found. Load with
`source ~/.qa-agent/bin/qa-env.sh && qa_load`. It parses files literally and never
`source`s them, because a password containing a backtick or `$(...)` would otherwise run.

`INTEGRATIONS` lists the external systems the project may call. The names are the ones
`qa-guard` knows (`~/.qa-agent/toolkit/hooks/integrations.json`): `jira`, `confluence`,
`figma`, `testrail`, `zephyr`, `xray`, `qtest`, `github`, `gitlab`, `bitbucket`, `slack`,
`linear`, `pactflow`, `llm-review`. A skill whose system is not in the list skips it and
writes local files instead, and access-preflight reports it as disabled, not failed. A
training or local-only project has an empty list and no `secrets.env`.

The list is enforced, not only read. `qa-guard` runs before every shell command, web fetch
and MCP call in both IDEs and, inside a workspace with a `.qa-project`, lets through only:
local hosts and package registries, the hosts of the listed systems, the environment hosts
this profile names (a URL in any variable that is not an integration's, and `*_HOST`), read-only access to `GC_SOURCE_REPOS`
and `GC_SOURCE_DOCS`, and `NET_ALLOW`. A self-hosted system is recognised by its variable
(`JIRA_BASE_URL=https://jira.acme.com` makes that host Jira), so name it in the profile even
when the integration is off. Anything else is denied unless `QA_GUARD_UNKNOWN` says `ask` or
`allow`.

### Project profile template

```bash
# projects/plat/profile.env — project "Platform"
PROJECT_KEY=PLAT
PROJECT_NAME=Platform
INTEGRATIONS=jira,confluence,figma,testrail,github
JIRA_BASE_URL=https://acme.atlassian.net   # also marks a self-hosted Jira when the integration is off
TICKET_SOURCE=jira                 # jira | linear | local (markdown in the workspace)
DEFECT_SINK=jira                   # jira | linear | local ("file a bug" -> bugs/<id>.md)
NET_ALLOW=playwright.dev           # extra hosts any call may reach, comma-separated, * wildcards
QA_GUARD_UNKNOWN=deny              # deny | ask | allow, for hosts nothing above names

# Where the agent delivers work
API_TESTS_REPO=https://github.com/acme/platform-api-tests
UI_TESTS_REPO=https://github.com/acme/platform-ui-tests
TMS_PROJECT=Platform               # TestRail project name
TMS_ROOT_SECTION=Platform          # agreed root folder, see team-agreements

# Sources the global context is built from
GC_SOURCE_REPOS=https://github.com/acme/platform-backend,https://github.com/acme/platform-frontend
GC_SOURCE_API_URLS=https://platform.test.acme.com
GC_SOURCE_CONFLUENCE=https://acme.atlassian.net/wiki/spaces/PLAT/pages/78901

# Environments
API_BASE_URL=https://api.platform.test.acme.com

# UI targets — one block per distinct interface. A product is rarely one UI:
# a public site and an admin panel differ in domain, authentication, technology
# and risk, and collapsing them into a single UI_BASE_URL loses all of that.
UI_TARGETS=landing,admin

UI_landing_BASE_URL=https://platform.test.acme.com
UI_landing_AUTH=none
UI_landing_STACK=                     # detected

UI_admin_BASE_URL=https://admin.platform.test.acme.com
UI_admin_AUTH=session                 # none | session | token | sso
UI_admin_SESSION_TTL_MINUTES=120
UI_admin_ROLES=superuser,operator
UI_admin_STACK=
DB_HOST=pg-test.internal.acme.com
DB_NAME=platform
DB_READONLY=true                   # QA connects read-only unless explicitly agreed otherwise

# Test stack — drives which automation skill variant is generated
API_TEST_STACK=typescript-playwright   # or python-pytest
UI_TEST_STACK=typescript-playwright

# Product stack — leave blank, global-context-builder detects and fills these in
BACKEND_STACK=
FRONTEND_STACK=
API_SPEC_SOURCE=                       # auto: openapi-live | openapi-file | code-routes | graphql | postman
```

Secrets never go in a project profile. Tokens live in that project's
`secrets.env` (chmod 600, outside any repo) or in the OS keychain, never in the
shared base `.env`. `DB_PASSWORD` in a file that someone later
commits is a real incident, not a hypothetical.

## Discovery interview

Ask for everything at once. The list below is the full set — go through it, fill
in whatever you can find yourself, and send the remainder as a single message.

```markdown
## Setup questions for PLAT — please reply inline

**Repositories**
1. Which repos make up the product? (backend, frontend, shared services)
   — no need to tell me the languages or frameworks, I detect those from the code
2. Do QA automation repos already exist, or should I create them?
3. Which GitHub org/team should own the test repos?

**Documentation**
4. Where does the requirements documentation live? (Confluence space URL)
5. Is there an API spec anywhere — Swagger/OpenAPI URL, a spec file in the repo,
   a Postman collection, a GraphQL endpoint? Any one of these is enough.

**Environments**
6. Test environment URLs — the API, and **every** UI separately. A public site,
   an admin panel and a partner portal are three targets, not one.
6b. For each UI: how does login work, how long does a session last, and which
   roles do I need accounts for?
7. Is the test environment reachable without VPN?
8. Is there a deployment schedule I should avoid running tests during?

**Test management**
9. TestRail project name, and which section should be my root?
10. Does the team have an existing folder convention I should follow?

**Data**
11. Test accounts — which roles exist, and who issues them?
12. Read-only DB access on the test environment — possible, and through whom?
12b. Is the test environment shared with other teams, and is creating or deleting
   records there acceptable? If yes, are there constraints on what and when?

**People**
13. Who is my main contact for business-logic questions? (usually the analyst)
14. Who reviews generated scenarios before automation starts?
```

Questions 9, 10 and 14 look procedural and are not. Agreeing the TestRail folder
structure before the first upload avoids someone dragging two hundred cases
between folders by hand later, and agreeing the reviewer before generation avoids
producing fifty scenarios nobody asked for.

## What to discover without asking

Before sending the interview, use whatever access already exists:
- list repositories in the org matching the project name
- probe the common spec paths: `/openapi.json`, `/swagger.json`, `/v3/api-docs`,
  `/api-docs`, `/swagger/v1/swagger.json`, `/graphql` (introspection)
- read repo manifests to detect the stack, so the engineer is never asked
- check whether the TestRail project already has sections
- check whether the automation repos exist and what framework they already use

Every answer you find yourself is one fewer question in the message, and the
response rate on a short list is far better than on a long one.

## Output

```
~/.qa-agent/                   outside the workspace — never committed
├── .env                       shared non-secret defaults
└── projects/plat/
    ├── profile.env            this project's profile + INTEGRATIONS
    └── secrets.env            this project's tokens (chmod 600)

plat-qa/.qa-project            one line: plat
plat-qa/AGENTS.md              the project's rules for every agent (Cursor reads it directly)
plat-qa/CLAUDE.md              one line: @AGENTS.md (Claude Code reads the same text)

plat-qa/01-docs/process/       inside the workspace — the team can see it
├── SETUP_STATUS.md            readiness checklist, what is blocked and on whom
├── OPEN_REQUESTS.md           access requests filed, dates, ticket numbers
└── ENVIRONMENTS.md            URLs, accounts by reference, deploy windows
```

Start `AGENTS.md` from `~/.qa-agent/toolkit/templates/AGENTS.md` and fill in what this
project needs an agent to know: which integrations are off and what replaces them, how to
start the environment, which database role to use. Keep project rules there, never in
`CLAUDE.md` or in IDE-specific rule files, so both IDEs and every agent read one text.

`SETUP_STATUS.md` is the answer to "can I start working yet":

```markdown
# PLAT setup status — updated 2026-09-11

| Item | Status | Blocked on |
|---|---|---|
| Project profile | ✅ | |
| GitHub read access to source repos | ✅ | |
| Automation repos created | ⏳ | ServiceDesk REQ-88213, filed 09-09 |
| Jira read access | ✅ | |
| TestRail token | ✅ | |
| Test environment reachable | ❌ | VPN request REQ-88240, filed 09-09 |
| Read-only DB access | ⏳ | DBA — needs security justification |
| Figma MCP connected | ✅ | |
| Team agreements signed off | ⏳ | Call scheduled 09-12 |

**Can start now**: requirements decomposition, scenario generation (no live checks)
**Blocked**: selector collection, test execution, MR delivery
```

That last block matters. Access delays are not a reason to sit idle — requirements
work and scenario generation need no environment access at all, and running them
in parallel with the ServiceDesk queue is what turns a week of waiting into a week
of work.

## Parallelise the waiting

Access requests are a background process that blocks almost every other step, so
file them on day one before anything else. A realistic shape:

- **Day 1** — file every access request, build whatever context the available
  access allows, schedule the team call
- **Day 2** — partial access arrives; set up TestRail and repos, hold the call
- **Day 3** — remaining access arrives; verify end to end, run the first real ticket

If the organisation has SSO and a single service desk, this compresses to a day.
If it does not, plan for a week and say so up front rather than promising four hours.
