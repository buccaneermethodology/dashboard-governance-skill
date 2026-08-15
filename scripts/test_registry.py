#!/usr/bin/env python3
"""Direct positive and fail-closed checks for the portable registry sample."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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

    print(
        "OK: complete registry surfaces, index symlink, contract exact/pattern consistency, "
        "positive registry, drift repair, DKG ordering, and unknown-archive cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
