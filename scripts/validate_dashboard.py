#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

STATUS_VALUES = {
    "todo",
    "doing",
    "blocked",
    "decision-needed",
    "done",
    "archived",
    "cancelled",
}

REQUIRED_COLUMNS = {
    "Big_Ideas.md": [
        "ID",
        "Topic",
        "Scope",
        "Purpose",
        "Status",
        "Exit Criteria",
        "Next Step",
        "Notes",
    ],
    "Sessions.md": [
        "ID",
        "Topic",
        "Scope",
        "Purpose",
        "Track",
        "Priority",
        "Status",
        "Depends On",
        "Deliverable",
        "Exit Criteria",
        "Next Step",
        "Notes",
    ],
    "Decisions.md": [
        "ID",
        "Topic",
        "Status",
        "Options",
        "Decision",
        "Rationale",
        "Next Step",
        "Notes",
    ],
    "Stage_Plans.md": [
        "ID",
        "Topic",
        "Scope",
        "Purpose",
        "Status",
        "Tracks",
        "Exit Criteria",
        "Validation",
        "Next Step",
        "Notes",
    ],
    "Risks.md": [
        "ID",
        "Topic",
        "Status",
        "Severity",
        "Trigger",
        "Mitigation",
        "Next Review",
        "Notes",
    ],
    "Exceptions.md": [
        "ID",
        "Topic",
        "Status",
        "Related Row",
        "Exception",
        "Resolution",
        "Next Step",
        "Notes",
    ],
    "Quality_Metrics.md": [
        "ID",
        "Metric",
        "Status",
        "Target",
        "Current",
        "Evidence",
        "Next Step",
        "Notes",
    ],
    "Automation.md": [
        "ID",
        "Topic",
        "Status",
        "Trigger",
        "Action",
        "Owner",
        "Last Run",
        "Next Step",
        "Notes",
    ],
    "External_Artifacts.md": [
        "ID",
        "Topic",
        "Status",
        "Location",
        "Artifact Type",
        "Related Rows",
        "Verification",
        "Notes",
    ],
}

CORE_FILES = {"Big_Ideas.md", "Sessions.md", "Decisions.md"}
TSP_FILES = {"Big_Ideas.md", "Sessions.md", "Stage_Plans.md"}
DURABLE_COLUMNS = {
    "Canonical Target",
    "Deliverable",
    "Decision",
    "Rationale",
    "Validation",
    "Evidence",
    "Location",
    "Verification",
    "Target",
    "Current",
}


@dataclass
class Table:
    headers: list[str]
    rows: list[dict[str, str]]


def split_md_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    parts = re.split(r"(?<!\\)\|", stripped)
    return [part.strip().replace(r"\|", "|") for part in parts]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def read_table(path: Path) -> Table:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        headers = split_md_row(line)
        if index + 1 >= len(lines):
            break
        separator = split_md_row(lines[index + 1])
        if not is_separator(separator):
            continue

        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.lstrip().startswith("|"):
                break
            cells = split_md_row(row_line)
            padded = cells + [""] * (len(headers) - len(cells))
            rows.append(dict(zip(headers, padded[: len(headers)])))
        return Table(headers=headers, rows=rows)
    raise ValueError("no Markdown table found")


def normalize_status(value: str) -> str:
    return value.strip().strip("`").strip().lower()


def clean_cell(value: str) -> str:
    stripped = value.strip()
    if stripped.lower() in {"none", "n/a", "na", "tbd", "-"}:
        return ""
    return stripped


def id_key(value: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"([A-Z]+)-(\d+)", value.strip())
    if not match:
        return None
    return match.group(1), int(match.group(2))


def validate_file(path: Path, max_notes_chars: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    name = path.name

    try:
        table = read_table(path)
    except ValueError as exc:
        return [f"{name}: {exc}"], warnings

    required = REQUIRED_COLUMNS.get(name)
    if required:
        missing = [column for column in required if column not in table.headers]
        if missing:
            errors.append(f"{name}: missing required columns: {', '.join(missing)}")

    seen_ids: set[str] = set()
    keys: list[tuple[str, int]] = []
    sortable = True

    for row_number, row in enumerate(table.rows, start=1):
        row_id = row.get("ID", "").strip()
        label = f"{name} row {row_number}" + (f" ({row_id})" if row_id else "")

        if "ID" in table.headers:
            if not row_id:
                errors.append(f"{label}: ID is empty")
            elif row_id in seen_ids:
                errors.append(f"{label}: duplicate ID")
            else:
                seen_ids.add(row_id)

            key = id_key(row_id)
            if key is None:
                errors.append(f"{label}: ID should look like PREFIX-001")
                sortable = False
            else:
                keys.append(key)

        if "Status" in table.headers:
            status = normalize_status(row.get("Status", ""))
            if not status:
                errors.append(f"{label}: Status is empty")
            elif status not in STATUS_VALUES:
                errors.append(
                    f"{label}: invalid Status `{status}`; expected one of {', '.join(sorted(STATUS_VALUES))}"
                )
            elif status == "done":
                notes = clean_cell(row.get("Notes", ""))
                durable_values = [
                    clean_cell(row.get(column, ""))
                    for column in DURABLE_COLUMNS
                    if column in table.headers
                ]
                if "Notes" in table.headers and not notes:
                    errors.append(f"{label}: done row needs durable Notes")
                if durable_values and not any(durable_values):
                    errors.append(f"{label}: done row needs a durable artifact, decision, evidence, or target")

        if name in TSP_FILES:
            for column in ("Topic", "Scope", "Purpose"):
                if column in table.headers and not clean_cell(row.get(column, "")):
                    errors.append(f"{label}: {column} is empty")

        if "Exit Criteria" in table.headers and not clean_cell(row.get("Exit Criteria", "")):
            errors.append(f"{label}: Exit Criteria is empty")

        if "Notes" in table.headers and len(row.get("Notes", "")) > max_notes_chars:
            warnings.append(
                f"{label}: Notes is longer than {max_notes_chars} chars; consider a closeout report or archive"
            )

    if sortable and keys and keys != sorted(keys):
        errors.append(f"{name}: IDs are not sorted")

    return errors, warnings


def validate_dashboard(dashboard_dir: Path, max_notes_chars: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not dashboard_dir.exists():
        return [f"{dashboard_dir}: directory not found"], warnings
    if not dashboard_dir.is_dir():
        return [f"{dashboard_dir}: not a directory"], warnings

    for filename in sorted(CORE_FILES):
        if not (dashboard_dir / filename).exists():
            errors.append(f"{filename}: required core file is missing")

    for filename in REQUIRED_COLUMNS:
        path = dashboard_dir / filename
        if not path.exists():
            continue
        file_errors, file_warnings = validate_file(path, max_notes_chars)
        errors.extend(file_errors)
        warnings.extend(file_warnings)

    readme = dashboard_dir / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        if "Current Frontier" not in text and "Current Snapshot" not in text:
            warnings.append("README.md: add a short Current Frontier or Current Snapshot section")
    else:
        warnings.append("README.md: missing; add one with a short Current Frontier or Current Snapshot")

    agent_logs = dashboard_dir / "Agent_Logs"
    if agent_logs.exists() and not (agent_logs / "README.md").exists():
        warnings.append("Agent_Logs/: add README.md with log retention and naming conventions")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Dashboard directory.")
    parser.add_argument("dashboard_dir", help="Path to Dashboard directory")
    parser.add_argument(
        "--max-notes-chars",
        type=int,
        default=240,
        help="Warn when a Notes cell is longer than this many characters",
    )
    args = parser.parse_args()

    errors, warnings = validate_dashboard(Path(args.dashboard_dir), args.max_notes_chars)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {args.dashboard_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
