# Performance requirements

Read this when a requirement states a response time, throughput or another performance target.

## Performance requirements need a shape, not a single call

A response-time NFR expressed as one assertion in one test is not a measurement.
`expect(elapsed).toBeLessThan(2000)` on a single request passes or fails on
network noise, and a percentile cannot be computed from one sample at all.

When a requirement states a percentile, the scenario must state the sample:

```json
{
  "id": "TC-DEMO-1-API-024",
  "name": "Registration responds within 2 seconds at p95",
  "technique": "non-functional",
  "measurement": {
    "calls": 20,
    "statistic": "p95",
    "threshold": "2000ms",
    "warmupCalls": 2,
    "source": "ticket §Acceptance criteria ¶6"
  }
}
```

When the requirement states a flat maximum rather than a percentile, say so and
assert the maximum across the sample. Either way the scenario carries the sample
size, so the automation stage cannot quietly reduce it to one call.

Note in the scenario that a shared public environment makes timing figures
indicative rather than authoritative — a number measured against a sandbox other
people are also using is evidence, not a gate.
