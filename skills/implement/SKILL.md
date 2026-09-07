---
name: implement
description: >-
  This skill should be used whenever a GitHub issue is being taken from its
  description to a pull request ready for review — including when the user says
  "/implement", "implement #191", "work on issue 12", "take #7", "start on
  that issue", or "let's build #4", and on Claude's own move from reading an
  issue to writing code for it. Supplies the order of the steps, the gates
  between them, and the rule that discharges the pre-ready review. Do NOT use
  this skill for merely reading, summarising, or discussing an issue —
  "what does #191 say" is a question, not an assignment.
---

# Implement

An issue in, a pull request ready for review out. Nine steps, and this skill
is the order they run in.

It is an orchestrator, in the same shape as `pr`: **it invokes, it does not
restate**. The title convention lives in `pr-title`, the review rubric in
`review`, the reply protocol in `pr-threads`, and the engineering standard in
the constitution. Where a step below names a rule those files own, it names it
as a pointer and cites the owner — a rule that acquires a second home here is
one whose copy goes stale, and a citation is what makes the drift visible.

What this skill owns is the sequencing, the gates, and the three corrections
below.


The sequence
============

| # | Step | Owner |
| - | ---- | ----- |
| 1 | Title the session from the issue | `session-title` |
| 2 | Read the issue and its edges | `mcp__github__issue_read`, `issue-deps` |
| 3 | Branch off the base branch | this skill |
| 4 | Implement | the constitution |
| 5 | Run the project's gates | the constitution |
| 6 | Push, and open the draft pull request | `pr` |
| 7 | Review | `review` |
| 8 | Fix, answer, resolve, push | `review`'s walkthrough, then `pr-threads` |
| 9 | Ready for review | `mcp__github__update_pull_request` |

1 — Title the session
---------------------

Before anything else. Read the issue *title* — that is all this step needs —
and title the session from it before reading the body. A web session otherwise
takes its name from the first prompt it received, which is the prompt that
invoked this skill. `session-title` has the form and the budget.

2 — Read the issue and its edges
--------------------------------

The body, and then the graph: parent, sub-issues, blocked-by. **An issue
blocked by an open one is a stop, not a start** — say which issue blocks it
and wait. Reading the graph is free and needs no confirmation; `issue-deps`
says so.

3 — Branch
----------

Off the base branch, never off whatever happens to be checked out. `pr` guards
against opening a pull request from `master`; the guard belongs *here* too,
before a line of code is written rather than after — a branch cut from the
wrong place is cheap to fix at step 3 and expensive at step 6.

4 — Implement
-------------

The constitution governs, under *While I write code*, *Before I commit* and
*When I hit a wall*. Nothing about how to write or commit the code is decided
here.

5 — Gates
---------

The constitution's *Before I call it done*, run at this point rather than
after the pull request, so that the draft opens green.

6 — Push, and open the draft pull request
-----------------------------------------

Push the branch, then invoke `pr`: it owns the branch guard, the existing-PR
check, draft state, and the call on whether there is an issue to reference —
there is, and it is this one. The `Issues` section of the body closes it, and
`issue-deps` treats that line as the write into the graph.

7 — Review
----------

**Wait for CI to report on the pushed head first.** A pull request opened
seconds ago has its checks queued, and `review`'s approval criteria read a
queued check as a failing one — so reviewing immediately buys a 👎 that says
nothing about the code.

Then invoke `review`. Not "dispatch a subagent to code review the branch": a
bare subagent gets no depth inference, no sensitive-path override, no
synthesis, and no handoff to `pr-threads`.

8 — Fix, answer, resolve, push
------------------------------

`review`'s walkthrough owns the fixing — the offer line it stops on, the
`[judgment]` discussion, and the execution plan. Push what it produces:
`review` refuses to read a branch whose local commits have not reached the
remote, and step 9's CI gate reads the remote head rather than this one.

`review` then offers to post its result to the pull request. **Take that
offer.** A review nobody posted leaves step 9's second gate vacuous — there
are no threads to answer, so nothing can fail it — and the record of why this
branch was judged ready never reaches the pull request. Posting is also what
hands the lifecycle to `pr-threads`, which owns every thread from there:
Claude's own, a human reviewer's, Claude Approvals', a bot's.

9 — Ready for review
--------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional, and the review it would normally trigger has
already run.


Three corrections
=================

The hand-typed prompt this skill replaces got three things wrong. These are
the three it corrects.

`draft: false` does not re-trigger `review`
-------------------------------------------

`review` fires on its own initiative before a draft is marked ready. Step 9 is
exactly that moment — and the review already ran, at step 7, on this same
branch.

**The step-7 review discharges it.** Do not review twice. `review`'s own
*Boundaries* section says the same from the other side, so that the rule holds
whichever file is being read at step 9.

The test is **provenance, not sameness**: record the head SHA at step 7, and
classify every commit made after it.

- **Answering** — a review finding, a review thread, a lint bot, a red check.
  These do not re-trigger step 7, however many of them there are. Answering a
  review is not new work, and re-reviewing the answer is the loop this rule
  exists to cut.
- **Changing what the code does** — new feature work, a scope addition, a
  merge or rebase that pulls in someone else's commits. This is a new diff.
  Step 7 runs again over it, once, before step 9, and its head SHA becomes the
  new mark.

The classification is per commit and the categories do not compound: a run
that only ever answers reaches step 9 with one review behind it, which is the
point.

Ready is a gate, not a step
---------------------------

"After fixing, set the PR to ready" reads as unconditional. It is not. The
pull request goes to ready only when **all** of these hold:

- CI is green on the head commit. **Pending is not green** — wait for it,
  rather than treating an unreported check as either answer.
- No review thread is unanswered or unresolved — from any reviewer, not only
  from the step-7 review.
- The step-7 review's verdict is 👍, or every 🔴 and 🟡 behind a 👎 has been
  fixed or explicitly deferred with the user's agreement.

Red CI or an open thread means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.

The review is a skill, not a subagent
-------------------------------------

Restated as step 7 because this is the correction most likely to be lost:
"dispatch a subagent" was written before `review` existed. It is `review`.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. There are four.

- **A blocked issue, or an issue whose intent is genuinely ambiguous.** The
  constitution forbids guessing at intent; this is that rule at step 2.
- **`review`'s offer line, and the `[judgment]` discussion behind it.** Both
  belong to `review`'s walkthrough — `review` is read-only until the offer is
  accepted, including for `[obvious]` fixes. Emit the offer and wait for it;
  do not pre-empt the pause, and do not add a second one around it.
- **The approach failing mid-implementation.** Cascading complexity, an
  assumption turning out wrong: stop and re-assess rather than pushing through
  to a pull request that documents a wrong turn.
- **CI still running**, at steps 7 and 9. A wait, not a question — nothing is
  asked, and nothing proceeds on a check that has not reported.

Everything else runs through. No permission is asked to commit, to push, or to
open the draft.


Non-goals
=========

- **Does not merge.** Ready for review is where this ends.
- **Does not close the issue by hand.** The pull request body does that, and
  the merge does it.
- **Does not fire on reading an issue.** Discussing #191 is not implementing
  it. "What does #191 say", "summarise #191", "is #191 still relevant" are
  questions; answer them, and do not cut a branch.
