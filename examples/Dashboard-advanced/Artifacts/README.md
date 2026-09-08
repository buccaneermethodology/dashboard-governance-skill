# Artifact Batches

This directory groups durable outputs by the Goal or Stage Plan that owns them.

## Layout

```text
Artifacts/
  README.md
  Stage-Plan-SP-001/
    README.md
    validation/
      verdict.md
```

Use one batch directory per owner:

- `Goal-<GOAL-ID>/` for work spanning the whole Goal.
- `Stage-Plan-<STAGE-PLAN-ID>/` for work scoped to one Stage Plan.

The batch `README.md` records the exact owner ID, scope, provenance, and contained files. Optional type directories belong inside the batch. Do not put loose artifact files in this root, duplicate one artifact across parent and child batches, or use symlinks. This layout improves findability; it does not make an artifact canonical truth, independently validated, approved, or released.
