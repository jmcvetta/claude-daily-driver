---
name: review-cycle
description: >-
  This skill should be used whenever a pull request is being reviewed and that
  review is then answered — including when the user says "/review-cycle",
  "review the PR and fix what it finds", "address the review feedback", "reply
  to the review comments", "resolve those threads", or "does that need another
  review?", and including any call Claude makes on its own initiative to the
  built-in `/code-review` aimed at a pull request, to
  `mcp__github__add_reply_to_pull_request_comment`, or to
  `mcp__github__resolve_review_thread`. Supplies the review invocation and its
  named effort level, the protocol every finding is answered under, and the
  test for whether a later push has earned a second round. Do NOT use this skill for opening a pull request or bringing
  one up to date — that is `pr` — nor for marking a draft ready, which is the
  caller's gate and not part of the round.
---

# Review cycle

One round: **review, answer, and decide whether it goes again.** A pull request
is reviewed once per diff, every finding it raises is closed out, and a push
that only answered the review does not buy a second review.

The analysis is the session's built-in `/code-review`. What this skill supplies
is the three things around it — the level, the thread protocol, and the
re-review test — none of which the built-in has an opinion about, and all three
of which are the ones that go wrong.

Callers keep their own gates. `undertake` runs this round between its step 6
and its step 9 and owns whether the pull request then goes ready; nothing here
marks a draft ready or merges anything.


The round
=========

| # | Stage | Owner |
| - | ----- | ----- |
| 1 | Review the head | the built-in `/code-review` |
| 2 | Fix, answer, resolve, push | this skill |
| 3 | Does it go again? | this skill |

**A round entered on findings that already exist starts at stage 2.** Half the
register arrives that way — *"address the review feedback"*, *"reply to the
review comments"*, *"resolve those threads"* — and the findings are then a
human's, a bot's, or an earlier `/code-review`'s. Running stage 1 over them
would post a fresh set on top of the ones somebody asked to have answered,
which is worse than not firing at all. Stage 1 is for a head nobody has
reviewed yet; stage 3 still decides what happens after.


1 — Review
==========

**Wait for CI to report on the pushed head first.** A pull request opened
seconds ago has its checks queued, and a queued check is not a passing one — a
review that reads it as either answer is reviewing the runner, not the code.

Then run the session's built-in **`/code-review`** against the pull request,
with `--comment`.

Name the level
--------------

**Name it; never inherit the remembered one.** On `claude-opus-5`, this
repository's model: `medium` by default, `xhigh` where the diff is large or
touches authentication, cryptography, access policy, migrations, or CI
configuration. Naming it is what makes two rounds on one branch comparable —
`/code-review` otherwise reuses whatever level was typed last, in some other
session, about some other diff.

`medium` rather than `high` because on that model the two resolve to the same
cell: `high` names a tier it does not deliver, and a default should say what it
runs. **That reason is the model's, not the level's.** On every other row of
`0001`'s matrix `high` is a distinct and deeper cell, so a session on another
family reads its own row and names `high` — taking this file's `medium` there
would buy a shallower review for a reason that does not hold in it. `xhigh` is
the deepest level a rule may select on its own, on any family, so it is where
the sensitive-touch escalation tops out: those are the diffs where a missed
finding is expensive and hard to see.

**`max` is not selectable here.** It is the only cell that dispatches a
verified panel on every family — and on `claude-opus-5` the only one that
verifies at all — and it is reserved for direct invocation by the author, who
names it themselves and unambiguously. No rule in this file selects it on the
reader's behalf: that spends the author's quota on a decision the author did
not make.

[`0001`](../../docs/decisions/0001-built-in-review-surface.md) is the matrix
behind all three, and the model family is the axis it insists on: the level
names mean different things row to row, and it is pinned to CLI 2.1.263
besides. Re-read the row for the session's own model before treating a cell as
current — a rule written against a stale table, or against another family's
row, names a tier it does not deliver.

A reviewer, not a subagent
--------------------------

Not "dispatch a subagent to code review the branch". A bare subagent inherits
no rubric, has no level anybody chose, and posts nothing — its findings die in
the transcript, and stage 2 has nothing to answer. The built-in is the
reviewer, and `--comment` is what makes its findings survive the session.

`--comment` is also what carries the findings out of the terminal and onto the
pull request, where they remain the record of why the branch was judged ready.
They arrive as **resolvable review threads**, inline on the diff under a
submitted `COMMENT` review — measured on live pull requests at `max` and again
at `medium`, CLI 2.1.263, 2026-09-07, and recorded in `0001` §4. The level is
part of that claim rather than incidental to it: `medium` and `high` dispatch
`o5-bmin`, the one cell `0001` records as ignoring the output-contract selector
every other cell threads through, so the default named above is measured rather
than inherited from a deeper level's result. Stage 2's reply-and-resolve is
therefore the ordinary path rather than a hoped-for one.

Should a later CLI post plain issue comments instead, stage 2 degrades to
reply-only: read them with `get_comments` rather than `get_review_comments`,
answer with `mcp__github__add_issue_comment`, and read *resolve* as *answered
in a comment* — in this file **and in the caller's gate**, where a bullet
asking for no unresolved thread would otherwise be a condition the round can
never satisfy. Say so once, and re-measure into `0001` rather than leaving the
next round to rediscover it.

Record the head SHA
-------------------

**Record the head SHA you reviewed.** Stage 3's test is measured from it, and
nothing else records it.


2 — Fix, answer, resolve, push
==============================

Every finding gets a verdict, on its thread, and the thread is closed:

1. **Implemented** — fix it, reply saying so, resolve the thread.
2. **Rejected** — reply with the reason, and resolve it anyway. A rejection is
   an answer; only silence is not.
3. **Deferred** — only where the user asks for it. Claude does not propose a
   deferral: `judgement-call` names "leave a TODO" as the option that is never
   a real one, so a deferral Claude offers is the noise that skill deletes.
   When the user does defer, reply naming what was deferred and to where, then
   resolve — an open thread would claim the question is still live.
4. **A repeat finding** — a reviewer opening a new thread for something already
   rejected in an earlier round — is resolved with the same message as before.
   A fresh variation invites a fresh argument over a question that was already
   answered. This one is live precisely because stage 1 can run again and
   re-raise what stage 2 rejected.
5. **Never left open silently.** The rule the other four exist to serve.

Every reviewer is the same protocol — Claude's own findings, a human's, a
bot's. None of it is reviewer-specific.

The reply
---------

Verdict-first, concise, technical. A reader skimming twenty threads should
never have to parse a paragraph to learn whether the finding was implemented or
rejected. No thanks, no apologies, no restating the finding back at the
reviewer, and no poetry — verse attaches to the pull request body, never to a
finding somebody has to act on.

A rejection carries its reason and stops. *"Rejected — `n` is bounded by the
caller's `len(items)` check at `loader.go:88`"* is a complete reply; softening
it into a discussion reopens the thread the rule just closed.

The clients, and the identifier trap
------------------------------------

Read the threads with `mcp__github__pull_request_read` using its
`get_review_comments` method, reply with
`mcp__github__add_reply_to_pull_request_comment`, close with
`mcp__github__resolve_review_thread`.

**The two calls take different identifiers, and only one of them is a field.**
Measured 2026-09-06: resolve wants the thread's `id`, a `PRRT_…` node ID, read
directly. Reply wants a number that appears nowhere as a field — the
`#discussion_r…` suffix of the comment's `html_url`, so
`…/pull/25#discussion_r3943994364` means `commentId: 3943994364`. Do not
substitute the thread ID into the reply: it is the identifier that *is*
present, which is why it gets reached for, and the call fails on a type that
looks plausible.

Then push
---------

A caller's CI gate reads the remote head, and a fix that never left the laptop
is not in it.


3 — Does it go again?
=====================

**Review once per diff.** Stage 2 usually puts commits on the branch, so by the
end of a round the head is usually not the one stage 1 read — and a rule that
keyed on sameness would re-review on every round that had anything to fix.

The test is therefore **provenance, not sameness**: take the head SHA recorded
at stage 1, and classify every commit made after it.

- **Answering** — a review finding, a review thread, a lint bot, a red check.
  These do not start a new round, however many of them there are. Answering a
  review is not new work, and re-reviewing the answer is the loop this rule
  exists to cut.
- **Changing what the code does** — new feature work, a scope addition, a
  conflict resolution that rewrites the branch's own files. This is a new diff.
  Stage 1 runs again over it, once, and its head SHA becomes the new mark.
- **Neither** — a comment reflow, a changelog line, a merge from the base
  branch that leaves the pull request's own diff untouched. **Not a new diff.**
  The default is not to go again, because stage 1 reads the pull request, whose
  diff is three-dot: a clean base merge changes the head and changes nothing
  stage 1 would read. Reviewing it again would review byte-identical content,
  and on a base branch that moves often it would do so without end.

The classification is per commit and the categories do not compound: a round
that only ever answers ends with one review behind it, which is the point.

When the mark is void
---------------------

Where the branch's history is rewritten — a rebase, an amend, a squash — the
recorded SHA stops being an ancestor of the head and the mark is void. There
are then no commits "after it" to read, which is not the same as there being
none. Fall back to content: compare the pull request's diff against what stage
1 reviewed, and go again only if it has changed.


Where it stops and waits
========================

- **CI still running**, before stage 1. A wait, not a question — nothing is
  asked, and nothing proceeds on a check that has not reported.
- **A finding whose fix is a real trade-off**, in the sense `judgement-call`
  gives that phrase: two defensible approaches differing in something the user
  owns. That skill owns the gate, and it is the gate for every question this
  round would otherwise ask. A finding whose fix the standard already picks is
  not one of these — fix it and say so.

Everything else runs through. No permission is asked to fix a finding, to
reply, to resolve, or to push.


Non-goals
=========

- **Does not open the pull request, and does not update it as a whole.** That
  is `pr`. This round starts from one that already exists.
- **Does not mark a draft ready, and does not merge.** Whether the round's
  outcome is enough to go ready is the caller's gate — `undertake` has one —
  and a skill that answered its own review is the wrong judge of it.
- **Does not fire on reading a review.** "What did the reviewer say about the
  retry loop" is a question; answer it, and do not start a round.
- **Does not minimise superseded comments.** That is `pr-threads`' other half,
  retired to the attic rather than shipped: it is a GraphQL mutation the GitHub
  MCP does not expose, reachable only from a laptop on a personal token.
