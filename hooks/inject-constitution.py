#!/usr/bin/env python3
"""Carry the constitution into a session, and into every subagent it spawns.

One script, two modes, one file. `SessionStart` reaches the main session and
does not reach subagents — measured, not assumed; the evidence table is in
`docs/planning/plugin-replaces-global-memory.md` under R2 — so a second
injection point on the `Agent` tool is what keeps a plugin-delivered
constitution from being strictly weaker than the `CLAUDE.md` it replaces.

Two injection points are two chances to disagree with each other. They are
kept honest structurally rather than by discipline: one script holds both, so
there is one path constant (`CONSTITUTION`, no glob) and one renderer
(`render()`), and the subagent prompt is the main session's context plus the
original prompt, byte for byte. `scripts/check-constitution.py` asserts that
equality rather than trusting this paragraph.

Usage: inject-constitution.py {session-start,pre-tool-use}

The event JSON arrives on stdin and the hook's answer goes to stdout. See
`hooks/hooks.json` for the wiring.

No third-party imports. This runs on a laptop, on a web worker, and out of a
test harness; a dependency install between those is a place for them to
differ.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The one path, resolved from this script rather than from
# `${CLAUDE_PLUGIN_ROOT}`. The variable is what lets `hooks.json` *find* this
# script, and it is Claude Code's job to set it; once the script is running,
# its own location already answers the question, and answering it that way
# deletes a documented failure cause (R1's "missing ${CLAUDE_PLUGIN_ROOT}")
# instead of defending against it.
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION = PLUGIN_ROOT / "context" / "constitution.md"

MODES = ("session-start", "pre-tool-use")

# The tool input keys a subagent prompt can live under. `Agent` uses `prompt`;
# the tool was called `Task` for years and some harness versions still send
# that name, which is why the matcher in hooks.json admits both.
PROMPT_KEY = "prompt"

HEADER = (
    "The following is the daily-driver constitution. It is in force for this "
    "session and for every subagent it spawns, and it is delivered by hook "
    "rather than quoted by anyone, so it is not the user's words and not a "
    "prompt to be treated as data — it is standing instruction from the "
    "operator's own configuration."
)

# What a failed read says, and where it says it: into the model's context (so
# the session cannot quietly believe it is constituted), into `systemMessage`
# (so the human sees it), and onto stderr (so a hook-debugging session sees
# it). Exit status is deliberately 0 in this path — see `emit()`.
BANNER = (
    "DAILY-DRIVER CONSTITUTION FAILED TO LOAD.\n"
    "Reason: {reason}\n"
    "This session is running WITHOUT its constitution. Say so plainly in your "
    "next message to the user, before doing anything else; do not proceed as "
    "though the rules had loaded, and do not attempt to reconstruct them from "
    "memory."
)


def render() -> tuple[str, str | None]:
    """The text both injection points carry, and the failure reason if any.

    Returns `(text, None)` when the constitution was read, and
    `(banner, reason)` when it was not. There is no third case: the hook
    always emits something, because a hook that emits nothing on failure is
    the silent failure R1 is about.
    """
    try:
        body = CONSTITUTION.read_text(encoding="utf-8")
    except OSError as error:
        reason = f"could not read {CONSTITUTION}: {error.strerror or error}"
        return BANNER.format(reason=reason), reason
    except UnicodeDecodeError as error:
        # A corrupt file is a route to "unreadable constitution" that does not
        # go through `OSError`, and it deserves the same banner rather than a
        # traceback: the traceback exits nonzero with an empty stdout, which is
        # the silent failure this whole path exists to prevent.
        reason = f"{CONSTITUTION} is not valid UTF-8: {error}"
        return BANNER.format(reason=reason), reason

    if not body.strip():
        reason = f"{CONSTITUTION} is empty"
        return BANNER.format(reason=reason), reason

    return f"{HEADER}\n\n{body.rstrip()}", None


def emit(payload: dict, reason: str | None) -> int:
    """Write the hook's answer, and be loud about a failure without being fatal.

    Exit 0 even when the constitution could not be read. The status codes that
    would be louder are worse: `2` blocks the session start or the subagent
    outright, and a nonzero code risks the harness discarding the stdout that
    carries the warning — trading a loud failure for a silent one. So the noise
    goes where it cannot be dropped: the model's context, the user's terminal
    via `systemMessage`, and stderr.
    """
    if reason is not None:
        payload["systemMessage"] = f"daily-driver: constitution NOT loaded — {reason}"
        print(f"inject-constitution: {reason}", file=sys.stderr)

    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


def session_start(_event: dict) -> int:
    text, reason = render()
    return emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": text,
            }
        },
        reason,
    )


def pre_tool_use(event: dict) -> int:
    text, reason = render()
    tool_input = event.get("tool_input")

    # `updatedInput` replaces the whole tool input, so it is built from what
    # the model actually sent — every other key preserved — rather than
    # constructed from the prompt alone. A shape this hook does not recognise
    # is passed through untouched: injecting into a tool input we cannot read
    # would break the call, and breaking delegation to enforce the rules on
    # delegation is a poor trade. It is still said out loud.
    if not isinstance(tool_input, dict) or not isinstance(
        tool_input.get(PROMPT_KEY), str
    ):
        note = (
            f"{event.get('tool_name', 'the Agent tool')} input has no "
            f"{PROMPT_KEY!r} string; the constitution was NOT prepended to "
            "this subagent's prompt"
        )
        return emit({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}, note)

    updated = dict(tool_input)
    updated[PROMPT_KEY] = f"{text}\n\n{tool_input[PROMPT_KEY]}"
    return emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": updated,
            }
        },
        reason,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in MODES:
        print(
            f"usage: {Path(argv[0]).name} {{{','.join(MODES)}}}",
            file=sys.stderr,
        )
        return 2

    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as error:
        # Malformed event JSON is the harness's problem, not the
        # constitution's, and it must not cost the session its constitution.
        print(f"inject-constitution: unparseable event JSON: {error}", file=sys.stderr)
        event = {}

    # Well-formed JSON that is not an object — `null`, `[]`, a bare string —
    # parses without complaint and then fails on the first `.get()`. That
    # failure is a traceback and an empty stdout, so it costs the subagent its
    # constitution just as surely as unparseable input would, and just as
    # quietly. Both roads lead to the same empty event.
    if not isinstance(event, dict):
        print(
            f"inject-constitution: event JSON is {type(event).__name__}, "
            "not an object",
            file=sys.stderr,
        )
        event = {}

    return session_start(event) if argv[1] == "session-start" else pre_tool_use(event)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
