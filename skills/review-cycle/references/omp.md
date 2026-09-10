# Omp routes — review-cycle

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).


The review surface
==================

The **`reviewer`** task agent, dispatched through the `task` tool: a
code-review specialist, taking the review brief for the pull request and
reading the diff through `pr://`.

**It takes no effort level.** The round names the agent and nothing more, and
the depth judgement is the agent's. `SKILL.md`'s `Name the level` has nothing
to bind here — there is no remembered level to override.

**Its findings do not land on the pull request as review threads.** They come
back in the agent's result and nowhere else, so the round carries them into
`Fix, answer, resolve, push` itself. That is the degradation `SKILL.md`
describes under `A reviewer, not a bare subagent`: nothing is posted for a
reviewer to resolve, so *resolve* reads as *answered*, and the caller's gate
reads its no-unresolved-thread condition the same way.


The wait
========

**`github.run_watch`.** The built-in `github` tool's `run_watch` op watches the
head commit's Actions runs and streams until every one has reported. Success is
double-checked with one more poll before it returns, and a failure names the
failed jobs.

It is a blocking watch, so the wait is one call. No subscription, no backstop,
no timer — the three things `claude.md` needs exist because Claude has nothing
that blocks. `SKILL.md`'s rules that hold either way still hold: the union of
the checks and the commit statuses is what *reported* means, an empty answer is
not an answer, and the fifteen-minute cap is a report to the user rather than a
longer wait.

`run_watch` is present wherever the `github` tool is enabled, which includes
the laptop Omp surface. The surface `SKILL.md` says cannot wait does not arise
here the way it arises on Claude.

There is no durable wake
------------------------

**`daily_driver_schedule` is an in-process managed timer, and a reminder dies
with the session.** Omp's own documentation says managed timers are unref'd and
cleared on `session_shutdown`. It is not a `send_later`, which survives the
session that armed it.

So the never-empty wake slot —
[`0010`](../../../docs/notes/0010-the-wake-slot-is-never-empty.md) — is
Claude's rule and not this harness's. It has nothing to hold. `run_watch`
completes the wait inside the turn, so no wake is scheduled around it, and a
wake scheduled with nothing to do on it is the noise `0010` exists to prevent.
Schedule with `daily_driver_schedule`, and cancel with
`daily_driver_cancel_schedule`, only where the round must hand the pull request
back to itself for a follow-up **inside the current session** — never as a
watch that outlives it.


The review threads
==================

**The built-in `github` tool has no review-thread operation.** All three go
through the GitHub CLI and API.

| Operation | Call |
| --------- | ---- |
| Read the threads | `gh api /repos/{owner}/{repo}/pulls/{n}/comments` |
| Reply on a thread | `gh api -X POST /repos/{owner}/{repo}/pulls/{n}/comments/{comment_id}/replies` |
| Resolve a thread | `gh api graphql` with the `resolveReviewThread` mutation |

The identifier trap `SKILL.md` states applies to the last two here too: the
mutation takes the thread's `PRRT_…` node ID, and the reply takes the
comment's numeric id — the `#discussion_r…` suffix of its `html_url`.
