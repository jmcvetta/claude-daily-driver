#!/usr/bin/env python3
"""A shipped `SKILL.md` names no harness's routes in its body.

The skills here run on two harnesses -- Claude Code and Omp -- and the routes
differ: `mcp__github__update_pull_request` against `gh pr ready`,
`${CLAUDE_PLUGIN_ROOT}` against `skill://`, a subscription and a `send_later`
against a blocking `run_watch`. Issue #146 settled where each half lives. The
`SKILL.md` body stays semantic: it names the operation in words -- "mark the
draft ready", "wait for CI on the pushed head" -- and points at
`skills/<name>/references/claude.md` or `skills/<name>/references/omp.md` for
the call. A route written back into the body is not wrong on the harness it was
written for, which is exactly why nothing else catches it: it reads correctly,
and it is silently wrong on the other harness.

WHAT IT FLAGS

    A harness-specific token in the body of a shipped `skills/*/SKILL.md`:

        mcp__                     a Claude MCP tool, either server
        AskUserQuestion           Claude's question widget
        /code-review              Claude's built-in review surface
        $CLAUDE_PLUGIN_ROOT      Claude's injected plugin root, braced or not
        daily_driver_             an Omp runtime-adapter tool
        run_watch                 the Omp `github` tool's blocking watch
        skill://                  Omp's injected skill-directory path

    The `description:` frontmatter is exempt, and that exemption is the point
    rather than a concession: the description is what triggers the skill, so a
    skill that fires on a tool call has to name that tool call -- both
    harnesses' -- to fire on either. Everything below the frontmatter is body.

    Reference files are not scanned at all. Naming routes is what they are for.

WHAT IT DOES NOT CATCH

    A route described in words rather than spelled. "Subscribe to the pull
    request and let the events wake the session" is Claude's mechanism with the
    tool name filed off, and it reads as neutral prose to any pattern. This
    check makes the loud half loud; the quiet half is still a reviewer's job.

    That a reference file exists for a skill whose body points at one. A dead
    link is `claude plugin validate`'s business and a reader's, not this one's.

No third-party imports, for the reason `check-manifests.py` gives: this runs
from a Makefile on a laptop and from CI, and a dependency install between the
two is a place for them to differ.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# One pattern per rule, named, so a failure says which rule it broke rather
# than which alternation branch matched.
ROUTES = {
    "mcp__": re.compile(r"mcp__"),
    "AskUserQuestion": re.compile(r"AskUserQuestion"),
    "/code-review": re.compile(r"/code-review"),
    "${CLAUDE_PLUGIN_ROOT}": re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?"),
    "daily_driver_": re.compile(r"daily_driver_"),
    "run_watch": re.compile(r"run_watch"),
    "skill://": re.compile(r"skill://"),
}


def body_of(text: str) -> tuple[str, int]:
    """Return a skill's body and the line the body starts on.

    The frontmatter is the block between the opening `---` and the next `---`
    on a line of its own. A file without one is all body, which is the safe
    reading: it exempts nothing.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, 1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :]), i + 2
    return text, 1


def main() -> int:
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skills:
        print("no skills/*/SKILL.md found; refusing to pass vacuously")
        return 1

    failures = []
    for path in skills:
        body, offset = body_of(path.read_text(encoding="utf-8"))
        for lineno, line in enumerate(body.splitlines(), start=offset):
            for name, pattern in ROUTES.items():
                if pattern.search(line):
                    rel = path.relative_to(ROOT)
                    failures.append(f"{rel}:{lineno}: {name} — {line.strip()}")

    if failures:
        print("harness-specific routes in a SKILL.md body:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            "\nMove the route to skills/<name>/references/claude.md or"
            "\nreferences/omp.md, and name the operation in words in the body."
            "\nThe description: frontmatter is the one place a route may stay.",
            file=sys.stderr,
        )
        return 1

    print(f"SKILL.md bodies are harness-neutral; {len(skills)} skill(s) checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
