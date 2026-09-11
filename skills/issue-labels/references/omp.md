# Omp routes — issue-labels

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

Two clients share the work, as they do for `undertake`: the built-in `github`
tool reads what it covers, `gh` writes, and `issue://<number>` resolves a read
from the same cache the `github` tool writes to.


Reading and writing a label
===========================

| Operation | Call |
| --------- | ---- |
| Read the labels on one issue | `issue://<number>`, or `gh issue view <number> --json labels` |
| Label an issue being opened | `gh issue create --label task` |
| Label an issue that exists | `gh issue edit <number> --add-label task` |
| Take a label off | `gh issue edit <number> --remove-label proposal` |

**`--add-label` adds; it does not replace.** That is the opposite of the
Claude route, and it is the safer half: nothing else on the issue is lost. It
is also why swapping one label for another takes both flags — `--add-label
task --remove-label proposal` — rather than one.

Finding the issues that carry a label is `gh issue list --label task`, or
`github.search_issues` with `label:task` in the query.
