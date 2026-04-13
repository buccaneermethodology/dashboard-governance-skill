# Contributing

Contributions should keep the skill small, portable, and directly useful to an AI coding agent.

## Guidelines

- Keep `SKILL.md` concise and workflow-focused.
- Put detailed reusable method notes in `references/dashboard-method.md`.
- Avoid adding repository-specific project names or paths.
- Keep examples generic enough to reuse across projects.
- Run validation before opening a pull request.

## Validate

```bash
python3 scripts/validate_skill.py skill/dashboard-governance
```

## Pull Request Checklist

- The skill frontmatter has `name` and `description`.
- The description clearly states when to use the skill.
- `agents/openai.yaml` has a default prompt that names `$dashboard-governance`.
- Example Dashboard tables remain valid Markdown.
- No project-specific private information was introduced.
