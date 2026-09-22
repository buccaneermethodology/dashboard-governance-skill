#!/usr/bin/env python3
"""Installed-copy positive and fail-closed tests for the frozen Authority v2 bundle."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "skill/dashboard-governance/fixtures/authority-v2"
INSTALLER = ROOT / "scripts/install_authority_bundle.py"


def run(args: list[str], expected: int, contains: str) -> None:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    output = result.stdout + result.stderr
    if result.returncode != expected or contains not in output:
        raise AssertionError(f"expected exit {expected} with {contains!r}\n{output}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dashboard-authority-install-") as temporary:
        install_root = Path(temporary) / "installed"
        scripts = install_root / "scripts"
        skill = install_root / "skill/dashboard-governance"
        scripts.mkdir(parents=True)
        skill.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/validate_work_breakdown.py", scripts / "validate_work_breakdown.py")
        shutil.copyfile(ROOT / "scripts/validate_dashboard.py", scripts / "validate_dashboard.py")
        managed = skill / ".managed-authority"
        run([sys.executable, str(INSTALLER), str(BUNDLE), str(managed)], 0, "exact authority bundle installed")
        run(
            [sys.executable, str(scripts / "validate_work_breakdown.py"), str(managed / "positive-work-breakdown.json")],
            0,
            "advanced work breakdown conforms",
        )

        missing_root = Path(temporary) / "missing-root"
        missing_scripts = missing_root / "scripts"
        missing_scripts.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/validate_work_breakdown.py", missing_scripts / "validate_work_breakdown.py")
        shutil.copyfile(ROOT / "scripts/validate_dashboard.py", missing_scripts / "validate_dashboard.py")
        run(
            [sys.executable, str(missing_scripts / "validate_work_breakdown.py"), str(BUNDLE / "positive-work-breakdown.json")],
            1,
            "AUTHORITY_PROVENANCE_NOT_BOUND",
        )

        tampered = Path(temporary) / "tampered"
        shutil.copytree(BUNDLE, tampered)
        (tampered / "authority-root.json").write_text("{}\n", encoding="utf-8")
        run([sys.executable, str(INSTALLER), str(tampered), str(Path(temporary) / "tampered-target")], 1, "BUNDLE_DIGEST_MISMATCH")

        unknown_directory = Path(temporary) / "unknown-directory"
        shutil.copytree(BUNDLE, unknown_directory)
        (unknown_directory / "unexpected-directory").mkdir()
        run(
            [sys.executable, str(INSTALLER), str(unknown_directory), str(Path(temporary) / "directory-target")],
            1,
            "BUNDLE_NON_REGULAR_ENTRY",
        )

        symlinked = Path(temporary) / "symlinked"
        shutil.copytree(BUNDLE, symlinked)
        (symlinked / "unexpected-link").symlink_to(symlinked / "authority-root.json")
        run(
            [sys.executable, str(INSTALLER), str(symlinked), str(Path(temporary) / "symlink-target")],
            1,
            "BUNDLE_SYMLINK_FORBIDDEN",
        )

        symlink_manifest = Path(temporary) / "symlink-manifest"
        shutil.copytree(BUNDLE, symlink_manifest)
        manifest_copy = Path(temporary) / "external-manifest.json"
        shutil.copyfile(symlink_manifest / "digest-manifest.json", manifest_copy)
        (symlink_manifest / "digest-manifest.json").unlink()
        (symlink_manifest / "digest-manifest.json").symlink_to(manifest_copy)
        run(
            [sys.executable, str(INSTALLER), str(symlink_manifest), str(Path(temporary) / "manifest-target")],
            1,
            "BUNDLE_MANIFEST_INVALID",
        )

        special = Path(temporary) / "special"
        shutil.copytree(BUNDLE, special)
        os.mkfifo(special / "unexpected-fifo")
        run(
            [sys.executable, str(INSTALLER), str(special), str(Path(temporary) / "special-target")],
            1,
            "BUNDLE_NON_REGULAR_ENTRY",
        )

        ambiguous = Path(temporary) / "ambiguous"
        ambiguous.mkdir()
        (ambiguous / "unknown.txt").write_text("unknown\n", encoding="utf-8")
        run([sys.executable, str(INSTALLER), str(BUNDLE), str(ambiguous)], 1, "MANAGED_TARGET_AMBIGUOUS")

    print("OK: exact-copy positive plus missing, tampered, unknown-directory, symlink, manifest-symlink, special-object, and ambiguous negatives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
