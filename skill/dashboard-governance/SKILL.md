---
name: dashboard-governance
description: Maintain a Big-Idea/Session/Decision project Dashboard with contract-authoritative lifecycle status, TSP fields, scope-aware closeout, optional current/index/archive/manifest reconciliation, and DKG post-gate generation. Use when a repository has a Dashboard directory or the user asks to track execution state, update task/session status, reconcile a Session registry, record decisions, or identify next sessions after completing a task.
---

# Dashboard Governance

## Workflow

Use this skill to keep execution state visible without contaminating canonical project truth.

1. Read repository workflow rules first. If the project provides `kb/data/strategy/dashboard_governance_contract.json`, read it before interpreting fields or lifecycle Status. Otherwise use the bundled portable sample contract as an explicit default.
2. Treat Big Ideas as stable semantic tracks and Sessions as bounded time-slice work.
3. Require TSP for Big Ideas and Sessions: Topic, Scope, and Purpose.
4. Track decisions separately when an unresolved choice could distort multiple sessions.
5. Keep lifecycle `Status` separate from Delivery State, Claim Ceiling, Authority / Blocker, Evidence, and Next. Never invent compound lifecycle values such as `partial`, `proposed`, or `bounded-*`.
6. At task start, set the active session to the contract-authorized active value if a row exists.
7. If actual work completed only a narrowed subset, record the scope delta and follow-on work; do not silently rewrite the original scope into apparent full completion.
8. At task end, update Status and the other state axes independently, update parent Big Idea next steps, and record durable output paths or closeout notes. A completed Session never closes its parent automatically.
9. Check whether one or more candidate next sessions became visible.
10. Add concrete P0 or P1 candidates by default. Add P2/P3 candidates only when they are specific, low-noise, and costly to rediscover. A `todo` session is a visible option, not an execution promise.
11. When the project uses advanced validation or closure lanes, do not close the governed batch until the required validation verdict or closure note is recorded.

## Session Registry

When a project has any of `Dashboard/Session_Index.md`, `Dashboard/Archives/Sessions/`, or `Dashboard/Archives/Sessions/archive_manifest.json`, treat it as registry-capable and read `references/dashboard-method.md` before editing Session records.

1. Run the project-provided `session_registry.py reconcile --check` and `validate` commands before editing.
2. Edit the authoritative current or archive Markdown record, not the derived index.
3. Run `reconcile --check`. Use `reconcile --apply` only for derived drift that the tool explicitly identifies as repairable, then rerun `--check` and `validate`.
4. Stop on duplicate identity, malformed row, unknown Status, or unknown archive surface. Do not guess, delete, or use first-wins behavior.
5. Generate DKG only after both registry gates pass, only when graph-affecting inputs changed, and only through an explicit generator command. Reconciliation must not generate DKG as a side effect, and DKG is never Session authority.

If the project has no registry tooling, report that the capability is unavailable. Do not claim reconciliation from prose inspection. The repository's `examples/Dashboard-advanced/tools/` provides portable sample tooling that projects may adopt explicitly.

## KB Boundary

- Put stable architecture, contracts, rollout policy, terminology, and durable decisions in the KB.
- Put status, priorities, blockers, active work, and candidate next sessions in the Dashboard.
- If a Dashboard row changes canonical truth, update the KB or create a decision artifact.

## References

Read `references/dashboard-method.md` for contract discovery, row semantics, TSP guidance, registry operation, DKG ordering, and end-of-task review prompts.

Read `references/advanced-governance.md` only when the repository already has advanced Dashboard files, the user asks for advanced governed execution, or a non-trivial governed batch needs stage plans, risks, exceptions, quality metrics, automation, external artifact tracking, validation, or closure lanes.
