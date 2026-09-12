# Codex routes — pr

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex has no GitHub tool of its own** — no `mcp__github__*` server and no
built-in `github` tool. Every call below is `gh` in the shell, which is the
half of the Omp routes that carries over unchanged.

- **Checking whether a pull request already exists for the branch.**
  `gh pr view` (or `gh pr list --head <branch>`) finds it.
- **Opening a new pull request.** `gh pr create --draft`, for the initial
  state this skill requires.
- **Updating an existing pull request as a whole** — title and body
  together. `gh pr edit`, called once both are decided (`pr-title`,
  `pr-body`).
