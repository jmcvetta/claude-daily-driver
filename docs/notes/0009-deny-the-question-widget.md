# The question widget is denied by hook, not discouraged by prose

**Status:** decided, 2026-09-09.
**Provenance:** the operator said the multiple-choice widget is unwelcome —
most of all on a phone — and asked whether a skill or a constitution directive
should carry the preference. Neither does.
**Implements:** the enforcement half that
[`0008`](0008-ci-runs-the-project-gates.md) declined to write, on a different
tool.

`AskUserQuestion` renders a multiple-choice widget. The operator prefers to
discuss the same question in chat, every time, and a preference answered the
same way every time is not a judgement. The question was where to put it.

## Decided

**A `PreToolUse` hook, `hooks/ask-in-chat.py`, matched on `^AskUserQuestion$`.**
It answers `permissionDecision: "deny"`, and the reason Claude Code shows the
model is the instruction that replaces the tool: ask in prose, list the
options, name a recommendation.

**Not the constitution.** That file's own admission test asks whether a rule
changes behaviour in most sessions, hangs off a nameable moment, and says
something the harness does not already say. This one passes the second and
third and fails the first — most sessions never reach for the widget — and it
would be paid for in tokens in every session and every subagent, forever. A
hook costs nothing until the moment it fires.

**Not a new skill.** `judgement-call` already fires on `AskUserQuestion`, so a
second skill on the same trigger is two descriptions competing to be loaded at
one moment. The two questions are ordered rather than overlapping —
`judgement-call` decides **whether** the question is the user's to answer, this
hook decides **how** a surviving one is put — and the denial reason names the
skill so the order survives being read out of context.

**Determinism is the whole argument.** Prose can be read and not followed, and
this preference has no exceptions to weigh, which is exactly
[`0008`](0008-ci-runs-the-project-gates.md)'s closing observation: a rule that
does not depend on a mid-task judgement should be enforced rather than
instructed.

## What it costs

**The widget is gone, not dimmed.** There is no escape hatch — no environment
variable, no flag — because a switch that is never set is dead code carrying a
test. A session that genuinely wants the widget disables the plugin, which is
the honest price of a bright line.

**A denial the model cannot read is a denial it will retry.** The reason
carries the whole burden, so `scripts/check-ask-in-chat.py` asserts on it
directly: a rewrite that drops *chat* or *retry* turns the repository red.

**One case fails open.** An event that positively names some other tool is let
through, with a `systemMessage` saying the matcher is wrong. Denying an
unrelated tool on a broken matcher shuts off something the session needs and
gives a misleading reason for it; one widget getting through is the cheaper
failure. An event the hook cannot read at all is still denied — the matcher
already identified the call, and failing open there would give the widget back
on the one glitch nobody would notice.

## What it does not decide

Whether the same argument reaches other tools. It plainly could — `0008` names
a local project check as a candidate — and nothing here is written to be
general. This hook denies one tool.
