---
name: contract-testing
description: Sets up and maintains consumer-driven or bi-directional contract tests between services using Pact, plus schema-level contract checks against an OpenAPI document, and wires can-i-deploy as a release gate. Use this skill when a project has several services with independent release cycles, when a provider change broke a consumer in production, when end-to-end integration tests are slow or flaky, or when the user asks about Pact, contract testing, or API compatibility between services. Also use it to check whether an OpenAPI specification still matches the running implementation.
---

# Contract Testing

There is a class of defect that lives between "my service works alone" and
"everything works together". A provider renames a field, every unit test passes
because the network is mocked, and production breaks at two in the morning.

End-to-end tests catch it only if you run every service together in the right
versions, which is slow and expensive enough that nobody does it per commit.
Contract testing replaces that with a pairwise check that runs in seconds.

## Disabled integrations

Follow `qa-conventions` → *Disabled integrations* for the contract broker (`pactflow`): read `INTEGRATIONS`, skip a
system that is not listed, report it as `➖ <system> disabled for this project`, never route
around a `qa-guard` block.

**Local alternative:** generate and verify pacts as files in the repository and run the provider verification against them. Publishing and `can-i-deploy` need the broker; report the release gate as not set up rather than simulating it.

## Which model to use

| Model | How it works | Choose when |
|---|---|---|
| **Consumer-driven (classic Pact)** | The consumer records the requests it makes and the responses it needs; the provider replays them against real code | Teams are willing to run a provider verification job; you want maximum fidelity |
| **Bi-directional** | The provider publishes its OpenAPI document plus evidence its own tests pass; the broker compares consumer expectations against it | You already maintain a trustworthy OpenAPI spec and want the pipelines decoupled |
| **Schema-only** | Validate the running API against the OpenAPI document directly, with Schemathesis or Dredd | There is one consumer, or the consumer is a third party you do not control |

Bi-directional trades some fidelity for speed: static comparison is less precise
than replaying real requests. It is the right trade only when the spec is
genuinely kept honest — otherwise you are gating releases on a document.

## Consumer side

The contract is what the consumer **actually needs**, not everything the provider
returns. This is the most common mistake: a consumer that asserts the full
response shape turns every harmless provider addition into a false failure.

```ts
import { PactV4, MatchersV3 } from '@pact-foundation/pact';
const { like, eachLike, integer } = MatchersV3;

const pact = new PactV4({ consumer: 'web-admin', provider: 'item-service' });

await pact
  .addInteraction()
  .given('an item with id 1 exists')
  .uponReceiving('a request for item 1')
  .withRequest('GET', '/items/1', b => b.headers({ Accept: 'application/json' }))
  .willRespondWith(200, b => b.jsonBody({
    id: integer(1),
    name: like('notebook'),
    status: like('available'),
  }))
  .executeTest(async mock => {
    const item = await new ItemClient(mock.url).get(1);
    expect(item.name).toBe('notebook');
  });
```

**Use matchers, not literal values**, for anything the consumer does not care
about exactly. `like('notebook')` says "a string here"; `'notebook'` says "exactly
this", and couples your contract to the provider's test data.

**Assert only the fields you consume.** If the consumer ignores `imageUrls`, it
does not belong in the contract.

**`given` states are provider setup, not consumer concerns.** Name them for what
must be true, and keep the list short — every state is a fixture the provider
team has to implement and maintain.

## Provider side

The provider pulls contracts from the broker and replays them against real code
with the database and dependencies its state handlers set up. Verification
results publish back to the broker.

A provider verification failure is a genuine finding: it means a consumer in
production expects something this code no longer does. Never fix it by editing
the consumer's pact — that inverts the whole point. Fix the provider, or go to
the consumer team and agree a change.

## The broker and the deploy gate

The broker holds contracts and verification results; `can-i-deploy` turns them
into a release decision:

```bash
pact-broker can-i-deploy \
  --pacticipant web-admin --version "$GIT_SHA" \
  --to-environment production --retry-while-unknown 30
```

Exit non-zero blocks the deploy. This is the payoff — everything before it is
bookkeeping.

**Back up the broker and monitor it.** Your deploy gate depends on it being
reachable; an unavailable broker either blocks every release or, worse, gets
bypassed once and then permanently.

**Version pacticipants by commit SHA**, and tag by branch and environment. A pact
published without a version cannot be reasoned about later.

## Avoiding contract bloat

One focused pact per consumer-provider pair. Dozens of near-duplicate
interactions make provider verification slow and give nobody more confidence.
Before adding an interaction, ask whether an existing one already covers the
shape — if it differs only in data, it does.

## OpenAPI-level checks

Where there is no consumer to drive the contract, check the spec against reality
directly:

- **Schemathesis** generates requests from the OpenAPI document and checks
  responses conform — good at finding endpoints that return undocumented shapes
  and 500s on valid input
- **Dredd** validates documented examples against the running service
- **Spectral** lints the specification itself for inconsistency and missing
  descriptions before either of the above can be trusted

Findings here feed `discrepancies-fix` like any other: an endpoint whose real
response differs from its documented one is either a defect or a stale spec, and
the source-priority rules decide which.

## What contract testing does not replace

It proves two services agree on shape and semantics at their boundary. It says
nothing about whether the overall business flow is correct. Keep a small
end-to-end suite for the critical paths; contract tests let you keep it small.

## Self-check before reporting completion

1. Every consumer interaction uses matchers rather than literal values for fields
   the consumer does not assert on.
2. No contract asserts a field the consumer does not read.
3. Every `given` state has a corresponding provider state handler.
4. Verification results publish to the broker, not just to the console.
5. `can-i-deploy` runs in CI and its exit code actually gates the deploy step.
6. Pacticipant versions are commit SHAs, not branch names or timestamps.
