# Claude Code routes — pr-body

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md).

- **Setting the body while opening a pull request.**
  `mcp__github__create_pull_request` takes `body` directly.
- **Revising the body of an existing pull request.**
  `mcp__github__update_pull_request` with `body` set.
