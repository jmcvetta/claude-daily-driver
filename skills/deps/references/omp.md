# Omp routes — deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

- **Finding what is behind.** The `github` tool has no PR-list operation at
  all, and no author filter either way. Its search op (`search_prs`) with
  `is:open author:app/dependabot` is the search route — the same underlying
  `gh pr list --search`. Where a plain listing is wanted rather than a
  search, `gh pr list` is that route; it is not exposed through the tool.
- **Marking the pull request ready**, once every check has reported green.
  `gh pr ready`.
- **Opening the pull request itself** is `pr`'s call — see that skill's own
  reference files.
