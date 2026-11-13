# Rubric — automation code (after Gate 3)

Stage reviewed: `automation-api` or `automation-ui` (the test project under `03-tests/`). Read
the scenario JSON the suite claims to implement, the spec files, fixtures, helpers and page
objects, and `TRACEABILITY.json`. Do not read the stage agent's report or its gate file's
self-check before you have answered every item. Do not run the suite against a shared
environment; reading the code and the recorded run reports is enough for this rubric.

Sample when an item says so; name the sample in the evidence. An item is `agree` when the code
meets it, `disagree` when you found a counter-example (cite file:line), `n/a` when it cannot
apply (say why).

| ID | Question | How to check |
|---|---|---|
| CD1 | Does each sampled test do its scenario's steps and assert its expected results? | 10 tests (all if 20 or fewer): scenario step by step against the test body, including helpers it calls |
| CD2 | Are the assertions specific? | Exact status, the fields and values the scenario names; not only `toBeTruthy`, `toBeDefined`, a length > 0 |
| CD3 | Could any test pass with the product broken? | Assertions on the request instead of the response, on a mock, on a locator that matches nothing, behind a condition |
| CD4 | Do known-defect tests assert the required behaviour under `test.fail`? | Not the observed wrong behaviour; the defect ID in the annotation |
| CD5 | Is test data isolated and cleaned up? | Each test creates what it changes and removes it; no dependence on run order or on another test's records |
| CD6 | Is anything hiding failures? | Retries, `try/catch` around assertions, conditional `test.skip`, fixed waits, `expect.soft` without a reason |
| CD7 | Does every test trace to a scenario, and every ready scenario to a test? | Title IDs against the suite; `TRACEABILITY.json` against both |
| CD8 | Are destructive calls limited to records the test created? | Every DELETE / PUT / bulk change: the target was created in the same test or fixture |
| CD9 | Is any credential or environment value hard-coded? | Tokens, passwords, hosts that should come from the profile or the environment |
| CD10 | Will a change to the product break many tests at once for one reason? | Duplicated request building, selectors repeated outside page objects, magic values copied between files |

A disagreement is a finding the engineer must decide on. State it as a question with your
proposed default, the test IDs and files it concerns, and the evidence (file:line).
