---
name: critic-review
description: Reviews one QA pipeline stage's artefacts against a fixed rubric (toolkit/rubrics/*.md) as an independent critic, and records the verdict and every disagreement with evidence, so the engineer decides each one. Use after Gate 1 (requirements) and Gate 3 (automation code), when qa-orchestrator asks for a critic, or when the user asks for a second opinion on generated requirements or tests. Not for reviewing your own work in the same conversation.
---

# Critic review

A stage agent checks its own work with its skill's self-check. That catches what the agent
knows to look for; it cannot catch what the agent misunderstood, because the same reading
produced both the artefact and the check. A critic reads the artefacts cold, against the
sources and a rubric it did not write, and reports where it disagrees. It does not fix
anything: every disagreement becomes a question for the engineer.

## Independence

- **Work from the artefacts and the sources**, never from the stage agent's report, its
  conversation or its gate file's self-check. Open the gate file only after every rubric item
  is answered, and only to see which IDs and paths the stage claims.
- **Another vendor's model is the strongest critic**, a local model the next, another model of
  the same vendor in a fresh context the weakest that still counts. `qa-critic record` works
  out `independence` (cross-vendor, local, same-vendor) from the critic's and the producer's
  models; report it as recorded. A same-vendor critic still catches omissions and unsourced
  values well; it shares the producer's blind spots on interpretation.
- **Never review work you produced** in the same conversation.

## Procedure

1. Get the task: `qa-critic prompt <TICKET> <STAGE>` prints the rubric, the files to read and
   the output format. The rubric for a stage: requirements-decomposer → `rubrics/requirements.md`,
   automation-api / automation-ui → `rubrics/code.md`.
2. Answer every rubric item, in order: `agree`, `disagree` or `n/a`, each with evidence a
   reader can check (file:line, the sample you took, the probe you ran). Sample where the item
   says so, and name the sample.
3. For every `disagree`, write one disagreement per distinct finding: the rubric item, the IDs
   it concerns, what is wrong, the question the engineer must decide, your proposed default,
   and the evidence. Severity `high` when a test or requirement would assert something false
   or miss a defect, `medium` when coverage or clarity suffers, `low` for maintainability.
4. Write the JSON to a scratch file and record it:
   `qa-critic record <TICKET> <STAGE> <file> --backend <claude-agent|cursor-subagent> --model <the model you run on>`.
   It refuses output that skips a rubric item or has a `disagree` without a disagreement; fix
   and record again. Recording copies each open disagreement into the stage gate file's
   `needsEngineer`.
5. Check: `qa-gate check-stage <TICKET> <STAGE>.critic`.

## What a critic does not do

- Edit the artefacts, the gate file's status or the self-check. The engineer decides; the
  stage agent re-runs if the answer changes the work.
- Disagree on taste. A disagreement names a rubric item and evidence; "I would phrase it
  differently" is not one.
- Run destructive calls or load against an environment. Reading code, specs and recorded run
  reports is enough; a read-only probe is allowed where the rubric asks for one and the
  project rules allow it.

## Self-check before reporting completion

1. **Every rubric item is answered**, in order, with evidence a reader can check.
2. **Every `disagree` has at least one disagreement**, and every disagreement has a question
   and a proposed default.
3. **No disagreement rests on the stage agent's report** rather than on the artefacts.
4. **The critic file is recorded** with `qa-critic record` and `qa-gate check-stage <T> <STAGE>.critic` passes.
5. **The model and backend recorded are the ones that ran.**
