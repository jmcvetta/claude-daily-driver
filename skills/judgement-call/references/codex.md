# Codex routes — judgement-call

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex's question widget is `request_user_input`**, which takes `questions`
with `options` — the same shape the other two harnesses' widgets take, under
a third name. `AskUserQuestion` does not exist here, so the matcher written
for Claude reaches nothing on its own.

Codex denies the widget through the `PreToolUse` hook `hooks/ask-in-chat.py`,
the same hook Claude Code uses and the same one copy of it: the matcher names
both widgets, and the hook refuses the call and tells the model to put the
question in the chat reply instead. As on Claude and on Omp, it does not
decide whether a question is warranted — that is this skill's gate — only how
a surviving question gets to the user.

**The harness narrows the widget as well, before the hook does.** The tool's
own description says it is available in Plan mode alone, and the binary
refuses it outright in `exec` mode. So an unattended Codex run cannot reach
the widget whichever of the two stops it first, and a session that *can*
reach it is one a person is watching. The hook is what makes the outcome the
same in the sessions where the harness would have allowed it.
