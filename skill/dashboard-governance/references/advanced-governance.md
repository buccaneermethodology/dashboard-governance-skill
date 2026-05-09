# Advanced Governance

Use this reference only when a project has outgrown the minimal Big Ideas / Sessions / Decisions Dashboard, or when the user explicitly asks for advanced governed execution.

The advanced layer is optional. Do not make ordinary projects create these files before they need them.

## Optional Files

Add these files only when they reduce hidden coordination cost:

- `Stage_Plans.md`: bounded multi-session plans, release gates, or phase slices.
- `Risks.md`: known risks, triggers, mitigations, and next reviews.
- `Exceptions.md`: intentional deviations from normal rules, contracts, or process.
- `Quality_Metrics.md`: evidence targets, quality bars, validation results, and metric history.
- `Automation.md`: recurring checks, reminders, monitors, scripts, or scheduled maintenance.
- `External_Artifacts.md`: durable artifacts outside the Dashboard, including reports, PRs, issues, datasets, generated files, and release links.
- `Agent_Logs/README.md`: conventions for storing or referencing agent logs when a project requires them.

These files remain indexes. Put durable project truth in the KB, specs, ADRs, or contracts. Put long narrative history in closeout reports, archives, or external artifacts.

## Advanced Lanes

For non-trivial governed batches, split the work conceptually into three lanes:

- Builder: changes the implementation, docs, fixtures, or other primary artifacts.
- Validation: checks the result against acceptance criteria and records a verdict with evidence.
- Closure: reconciles Dashboard rows, scope narrowing, follow-on sessions, decisions, and next recommendation.

The lanes can be done by one agent in sequence or by multiple agents in parallel. Multi-agent execution is an advanced option, not a requirement.

## Validation Gate

When a Stage Plan or governed batch uses a Validation lane, do not mark it `done` until:

1. Builder artifacts exist and are referenced.
2. Validation has a recorded verdict: pass, fail, or conditional.
3. Failures or conditions have either been fixed or converted into explicit follow-on sessions, risks, exceptions, or decisions.
4. Closure has updated affected Big Ideas, Sessions, Stage Plans, and next recommendations.

If validation is not possible, record why in Notes and keep the status honest: `blocked`, `decision-needed`, `cancelled`, or a narrower `done` row with follow-on work.

## Scope Narrowing In Advanced Batches

When a governed batch finishes only part of the original Stage Plan or Session:

1. Narrow the completed row before closing it.
2. Record the reason for narrowing in Notes or a closeout artifact.
3. Add follow-on rows for each remaining concrete part.
4. Keep risk, exception, metric, and external artifact indexes aligned with the narrowed scope.

This prevents a Stage Plan from claiming completion while unfinished work survives only in chat memory.

## Advanced Next Recommendation

Closeout should recommend the next Big Idea, Stage Plan, or Session by naming:

- the row ID and topic
- the intended outcome
- the current signal that makes it timely
- why it outranks other open rows
- whether validation, closure, or human decision is the limiting factor

## Anti-Bloat Rules

- Keep the Dashboard frontier visible with a short `Current Frontier` or `Current Snapshot` in `README.md`.
- Prefer pointers over pasted detail.
- Move long Notes into a closeout report, archive entry, external artifact, or KB document.
- Use P2/P3 memory rows sparingly: only for specific items with high rediscovery cost or hidden debt risk.
- Do not bake project-specific phase codes, readiness routers, evaluator seeds, or private release rituals into the generic Dashboard method.

## Minimal Suggested Schemas

`Stage_Plans.md`:

| ID | Topic | Scope | Purpose | Status | Tracks | Exit Criteria | Validation | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

`Risks.md`:

| ID | Topic | Status | Severity | Trigger | Mitigation | Next Review | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

`Exceptions.md`:

| ID | Topic | Status | Related Row | Exception | Resolution | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

`Quality_Metrics.md`:

| ID | Metric | Status | Target | Current | Evidence | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |

`Automation.md`:

| ID | Topic | Status | Trigger | Action | Owner | Last Run | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

`External_Artifacts.md`:

| ID | Topic | Status | Location | Artifact Type | Related Rows | Verification | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
