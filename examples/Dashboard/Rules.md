# Dashboard Rules

## Boundaries

- Put stable truth in the KB, docs, ADRs, specs, or contracts.
- Put status, sequencing, blockers, and candidate next work here.
- If a row changes stable truth, update the canonical source too.

## Row Rules

- Every row needs an ID.
- Big Ideas and Sessions should expose Topic, Scope, and Purpose.
- Every row should have exit criteria.
- Sessions should be small enough to complete in one focused work cycle.
- Decisions should state a recommended option when possible.
- Status must use the lifecycle values authorized by the selected Dashboard governance contract. This template uses the bundled portable contract: `todo`, `doing`, `blocked`, `decision-needed`, `done`, `archived`, or `cancelled`.
- Keep lifecycle Status separate from delivery state, claim ceiling, authority/blocker, evidence, and next action.

## Scope Narrowing

If a session only completed a narrower subset of its original scope:

1. Update the row text so Topic, Scope, Deliverable, Exit Criteria, and Notes describe the completed subset.
2. Mark the revised row `done`.
3. Add follow-on sessions for the remaining concrete work.

Do not close a row whose wording still claims unfinished scope.

## Candidate Memory

- Add concrete P0/P1 next-session candidates by default.
- Add P2/P3 candidates only when they are specific, low-noise, and costly to rediscover.
- Do not add vague low-priority speculation.

## Frontier Control

- Keep the README `Current Snapshot` short.
- Treat Dashboard rows as indexes, not long-form reports.
- Move long history to closeout reports, archives, project docs, or KB entries.

## End-of-Task Review

At the end of meaningful work, ask:

1. Did any session status change?
2. Did any Big Idea advance or reshape?
3. Did completed scope narrow before closeout?
4. Did any P0/P1 session emerge, or any concrete P2/P3 memory candidate with high rediscovery cost?
5. Did any decision need to be recorded?
6. Did stable truth change outside the Dashboard?
7. Does the next recommendation explain what the row is, why now, and why it outranks alternatives?
