#!/usr/bin/env python3
"""Direct positive and fail-closed checks for the portable registry sample."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/Dashboard-advanced"
CONTRACT = ROOT / "examples/contracts/dashboard_governance_contract.json"
VALIDATOR = ROOT / "scripts/validate_dashboard.py"


def run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    if result.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {result.returncode}: {' '.join(args)}\n{result.stdout}{result.stderr}"
        )
    return result


def install_sample(root: Path, name: str) -> tuple[Path, Path, Path]:
    project = root / name
    dashboard = project / "Dashboard"
    shutil.copytree(SOURCE, dashboard)
    return project, dashboard, dashboard / "tools/session_registry.py"


def validate_dashboard(dashboard: Path, contract: Path = CONTRACT, expect: int = 0) -> None:
    run(
        sys.executable, str(VALIDATOR), str(dashboard), "--contract", str(contract),
        "--require-registry", expect=expect,
    )


def load_registry(path: Path) -> ModuleType:
    name = f"session_registry_{path.parent.parent.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load registry module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def invoke(module: ModuleType, *args: str) -> tuple[int, str]:
    output = io.StringIO()
    with patch.object(sys, "argv", ["session_registry.py", *args]), contextlib.redirect_stdout(output):
        result = module.main()
    return result, output.getvalue()


def snapshot(*paths: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in paths}


def assert_snapshot(expected: dict[Path, bytes]) -> None:
    actual = snapshot(*expected)
    if actual != expected:
        changed = [str(path) for path in expected if expected[path] != actual[path]]
        raise AssertionError(f"unexpected file changes: {changed}")


def move_s002_to_archive(dashboard: Path) -> None:
    sessions = dashboard / "Sessions.md"
    archive = dashboard / "Archives/Sessions/Completed.md"
    lines = sessions.read_text(encoding="utf-8").splitlines()
    source = next(line for line in lines if line.startswith("| S-002 |"))
    lines.remove(source)
    sessions.write_text("\n".join(lines) + "\n", encoding="utf-8")
    completed = source.replace("`doing`", "`done`")
    archive.write_text(archive.read_text(encoding="utf-8") + completed + "\n", encoding="utf-8")


def registry_args(project: Path, command: str, *tail: str) -> tuple[str, ...]:
    return (command, "--repo", str(project), "--contract", str(CONTRACT), *tail)


def assert_code_output(result: tuple[int, str], code: int, *fragments: str) -> str:
    actual, output = result
    if actual != code or any(fragment not in output for fragment in fragments):
        raise AssertionError(f"expected code={code} and {fragments}, got code={actual}: {output}")
    return output


def test_transactional_registry(root: Path) -> None:
    # AC-01: a status-only authority edit changes only the index and converges once.
    status_project, status_dashboard, status_registry = install_sample(root, "status-only")
    status_module = load_registry(status_registry)
    status_sessions = status_dashboard / "Sessions.md"
    status_archive = status_dashboard / "Archives/Sessions/Completed.md"
    status_index = status_dashboard / "Session_Index.md"
    status_manifest = status_dashboard / "Archives/Sessions/archive_manifest.json"
    authority_before = snapshot(status_sessions, status_archive)
    status_sessions.write_text(
        status_sessions.read_text(encoding="utf-8").replace("`doing`", "`Done`", 1), encoding="utf-8"
    )
    authority_after_edit = snapshot(status_sessions, status_archive)
    derived_before = snapshot(status_index, status_manifest)
    assert_code_output(invoke(status_module, *registry_args(status_project, "reconcile", "--check")), 1, "Session_Index.md")
    assert_snapshot({**authority_after_edit, **derived_before})
    assert_code_output(
        invoke(status_module, *registry_args(status_project, "reconcile", "--apply")),
        0, "APPLIED: Session_Index.md", "write_performed=true", "final_change=true",
    )
    assert_code_output(invoke(status_module, *registry_args(status_project, "reconcile", "--check")), 0, "OK")
    assert_code_output(invoke(status_module, *registry_args(status_project, "validate")), 0, "OK")
    assert_snapshot(authority_after_edit)
    if authority_before[status_archive] != status_archive.read_bytes():
        raise AssertionError("status-only apply moved or changed an archive")

    # AC-02/06: explicit authority move produces two drifts, converges once, then no-op apply preserves mtimes.
    move_project, move_dashboard, move_registry = install_sample(root, "multi-drift")
    move_module = load_registry(move_registry)
    move_s002_to_archive(move_dashboard)
    move_sessions = move_dashboard / "Sessions.md"
    move_archive = move_dashboard / "Archives/Sessions/Completed.md"
    move_index = move_dashboard / "Session_Index.md"
    move_manifest = move_dashboard / "Archives/Sessions/archive_manifest.json"
    moved_authority = snapshot(move_sessions, move_archive)
    moved_derived = snapshot(move_index, move_manifest)
    assert_code_output(
        invoke(move_module, *registry_args(move_project, "reconcile", "--check")),
        1, "Session_Index.md", "archive_manifest.json",
    )
    assert_snapshot({**moved_authority, **moved_derived})
    assert_code_output(
        invoke(move_module, *registry_args(move_project, "reconcile", "--apply")),
        0, "Session_Index.md", "Archives/Sessions/archive_manifest.json", "write_performed=true",
    )
    assert_code_output(invoke(move_module, *registry_args(move_project, "reconcile", "--check")), 0, "OK")
    assert_code_output(invoke(move_module, *registry_args(move_project, "validate")), 0, "OK")
    assert_snapshot(moved_authority)
    mtimes = {path: path.stat().st_mtime_ns for path in (move_index, move_manifest)}
    assert_code_output(
        invoke(move_module, *registry_args(move_project, "reconcile", "--apply")),
        0, "APPLIED: no drift", "write_performed=false", "final_change=false",
    )
    if mtimes != {path: path.stat().st_mtime_ns for path in mtimes}:
        raise AssertionError("no-op apply rewrote a derived surface")

    # AC-03: every named malformed or unsafe input fails before managed-file commit.
    invalid_cases: list[tuple[str, str]] = []
    for case_name in ("duplicate-id", "malformed-row", "unknown-status", "unknown-archive", "corrupt-manifest"):
        bad_project, bad_dashboard, bad_registry = install_sample(root, case_name)
        bad_module = load_registry(bad_registry)
        bad_sessions = bad_dashboard / "Sessions.md"
        bad_archive = bad_dashboard / "Archives/Sessions/Completed.md"
        bad_manifest = bad_dashboard / "Archives/Sessions/archive_manifest.json"
        if case_name == "duplicate-id":
            duplicate = next(line for line in bad_sessions.read_text(encoding="utf-8").splitlines() if line.startswith("| S-001 |"))
            bad_archive.write_text(bad_archive.read_text(encoding="utf-8") + duplicate + "\n", encoding="utf-8")
            expected_error = "duplicate Session ID"
        elif case_name == "malformed-row":
            bad_sessions.write_text(
                bad_sessions.read_text(encoding="utf-8").replace("| Active frontier row. |", "|"), encoding="utf-8"
            )
            expected_error = "malformed registry row"
        elif case_name == "unknown-status":
            bad_sessions.write_text(
                bad_sessions.read_text(encoding="utf-8").replace("`doing`", "`invented`", 1), encoding="utf-8"
            )
            expected_error = "unknown Status"
        elif case_name == "unknown-archive":
            (bad_dashboard / "Archives/Sessions/Unknown.md").write_text("# Unknown\n", encoding="utf-8")
            expected_error = "unknown archive surface"
        else:
            bad_manifest.write_text("{not json", encoding="utf-8")
            expected_error = "invalid manifest"
        protected = [bad_sessions, bad_archive, bad_dashboard / "Session_Index.md", bad_manifest]
        before = snapshot(*protected)
        output = assert_code_output(
            invoke(bad_module, *registry_args(bad_project, "reconcile", "--apply")), 1, expected_error
        )
        assert_snapshot(before)
        invalid_cases.append((case_name, output))

    symlink_project, symlink_dashboard, symlink_registry = install_sample(root, "apply-symlink")
    symlink_module = load_registry(symlink_registry)
    symlink_index = symlink_dashboard / "Session_Index.md"
    external_index = root / "apply-symlink-external.md"
    external_index.write_bytes(symlink_index.read_bytes())
    symlink_index.unlink()
    symlink_index.symlink_to(external_index)
    symlink_before = snapshot(
        symlink_dashboard / "Sessions.md",
        symlink_dashboard / "Archives/Sessions/Completed.md",
        external_index,
        symlink_dashboard / "Archives/Sessions/archive_manifest.json",
    )
    assert_code_output(
        invoke(symlink_module, *registry_args(symlink_project, "reconcile", "--apply")),
        1, "derived index must be a regular non-symlink file",
    )
    assert_snapshot(symlink_before)

    # AC-04: failure while persisting the initial journal also leaves target bytes unchanged.
    journal_project, journal_dashboard, journal_registry = install_sample(root, "journal-stage")
    journal_module = load_registry(journal_registry)
    move_s002_to_archive(journal_dashboard)
    journal_managed = [
        journal_dashboard / "Sessions.md",
        journal_dashboard / "Archives/Sessions/Completed.md",
        journal_dashboard / "Session_Index.md",
        journal_dashboard / "Archives/Sessions/archive_manifest.json",
    ]
    journal_before = snapshot(*journal_managed)
    with patch.object(journal_module, "write_json_durable", side_effect=OSError("injected journal staging failure")):
        assert_code_output(
            invoke(journal_module, *registry_args(journal_project, "reconcile", "--apply")),
            1, "APPLY_FAILED_ROLLED_BACK", "write_performed=false", "final_change=false",
        )
    assert_snapshot(journal_before)

    # AC-04: partial staging failures for both derived targets leave every managed byte unchanged.
    for relative, case_name in (
        ("Session_Index.md", "stage-index"),
        ("Archives/Sessions/archive_manifest.json", "stage-manifest"),
    ):
        fault_project, fault_dashboard, fault_registry = install_sample(root, case_name)
        fault_module = load_registry(fault_registry)
        move_s002_to_archive(fault_dashboard)
        managed = [
            fault_dashboard / "Sessions.md",
            fault_dashboard / "Archives/Sessions/Completed.md",
            fault_dashboard / "Session_Index.md",
            fault_dashboard / "Archives/Sessions/archive_manifest.json",
        ]
        before = snapshot(*managed)
        fault_target = fault_dashboard / relative
        original_stage = fault_module.stage_bytes
        injected = False

        def partial_stage(target: Path, payload: bytes) -> Path:
            nonlocal injected
            if target.resolve() == fault_target.resolve() and not injected:
                injected = True
                descriptor, name = tempfile.mkstemp(prefix="partial-stage-", dir=target.parent)
                try:
                    os.write(descriptor, payload[: max(1, len(payload) // 2)])
                finally:
                    os.close(descriptor)
                    Path(name).unlink(missing_ok=True)
                raise OSError(f"injected partial staging failure: {relative}")
            return original_stage(target, payload)

        with patch.object(fault_module, "stage_bytes", partial_stage):
            assert_code_output(
                invoke(fault_module, *registry_args(fault_project, "reconcile", "--apply")),
                1, "APPLY_FAILED_ROLLED_BACK", "write_performed=false", "final_change=false",
            )
        assert_snapshot(before)
        if (fault_dashboard / fault_module.RECOVERY_ROOT).exists():
            raise AssertionError("rolled-back staging failure left recovery material")

    # AC-04: either target commit can fail; rollback restores all invocation-time bytes.
    for relative, expected_write, case_name in (
        ("Session_Index.md", "write_performed=false", "commit-index"),
        ("Archives/Sessions/archive_manifest.json", "write_performed=true", "commit-manifest"),
    ):
        fault_project, fault_dashboard, fault_registry = install_sample(root, case_name)
        fault_module = load_registry(fault_registry)
        move_s002_to_archive(fault_dashboard)
        managed = [
            fault_dashboard / "Sessions.md",
            fault_dashboard / "Archives/Sessions/Completed.md",
            fault_dashboard / "Session_Index.md",
            fault_dashboard / "Archives/Sessions/archive_manifest.json",
        ]
        before = snapshot(*managed)
        fault_target = fault_dashboard / relative
        original_replace = fault_module.replace_path
        injected = False

        def fail_commit(source: Path, target: Path) -> None:
            nonlocal injected
            if target.resolve() == fault_target.resolve() and not injected:
                injected = True
                raise OSError(f"injected commit failure: {relative}")
            original_replace(source, target)

        with patch.object(fault_module, "replace_path", fail_commit):
            assert_code_output(
                invoke(fault_module, *registry_args(fault_project, "reconcile", "--apply")),
                1, "APPLY_FAILED_ROLLED_BACK", expected_write, "final_change=false",
            )
        assert_snapshot(before)

    # AC-04/07: replacement followed by directory fsync failure is still an actual write.
    for relative, case_name in (
        ("Session_Index.md", "fsync-index"),
        ("Archives/Sessions/archive_manifest.json", "fsync-manifest"),
    ):
        fsync_project, fsync_dashboard, fsync_registry = install_sample(root, case_name)
        fsync_module = load_registry(fsync_registry)
        move_s002_to_archive(fsync_dashboard)
        fsync_target = fsync_dashboard / relative
        fsync_managed = [
            fsync_dashboard / "Sessions.md",
            fsync_dashboard / "Archives/Sessions/Completed.md",
            fsync_dashboard / "Session_Index.md",
            fsync_dashboard / "Archives/Sessions/archive_manifest.json",
        ]
        fsync_before = snapshot(*fsync_managed)
        original_fsync = fsync_module.fsync_directory
        injected = False

        def fail_after_replace(path: Path) -> None:
            nonlocal injected
            if path.resolve() == fsync_target.parent.resolve() and not injected:
                injected = True
                raise OSError(f"injected post-replace fsync failure: {relative}")
            original_fsync(path)

        with patch.object(fsync_module, "fsync_directory", fail_after_replace):
            assert_code_output(
                invoke(fsync_module, *registry_args(fsync_project, "reconcile", "--apply")),
                1, "APPLY_FAILED_ROLLED_BACK", "write_performed=true", "final_change=false",
            )
        assert_snapshot(fsync_before)

    # AC-05/07: second commit plus rollback failure leaves truthful recovery material and blocks all gates.
    recovery_project, recovery_dashboard, recovery_registry = install_sample(root, "recovery-required")
    recovery_module = load_registry(recovery_registry)
    move_s002_to_archive(recovery_dashboard)
    recovery_index = recovery_dashboard / "Session_Index.md"
    recovery_manifest = recovery_dashboard / "Archives/Sessions/archive_manifest.json"
    recovery_before = snapshot(recovery_index, recovery_manifest)
    original_replace = recovery_module.replace_path
    manifest_failed = False
    rollback_failed = False

    def fail_commit_and_rollback(source: Path, target: Path) -> None:
        nonlocal manifest_failed, rollback_failed
        if target.resolve() == recovery_manifest.resolve() and not manifest_failed:
            manifest_failed = True
            raise OSError("injected second commit failure")
        if manifest_failed and target.resolve() == recovery_index.resolve() and not rollback_failed:
            rollback_failed = True
            raise OSError("injected rollback failure")
        original_replace(source, target)

    with patch.object(recovery_module, "replace_path", fail_commit_and_rollback):
        output = assert_code_output(
            invoke(recovery_module, *registry_args(recovery_project, "reconcile", "--apply")),
            1, "RECOVERY_REQUIRED", "write_performed=true", "final_change=true", "Session_Index.md",
        )
    recovery_root = recovery_dashboard / recovery_module.RECOVERY_ROOT
    transactions = list(recovery_root.iterdir())
    if len(transactions) != 1:
        raise AssertionError(f"expected one recovery transaction, got {transactions}")
    transaction = transactions[0]
    journal = json.loads((transaction / "journal.json").read_text(encoding="utf-8"))
    if journal["state"] != "recovery_required" or journal["write_performed"] is not True:
        raise AssertionError(f"untruthful recovery journal: {journal}")
    if journal["changed_paths"] != ["Session_Index.md"] or str(transaction) not in output:
        raise AssertionError(f"recovery journal/output lacks changed path or locator: {journal}\n{output}")
    assert_code_output(invoke(recovery_module, *registry_args(recovery_project, "reconcile", "--check")), 1, "RECOVERY_REQUIRED")
    assert_code_output(invoke(recovery_module, *registry_args(recovery_project, "validate")), 1, "RECOVERY_REQUIRED")
    recovery_manifest.write_text("{damaged manifest", encoding="utf-8")
    assert_code_output(
        invoke(recovery_module, "recover", "--repo", str(recovery_project), "--transaction", transaction.name),
        0, "RECOVERED", transaction.name,
    )
    assert_snapshot(recovery_before)
    assert_code_output(invoke(recovery_module, *registry_args(recovery_project, "reconcile", "--apply")), 0, "APPLIED")
    assert_code_output(invoke(recovery_module, *registry_args(recovery_project, "reconcile", "--check")), 0, "OK")
    assert_code_output(invoke(recovery_module, *registry_args(recovery_project, "validate")), 0, "OK")

    # AC-05: cleanup failure after a rolled-back apply is also recoverable and cannot be hidden.
    cleanup_project, cleanup_dashboard, cleanup_registry = install_sample(root, "cleanup-failure")
    cleanup_module = load_registry(cleanup_registry)
    move_s002_to_archive(cleanup_dashboard)
    cleanup_manifest = cleanup_dashboard / "Archives/Sessions/archive_manifest.json"
    original_replace = cleanup_module.replace_path
    commit_failed = False

    def fail_second_commit(source: Path, target: Path) -> None:
        nonlocal commit_failed
        if target.resolve() == cleanup_manifest.resolve() and not commit_failed:
            commit_failed = True
            raise OSError("injected second commit failure")
        original_replace(source, target)

    with patch.object(cleanup_module, "replace_path", fail_second_commit), patch.object(
        cleanup_module, "remove_transaction", side_effect=OSError("injected cleanup failure")
    ):
        assert_code_output(
            invoke(cleanup_module, *registry_args(cleanup_project, "reconcile", "--apply")),
            1, "RECOVERY_REQUIRED", "write_performed=true", "final_change=false", "cleanup failed",
        )
    cleanup_transactions = list((cleanup_dashboard / cleanup_module.RECOVERY_ROOT).iterdir())
    assert_code_output(
        invoke(cleanup_module, "recover", "--repo", str(cleanup_project), "--transaction", cleanup_transactions[0].name),
        0, "RECOVERED",
    )

    # AC-05/07: failure to fsync an already-deleted transaction must not advertise impossible recovery.
    deleted_project, deleted_dashboard, deleted_registry = install_sample(root, "deleted-cleanup-fsync")
    deleted_module = load_registry(deleted_registry)
    move_s002_to_archive(deleted_dashboard)
    original_fsync = deleted_module.fsync_directory
    cleanup_fsync_failed = False

    def fail_deleted_transaction_fsync(path: Path) -> None:
        nonlocal cleanup_fsync_failed
        if path.name == deleted_module.RECOVERY_ROOT and not cleanup_fsync_failed:
            cleanup_fsync_failed = True
            raise OSError("injected fsync failure after transaction deletion")
        original_fsync(path)

    with patch.object(deleted_module, "fsync_directory", fail_deleted_transaction_fsync):
        assert_code_output(
            invoke(deleted_module, *registry_args(deleted_project, "reconcile", "--apply")),
            0, "APPLIED", "write_performed=true", "final_change=true",
        )
    if (deleted_dashboard / deleted_module.RECOVERY_ROOT).exists():
        raise AssertionError("successful cleanup left a recovery root after transaction deletion")

    # AC-03/05: recover rejects a managed target replaced by an in-Dashboard symlink.
    target_link_project, target_link_dashboard, target_link_registry = install_sample(root, "recovery-target-symlink")
    target_link_module = load_registry(target_link_registry)
    move_s002_to_archive(target_link_dashboard)
    target_link_index = target_link_dashboard / "Session_Index.md"
    target_link_manifest = target_link_dashboard / "Archives/Sessions/archive_manifest.json"
    original_replace = target_link_module.replace_path
    target_link_commit_failed = False

    def create_target_link_pending(source: Path, target: Path) -> None:
        nonlocal target_link_commit_failed
        if target.resolve() == target_link_manifest.resolve() and not target_link_commit_failed:
            target_link_commit_failed = True
            raise OSError("injected second commit failure")
        if target_link_commit_failed and target.resolve() == target_link_index.resolve():
            raise OSError("injected rollback failure")
        original_replace(source, target)

    with patch.object(target_link_module, "replace_path", create_target_link_pending):
        assert_code_output(
            invoke(target_link_module, *registry_args(target_link_project, "reconcile", "--apply")),
            1, "RECOVERY_REQUIRED",
        )
    target_link_transaction = next((target_link_dashboard / target_link_module.RECOVERY_ROOT).iterdir())
    manifest_before_link_recover = target_link_manifest.read_bytes()
    target_link_index.unlink()
    target_link_index.symlink_to(target_link_manifest)
    assert_code_output(
        invoke(
            target_link_module, "recover", "--repo", str(target_link_project),
            "--transaction", target_link_transaction.name,
        ),
        1, "symlinked target path",
    )
    if not target_link_index.is_symlink() or target_link_manifest.read_bytes() != manifest_before_link_recover:
        raise AssertionError("failed symlink recovery mutated a managed target")
    if not target_link_transaction.is_dir():
        raise AssertionError("failed symlink recovery deleted recovery material")

    # AC-03: a journal cannot select an unmanaged or escaping target.
    tamper_project, tamper_dashboard, tamper_registry = install_sample(root, "tampered-recovery")
    tamper_module = load_registry(tamper_registry)
    move_s002_to_archive(tamper_dashboard)
    tamper_manifest = tamper_dashboard / "Archives/Sessions/archive_manifest.json"
    original_replace = tamper_module.replace_path
    failed = False

    def create_pending(source: Path, target: Path) -> None:
        nonlocal failed
        if target.resolve() == tamper_manifest.resolve() and not failed:
            failed = True
            raise OSError("injected second commit failure")
        if failed and target.resolve() == (tamper_dashboard / "Session_Index.md").resolve():
            raise OSError("injected rollback failure")
        original_replace(source, target)

    with patch.object(tamper_module, "replace_path", create_pending):
        assert_code_output(invoke(tamper_module, *registry_args(tamper_project, "reconcile", "--apply")), 1, "RECOVERY_REQUIRED")
    tamper_transaction = next((tamper_dashboard / tamper_module.RECOVERY_ROOT).iterdir())
    tamper_journal_path = tamper_transaction / "journal.json"
    tamper_journal = json.loads(tamper_journal_path.read_text(encoding="utf-8"))
    tamper_journal["targets"][0]["path"] = "../outside.txt"
    tamper_journal_path.write_text(json.dumps(tamper_journal, indent=2) + "\n", encoding="utf-8")
    assert_code_output(
        invoke(tamper_module, "recover", "--repo", str(tamper_project), "--transaction", tamper_transaction.name),
        1, "unmanaged recovery target",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dashboard-registry-") as tmp:
        root = Path(tmp)
        project, dashboard, registry = install_sample(root, "positive")
        dkg = dashboard / "tools/generate_dashboard_kg.py"
        base = [sys.executable, str(registry)]

        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--check")
        run(*base, "validate", "--repo", str(project), "--contract", str(CONTRACT))
        validate_dashboard(dashboard)
        output = dashboard / "dashboard-kg.json"
        run(sys.executable, str(dkg), "--repo", str(project), "--contract", str(CONTRACT), "--output", str(output))
        if not output.is_file():
            raise AssertionError("positive DKG case did not create output")

        index = dashboard / "Session_Index.md"
        index.write_text(index.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")
        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--check", expect=1)
        run(sys.executable, str(dkg), "--repo", str(project), "--contract", str(CONTRACT), "--output", str(output), expect=1)
        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--apply")
        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--check")

        # B-01: every contract-required current/index/archive/manifest surface is mandatory.
        missing_cases = {
            "missing-current": "Sessions.md",
            "missing-index": "Session_Index.md",
            "missing-archive": "Archives/Sessions/Completed.md",
            "missing-manifest": "Archives/Sessions/archive_manifest.json",
        }
        for name, relative in missing_cases.items():
            _, candidate, _ = install_sample(root, name)
            (candidate / relative).unlink()
            validate_dashboard(candidate, expect=1)

        # B-02: a same-content index symlink blocks reconcile, validate, and DKG.
        link_project, link_dashboard, link_registry = install_sample(root, "index-symlink")
        link_index = link_dashboard / "Session_Index.md"
        external_index = root / "external-index.md"
        external_index.write_text(link_index.read_text(encoding="utf-8"), encoding="utf-8")
        link_index.unlink()
        link_index.symlink_to(external_index)
        link_base = [sys.executable, str(link_registry)]
        run(*link_base, "reconcile", "--repo", str(link_project), "--contract", str(CONTRACT), "--check", expect=1)
        run(*link_base, "validate", "--repo", str(link_project), "--contract", str(CONTRACT), expect=1)
        run(
            sys.executable, str(link_dashboard / "tools/generate_dashboard_kg.py"),
            "--repo", str(link_project), "--contract", str(CONTRACT),
            "--output", str(link_dashboard / "dashboard-kg.json"), expect=1,
        )
        validate_dashboard(link_dashboard, expect=1)

        # B-03 positive: a project override may add a value that is not forbidden.
        sessions = dashboard / "Sessions.md"
        sessions.write_text(sessions.read_text(encoding="utf-8").replace("`doing`", "`queued`", 1), encoding="utf-8")
        custom_contract = root / "custom-contract.json"
        contract_data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        contract_data["lifecycle_status"]["allowed"].append("queued")
        custom_contract.write_text(json.dumps(contract_data, indent=2) + "\n", encoding="utf-8")
        run(*base, "reconcile", "--repo", str(project), "--contract", str(custom_contract), "--apply")
        run(*base, "validate", "--repo", str(project), "--contract", str(custom_contract))
        validate_dashboard(dashboard, custom_contract)

        # B-03 negatives: reject exact and wildcard intersections before row validation.
        for value, name in (("partial", "exact-conflict"), ("bounded-review", "pattern-conflict")):
            conflict_data = json.loads(CONTRACT.read_text(encoding="utf-8"))
            conflict_data["lifecycle_status"]["allowed"].append(value)
            conflict_contract = root / f"{name}.json"
            conflict_contract.write_text(json.dumps(conflict_data, indent=2) + "\n", encoding="utf-8")
            run(*base, "validate", "--repo", str(project), "--contract", str(conflict_contract), expect=1)
            validate_dashboard(dashboard, conflict_contract, expect=1)

        sessions.write_text(sessions.read_text(encoding="utf-8").replace("`queued`", "`doing`", 1), encoding="utf-8")
        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--apply")
        (dashboard / "Archives/Sessions/Unknown.md").write_text("# Unknown\n", encoding="utf-8")
        run(*base, "reconcile", "--repo", str(project), "--contract", str(CONTRACT), "--apply", expect=1)

        test_transactional_registry(root)

    print(
        "OK: complete registry surfaces, index symlink, contract exact/pattern consistency, "
        "positive registry, drift repair, DKG ordering, unknown-archive cases, and G-001 AC-01..AC-08 fault coverage"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
