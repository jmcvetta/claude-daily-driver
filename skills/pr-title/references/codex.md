# Codex routes — pr-title

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex has no GitHub tool of its own**, so both calls are `gh` in the shell.

- **Setting the title while opening a pull request.**
  `gh pr create --title "…"`.
- **Revising the title of an existing pull request.**
  `gh pr edit --title "…"`.
