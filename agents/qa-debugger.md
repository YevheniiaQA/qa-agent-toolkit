---
name: qa-debugger
description: Runs test-debugger in an isolated context: classifies failures of a generated suite and runs the mutation pass. Use when qa-orchestrator runs stage 4, or when generated tests fail.
model: inherit
skills:
  - test-debugger
disallowedTools: Agent
color: red
---

# qa-debugger — test-debugger

Run the gate after your fixes, so the orchestrator can see that debugging did not reintroduce `test.only`, waits, or assertion-free tests. Report product defects in `needsEngineer` only when the skill says the engineer must confirm them; otherwise list them in `counts` and the gate file.

{{include:how-you-run}}

## Mechanical gate

After the skill's own work, and before the self-check, run:

```
qa-gate code <TEST_DIR> [--ui] --ticket <TICKET> --write test-debugger
```

Fix what it reports if the skill allows the fix, then run it again. Its checks
overlap part of the skill's self-check; the self-check still has to be done in
full: the script cannot judge the rest.

## Gate file

Write `02-analysis/<TICKET>/_gates/test-debugger.json`. If a `qa-gate --write` run
already created it, keep its `mechanical` key and add the rest:

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE test-debugger — <passed|failed|partial|blocked>   ticket <TICKET>
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate file: 02-analysis/<TICKET>/_gates/test-debugger.json
```
