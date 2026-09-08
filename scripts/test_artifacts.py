#!/usr/bin/env python3
"""Direct positive and fail-closed checks for artifact-batch validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_artifacts.py"


def run(path: Path, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != expect:
        raise AssertionError(
            f"expected exit {expect}, got {result.returncode}: {result.stdout}{result.stderr}"
        )
    return result


def make_root(parent: Path, name: str = "Artifacts") -> Path:
    root = parent / name
    root.mkdir()
    (root / "README.md").write_text("# Artifact Batches\n", encoding="utf-8")
    batch = root / "Stage-Plan-SP-001"
    batch.mkdir()
    (batch / "README.md").write_text("# Batch\n", encoding="utf-8")
    (batch / "validation").mkdir()
    (batch / "validation/verdict.md").write_text("pass\n", encoding="utf-8")
    return root


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dashboard-artifacts-") as temporary:
        parent = Path(temporary)

        positive = make_root(parent, "positive")
        run(positive)

        loose = make_root(parent, "loose")
        (loose / "orphan.md").write_text("orphan\n", encoding="utf-8")
        run(loose, expect=1)

        invalid_name = make_root(parent, "invalid-name")
        batch = invalid_name / "Stage-Plan-SP-001"
        batch.rename(invalid_name / "not-a-batch")
        run(invalid_name, expect=1)

        missing_metadata = make_root(parent, "missing-metadata")
        (missing_metadata / "Stage-Plan-SP-001/README.md").unlink()
        run(missing_metadata, expect=1)

        symlinked = make_root(parent, "symlinked")
        target = symlinked / "validation-target.md"
        target.write_text("outside\n", encoding="utf-8")
        (symlinked / "Stage-Plan-SP-001/validation/link.md").symlink_to(target)
        run(symlinked, expect=1)

        root_link_target = make_root(parent, "root-link-target")
        root_link = parent / "root-link"
        root_link.symlink_to(root_link_target, target_is_directory=True)
        run(root_link, expect=1)

    print("OK: artifact batch positive, loose-file, naming, metadata, and symlink cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
