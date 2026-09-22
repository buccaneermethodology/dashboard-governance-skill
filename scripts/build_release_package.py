#!/usr/bin/env python3
"""Build or verify a deterministic dashboard-governance skill archive."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import tarfile
from pathlib import Path

EPOCH = 0
PREFIX = "dashboard-governance"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed in release source: {path}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise ValueError(f"special object is not allowed in release source: {path}")
    return files


def build(source: Path, version: str, output_dir: Path) -> tuple[Path, Path]:
    files = source_files(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"dashboard-governance-skill-v{version}.tar.gz"
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=EPOCH) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar:
                root = tarfile.TarInfo(PREFIX)
                root.type = tarfile.DIRTYPE
                root.mode = 0o755
                root.mtime = EPOCH
                tar.addfile(root)
                for path in files:
                    relative = path.relative_to(source).as_posix()
                    payload = path.read_bytes()
                    info = tarfile.TarInfo(f"{PREFIX}/{relative}")
                    info.size = len(payload)
                    info.mode = 0o644
                    info.mtime = EPOCH
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    tar.addfile(info, io.BytesIO(payload))
    checksums = output_dir / "SHA256SUMS"
    checksums.write_text(f"{digest(archive)}  {archive.name}\n", encoding="utf-8")
    return archive, checksums


def verify(archive: Path, checksums: Path, source: Path | None) -> list[str]:
    errors: list[str] = []
    expected_line = checksums.read_text(encoding="utf-8").strip().split()
    if len(expected_line) != 2 or expected_line[1] != archive.name or expected_line[0] != digest(archive):
        errors.append("RELEASE_CHECKSUM_MISMATCH")
    expected_members = None
    if source is not None:
        expected_members = {PREFIX} | {f"{PREFIX}/{path.relative_to(source).as_posix()}" for path in source_files(source)}
    with tarfile.open(archive, mode="r:gz") as tar:
        members = tar.getmembers()
        names = {member.name for member in members}
        if len(names) != len(members) or any(name.startswith("/") or ".." in Path(name).parts for name in names):
            errors.append("RELEASE_ARCHIVE_UNSAFE_OR_DUPLICATE")
        if expected_members is not None and names != expected_members:
            errors.append("RELEASE_ARCHIVE_INVENTORY_MISMATCH")
        for member in members:
            if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
                errors.append(f"RELEASE_ARCHIVE_UNSUPPORTED_MEMBER: {member.name}")
            if member.mtime != EPOCH or member.uid != 0 or member.gid != 0:
                errors.append(f"RELEASE_ARCHIVE_NONDETERMINISTIC_METADATA: {member.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--source", type=Path, required=True)
    build_parser.add_argument("--version", required=True)
    build_parser.add_argument("--output-dir", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--archive", type=Path, required=True)
    verify_parser.add_argument("--checksums", type=Path, required=True)
    verify_parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        archive, checksums = build(args.source.resolve(), args.version, args.output_dir.resolve())
        print(f"OK: {archive}")
        print(f"OK: {checksums}")
        return 0
    errors = verify(args.archive.resolve(), args.checksums.resolve(), args.source.resolve() if args.source else None)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"OK: verified {args.archive.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
