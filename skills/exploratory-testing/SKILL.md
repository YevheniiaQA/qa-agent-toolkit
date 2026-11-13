---
name: exploratory-testing
description: Plans and records session-based exploratory testing — time-boxed charters aimed at what scripted cases cannot cover, with session notes, findings and coverage of the areas explored. Use this skill when a feature is too new or too uncertain for scripted cases, after scripted execution finds nothing, when the user asks how to find bugs the test cases missed, or when testing a third-party integration or a legacy area with no requirements. Also use it to turn a vague "have a look at this" request into something with a scope and a record.
---

# Exploratory Testing

Scripted cases verify what somebody thought of. Everything else is found by
somebody looking — and on most products, the most serious defects are in that
second category.

The failure mode of exploratory testing is that it leaves no record, so nobody
can say what was covered and it cannot be repeated. Session-based testing fixes
that without turning it back into a script.

## Charters

A charter is a mission, not a procedure. Time-boxed, with an area and a risk in
mind, and deliberately open about method.

```markdown
## CH-03 — Confluence connection under adverse conditions
**Explore** the connect flow
**With** network interruption, slow responses, and concurrent sessions
**To discover** whether partial connections leave recoverable state
**Time-box** 60 minutes · **Risk** medium — partial state is invisible to the user
```

Good charters come from where the scripted cases are weakest:

- **Where requirements were silent.** Every open question is a charter.
- **Where the design showed states nobody specified** — empty, loading, error.
- **Interruption and concurrency.** Scripted cases almost never cover a second
  tab, a back button mid-flow, or a session expiring at the wrong moment.
- **Data that is unusual rather than invalid.** Very long names, right-to-left
  text, emoji, a leading zero, a value that looks numeric but is not.
- **Boundaries between systems.** Integrations are where ownership is unclear and
  nobody tested both sides.
- **Areas where defects already clustered.** Defect density predicts defect
  density better than anything else available.

## Sessions

Write charters to `04-results/<TICKET>/sessions/CHARTERS.md` and each session to
`04-results/<TICKET>/sessions/<charter-id>.md`.


Time-boxed, uninterrupted, one charter. Sixty minutes is the usual unit; ninety
is the practical ceiling before notes get thin.

Record as you go, not afterwards. A session reconstructed from memory loses
exactly the detail that made a finding reproducible.

```markdown
# Session CH-03 — 2026-09-14 14:00–15:00 — Alex T.
Build 2026.09.14-a4f21 · staging

## Coverage
Connect flow with the network throttled, interrupted mid-request, and with two
tabs connecting the same workspace simultaneously.

## Notes
14:06 Throttled to 3G. Connect takes 9s with no loading indicator at all — the
      button stays enabled and a second click starts a second request.
14:14 Double-clicked Connect. Two integrations created, both listed, identical
      names. No way to tell them apart in the UI.
14:31 Killed the request mid-flight at ~4s. UI shows an error; a record was
      created on the server regardless. Visible after a refresh.
14:48 Two tabs, same workspace. Both succeed. Duplicate again.

## Findings
- F1 No loading state; double submission creates duplicates — likely major
- F2 Cancelled request leaves a record — partial state, user cannot see it
- F3 No duplicate detection on workspace URL

## Not covered
Mobile viewport. Session expiry during connect — ran out of time, worth a charter.

## Time split
Setup 10m · exploring 40m · writing findings 10m
```

The **not covered** section is what makes a session honest, and the time split is
what tells you whether the environment is eating the session.

Keep the header (`# Session <id> — <date> <start>–<end> — <tester>`) and the *Time split*
line in this shape, then record the sheet: `qa-event session 04-results/<T>/sessions/<id>.md`.
`qa-metrics` reads hours, the setup / test / bug split and findings per session from it.

## Findings become scenarios

A finding that matters becomes a scripted case, so the next regression catches it
without anyone having to think of it again. Hand findings to
`scenarios-generator` as new scenarios and to `discrepancies-fix` as defect
drafts. F1 above is both: a defect now, and a case in the suite forever.

This is the loop that makes exploratory testing compound rather than evaporate.

## When to use it

- **Before scripted cases exist**, on a feature too new to specify — the session
  produces both findings and better cases
- **After scripted execution passes cleanly.** A clean scripted run means the
  cases were right, not that the feature is correct
- **On legacy areas with no requirements**, where writing cases first would mean
  inventing the specification
- **On integrations**, where neither side's tests cover the boundary

## What it does not replace

It is not a substitute for coverage, and a report cannot claim a requirement is
covered because somebody explored near it. Keep the two accountings separate:
scripted coverage is measured against requirements, exploratory coverage is
measured in charters completed and areas visited.

## Self-check

1. Every charter states an area, a risk and a time-box.
2. Every session records what was covered **and** what was not.
3. Findings are specific enough to reproduce without the author present.
4. Findings that matter became scenarios, not just defects.
5. Exploratory coverage is reported separately from requirement coverage.
