# Advanced Dashboard Methodology

The advanced Dashboard is an execution-state index for projects that need more than Big Ideas, Sessions, and Decisions.

It adds optional files for stage plans, risks, exceptions, quality metrics, automation, external artifacts, and agent log conventions. These files are still not canonical truth. They help agents close work honestly, preserve high-value memory, and avoid rediscovering specific deferred work.

Durable outputs use the optional `Artifacts/` batch layout: one `Goal-<ID>/` or `Stage-Plan-<ID>/` directory per owner, with a batch `README.md` describing scope and provenance. The root is only a locator surface; it must not accumulate loose files.

## Lanes

- Builder creates or changes the primary artifacts.
- Validation checks acceptance criteria and records a verdict with evidence.
- Closure reconciles Dashboard rows, narrowed scope, follow-on sessions, and next recommendations.

One agent can perform all lanes in sequence. Multiple agents are optional for non-trivial governed batches.

## Closeout Gate

A Stage Plan with a Validation lane cannot be marked `done` until validation evidence exists or the missing validation has been converted into an explicit blocker, risk, exception, or follow-on session.

## Scope Narrowing

If only a narrowed subset finished, rewrite the row to match the completed subset before marking it `done`. Preserve the remaining work as concrete follow-on Sessions or Stage Plans.

## Frontier Control

Keep `README.md` focused on the current frontier. Move long history into closeout reports, archives, external artifacts, or canonical project docs.

## Portable Authority And Registry

This example uses `../contracts/dashboard_governance_contract.json` as its lifecycle and field authority. A consuming repository should prefer its own `kb/data/strategy/dashboard_governance_contract.json` when present.

The advanced example also demonstrates a four-surface Session registry: current records, locator index, archived records, and archive manifest. Its tools reconcile only derived surfaces. DKG generation is a separate post-gate command and produces a non-authoritative read model.
