# Templates for the context files

Read this before writing or checking any file under `01-docs/context/`.

## `_index.json` stack block

`_index.json` records the detected stack so every downstream skill can adapt
without being told:

```json
{
  "stack": {
    "backend": { "language": "go", "framework": "gin", "confidence": "high" },
    "frontend": { "language": "typescript", "framework": "react", "router": "react-router" },
    "database": { "engine": "postgresql", "migrations": "db/migrate" },
    "apiStyle": ["rest", "graphql"],
    "specSource": "live-openapi",
    "detectedFrom": ["go.mod", "package.json", "docker-compose.yml"]
  }
}
```

## Fixed templates, not free form

Every file follows a fixed section structure. Predictable placement helps the
agent find things and helps the engineer read the project for the first time.

`FULL_SPECIFICATION.md` — exactly these six headings, in this order:
`## Purpose` · `## Actor roles` · `## Business processes` · `## Key entities` ·
`## Integrations` · `## Glossary`

`TECHNICAL_REQUIREMENTS.md` — exactly these seven headings, in this order:
`## Components` · `## Infrastructure` · `## Authentication and authorisation` ·
`## Databases` · `## Inter-service communication` · `## Environments` · `## CI`

Where a section cannot be filled from the available sources, keep the heading and
write one line stating what is missing and why. A heading that is present and
honest is useful; an absent heading is indistinguishable from an oversight, and
the next person cannot tell whether you looked.

For an API-only project with no business documentation — a public sandbox, a
service extracted from a monolith — `FULL_SPECIFICATION.md` is still written.
Derive the roles and processes from the endpoint groups and their descriptions.
A typical catalogue API, for example, yields three actor-facing areas (item, order, user)
and an obvious set of entities, which is enough for a useful specification even
with no prose documentation anywhere.

`api/<service>.yaml` is always written in OpenAPI shape regardless of where the
information came from. A GraphQL schema, a proto file, and a Postman collection
all normalise into the same structure, so every downstream skill reads one format
and never needs to know what the backend is. This is what keeps the pipeline
portable across projects with different stacks.

`services_endpoints.yaml`:

```yaml
services:
  auth:
    repo: acme/platform-backend
    environments:
      test: https://api.platform.test.acme.com/auth
      staging: https://api.platform.stage.acme.com/auth
    health: /health
    endpoints:
      - operation: POST /api/v1/auth/login    # or "mutation login" / "auth.v1.Auth/Login"
        protocol: rest                        # rest | graphql | grpc | queue
        source: src/auth/auth.controller.ts:31
        spec_source: live-openapi             # where the contract came from
        auth: none
```

The `source` reference on every endpoint is what makes `cleanup` and `update`
possible — an entry whose source file no longer exists is a dead entry.

## `test_data.yaml` example

```yaml
users:
  admin:
    email: qa.admin@example.com
    password_env: QA_ADMIN_PASSWORD      # never the value itself
    roles: [admin, integrations:write]
  viewer:
    email: qa.viewer@example.com
    password_env: QA_VIEWER_PASSWORD
    roles: [viewer]
  # deprecated 2026-08 — role removed from the product, kept for old cases
  legacy_editor:
    email: qa.editor@example.com
```

Credentials are referenced by environment variable name, never by value. This
file is committed; the values are not.
