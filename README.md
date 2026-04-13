# Dashboard Governance Skill

A portable Codex skill for maintaining a Big-Idea/Session/Decision project Dashboard with Big Ideas, Sessions, Decisions, TSP fields, and emergent next steps.

This repository packages the `dashboard-governance` skill as a reusable open-source asset. It helps an AI coding agent keep execution state visible without contaminating canonical project truth.

## What This Skill Does

Use this skill when a repository has, or should have, a `Dashboard/` directory that tracks project execution state.

It helps the agent:

- keep stable project truth separate from task state
- maintain Big Ideas, Sessions, and Decisions
- use TSP fields: Topic, Scope, Purpose
- update active and completed sessions
- record decision-needed work separately from tasks
- identify concrete P0/P1 emergent sessions after meaningful progress
- preserve the rule that `todo` means candidate next step, not execution commitment

## Install For Codex

Copy the skill folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skill/dashboard-governance ~/.codex/skills/dashboard-governance
```

Then start a new Codex session so the skill registry is reloaded.

## Usage

Invoke the skill explicitly in natural language:

```text
Use $dashboard-governance after finishing this task. Update Big Ideas, Sessions, and Decisions, and decide whether any high-priority sessions emerged.
```

Or use it during a planning or review task:

```text
Use $dashboard-governance to create a Dashboard for this repository and seed initial Big Ideas, Sessions, and Decisions.
```

## Repository Layout

```text
skill/dashboard-governance/
  SKILL.md
  agents/openai.yaml
  references/dashboard-method.md
examples/Dashboard/
  README.md
  Methodology.md
  Rules.md
  Big_Ideas.md
  Sessions.md
  Decisions.md
scripts/
  validate_skill.py
.github/workflows/
  validate.yml
```

## Validate

Run the bundled no-dependency validator:

```bash
python3 scripts/validate_skill.py skill/dashboard-governance
```

If you have the official Codex skill validator available, you can also run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/dashboard-governance
```

## Publish To GitHub

From the repository root, create the GitHub repository and push the first commit:

```bash
gh repo create dashboard-governance-skill --public --source . --remote origin --push
```

If you prefer the GitHub web UI, create an empty public repository named `dashboard-governance-skill`, then run:

```bash
git remote add origin https://github.com/<owner>/dashboard-governance-skill.git
git push -u origin main
```

Recommended release flow:

1. Keep installable skill files under `skill/dashboard-governance/`.
2. Run local and official validators before tagging.
3. Tag stable releases with semantic versions such as `v0.1.0`.
4. Include compatibility notes when Dashboard row semantics change.

## Portability

The skill is written as plain Markdown plus small metadata files. See [docs/PORTABILITY.md](docs/PORTABILITY.md) for adapting the method to other IDE agents or model environments.

## License

MIT
