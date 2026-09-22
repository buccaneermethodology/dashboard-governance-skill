#!/usr/bin/env python3
"""Contract tests for dashboard_work_breakdown_v2."""

from __future__ import annotations

import subprocess
import sys
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_work_breakdown.py"
FIXTURES = ROOT / "examples/work-breakdown"


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run(name: str, expected: int, contains: tuple[str, ...], *, trusted: bool = False, mutate_root=None, mutate_data=None, bad_digest: bool = False) -> None:
    extra: list[str] = []
    fixture_path = FIXTURES / name
    temporary = tempfile.TemporaryDirectory(prefix="authority-v2-") if trusted else None
    if temporary:
        temp = Path(temporary.name)
        provenance = temp / "approval.txt"
        source = temp / "goal.txt"
        provenance.write_text("human-approved delivery authority\n", encoding="utf-8")
        source.write_text("frozen goal revision\n", encoding="utf-8")
        data = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        if mutate_data:
            mutate_data(data)
            fixture_path = temp / name
            fixture_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        sessions = data.get("sessions", [])
        authorized_sessions = sessions if expected == 0 else [{
            "id": "delivery-session", "parent_delivery_id": "trusted-delivery",
            "completion_rule_id": "delivery-completion"
        }]
        root = {
            "schema_version": "evidence_authority_root_v2",
            "authority_root_id": "trusted-delivery-root",
            "issuer": {
                "issuer_id": "delivery-owner", "issuer_role": "goal_or_stage_plan_owner",
                "provenance_ref": "approval.txt", "provenance_sha256": hashlib.sha256(provenance.read_bytes()).hexdigest()
            },
            "scope": {"scope_id": "delivery-scope", "subject_kinds": ["session"], "parent_identity": "trusted-delivery", "source_revision": "frozen-goal-r1"},
            "subjects": [{
                "subject_id": session["id"], "subject_kind": "session",
                "parent_identity": session.get("parent_delivery_id", "trusted-delivery"),
                "revision": "frozen-goal-r1", "digest": digest(session)
            } for session in authorized_sessions],
            "source": {"source_kind": "final_goal", "locator": "goal.txt", "revision": "frozen-goal-r1", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
            "root_revision": "2", "issued_at": "2026-01-01T00:00:00Z",
            "effective_before": "2026-01-01T12:00:00Z", "supersedes": None
        }
        if mutate_root:
            mutate_root(root)
        root_path = temp / "root.json"
        root_path.write_text(json.dumps(root, indent=2) + "\n", encoding="utf-8")
        expected_digest = "0" * 64 if bad_digest else hashlib.sha256(root_path.read_bytes()).hexdigest()
        extra = ["--trusted-authority-root", str(root_path), "--expected-root-sha256", expected_digest]
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(fixture_path), *extra],
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stdout + result.stderr
    if result.returncode != expected:
        raise AssertionError(f"{name}: expected {expected}, got {result.returncode}\n{output}")
    for text in contains:
        if text not in output:
            raise AssertionError(f"{name}: missing {text!r}\n{output}")
    if temporary:
        temporary.cleanup()


def run_c002_arbitrary_root_attack() -> None:
    with tempfile.TemporaryDirectory(prefix="c002-attacker-root-") as temporary:
        temp = Path(temporary)
        attacker_root = temp / "root.json"
        attacker_root.write_text('{"schema_version":"evidence_authority_root_v2","authority_root_id":"attacker"}\n', encoding="utf-8")
        data = json.loads((FIXTURES / "invalid-caller-selected-root.json").read_text(encoding="utf-8"))
        data["delivery_authority"] = {
            "path": str(attacker_root),
            "sha256": hashlib.sha256(attacker_root.read_bytes()).hexdigest(),
        }
        payload = temp / "work-breakdown.json"
        payload.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(payload)], text=True, capture_output=True, check=False
        )
        output = result.stdout + result.stderr
        if result.returncode != 1 or "UNTRUSTED_PARALLEL_AUTHORITY_ROOT" not in output:
            raise AssertionError(f"AUTH-V2-C002 did not fail closed\n{output}")


def main() -> int:
    run("minimal-compatible.json", 0, ("minimal profile accepted", "not claimed"))
    run("invalid-minimal-empty.json", 1, ("INVALID_MINIMAL_EVIDENCE",))
    run("invalid-minimal-self-reported-fields.json", 1, ("INVALID_MINIMAL_EVIDENCE",))
    run("advanced-v1-migration-required.json", 1, ("MIGRATION_REQUIRED", "MISSING_WORK_BREAKDOWN_V2"))
    run("invalid-caller-selected-root.json", 1, ("UNTRUSTED_PARALLEL_AUTHORITY_ROOT",))
    run_c002_arbitrary_root_attack()
    run(
        "invalid-shared-completion-split.json", 1,
        ("SHARED_COMPLETION_RULE_REQUIRES_SINGLE_SESSION", "AUTHORITY_PROVENANCE_NOT_BOUND", "NAME_HEURISTIC_ONLY"),
    )
    run(
        "invalid-shared-completion-split-without-group.json",
        1,
        ("AUTHORITY_PROVENANCE_NOT_BOUND",),
    )
    run(
        "valid-one-session-multiple-milestones.json",
        1,
        ("AUTHORITY_PROVENANCE_NOT_BOUND", "NAME_HEURISTIC_ONLY"),
    )
    print("OK: AUTH-V2-C002 GREEN; caller-selected/self-signed roots fail as UNTRUSTED_PARALLEL_AUTHORITY_ROOT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
