# Codex routes — undertake

`SKILL.md` names each operation in words. This file names the call, for a
session running in Codex. Claude Code's routes are in
[`claude.md`](claude.md), Oh My Pi's in [`omp.md`](omp.md).

**Codex has no GitHub tool of its own** — no `mcp__github__*` server, and no
built-in `github` tool with an `issue://` or `pr://` cache behind it. There is
one client, `gh` in the shell.


The issue
=========

| Step | Operation | Call |
| ---- | --------- | ---- |
| `Open the issue` | Search the open issues | `gh search issues` |
| `Open the issue` | Open one, labelled | `gh issue create --label task` |
| `Read the issue and its edges` | Read the body and the graph | `gh issue view <number> --json body,labels,blockedBy,subIssues,parent` |
| `Read the issue and its edges` | Label an issue that carries none | `gh issue edit <number> --add-label task` |
| `Claim the issue` | Comment on the issue | `gh issue comment <number> --body-file <path>` |

`--body-file` rather than `-b`: the claim carries backticks and markdown
links, and a double-quoted shell argument substitutes the backticks before
`gh` sees them. `pr-body`'s [`codex.md`](../../pr-body/references/codex.md)
makes the same argument at length.

The `--json` fields in the read row need `gh` at its stated floor.
`issue-deps` owns the edge reads and picks its own client — two clients here
rather than three — so read that skill's routes before believing an empty
answer. So does `issue-labels`, whose `references/codex.md` says why
`--add-label` needs no read-first and the Claude route does.


The pull request
================

| Step | Operation | Call |
| ---- | --------- | ---- |
| `Open the draft` | Open it | `pr`, which owns the call |
| `Ready for review` | Take it out of draft | `gh pr ready <number>` |
| `Keep it current` | Merge the base branch in | `gh pr update-branch <number>` |
| `A round after ready goes back to draft` | Return it to draft | `gh pr ready <number> --undo` |

Reading a pull request is `gh pr view <number>`. `Review the head` and
`Fix, answer, resolve, push` are `review-cycle`'s, and that skill carries no
Codex routes yet: until it does, run the round from what its body says and
take nothing from its Claude reference file, whose thread protocol rests on a
review surface this harness has not been shown to have.


The session
===========

**There is no session call**, so two of the three things `Claim the issue`
carries are unavailable: the claim says the surface supplied no model and no
session, which is the truth of a Codex session, and carries the branch alone.

The branch comes from the harness's own git state, which is the designation
here. `git branch --show-current` names the branch this session works on.
`OWNER/REPO` for the branch link comes from the `origin` remote.


There is no durable wake
========================

**No wake on this harness is known to outlive the turn that armed it**, so
`Keep it current`'s cadence does not run here. After `Ready for review`, say
once that the branch is kept current by the next session that picks the pull
request up, and stop.

This is the Omp answer arrived at for a different reason. Omp has a timer and
it is measured to die with the session; Codex has no timer this plugin has
found at all. Either way `SKILL.md`'s own rule applies — a watch a surface
cannot keep is worse claimed than skipped — and the never-empty wake slot,
[`0010`](../../../docs/notes/0010-the-wake-slot-is-never-empty.md), is the
Claude Code rule this harness does not carry.
