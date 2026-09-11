# Claude Code routes — deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md).

- **Finding what is behind.** `mcp__github__search_pull_requests` with
  `is:open author:app/dependabot` is the list, and each title names the
  dependency and the version it wants. Not
  `mcp__github__list_pull_requests`: it takes no author, so a filter written
  for it is one the server never applies, and a busy repository answers
  with everybody's pull requests.
- **Marking the pull request ready**, once every check has reported green.
  `mcp__github__update_pull_request` with `draft: false`.
- **Opening the pull request itself** is `pr`'s call — see that skill's own
  reference files.
