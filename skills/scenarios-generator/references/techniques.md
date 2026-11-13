# Test design techniques

Read this while designing scenarios: which technique to apply, and where the boundaries come from when the ticket is silent.

## Apply ISTQB techniques explicitly

Do not generate scenarios by intuition. Work through the techniques and record
which one produced each case — the technique name is what lets a reviewer judge
whether coverage is adequate.

**Equivalence partitioning.** Group inputs into classes that should behave
identically; take one representative per class. Cover valid classes and each
invalid class separately.

**Boundary value analysis.** For every bounded input, test min-1, min, min+1,
max-1, max, max+1. Domain length limited to 50 characters means cases at 49, 50,
and 51 — off-by-one is the single most common backend validation defect.

**Decision tables.** When behaviour depends on a combination of conditions, build
the table and cover each rule. Two booleans and a role field is eight rules, not
three cases.

**State transition testing.** For flows with state (draft → submitted → approved),
cover valid transitions, invalid transitions, and re-entry into the same state.

**Error guessing, informed.** Add cases from known failure patterns: concurrent
submission, expired session mid-flow, network failure between two calls, browser
back after submit, double-click on submit, paste of leading/trailing whitespace.

**Validation asymmetry between write and read.** This one deserves naming,
because it produces the worst class of defect and almost never appears in a
ticket. A field validated on the read path but not on the write path lets a record
be created that no query can reach: the write returns success, the data is stored,
and the only search path the feature offers filters it out. Nothing fails, nothing
is logged, and the record is invisible.

Generate a case for it wherever a value is both written and used as a filter:

- write a case-variant of a valid enum member, then read back through the filter
- write a value with leading or trailing whitespace, then filter on the trimmed form
- write a valid value through one endpoint, then read through every path that
  should surface it
- where a write normalises and a read does not, or vice versa, test both directions

The assertion that matters is the **read-back**, not the write. A write returning
200 is what makes this defect invisible in the first place, so a scenario that
stops at the write status code will report success on a broken system.

Priority these high. A rejected write is a visible failure the user can act on; a
silently unreachable record is data loss the user discovers weeks later.

## Choosing between equivalence partitioning and boundary analysis

These get conflated, and the distinction decides what cases you write.

**Equivalence partitioning** applies to unordered sets — enums, roles, country
codes, status values. There is no boundary between `available` and `pending`;
there are classes. Cover every valid member plus at least one invalid class, and
consider these invalid classes separately: an unrecognised member, an empty
value, a case variant of a valid member, and where relevant a value valid for a
different field.

**Boundary value analysis** applies to ordered inputs — lengths, counts, dates,
numeric ranges, page sizes. Cover min-1, min, min+1, max-1, max, max+1.

An enum covered by three valid classes and three invalid ones is complete, and
labelling it boundary analysis would be wrong. Say which technique you applied
and why, so a reviewer expecting "boundary cases on the enum" understands what
they are looking at instead of assuming a gap.

## Boundaries come from the contract when the ticket is silent

A ticket rarely states length limits, formats, or enum members. That silence is
not a reason to skip boundary analysis — it is a reason to look one layer down.

The global context holds the API spec and, where available, the database schema.
Constraints there are **sourced**, not invented, and the distinction is exactly
the one `requirements-decomposer` draws: `maxLength: 50` in the OpenAPI document
is a fact about the system with an anchor you can cite, whereas "let's say 3
seconds" is fabrication.

Order of lookup when the ticket does not state a boundary:

1. The endpoint's schema in `api/<service>.yaml` — `maxLength`, `minimum`,
   `pattern`, `enum`, `required`, `format`
2. The column definition in `db_schema.md` — `varchar(n)`, `NOT NULL`, unique
   constraints, enum types
3. Framework-level defaults recorded in the technical requirements — body size
   limits, request timeouts
4. Nothing found → no boundary case, and an open question proposing one

Cite the source on the scenario the same way requirements do:

```json
"technique": "boundary-value-analysis",
"boundarySource": "api/openapi.yaml#/components/schemas/Item/properties/name"
```

A requirement marked Partial because "no limit appears in the ticket" should be
re-checked against the spec before that verdict stands. Often the limit is there
and nobody read that far.
