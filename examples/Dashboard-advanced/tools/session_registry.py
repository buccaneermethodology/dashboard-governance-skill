#!/usr/bin/env python3
"""Portable current/index/archive/manifest Session registry gate."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
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


def dashboard_for(repo: Path) -> Path:
    return repo if (repo / "Sessions.md").is_file() else repo / "Dashboard"


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
        index_path.write_text(expected_index, encoding="utf-8")
        manifest_path.write_text(expected_manifest, encoding="utf-8")
        print(f"APPLIED: {', '.join(drift) if drift else 'no drift'}")
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
    parser.add_argument("command", choices=["reconcile", "validate"])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--contract")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            if args.check or args.apply:
                parser.error("validate does not accept --check/--apply")
            return validate(Path(args.repo).resolve(), args.contract)
        if not args.check and not args.apply:
            parser.error("reconcile requires --check or --apply")
        return reconcile(Path(args.repo).resolve(), args.contract, args.apply)
    except (RegistryError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
