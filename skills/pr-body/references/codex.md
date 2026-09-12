# Codex routes — pr-body

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex has no GitHub tool of its own**, so both calls are `gh` in the shell.

- **Setting the body while opening a pull request.**
  `gh pr create --body "…"`.
- **Revising the body of an existing pull request.**
  `gh pr edit --body "…"`.
