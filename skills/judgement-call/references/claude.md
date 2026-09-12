# Claude Code routes — judgement-call

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md),
Codex's in [`codex.md`](codex.md).

Claude denies `AskUserQuestion` through the `PreToolUse` hook
`hooks/ask-in-chat.py`. The hook fires the moment the model reaches for the
widget, refuses the call, and tells the model to put the question in the
chat reply instead. It does not decide whether a question is warranted —
that is this skill's gate — only how a surviving question gets to the user.
