#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_DESCRIPTION_LENGTH = 1024


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")

    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["SKILL.md not found"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not re.fullmatch(r"[a-z0-9-]+", name):
        errors.append("name must be lowercase hyphen-case")
    if name != skill_dir.name:
        errors.append("frontmatter name must match skill directory name")
    if not description:
        errors.append("description is required")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append("description is too long")
    if "<" in description or ">" in description:
        errors.append("description must not contain angle brackets")
    if "TODO" in text or "[TODO" in text:
        errors.append("SKILL.md still contains TODO markers")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append("agents/openai.yaml not found")
    elif f"${name}" not in openai_yaml.read_text(encoding="utf-8"):
        errors.append("agents/openai.yaml default_prompt should mention the skill as $name")

    references = list((skill_dir / "references").glob("*.md")) if (skill_dir / "references").exists() else []
    if not references:
        errors.append("at least one references/*.md file is expected for this skill")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py <skill_dir>")
        return 2

    skill_dir = Path(sys.argv[1])
    errors = validate(skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
