---
name: dashboard-governance
description: Maintain a Big-Idea/Session/Decision project Dashboard with Big Ideas, Sessions, Decisions, TSP fields, scope-aware closeout, candidate next steps, and optional advanced governance files. Use when a repository has a Dashboard directory or the user asks to track execution state, update task/session status, split or narrow long-running work, record decisions, or identify next sessions after completing a task.
---

# Dashboard Governance

## Workflow

Use this skill to keep execution state visible without contaminating canonical project truth.

1. Read repository workflow rules first, especially any instructions that define KB vs Dashboard boundaries.
2. Treat Big Ideas as stable semantic tracks and Sessions as bounded time-slice work.
3. Require TSP for Big Ideas and Sessions: Topic, Scope, and Purpose.
4. Track decisions separately when an unresolved choice could distort multiple sessions.
5. At task start, set the active session to `doing` if a row exists.
6. If actual work completed only a narrowed subset, rewrite the row to that completed scope before marking it `done`, then add follow-on sessions for the remainder.
7. At task end, mark completed sessions, update parent Big Idea next steps, and record durable output paths or closeout notes.
8. Check whether one or more candidate next sessions became visible.
9. Add concrete P0 or P1 candidates by default. Add P2/P3 candidates only when they are specific, low-noise, and costly to rediscover. A `todo` session is a visible option, not an execution promise.
10. When the project uses advanced validation or closure lanes, do not close the governed batch until the required validation verdict or closure note is recorded.

## KB Boundary

- Put stable architecture, contracts, rollout policy, terminology, and durable decisions in the KB.
- Put status, priorities, blockers, active work, and candidate next sessions in the Dashboard.
- If a Dashboard row changes canonical truth, update the KB or create a decision artifact.

## References

Read `references/dashboard-method.md` for row semantics, TSP guidance, status vocabulary, and end-of-task review prompts.

Read `references/advanced-governance.md` only when the repository already has advanced Dashboard files, the user asks for advanced governed execution, or a non-trivial governed batch needs stage plans, risks, exceptions, quality metrics, automation, external artifact tracking, validation, or closure lanes.
