---
name: performance-testing
description: Builds and runs k6 performance tests — smoke, load, stress, spike, soak and breakpoint — with thresholds as pass/fail gates, and produces a performance report with percentiles, saturation point and regression against a baseline. Use this skill after functional testing is complete and the build is otherwise ready, when the user asks about load testing, throughput, latency under load, or capacity, or when a release needs a performance sign-off. Never run it against production or against a shared environment without approval.
---

# Performance Testing

Runs **after** functional testing, not alongside it. A performance figure taken
from a build whose behaviour is not yet verified measures the wrong thing, and
running both at once means each becomes the other's load.

Keep the investment proportionate. Most projects need a smoke test, one load
test at expected traffic, and a baseline to compare against. Stress, spike and
soak are worth building when there is a specific question to answer.

## Before running anything

**Approval is mandatory.** Load testing generates real traffic against real
infrastructure. Against a shared staging environment it degrades everyone else's
work; against production it is an outage you caused. Confirm in chat: which
environment, what peak load, what window, and who has been told.

**Never test production** unless the engineer explicitly directs it, the window
is agreed, and there is a documented abort procedure.

**Record the conditions before the numbers.** Environment size, dataset size,
whether other traffic is present, whether caches are warm. A latency figure
without these is uninterpretable a month later, and comparing two runs with
different conditions is worse than having no comparison at all.

## Test types

| Type | Shape | Answers |
|---|---|---|
| **Smoke** | 1–5 VUs, 30s | Does the script work and the system respond at all? Always run first |
| **Load** | Ramp to expected peak, hold, ramp down | Does it meet its targets under normal traffic? |
| **Stress** | Ramp beyond peak until degradation | Where does it start to fail, and how? |
| **Spike** | Sudden jump to a multiple of peak, brief | Does it survive a traffic surge and recover? |
| **Soak** | Moderate load, hours | Memory leaks, connection exhaustion, degradation over time |
| **Breakpoint** | Ramp indefinitely until failure | What is the hard ceiling? |

Start with smoke. A load test that runs a broken script for ten minutes produces
confident nonsense.

## Project shape

```
03-tests/performance/
├── scripts/  smoke.js · load.js · stress.js · spike.js · soak.js
├── lib/      helpers.js · endpoints.js · auth.js
├── config/   thresholds.js · environments.js
└── data/     users.json
```

Thresholds live in one shared file so a target is defined once and every script
enforces the same one.

## Thresholds are the gate

A run without thresholds produces a chart somebody looks at once. A run with
thresholds produces a pass or a fail, which is what CI needs.

```js
import { check, sleep } from 'k6';
import http from 'k6/http';
import { Trend, Rate } from 'k6/metrics';

const registerDuration = new Trend('register_duration');
const businessErrors = new Rate('business_errors');

export const options = {
  stages: [
    { duration: '2m', target: 20 },
    { duration: '5m', target: 20 },
    { duration: '2m', target: 50 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
    register_duration: ['p(95)<2000'],
    business_errors: ['rate<0.01'],
  },
};
```

**Percentiles, never averages.** An average hides the tail, and the tail is what
users experience as "the site is slow". Report p50, p95 and p99 together — p50
alone looks healthy while a quarter of requests time out.

**Threshold values come from the requirement**, cited like any other. If no
target is stated, that is an open question with a proposed default, not a number
to invent — the same rule the decomposer follows.

**Check business outcomes, not just status codes.** A 200 carrying an error body
is a failure. Track it as a custom metric.

```js
const res = http.post(`${__ENV.API_BASE_URL}items`, payload, params);
const ok = check(res, {
  'status 200': r => r.status === 200,
  'body has id': r => r.json('id') !== undefined,
});
businessErrors.add(!ok);
registerDuration.add(res.timings.duration);
sleep(1);
```

**Include think time.** A loop with no `sleep` models nothing human and saturates
on connection handling rather than on the behaviour you meant to measure.

## Frontend performance

Backend latency is not user-perceived speed. Where the frontend matters, measure
it separately with Lighthouse in CI, and report Core Web Vitals — LCP, CLS, INP —
alongside the API figures. k6's browser module can drive real page loads under
load, but keep those runs small: browser VUs are expensive and a handful is
usually enough to see the effect.

## Baseline and regression

The single most useful output is not the absolute number — it is the movement.
Store each run's summary and compare:

```markdown
| Metric | Baseline (2026-08-14) | Current | Change |
|---|---|---|---|
| p95 register | 840 ms | 1,310 ms | +56% ⚠ |
| p99 register | 1,900 ms | 4,700 ms | +147% ⚠ |
| Error rate | 0.2% | 0.3% | — |
| Throughput | 42 rps | 39 rps | −7% |
| Dataset size | 1,266 records | 8,410 records | +564% |
```

The dataset row is there deliberately: most unexplained regressions turn out to
be data growth rather than code, and without it the team spends a day bisecting
commits.

Record each run with `qa-event counts performance-testing …` (see *Where run output
goes*) so `qa-metrics` can trend it across releases.

## Reporting

Emit a `performance` block for `test-report` so the results appear in the same
HTML report the client already reads. Include: test type, load profile, duration,
thresholds with pass or fail, p50/p95/p99 per operation, throughput, error rate,
saturation point where one was found, comparison against baseline, and the
environment conditions.

State plainly what the run does **not** establish. A load test on a single
staging node says nothing about production behind a load balancer, and saying so
protects the figure from being quoted as something it is not.

## Self-check before reporting completion

1. A smoke test ran and passed before any larger run.
2. Approval for the environment and the load level is recorded.
3. Every threshold traces to a stated requirement or a recorded proposed default.
4. Percentiles are reported, not averages.
5. Checks cover business outcomes, not only status codes.
6. Environment conditions and dataset size are recorded with the results.
7. A baseline comparison is present, or it is stated that this run is the baseline.
8. The report says what the run does not establish.

## Where run output goes

Follow `qa-conventions` → *Run output*: heavy artefacts to `.runs/<target>/<timestamp>/`, runs into
`05-metrics/events.jsonl` only through `qa-event`, evidence worth keeping in `.runs/KEEP`.

This skill records `qa-event counts performance-testing p95Ms=<n> p99Ms=<n> rps=<n>
errorRate=<n> vus=<n> --suite <scenario> --source <k6 summary JSON>`.

