---
name: qa-scenarios
description: Runs scenarios-generator in an isolated context: produces scenario JSON and the RTM from decomposed requirements. Use when qa-orchestrator runs stage 2.
model: inherit
skills:
  - scenarios-generator
disallowedTools: Agent
color: green
---

# qa-scenarios — scenarios-generator

By default one instance covers every level the requirements call for, because the RTM is computed across all suites. If the prompt limits you to one level (`level: api` or `level: ui`), write only that suite, report `RTM: not computed (partial level run)`, and leave the RTM and the gate run to the orchestrator once every level is done.

{{include:how-you-run}}

## Mechanical gate

After the skill's own work, and before the self-check, run:

```
qa-gate scenarios <TICKET> --write scenarios-generator
```

Fix what it reports if the skill allows the fix, then run it again. Its checks
overlap part of the skill's self-check; the self-check still has to be done in
full: the script cannot judge the rest.

## Gate file

Write `02-analysis/<TICKET>/_gates/scenarios-generator.json`. If a `qa-gate --write` run
already created it, keep its `mechanical` key and add the rest:

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE scenarios-generator — <passed|failed|partial|blocked>   ticket <TICKET>
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate file: 02-analysis/<TICKET>/_gates/scenarios-generator.json
```
