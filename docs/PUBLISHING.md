# Publishing

Use this checklist before publishing the dashboard-governance skill.

## Preflight

- Remove private project names, absolute local paths, and proprietary examples.
- Confirm `VERSION`, tag, and release title all use `0.4.0` / `v0.4.0`.
- Keep the installable skill folder self-contained under `skill/dashboard-governance/`.
- Keep examples generic enough to copy into another repository.
- Run `python3 scripts/validate_skill.py skill/dashboard-governance`.
- Run `python3 scripts/validate_dashboard.py examples/Dashboard --contract examples/contracts/dashboard_governance_contract.json`.
- Run `python3 scripts/validate_dashboard.py examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json --require-registry`.
- Run `python3 scripts/test_registry.py` for positive, derived-drift, DKG-ordering, unknown-Status, and unknown-archive cases.
- Run `python3 scripts/validate_artifacts.py examples/Dashboard-advanced/Artifacts` and `python3 scripts/test_artifacts.py`.
- Run `python3 scripts/test_work_breakdown.py` and `python3 scripts/test_authority_bundle.py`. The latter provisions the frozen owner bundle into an isolated installed copy before running the advanced positive validator; do not add task-selected anchor flags or environment overrides.
- Run `python3 scripts/test_release_package.py` to verify deterministic archive bytes, inventory closure, checksums, and tamper refusal.
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

Build the release assets twice from the exact committed tree and compare them before tagging:

```bash
python3 scripts/build_release_package.py build \
  --source skill/dashboard-governance \
  --version 0.4.0 \
  --output-dir dist-a
python3 scripts/build_release_package.py build \
  --source skill/dashboard-governance \
  --version 0.4.0 \
  --output-dir dist-b
cmp dist-a/dashboard-governance-skill-v0.4.0.tar.gz \
  dist-b/dashboard-governance-skill-v0.4.0.tar.gz
cmp dist-a/SHA256SUMS dist-b/SHA256SUMS
python3 scripts/build_release_package.py verify \
  --archive dist-a/dashboard-governance-skill-v0.4.0.tar.gz \
  --checksums dist-a/SHA256SUMS \
  --source skill/dashboard-governance
```

The archive contains only the installable `dashboard-governance/` skill directory. Tar member order and metadata are normalized; symlinks and special objects are rejected. `SHA256SUMS` covers the archive bytes.

Before any remote write, verify that the tag and release do not already exist:

```bash
git ls-remote --tags origin 'refs/tags/v0.4.0' 'refs/tags/v0.4.0^{}'
gh release view v0.4.0 --repo buccaneermethodology/dashboard-governance-skill
```

After the committed candidate and CI pass, create and push the tag, then create the release with both assets:

```bash
git tag -a v0.4.0 -m "dashboard-governance v0.4.0"
git push origin v0.4.0
gh release create v0.4.0 \
  dist-a/dashboard-governance-skill-v0.4.0.tar.gz \
  dist-a/SHA256SUMS \
  --repo buccaneermethodology/dashboard-governance-skill \
  --title "dashboard-governance v0.4.0" \
  --notes "See the v0.4.0 release notes in docs/PUBLISHING.md."
```

Do not treat release creation as verification. Download the remote assets into a fresh directory, verify `SHA256SUMS`, verify archive inventory, and compare the remote tag commit with the intended release commit:

```bash
mkdir -p /tmp/dashboard-governance-v0.4.0-readback
gh release download v0.4.0 \
  --repo buccaneermethodology/dashboard-governance-skill \
  --dir /tmp/dashboard-governance-v0.4.0-readback
cd /tmp/dashboard-governance-v0.4.0-readback
shasum -a 256 -c SHA256SUMS
cd -
python3 scripts/build_release_package.py verify \
  --archive /tmp/dashboard-governance-v0.4.0-readback/dashboard-governance-skill-v0.4.0.tar.gz \
  --checksums /tmp/dashboard-governance-v0.4.0-readback/SHA256SUMS \
  --source skill/dashboard-governance
git ls-remote --tags origin 'refs/tags/v0.4.0' 'refs/tags/v0.4.0^{}'
gh release view v0.4.0 --repo buccaneermethodology/dashboard-governance-skill --json tagName,targetCommitish,assets,url
gh run list --repo buccaneermethodology/dashboard-governance-skill --limit 10
```

## v0.4.0 Release Notes

- Group durable artifacts by owning Goal or Stage Plan under one dedicated batch directory.
- Add a fail-closed validator and tests for loose root files, invalid batch names, missing batch metadata, and symlinks.
- Document the batch convention across the Skill, advanced Dashboard example, portability guide, and release checklist.

These notes describe the `v0.4.0` candidate. They do not claim a tag, push, or GitHub Release until remote read-back succeeds.

- Adds an advanced v2 Session/Milestone/Lane work-breakdown contract and standard-library validator.
- Keeps the minimal profile compatible and reports legacy advanced data as migration-required instead of silently claiming v2 compliance.
- Adds positive, negative, migration, and naming-warning fixtures for the Session Granularity Gate.
- Adds owner-provisioned Authority v2 bundles, fixed managed-boundary loading, strict manifest closure, and installed-copy positive/negative gates.
- Adds deterministic installable-skill archives, `SHA256SUMS`, inventory verification, and explicit remote read-back.
