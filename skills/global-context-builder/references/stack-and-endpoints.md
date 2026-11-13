# Stack detection and endpoint extraction

Read this at the start of a `build`, and in `update` when the stack or the API surface changed.

## Detect the stack, never assume it

Do not ask the engineer what the backend is written in, and do not guess from the project
name. Detect it from the sources, because that is the only answer that stays true after a
rewrite. Run detection before extraction and record the result in `_index.json`; everything
downstream adapts to what was found.

**Step 1 — the ecosystem and framework from manifest files at the repo root.** One file
identifies the ecosystem, and the framework follows from the dependency list:

| Manifest found | Ecosystem | Then look for the framework in |
|---|---|---|
| `package.json` | Node | `express`, `fastify`, `@nestjs/core`, `koa`, `hapi`, `next` |
| `go.mod` | Go | `gin`, `echo`, `fiber`, `chi`, `net/http` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `spring-boot`, `quarkus`, `micronaut`, `ktor` |
| `requirements.txt`, `pyproject.toml` | Python | `fastapi`, `django`, `flask`, `litestar` |
| `*.csproj`, `*.sln` | .NET | `Microsoft.AspNetCore` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `composer.json` | PHP | `laravel`, `symfony` |
| `Cargo.toml` | Rust | `axum`, `actix-web`, `rocket` |
| `mix.exs` | Elixir | `phoenix` |

**Detect the frontend the same way**: React, Vue, Angular, Svelte, Next, Nuxt from
`package.json`; the routing convention from the router package or the file layout.

**Detect the database** from migration directories (`migrations/`, `db/migrate/`,
`prisma/schema.prisma`, `alembic/`), ORM configuration, and connection strings in CI
variables. Record the engine and where the schema is defined.

**Step 2 — routes, validation and configuration where the framework keeps them:**

| Framework | Routes | Validation | Configuration |
|---|---|---|---|
| NestJS | `@Controller` + `@Get/@Post…` decorators | DTO classes with `class-validator` | `ConfigModule`, `.env` |
| Express / Koa / Fastify | `app.get(…)`, `router.*`, `fastify.route` | `joi`, `zod`, `celebrate`, JSON schema on the route | `config/`, `.env` |
| Next.js | `app/**/route.ts`, `pages/api/**` | `zod` in the handler | `next.config.*` |
| Spring Boot | `@RestController` + `@RequestMapping/@GetMapping…` | `jakarta.validation` annotations on DTOs, `@Valid` | `application.yml` / `.properties` |
| Quarkus / Micronaut | JAX-RS `@Path` / `@Controller` | Bean Validation annotations | `application.properties` / `.yml` |
| Ktor | `routing { get(…) }` | manual or `RequestValidation` plugin | `application.conf` |
| FastAPI / Litestar | `@app.get(…)`, routers | Pydantic models | settings module, `.env` |
| Django (REST) | `urls.py`, viewsets / routers | serializers, model field options | `settings.py` |
| Flask | `@app.route`, blueprints | marshmallow / pydantic / manual | `config.py` |
| Gin / Echo / Fiber / Chi | `r.GET(…)`, route groups | `binding:` struct tags, validator | env, `config.*` |
| ASP.NET Core | `[Route]`, `[HttpGet]…`, minimal APIs `MapGet` | DataAnnotations, FluentValidation | `appsettings*.json` |
| Rails | `config/routes.rb` | model validations, strong params | `config/*.yml`, credentials |
| Laravel | `routes/api.php` | `FormRequest` rules | `config/*.php`, `.env` |
| Phoenix | `router.ex` | Ecto changesets | `config/*.exs` |

Record the convention you used in `_index.json` so a later refresh does not re-derive it.

**Step 3 — if nothing matches**, fall back to language-agnostic search: HTTP method strings
next to path literals, OpenAPI annotations, the CI config and Dockerfile for the run command
and exposed ports — those two describe how the thing actually builds and runs. Say plainly in
`_index.json` that routes were derived heuristically and are less reliable: an honest
confidence level is worth more than a confident wrong answer. An unlisted framework is a
documentation task for this file, not a blocker.

Record the detected stack back into the project profile (`BACKEND_STACK`, `FRONTEND_STACK`)
so later runs skip detection.

## Endpoint sources, in order of trust

Whatever the project has, one of these will exist. Probe for a live spec before anything
else — one HTTP call can replace an hour of code reading. Use the highest-trust source
available and cross-check against the next one down.

| Source | How to get it | Trust |
|---|---|---|
| Live OpenAPI document | `GET /openapi.json`, `/swagger.json`, `/v3/api-docs`, `/api-docs`, `/swagger/v1/swagger.json`, `/docs/json` | Highest — it is what is deployed |
| OpenAPI file in the repo | `openapi.yaml`, `swagger.yaml`, `api/**/*.yaml` | High — may lag the deployment |
| Route definitions in code | The framework convention above | High for structure, authoritative for what exists |
| GraphQL introspection or `.graphql` schema | An introspection query to the graphql endpoint | High |
| Protobuf definitions | `**/*.proto` for gRPC services | High |
| API gateway or ingress config | Gateway routes, ingress rules | Medium — reveals routes code search misses |
| Postman / Insomnia / Bruno collection | Exported JSON in the repo or from the team | Medium — often stale on paths, excellent on example bodies |
| HAR capture | Browser network export from a manual session | Medium — only what was exercised |
| Frontend API calls | fetch / axios call sites in the frontend repo | Medium — endpoints the backend docs omit |
| `.http` / `.rest` files, curl scripts | In the repo | Low — example data only |

**Cross-check rather than picking one.** An endpoint in the code but missing from Swagger is
usually undocumented, not absent. An endpoint in Swagger but not in the code is usually
removed and the spec is stale. Both are findings worth recording, and both routinely produce
test cases nobody else would write. Harvest example payloads from collections even when you
distrust their paths.

**Protocol-agnostic output.** REST paths, GraphQL operations, gRPC methods and queue topics
all normalise to the same shape: an operation identifier, an input contract, a set of
possible outcomes, an auth requirement and a source reference. Scenario generation works off
that shape, so a project that is half REST and half GraphQL needs no special handling.
