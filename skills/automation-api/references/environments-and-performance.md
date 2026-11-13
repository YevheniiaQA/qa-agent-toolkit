# Shared environments and performance assertions

Read this when the environment is shared or foreign, or a scenario carries a timing assertion.

## Shared and foreign environments

Assume the environment is shared unless told otherwise. Staging has other people
on it; a public sandbox has strangers. Suites written for a controlled
environment fail for reasons that have nothing to do with the feature.

**Parse foreign records loosely, your own strictly.** A collection you did not
create will contain records that violate the schema — another team's test data,
a half-migrated row, `imageUrls: [null]`. Validate the full schema only on
records you created; for the rest, parse by reference with passthrough:

```ts
const Loose = ItemRef.passthrough();           // id + name, anything else allowed
const mine = Item.parse(all.find(p => p.id === createdId));   // strict, yours
```

**Never assert on collection length, ordering, or absence of elements** in a
shared collection. `toHaveLength(3)` passes on your machine and fails the moment
someone else runs their suite. Assert that *your* record is present, or absent,
by id.

**Clean up in fixture teardown, never at the end of the test body.** A failing
test never reaches its last lines, so body-level cleanup leaks exactly when the
run went wrong and the environment most needs tidying.

**Every record you create is identifiable as yours** — a run-scoped prefix in the
name, ids in a reserved range. When cleanup fails, somebody needs to be able to
find and remove your data without guessing.

## Performance assertions need isolation

Three rules, each learned the expensive way:

**A timing assertion never runs in the same worker pool as functional tests.**
Measuring latency while twenty of your own requests are in flight measures your
own load. Put timing tests in a separate Playwright project with `workers: 1`.

**Performance never gates functional results.** A `dependencies: []` chain that
puts timing first means one budget overrun produces `1 failed, 21 did not run` —
the entire functional result hidden behind a number that was always going to be
noisy. Separate project, separate report, no dependency either way.

**The measurement condition sits beside the threshold in the test**, because a
threshold without a condition is meaningless:

```ts
// NF-DEMO-1-BE-01 — ticket §AC ¶6: under 2 seconds.
// Measured sequentially, single caller, 20 samples after 2 warmups,
// against a shared public sandbox — indicative, not a gate.
test('TC-024 registration responds within 2s at p95', async ({ api }) => {
  const samples: number[] = [];
  for (let i = 0; i < 22; i++) {
    const t0 = performance.now();
    await api.createItem(uniqueItem());
    if (i >= 2) samples.push(performance.now() - t0);
  }
  const p95 = samples.sort((a, b) => a - b)[Math.floor(samples.length * 0.95)];
  expect(p95, `p95 over ${samples.length} sequential samples`).toBeLessThan(2000);
});
```

```ts
projects: [
  { name: 'api',    testMatch: /.*\.spec\.ts/, testIgnore: /.*\.timing\.spec\.ts/ },
  { name: 'timing', testMatch: /.*\.timing\.spec\.ts/, workers: 1 },
]
```

And `npx playwright test --project=api` is the default command in the README you
generate — a bare `npx playwright test` puts both pools together again.
