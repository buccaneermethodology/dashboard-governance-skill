# Session registry reconcile recovery contract

This contract governs `examples/Dashboard-advanced/tools/session_registry.py` for G-001. It describes target behavior; the v0.4.0 baseline did not provide transactional recovery.

## Authority and compatibility

`Sessions.md` and managed `Archives/Sessions/*.md` remain authoritative. `Session_Index.md` and `Archives/Sessions/archive_manifest.json` remain derived. `reconcile --check` and `validate` are read-only. `reconcile --apply` may change only derived surfaces and transaction material under `.session-registry-recovery/`. It never moves a Session, creates an archive, or generates DKG.

The existing commands and exit convention remain supported. `recover` is additive. Successful commands return zero; rejected input, failed apply, pending recovery, and failed recovery return nonzero.

## Apply protocol

1. Reject malformed authority, unknown archives, symlinks, missing files, and any pending recovery before staging.
2. Render every target fully in memory and determine the exact drift set. With no drift, report success without rewriting files or changing mtimes.
3. Create a transaction directory under `Dashboard/.session-registry-recovery/<transaction-id>/`. Write a durable journal plus byte-for-byte backups for every drifting target before committing any target.
4. Stage each complete replacement in the target directory, flush it, and replace targets one at a time. A successful result is reported only after every target is replaced and reread as the expected bytes.
5. On a caught staging or commit failure, restore every drifting target to its invocation-time bytes. If restore and cleanup succeed, return nonzero with `APPLY_FAILED_ROLLED_BACK`, `write_performed=<true|false>`, and `final_change=false`.
6. If restore or required cleanup fails, retain the journal and backups, mark the transaction `recovery_required`, and return nonzero with `RECOVERY_REQUIRED`, actual changed paths, the recovery directory, and the exact `recover --repo ... --transaction ...` command. Do not claim that no write occurred.

If the transaction directory has already been deleted, a later parent-directory `fsync` error cannot truthfully produce a recoverable transaction. The command treats the observed cleanup as complete for this caught-error contract and does not emit an impossible `RECOVERY_REQUIRED` instruction. Persistence across a crash at that boundary remains outside the stated guarantee.

Per-file replace is atomic on the supported local-filesystem baseline; the set of files is not instantaneously atomic. This protocol guarantees caught-error recovery, not crash consistency, power-loss recovery, or concurrent-writer serialization.

## Recovery protocol

While any transaction directory exists, `reconcile` and `validate` fail closed before parsing the manifest. This preserves recovery even when the manifest is corrupted.

`recover --repo REPO --transaction ID` reads only the transaction journal and backup files, restores every listed target to the recorded pre-apply bytes, rereads them, and removes the transaction directory after verified success. It never treats the candidate manifest as recovery authority. Missing, malformed, ambiguous, symlinked, or escaping recovery paths fail closed. A failed recovery retains its material for another explicit recovery attempt.

## Diagnostic semantics

- `write_performed` means at least one replacement of a managed target occurred during this invocation, even when rollback later restored the original bytes.
- `final_change` means managed target bytes differ from invocation-time bytes when the command exits.
- `changed_paths` lists the managed targets known to differ when recovery is required.
- `APPLIED` is emitted only after disk reread confirms every expected byte.
- `APPLY_FAILED_ROLLED_BACK` never implies the input drift was repaired; a following `validate` may correctly report the original drift.
- `RECOVERY_REQUIRED` is not a receipt of successful repair.

## Fault and test boundary

Blocking tests use real temporary directories and deterministic in-process fault injection at staging writes, first and second target replacement, backup restoration, journal update, and cleanup. They assert target bytes, mtimes for no-op apply, diagnostics, recovery material, and post-recovery check/validate behavior. Existing invalid-input and DKG-ordering tests remain blocking.

Process termination, machine crash, power loss, and concurrent external writers are explicitly uncovered. Expanding those guarantees requires a separately reviewed contract change.
