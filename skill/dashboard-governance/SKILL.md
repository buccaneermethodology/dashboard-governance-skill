---
name: dashboard-governance
description: Maintain a Big-Idea/Session/Decision project Dashboard with Big Ideas, Sessions, Decisions, TSP fields, and emergent next steps. Use when a repository has a Dashboard directory or the user asks to track execution state, update task/session status, split long-running ideas from bounded work, record decisions, or identify high-priority sessions after completing a task.
---

# Dashboard Governance

## Workflow

Use this skill to keep execution state visible without contaminating canonical project truth.

1. Read repository workflow rules first, especially any instructions that define KB vs Dashboard boundaries.
2. Treat Big Ideas as stable semantic tracks and Sessions as bounded time-slice work.
3. Require TSP for Big Ideas and Sessions: Topic, Scope, and Purpose.
4. Track decisions separately when an unresolved choice could distort multiple sessions.
5. At task start, set the active session to `doing` if a row exists.
6. At task end, mark completed sessions, update parent Big Idea next steps, and record durable output paths.
7. Check whether one or more high-priority emergent sessions became visible.
8. Add only concrete P0 or P1 candidates by default. A `todo` session is a visible option, not an execution promise.

## KB Boundary

- Put stable architecture, contracts, rollout policy, terminology, and durable decisions in the KB.
- Put status, priorities, blockers, active work, and candidate next sessions in the Dashboard.
- If a Dashboard row changes canonical truth, update the KB or create a decision artifact.

## References

Read `references/dashboard-method.md` for row semantics, TSP guidance, status vocabulary, and end-of-task review prompts.
