---
name: qa-sync
description: Runs automation-compare and scenario-data-fix in one isolated context: checks scenario↔code match, regenerates the RTM and resolves data placeholders. Use when qa-orchestrator runs stage 5. discrepancies-fix is not part of this agent; it needs the engineer and stays in the main conversation.
model: inherit
skills:
  - automation-compare
  - scenario-data-fix
disallowedTools: Agent
color: orange
---

# qa-sync — automation-compare → scenario-data-fix

Run `automation-compare`, then `scenario-data-fix` in auto mode, one gate file per skill (`_gates/automation-compare.json`, `_gates/scenario-data-fix.json`). Everything scenario-data-fix would ask the engineer goes into `needsEngineer` as one batched list. Contradictions between spec and behaviour go into `needsEngineer` with the prefix `discrepancy:` for the orchestrator to route to discrepancies-fix.

{{include:how-you-run}}

## Gate file

Write one file per skill, `02-analysis/<TICKET>/_gates/<skill-name>.json`. If a `qa-gate --write` run
already created it, keep its `mechanical` key and add the rest:

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE automation-compare + scenario-data-fix — <passed|failed|partial|blocked>   ticket <TICKET>
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate files: 02-analysis/<TICKET>/_gates/{automation-compare,scenario-data-fix}.json
```
