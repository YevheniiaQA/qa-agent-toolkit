---
name: qa-conventions
description: Conventions every QA skill shares — where run output goes and how runs are recorded, how a disabled integration is handled, how a lesson is recorded. Read it whenever a QA skill points to it (sections "Where run output goes", "Disabled integrations"), and before writing run artefacts, metric events or anything that would call an outside system from a QA workspace.
---

# QA conventions

Skills point here instead of repeating these rules, so they cannot drift apart. A skill's own
section adds only what is specific to it: the command it records with, the systems it touches,
its local alternative.

## Run output

Write heavy artefacts — traces, videos, screenshots, raw reporter output, scanner and capture
files — to `.runs/<target>/<timestamp>/`, where `<target>` is the service or UI target from the
project profile. Never to the repository root, never into the generated test project, and
never anywhere that gets committed.

Namespacing by target is what makes retention work on a multi-service project: without it, a
suite that runs twenty times a day evicts the artefacts of one that runs twice a week.

Record every run with the `qa-event` command the skill names; it is the only way into
`05-metrics/events.jsonl`. Never write that file by hand or from memory: `qa-event` reads the
numbers from the file it is given, names that file in the event and validates the line. The
file is append-only and kept indefinitely; it costs a few hundred bytes a run and is the basis
of every trend `qa-metrics` can show.

Only the last three runs per target are retained. If a run produced evidence for a defect that
is still open, or is the current baseline, or is the last known-good run, add its path to
`.runs/KEEP` so retention does not remove it. See `artifact-retention`.

## Disabled integrations

Read `INTEGRATIONS` from the project profile (`source ~/.qa-agent/bin/qa-env.sh && qa_load`)
before touching any system the skill names. A system that is not listed is **disabled on
purpose**: skip it, do the skill's local alternative, and report it as `➖ <system> disabled
for this project`. Do not probe it, not even to check that a token works, and never borrow
another project's token. Every script a skill runs against such a system starts with
`qa_enabled <system> || exit 0`.

`qa-guard` enforces the same list in Cursor and Claude Code and blocks the call when this step
is skipped. A block from it is the answer, not an obstacle to route around. Declared sources
(`GC_SOURCE_REPOS`, `GC_SOURCE_DOCS`) stay readable; `qa-guard --check <url> --read` says so.

## Lessons

A lesson from a work block goes to `01-docs/context/lessons/<YYYY-MM-DD>-<slug>.md`, never into
the knowledge base files themselves (the Cursor rule `shared-context-protocol` has the template).
`global-context-builder` does not clean, prune or roll back `lessons/`.
