# Dashboard Method

## Row Types

Use these row types:

- Big Idea: a long-lived semantic track or implementation direction.
- Session: a bounded execution or exploration time-slice.
- Decision: a choice that blocks or shapes multiple sessions.

Keep these as the minimal core. Advanced projects may add optional files for stage plans, risks, exceptions, quality metrics, automation, external artifacts, and agent logs. See `advanced-governance.md` only when that extra layer is present or requested.

## TSP

Every Big Idea and Session should expose:

- Topic: the central subject.
- Scope: what is inside and outside the item.
- Purpose: why the item matters now.

## Status Vocabulary

Use a small controlled vocabulary:

- `todo`: visible candidate next step.
- `doing`: currently active.
- `blocked`: waiting on dependency.
- `decision-needed`: cannot proceed safely without a choice.
- `done`: completed and reflected in a durable artifact.
- `archived`: kept for reference, not active.
- `cancelled`: intentionally stopped and not expected to resume.

## Emergent Session Filter

Add a new session when it is concrete, newly visible from work just completed, and worth preserving as execution memory.

Score candidates by:

- necessity
- urgency
- leverage
- value
- freshness
- rediscovery cost
- hidden debt risk

Add P0 or P1 candidates by default. Add P2/P3 candidates only when they are specific, low-noise, and costly to rediscover or likely to become hidden debt. Do not add vague low-priority speculation.

## Scope Narrowing Closeout

If actual work completed only a narrower subset of the original session:

1. Rewrite the row Topic, Scope, Deliverable, Exit Criteria, and Notes so the row describes what actually completed.
2. Mark the revised row `done` only after the narrowed scope is accurate.
3. Add one or more follow-on sessions for the remaining concrete work.
4. Keep the follow-on rows specific enough that a later agent does not need to reconstruct the omitted scope from chat history.

Do not mark an overbroad row `done` and leave the uncompleted parts implicit.

## Next Recommendation Quality

When recommending the next step in a closeout, include:

- the ID and topic of the recommended Big Idea, Stage Plan, or Session
- what the item is meant to accomplish
- why it is timely now
- why it outranks other open rows

Do not write only `Next: S-123`. If there is no strong next recommendation, say that and explain what signal is missing.

## Dashboard Bloat Control

The Dashboard is an index, not a second KB.

- Keep rows short enough to scan.
- Put long history in closeout reports, archives, project docs, or KB entries.
- Use Notes for durable pointers and concise rationale, not transcripts.
- Keep a short `Current Frontier` or `Current Snapshot` near the top of the Dashboard README when the project has many open rows.

## End-of-Task Review

Ask:

1. Did any tracked session change status?
2. Did this task advance or reshape a Big Idea?
3. Did the completed scope narrow relative to the original row?
4. Did a new P0/P1 session emerge, or a concrete P2/P3 memory candidate with high rediscovery cost?
5. Should any session be reprioritized, split, merged, archived, or cancelled?
6. Did any recommendation need more detail than a bare ID?
7. Are any Notes too long for a Dashboard row?
8. Does a non-trivial governed batch need validation or closure before being marked complete?
9. Did any choice belong in Decisions instead of Sessions?
10. Did stable truth change, requiring a KB update?

## Forward-Test Prompt

Representative user request:

```text
Use $dashboard-governance after finishing this task. Update Big Ideas, Sessions, and Decisions, decide whether any candidate next sessions emerged, and recommend the next row with rationale.
```

Expected first actions:

1. Read repository-specific dashboard rules before editing rows.
2. Identify the active or completed session.
3. Decide whether stable truth changed and belongs in the KB instead.
4. If the completed work is narrower than the row, update the row text before closing it.
5. Update status and durable output paths.
6. Evaluate new sessions with the emergent session filter.
7. Add concrete P0/P1 candidates by default, and P2/P3 only when they preserve specific high-value memory.
8. Recommend the next row with a short why-now and why-this explanation.

Output checklist:

- Big Ideas remain more stable than Sessions.
- Completed sessions do not automatically close parent Big Ideas.
- Decisions are recorded separately from task rows.
- New sessions expose Topic, Scope, and Purpose.
- `todo` means visible candidate, not execution commitment.
- `cancelled` means intentionally stopped, not forgotten.
- Closeout does not overclaim broader work than actually completed.
- Final next recommendations explain what, why now, and why before other open rows.
- Final response states whether KB and Dashboard needed updates.
