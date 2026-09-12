# Claude Code routes — pr-title

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md),
Codex's in [`codex.md`](codex.md).

- **Setting the title while opening a pull request.**
  `mcp__github__create_pull_request` takes `title` directly.
- **Revising the title of an existing pull request.**
  `mcp__github__update_pull_request` with `title` set.
