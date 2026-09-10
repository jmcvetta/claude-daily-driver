#!/usr/bin/env python3
"""Close the AskUserQuestion widget, so the question is asked in the chat reply.

`AskUserQuestion` renders a multiple-choice widget. On a phone it is harder to
work with than plain text, and the operator's answer to it is the same every
time: ask in chat instead. A preference answered the same way every time is not
a judgement, and prose that asks for it is prose that can be read and not
followed. So the tool is denied, and the denial reason carries the instruction
that replaces it.

This is deliberately not a rule in `rules/constitution.md`. That file states
its own admission test — a rule earns its place only if it changes behaviour in
most sessions, hangs off a nameable moment, and says something the harness does
not already say — and it is paid for in tokens in every session and every
subagent, forever. A hook costs nothing until the moment it fires, and it
cannot be read and ignored. `docs/notes/0009-deny-the-question-widget.md` is
the decision.

Nor does it duplicate the `judgement-call` skill, which fires at the same
moment. That skill decides **whether** a question is the user's to answer. This
hook decides **how** a surviving question is put. The two are ordered rather
than overlapping, and the denial reason says so.

Usage: ask-in-chat.py

The event JSON arrives on stdin and the hook's answer goes to stdout. See
`hooks/hooks.json` for the wiring, and `scripts/check-ask-in-chat.py` for the
acceptance test.

No third-party imports. This runs on a laptop, on a web worker, and out of a
test harness; a dependency install between those is a place for them to differ.
"""

from __future__ import annotations

import json
import sys

# The one tool this hook is wired to. The matcher in `hooks.json` is what
# selects it; the name here is only used to notice that the matcher has gone
# wrong — see `decide()`.
TOOL = "AskUserQuestion"

# What Claude is told when the call is denied. Claude Code shows this text and
# nothing else, so it is written to be acted on rather than read: the tool is
# shut, a retry buys nothing, and here is the thing to do instead.
REASON = (
    "The AskUserQuestion widget is closed in this configuration. Calling it "
    "again will be denied in the same way, so do not retry it.\n\n"
    "Ask the same question in your chat reply instead. Write the question as "
    "prose, give the options as a short list, and name the one you recommend "
    "and why. The user answers in chat.\n\n"
    "Check first whether the question needs asking at all. The "
    "`judgement-call` skill's gate settles most of these — where the correct, "
    "standard way already picks the answer, make the call, say in one line "
    "which way it went, and carry on. This hook governs how a question that "
    "survives that gate is put, not whether it is worth putting."
)


def decide(event: dict) -> tuple[dict, str | None]:
    """The hook's answer for one event, and the warning that rides with it.

    Returns `(payload, None)` for the denial, and `(payload, note)` where the
    call was let through and somebody should know why.

    The rule is: deny unless the event positively names a different tool. The
    matcher in `hooks.json` is what identifies the call, so an event this
    script cannot read does not overturn it — an empty or malformed event is
    still an `AskUserQuestion` call, and failing open there would hand the
    widget back on exactly the harness glitch nobody would notice.

    An event that names some *other* tool is the one case that is let through.
    That means the matcher is wrong, and denying an unrelated tool on a broken
    matcher is the worse failure: it could shut off something the session needs
    and give a misleading reason for it.
    """
    tool = event.get("tool_name")
    if isinstance(tool, str) and tool != TOOL:
        note = (
            f"ask-in-chat was invoked on {tool!r}, not {TOOL!r}, so the call "
            f"was allowed. The PreToolUse matcher in hooks/hooks.json is wrong."
        )
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse"}}, note

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    }, None


def emit(payload: dict, note: str | None) -> int:
    """Write the hook's answer, and be loud about a misfire without being fatal.

    Exit 0 on both paths. A nonzero exit risks the harness discarding the
    stdout that carries the decision, which would trade a denial Claude can
    read for one it cannot.
    """
    if note is not None:
        payload["systemMessage"] = f"daily-driver: {note}"
        print(f"ask-in-chat: {note}", file=sys.stderr)

    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


def read_event() -> dict:
    """The event on stdin, or an empty one where it cannot be read.

    Every road to unusable input ends in the same place — a dict with no
    `tool_name`, which `decide()` reads as "trust the matcher and deny". Both
    roads are still said out loud on stderr, because a harness sending garbage
    is worth knowing about even where the answer is unchanged.
    """
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as error:
        print(f"ask-in-chat: unparseable event JSON: {error}", file=sys.stderr)
        return {}

    # Well-formed JSON that is not an object — `null`, `[]`, a bare string —
    # parses without complaint and then fails on the first `.get()`.
    if not isinstance(event, dict):
        print(
            f"ask-in-chat: event JSON is {type(event).__name__}, not an object",
            file=sys.stderr,
        )
        return {}

    return event


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        # A typo in hooks.json lands here. Exit 2 is the loud answer, and on
        # PreToolUse it blocks the call anyway, so a misconfigured hook fails
        # towards the behaviour it was installed for rather than away from it.
        print(f"usage: {argv[0].rsplit('/', 1)[-1]}", file=sys.stderr)
        return 2

    return emit(*decide(read_event()))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
