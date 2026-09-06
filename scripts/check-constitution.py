#!/usr/bin/env python3
"""The credential-free half of the constitution's acceptance test.

The constitution carries the rule *code without tests is broken*, which makes
an untested delivery mechanism for it indefensible. The test divides where the
credential requirement actually starts, and this is the half below that line:

- **Here**: run each hook exactly as the harness runs it — the real script,
  synthetic event JSON on stdin — and assert on what comes back. No model in
  the loop, so it belongs in `make check` and in a CI that holds no
  credentials. It catches every cause listed under R1: a bad path, an empty or
  unreadable constitution, malformed event JSON, a nonzero exit, output that
  is not JSON.
- **`evals/constitution-reaches-subagent/`**: the live half. Only a real
  session can prove the harness *honours* `updatedInput`, which is the R2
  finding proper, and only a real model can be asked what it was told.

They fail for different reasons and deserve to fail separately: the first
tests this plugin, the second tests an assumption about the harness that a
future release could withdraw without telling anyone.

One assertion here is worth naming, because it is the one that keeps D12 true
over time: the subagent's prompt must be *exactly* the main session's context
plus the original prompt. Two injection points reading one file is not
sufficient for them to agree — they could still wrap it differently — so the
agreement is asserted byte for byte rather than argued for in a comment.

No third-party imports: this runs from a Makefile on a laptop and from CI, and
a dependency install between the two is a place for them to differ.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_JSON = ROOT / "hooks" / "hooks.json"
SCRIPT = ROOT / "hooks" / "inject-constitution.py"
CONSTITUTION = ROOT / "context" / "constitution.md"
EVALS = ROOT / "evals"

TOKEN_LINE = re.compile(r"^constitution-token: (\S+)$")

# The tool names a subagent spawn can arrive under. `Agent` is current; `Task`
# is what the same tool was called for years, and a matcher that admits only
# the current name is a silent regression the day a session runs an older
# harness -- the exact failure mode R2 exists to prevent.
SUBAGENT_TOOLS = ("Agent", "Task")
NOT_SUBAGENT_TOOLS = ("Bash", "Edit", "AgentOutput", "MyAgent")

SESSION_START_EVENT = {
    "session_id": "check-constitution",
    "cwd": str(ROOT),
    "hook_event_name": "SessionStart",
    "startup_reason": "startup",
}

ORIGINAL_PROMPT = "Find every caller of frobnicate() and report the list."
PRE_TOOL_USE_EVENT = {
    "session_id": "check-constitution",
    "cwd": str(ROOT),
    "hook_event_name": "PreToolUse",
    "tool_name": "Agent",
    "tool_input": {
        "prompt": ORIGINAL_PROMPT,
        "description": "find callers",
        "subagent_type": "Explore",
    },
    "tool_use_id": "toolu_check",
}


class Failed(Exception):
    """A check that did not hold. The message is the report."""


def spawn(script: Path, mode: str, stdin: str) -> subprocess.CompletedProcess[str]:
    """Run a hook script as the harness runs it: argv, stdin, and nothing else.

    `CLAUDE_PLUGIN_ROOT` is stripped deliberately. The harness sets it, the
    script must not need it, and clearing it here is the regression test for
    that -- see PLUGIN_ROOT in the script.
    """
    try:
        return subprocess.run(
            [str(script), mode],
            input=stdin,
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"},
        )
    except OSError as error:
        raise Failed(
            f"{script} {mode} could not be executed ({error.strerror or error}); "
            f"the hook command runs it directly"
        ) from None


def run_hook(mode: str, event: dict) -> dict:
    """Invoke a hook the way Claude Code does, and insist on a usable answer."""
    where = f"hooks/inject-constitution.py {mode}"
    result = spawn(SCRIPT, mode, json.dumps(event))
    if result.returncode != 0:
        raise Failed(
            f"{where}: exited {result.returncode}; a nonzero exit is a session "
            f"with no constitution and no reliable warning\n  stderr: "
            f"{result.stderr.strip() or '(empty)'}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise Failed(
            f"{where}: stdout is not JSON ({error}); the harness would ignore "
            f"it\n  stdout: {result.stdout[:200]!r}"
        ) from None
    if not isinstance(payload, dict):
        raise Failed(f"{where}: emitted {type(payload).__name__}, not an object")
    return payload


def hook_specific(payload: dict, event_name: str, where: str) -> dict:
    output = payload.get("hookSpecificOutput")
    if not isinstance(output, dict):
        raise Failed(f"{where}: no hookSpecificOutput object")
    if output.get("hookEventName") != event_name:
        raise Failed(
            f"{where}: hookEventName is {output.get('hookEventName')!r}, "
            f"expected {event_name!r} -- Claude Code keys the output off this"
        )
    return output


def token() -> str:
    """The last line of the constitution, which R1 makes checkable on purpose."""
    text = CONSTITUTION.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise Failed(f"{CONSTITUTION.relative_to(ROOT)} is empty")
    match = TOKEN_LINE.match(lines[-1])
    if not match:
        raise Failed(
            f"{CONSTITUTION.relative_to(ROOT)}: the last non-empty line is "
            f"{lines[-1]!r}, not a `constitution-token: <token>` line. The "
            f"token is how a session proves the constitution reached it "
            f"(R1); without it the failure is silent again."
        )
    return match.group(1)


def check_wiring(errors: list[str]) -> None:
    """hooks.json wires both events to the one script, and matches the right tool."""
    try:
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8")).get("hooks", {})
    except (OSError, json.JSONDecodeError) as error:
        raise Failed(f"hooks/hooks.json: {error}") from None
    commands: dict[str, str] = {}

    for event, expected_mode in (
        ("SessionStart", "session-start"),
        ("PreToolUse", "pre-tool-use"),
    ):
        entries = config.get(event) or []
        handlers = [h for entry in entries for h in entry.get("hooks", [])]
        if len(handlers) != 1:
            errors.append(
                f"hooks/hooks.json: {event} has {len(handlers)} handlers, "
                f"expected exactly 1"
            )
            continue
        command = handlers[0].get("command", "")
        commands[event] = command
        if not command.endswith(f" {expected_mode}"):
            errors.append(
                f"hooks/hooks.json: the {event} command does not end in "
                f"{expected_mode!r}: {command!r}"
            )
        if "*" in command or "glob" in command:
            errors.append(
                f"hooks/hooks.json: the {event} command looks like a glob "
                f"({command!r}); D12 is one file read by exact path"
            )

    # One script for both events is what makes "the same file, by exact path"
    # structural rather than aspirational: there is only one path constant.
    stems = {c.rsplit(" ", 1)[0] for c in commands.values()}
    if len(stems) > 1:
        errors.append(
            "hooks/hooks.json: the two events run different commands "
            f"({sorted(stems)}); they must run the one script, so that they "
            "cannot read different files"
        )
    for command in stems:
        if SCRIPT.name not in command:
            errors.append(f"hooks/hooks.json: {command!r} does not name {SCRIPT.name}")
        if "${CLAUDE_PLUGIN_ROOT}" not in command:
            errors.append(
                f"hooks/hooks.json: {command!r} does not resolve the script "
                "through ${CLAUDE_PLUGIN_ROOT}; nothing else knows where an "
                "installed plugin lives"
            )

    matchers = [entry.get("matcher", "") for entry in config.get("PreToolUse") or []]
    for matcher in matchers:
        try:
            re.compile(matcher)
        except re.error as error:
            raise Failed(
                f"hooks/hooks.json: PreToolUse matcher {matcher!r} is not a "
                f"regular expression ({error}), so it matches nothing"
            ) from None

    for tool in SUBAGENT_TOOLS:
        if not any(re.search(m, tool) for m in matchers if m):
            errors.append(
                f"hooks/hooks.json: no PreToolUse matcher in {matchers} matches "
                f"{tool!r}, so subagents spawned through it get no constitution"
            )
    for tool in NOT_SUBAGENT_TOOLS:
        if any(re.search(m, tool) for m in matchers if m):
            errors.append(
                f"hooks/hooks.json: a PreToolUse matcher in {matchers} also "
                f"matches {tool!r}, which takes no subagent prompt"
            )

    if not os.access(SCRIPT, os.X_OK):
        errors.append(
            f"{SCRIPT.relative_to(ROOT)} is not executable; the hook command "
            "runs it directly, so the bit is load-bearing"
        )


def check_delivery(errors: list[str], expected_token: str) -> None:
    """Both injection points carry the constitution, and carry the same one."""
    body = CONSTITUTION.read_text(encoding="utf-8").rstrip()

    start = hook_specific(
        run_hook("session-start", SESSION_START_EVENT),
        "SessionStart",
        "SessionStart",
    )
    context = start.get("additionalContext")
    if not isinstance(context, str) or not context.strip():
        errors.append("SessionStart: additionalContext is missing or empty")
        return
    if body not in context:
        errors.append(
            "SessionStart: additionalContext does not carry the constitution "
            "verbatim"
        )
    if expected_token not in context:
        errors.append(
            f"SessionStart: additionalContext does not carry the token "
            f"{expected_token!r}"
        )

    agent = hook_specific(
        run_hook("pre-tool-use", PRE_TOOL_USE_EVENT), "PreToolUse", "PreToolUse"
    )
    updated = agent.get("updatedInput")
    if not isinstance(updated, dict):
        errors.append(
            "PreToolUse: no updatedInput object, so the subagent is spawned "
            "with the prompt Claude wrote and no constitution"
        )
        return

    prompt = updated.get("prompt")
    if not isinstance(prompt, str):
        errors.append("PreToolUse: updatedInput has no prompt string")
        return
    if ORIGINAL_PROMPT not in prompt:
        errors.append(
            "PreToolUse: updatedInput.prompt dropped the prompt Claude wrote"
        )
    if expected_token not in prompt:
        errors.append(
            f"PreToolUse: updatedInput.prompt does not carry the token "
            f"{expected_token!r}"
        )

    # D12, asserted rather than asserted-to-be-true: the subagent gets the main
    # session's context and then its own prompt, with nothing added, dropped or
    # reworded in between. This is the check that fails when the two injection
    # points start to drift.
    if prompt != f"{context}\n\n{ORIGINAL_PROMPT}":
        errors.append(
            "the two injection points have drifted: updatedInput.prompt is "
            "not the SessionStart additionalContext followed by the original "
            "prompt"
        )

    for key, value in PRE_TOOL_USE_EVENT["tool_input"].items():
        if key != "prompt" and updated.get(key) != value:
            errors.append(
                f"PreToolUse: updatedInput dropped or changed {key!r} "
                f"({updated.get(key)!r} != {value!r}); updatedInput replaces "
                f"the whole tool input"
            )


def check_loud_failure(errors: list[str]) -> None:
    """A constitution that cannot be read says so, everywhere it can.

    R1's whole point: the interesting failure is not the hook that crashes, it
    is the hook that returns cleanly having delivered nothing. So this stands
    up a plugin root with no constitution in it and insists on the noise.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fake_root = Path(tmp) / "daily-driver"
        (fake_root / "hooks").mkdir(parents=True)
        (fake_root / "context").mkdir()
        broken = fake_root / "hooks" / SCRIPT.name
        shutil.copy2(SCRIPT, broken)

        for mode, event, event_name in (
            ("session-start", SESSION_START_EVENT, "SessionStart"),
            ("pre-tool-use", PRE_TOOL_USE_EVENT, "PreToolUse"),
        ):
            where = f"missing constitution, {mode}"
            result = spawn(broken, mode, json.dumps(event))
            if result.returncode != 0:
                errors.append(
                    f"{where}: exited {result.returncode}; the warning rides "
                    f"on stdout, which a nonzero exit puts at risk"
                )
                continue
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                errors.append(f"{where}: stdout is not JSON: {result.stdout[:200]!r}")
                continue

            if "FAILED TO LOAD" not in json.dumps(payload):
                errors.append(
                    f"{where}: the payload does not say the constitution "
                    f"failed to load, so the session would not know"
                )
            if "NOT loaded" not in (payload.get("systemMessage") or ""):
                errors.append(f"{where}: no systemMessage warning for the user")
            if "inject-constitution" not in result.stderr:
                errors.append(f"{where}: nothing on stderr")

            output = payload.get("hookSpecificOutput") or {}
            if output.get("hookEventName") != event_name:
                errors.append(
                    f"{where}: hookEventName is {output.get('hookEventName')!r}"
                )
            if event_name == "PreToolUse" and ORIGINAL_PROMPT not in json.dumps(
                output.get("updatedInput") or {}
            ):
                errors.append(
                    f"{where}: the subagent's own prompt was lost; a missing "
                    f"constitution must not also break delegation"
                )


def check_eval_token(errors: list[str], expected: str) -> None:
    """The live half asserts on the same token this half reads.

    The token is written twice by necessity — once in the constitution, once in
    the grader that looks for it coming back — and two copies of a constant is
    how the live suite comes to be quietly testing last month's token. Any eval
    file that talks about the token has to name the current one.
    """
    if not EVALS.is_dir():
        errors.append(
            f"{EVALS.relative_to(ROOT)}/ is missing; the live half of the "
            f"acceptance test is where `updatedInput` is actually proven"
        )
        return

    asserted = False
    for path in sorted(EVALS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        where = path.relative_to(ROOT)
        if path.parent.name == "graders":
            if "constitution-token" not in text:
                continue
            if expected in text:
                asserted = True
            else:
                errors.append(
                    f"{where}: names the constitution token but not the "
                    f"current one ({expected}); the live suite would be "
                    f"testing a token that no longer ships"
                )
        elif expected in text:
            # A prompt that spells the token out hands the parent the answer,
            # and a live run that then "passes" has measured nothing.
            errors.append(
                f"{where}: contains the token itself. Only the graders may "
                f"name it; a case prompt that does is telling the session "
                f"what the subagent was supposed to have been told."
            )

    if not asserted:
        errors.append(
            f"no grader under {EVALS.relative_to(ROOT)}/ asserts on the "
            f"constitution token, so the live half proves nothing"
        )


def check_bad_input(errors: list[str]) -> None:
    """Garbage on stdin is the harness's problem, not the constitution's."""
    for stdin in ("", "not json at all", "[]"):
        result = spawn(SCRIPT, "session-start", stdin)
        if result.returncode != 0:
            errors.append(
                f"session-start on {stdin!r}: exited {result.returncode}, "
                f"costing the session its constitution over a bad event"
            )
            continue
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            errors.append(f"session-start on {stdin!r}: stdout is not JSON")
            continue
        context = (payload.get("hookSpecificOutput") or {}).get("additionalContext")
        if not isinstance(context, str) or "Constitution" not in context:
            errors.append(
                f"session-start on {stdin!r}: no constitution in the output"
            )

    result = spawn(SCRIPT, "no-such-mode", "{}")
    if result.returncode == 0:
        errors.append("an unknown mode exited 0; a typo in hooks.json would be silent")


def main() -> int:
    errors: list[str] = []
    try:
        expected = token()
        check_wiring(errors)
        check_delivery(errors, expected)
        check_loud_failure(errors)
        check_eval_token(errors, expected)
        check_bad_input(errors)
    except Failed as failure:
        errors.append(str(failure))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(
        "constitution delivery holds: both hooks carry "
        f"{CONSTITUTION.relative_to(ROOT)} (token {expected}), identically, "
        "and fail loudly when it is missing"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
