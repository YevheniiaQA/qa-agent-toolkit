```json
{
  "ticket": "{{ticket}}",
  "stage": "<skill-name>",
  "agent": "{{agent}}",
  "status": "passed | failed | partial | blocked",
  "finishedAt": "<ISO-8601>",
  "selfCheck": [
    {"id": 1, "gate": "<gate name from the skill>", "result": "pass | fail | n/a", "evidence": "<what you ran or compared>"}
  ],
  "mechanical": { "...": "written by qa-gate --write" },
  "artefacts": ["<workspace-relative paths>"],
  "counts": { "<metric>": 0 },
  "needsEngineer": [{"question": "...", "proposedDefault": "..."}]
}
```

`selfCheck` lists **every** gate of the skill's "Self-check before reporting
completion" section (or its completion criteria, if it has no such section),
in the skill's order, each with evidence. `status` is `passed` only if every
self-check result is `pass` or `n/a` and every `mechanical` exitCode is 0; one
failure makes the stage `failed`, never "mostly passed". `partial` means you hit
a limit before finishing; `blocked` means you are waiting on the engineer.

Before the final message, run `qa-gate check-stage <TICKET> <STAGE>` (TICKET `_project` for a
project-scoped stage) for every gate file you wrote, and fix what it reports. When you stop, the
`qa-stage-gate` hook runs the same check on the gate file your report names and sends you back if
it fails. An honest failed, partial or blocked gate file is accepted; a missing or incomplete one is not.
