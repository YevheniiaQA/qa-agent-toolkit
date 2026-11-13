# Suite JSON, handoff fields, waivers, placeholders, coverage counting

Read this before writing or checking a suite file, the RTM, or a waiver.

## Full suite example

`02-analysis/<TICKET-ID>/scenarios/<suite>.json`:

```json
{
  "testSuite": {
    "name": "US-001: Connect a Confluence workspace",
    "level": "api",
    "ticket": "DEVAI-283",
    "testCases": [
      {
        "id": "TC-283-API-001",
        "name": "Connect succeeds with valid url and token",
        "priority": "HIGH",
        "technique": "equivalence-partitioning",
        "preconditions": [
          "User test.qa@example.com is authenticated",
          "No Confluence integration exists for the workspace"
        ],
        "testSteps": [
          {
            "stepNumber": 1,
            "action": "POST /api/v1/integrations/confluence/connect",
            "inputData": "{ \"url\": \"https://acme.atlassian.net\", \"token\": \"valid-token\" }",
            "expectedResult": "HTTP 200, body.success === true, body.integrationId is a uuid"
          }
        ],
        "postconditions": ["Integration is returned by GET /api/v1/integrations"],
        "traceability": {
          "requirementIds": ["F-DEVAI-283-BE-01"],
          "acceptanceCriteria": ["AC-DEVAI-283-01"],
          "userStory": "US-001"
        }
      }
    ]
  }
}
```

## The handoff contract to automation

Every scenario carries these fields, and the automation skills read them rather
than re-deriving intent from prose:

```json
{
  "status": "known-defect",
  "expectedOutcome": "fail",
  "observedBehaviour": "POST /items without name returns 200 and stores the record. Probed 2026-09-12.",
  "defectRef": "Q-03",
  "doNotRelax": true
}
```

`expectedOutcome: "fail"` means the generated test asserts the ticket's rule and
is marked as an expected failure — `test.fail()` in Playwright,
`@pytest.mark.xfail(strict=True)` in pytest. Strict matters: when the defect is
fixed, the test fails as "expected failure did not occur" and tells someone to
remove the marker. Without strict, a fix goes unnoticed and the marker outlives
the bug.

`doNotRelax: true` instructs every downstream stage that this assertion is
deliberate. If `test-debugger` later classifies its failure, the correct
classification is already recorded — it is a product defect, not a test bug, and
no debugging pass should weaken it.

Scenarios with `status: "undecided"` are excluded from automation and listed in
the handoff report as blocked, with the question they wait on.

## Waivers live in the JSON, not in prose

A non-functional requirement with no scenario needs a waiver, and a waiver
written only as a sentence in `RTM.md` is invisible to every machine downstream.
It will not reach the TMS, it will not appear in a coverage audit, and nobody can
tell a deliberate waiver from an oversight six months later.

Put them in `api.json` alongside the suite:

```json
"nfrWaivers": [
  {
    "requirementId": "NF-DEMO-1-BE-02",
    "reason": "No authorisation boundary exists — nothing returns 401 or 403, so an auth scenario would assert a boundary the system does not have",
    "blockedBy": null,
    "revisitWhen": "Authentication is introduced"
  },
  {
    "requirementId": "NF-DEMO-1-BE-03",
    "reason": "No length or format constraint stated in the ticket, the OpenAPI schema, or the database schema",
    "blockedBy": "Q-06",
    "revisitWhen": "Q-06 is answered"
  }
]
```

`RTM.md` is then **generated from this block**, not written alongside it. A waiver
that exists in prose but not in JSON is a bug in the generator.

`revisitWhen` is what stops a waiver becoming permanent by default. "Waived
forever" and "waived until auth ships" look identical in a sentence and are
entirely different commitments.

## Two kinds of placeholder

Test data splits into things that exist and things that must be made, and
conflating them is why every agent invents its own notation.

**`{{TEST_DATA: key}}`** — static data that lives in the global context. A test
user, a seeded workspace, an API token. `scenario-data-fix` resolves these by
lookup.

**`{{GENERATED: key}}`** — values created fresh on each run, which must never be
hardcoded and must not collide between parallel workers. Every one carries a rule
so the automation stage generates it correctly rather than guessing:

```json
"dataGeneration": {
  "itemId": {
    "rule": "unique int64 in the range 900000000–999999999",
    "scope": "per-test",
    "reuse": "never",
    "cleanup": "DELETE /items/{id} in teardown"
  },
  "itemName": {
    "rule": "qa-dry-run-<epoch>-<random>",
    "scope": "per-test",
    "reuse": "never"
  }
}
```

`scope` matters for parallelism: `per-test` values may collide across workers if
the rule is weak, and a suite that passes serially and fails at four workers is
almost always a `per-test` value that was really `per-suite`.

Do not invent a third notation. If a value fits neither category, it is a gap —
raise it as an open question rather than documenting a private convention that
`scenario-data-fix` will never read.

## Coverage is counted, not estimated

A coverage column reading only 100 / 50 / 0 hides the difference between a
requirement with one assertion and a requirement with four covering every input
class. Report both numbers:

```markdown
| Requirement       | Scenarios | Assertions | Classes covered | Coverage |
|-------------------|-----------|------------|-----------------|----------|
| F-DEMO-1-BE-01    | 4         | 9          | 4 of 4          | Covered  |
| F-DEMO-1-BE-05    | 1         | 1          | 1 of 3          | Partial  |
| F-DEMO-1-BE-09    | 1         | 0          | 0 of 2          | Blocked  |
```

"Classes covered" is the honest figure: it compares what the requirement implies
against what the suite asserts. A requirement with one scenario and one assertion
scoring "Covered" is how a matrix reads 100% while the feature is barely tested.

Count these from the suite itself. An RTM written by hand alongside the scenarios
will drift from them within one revision, and drift in the direction of looking
better.
