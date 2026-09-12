# Codex routes — judgement-call

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex's question widget is `request_user_input`**, which takes `questions`
with `options` — the same shape the other two harnesses' widgets take, under
a third name. `AskUserQuestion` does not exist here, so the matcher written
for Claude reaches nothing.

Codex narrows the widget on its own, before any adapter does. The tool's own
description says it is available in Plan mode alone, and the binary refuses
it outright in `exec` mode. So an unattended Codex run cannot reach the
widget whether or not the plugin denies it, and a session that *can* reach it
is one a person is watching.

That is a reason to be careful about what the denial is read as saying. As on
Claude and on Omp, the adapter decides how a surviving question is put, not
whether there is one — and here the harness has already decided most of the
how. The gate in `SKILL.md` is unchanged: it is what separates a question
only the user can answer from one Claude can answer himself, and a widget
that is unreachable answers neither.
