---
name: security-testing
description: Runs QA-level security testing across the API, backend, frontend and the test suite itself — authorisation boundaries from the OWASP API Security Top 10, common web risks, dependency and secret exposure — and produces a findings report with evidence and severity. Use this skill when a feature touches authentication, authorisation, payments or personal data, when the user asks for a security review or a security report, or before a release that changes permissions. It is QA security testing, not a penetration test, and the report says so.
---

# Security Testing

Scope this honestly. What a QA engineer with an agent can do is verify
authorisation boundaries, check for the well-known classes of mistake, and find
what a scanner finds. What it cannot do is a penetration test. Say so in the
report — a document that implies more assurance than it delivers is worse than no
document.

**Never test a system you do not have written permission to test.** Never run
active scanning against production. Never attempt to access another real user's
data — use test accounts you control on both sides of every authorisation check.

## Start with authorisation, because that is where the bugs are

The OWASP API Security Top 10 (2023 edition, still the current list) puts three
authorisation failures in the top three, and the first of them is the single most
common serious API bug. Test them in this order; it matches where findings
actually are.

**BOLA — broken object level authorisation (API1).** Take an object ID belonging
to user A, request it as user B. This one line is the highest-value security test
in existence for a typical API.

```
As user B:  GET /api/v1/orders/{A's order id}
Expected:   404 or 403.  A 200 is a finding, and usually a critical one.
```

Test it on every endpoint that takes an ID — read, update **and** delete. Teams
that fixed it on GET routinely left DELETE open. Try the ID in the path, in a
query parameter, in the body, and in a nested field.

**Broken authentication (API2).** Expired token accepted, token signature not
verified, `alg: none`, token from a different environment accepted, password
reset token reusable, no lockout on repeated failures, session not invalidated on
logout or password change.

**Broken object property level authorisation (API3).** Two halves, both common:
*mass assignment* — send `"role": "admin"` or `"isVerified": true` in a create or
update body and see whether it binds; and *excessive data exposure* — check
whether responses contain fields the caller should not see, such as password
hashes, internal IDs, other users' emails.

**Broken function level authorisation (API5).** Call admin endpoints as a normal
user. Change the method — a route that rejects `GET` may accept `PUT`. Guess
adjacent routes: if `/api/v1/admin/users` exists, try `/api/v1/admin/settings`.

## The rest of the list, briefly

| Risk | What to test |
|---|---|
| Unrestricted resource consumption (API4) | Huge page sizes, deeply nested payloads, large uploads, absent rate limiting |
| Unrestricted access to sensitive business flows (API6) | Automate a flow meant to be manual — bulk purchase, mass signup, repeated password reset |
| SSRF (API7) | Any endpoint accepting a URL: point it at `localhost`, at cloud metadata addresses, at an internal hostname |
| Misconfiguration (API8) | Verbose errors and stack traces, permissive CORS, missing security headers, directory listing, debug endpoints |
| Improper inventory management (API9) | Old API versions still routed, staging hosts publicly reachable, undocumented endpoints in the code |
| Unsafe consumption of APIs (API10) | Whether responses from third-party services are validated before use |

## Frontend

- **Reflected and stored XSS** — inject a benign marker into every field that is
  later rendered, and check whether it executes. Pay special attention to fields
  rendered in a different context from where they were entered.
- **Security headers** — Content-Security-Policy, Strict-Transport-Security,
  X-Content-Type-Options, Referrer-Policy. Absence is a finding even without a
  demonstrated exploit.
- **Secrets in the bundle** — search built JavaScript for keys and tokens.
  Anything in the frontend bundle is public; the only question is whether the team
  knows it.
- **Authorisation enforced server-side** — hide an admin control in the UI, then
  call the endpoint directly. A permission that exists only in the frontend is
  not a permission.
- **Cookie flags** — `HttpOnly`, `Secure`, `SameSite` on session cookies.
- **Client-side storage** — tokens in `localStorage` are readable by any script on
  the page.

## The test suite itself

Frequently overlooked, and it is your own responsibility rather than the
product team's:

- **No credential in any committed file.** Scan the repository history, not just
  the working tree — `gitleaks` or `trufflehog` do this in seconds.
- **`storageState` and `.auth/` are gitignored.** They hold live sessions.
- **CI secrets are not logged.** Redact `authorization` and `cookie` headers in
  any request logging the suite does.
- **Dependencies are scanned.** `npm audit`, `pip-audit` or equivalent, in CI.
- **Test accounts are least-privilege**, and never reuse a real user's credentials.

## Tooling

Automated scanning covers breadth; the authorisation tests above cover the depth
that scanners cannot reach because they do not know which object belongs to whom.

- **OWASP ZAP** — baseline scan in CI for passive findings, full scan on demand
  against a non-production target
- **Semgrep** — static analysis for injection patterns and unsafe sinks
- **gitleaks / trufflehog** — secret scanning including history
- **npm audit / pip-audit / Dependabot** — dependency vulnerabilities
- **Schemathesis** — fuzzing generated from the OpenAPI document, which finds
  500s on malformed input

Never paste a scanner's raw output into a report. It contains noise, duplicates
and findings that do not apply, and a report nobody trusts gets skimmed.

## Findings

Every finding carries: the risk category, severity, the exact reproduction, the
evidence, the affected surface, and the fix. Redact real data in evidence.

```markdown
### SEC-04 — BOLA on order retrieval — Critical

**Category** API1:2023 Broken Object Level Authorisation
**Surface** Backend API, `GET /api/v1/orders/{id}`

**Reproduction**
1. As user A (`qa.a@example.com`), create an order. Note its id.
2. As user B (`qa.b@example.com`), authenticated with B's own token,
   send `GET /api/v1/orders/{A's id}`.

**Expected** 403 or 404
**Actual** 200, with A's full order including delivery address and last four
digits of the payment card

**Impact** Any authenticated user can read any other user's orders by iterating
sequential identifiers. Order ids are sequential, so enumeration is trivial.

**Fix** Verify ownership server-side in the route handler on every request, not
only that the caller is authenticated.

**Evidence** `04-results/<T>/evidence/SEC-04.http` — headers redacted
```

Severity follows exploitability and impact together: a critical finding is one
that is reachable by an ordinary authenticated user and exposes or destroys data.

Report findings through `discrepancies-fix` for ticket creation, with the same
per-ticket approval barrier. Security findings additionally should not be filed
into a public backlog without asking where they should go — many teams have a
restricted project for them, and putting a working exploit in a ticket everyone
can read is itself a disclosure.

## Reporting

Emit a `security` block for `test-report` so findings appear in the same HTML
report. Include the scope statement, what was and was not tested, findings by
severity, the surfaces covered, and the tooling used with versions.

Open the report with the scope limitation, not with the findings. "This is QA
security testing covering authorisation boundaries and known risk classes on the
API and frontend. It is not a penetration test and does not constitute a security
audit." That sentence is what makes the rest of the document honest.

## Self-check before reporting completion

1. Written permission to test is recorded, and nothing ran against production.
2. BOLA was tested on every endpoint taking an identifier, across read, update
   and delete.
3. Both halves of API3 were tested — mass assignment and excessive exposure.
4. Every finding has a reproduction someone else can follow.
5. No real user's data was accessed; both sides of every check used test accounts.
6. No credential, token or personal datum appears in the report or the evidence.
7. Scanner output was triaged, not pasted.
8. The report states its scope limitation before its findings.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event counts security-testing critical=<n> high=<n> medium=<n> low=<n>
--source <the findings report>`.

