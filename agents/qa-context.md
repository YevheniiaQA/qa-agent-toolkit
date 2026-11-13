---
name: qa-context
description: Runs global-context-builder in an isolated context: builds, refreshes or rolls back the project knowledge base under 01-docs/context. Use when qa-orchestrator runs stage 0, or when the user asks to build or refresh the context for a project.
model: inherit
skills:
  - global-context-builder
scope: project
disallowedTools: Agent
color: blue
---

# qa-context — global-context-builder

Repository clones and live specs under `.runs/context/` are the noisiest input in the pipeline. Search them with `grep`/`rg` and read only the files that answer a specific question.

This stage is project-scoped, not ticket-scoped; the gate file goes under `02-analysis/_project/`.

{{include:how-you-run}}

## Gate file

Write `02-analysis/_project/_gates/global-context-builder.json`. Not under `.runs/`: retention prunes that.

{{include:gate-file}}

## Final message — this is all the orchestrator sees

Reply with at most 25 lines, in this shape and nothing else: no file contents,
no diffs, no logs, no narration of what you did.

```
STAGE global-context-builder — <passed|failed|partial|blocked>   project-scoped
Self-check: <n>/<m> pass   failing: #<id> <gate> — <one line why>
Mechanical: <qa-gate command> → exit <code> (<pass>/<total>)   or: none for this stage
Artefacts: <up to 8 paths>
Counts: <key numbers, e.g. 52 reqs · 63 scenarios · RTM 100%>
Needs engineer: <one line per question with its proposed default, or "none">
Gate file: 02-analysis/_project/_gates/global-context-builder.json
```
