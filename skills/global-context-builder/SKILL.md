---
name: global-context-builder
description: Builds, updates, cleans, and rolls back the project knowledge base that every other QA skill reads from — service map, test data, business specification, technical requirements, API specs, and frontend map — assembled automatically from source repositories, live OpenAPI endpoints, and Confluence. Use this skill when onboarding onto a new project, when the user says "build the context for project X", when generated tests reference endpoints that do not exist, when architecture or contracts have changed, or before the first pipeline run. Also use it to refresh a stale context or to roll back a bad update.
---

# Global Context Builder

Without this, scenario generation produces plausible rubbish — well-formed tests
against endpoints that were never built. With it, tests bind to real contracts.

It is also the fastest onboarding available: thirty minutes after it runs, a newcomer
has a dossier of services, roles, endpoints and data.

Expect the first build to yield roughly 70–80% of what is eventually needed. The
remainder accumulates during real work — `scenario-data-fix` finds gaps in
`test_data.yaml` on the first scenario run and offers to fill them. Do not chase
completeness on day one.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for the wiki, the tracker or the git host
(`confluence`, `jira`, `github`): read `INTEGRATIONS`, skip a system that is not listed, report it
as `➖ <system> disabled for this project`, never route around a `qa-guard` block.

**What stays available:** repositories listed in `GC_SOURCE_REPOS` and pages under `GC_SOURCE_DOCS` are declared sources and may be cloned or read even when their host's integration is off; the guard allows read-only access to exactly those addresses and nothing else on the host. Confluence and Jira context needs the integration; without it, record the gap in the context and continue in degraded mode.

## Modes

| Mode | What it does | When |
|---|---|---|
| `build` | Full assembly from scratch | New project |
| `update` | Adds new findings, shows a diff, asks per change | New service, new endpoints, contract change |
| `cleanup` | Verifies every entry still exists, removes dead ones | Quarterly, or after a big refactor |
| `rollback` | Restores a previous snapshot | A bad update polluted the context |

Snapshot before every write. A git commit in the context directory is enough, and
it is what makes `rollback` a real option rather than a promise. `cleanup` and `rollback`
never touch `01-docs/context/lessons/`: lessons are not part of the knowledge base
(see `qa-conventions` → *Lessons*).

## Stack and endpoints

Detect the stack from the sources, never assume it, and take endpoints from the
highest-trust source available, cross-checked against the next one down: live OpenAPI,
then a spec file, then routes in code, then collections, HAR captures and frontend calls.
A disagreement between two sources is a finding, never a silent pick. Everything is
normalised to one protocol-agnostic endpoint shape.

Read `references/stack-and-endpoints.md` before extraction: the manifest table, where each
framework keeps routes, validation and config, the fallback when nothing matches, and the
full source-trust table. When the project has no repository and no specification, read
`references/degraded-mode.md`: build from what is observable, label every entry
`read | observed | inferred`, and list `blindSpots`.

## Sources and priority

Read `GC_SOURCE_*` from the project profile (`source ~/.qa-agent/bin/qa-env.sh && qa_load`). If those are
absent, fall back to interactive discovery: list org repositories, probe common
OpenAPI paths, ask which Confluence space holds the documentation.

| Priority | Source | Used for |
|---|---|---|
| P1 | Source repositories | Structure: services, endpoints, stack, data models, CI config |
| P2 | Live OpenAPI / GraphQL / proto / Postman | Cross-check against what the code says |
| P3 | Confluence / Jira | Business context: roles, processes, use cases |
| P4 | Existing TestRail cases | Observed correct behaviour, reconstructed from tests |

**Conflict rule, and it is not symmetric.** For *behaviour* — what the system
should do, which status code, which validation — **requirements win over code**,
because code is an implementation that may contain the defect you are about to
find. For *structure* — which services exist, which endpoints are deployed, what
the stack is — **code wins**, because it is the fact on the ground.

Getting this backwards is how a pipeline quietly ratifies bugs as requirements.

## Output files and priorities

`_index.json` records the detected stack (`references/templates.md` has the block) so every
downstream skill can adapt without being told.


```
01-docs/context/
├── services_endpoints.yaml           P0  service map, URLs per environment
├── test_data.yaml                    P0  test accounts, roles, seed data
├── FULL_SPECIFICATION.md   P1  business logic, roles, processes, glossary
├── TECHNICAL_REQUIREMENTS.md P1 architecture, stack, DB, integrations, auth
├── api/<service>.yaml                P1  normalised endpoint spec per service
├── stack.md                          P1  detected languages, frameworks, build and run
├── web_<app>.md                      P2  routing, forms, frontend API calls
├── db_schema.md                      P2  tables, keys, constraints, enums
├── actual_features.md                P3  behaviour reconstructed from existing test cases
└── _index.json                           metadata: sources, timestamps, gaps
```

### Required deliverables — a build is not complete until all of these exist

The tree above is a map, not a menu. Every P0 and P1 file is mandatory on a
`build` run. Work through this checklist explicitly and confirm each item before
reporting the build as done:

- [ ] `services_endpoints.yaml` — every endpoint, with `source` references
- [ ] `test_data.yaml` — created even when empty, with a `gaps` comment listing
      what still needs supplying
- [ ] `api/<service>.yaml` — **one per service**, in OpenAPI shape, regardless of
      whether the original source was OpenAPI, GraphQL, proto, or a collection.
      Copying a live spec verbatim is acceptable; producing nothing is not.
- [ ] `FULL_SPECIFICATION.md` — all six sections, even where a section
      reads "not determinable from available sources" with the reason
- [ ] `TECHNICAL_REQUIREMENTS.md` — all seven sections, same rule
- [ ] `stack.md` — detected stack with the evidence for each conclusion
- [ ] `_index.json` — sources, timestamps, gaps, and the stack block

P2 and P3 files are genuinely conditional: skip them when the project has no
frontend, no database, or no existing test cases, and record the skip in
`_index.json` under `skipped` with the reason.

**A missing P1 file is a failed build, not a partial one.** Downstream skills
read these by name. `automation-api` will follow the load instruction in
`_index.json`, find nothing, and generate tests against guesses — which surfaces
three stages later as inexplicably wrong endpoints.

### Self-check before reporting completion

Do not describe the build as finished until all four of these pass:

1. **Every required file exists and is non-empty.** List the directory and
   compare against the checklist above. State the comparison in your report.
2. **No dangling references.** Every filename mentioned in `_index.json`
   (especially in any load instruction for downstream skills) resolves to a file
   that was actually written.
3. **Every markdown deliverable has all its template sections present**, even if
   some are marked as undetermined.
4. **Endpoint count is consistent** between `services_endpoints.yaml` and the
   `api/<service>.yaml` files.

If a check fails, write the missing artefact before reporting. If it cannot be
written — the source genuinely does not exist — say so explicitly and record it
in `gaps`. Silence is the failure mode; an honest gap is fine.

When resuming an incomplete build, run in `update` mode scoped to the missing
files rather than rebuilding. P0 output that has already been verified should not
be churned.

Priorities: **P0** tests cannot run without it · **P1** scenario quality depends on it ·
**P2** improves UI and data-layer tests · **P3** generated automatically, never hand-edited.

Each file carries a metadata header: which sources it came from, when it was
created, when it was last updated, and which commit of the source repo it
reflects. Context without provenance cannot be audited or refreshed safely.

## Fixed templates, not free form

Every file follows a fixed section structure; read `references/templates.md` before writing
or checking one. `FULL_SPECIFICATION.md` has exactly six headings and
`TECHNICAL_REQUIREMENTS.md` exactly seven, in the template's order. Where a section cannot be
filled, keep the heading and write one line stating what is missing and why. Every
`api/<service>.yaml` is OpenAPI-shaped whatever the source was, and every endpoint in
`services_endpoints.yaml` carries a `source` reference — that is what makes `cleanup` and
`update` possible.

## test_data.yaml is append-only

Data is added, never deleted. Something that looks obsolete gets a `# deprecated` comment and
stays: an extra line costs nothing, a deleted test user costs a red suite and an hour of
confused debugging. Credentials are referenced by environment variable name
(`password_env: QA_ADMIN_PASSWORD`), never by value; the file is committed, the values are not.

## Validation pass

Before writing, verify rather than trust:
- every endpoint exists in the current code or the live OpenAPI document
- every service answers on its health path
- every environment variable referenced exists in the current CI config
- every Confluence page cited still resolves

Entries that fail validation are marked `unverified` with the reason rather than
dropped — a genuinely missing health endpoint is itself a finding.

## Keeping it compact

Downstream skills load this repeatedly, and approaching the context limit degrades
output quality long before it overflows. Budget roughly: technical requirements
under 300 lines, each API file under 400, specification under 250. Skills load
only the service files relevant to their ticket, never the whole directory —
state that requirement explicitly in `_index.json`.

When a service exceeds its budget, split by bounded context rather than truncating.

## Gaps

Whatever could not be determined goes into `_index.json` under `gaps`, with the
reason. Silent guesses are the exact failure mode this skill exists to prevent,
and a listed gap is something `scenario-data-fix` can pick up later.

## Keep the heavy inputs out of the repository

HAR captures and other heavy inputs go to `.runs/context/<timestamp>/`, never into the context
directory, and are never committed: a HAR may hold session cookies and personal data. Details
in `references/degraded-mode.md`.
