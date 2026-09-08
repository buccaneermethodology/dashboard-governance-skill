# Advanced Dashboard Rules

## Boundaries

- Put stable truth in the KB, docs, ADRs, specs, or contracts.
- Put execution state, sequencing, blockers, risks, and validation gates here.
- Treat every Dashboard row as an index to durable work, not as the work itself.

## Required Core

- Keep `Big_Ideas.md`, `Sessions.md`, and `Decisions.md` present.
- Big Ideas and Sessions must expose Topic, Scope, and Purpose.
- Status must use the lifecycle values authorized by the selected Dashboard governance contract. This template uses the bundled portable contract: `todo`, `doing`, `blocked`, `decision-needed`, `done`, `archived`, or `cancelled`.
- Keep lifecycle Status separate from delivery state, claim ceiling, authority/blocker, evidence, and next action.
- Exit Criteria must be non-empty for Big Ideas, Sessions, and Stage Plans.

## Advanced Closeout

For non-trivial governed batches:

1. Confirm Builder artifacts exist.
2. Record a Validation verdict or the reason validation is blocked.
3. Narrow any overbroad completed row before marking it `done`.
4. Add follow-on rows for unfinished concrete work.
5. Explain the next recommendation with row ID, topic, why now, and why before other open rows.

## Artifact Batches

- Keep durable outputs under `Artifacts/`, grouped by the owning Goal or Stage Plan.
- Use `Artifacts/Goal-<GOAL-ID>/` or `Artifacts/Stage-Plan-<STAGE-PLAN-ID>/` and keep a batch `README.md` with scope and provenance.
- Keep the `Artifacts/` root free of direct artifact files; use optional type subdirectories only inside a batch.
- Prefer the narrowest owner and do not duplicate one artifact in both a Goal and a Stage Plan batch.
- Validate the layout with `python3 scripts/validate_artifacts.py Dashboard/Artifacts` when the project adopts the portable validator.

## Registry And DKG

- `Sessions.md` and archive Markdown are authoritative records; `Session_Index.md` is derived.
- Run `python3 Dashboard/tools/session_registry.py reconcile --repo . --check` and `validate` before and after Session changes.
- Use `reconcile --apply` only for reported derived drift. Duplicate identity, malformed rows, unknown Status, or unknown archive files require manual handling.
- Generate `dashboard-kg.json` explicitly only after both registry gates pass. Reconcile never generates it.

## Candidate Memory

- Add P0/P1 next sessions by default when they are concrete.
- Add P2/P3 rows only when they are specific, low-noise, and costly to rediscover.
- Cancel rows that are intentionally stopped; archive rows that are kept only for reference.

## Bloat Control

- Keep Notes short.
- Put long closure narrative in closeout reports or external artifacts.
- Keep the README `Current Frontier` short enough to scan before reading tables.
