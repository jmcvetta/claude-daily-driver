#!/usr/bin/env python3
"""Append each `Agent` dispatch's `subagent_type` to a roster file.

Wired as a `PreToolUse` hook by the `review-depth` tasks; event JSON on stdin.
The reasoning — why the observation is taken here rather than by a criterion,
and what the roster does and does not prove — is in `evals/README.md` under
"Grading dispatch". It is deliberately not in this file: this directory is
mounted inside the sandbox the agent under test is working in, so a docstring
here is an answer key one `cat` away.

Three constraints, in the order they bite:

1. **Never break the call it observes.** A `PreToolUse` hook that exits
   non-zero blocks the tool call, so every failure path here exits 0. (The
   invocation is guarded too — see the hook command in the task YAML.)
2. **Emit nothing.** Another `PreToolUse` hook on this same event returns an
   `updatedInput`; a second one printing JSON is a chance to disagree with it.
   Silence composes.
3. **Resolve the roster from this file**, not from the working directory,
   which is the session's and not this script's business.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Beside this script, which the fixtures keep out of git via
# `.git/info/exclude`, so recording never dirties the worktree under review.
ROSTER = Path(__file__).resolve().parent / "dispatched.txt"

# `Agent` is current; `Task` is what the same tool was called for years. The
# hook matcher admits both, so this does too.
SUBAGENT_KEY = "subagent_type"


def main() -> int:
    try:
        event = json.load(sys.stdin)
        requested = (event.get("tool_input") or {}).get(SUBAGENT_KEY)
        if isinstance(requested, str) and requested:
            with ROSTER.open("a", encoding="utf-8") as handle:
                handle.write(f"{requested}\n")
    except Exception:  # noqa: BLE001 -- see constraint 1 above
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
