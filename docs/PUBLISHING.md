# Publishing

Use this checklist before publishing the dashboard-governance skill.

## Preflight

- Remove private project names, absolute local paths, and proprietary examples.
- Confirm `VERSION`, tag, and release title all use `0.2.0` / `v0.2.0`.
- Keep the installable skill folder self-contained under `skill/dashboard-governance/`.
- Keep examples generic enough to copy into another repository.
- Run `python3 scripts/validate_skill.py skill/dashboard-governance`.
- Run `python3 scripts/validate_dashboard.py examples/Dashboard --contract examples/contracts/dashboard_governance_contract.json`.
- Run `python3 scripts/validate_dashboard.py examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json --require-registry`.
- Run `python3 scripts/test_registry.py` for positive, derived-drift, DKG-ordering, unknown-Status, and unknown-archive cases.
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
git tag v0.2.0
git push origin v0.2.0
```

Use GitHub Releases to describe installation, validator status, and any Dashboard method changes.

## v0.2.0 Release Notes

- Make a project contract, or the explicitly selected portable sample, authoritative for lifecycle Status and field requirements.
- Keep lifecycle Status separate from delivery state, claim ceiling, authority/blocker, evidence, and next action.
- Add portable current/index/archive/manifest reconciliation with fail-closed identity, row, Status, symlink, and archive-surface handling.
- Add explicit DKG post-gate sample generation; reconcile does not generate DKG, and DKG remains a read model.
- Extend repository validation and CI with direct positive and fail-closed cases.

These notes describe the `v0.2.0` candidate. They do not claim a tag, push, or GitHub Release until remote read-back succeeds.
