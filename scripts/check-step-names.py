#!/usr/bin/env python3
"""A step is cited by its name, never by its number.

Several files here lay out a numbered sequence -- `undertake`'s eleven steps,
`review-cycle`'s three stages, `session-title`'s four cuts -- and other files
cite them. A number is positional: insert one step and every citation of every
later step is silently wrong, in prose that still reads exactly like prose that
is right. It has already cost once. 8354f33 added a step in the middle of
`undertake` and had to hand-chase two citations in other files; nothing would
have caught the one that got missed.

So the numbers stay for reading -- in the sequence table, and as the `4 — Cut
the branch` prefix on a heading -- and every *reference* names the step
instead. A name survives the insertion that renumbers everything after it.
That is the rule this script enforces, and
`docs/notes/0004-steps-are-cited-by-name.md` is the decision behind it.

WHAT IT FLAGS

    A sequence noun followed by a number: "step 7", "stage 2", "phases 2-4",
    "Rules 1 and 2". Nothing else -- a heading written `7 — Open the draft` and
    a table row written `| 7 |` do not match, which is what leaves the numbers
    their reading job.

THE ESCAPE HATCH

    A numbering this repository does not own cannot be renamed here. A file
    exempts one noun, with its reason, in a comment anywhere in it:

        <!-- step-names: external phase — the phases are issue #35's. -->

    The exemption is per noun, not per file: `docs/notes/0001` cites issue
    #35's phases throughout and still had a stale `stage 2` pointing at
    `review-cycle`, which is exactly the citation a file-wide waiver would have
    hidden.

WHY THE SELF-TEST RUNS EVERY TIME

    This check fails silently in the direction that matters. A regex that has
    stopped matching reports a clean repository, which is indistinguishable
    from a clean repository -- so a suite that could be skipped, or left
    un-run on a laptop, would not be protecting anything. `selftest` is
    therefore not a flag: it runs before the scan on every invocation, costs
    microseconds, and there is no way to reach the scan without it.

No third-party imports: this runs from a Makefile on a laptop and from CI, and
a dependency install between the two is a place for them to differ.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The nouns a numbered sequence is written with here. Each is checked in the
# singular and the plural, so "step 3" and "Steps 3 through 9" both land.
NOUNS = ("step", "stage", "phase", "rule", "item")

# Prose only. Skill and agent bodies are Markdown; eval cases carry their
# prose in YAML `description` blocks, and a stale citation there is a stale
# citation in the thing that documents what the suite measures.
SUFFIXES = (".md", ".yaml", ".yml")

# Generated from commit messages by release-please. Rewriting it would falsify
# the record, and nothing reads it as an instruction.
SKIP = ("CHANGELOG.md",)

CITATION = re.compile(rf"\b({'|'.join(NOUNS)})s?\s+\d", re.IGNORECASE)

# `<!-- step-names: external phase — reason -->`. The noun is what the waiver
# covers; the trailing text is the reason, required so that a waiver has to say
# whose numbering it is deferring to.
WAIVER = re.compile(
    rf"step-names:\s*external\s+({'|'.join(NOUNS)})s?\b[^\S\n]*(?P<reason>[^\n>]*)",
    re.IGNORECASE,
)

# What the two patterns above are asserted to do, on every run. The flagged
# half is the register the repository actually writes citations in; the clean
# half is everything the numbers are still allowed to do, and is the half that
# would break first if the pattern were widened carelessly.
FLAGGED = (
    "runs this round between its step 7",
    "Steps 3 through 9 shift up by one",
    "starts at stage 2",
    "Phase 1 runs over the `[judgment]` items",
    "Rules 1 and 2 are one rule",
    "needs step 1 alone",
    "the numbers in #35 phases 3-4",
)
CLEAN = (
    "| 7 | `Open the draft` | `pr` |",
    "7 — Open the draft",
    "runs this round between its `Open the draft` and `Ready for review` steps",
    "1. **Tracker prefix.** Drop a leading prefix",
    "eleven steps, and this skill is the order they run in",
    "step by step, without stopping",
)


def selftest() -> None:
    for text in FLAGGED:
        assert CITATION.search(text), f"selftest: not flagged: {text!r}"
    for text in CLEAN:
        assert not CITATION.search(text), f"selftest: wrongly flagged: {text!r}"

    assert waived("<!-- step-names: external phase — issue #35's. -->") == {"phase"}
    assert waived("<!-- step-names: external phases — issue #35's. -->") == {"phase"}
    # A waiver covers the noun it names and no other.
    assert "stage" not in waived("<!-- step-names: external phase — #35's. -->")
    # A waiver with no reason is not a waiver.
    assert waived("<!-- step-names: external phase -->") == set()


def tracked() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [
        ROOT / name
        for name in out.split("\0")
        if name and name.endswith(SUFFIXES) and name not in SKIP
    ]


def waived(text: str) -> set[str]:
    """The nouns this file has waived, lowercased and singular."""
    nouns = set()
    for match in WAIVER.finditer(text):
        if match.group("reason").strip(" -—–:"):
            nouns.add(match.group(1).lower().rstrip("s"))
    return nouns


def main() -> int:
    selftest()

    errors: list[str] = []
    files = tracked()
    for path in files:
        text = path.read_text(encoding="utf-8")
        exempt = waived(text)
        where = path.relative_to(ROOT)
        for number, line in enumerate(text.splitlines(), 1):
            for match in CITATION.finditer(line):
                if match.group(1).lower() in exempt:
                    continue
                errors.append(
                    f"{where}:{number}: {match.group(0).strip()!r} cites a step "
                    f"by number; name it instead"
                )

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        print(
            "\nSteps are cited by name so that inserting one does not "
            "invalidate every\nlater citation. See "
            "docs/notes/0004-steps-are-cited-by-name.md.",
            file=sys.stderr,
        )
        return 1
    print(f"steps are cited by name; {len(files)} file(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
