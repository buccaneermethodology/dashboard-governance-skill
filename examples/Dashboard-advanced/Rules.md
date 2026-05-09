# Advanced Dashboard Rules

## Boundaries

- Put stable truth in the KB, docs, ADRs, specs, or contracts.
- Put execution state, sequencing, blockers, risks, and validation gates here.
- Treat every Dashboard row as an index to durable work, not as the work itself.

## Required Core

- Keep `Big_Ideas.md`, `Sessions.md`, and `Decisions.md` present.
- Big Ideas and Sessions must expose Topic, Scope, and Purpose.
- Status must use: `todo`, `doing`, `blocked`, `decision-needed`, `done`, `archived`, or `cancelled`.
- Exit Criteria must be non-empty for Big Ideas, Sessions, and Stage Plans.

## Advanced Closeout

For non-trivial governed batches:

1. Confirm Builder artifacts exist.
2. Record a Validation verdict or the reason validation is blocked.
3. Narrow any overbroad completed row before marking it `done`.
4. Add follow-on rows for unfinished concrete work.
5. Explain the next recommendation with row ID, topic, why now, and why before other open rows.

## Candidate Memory

- Add P0/P1 next sessions by default when they are concrete.
- Add P2/P3 rows only when they are specific, low-noise, and costly to rediscover.
- Cancel rows that are intentionally stopped; archive rows that are kept only for reference.

## Bloat Control

- Keep Notes short.
- Put long closure narrative in closeout reports or external artifacts.
- Keep the README `Current Frontier` short enough to scan before reading tables.
