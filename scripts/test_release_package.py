#!/usr/bin/env python3
"""Determinism and fail-closed tests for the v0.4.0 release package."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_release_package.py"
SOURCE = ROOT / "skill/dashboard-governance"


def run(args: list[str], expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    if result.returncode != expected:
        raise AssertionError(f"expected {expected}, got {result.returncode}\n{result.stdout}{result.stderr}")
    return result


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dashboard-release-") as temporary:
        root = Path(temporary)
        first, second = root / "first", root / "second"
        for output in (first, second):
            run([sys.executable, str(BUILDER), "build", "--source", str(SOURCE), "--version", "0.4.0", "--output-dir", str(output)])
        archive_name = "dashboard-governance-skill-v0.4.0.tar.gz"
        if (first / archive_name).read_bytes() != (second / archive_name).read_bytes():
            raise AssertionError("release archive is not deterministic")
        if (first / "SHA256SUMS").read_bytes() != (second / "SHA256SUMS").read_bytes():
            raise AssertionError("SHA256SUMS is not deterministic")
        run([
            sys.executable, str(BUILDER), "verify", "--archive", str(first / archive_name),
            "--checksums", str(first / "SHA256SUMS"), "--source", str(SOURCE),
        ])
        (first / archive_name).write_bytes((first / archive_name).read_bytes() + b"tamper")
        run([
            sys.executable, str(BUILDER), "verify", "--archive", str(first / archive_name),
            "--checksums", str(first / "SHA256SUMS"), "--source", str(SOURCE),
        ], expected=1)
    print("OK: deterministic archive/checksum, inventory verification, and tamper negative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
