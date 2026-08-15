# Portability

The dashboard-governance skill is designed to be portable because its core is a method, not a Codex-only implementation.

## Codex

Install `skill/dashboard-governance` into `$CODEX_HOME/skills` or `~/.codex/skills`.

Invoke it with:

```text
Use $dashboard-governance to update Dashboard after this task.
```

## Claude Code

Move the workflow into one of these locations:

- `CLAUDE.md`
- `.claude/rules/dashboard-governance.md`
- a project command that says to follow the Dashboard method

Keep `examples/Dashboard/` in the repository as the minimal template. Use `examples/Dashboard-advanced/` only when the project needs optional stage plans, risks, exceptions, quality metrics, automation, external artifact indexes, or agent logs.

If adopting the advanced registry, copy `examples/contracts/dashboard_governance_contract.json` to `kb/data/strategy/dashboard_governance_contract.json` or supply an equivalent project contract. The sample is a portable default, not a claim that every project uses the same lifecycle.

## Cursor, Windsurf, Continue, Or Other IDE Agents

Use the `SKILL.md` content as a workspace rule or reusable prompt. Keep the method references available to the model when the task involves Dashboard row semantics, scope-aware closeout, emergent sessions, KB/Dashboard boundaries, or advanced validation and closure lanes.

## Model Independence

The method is most reliable when paired with durable repo artifacts:

- `Dashboard/Methodology.md`
- `Dashboard/Rules.md`
- `Dashboard/Big_Ideas.md`
- `Dashboard/Sessions.md`
- `Dashboard/Decisions.md`
- optional advanced files such as `Dashboard/Stage_Plans.md`, `Dashboard/Risks.md`, and `Dashboard/Quality_Metrics.md`
- repository workflow rules that require end-of-task review

Do not rely on chat memory alone.

## Capability Detection

- If a project provides `kb/data/strategy/dashboard_governance_contract.json`, use it as lifecycle and field authority.
- Otherwise a repository validator may explicitly receive the bundled sample with `--contract`; do not silently claim project-specific authority.
- If current/index/archive/manifest surfaces and registry tooling are absent, use the minimal Dashboard mode and do not claim reconciliation.
- If registry tooling exists, require `reconcile --check` and `validate` before DKG generation. DKG remains a non-authoritative read model.

The tools use only Python's standard library and relative paths. They contain no Semx project path, private phase code, or migration-only identity rule.
