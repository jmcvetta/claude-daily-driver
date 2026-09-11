# Omp routes — pr-body

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

- **Setting the body while opening a pull request.** The `github` tool's
  `pr_create` op takes `body` directly.
- **Revising the body of an existing pull request.**
  `gh pr edit --body "…"`.
