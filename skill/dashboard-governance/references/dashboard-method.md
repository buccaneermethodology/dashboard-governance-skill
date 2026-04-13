# Dashboard Method

## Row Types

Use these row types:

- Big Idea: a long-lived semantic track or implementation direction.
- Session: a bounded execution or exploration time-slice.
- Decision: a choice that blocks or shapes multiple sessions.

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

## Emergent Session Filter

Add a new session when it is concrete, high priority, and newly visible from work just completed.

Score candidates by:

- necessity
- urgency
- leverage
- value
- freshness

Add P0 or P1 candidates by default. Do not add low-priority speculation.

## End-of-Task Review

Ask:

1. Did any tracked session change status?
2. Did this task advance or reshape a Big Idea?
3. Did a new P0 or P1 session emerge?
4. Should any session be reprioritized, split, merged, or archived?
5. Did any choice belong in Decisions instead of Sessions?
6. Did stable truth change, requiring a KB update?

## Forward-Test Prompt

Representative user request:

```text
Use $dashboard-governance after finishing this task. Update Big Ideas, Sessions, and Decisions, and decide whether any high-priority sessions emerged.
```

Expected first actions:

1. Read repository-specific dashboard rules before editing rows.
2. Identify the active or completed session.
3. Decide whether stable truth changed and belongs in the KB instead.
4. Update status and durable output paths.
5. Evaluate new sessions with the emergent session filter.
6. Add concrete P0/P1 candidates only when they are likely near-term options.

Output checklist:

- Big Ideas remain more stable than Sessions.
- Completed sessions do not automatically close parent Big Ideas.
- Decisions are recorded separately from task rows.
- New sessions expose Topic, Scope, and Purpose.
- `todo` means visible candidate, not execution commitment.
- Final response states whether KB and Dashboard needed updates.
