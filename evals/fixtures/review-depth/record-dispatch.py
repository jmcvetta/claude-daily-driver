#!/usr/bin/env python3
"""Record which subagent each `Agent` dispatch asked for, as it happens.

`review-depth` grades **which agents were dispatched**, and on `coder_eval`
0.11.6 that fact is not observable through the criteria:

- `command_executed` matches its pattern against `json.dumps(parameters)`
  truncated to 2000 characters (`_MAX_PATTERN_SEARCH_LEN`), and the `Agent`
  tool's schema orders its keys `description, prompt, subagent_type`. Every
  panel dispatch carries the diff in `prompt`, so on any diff of consequence
  `subagent_type` sits past the window. The criterion then reports "not
  dispatched" for a dispatch that happened — silently inverting a negative
  control and zeroing a positive.
- `llm_judge` / `agent_judge` do not see it either: their tool-call summariser
  renders an `Agent` call as its `description` field, which is a three-word
  label the model writes.

So the observation is taken where it is complete: a `PreToolUse` hook, wired
through the task's `claude_settings` and therefore part of the *instrument*
rather than of the plugin under test. It fires in both arms, sees the tool
input verbatim, and appends one line per dispatch to a file a
`file_matches_regex` criterion can read.

This is not the mode line. The mode line is what the skill *says* it decided;
this is the argument it passed to the tool. A skill announcing "Standard" and
dispatching the Full panel fails here and passed there.

Design constraints, in the order they bite:

1. **Never break the call it observes.** Any failure exits 0 with empty stdout,
   which Claude Code reads as "no opinion". A recorder that can veto a dispatch
   would be measuring itself.
2. **Emit nothing.** The plugin's own `PreToolUse` hook on `Agent` returns
   `updatedInput` carrying the constitution; a second hook printing JSON on the
   same event is a chance to disagree with it. Silence composes.
3. **Resolve the roster from this file, not from the working directory.** Hooks
   run with the session's cwd, which is the sandbox root today and is not this
   script's business either way.

Usage: wired as a PreToolUse hook command; event JSON on stdin.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Beside this script, which the fixtures keep out of git via
# `.git/info/exclude` — so recording a dispatch never dirties the worktree the
# skill under test is reading.
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
