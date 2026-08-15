#!/usr/bin/env python3
"""Generate a non-authoritative Dashboard graph after registry gates pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from session_registry import RegistryError, collect, render_index, render_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--contract")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        dashboard, records, manifest = collect(Path(args.repo).resolve(), args.contract)
        if (dashboard / "Session_Index.md").read_text(encoding="utf-8") != render_index(records):
            raise RegistryError("registry gate failed: Session_Index.md drift")
        manifest_path = dashboard / "Archives/Sessions/archive_manifest.json"
        if manifest_path.read_text(encoding="utf-8") != render_manifest(manifest, records):
            raise RegistryError("registry gate failed: archive_manifest.json drift")
        output = Path(args.output).resolve()
        payload = {
            "schema_version": "dashboard_kg_read_model_v1",
            "authority": "non_authoritative_read_model",
            "nodes": [
                {
                    "id": record.identifier,
                    "type": "Session",
                    "status": record.status,
                    "topic": record.topic,
                    "source": record.location,
                }
                for record in sorted(records, key=lambda item: item.identifier)
            ],
            "edges": [],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"OK: wrote DKG read model to {output}")
        return 0
    except (RegistryError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
