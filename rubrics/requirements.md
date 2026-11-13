# Rubric — requirements (after Gate 1)

Stage reviewed: `requirements-decomposer` (`02-analysis/<T>/requirements/`). Read the ticket
source (`_source.json` / `_fetch.json` and what it points to), the global context it cites,
`_index.json`, the story and task files and `OPEN_QUESTIONS.md`. Do not read the stage
agent's report or its gate file's self-check before you have answered every item: you are
checking the artefacts, not the agent's account of them.

Sample when an item says so; name the sample in the evidence. An item is `agree` when the
artefacts meet it, `disagree` when you found a counter-example (cite it), `n/a` when it
cannot apply (say why).

| ID | Question | How to check |
|---|---|---|
| RQ1 | Does every sampled requirement say what its `source` anchor says? | Open the anchor for 10 requirements (all if 30 or fewer); compare the claim, not the wording |
| RQ2 | Is any limit, status code, message or enum value stated that no source states? | Every number and quoted string in the sample: find it in the source or in a probe the file names |
| RQ3 | Is every acceptance criterion observable and single-outcome? | A tester could decide pass/fail from `then` alone; no "works", no two outcomes joined by "and" |
| RQ4 | Does each story have its main flow and at least one failure mode in its criteria? | Per story: list the criteria; the unhappy path is the one most often missing |
| RQ5 | Are contradictions between sources surfaced, not silently resolved? | Where two sources disagree (spec vs code vs UI), there is a finding or a question, not a quiet pick |
| RQ6 | Is every invented value marked `proposed` with an open question and a default? | Search the requirements for values without a source; each must be `proposed` and cited by a Q |
| RQ7 | Is behaviour that looks like a defect accepted as `as-built`? | A 500 for bad input, data loss, a security gap recorded as the requirement is a disagreement |
| RQ8 | Is anything in the source missing from the requirements? | Endpoints, fields, roles, validation rules, error paths in the source with no requirement |
| RQ9 | Are NFRs present, or explicitly N/A with a reason? | Performance, security, accessibility, data retention: present, waived with reason, or questioned |
| RQ10 | Can each open question be answered in one reply? | One decision per question, the options or the proposed default stated, what it blocks named |

A disagreement is a finding the engineer must decide on. State it as a question with your
proposed default, the requirement IDs it concerns, and the evidence (file:line or probe).
