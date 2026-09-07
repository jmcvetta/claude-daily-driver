#!/usr/bin/env python3
"""Record what `review` routed to, into two files beside this script.

Reads one hook event as JSON on stdin. Two tool families are watched, because
the skill has two kinds of route and they are observed differently:

* `Agent` / `Task` — the `subagent_type` is appended to `dispatched.txt`. This
  is how the planning route is seen: `planning-fitness-reviewer` is the only
  agent the skill dispatches.
* `Skill` — the skill name and its arguments are appended, space-joined, to
  `code-review.txt`. This is how every other route is seen, because the
  analysis is the built-in `/code-review` at an effort level and the level is
  the whole routing decision.

Exits 0 on every path, including every failure, and writes nothing to stdout.
See `evals/README.md` for what this is for and what its output is used for.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROSTER = HERE / "dispatched.txt"
INVOCATIONS = HERE / "code-review.txt"

SUBAGENT_KEY = "subagent_type"
SKILL_KEY = "skill"
ARGS_KEY = "args"


def _append(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def main() -> int:
    try:
        event = json.load(sys.stdin)
        tool_input = event.get("tool_input") or {}

        requested = tool_input.get(SUBAGENT_KEY)
        if isinstance(requested, str) and requested:
            _append(ROSTER, requested)

        skill = tool_input.get(SKILL_KEY)
        if isinstance(skill, str) and skill:
            args = tool_input.get(ARGS_KEY)
            args = args if isinstance(args, str) else ""
            _append(INVOCATIONS, f"{skill} {args}".strip())
    except Exception:  # noqa: BLE001 -- never fail; see evals/README.md
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
