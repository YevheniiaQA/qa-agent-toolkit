---
name: qa-automation-api
description: Runs automation-api in an isolated context: generates the Playwright API test project from scenario JSON. Use when qa-orchestrator runs the API branch of stage 3.
model: inherit
skills:
  - automation-api
disallowedTools: Agent
color: purple
---

# qa-automation-api — automation-api

`<API_TEST_DIR>` is the project directory the skill writes to (`03-tests/api/` by default). The skill's three-run stability gate is yours to run; `qa-gate` does not run the suite unless you pass `--run`.

{{include:how-you-run}}

## Mechanical gate

After the skill's own work, and before the self-check, run:

```
qa-gate code <API_TEST_DIR> --ticket <TICKET> --write automation-api
```

Fix what it reports if the skill allows the fix, then run it again. Its checks
overlap part of the skill's self-check; the self-check still has to be done in
full: the script cannot judge the rest.

## Gate file

Write `02-analysis/<TICKET>/_gates/automation-api.json`. If a `qa-gate --write` run
already created it, keep its `mechanical` key and add the rest:

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE automation-api — <passed|failed|partial|blocked>   ticket <TICKET>
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate file: 02-analysis/<TICKET>/_gates/automation-api.json
```
