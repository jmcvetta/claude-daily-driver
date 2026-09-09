#!/usr/bin/env python3
"""The manifest checks `claude plugin validate` does not make.

`claude plugin validate --strict` covers most of what can go wrong in a
plugin, and everything it covers is left to it. Four things it lets through
are checked here, each measured against the CLI rather than assumed:

- A skill whose frontmatter `name` disagrees with its directory. `validate`
  passes it; Claude Code resolves the skill by directory, so the name in the
  file is the one that is wrong and nothing says so.
- An agent whose frontmatter `name` disagrees with its filename. Agents resolve
  the other way round -- by the frontmatter `name`, measured -- so the file is
  the misleading half, and a reader looking for `logic-reviewer` finds nothing.
- Two agents claiming one `name`. Only one of them is dispatchable; the other
  is silently shadowed, and `validate --strict` says nothing.
- A `description:` present but empty, in a skill or an agent. `validate` warns
  only when the key is missing outright, so `description: ""` is green under
  `--strict` and the component reaches users with nothing to trigger on.
- A `name` disagreeing between plugin.json and its marketplace entry, or
  between the marketplace and the repository it names. `validate` reads one
  manifest at a time, so it never compares them. (It *does* compare the
  `version` fields, so those are its job and not this script's.)
- A copy of the repository stanza — the template, this repository's own
  `.claude/settings.json`, a fenced block in the documentation — that has
  drifted from the marketplace and plugin names it enables. `validate` does not
  read settings files at all, and a stanza naming a marketplace that does not
  exist enables nothing while looking entirely correct. See `stanza.py`. A
  documented block may quote part of the stanza; a block deliberately showing
  a wrong one is exempted with `<!-- stanza-check: ignore -->` above it.

No third-party imports: this runs from a Makefile on a laptop and from CI,
and a dependency install between the two is a place for them to differ.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import stanza

ROOT = Path(__file__).resolve().parent.parent

# Fenced JSON in the prose. Documentation is where the cold start is served
# from -- a person with no plugin and no tooling copies a block out of a file
# -- so a block that has drifted is a silent failure handed out on purpose.
JSON_BLOCK = re.compile(r"^```json\n(.*?)^```", re.DOTALL | re.MULTILINE)

# The one block that must not be checked is the one printing a stanza known to
# be wrong -- `daily-driver@daily-driver` is worth showing precisely because it
# looks right -- so a block preceded by this marker is skipped. It has to be
# the last thing before the fence, so it cannot be left behind by an edit that
# moves the block it was written for.
IGNORE = re.compile(r"<!--\s*stanza-check:\s*ignore\s*-->\s*\Z")

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


def load_json(path: Path, errors: list[str]) -> object | None:
    """Parse `path`, reporting a bad file the way every other check reports.

    A settings file people hand-edit is exactly where a trailing comma turns
    up, and a traceback there both reads as a broken check and abandons the
    copies not yet looked at.
    """
    where = path.relative_to(ROOT)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{where}: not valid JSON: {exc}")
        return None
    except OSError as exc:
        errors.append(f"{where}: cannot be read: {exc}")
        return None


def section_of(parsed: object, section: str) -> dict | None:
    """A stanza section of `parsed`, or None if it has none worth comparing."""
    if not isinstance(parsed, dict):
        return None
    entries = parsed.get(section)
    return entries if isinstance(entries, dict) else None


def stanza_errors() -> list[str]:
    """Every copy of the stanza, measured against the manifests."""
    errors: list[str] = []
    expected = stanza.canonical()

    # The template is copied wholesale into a new repository, so it is the one
    # copy that must be the stanza and nothing else.
    template = ROOT / "template" / ".claude" / "settings.json"
    if not template.exists():
        errors.append(f"{template.relative_to(ROOT)}: missing")
    else:
        parsed = load_json(template, errors)
        if parsed is not None and parsed != expected:
            errors.append(
                f"{template.relative_to(ROOT)}: does not match the stanza "
                "`python3 scripts/stanza.py` prints"
            )

    # This repository carries the stanza too, and may grow other settings
    # around it, so it is checked for containment rather than equality.
    own = ROOT / ".claude" / "settings.json"
    if not own.exists():
        errors.append(f"{own.relative_to(ROOT)}: missing")
    else:
        settings = load_json(own, errors)
        if settings is not None:
            for section, entries in expected.items():
                present = section_of(settings, section)
                for key, value in entries.items():
                    if present is None or present.get(key) != value:
                        errors.append(
                            f"{own.relative_to(ROOT)}: {section}.{key} is "
                            "missing or disagrees with the stanza"
                        )

    docs = [ROOT / "README.md", *sorted(ROOT.glob("docs/**/*.md"))]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        where = doc.relative_to(ROOT)
        for match in JSON_BLOCK.finditer(text):
            block = match.group(1)
            if not any(key in block for key in expected):
                continue
            if IGNORE.search(text[: match.start()]):
                continue
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError as exc:
                errors.append(f"{where}: stanza block is not valid JSON: {exc}")
                continue
            if not isinstance(parsed, dict):
                errors.append(f"{where}: stanza block is not a JSON object")
                continue
            # A block is allowed to quote part of the stanza — one section, or
            # one entry of one — since the prose walks through the halves
            # separately. What it may not do is name a key the stanza does not
            # have, or give one a different value: that is the drift being
            # hunted, and it looks entirely correct on the page.
            for section, entries in expected.items():
                present = parsed.get(section)
                if present is None:
                    continue
                if not isinstance(present, dict):
                    errors.append(f"{where}: stanza block's {section} is not an object")
                    continue
                for key, value in present.items():
                    if key not in entries:
                        errors.append(
                            f"{where}: stanza block's {section} names {key!r}, "
                            "which is not in the stanza `python3 "
                            "scripts/stanza.py` prints"
                        )
                    elif value != entries[key]:
                        errors.append(
                            f"{where}: stanza block's {section}.{key} disagrees "
                            "with `python3 scripts/stanza.py`"
                        )
    return errors


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
    repository = stanza.owner_repo(plugin["repository"]).split("/")[-1]
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

    # Agents resolve by their frontmatter `name`, not their filename -- the
    # opposite of skills -- so a mismatch means the filename lies, and two
    # agents sharing a name means one of them is unreachable.
    #
    # Zero agents is not an error, unlike zero skills: the plugin ships none
    # today, and `glob` on the absent directory is empty rather than a crash.
    # The loop stays so that an agent revived out of `attic/agents/` is checked
    # the moment it lands.
    agents = sorted((ROOT / "agents").glob("*.md"))
    claimed: dict[str, Path] = {}
    for agent in agents:
        where = agent.relative_to(ROOT)
        fields = frontmatter(agent)
        if fields is None:
            errors.append(f"{where}: no `---` frontmatter block")
            continue
        name = fields.get("name")
        if name != agent.stem:
            errors.append(
                f"{where}: frontmatter name is {name!r} "
                f"but the file is named {agent.stem!r}"
            )
        if not fields.get("description"):
            errors.append(f"{where}: frontmatter description is empty")
        if name:
            if name in claimed:
                errors.append(
                    f"{where}: agent name {name!r} is already claimed by "
                    f"{claimed[name].relative_to(ROOT)}; one of them is "
                    "unreachable"
                )
            else:
                claimed[name] = agent

    errors.extend(stanza_errors())

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(
        f"manifests agree; {len(skills)} skill(s) "
        f"and {len(agents)} agent(s) checked; stanza copies agree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
