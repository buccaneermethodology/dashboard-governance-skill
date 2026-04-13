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

Keep `examples/Dashboard/` in the repository as templates.

## Cursor, Windsurf, Continue, Or Other IDE Agents

Use the `SKILL.md` content as a workspace rule or reusable prompt. Keep the reference file available to the model when the task involves Dashboard row semantics, emergent sessions, or KB/Dashboard boundaries.

## Model Independence

The method is most reliable when paired with durable repo artifacts:

- `Dashboard/Methodology.md`
- `Dashboard/Rules.md`
- `Dashboard/Big_Ideas.md`
- `Dashboard/Sessions.md`
- `Dashboard/Decisions.md`
- repository workflow rules that require end-of-task review

Do not rely on chat memory alone.
