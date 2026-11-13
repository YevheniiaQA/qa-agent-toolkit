---
name: db-validator
description: Prepares test data and verifies system state directly in PostgreSQL — seeding preconditions, asserting postconditions the API does not expose, and diagnosing failures that look like application bugs but are data problems. Use this skill when a scenario needs a database precondition that no API can create, when a test must verify persisted state, when the user asks whether a failure is a data issue, or when building test data for the global context. Always operates read-only unless the engineer explicitly approves a write.
---

# DB Validator (PostgreSQL)

Some assertions only exist in the database. A soft delete that should set
`deleted_at`, an audit row that should be written, a foreign key that should
cascade — the API returns 204 either way, and only the table knows the truth.

This skill is also the fastest way to settle "is this a bug or is my test data
wrong", which is otherwise an hour of guessing.

## Read-only by default

Connect with a read-only role. This is not caution for its own sake: a shared test
database is shared, and one careless `UPDATE` without a `WHERE` blocks an entire
team for the afternoon.

Writes are permitted only when all three hold: the engineer explicitly approved
this specific operation, the statement is scoped to data the test itself created,
and it runs inside a transaction that the fixture rolls back. Otherwise, provision
data through the API.

Never run `DELETE` or `TRUNCATE` without a `WHERE` clause, never touch a table
outside the feature under test, and never connect to anything but a test
environment. If the host in the profile resolves to production, stop and say so.

## Where it fits in the pipeline

**Global context.** Extract the schema into `db_schema.md`: tables, columns with
types and nullability, enums, foreign keys, unique constraints, indexes. This is
a first-class source of boundary values — `varchar(50)` is where the off-by-one
cases come from, and a `NOT NULL` without a default is a 500 waiting to be found.

**Preconditions.** When a scenario needs state the API cannot produce — an
expired subscription, an orphaned record, a row in a legacy state — seed it in a
fixture and clean it up after.

**Postconditions.** Assert what the API hides:

```ts
test('TC-283-API-020 deleting an integration soft-deletes and writes an audit row',
  async ({ api, db }) => {
    const { id } = await api.createIntegration();
    await api.delete(`/api/v1/integrations/${id}`);

    const row = await db.one(
      'select deleted_at from integrations where id = $1', [id]);
    expect(row.deleted_at).not.toBeNull();

    const audit = await db.one(
      'select action from audit_log where entity_id = $1 order by created_at desc limit 1', [id]);
    expect(audit.action).toBe('integration.deleted');
  });
```

**Diagnosis.** When a test fails, checking the row is often faster than reading
logs, and it distinguishes "the write never happened" from "the write happened and
the read is wrong" immediately.

## Deriving test cases from the schema

Read the schema as a specification and generate cases from it:

| Schema feature | Cases it implies |
|---|---|
| `varchar(n)` | n-1, n, n+1 characters |
| `NOT NULL` without default | Omitted field must be rejected, not 500 |
| `UNIQUE` constraint | Duplicate insert returns a clean 409, not a raw constraint error |
| Foreign key | Referencing a non-existent parent; deleting a referenced parent |
| Enum column | Every valid value; one invalid value rejected |
| `timestamptz` vs `timestamp` | Timezone handling across a DST boundary |
| Nullable column read by the UI | Null renders as an empty state, not "null" |

Feed these to `scenarios-generator` as additional boundary and negative cases —
they are frequently the ones requirements omit entirely.

## Secrets and safety

Read the connection details from the project profile and the password from an
environment variable. Never write a connection string containing a password into
a report, a test file, or the conversation. Use parameterised queries only —
string-interpolated SQL in generated test code is a pattern that eventually gets
copied somewhere it matters.
