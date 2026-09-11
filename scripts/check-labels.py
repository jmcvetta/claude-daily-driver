#!/usr/bin/env python3
"""The label standard is written twice, so the two copies are checked.

`skills/issue-labels/SKILL.md` carries the table a session reads.
`infra/github/labels.tf` carries the `github_issue_label` resources GitHub is
configured from. A label's description is the same string in both, because the
skill is what Claude reads and GitHub is what a person hovers, and a standard
that says one thing in each is not a standard.

Nothing else would catch the drift. `claude plugin validate` never opens a
`.tf` file, `tofu validate` never opens a skill, and a table row that has
fallen behind the Tofu reads exactly like one that has not -- it is prose, and
it is still well-formed. The failure is silent in both directions: a label
declared in Tofu and missing from the table is one no session will ever apply,
and a label in the table and missing from Tofu is one an apply will not create.

WHAT IT ASSERTS

    The same set of label names in both files.
    The same description for every name.
    A non-empty colour on every Tofu resource, and no two labels sharing one.

WHAT IT DOES NOT ASSERT

    That the labels exist on GitHub. Only an apply puts them there, and this
    script is credential-free on purpose -- it runs from a Makefile on a
    laptop and from CI, and neither has a token with admin rights.

No third-party imports, for the reason `check-manifests.py` gives: a
dependency install between the laptop and CI is a place for them to differ.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "issue-labels" / "SKILL.md"
LABELS_TF = ROOT / "infra" / "github" / "labels.tf"

# The table is found by its marker rather than by position, so prose may be
# added above or below it without silently moving what is parsed. Rows run
# from the marker to the first blank line after the table.
TABLE_MARKER = "<!-- labels-table -->"

# | `name` | description | anything |
TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|")

# resource "github_issue_label" "epic" { ... }
TF_RESOURCE = re.compile(
    r'resource\s+"github_issue_label"\s+"[^"]+"\s*\{(.*?)^\}',
    re.DOTALL | re.MULTILINE,
)
TF_ATTR = re.compile(r'^\s*(\w+)\s*=\s*"([^"]*)"\s*$', re.MULTILINE)


def parse_skill_table(text: str) -> dict[str, str]:
    """Return {label name: description} from the marked table in the skill."""
    start = text.find(TABLE_MARKER)
    if start < 0:
        sys.exit(f"{SKILL}: no {TABLE_MARKER} marker; nothing to check against")

    labels: dict[str, str] = {}
    for line in text[start + len(TABLE_MARKER):].splitlines():
        if labels and not line.startswith("|"):
            break
        match = TABLE_ROW.match(line)
        if match:
            labels[match.group(1)] = match.group(2)
    if not labels:
        sys.exit(f"{SKILL}: the table after {TABLE_MARKER} has no rows")
    return labels


def parse_labels_tf(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return ({name: description}, {name: colour}) from the Tofu resources."""
    descriptions: dict[str, str] = {}
    colours: dict[str, str] = {}
    for body in TF_RESOURCE.findall(text):
        attrs = dict(TF_ATTR.findall(body))
        name = attrs.get("name")
        if not name:
            sys.exit(f"{LABELS_TF}: a github_issue_label resource declares no name")
        descriptions[name] = attrs.get("description", "")
        colours[name] = attrs.get("color", "")
    if not descriptions:
        sys.exit(f"{LABELS_TF}: no github_issue_label resources found")
    return descriptions, colours


def main() -> int:
    table = parse_skill_table(SKILL.read_text(encoding="utf-8"))
    declared, colours = parse_labels_tf(LABELS_TF.read_text(encoding="utf-8"))

    problems: list[str] = []

    for name in sorted(set(table) - set(declared)):
        problems.append(
            f"`{name}` is in the skill's table but not declared in labels.tf, "
            f"so an apply will not create it"
        )
    for name in sorted(set(declared) - set(table)):
        problems.append(
            f"`{name}` is declared in labels.tf but missing from the skill's "
            f"table, so no session will ever apply it"
        )
    for name in sorted(set(table) & set(declared)):
        if table[name] != declared[name]:
            problems.append(
                f"`{name}` has two descriptions:\n"
                f"    skill: {table[name]}\n"
                f"    tofu:  {declared[name]}"
            )

    for name in sorted(declared):
        if not colours.get(name):
            problems.append(f"`{name}` declares no colour in labels.tf")
    seen: dict[str, str] = {}
    for name in sorted(declared):
        colour = colours.get(name)
        if colour and colour in seen:
            problems.append(
                f"`{name}` and `{seen[colour]}` share the colour {colour}; "
                f"a label is told apart by it"
            )
        elif colour:
            seen[colour] = name

    if problems:
        print("the label standard disagrees with itself:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"label standard: {len(table)} labels agree between the skill and the Tofu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
