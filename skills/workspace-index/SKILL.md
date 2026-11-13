---
name: workspace-index
description: Generates and refreshes the navigation layer of the QA workspace — the root README that explains where everything lives, a README per ticket routing each role to what they need, and an audit for artefacts nothing links to. Use this skill as the last step of every pipeline run, when someone new opens the repository, when the user asks where something is or what state a ticket is in, or when the workspace has drifted from the standard layout. Also use it to move a workspace onto the standard layout.
---

# Workspace Index

Artefacts nobody can find are artefacts that do not exist. This skill makes the
workspace self-explanatory to someone opening it for the first time, and keeps it
that way.

The layout itself is defined in `docs/LAYOUT.md` in the skills repository. This
skill enforces and explains it; it does not invent its own.

## The root README

The first thing anyone sees. It answers three questions in order: what is this,
where does everything live, and where do I start.

```markdown
# Platform — QA workspace

Testing for the Platform product: requirements analysis, manual and automated
tests, results and reports. Generated and maintained by the QA agent pipeline.

## Where things live

| Folder | What is in it |
|---|---|
| [`01-docs/`](01-docs/) | **Everything about the product and the process.** How the system works, the test plan, environments and accounts, the working agreement |
| [`02-analysis/`](02-analysis/) | **Per ticket — understanding before testing.** Requirements, scenarios, open questions for the analyst |
| [`03-tests/`](03-tests/) | **Everything executable, organised by feature.** Manual cases, API and UI automation, contract, performance and security tests |
| [`04-results/`](04-results/) | **Per ticket — what happened.** Execution packs, results, defects, evidence, reports |
| [`05-metrics/`](05-metrics/) | **Trends across releases.** `events.jsonl`, append-only, written by `qa-event`; read with `qa-metrics` |

Folders are numbered in the order work happens: understand the product, analyse
the ticket, write the tests, run them, track the trend.

## Start here

| I am a… | Go to |
|---|---|
| Manual tester | The ticket's `04-results/<TICKET>/EXECUTE.md` |
| Analyst | The ticket's `02-analysis/<TICKET>/OPEN_QUESTIONS.md` |
| Team lead or client | The ticket's `04-results/<TICKET>/REPORT.html` |
| Developer | `03-tests/api/` and `03-tests/ui/` — run instructions in each README |
| New to the project | `01-docs/context/FULL_SPECIFICATION.md` |

## Tickets

| Ticket | What | State | Analysis | Results |
|---|---|---|---|---|
| PLAT-118 | Connect Confluence | Ready to execute | [analysis](02-analysis/PLAT-118/) | [pack](04-results/PLAT-118/EXECUTE.md) |
| PLAT-112 | Bulk export | Reported · 3 defects open | [analysis](02-analysis/PLAT-112/) | [report](04-results/PLAT-112/REPORT.html) |

## Test inventory

| Layer | Location | Tests | Last run |
|---|---|---|---|
| Manual | `03-tests/manual/` | 142 cases across 9 features | — |
| API | `03-tests/api/` | 96 | 2026-09-14 · 94 passed, 2 known defects |
| UI — admin | `03-tests/ui/admin/` | 38 | 2026-09-14 · 38 passed |
```

The **test inventory** table is what answers "what do we actually have?" — the
question every new person asks first and nobody can answer without it.

## The ticket README

At `02-analysis/<TICKET>/README.md`. It is the hub for one ticket and links
**across** the top-level folders, because a ticket's material is split by design
between analysis, tests and results.

```markdown
# PLAT-118 — Connect a Confluence workspace

**State** Ready to execute · **Updated** 2026-09-14 · [Jira](…)

| I am a… | Read this |
|---|---|
| Manual tester | [EXECUTE.md](../../04-results/PLAT-118/EXECUTE.md) |
| Analyst | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — 3 awaiting an answer |
| Team lead | [REPORT.html](../../04-results/PLAT-118/REPORT.html) |
| Developer | [PR #241](…) · test ids requested in [TEST_IDS.md](../../03-tests/ui/admin/TEST_IDS.md) |

## Everything for this ticket
| What | Where |
|---|---|
| Requirements | [requirements/](requirements/) — 12 functional, 5 non-functional, 8 criteria |
| Scenarios | [scenarios/](scenarios/) — 24, with RTM |
| Manual cases | [03-tests/manual/integrations/confluence/](../../03-tests/manual/integrations/confluence/) |
| API tests | [03-tests/api/specs/integrations/](../../03-tests/api/specs/integrations/) |
| UI tests | [03-tests/ui/admin/specs/integrations/](../../03-tests/ui/admin/specs/integrations/) |
| Results | [04-results/PLAT-118/](../../04-results/PLAT-118/) |

## State history
- 2026-09-14 Scenarios reviewed by analyst, ready to execute
- 2026-09-13 Scenarios generated, 3 open questions raised
```

The "everything for this ticket" table is what reconnects a ticket to its tests.
Tests are filed by feature, so without this table a reader has to know which
feature a ticket touched before they can find anything.

## Folder READMEs

Each numbered top-level folder carries a short README saying what belongs there
and what does not. One paragraph is enough. Its job is to stop the wrong thing
being put in the wrong place by the next person — human or agent.

## One state vocabulary

`analysing` → `awaiting answers` → `designing` → `ready to execute` →
`executing` → `reported` → `closed`

Used identically everywhere. A ticket in `awaiting answers` for a week is the most
useful thing the index surfaces.

## Audit

Every run, check:

- **Files outside the layout.** Anything at the root other than the numbered
  folders, `README.md` and dotfiles is misplaced. Report it with where it belongs.
- **Artefacts no index references** — they exist and nobody will find them.
- **Index entries pointing at missing files** — one dead link destroys trust in
  every other link on the page.
- **Tests filed by ticket.** A path like `03-tests/api/PLAT-118/` violates the
  feature rule. Report it and propose the feature path.

Report rather than fixing silently. A misplaced or missing file usually means a
stage did something wrong, and quietly tidying it hides that.

## Migrating an existing workspace

When a workspace predates this layout, propose the moves as a table — old path,
new path, reason — and wait for approval before moving anything. Use `git mv` so
history follows the files. Never move and rewrite in the same step; a move that
also changes content cannot be reviewed.

## Keep it generated

Never hand-edit these READMEs. They are derived from what is on disk and the
pipeline state. A hand-edited index drifts within a week and then nobody reads it.
