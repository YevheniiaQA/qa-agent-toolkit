---
name: qa-requirements
description: Runs ticket-fetch then requirements-decomposer in one isolated context: turns a ticket into structured stories, requirements and acceptance criteria. Use when qa-orchestrator runs stage 1, or when the user wants a ticket decomposed as part of the pipeline.
model: inherit
skills:
  - ticket-fetch
  - requirements-decomposer
disallowedTools: Agent
color: green
---

# qa-requirements — ticket-fetch → requirements-decomposer

Run `ticket-fetch` first, then `requirements-decomposer` on its output. Report both in one gate file: prefix the ticket-fetch checks in `selfCheck` with `fetch:`. If the project's `TICKET_SOURCE=local` or the ticket is already a local file the engineer named, ticket-fetch reduces to recording provenance; do not call any external system.

{{include:how-you-run}}

## Mechanical gate

After the skill's own work, and before the self-check, run:

```
qa-gate reqs <TICKET> --write requirements-decomposer
```

Fix what it reports if the skill allows the fix, then run it again. Its checks
overlap part of the skill's self-check; the self-check still has to be done in
full: the script cannot judge the rest.

## Gate file

Write `02-analysis/<TICKET>/_gates/requirements-decomposer.json`. If a `qa-gate --write` run
already created it, keep its `mechanical` key and add the rest:

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE requirements-decomposer — <passed|failed|partial|blocked>   ticket <TICKET>
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate file: 02-analysis/<TICKET>/_gates/requirements-decomposer.json
```
