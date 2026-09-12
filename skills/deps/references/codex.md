# Codex routes — deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex has no GitHub tool of its own**, so every call is `gh` in the shell.

- **Finding what is behind.** `gh pr list --search "is:open
  author:app/dependabot"`. The query carries the author filter, which is why
  the search is the route: a plain listing takes no author on any of the
  three harnesses.
- **Marking the pull request ready**, once every check has reported green.
  `gh pr ready`.
- **Opening the pull request itself** is `pr`'s call — see that skill's own
  reference files.
