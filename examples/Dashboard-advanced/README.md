# Advanced Dashboard

## Current Frontier

- Frontier: SP-001 defines the current governed batch and its validation gate.
- Next recommendation: finish S-002 because it wires the optional advanced layer before lower-priority memory rows are useful.
- Closure gate: do not mark SP-001 `done` until validation evidence is recorded in `Quality_Metrics.md`.

This Dashboard extends the minimal Big Ideas / Sessions / Decisions model with optional governance indexes.

Use this template when the project needs:

- stage plans for multi-session work
- explicit risk and exception tracking
- quality metrics or validation gates
- automation and external artifact indexes
- Goal/Stage Plan artifact batches under `Artifacts/`
- agent log conventions

Stable project truth still belongs in the KB, docs, ADRs, specs, or contracts. Dashboard rows should point to durable artifacts instead of copying their contents.

## Artifact Batches

Durable outputs are grouped by their owner so the root does not become a flat pile of files:

```text
Artifacts/
  README.md
  Stage-Plan-SP-001/
    README.md
    validation/
      verdict.md
```

Use a Goal batch when the output belongs to the whole Goal; use a Stage Plan batch for narrower work. Keep the exact owner ID, scope, provenance, and artifact list in each batch `README.md`. Run `python3 scripts/validate_artifacts.py examples/Dashboard-advanced/Artifacts` after adding or moving outputs.
