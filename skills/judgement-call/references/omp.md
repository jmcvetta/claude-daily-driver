# Omp routes — judgement-call

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md), Codex's in [`codex.md`](codex.md).

Omp blocks its `ask` tool in the runtime adapter `extensions/daily-driver.js`.
The adapter intercepts the call, refuses it, and tells the model not to retry
the widget but to ask in chat instead. As on Claude, this adapter decides how
a surviving question is put, not whether there is one.
