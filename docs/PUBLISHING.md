# Publishing

Use this checklist before publishing the dashboard-governance skill.

## Preflight

- Remove private project names, absolute local paths, and proprietary examples.
- Keep the installable skill folder self-contained under `skill/dashboard-governance/`.
- Keep examples generic enough to copy into another repository.
- Run `python3 scripts/validate_skill.py skill/dashboard-governance`.
- Run the official validator when available: `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/dashboard-governance`.

## First Publish

```bash
git init
git branch -M main
git add .
git commit -m "Initial dashboard-governance skill release"
gh repo create dashboard-governance-skill --public --source . --remote origin --push
```

## Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

Use GitHub Releases to describe installation, validator status, and any Dashboard method changes.
