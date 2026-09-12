# Claude Code routes — pr

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md),
Codex's in [`codex.md`](codex.md).

- **Checking whether a pull request already exists for the branch.**
  `mcp__github__list_pull_requests` filtered to `head` finds it;
  `mcp__github__pull_request_read` reads one once its number is known.
- **Opening a new pull request.** `mcp__github__create_pull_request`, with
  `draft: true` for the initial state this skill requires.
- **Updating an existing pull request as a whole** — title and body
  together. `mcp__github__update_pull_request`, called once both are decided
  (`pr-title`, `pr-body`).
