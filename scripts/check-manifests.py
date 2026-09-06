#!/usr/bin/env python3
"""The manifest checks `claude plugin validate` does not make.

`claude plugin validate --strict` covers most of what can go wrong in a
plugin, and everything it covers is left to it. Three things it lets through
are checked here, each measured against the CLI rather than assumed:

- A skill whose frontmatter `name` disagrees with its directory. `validate`
  passes it; Claude Code resolves the skill by directory, so the name in the
  file is the one that is wrong and nothing says so.
- A `description:` present but empty. `validate` warns only when the key is
  missing outright, so `description: ""` is green under `--strict` and the
  skill reaches users with nothing to trigger on.
- A `name` disagreeing between plugin.json and its marketplace entry, or
  between the marketplace and the repository it names. `validate` reads one
  manifest at a time, so it never compares them. (It *does* compare the
  `version` fields, so those are its job and not this script's.)

No third-party imports: this runs from a Makefile on a laptop and from CI,
and a dependency install between the two is a place for them to differ.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Not a YAML parser, and not trying to be. Skill frontmatter here is flat
# `key: value` with folded scalars, so this reads exactly that shape and
# reports anything else as unparseable rather than guessing at it.
KEY = re.compile(r"([A-Za-z0-9_-]+):(.*)$")
BLOCK_SCALAR = {">", ">-", ">+", "|", "|-", "|+"}


def frontmatter(path: Path) -> dict[str, str] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next(
        (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None
    )
    if end is None:
        return None

    fields: dict[str, list[str]] = {}
    key: str | None = None
    for line in lines[1:end]:
        match = KEY.match(line)
        if match and not line[:1].isspace():
            key = match.group(1)
            fields[key] = [match.group(2).strip()]
        elif key is not None:
            fields[key].append(line.strip())
    return {name: unfold(parts) for name, parts in fields.items()}


def unfold(parts: list[str]) -> str:
    head, *rest = parts
    if head in BLOCK_SCALAR:
        head = ""
    return " ".join(part for part in [head, *rest] if part).strip().strip("\"'")


def main() -> int:
    errors: list[str] = []

    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text())

    # The marketplace names the repository people install from -- `claude
    # plugin marketplace add jmcvetta/claude-daily-driver` resolves through
    # that name -- so it has to be the repository's. Read from plugin.json's
    # declared `repository` rather than from the checkout directory, which is
    # whatever the person cloning chose to call it.
    declared = plugin["repository"].rstrip("/").removesuffix(".git")
    repository = declared.rsplit("/", 1)[-1]
    if marketplace["name"] != repository:
        errors.append(
            f"marketplace.json name is {marketplace['name']!r} "
            f"but plugin.json declares the repository {repository!r}"
        )

    # The plugin is the repository root -- `"source": "./"` -- so exactly one
    # marketplace entry describes it, and it has to agree about the name.
    own = [e for e in marketplace["plugins"] if e.get("source") == "./"]
    if len(own) != 1:
        errors.append(
            "expected exactly one marketplace entry with source './', "
            f"found {len(own)}"
        )
    elif own[0]["name"] != plugin["name"]:
        errors.append(
            f"marketplace entry name is {own[0]['name']!r} "
            f"but plugin.json says {plugin['name']!r}"
        )

    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        errors.append("no skills/*/SKILL.md found")
    for skill in skills:
        where = skill.relative_to(ROOT)
        fields = frontmatter(skill)
        if fields is None:
            errors.append(f"{where}: no `---` frontmatter block")
            continue
        if fields.get("name") != skill.parent.name:
            errors.append(
                f"{where}: frontmatter name is {fields.get('name')!r} "
                f"but the directory is {skill.parent.name!r}"
            )
        if not fields.get("description"):
            errors.append(f"{where}: frontmatter description is empty")

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"manifests agree; {len(skills)} skill(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
