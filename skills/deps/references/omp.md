# Omp routes — deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

- **Finding what is behind.** `search_prs`, the `github` tool's search op,
  with `is:open author:app/dependabot` — the same underlying
  `gh pr list --search`. The query carries the author filter, which is why the
  search is the route: a plain listing takes no author on either harness. The
  tool exposes no list op at all, so where a listing is wanted rather than a
  search, `gh pr list` is it.
- **Marking the pull request ready**, once every check has reported green.
  `gh pr ready`.
- **Opening the pull request itself** is `pr`'s call — see that skill's own
  reference files.
