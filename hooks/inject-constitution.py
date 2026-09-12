#!/usr/bin/env python3
"""Carry the constitution into a session, and into every subagent it spawns.

One script, three modes, one file. `SessionStart` reaches the main session and
does not reach subagents — measured, not assumed; the evidence table is in
`docs/planning/plugin-replaces-global-memory.md` under R2 — so a second
injection point on the `Agent` tool is what keeps a plugin-delivered
constitution from being strictly weaker than the `CLAUDE.md` it replaces.

`SubagentStart` is the third injection point, and it is there for Codex. Codex
delegates through `multi_agent_v1` rather than through `Agent` or `Task`, so
the `PreToolUse` matcher reaches nothing on that harness and `SubagentStart` is
the only route a Codex subagent's constitution can arrive by. Claude Code fires
that event too and honours the same `additionalContext`, so a Claude Code
subagent is handed the constitution twice — once prepended to its prompt by
`pre-tool-use`, once as context by this mode. That duplicate is the price of
one `hooks.json` serving both harnesses: `SubagentStart` carries only
`agent_id` and `agent_type`, so neither mode can see that the other has already
fired, and sniffing the harness to suppress one of them is a workaround this
file does not carry.

The file lives at `rules/constitution.md`, the one source for both Claude Code
and Oh My Pi. Omp's rule provider reads it from `rules/`, strips the
`alwaysApply` frontmatter and injects the body into the main agent and every
subagent; this hook reads the same file, validates that exact frontmatter and
strips it, so the two harnesses inject the identical body.

Three injection points are three chances to disagree with each other. They
are kept honest structurally rather than by discipline: one script holds all
three, so there is one path constant (`CONSTITUTION`, no glob) and one renderer
(`render()`), and the subagent prompt is the main session's context plus the
original prompt, byte for byte. `scripts/check-constitution.py` asserts that
equality rather than trusting this paragraph.

Usage: inject-constitution.py {session-start,subagent-start,pre-tool-use}

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
CONSTITUTION = PLUGIN_ROOT / "rules" / "constitution.md"

# The frontmatter the canonical file must carry, exactly. Omp's rule provider
# reads `rules/*.md`, strips this frontmatter and injects the body into the
# main agent and every subagent when `alwaysApply` is true — there is no
# `agents` filter, so `alwaysApply: true` is the only metadata the file may
# have. Claude does not read the frontmatter at all; this hook strips it so
# Claude's body is identical to Omp's, and validates it so a drift in the Omp
# contract is a loud failure rather than a silent change of behaviour. The
# block is matched exactly: no other key, no extra whitespace, no shorthand.
FRONTMATTER_OPEN = "---"
FRONTMATTER_BLOCK = "alwaysApply: true"

# The modes, and the event name each one echoes back. The echo is a contract
# rather than a courtesy: Codex rejects a handler whose
# `hookSpecificOutput.hookEventName` is not the event it was sent — the output
# is dropped and the hook reports `Failed` — and Claude Code keys its own
# reading of the output off the same field.
MODES = {
    "session-start": "SessionStart",
    "subagent-start": "SubagentStart",
    "pre-tool-use": "PreToolUse",
}

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
    """The text every injection point carries, and the failure reason if any.

    Returns `(text, None)` when the constitution was read, and
    `(banner, reason)` when it was not. There is no third case: the hook
    always emits something, because a hook that emits nothing on failure is
    the silent failure R1 is about.
    """
    try:
        text = CONSTITUTION.read_text(encoding="utf-8")
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

    if not text.strip():
        reason = f"{CONSTITUTION} is empty"
        return BANNER.format(reason=reason), reason

    # The canonical file carries frontmatter for Omp. Claude must get the body
    # alone — never the YAML delimiters or the metadata — so the frontmatter is
    # stripped here, and validated so that a file whose metadata no longer
    # says `alwaysApply: true` is a loud failure rather than a silent one.
    # This is the same strip Omp's rule provider performs; the two harnesses
    # inject the same body, which is the point of the shared source.
    lines = text.splitlines()
    if not lines or lines[0] != FRONTMATTER_OPEN:
        reason = f"{CONSTITUTION} is missing its {FRONTMATTER_OPEN} frontmatter"
        return BANNER.format(reason=reason), reason
    try:
        close = next(
            i for i in range(1, len(lines)) if lines[i] == FRONTMATTER_OPEN
        )
    except StopIteration:
        reason = f"{CONSTITUTION} frontmatter is never closed"
        return BANNER.format(reason=reason), reason

    found = "\n".join(lines[1:close])
    if found != FRONTMATTER_BLOCK:
        reason = (
            f"{CONSTITUTION} frontmatter is {found!r}, expected exactly "
            f"{FRONTMATTER_BLOCK!r}"
        )
        return BANNER.format(reason=reason), reason

    # Omp trims the body after extracting frontmatter. Match that behaviour,
    # including its removal of the conventional blank line after the closing
    # delimiter, so both harnesses receive the same bytes.
    body = "\n".join(lines[close + 1 :]).strip()
    if not body.strip():
        reason = f"{CONSTITUTION} is empty"
        return BANNER.format(reason=reason), reason

    return f"{HEADER}\n\n{body}", None


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


def additional_context(event_name: str) -> int:
    """Deliver the constitution as context, for an event whose output takes it.

    `SessionStart` and `SubagentStart` differ in nothing but the name they echo
    and neither reads its event, so they share one body. Two copies would be
    two texts to keep equal, and the equality is the whole point:
    `scripts/check-constitution.py` asserts that every injection point carries
    the same bytes.
    """
    text, reason = render()
    return emit(
        {
            "hookSpecificOutput": {
                "hookEventName": event_name,
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

    if argv[1] == "pre-tool-use":
        return pre_tool_use(event)
    return additional_context(MODES[argv[1]])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
