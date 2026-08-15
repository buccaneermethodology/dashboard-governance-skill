# Dashboard Governance Skill

Current candidate version: `0.2.0`. Local files and validators do not prove publication; publication requires the tag and GitHub Release steps in `docs/PUBLISHING.md`.

[![validate](https://github.com/buccaneermethodology/dashboard-governance-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/buccaneermethodology/dashboard-governance-skill/actions/workflows/validate.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`dashboard-governance` is a portable Codex skill for maintaining a project Dashboard across long-running human-AI work. It helps an AI coding agent update Big Ideas, Sessions, Decisions, TSP fields, status, blockers, durable outputs, scope-aware closeout, and emergent next steps without treating the Dashboard as canonical project truth.

The skill is useful when a repository needs an execution-state layer that survives model changes, session changes, and handoff between humans and AI agents. The default template stays lightweight; v0.2.0 also adds an optional advanced governance layer for projects that need stage plans, risks, exceptions, quality metrics, automation, external artifact indexes, agent logs, or validation/closure lanes.

## What It Is For

Use this skill when you want an AI agent to:

- keep project execution state visible across sessions
- separate stable truth from active task tracking
- maintain a Dashboard with Big Ideas, Sessions, and Decisions
- preserve Topic, Scope, and Purpose for large tracks and bounded tasks
- update task state after meaningful progress
- record unresolved choices separately from implementation tasks
- close narrowed work honestly before marking rows done
- identify concrete P0/P1 next-session candidates after work finishes
- preserve P2/P3 candidate memory only when it is specific and costly to rediscover
- use optional advanced governance files for non-trivial governed batches
- keep `todo` rows as visible options, not execution promises

It is not a replacement for an architecture document, issue tracker, design review, or human priority decision. It is a lightweight coordination surface for agentic work.

## Core Concepts

### Big Ideas

Big Ideas are long-lived semantic tracks. They describe important directions, themes, or implementation streams that may span many work sessions. A Big Idea should not close just because one related session finishes.

### Sessions

Sessions are bounded execution or exploration units. They are small enough to be selected, completed, reviewed, and handed off. Sessions carry priority, status, dependencies, deliverables, exit criteria, next steps, and notes.

### Decisions

Decisions capture choices that could block or distort multiple sessions if left implicit. Keeping them separate from Sessions prevents unresolved strategy from becoming hidden task churn.

### TSP

TSP means Topic, Scope, and Purpose. Big Ideas and Sessions should expose all three so future agents can understand what the row is about, what is included or excluded, and why it matters.

### Emergent Sessions

After non-trivial work, the agent reviews whether a new bounded next step has become visible. Concrete P0/P1 candidates should be added by default. P2/P3 candidates should be added only when they are specific, low-noise, and costly to rediscover. Low-priority speculation belongs outside the active session queue.

### Scope-Aware Closeout

If actual work completed only a narrowed subset of the original session, the agent should update the row text first, then mark it `done`, then add follow-on sessions for the remaining concrete work.

### Minimal And Advanced Modes

Use `examples/Dashboard/` for lightweight projects. Use `examples/Dashboard-advanced/` when the project needs optional files such as `Stage_Plans.md`, `Risks.md`, `Exceptions.md`, `Quality_Metrics.md`, `Automation.md`, `External_Artifacts.md`, or `Agent_Logs/README.md`.

## Features

- Codex-native skill layout with `SKILL.md` and `agents/openai.yaml`
- Reference method for Dashboard row semantics, scope narrowing, candidate memory, and end-of-task review
- Optional advanced governance reference for stage plans, validation, closure, and Dashboard bloat control
- Minimal and advanced example Dashboard directories that can be copied into a repository
- No-dependency local validators for skill structure and Dashboard health
- Portable contract authority, optional four-surface Session registry reconciliation, and explicit post-gate DKG sample tooling
- GitHub Actions workflow for validation on push and pull request
- Portability notes for Claude Code, Cursor, Windsurf, Continue, and other IDE agents
- Publishing checklist for public GitHub release

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/buccaneermethodology/dashboard-governance-skill.git
cd dashboard-governance-skill
```

### 2. Install the Codex skill

Copy the installable skill folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R skill/dashboard-governance ~/.codex/skills/dashboard-governance
```

Start a new Codex session so the skill registry is reloaded.

### 3. Add Dashboard templates to a project

From your target repository, copy the minimal example Dashboard folder:

```bash
cp -R /path/to/dashboard-governance-skill/examples/Dashboard ./Dashboard
```

For advanced governed execution, copy the advanced template instead:

```bash
cp -R /path/to/dashboard-governance-skill/examples/Dashboard-advanced ./Dashboard
```

Then edit the rows to match your project. Keep the row semantics in `Dashboard/Methodology.md` and `Dashboard/Rules.md` visible to future agents.

For the advanced registry workflow, also install a project contract:

```bash
mkdir -p kb/data/strategy
cp /path/to/dashboard-governance-skill/examples/contracts/dashboard_governance_contract.json \
  kb/data/strategy/dashboard_governance_contract.json
python3 Dashboard/tools/session_registry.py reconcile --repo . --check
python3 Dashboard/tools/session_registry.py validate --repo .
python3 Dashboard/tools/generate_dashboard_kg.py --repo . --output Dashboard/dashboard-kg.json
```

The selected contract is the lifecycle Status authority. Reconcile may rebuild only the derived index and manifest counts; DKG generation is a separate post-gate operation, and its output is never Dashboard authority.

### 4. Ask Codex to use the skill

Example end-of-task prompt:

```text
Use $dashboard-governance after finishing this task. Update Big Ideas, Sessions, and Decisions, decide whether any candidate next sessions emerged, and recommend the next row with rationale.
```

Example bootstrap prompt:

```text
Use $dashboard-governance to create a Dashboard for this repository and seed initial Big Ideas, Sessions, and Decisions.
```

## Example

A human finishes a project task and asks the agent to update the Dashboard. The agent should read repository rules, inspect the current Dashboard, and make bounded updates.

```text
Task completed: added the first provider-neutral runner skeleton and fake-provider tests.
Use $dashboard-governance to update the Dashboard, identify candidate next sessions, and recommend the next row with rationale.
```

Expected Dashboard effects:

| Area | Expected update |
| --- | --- |
| Sessions | Mark the active runner session `done` if exit criteria are met. |
| Big Ideas | Update the parent track's next step without closing it prematurely. |
| Decisions | Add or resolve provider, dependency, or rollout choices if they affect later sessions. |
| Emergent sessions | Add concrete P0/P1 candidates, and P2/P3 only when they preserve specific high-cost memory. |
| Scope narrowing | If the task completed only a subset, narrow the row before marking it `done` and add follow-on sessions. |
| Final response | State whether Dashboard and stable project truth needed updates, then recommend the next row with why-now and why-this detail. |

A minimal Session row looks like this:

```markdown
| ID | Topic | Scope | Purpose | Track | Priority | Status | Depends On | Deliverable | Exit Criteria | Next Step | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S-001 | Bootstrap Dashboard | Create initial Dashboard files and rules. | Give the project an execution-state layer. | BI-001 | P1 | `todo` | none | Initial Dashboard files | Files exist and row semantics are documented. | Start when approved. | Replace with project-specific work. |
```

## Repository Layout

```text
skill/dashboard-governance/
  SKILL.md
  agents/openai.yaml
  references/dashboard-method.md
  references/advanced-governance.md
examples/Dashboard/
  README.md
  Methodology.md
  Rules.md
  Big_Ideas.md
  Sessions.md
  Decisions.md
examples/Dashboard-advanced/
  README.md
  Methodology.md
  Rules.md
  Big_Ideas.md
  Sessions.md
  Decisions.md
  Stage_Plans.md
  Risks.md
  Exceptions.md
  Quality_Metrics.md
  Automation.md
  External_Artifacts.md
  Agent_Logs/README.md
  Session_Index.md
  Archives/Sessions/
  tools/session_registry.py
  tools/generate_dashboard_kg.py
examples/contracts/dashboard_governance_contract.json
docs/
  PORTABILITY.md
  PUBLISHING.md
scripts/
  validate_skill.py
  validate_dashboard.py
.github/
  workflows/validate.yml
  ISSUE_TEMPLATE/
  pull_request_template.md
```

## Validate

Run the bundled no-dependency validator:

```bash
python3 scripts/validate_skill.py skill/dashboard-governance
python3 scripts/validate_dashboard.py examples/Dashboard --contract examples/contracts/dashboard_governance_contract.json
python3 scripts/validate_dashboard.py examples/Dashboard-advanced --contract examples/contracts/dashboard_governance_contract.json --require-registry
python3 scripts/test_registry.py
```

If you have the official Codex skill validator available, run it too:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill/dashboard-governance
```

## Portability

The method is portable because it is stored as plain Markdown plus durable repository files. Codex can use the installable skill folder directly. Other IDE agents can use the same content as workspace rules, project memory, or a reusable prompt.

See [docs/PORTABILITY.md](docs/PORTABILITY.md) for adaptation notes.

## Relationship To Dashboard Synthesis

This repository focuses on governance after a Dashboard exists: maintaining status, decisions, next steps, and end-of-task review discipline during ongoing work.

For a complementary skill that synthesizes an initial Exploration Dashboard from unstructured material, see [Exploration Dashboard Synthesizer](https://github.com/buccaneermethodology/ExplorationDashboardSynthesizer).

## Related Articles

- [把探索过程交给 Dashboard：从 RSEM 到 dashboard-governance-skill](docs/articles/rsem-dashboard-governance-skill.md)

## References

- [Exploration Dashboard Synthesizer](https://github.com/buccaneermethodology/ExplorationDashboardSynthesizer)
- [BM Dashboard：一种用于管理高度探索性认知过程的结构化框架](https://github.com/buccaneermethodology/ExplorationDashboardSynthesizer/blob/main/docs/bm-dashboard.md)
- [Codex skill folder](skill/dashboard-governance/SKILL.md)
- [Dashboard method reference](skill/dashboard-governance/references/dashboard-method.md)
- [Advanced governance reference](skill/dashboard-governance/references/advanced-governance.md)
- [Minimal Dashboard example template](examples/Dashboard/README.md)
- [Advanced Dashboard example template](examples/Dashboard-advanced/README.md)

See [docs/PUBLISHING.md](docs/PUBLISHING.md) for the release checklist.

## Contributing

Issues and pull requests are welcome. Useful contributions include:

- clearer Dashboard row semantics
- additional example Dashboard templates
- portability notes for more IDE agents
- validator improvements
- examples of end-of-task review prompts

Please keep the installable skill concise. Human-facing repository docs belong outside `skill/dashboard-governance/`.

## License

MIT. See [LICENSE](LICENSE).

## Maintenance

Maintainer: Tai Xiaomei buccaneermethodology@gmail.com GitHub: @buccaneermethodology

For maintainer release steps, see [docs/PUBLISHING.md](docs/PUBLISHING.md).
