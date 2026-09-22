#!/usr/bin/env python3
"""Owner-side exact-copy installer for a frozen Dashboard authority bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_bundle(bundle: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    manifest_path = bundle / "digest-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {}, ["BUNDLE_MANIFEST_INVALID: manifest must be a regular non-symlink file"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"BUNDLE_MANIFEST_INVALID: {exc}"]
    if manifest.get("schema_version") != "owner_provisioned_authority_bundle_manifest_v1":
        return {}, ["BUNDLE_MANIFEST_INVALID: wrong schema_version"]
    expected: dict[str, str] = {}
    for item in manifest.get("files", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
            errors.append("BUNDLE_MANIFEST_INVALID: malformed file entry")
            continue
        expected[item["path"]] = item["sha256"]
    expected_names = set(expected) | {"digest-manifest.json"}
    actual_names: set[str] = set()
    for path in bundle.iterdir():
        actual_names.add(path.name)
        if path.is_symlink():
            errors.append(f"BUNDLE_SYMLINK_FORBIDDEN: {path.name}")
        elif not path.is_file():
            errors.append(f"BUNDLE_NON_REGULAR_ENTRY: {path.name}")
    if actual_names != expected_names:
        errors.append("BUNDLE_FILE_SET_MISMATCH: bundle files differ from manifest")
    for name, digest in expected.items():
        path = bundle / name
        if not path.is_file() or path.is_symlink() or sha256(path) != digest:
            errors.append(f"BUNDLE_DIGEST_MISMATCH: {name}")
    return expected, errors


def install(bundle: Path, target: Path) -> list[str]:
    expected, errors = verify_bundle(bundle)
    if errors:
        return errors
    if target.exists():
        actual = {path.name for path in target.iterdir() if path.is_file()}
        allowed = set(expected) | {"digest-manifest.json"}
        if actual - allowed or any(path.is_dir() or path.is_symlink() for path in target.iterdir()):
            return ["MANAGED_TARGET_AMBIGUOUS: unknown target content"]
    target.mkdir(parents=True, exist_ok=True)
    for name in [*sorted(expected), "digest-manifest.json"]:
        shutil.copyfile(bundle / name, target / name)
    installed, installed_errors = verify_bundle(target)
    if installed_errors or installed != expected or sha256(target / "digest-manifest.json") != sha256(bundle / "digest-manifest.json"):
        return installed_errors or ["INSTALLED_COPY_MISMATCH"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision a frozen authority bundle before task start.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("managed_target", type=Path)
    args = parser.parse_args()
    errors = install(args.bundle.resolve(), args.managed_target.resolve())
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"OK: exact authority bundle installed at {args.managed_target.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
