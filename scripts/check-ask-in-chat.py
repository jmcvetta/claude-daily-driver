#!/usr/bin/env python3
"""The acceptance test for the hook that closes the AskUserQuestion widget.

The constitution carries the rule *code without tests is broken*, and a hook
is the worst place to break that rule: it runs in one line of `hooks.json`
that nothing else reads, on an event nobody watches, and its failure mode is
the widget quietly coming back. So the hook is run here exactly as the harness
runs it — the real script, synthetic event JSON on stdin — and the answer is
asserted on.

No model is needed for any of it, so it belongs in `make check` and in a CI
that holds no credentials. There is no live half: unlike the constitution,
which has to be *believed* by a session before it does anything, a denial is
enforced by the harness. What a session then writes instead is
`judgement-call`'s business and the eval suite's.

No third-party imports: this runs from a Makefile on a laptop and from CI, and
a dependency install between the two is a place for them to differ.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
SCRIPT = ROOT / "hooks" / "ask-in-chat.py"

TOOL = "AskUserQuestion"

# Tool names the matcher must leave alone. The last two are the point: a
# matcher written without anchors — `AskUserQuestion` rather than
# `^AskUserQuestion$` — matches both, and denying a tool nobody asked about is
# a failure that reads like a broken session rather than like a wrong hook.
NOT_THIS_TOOL = (
    "Bash",
    "Edit",
    "Agent",
    "Task",
    "AskUserQuestionLater",
    "MyAskUserQuestion",
)

# The two instructions the denial reason carries, named here so that a rewrite
# which drops one turns this red. Prose in the script is free to change; these
# are what the change has to keep saying — where to put the question, and that
# calling again buys nothing.
REQUIRED_IN_REASON = ("chat", "retry")

EVENT = {
    "session_id": "check-ask-in-chat",
    "cwd": str(ROOT),
    "hook_event_name": "PreToolUse",
    "tool_name": TOOL,
    "tool_input": {
        "questions": [
            {
                "question": "Which retry backoff should the client use?",
                "header": "Backoff",
                "multiSelect": False,
                "options": [
                    {"label": "Exponential", "description": "Doubling, with a cap."},
                    {"label": "Fixed", "description": "One interval, every time."},
                ],
            }
        ]
    },
    "tool_use_id": "toolu_check",
}

# Stdin the harness should never send, in the two kinds it comes in: input that
# does not parse, and input that parses into something that is not an event.
# Every one of them must still deny — the matcher already identified the call,
# and a hook that hands back the widget on a malformed event is a hook that
# fails open on the one day nobody is looking.
BAD_STDIN = ("", "not json at all", "[]", "null", '"hi"', "5", "{}")


class Failed(Exception):
    """A check that did not hold. The message is the report."""


def spawn(*args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
    """Run the hook script as the harness runs it: argv, stdin, and nothing else.

    `CLAUDE_PLUGIN_ROOT` is stripped deliberately. The harness sets it, the
    script must not need it, and clearing it here is the regression test for
    that.
    """
    try:
        return subprocess.run(
            [str(SCRIPT), *args],
            input=stdin,
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"},
        )
    except OSError as error:
        raise Failed(
            f"{SCRIPT} could not be executed ({error.strerror or error}); the "
            f"hook command runs it directly"
        ) from None


def run_hook(errors: list[str], where: str, stdin: str) -> dict | None:
    """Invoke the hook and insist on a usable answer, or report and return None."""
    result = spawn(stdin=stdin)
    if result.returncode != 0:
        errors.append(
            f"{where}: exited {result.returncode}; the decision rides on "
            f"stdout, which a nonzero exit puts at risk\n  stderr: "
            f"{result.stderr.strip() or '(empty)'}"
        )
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        errors.append(
            f"{where}: stdout is not JSON ({error}); the harness would ignore "
            f"it and the widget would open\n  stdout: {result.stdout[:200]!r}"
        )
        return None
    if not isinstance(payload, dict):
        errors.append(f"{where}: emitted {type(payload).__name__}, not an object")
        return None

    output = payload.get("hookSpecificOutput")
    if not isinstance(output, dict):
        errors.append(f"{where}: no hookSpecificOutput object")
        return None
    if output.get("hookEventName") != "PreToolUse":
        errors.append(
            f"{where}: hookEventName is {output.get('hookEventName')!r}, "
            f"expected 'PreToolUse' -- Claude Code keys the output off this"
        )
    return payload


def check_wiring(errors: list[str]) -> None:
    """hooks.json runs this script on PreToolUse, on this tool and no other."""
    # First, because it depends on nothing below it and the returns below
    # would skip it. The hook command runs the script directly, so the bit is
    # load-bearing.
    if not os.access(SCRIPT, os.X_OK):
        errors.append(
            f"{SCRIPT.relative_to(ROOT)} is not executable; the hook command "
            f"runs it directly, so the bit is load-bearing"
        )

    try:
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8")).get("hooks", {})
    except (OSError, json.JSONDecodeError) as error:
        raise Failed(f"hooks/hooks.json: {error}") from None

    # Every entry that runs this script, whatever event it sits under. Reading
    # the whole file rather than only `PreToolUse` is what catches the wiring
    # that looks right and does nothing: a denial is a `PreToolUse` answer, and
    # the same handler on `PostToolUse` returns it after the widget has opened.
    entries = []
    for event, event_entries in config.items():
        for entry in event_entries or []:
            if not any(
                SCRIPT.name in handler.get("command", "")
                for handler in entry.get("hooks", [])
            ):
                continue
            if event != "PreToolUse":
                errors.append(
                    f"hooks/hooks.json: {SCRIPT.name} is wired to {event}; a "
                    f"permissionDecision means nothing outside PreToolUse"
                )
                continue
            entries.append(entry)

    # Filtered again, because an entry is a matcher and a *list* of handlers:
    # a second hook sharing this entry's matcher is somebody else's, and
    # counting it here would report the wrong script and then skip every
    # assertion below on the early return.
    handlers = [
        handler
        for entry in entries
        for handler in entry.get("hooks", [])
        if SCRIPT.name in handler.get("command", "")
    ]
    if len(handlers) != 1:
        errors.append(
            f"hooks/hooks.json: PreToolUse has {len(handlers)} handlers "
            f"running {SCRIPT.name}, expected exactly 1"
        )
        return

    command = handlers[0].get("command", "")
    if "${CLAUDE_PLUGIN_ROOT}" not in command:
        errors.append(
            f"hooks/hooks.json: {command!r} does not resolve the script "
            f"through ${{CLAUDE_PLUGIN_ROOT}}; nothing else knows where an "
            f"installed plugin lives"
        )
    if "*" in command:
        errors.append(
            f"hooks/hooks.json: {command!r} looks like a glob; the "
            f"constitution's *name every script you run* covers a hook too"
        )

    # An absent or empty matcher is the dangerous one, and it is dangerous in
    # the opposite direction to a wrong one: Claude Code reads it as *every*
    # tool, so the hook would deny Bash and Edit and the rest. It is diagnosed
    # first and on its own, because every test below reads it as a pattern --
    # `re.search("", anything)` matches, so the over-match loop would pass it
    # and the match test would report the exact opposite of what it does.
    matcher = entries[0].get("matcher", "")
    if not matcher:
        errors.append(
            f"hooks/hooks.json: the entry running {SCRIPT.name} has no "
            f"matcher, and Claude Code reads an empty matcher as every tool; "
            f"this hook would deny {', '.join(NOT_THIS_TOOL)} and the rest"
        )
        return

    # From here the matcher is a pattern, and is read as one.
    try:
        re.compile(matcher)
    except re.error as error:
        raise Failed(
            f"hooks/hooks.json: PreToolUse matcher {matcher!r} is not a "
            f"regular expression ({error}), so it matches nothing"
        ) from None
    if not re.search(matcher, TOOL):
        errors.append(
            f"hooks/hooks.json: matcher {matcher!r} does not match {TOOL!r}, "
            f"so the widget opens as before"
        )
    for tool in NOT_THIS_TOOL:
        if re.search(matcher, tool):
            errors.append(
                f"hooks/hooks.json: matcher {matcher!r} also matches {tool!r}, "
                f"which this hook has no business denying"
            )


def denial(errors: list[str], where: str, stdin: str) -> None:
    """The hook denies, and the reason it gives is one Claude can act on."""
    payload = run_hook(errors, where, stdin)
    if payload is None:
        return
    output = payload["hookSpecificOutput"]

    if output.get("permissionDecision") != "deny":
        errors.append(
            f"{where}: permissionDecision is "
            f"{output.get('permissionDecision')!r}, not 'deny'; the widget "
            f"would open"
        )
        return

    reason = output.get("permissionDecisionReason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append(
            f"{where}: the denial carries no reason. Claude is shown this "
            f"text and nothing else, so an empty one is a blocked call with "
            f"no instruction to replace it"
        )
        return
    for word in REQUIRED_IN_REASON:
        if word not in reason.lower():
            errors.append(
                f"{where}: the denial reason never says {word!r}; it has to "
                f"send the question to the chat reply and stop a retry"
            )


def check_denies(errors: list[str]) -> None:
    """A real call is denied, and so is one the hook cannot read."""
    denial(errors, "a real AskUserQuestion call", json.dumps(EVENT))
    for stdin in BAD_STDIN:
        denial(errors, f"unusable stdin {stdin!r}", stdin)


def check_allows_other_tools(errors: list[str]) -> None:
    """An event naming another tool is let through, loudly.

    This is the one case the hook fails open on, and the reasoning is in the
    script: an event that names a different tool means the matcher is wrong,
    and shutting off an unrelated tool with a message about a widget is worse
    than one widget getting through.
    """
    event = dict(EVENT, tool_name="Bash", tool_input={"command": "ls"})
    where = "an event naming Bash"
    payload = run_hook(errors, where, json.dumps(event))
    if payload is None:
        return
    decision = payload["hookSpecificOutput"].get("permissionDecision")
    if decision is not None:
        errors.append(
            f"{where}: permissionDecision is {decision!r}; a hook wired to "
            f"the wrong tool must not decide for it"
        )
    if SCRIPT.stem not in (payload.get("systemMessage") or ""):
        errors.append(
            f"{where}: no systemMessage naming the hook, so a wrong matcher "
            f"in hooks.json would never be noticed"
        )


def check_bad_argv(errors: list[str]) -> None:
    """A typo in hooks.json exits nonzero rather than passing silently."""
    result = spawn("session-start", stdin=json.dumps(EVENT))
    if result.returncode == 0:
        errors.append(
            "an unexpected argument exited 0; a typo in hooks.json would be "
            "silent"
        )


def main() -> int:
    errors: list[str] = []
    try:
        check_wiring(errors)
        check_denies(errors)
        check_allows_other_tools(errors)
        check_bad_argv(errors)
    except Failed as failure:
        errors.append(str(failure))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(
        f"the question widget is closed: {SCRIPT.relative_to(ROOT)} denies "
        f"{TOOL} with a reason that sends the question to the chat reply"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
