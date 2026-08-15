#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CORE_FILES = {"Big_Ideas.md", "Sessions.md", "Decisions.md"}
TSP_FILES = {"Big_Ideas.md", "Sessions.md", "Stage_Plans.md"}
DURABLE_COLUMNS = {
    "Canonical Target", "Deliverable", "Decision", "Rationale", "Validation",
    "Evidence", "Location", "Verification", "Target", "Current",
}


@dataclass
class Table:
    headers: list[str]
    rows: list[dict[str, str]]


def split_md_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [part.strip().replace(r"\|", "|") for part in re.split(r"(?<!\\)\|", stripped)]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def read_table(path: Path) -> Table:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|") or index + 1 >= len(lines):
            continue
        headers = split_md_row(line)
        if not is_separator(split_md_row(lines[index + 1])):
            continue
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2:]:
            if not row_line.lstrip().startswith("|"):
                break
            cells = split_md_row(row_line)
            padded = cells + [""] * (len(headers) - len(cells))
            rows.append(dict(zip(headers, padded[:len(headers)])))
        return Table(headers, rows)
    raise ValueError("no Markdown table found")


def clean(value: str) -> str:
    value = value.strip().strip("`").strip()
    return "" if value.lower() in {"none", "n/a", "na", "tbd", "-"} else value


def default_contract() -> Path:
    return Path(__file__).resolve().parents[1] / "examples/contracts/dashboard_governance_contract.json"


def discover_contract(dashboard: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for root in [dashboard.parent, *dashboard.parents]:
        candidate = root / "kb/data/strategy/dashboard_governance_contract.json"
        if candidate.is_file():
            return candidate
    return default_contract()


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"contract unreadable: {path}: {exc}") from exc
    statuses = data.get("lifecycle_status", {}).get("allowed")
    forbidden = data.get("forbidden_status_collapses")
    columns = data.get("required_columns")
    if not isinstance(statuses, list) or not statuses or not all(isinstance(x, str) for x in statuses):
        raise ValueError("contract lifecycle_status.allowed must be a non-empty string list")
    if not isinstance(forbidden, list) or not all(isinstance(x, str) for x in forbidden):
        raise ValueError("contract forbidden_status_collapses must be a string list")
    conflicts = sorted({
        status
        for status in statuses
        if any(fnmatch.fnmatchcase(status.lower(), pattern.lower()) for pattern in forbidden)
    })
    if conflicts:
        raise ValueError(
            "contract lifecycle_status.allowed intersects forbidden_status_collapses: "
            + ", ".join(conflicts)
        )
    if not isinstance(columns, dict):
        raise ValueError("contract required_columns must be an object")
    return data


def validate_file(path: Path, contract: dict[str, Any], max_notes_chars: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        table = read_table(path)
    except ValueError as exc:
        return [f"{path.name}: {exc}"], warnings
    required = contract["required_columns"].get(path.name, [])
    missing = [column for column in required if column not in table.headers]
    if missing:
        errors.append(f"{path.name}: missing required columns: {', '.join(missing)}")
    allowed = set(contract["lifecycle_status"]["allowed"])
    seen: set[str] = set()
    keys: list[tuple[str, int]] = []
    sortable = True
    for row_number, row in enumerate(table.rows, 1):
        row_id = clean(row.get("ID", ""))
        label = f"{path.name} row {row_number}" + (f" ({row_id})" if row_id else "")
        if "ID" in table.headers:
            if not row_id:
                errors.append(f"{label}: ID is empty")
            elif row_id in seen:
                errors.append(f"{label}: duplicate ID")
            else:
                seen.add(row_id)
            match = re.fullmatch(r"([A-Z]+)-(\d+)", row_id)
            if match:
                keys.append((match.group(1), int(match.group(2))))
            else:
                errors.append(f"{label}: ID should look like PREFIX-001")
                sortable = False
        if "Status" in table.headers:
            status = clean(row.get("Status", "")).lower()
            if not status:
                errors.append(f"{label}: Status is empty")
            elif status not in allowed:
                errors.append(f"{label}: invalid Status `{status}`; contract allows {', '.join(sorted(allowed))}")
            elif status == "done":
                notes = clean(row.get("Notes", ""))
                durable = [clean(row.get(column, "")) for column in DURABLE_COLUMNS if column in table.headers]
                if "Notes" in table.headers and not notes:
                    errors.append(f"{label}: done row needs durable Notes")
                if durable and not any(durable):
                    errors.append(f"{label}: done row needs durable evidence or target")
        if path.name in TSP_FILES:
            for column in ("Topic", "Scope", "Purpose"):
                if column in table.headers and not clean(row.get(column, "")):
                    errors.append(f"{label}: {column} is empty")
        if "Exit Criteria" in table.headers and not clean(row.get("Exit Criteria", "")):
            errors.append(f"{label}: Exit Criteria is empty")
        if "Notes" in table.headers and len(row.get("Notes", "")) > max_notes_chars:
            warnings.append(f"{label}: Notes exceeds {max_notes_chars} chars")
    if sortable and keys and keys != sorted(keys):
        errors.append(f"{path.name}: IDs are not sorted")
    return errors, warnings


def validate_registry_surfaces(dashboard: Path) -> list[str]:
    errors: list[str] = []
    regular_files = [
        dashboard / "Sessions.md",
        dashboard / "Session_Index.md",
        dashboard / "Archives/Sessions/archive_manifest.json",
    ]
    for path in regular_files:
        if not path.is_file() or path.is_symlink():
            errors.append(f"registry surface must be a regular non-symlink file: {path.relative_to(dashboard)}")
    archive_root = dashboard / "Archives/Sessions"
    if not archive_root.is_dir() or archive_root.is_symlink():
        errors.append("registry surface must be a regular non-symlink directory: Archives/Sessions")
        return errors
    archives = list(archive_root.glob("*.md"))
    if not archives:
        errors.append("registry surface is missing: Archives/Sessions/*.md")
    for path in archives:
        if not path.is_file() or path.is_symlink():
            errors.append(f"registry archive must be a regular non-symlink file: {path.relative_to(dashboard)}")
    return errors


def validate_dashboard(dashboard: Path, contract: dict[str, Any], max_notes_chars: int, require_registry: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not dashboard.is_dir():
        return [f"{dashboard}: directory not found"], warnings
    for filename in sorted(CORE_FILES):
        if not (dashboard / filename).is_file():
            errors.append(f"{filename}: required core file is missing")
    for filename in contract["required_columns"]:
        path = dashboard / filename
        if path.is_file():
            found_errors, found_warnings = validate_file(path, contract, max_notes_chars)
            errors.extend(found_errors)
            warnings.extend(found_warnings)
    readme = dashboard / "README.md"
    if not readme.is_file():
        warnings.append("README.md: missing Current Frontier/Snapshot surface")
    elif not re.search(r"Current (?:Frontier|Snapshot)", readme.read_text(encoding="utf-8")):
        warnings.append("README.md: add a short Current Frontier or Current Snapshot section")
    if (dashboard / "Agent_Logs").exists() and not (dashboard / "Agent_Logs/README.md").is_file():
        warnings.append("Agent_Logs/: add README.md with retention and naming conventions")
    if require_registry:
        errors.extend(validate_registry_surfaces(dashboard))
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Dashboard against its status/field contract.")
    parser.add_argument("dashboard_dir")
    parser.add_argument("--contract", help="Explicit Dashboard governance contract JSON")
    parser.add_argument("--require-registry", action="store_true")
    parser.add_argument("--max-notes-chars", type=int, default=240)
    args = parser.parse_args()
    dashboard = Path(args.dashboard_dir).resolve()
    contract_path = discover_contract(dashboard, args.contract)
    try:
        contract = load_contract(contract_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    errors, warnings = validate_dashboard(dashboard, contract, args.max_notes_chars, args.require_registry)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"OK: {dashboard} (contract: {contract_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
