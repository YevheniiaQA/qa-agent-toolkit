# Degraded mode and heavy inputs

Read this when the project has no source repository and no API specification, or when a
build uses HAR captures or other heavy inputs.

## Degraded mode — no repository, no specification

Some products have neither. A jQuery landing page, an admin panel built on a
framework with no public API, a vendor system you can only see through a browser.
The skill must not respond by producing confident structure from guesses, and it
must not simply stop.

Build from what is observable, and mark every conclusion by how it was obtained:

| Source | What it yields | Confidence |
|---|---|---|
| Framework's own embedded configuration | Resource lists, field definitions, routes. Admin frameworks frequently expose the whole model in a bootstrap payload | High — read, not inferred |
| HAR capture of a real session | Actual endpoints, request and response shapes, auth headers, ordering | High for what was exercised, silent about the rest |
| Rendered DOM | Forms, fields, validation attributes, navigation structure | Medium |
| Client-side JavaScript | Route tables, API base paths, validation rules | Medium |
| Observed behaviour during exploration | Error messages, state transitions | Medium, and dated |

**Label everything.** Every entry in `services_endpoints.yaml` and each API file
carries `derivedFrom` with one of: `read` (taken verbatim from a config or spec),
`observed` (seen in a HAR or a response), `inferred` (reasoned from structure).
Downstream skills weigh these differently, and `inferred` entries are the ones
that produce tests against endpoints that do not exist.

State the mode prominently in `_index.json` and in your report:

```json
"mode": "degraded",
"reason": "No source repository or API specification available",
"sources": ["bootstrap-config", "har-capture-2026-09-14"],
"confidence": { "read": 31, "observed": 12, "inferred": 4 },
"blindSpots": ["Endpoints not exercised during the HAR session are unknown",
               "No visibility into server-side validation rules"]
```

`blindSpots` is the important field. A degraded context is not a worse context as
long as everyone knows where it stops — it becomes dangerous only when its
silence is mistaken for completeness.

Expand a degraded context by exploring, not by guessing: a second HAR session
covering a different flow adds real knowledge; another round of inference does not.


## Keep the heavy inputs out of the repository

HAR captures and other heavy source material used to build a degraded context go
to `.runs/context/<timestamp>/`, not into the context directory itself.
The context files are small, durable and committed; the captures they were
derived from are large, reproducible, and subject to the usual three-run
retention. Record in `_index.json` which capture each conclusion came from, so a
pruned capture is still explicable.

A HAR may contain session cookies and personal data. Treat it as sensitive: never
commit it, and prune it on the normal schedule.

