#!/usr/bin/env python3
"""Record what `review` routed to, into two files beside this script.

Reads one hook event as JSON on stdin. Two tool families are watched, because
the skill has two kinds of route and they are observed differently:

* `Agent` / `Task` — the `subagent_type` is appended to `dispatched.txt`. This
  is how the planning route is seen: `planning-fitness-reviewer` is the only
  agent the skill dispatches.
* `Skill` — the skill name and its arguments are appended to
  `invocations.txt`. This is how every other route is seen, because the
  analysis is the built-in `/code-review` at an effort level and the level is
  the whole routing decision. Every `Skill` call is recorded, not only
  `/code-review`; the criteria anchor on the name.

Both files are line-oriented and read with `re.MULTILINE`, which is what the
two normalisations below are for. See `evals/README.md` for what this is for
and what its output is used for.

Exits 0 on every path, including every failure, and writes nothing to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROSTER = HERE / "dispatched.txt"
INVOCATIONS = HERE / "invocations.txt"

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
            # Safe unnormalised: the CLI's own schema rejects a newline in a
            # subagent name. `args` below carries no such guard.
            _append(ROSTER, requested)

        skill = tool_input.get(SKILL_KEY)
        if isinstance(skill, str) and skill:
            args = tool_input.get(ARGS_KEY)
            args = args if isinstance(args, str) else ""
            # Two normalisations, both load-bearing.
            #
            # The leading slash: the CLI accepts `skill: "/code-review"` and
            # strips it *after* `checkPermissions` has returned the input, so
            # what a `PreToolUse` hook sees is whatever the model typed — and
            # `SKILL.md` writes the name with the slash everywhere, which is
            # the likeliest thing for it to copy. Unstripped, every criterion
            # anchored on `^(?:[A-Za-z0-9_.-]+:)?code-review` misses, and it
            # misses in the direction that hides the failure: the positives
            # read as a skill that never routed, the negatives pass while a
            # review ran.
            #
            # The whitespace collapse: `args` is arbitrary model-authored text
            # and this file is read with `re.MULTILINE`, so a multi-line
            # argument to any skill would write extra lines that a criterion
            # scores as records of their own. The instrument must not be
            # forgeable by the payload it observes.
            line = f"{skill.lstrip('/')} {args}"
            _append(INVOCATIONS, " ".join(line.split()))
    except Exception:  # noqa: BLE001 -- never fail; see evals/README.md
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
