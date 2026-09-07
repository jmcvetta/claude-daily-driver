---
name: implement
description: >-
  This skill should be used whenever a GitHub issue is being taken from its
  description to a pull request ready for review — including when the user says
  "/implement", "implement #191", "work on issue 12", "take #7", "start on
  that issue", or "let's build #4", and on Claude's own move from reading an
  issue to writing code for it. Supplies the order of the steps, the gates
  between them, and the rule that keeps the branch from being reviewed twice.
  Do NOT use
  this skill for merely reading, summarising, or discussing an issue —
  "what does #191 say" is a question, not an assignment.
---

# Implement

An issue in, a pull request ready for review out. Nine steps, and this skill
is the order they run in.

It is an orchestrator, in the same shape as `pr`: **it invokes, it does not
restate**. The title convention lives in `pr-title`, the pull request itself in
`pr`, what is worth asking the user in `judgement-call`, and the engineering
standard in the constitution. Where a step below names a rule one of those
owns, it names it as a pointer and cites the owner — a rule that acquires a
second home here is one whose copy goes stale, and a citation is what makes the
drift visible. The one exception is flagged where it occurs, at step 8.

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
| 7 | Review | the built-in `/code-review` |
| 8 | Fix, answer, resolve, push | this skill |
| 9 | Ready for review | `mcp__github__update_pull_request` |

1 — Title the session
---------------------

Before anything else. Read the issue *title* — that is all this step needs —
and title the session from it before reading the body. A web session otherwise
takes its name from the first prompt it received, which is the prompt that
invoked this skill. `session-title` has the form and the budget.

`session-title` stops where `set_session_title` does not exist, which on a
laptop it does not. That stop is the step's, not the sequence's: say so in a
line and go to step 2.

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
`issue-deps` treats that line as the write into the graph — and its
confirm-before-write rule does not bite here, because the edge is given by the
assignment rather than inferred from evidence. The issue being implemented is
the issue the pull request closes.

7 — Review
----------

**Wait for CI to report on the pushed head first.** A pull request opened
seconds ago has its checks queued, and a queued check is not a passing one — a
review that reads it as either answer is reviewing the runner, not the code.

Then run the session's built-in **`/code-review`** against the pull request,
with `--comment` so the findings land as inline review comments. Name an
effort level rather than taking the remembered one, and read
[`docs/decisions/0001-built-in-review-surface.md`](../../docs/decisions/0001-built-in-review-surface.md)
first: what a given level buys depends on the model family, and on Opus 5
`medium` and `high` are the same cell — only `max` verifies.

Not "dispatch a subagent to code review the branch". A bare subagent inherits
no rubric, posts nothing, and leaves no thread behind for step 8 to answer.

`--comment` is what makes step 8 possible at all: findings on the pull request
are threads, and threads are the record of why the branch was judged ready.
Findings that stay in the terminal are gone by the next session.

**Record the head SHA you reviewed.** Step 9's test is measured from it, and
nothing else records it.

8 — Fix, answer, resolve, push
------------------------------

Every finding gets a verdict, on its thread, and the thread is closed:

1. **Implemented** — fix it, reply saying so, resolve the thread.
2. **Rejected** — reply with the reason, and resolve it anyway. A rejection is
   an answer; only silence is not.
3. **Never left open silently.** The one rule this skill states rather than
   cites, because since `pr-threads` was retired nothing else states it.

The tools are `mcp__github__pull_request_read` with `get_review_comments` to
read the threads, `mcp__github__add_reply_to_pull_request_comment` to answer,
and `mcp__github__resolve_review_thread` to close. Every reviewer is the same
protocol — Claude's own findings, a human's, Claude Approvals', a bot's.

Then push. Step 9's CI gate reads the remote head, and a fix that never left
the laptop is not in it.

9 — Ready for review
--------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional, and it does not re-run step 7.


Three corrections
=================

The hand-typed prompt this skill replaces got three things wrong. These are
the three it corrects.

Step 9 does not re-run step 7
-----------------------------

Marking a draft ready is a natural moment to review, and the branch was
already reviewed at step 7. **Review once.** The question this answers is not
academic: step 8 puts commits on the branch, so by step 9 the head is never
the one step 7 read, and a rule that keyed on sameness would re-review every
run forever.

The test is therefore **provenance, not sameness**: record the head SHA at
step 7, and classify every commit made after it.

- **Answering** — a review finding, a review thread, a lint bot, a red check.
  These do not re-trigger step 7, however many of them there are. Answering a
  review is not new work, and re-reviewing the answer is the loop this rule
  exists to cut.
- **Changing what the code does** — new feature work, a scope addition, a
  merge or rebase that pulls in someone else's commits. This is a new diff.
  Step 7 runs again over it, once, before step 9, and its head SHA becomes the
  new mark.

Where one commit is both — a merge from the base branch made to get a red
check green — **changing what the code does wins**. A merge brings in code
nothing has reviewed, whatever its reason.

Otherwise the classification is per commit and the categories do not compound:
a run that only ever answers reaches step 9 with one review behind it, which
is the point. Where `review` is live rather than in `attic/skills/`, this is also
what discharges the `draft: false` trigger in its description — it fires on
exactly the moment step 9 occupies, and a review already run on this head is
that trigger already answered.

Ready is a gate, not a step
---------------------------

"After fixing, set the PR to ready" reads as unconditional. It is not. The
pull request goes to ready only when **all** of these hold:

- CI is green on the head commit. **Pending is not green** — wait for it,
  rather than treating an unreported check as either answer.
- No review thread is unanswered or unresolved — from any reviewer, not only
  from step 7.
- Every finding step 7 raised has been fixed, or rejected with a reason on its
  thread, or deferred with the user's agreement.

Red CI or an open thread means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.

Review is a reviewer, not a subagent
------------------------------------

Restated as step 7 because this is the correction most likely to be lost. A
subagent handed "code review this branch" inherits no rubric, has no effort
level anybody chose, and posts nothing — so its findings die in the transcript
and step 8 has nothing to answer. The built-in `/code-review` is the reviewer,
and `--comment` is what makes its findings survive the session.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. Four go to the user;
the waits and hard stops at steps 7 and 9 are named there and ask nothing.

- **A blocked issue, or an issue whose intent is genuinely ambiguous.** The
  constitution forbids guessing at intent; this is that rule at step 2.
- **A review finding whose fix is a real trade-off**, in the sense
  `judgement-call` gives that phrase: two defensible approaches differing in
  something the user owns. That skill owns the gate, and it is the gate for
  every question this skill would otherwise ask. A finding whose fix the
  standard already picks is not one of these — fix it and say so.
- **The approach failing mid-implementation** — the constitution's *When I hit
  a wall*, at step 4. A pull request that documents a wrong turn is worse than
  no pull request.
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
