#!/usr/bin/env python3
"""Portable current/index/archive/manifest Session registry gate."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

HEADERS = [
    "ID", "Topic", "Scope", "Purpose", "Track", "Priority", "Status",
    "Depends On", "Deliverable", "Exit Criteria", "Next Step", "Notes",
]


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Record:
    identifier: str
    topic: str
    status: str
    location: str


@dataclass(frozen=True)
class ProjectionTarget:
    path: Path
    expected: bytes


RECOVERY_SCHEMA = "dashboard_session_registry_recovery_v1"
RECOVERY_ROOT = ".session-registry-recovery"
MANAGED_TARGETS = {
    "Session_Index.md",
    "Archives/Sessions/archive_manifest.json",
}


def dashboard_for(repo: Path) -> Path:
    return repo if (repo / "Sessions.md").is_file() else repo / "Dashboard"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def stage_bytes(target: Path, payload: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.registry-", suffix=".tmp", dir=target.parent)
    staged = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return staged
    except BaseException:
        staged.unlink(missing_ok=True)
        raise


def replace_path(source: Path, target: Path) -> None:
    os.replace(source, target)


def write_json_durable(path: Path, value: dict[str, object]) -> None:
    payload = (json.dumps(value, indent=2) + "\n").encode("utf-8")
    staged = stage_bytes(path, payload)
    try:
        replace_path(staged, path)
        fsync_directory(path.parent)
    finally:
        staged.unlink(missing_ok=True)


def remove_transaction(transaction: Path) -> None:
    root = transaction.parent
    shutil.rmtree(transaction)
    try:
        fsync_directory(root)
    except OSError:
        if transaction.exists():
            raise
    try:
        root.rmdir()
    except OSError:
        return
    try:
        fsync_directory(root.parent)
    except OSError:
        if root.exists():
            raise


def recovery_root_for(dashboard: Path) -> Path:
    return dashboard / RECOVERY_ROOT


def pending_transactions(dashboard: Path) -> list[Path]:
    root = recovery_root_for(dashboard)
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        raise RegistryError(f"recovery root must be a regular non-symlink directory: {root}")
    entries = sorted(root.iterdir(), key=lambda item: item.name)
    invalid = [entry for entry in entries if entry.is_symlink() or not entry.is_dir()]
    if invalid:
        raise RegistryError(f"invalid recovery entry: {invalid[0]}")
    return entries


def ensure_no_pending_recovery(dashboard: Path) -> None:
    pending = pending_transactions(dashboard)
    if pending:
        identifiers = ", ".join(path.name for path in pending)
        raise RegistryError(
            f"RECOVERY_REQUIRED: pending transaction(s): {identifiers}; "
            f"run recover --repo {shlex.quote(str(dashboard))} --transaction TRANSACTION_ID"
        )


def split_row(line: str) -> list[str]:
    return [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def parse_records(path: Path, location: str, allowed: set[str]) -> list[Record]:
    if not path.is_file() or path.is_symlink():
        raise RegistryError(f"registry source must be a regular file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    records: list[Record] = []
    for line_no, line in enumerate(lines, 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if cells == HEADERS:
            if header is not None:
                raise RegistryError(f"{path}:{line_no}: duplicate registry header")
            header = cells
            continue
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if header is None:
            continue
        if len(cells) != len(HEADERS):
            raise RegistryError(f"{path}:{line_no}: malformed registry row")
        row = dict(zip(HEADERS, cells))
        identifier = row["ID"].strip("`")
        status = row["Status"].strip("`").lower()
        if not re.fullmatch(r"[A-Z]+-\d{3,}", identifier):
            raise RegistryError(f"{path}:{line_no}: malformed ID `{identifier}`")
        if status not in allowed:
            raise RegistryError(f"{path}:{line_no}: unknown Status `{status}`")
        if not row["Topic"] or not row["Scope"] or not row["Purpose"]:
            raise RegistryError(f"{path}:{line_no}: Topic/Scope/Purpose must be non-empty")
        records.append(Record(identifier, row["Topic"], status, location))
    if header is None:
        raise RegistryError(f"{path}: registry header not found")
    return records


def discover_contract(repo: Path, dashboard: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    candidate = repo / "kb/data/strategy/dashboard_governance_contract.json"
    if candidate.is_file():
        return candidate
    bundled = dashboard.parent / "contracts/dashboard_governance_contract.json"
    if bundled.is_file():
        return bundled
    raise RegistryError("no project contract found; pass --contract or install kb/data/strategy/dashboard_governance_contract.json")


def load_statuses(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        values = data["lifecycle_status"]["allowed"]
        forbidden = data["forbidden_status_collapses"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RegistryError(f"invalid contract: {path}: {exc}") from exc
    if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
        raise RegistryError("contract lifecycle_status.allowed must be a non-empty string list")
    if not isinstance(forbidden, list) or not all(isinstance(pattern, str) for pattern in forbidden):
        raise RegistryError("contract forbidden_status_collapses must be a string list")
    normalized = {value.lower() for value in values}
    conflicts = sorted({
        value
        for value in normalized
        if any(fnmatch.fnmatchcase(value, pattern.lower()) for pattern in forbidden)
    })
    if conflicts:
        raise RegistryError(
            "contract lifecycle_status.allowed intersects forbidden_status_collapses: "
            + ", ".join(conflicts)
        )
    return normalized


def load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise RegistryError(f"manifest must be a regular file: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"invalid manifest: {exc}") from exc
    managed = manifest.get("managed_archives")
    if not isinstance(managed, list) or not all(isinstance(item, str) for item in managed):
        raise RegistryError("manifest managed_archives must be a string list")
    return manifest


def collect(repo: Path, contract: str | None) -> tuple[Path, list[Record], dict[str, object]]:
    dashboard = dashboard_for(repo)
    archive_root = dashboard / "Archives/Sessions"
    index_path = dashboard / "Session_Index.md"
    manifest_path = archive_root / "archive_manifest.json"
    if not dashboard.is_dir() or dashboard.is_symlink():
        raise RegistryError(f"Dashboard must be a regular non-symlink directory: {dashboard}")
    ensure_no_pending_recovery(dashboard)
    if not archive_root.is_dir() or archive_root.is_symlink():
        raise RegistryError(f"archive root must be a regular non-symlink directory: {archive_root}")
    if not index_path.is_file() or index_path.is_symlink():
        raise RegistryError(f"derived index must be a regular non-symlink file: {index_path}")
    manifest = load_manifest(manifest_path)
    managed = set(manifest["managed_archives"])
    actual = {path.name for path in archive_root.glob("*.md")}
    if managed != actual:
        raise RegistryError(f"unknown archive surface or stale manifest: managed={sorted(managed)} actual={sorted(actual)}")
    allowed = load_statuses(discover_contract(repo, dashboard, contract))
    records = parse_records(dashboard / "Sessions.md", "Sessions.md", allowed)
    for filename in sorted(managed):
        records.extend(parse_records(archive_root / filename, f"Archives/Sessions/{filename}", allowed))
    seen: set[str] = set()
    for record in records:
        if record.identifier in seen:
            raise RegistryError(f"duplicate Session ID: {record.identifier}")
        seen.add(record.identifier)
    return dashboard, records, manifest


def render_index(records: list[Record]) -> str:
    lines = [
        "# Session Index", "",
        "This file is a derived locator. `Sessions.md` and `Archives/Sessions/*.md` remain authoritative execution-memory records.", "",
        "| ID | Status | Location | Topic |", "| --- | --- | --- | --- |",
    ]
    for record in sorted(records, key=lambda item: item.identifier):
        label = "current" if record.location == "Sessions.md" else "archive"
        lines.append(f"| {record.identifier} | `{record.status}` | [{label}]({record.location}) | {record.topic} |")
    return "\n".join(lines) + "\n"


def render_manifest(manifest: dict[str, object], records: list[Record]) -> str:
    managed = list(manifest["managed_archives"])
    archive_files = {
        filename: sum(record.location == f"Archives/Sessions/{filename}" for record in records)
        for filename in managed
    }
    current_count = sum(record.location == "Sessions.md" for record in records)
    result = {
        "schema_version": "dashboard_session_archive_manifest_v1",
        "managed_archives": managed,
        "archive_files": archive_files,
        "current_count": current_count,
        "archive_count": len(records) - current_count,
        "record_count": len(records),
        "claim_ceiling": "dashboard_execution_memory_projection_only",
    }
    return json.dumps(result, indent=2) + "\n"


def target_relative(dashboard: Path, path: Path) -> str:
    return path.relative_to(dashboard).as_posix()


def journal_for(
    dashboard: Path,
    transaction_id: str,
    targets: list[ProjectionTarget],
    backups: list[Path],
    originals: list[bytes],
) -> dict[str, object]:
    return {
        "schema_version": RECOVERY_SCHEMA,
        "transaction_id": transaction_id,
        "state": "prepared",
        "dashboard": ".",
        "targets": [
            {
                "path": target_relative(dashboard, target.path),
                "backup": backup.relative_to(backup.parents[1]).as_posix(),
                "before_sha256": sha256_bytes(original),
                "expected_sha256": sha256_bytes(target.expected),
            }
            for target, backup, original in zip(targets, backups, originals)
        ],
        "write_performed": False,
        "changed_paths": [],
    }


def actual_changed_paths(
    dashboard: Path,
    targets: list[ProjectionTarget],
    originals: list[bytes],
) -> list[str]:
    changed: list[str] = []
    for target, original in zip(targets, originals):
        try:
            current = target.path.read_bytes()
        except OSError:
            current = None
        if current != original:
            changed.append(target_relative(dashboard, target.path))
    return changed


def restore_target(target: Path, backup: Path) -> None:
    staged = stage_bytes(target, backup.read_bytes())
    try:
        replace_path(staged, target)
        fsync_directory(target.parent)
    finally:
        staged.unlink(missing_ok=True)


def apply_targets(dashboard: Path, targets: list[ProjectionTarget]) -> None:
    if not targets:
        print("APPLIED: no drift; write_performed=false final_change=false")
        return

    originals = [target.path.read_bytes() for target in targets]
    transaction_id = uuid.uuid4().hex
    recovery_root = recovery_root_for(dashboard)
    transaction = recovery_root / transaction_id
    backup_root = transaction / "backups"
    staged_targets: list[Path] = []
    backups: list[Path] = []
    write_performed = False
    journal_path = transaction / "journal.json"

    recovery_root.mkdir(mode=0o700, exist_ok=True)
    if recovery_root.is_symlink() or not recovery_root.is_dir():
        raise RegistryError(f"recovery root must be a regular non-symlink directory: {recovery_root}")
    transaction.mkdir(mode=0o700)
    backup_root.mkdir(mode=0o700)
    try:
        for index, original in enumerate(originals):
            backup = backup_root / f"{index:03d}.bin"
            backup_stage = stage_bytes(backup, original)
            try:
                replace_path(backup_stage, backup)
                fsync_directory(backup.parent)
            finally:
                backup_stage.unlink(missing_ok=True)
            backups.append(backup)
        journal = journal_for(dashboard, transaction_id, targets, backups, originals)
        write_json_durable(journal_path, journal)
        for target in targets:
            staged_targets.append(stage_bytes(target.path, target.expected))
        journal["state"] = "committing"
        write_json_durable(journal_path, journal)
        for target, staged in zip(targets, staged_targets):
            replace_path(staged, target.path)
            write_performed = True
            fsync_directory(target.path.parent)
        for target in targets:
            if target.path.read_bytes() != target.expected:
                raise OSError(f"post-commit readback mismatch: {target.path}")
        try:
            remove_transaction(transaction)
        except OSError as exc:
            changed = actual_changed_paths(dashboard, targets, originals)
            journal.update({
                "state": "recovery_required",
                "write_performed": write_performed,
                "changed_paths": changed,
                "error": f"transaction cleanup failed after commit: {exc}",
            })
            try:
                write_json_durable(journal_path, journal)
            except OSError:
                pass
            command = recovery_command(dashboard, transaction_id)
            raise RegistryError(
                "RECOVERY_REQUIRED: transaction cleanup failed after commit; "
                f"write_performed={str(write_performed).lower()} final_change={str(bool(changed)).lower()} "
                f"changed_paths={changed} recovery_dir={transaction}; run {command}"
            ) from exc
        names = ", ".join(target_relative(dashboard, target.path) for target in targets)
        print(f"APPLIED: {names}; write_performed=true final_change=true")
        return
    except RegistryError:
        raise
    except OSError as exc:
        rollback_errors: list[str] = []
        for target, backup, original in zip(targets, backups, originals):
            try:
                if target.path.read_bytes() == original:
                    continue
            except OSError:
                pass
            try:
                restore_target(target.path, backup)
                write_performed = True
            except OSError as rollback_exc:
                rollback_errors.append(f"{target_relative(dashboard, target.path)}: {rollback_exc}")
        changed = actual_changed_paths(dashboard, targets, originals)
        cleanup_error: OSError | None = None
        if not rollback_errors and not changed:
            try:
                remove_transaction(transaction)
            except OSError as found:
                cleanup_error = found
        if not rollback_errors and not changed and cleanup_error is None:
            raise RegistryError(
                f"APPLY_FAILED_ROLLED_BACK: {exc}; "
                f"write_performed={str(write_performed).lower()} final_change=false"
            ) from exc
        journal = journal_for(dashboard, transaction_id, targets, backups, originals)
        journal.update({
            "state": "recovery_required",
            "write_performed": write_performed,
            "changed_paths": changed,
            "error": "; ".join(
                [f"apply failed: {exc}"]
                + (["rollback failed: " + " | ".join(rollback_errors)] if rollback_errors else [])
                + ([f"cleanup failed: {cleanup_error}"] if cleanup_error else [])
            ),
        })
        try:
            write_json_durable(journal_path, journal)
        except OSError as journal_exc:
            journal["error"] = f"{journal['error']}; journal update failed: {journal_exc}"
        command = recovery_command(dashboard, transaction_id)
        raise RegistryError(
            f"RECOVERY_REQUIRED: {journal['error']}; "
            f"write_performed={str(write_performed).lower()} final_change={str(bool(changed)).lower()} "
            f"changed_paths={changed} recovery_dir={transaction}; run {command}"
        ) from exc
    finally:
        for staged in staged_targets:
            staged.unlink(missing_ok=True)


def recovery_command(dashboard: Path, transaction_id: str) -> str:
    return (
        "session_registry.py recover --repo "
        f"{shlex.quote(str(dashboard))} --transaction {shlex.quote(transaction_id)}"
    )


def safe_relative_path(base: Path, relative: object, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise RegistryError(f"invalid {label} path in recovery journal")
    candidate = base / relative
    cursor = base
    for part in Path(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise RegistryError(f"symlinked {label} path in recovery journal: {cursor}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise RegistryError(f"escaping {label} path in recovery journal") from exc
    return resolved


def recover(repo: Path, transaction_id: str | None) -> int:
    dashboard = dashboard_for(repo)
    if not dashboard.is_dir() or dashboard.is_symlink():
        raise RegistryError(f"Dashboard must be a regular non-symlink directory: {dashboard}")
    if not transaction_id or not re.fullmatch(r"[A-Za-z0-9._-]+", transaction_id):
        raise RegistryError("recover requires a valid --transaction identifier")
    root = recovery_root_for(dashboard)
    transaction = root / transaction_id
    if root.is_symlink() or not root.is_dir() or transaction.is_symlink() or not transaction.is_dir():
        raise RegistryError(f"recovery transaction not found or unsafe: {transaction}")
    journal_path = transaction / "journal.json"
    if journal_path.is_symlink() or not journal_path.is_file():
        raise RegistryError(f"recovery journal must be a regular file: {journal_path}")
    try:
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"invalid recovery journal: {exc}") from exc
    if not isinstance(journal, dict) or journal.get("schema_version") != RECOVERY_SCHEMA:
        raise RegistryError("invalid recovery journal schema")
    if journal.get("transaction_id") != transaction_id:
        raise RegistryError("recovery journal transaction identity mismatch")
    items = journal.get("targets")
    if not isinstance(items, list) or not items:
        raise RegistryError("recovery journal targets must be a non-empty list")
    restored: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            raise RegistryError("invalid recovery journal target entry")
        relative = item.get("path")
        if relative not in MANAGED_TARGETS:
            raise RegistryError(f"unmanaged recovery target: {relative}")
        target = safe_relative_path(dashboard, relative, "target")
        backup = safe_relative_path(transaction, item.get("backup"), "backup")
        if target.exists() and not target.is_file():
            raise RegistryError(f"recovery target must be a regular file when present: {target}")
        if backup.is_symlink() or not backup.is_file():
            raise RegistryError(f"recovery backup must be a regular file: {backup}")
        payload = backup.read_bytes()
        if sha256_bytes(payload) != item.get("before_sha256"):
            raise RegistryError(f"recovery backup digest mismatch: {backup}")
        restore_target(target, backup)
        if target.is_symlink() or not target.is_file() or target.read_bytes() != payload:
            raise RegistryError(f"recovery readback mismatch: {target}")
        restored.append(str(relative))
    try:
        remove_transaction(transaction)
    except OSError as exc:
        raise RegistryError(f"recovery restored targets but cleanup failed: {exc}") from exc
    print(f"RECOVERED: {', '.join(restored)}; transaction={transaction_id}")
    return 0


def reconcile(repo: Path, contract: str | None, apply: bool) -> int:
    dashboard, records, manifest = collect(repo, contract)
    expected_index = render_index(records)
    expected_manifest = render_manifest(manifest, records)
    index_path = dashboard / "Session_Index.md"
    manifest_path = dashboard / "Archives/Sessions/archive_manifest.json"
    drift = []
    if not index_path.is_file() or index_path.read_text(encoding="utf-8") != expected_index:
        drift.append("Session_Index.md")
    if manifest_path.read_text(encoding="utf-8") != expected_manifest:
        drift.append("archive_manifest.json")
    if drift and not apply:
        print(f"DRIFT: rebuildable derived surfaces: {', '.join(drift)}")
        return 1
    if apply:
        targets = []
        if "Session_Index.md" in drift:
            targets.append(ProjectionTarget(index_path, expected_index.encode("utf-8")))
        if "archive_manifest.json" in drift:
            targets.append(ProjectionTarget(manifest_path, expected_manifest.encode("utf-8")))
        apply_targets(dashboard, targets)
    else:
        print(f"OK: registry reconciled ({len(records)} records)")
    return 0


def validate(repo: Path, contract: str | None) -> int:
    dashboard, records, manifest = collect(repo, contract)
    if (dashboard / "Session_Index.md").read_text(encoding="utf-8") != render_index(records):
        raise RegistryError("Session_Index.md drift")
    if (dashboard / "Archives/Sessions/archive_manifest.json").read_text(encoding="utf-8") != render_manifest(manifest, records):
        raise RegistryError("archive_manifest.json drift")
    print(f"OK: registry valid ({len(records)} unique records)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["reconcile", "validate", "recover"])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--contract")
    parser.add_argument("--transaction")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "recover":
            if args.check or args.apply or args.contract:
                parser.error("recover does not accept --check/--apply/--contract")
            return recover(Path(args.repo).resolve(), args.transaction)
        if args.command == "validate":
            if args.check or args.apply or args.transaction:
                parser.error("validate does not accept --check/--apply/--transaction")
            return validate(Path(args.repo).resolve(), args.contract)
        if args.transaction:
            parser.error("reconcile does not accept --transaction")
        if not args.check and not args.apply:
            parser.error("reconcile requires --check or --apply")
        return reconcile(Path(args.repo).resolve(), args.contract, args.apply)
    except (RegistryError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
