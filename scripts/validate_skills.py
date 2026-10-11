#!/usr/bin/env python3
"""Validate the skill pack.

Checks, for every skills/<dir>/SKILL.md:
  1. file exists and is non-empty UTF-8
  2. has YAML frontmatter delimited by --- on the first line
  3. frontmatter has non-empty `name` and `description`
  4. frontmatter `name` matches the directory name
  5. description length is within a usable range (30..1200 chars)
  6. every relative markdown link to a local file resolves
  7. no CRLF line endings

Exit code 0 = pass, 1 = at least one failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue  # nested key, handled loosely
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def check_links(text: str, where: Path, errors: list[str]) -> None:
    for target in LINK_RE.findall(text):
        t = target.split("#", 1)[0].strip()
        if not t:
            continue
        if t.startswith(("http://", "https://", "mailto:", "/", "#")):
            continue
        resolved = (where.parent / t).resolve()
        if not resolved.exists():
            errors.append(f"{where.relative_to(ROOT)}: broken link -> {target}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not SKILLS.is_dir():
        print(f"FAIL: skills directory not found at {SKILLS}")
        return 1

    dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    if not dirs:
        print("FAIL: no skill directories found")
        return 1

    for d in dirs:
        skill_md = d / "SKILL.md"
        rel = skill_md.relative_to(ROOT)

        if not skill_md.is_file():
            errors.append(f"{d.name}: missing SKILL.md")
            continue

        raw = skill_md.read_bytes()
        if b"\r\n" in raw:
            errors.append(f"{rel}: contains CRLF line endings")

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{rel}: not valid UTF-8 ({exc})")
            continue

        if not text.strip():
            errors.append(f"{rel}: file is empty")
            continue

        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{rel}: missing or malformed YAML frontmatter")
            continue

        name = fm.get("name", "")
        desc = fm.get("description", "")

        if not name:
            errors.append(f"{rel}: frontmatter missing `name`")
        elif name != d.name:
            errors.append(
                f"{rel}: frontmatter name `{name}` != directory name `{d.name}`"
            )

        if not desc:
            errors.append(f"{rel}: frontmatter missing `description`")
        elif not (30 <= len(desc) <= 1200):
            errors.append(
                f"{rel}: description length {len(desc)} outside 30..1200"
            )

        check_links(text, skill_md, errors)

        body_lines = len(text.split("\n"))
        if body_lines < 40:
            warnings.append(f"{rel}: only {body_lines} lines — is it substantive?")

        # Placeholder patterns are only a problem inside fenced code blocks;
        # prose legitimately discusses them.
        for fence in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
            for pat in ("TODO", "FIXME", "// ...", "/* ... */"):
                if pat in fence:
                    warnings.append(f"{rel}: placeholder `{pat}` inside a code block")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print(f"\nchecked {len(dirs)} skills · {len(errors)} errors · {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
