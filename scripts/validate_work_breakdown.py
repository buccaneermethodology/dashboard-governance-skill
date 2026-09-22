#!/usr/bin/env python3
"""Validate the portable Session -> Milestone and Lane work-breakdown contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from validate_dashboard import load_contract, validate_dashboard

VERSION = "dashboard_work_breakdown_v2"
STATES = {
    "session": {"planned", "active", "blocked", "terminal_candidate", "terminal"},
    "milestone": {"planned", "ready", "active", "blocked", "satisfied"},
    "lane": {"planned", "ready", "running", "blocked", "output_candidate", "validated"},
}
NAME_HINT = re.compile(r"(?:^|[-_])(phase|stage|step)[-_]?\d*(?:$|[-_])", re.IGNORECASE)
PRECONFIGURED_BOUNDARY = (
    Path(__file__).resolve().parents[1]
    / "skill/dashboard-governance/.managed-authority/trusted-authority-boundary.json"
)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unreadable work breakdown: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("work breakdown root must be an object")
    return value


def migration_result(reason: str) -> tuple[list[str], list[str]]:
    return ["MISSING_WORK_BREAKDOWN_V2: advanced profile is not v2 compliant"], [
        "MIGRATION_REQUIRED: " + reason
        + "; add explicit sessions, milestones, lanes, parent edges, and aggregation states"
    ]


def resolve_bound_file(source_dir: Path | None, locator: Any, label: str) -> tuple[Path | None, list[str]]:
    if source_dir is None or not isinstance(locator, dict):
        return None, [f"MISSING_{label}: path+sha256 locator is required"]
    relative = locator.get("path")
    expected = locator.get("sha256")
    if not isinstance(relative, str) or not relative or not isinstance(expected, str) or len(expected) != 64:
        return None, [f"INVALID_{label}: locator needs path and sha256"]
    path = (source_dir / relative).resolve()
    if not path.is_file() or path.is_symlink():
        return None, [f"INVALID_{label}: bound file is missing or not regular"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        return None, [f"INVALID_{label}: sha256 mismatch"]
    return path, []


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_trusted_root(
    boundary_path: Path,
    data: dict[str, Any],
    sessions: dict[str, dict[str, Any]],
) -> list[str]:
    if not boundary_path.is_file() or boundary_path.is_symlink():
        if "delivery_authority" in data:
            return ["UNTRUSTED_PARALLEL_AUTHORITY_ROOT: payload-selected authority is not a trust anchor"]
        return ["AUTHORITY_PROVENANCE_NOT_BOUND: preconfigured authority boundary is unavailable"]
    try:
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AUTHORITY_PROVENANCE_NOT_BOUND: unreadable preconfigured boundary: {exc}"]
    if boundary.get("schema_version") != "trusted_authority_boundary_v1":
        return ["AUTHORITY_PROVENANCE_NOT_BOUND: invalid preconfigured boundary schema"]
    root_ref = boundary.get("root", {})
    root_locator = root_ref.get("path")
    expected_root_sha256 = root_ref.get("sha256")
    if not isinstance(root_locator, str) or not isinstance(expected_root_sha256, str):
        return ["AUTHORITY_PROVENANCE_NOT_BOUND: boundary does not pin root path and digest"]
    root_path = Path(root_locator)
    if not root_path.is_absolute():
        root_path = (boundary_path.parent / root_path).resolve()
    if not root_path.is_file() or root_path.is_symlink():
        return ["AUTHORITY_PROVENANCE_NOT_BOUND: trusted root is missing or not regular"]
    if hashlib.sha256(root_path.read_bytes()).hexdigest() != expected_root_sha256:
        return ["AUTHORITY_DIGEST_MISMATCH: configured root digest differs"]
    try:
        root = json.loads(root_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AUTHORITY_PROVENANCE_NOT_BOUND: unreadable root: {exc}"]
    errors: list[str] = []
    if root.get("schema_version") != "evidence_authority_root_v2":
        errors.append("AUTHORITY_PROVENANCE_NOT_BOUND: wrong root schema")
        return errors
    if data.get("authority_root_id") != root.get("authority_root_id") or data.get("authority_root_revision") != root.get("root_revision"):
        errors.append("UNTRUSTED_PARALLEL_AUTHORITY_ROOT: submitted root identity/revision is not configured root")
    issuer = root.get("issuer", {})
    scope = root.get("scope", {})
    if issuer.get("issuer_role") != "goal_or_stage_plan_owner":
        errors.append("AUTHORITY_ISSUER_ROLE_FORBIDDEN: delivery root issuer is not an owner")
    if "session" not in scope.get("subject_kinds", []) or scope.get("parent_identity") != data.get("parent_delivery_id"):
        errors.append("AUTHORITY_SUBJECT_MISMATCH: scope does not authorize this parent/session kind")
    provenance, provenance_errors = resolve_bound_file(root_path.parent, {
        "path": issuer.get("provenance_ref"), "sha256": issuer.get("provenance_sha256")
    }, "ISSUER_PROVENANCE")
    errors.extend("AUTHORITY_PROVENANCE_NOT_BOUND: " + item for item in provenance_errors)
    source = root.get("source", {})
    source_path, source_errors = resolve_bound_file(root_path.parent, {
        "path": source.get("locator"), "sha256": source.get("sha256")
    }, "AUTHORITY_SOURCE")
    errors.extend("AUTHORITY_DIGEST_MISMATCH: " + item for item in source_errors)
    if source.get("revision") != scope.get("source_revision") or data.get("source_revision") != source.get("revision"):
        errors.append("AUTHORITY_SUBJECT_MISMATCH: source revision differs")
    issued = parse_time(root.get("issued_at"))
    effective = parse_time(root.get("effective_before"))
    created = parse_time(data.get("subject_created_at"))
    if issued is None or effective is None or created is None or not (issued <= effective < created):
        errors.append("AUTHORITY_ISSUED_TOO_LATE: root timing does not precede subject")
    subjects = root.get("subjects")
    if not isinstance(subjects, list):
        errors.append("AUTHORITY_PROVENANCE_NOT_BOUND: subjects inventory is invalid")
        subjects = []
    signed: dict[str, dict[str, Any]] = {}
    for subject in subjects:
        if not isinstance(subject, dict) or subject.get("subject_kind") != "session":
            errors.append("AUTHORITY_SUBJECT_MISMATCH: invalid subject entry")
            continue
        signed[str(subject.get("subject_id"))] = subject
    if set(signed) != set(sessions):
        errors.append("AUTHORITY_SUBJECT_MISMATCH: actual Session set differs from trusted root")
    for session_id, session in sessions.items():
        subject = signed.get(session_id)
        if subject and (
            subject.get("parent_identity") != session.get("parent_delivery_id")
            or subject.get("revision") != data.get("source_revision")
            or subject.get("digest") != canonical_digest(session)
        ):
            errors.append(f"AUTHORITY_SUBJECT_MISMATCH: Session {session_id} binding differs")
    return errors


def validate(
    data: dict[str, Any],
    source_dir: Path | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    profile = data.get("profile", "minimal")
    version = data.get("schema_version")
    if profile == "minimal":
        evidence = data.get("minimal_evidence")
        if source_dir is None or not isinstance(evidence, dict):
            return ["INVALID_MINIMAL_EVIDENCE: real dashboard_dir and contract paths are required"], warnings
        dashboard_ref = evidence.get("dashboard_dir")
        contract_ref = evidence.get("contract")
        if not isinstance(dashboard_ref, str) or not isinstance(contract_ref, str):
            return ["INVALID_MINIMAL_EVIDENCE: dashboard_dir and contract must be paths"], warnings
        dashboard = (source_dir / dashboard_ref).resolve()
        contract_path = (source_dir / contract_ref).resolve()
        try:
            contract = load_contract(contract_path)
        except ValueError as exc:
            return [f"INVALID_MINIMAL_EVIDENCE: {exc}"], warnings
        found_errors, found_warnings = validate_dashboard(dashboard, contract, 240, False)
        errors.extend(f"INVALID_MINIMAL_SURFACE: {error}" for error in found_errors)
        warnings.extend(found_warnings)
        return errors, warnings
    if profile != "advanced":
        return [f"INVALID_PROFILE: expected minimal or advanced, got {profile!r}"], warnings
    if version != VERSION:
        return migration_result(f"found schema_version {version!r}")

    collections: dict[str, list[dict[str, Any]]] = {}
    for plural in ("sessions", "milestones", "lanes"):
        value = data.get(plural)
        if not isinstance(value, list) or not value:
            errors.append(f"MISSING_{plural.upper()}: advanced v2 requires a non-empty {plural} array")
            collections[plural] = []
        elif not all(isinstance(item, dict) for item in value):
            errors.append(f"INVALID_{plural.upper()}: every entry must be an object")
            collections[plural] = []
        else:
            collections[plural] = value

    by_kind: dict[str, dict[str, dict[str, Any]]] = {}
    for singular, plural in (("session", "sessions"), ("milestone", "milestones"), ("lane", "lanes")):
        indexed: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(collections[plural], 1):
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id.strip():
                errors.append(f"INVALID_ID: {singular} entry {index} needs a non-empty id")
                continue
            if item_id in indexed:
                errors.append(f"DUPLICATE_ID: {singular} {item_id}")
            indexed[item_id] = item
            state = item.get("status")
            if state not in STATES[singular]:
                errors.append(f"INVALID_STATE: {singular} {item_id} has {state!r}")
            if NAME_HINT.search(item_id):
                warnings.append(
                    f"NAME_HEURISTIC_ONLY: {singular} {item_id} resembles a phase/stage name; "
                    "kind is determined by explicit structure"
                )
        by_kind[singular] = indexed

    overlapping = (
        set(by_kind["session"]) & set(by_kind["milestone"])
        | set(by_kind["session"]) & set(by_kind["lane"])
        | set(by_kind["milestone"]) & set(by_kind["lane"])
    )
    for item_id in sorted(overlapping):
        errors.append(f"WORK_UNIT_KIND_COLLAPSE: {item_id} appears in more than one kind")

    milestone_parents: dict[str, str] = {}
    for milestone_id, milestone in by_kind["milestone"].items():
        parent = milestone.get("session_id")
        if parent not in by_kind["session"]:
            errors.append(f"UNKNOWN_SESSION_PARENT: milestone {milestone_id} -> {parent!r}")
        milestone_parents[milestone_id] = parent
        sequence = milestone.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"INVALID_SEQUENCE: milestone {milestone_id} needs a positive integer")

    for session_id, session in by_kind["session"].items():
        completion_rule = session.get("completion_rule")
        if not isinstance(completion_rule, str) or not completion_rule.strip():
            errors.append(f"MISSING_COMPLETION_RULE: session {session_id}")
        completion_rule_id = session.get("completion_rule_id")
        if not isinstance(completion_rule_id, str) or not completion_rule_id.strip():
            errors.append(f"MISSING_COMPLETION_RULE_ID: session {session_id}")
        parent_delivery_id = session.get("parent_delivery_id")
        if not isinstance(parent_delivery_id, str) or not parent_delivery_id.strip():
            errors.append(f"MISSING_PARENT_DELIVERY_ID: session {session_id}")
        milestone_ids = session.get("milestone_ids")
        lane_ids = session.get("required_lane_ids")
        if not isinstance(milestone_ids, list) or not milestone_ids:
            errors.append(f"MISSING_MILESTONE_EDGES: session {session_id}")
            milestone_ids = []
        if not isinstance(lane_ids, list) or not lane_ids:
            errors.append(f"MISSING_LANE_EDGES: session {session_id}")
            lane_ids = []
        actual_children = {mid for mid, parent in milestone_parents.items() if parent == session_id}
        if set(milestone_ids) != actual_children:
            errors.append(f"MILESTONE_EDGE_MISMATCH: session {session_id}")
        unknown_lanes = sorted(set(lane_ids) - set(by_kind["lane"]))
        if unknown_lanes:
            errors.append(f"UNKNOWN_REQUIRED_LANE: session {session_id}: {', '.join(unknown_lanes)}")
        if session.get("status") == "terminal":
            unsatisfied = [mid for mid in milestone_ids if by_kind["milestone"].get(mid, {}).get("status") != "satisfied"]
            unvalidated = [lid for lid in lane_ids if by_kind["lane"].get(lid, {}).get("status") != "validated"]
            if unsatisfied or unvalidated:
                errors.append(f"PREMATURE_SESSION_TERMINAL: session {session_id}")

    groups: dict[str, list[str]] = {}
    rules: dict[str, list[str]] = {}
    for session_id, session in by_kind["session"].items():
        group = session.get("completion_rule_id")
        if isinstance(group, str) and group:
            groups.setdefault(group, []).append(session_id)
        rule = session.get("completion_rule")
        if isinstance(rule, str) and rule.strip():
            normalized_rule = " ".join(rule.casefold().split())
            rules.setdefault(normalized_rule, []).append(session_id)
    for group, session_ids in groups.items():
        if len(session_ids) > 1:
            errors.append(
                "SHARED_COMPLETION_RULE_REQUIRES_SINGLE_SESSION: "
                f"completion rule {group!r} is split across {', '.join(sorted(session_ids))}"
            )
    for normalized_rule, session_ids in rules.items():
        if len(session_ids) > 1 and not any(set(session_ids) == set(group_sessions) for group_sessions in groups.values()):
            errors.append(
                "SHARED_COMPLETION_RULE_REQUIRES_SINGLE_SESSION: "
                f"equivalent completion rule {normalized_rule!r} is split across {', '.join(sorted(session_ids))}"
            )

    errors.extend(validate_trusted_root(PRECONFIGURED_BOUNDARY, data, by_kind["session"]))
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Session, Milestone, and Lane work breakdown.")
    parser.add_argument("work_breakdown", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.work_breakdown)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    errors, warnings = validate(data, args.work_breakdown.resolve().parent)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    if data.get("profile", "minimal") == "minimal":
        print("OK: minimal profile accepted; advanced v2 compliance not claimed")
    else:
        print("OK: advanced work breakdown conforms to dashboard_work_breakdown_v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
