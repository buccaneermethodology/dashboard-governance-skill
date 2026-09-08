#!/usr/bin/env python3
"""Validate the portable Goal/Stage Plan artifact-batch layout."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BATCH_NAME = re.compile(r"^(?:Goal|Stage-Plan)-[A-Za-z0-9][A-Za-z0-9._-]*$")
ROOT_FILES = {"README.md"}


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.exists():
        return [f"artifact root not found: {root}"]
    if root.is_symlink() or not root.is_dir():
        return [f"artifact root must be a regular directory: {root}"]

    for path in sorted(root.iterdir(), key=lambda item: item.name):
        relative = path.relative_to(root)
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {relative}")
            continue
        if path.is_file():
            if path.name not in ROOT_FILES:
                errors.append(f"loose file is not allowed at artifact root: {relative}")
            continue
        if not path.is_dir():
            errors.append(f"unsupported artifact-root entry: {relative}")
            continue
        if not BATCH_NAME.fullmatch(path.name):
            errors.append(f"invalid batch directory name: {relative}")
        readme = path / "README.md"
        if not readme.is_file() or readme.is_symlink():
            errors.append(f"batch must contain a regular README.md: {relative}")
        for child in path.rglob("*"):
            child_relative = child.relative_to(root)
            if child.is_symlink():
                errors.append(f"symlink is not allowed: {child_relative}")
            elif not child.is_file() and not child.is_dir():
                errors.append(f"unsupported artifact entry: {child_relative}")

    readme = root / "README.md"
    if not readme.is_file() or readme.is_symlink():
        errors.append("artifact root must contain a regular README.md")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Goal/Stage Plan artifact batches.")
    parser.add_argument("artifacts_dir", type=Path)
    args = parser.parse_args()
    errors = validate(args.artifacts_dir)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"OK: artifact batches {args.artifacts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
