---
name: undertake
description: >-
  This skill should be used whenever a GitHub issue is being taken from its
  description to a pull request ready for review — including when the user says
  "/undertake", "undertake #34", "take #7", "work on issue 12", "start on
  that issue", "let's build #4", or "implement #191" — and on Claude's own
  move from reading an issue to writing code for it. Every one of those names
  a tracked issue, which is the point: this skill fires on a verb plus an
  issue reference, never on the verb alone. Supplies the order of the steps,
  the gates between them, and the ready gate the sequence ends on; the review
  round at steps 7 and 8 is `review-cycle`'s. Do NOT use this skill for work
  that is not a tracked issue — "implement a retry loop", "build the parser"
  and "fix this function" are ordinary work and must not fire it — nor for
  merely reading, summarising or discussing an issue, since "what does #191
  say" is a question rather than an assignment.
---

# Undertake

An issue in, a pull request ready for review out. Nine steps, and this skill
is the order they run in.

It is an orchestrator, in the same shape as `pr`: **it invokes, it does not
restate**. The title convention lives in `pr-title`, the pull request itself in
`pr`, the review round in `review-cycle`, what is worth asking the user in
`judgement-call`, and the engineering standard in the constitution. Where a
step below names a rule one of those owns, it names it as a pointer and cites
the owner — a rule that acquires a second home here is one whose copy goes
stale, and a citation is what makes the drift visible. There is no exception.

What this skill owns is the sequencing and the gates between the steps.


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
| 7 | Review | `review-cycle` |
| 8 | Fix, answer, resolve, push | `review-cycle` |
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

7 and 8 — The review round
--------------------------

Invoke `review-cycle`. It owns the wait for CI on the pushed head, the built-in
`/code-review` at a level it names, the protocol every finding is answered and
resolved under, and the test for whether a later push has earned a second
review.

Two rows in the table above rather than one, because the ready gate tests them
separately: green CI on the head step 8 pushed, and every finding step 7 raised
answered. One round, two things to be true of it.

What is this skill's is where the round sits — after the draft is open, before
the ready gate, and once. `review-cycle` decides whether it goes again, and it
decides that from the head SHA it recorded, so step 9 never re-runs it and
never needs to ask.

9 — Ready for review
--------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional.

It does not review. Marking a draft ready is a natural moment to reach for one,
and the branch was already reviewed at step 7 — whether that review is stale is
`review-cycle`'s provenance test and is answered inside the round, not here.
Where `review` is live rather than in `attic/skills/`, this is also what
discharges the `draft: false` trigger in its description: it fires on exactly
the moment this step occupies, and a round already run on this head is that
trigger already answered.


The gate
========

The hand-typed prompt this skill replaces got three things wrong. Two of them
were about the round rather than the sequence and left with it — `review-cycle`
carries *review once per diff* and *a reviewer, not a subagent*. The third is
this skill's, and it is the one the sequence ends on.

Ready is a gate, not a step
---------------------------

"After fixing, set the PR to ready" reads as unconditional. It is not. The
pull request goes to ready only when **all** of these hold:

- CI is green on the head commit. **Pending is not green** — wait for it,
  rather than treating an unreported check as either answer.
- No review thread is unanswered or unresolved — from any reviewer, not only
  from the round at step 7.
- Every finding that round raised has been fixed, or rejected with a reason on
  its thread, or deferred with the user's agreement.

Red CI or an open thread means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. Three stop the
sequence; the ones that stop it to *ask* are the ambiguous issue and the
failing approach. A blocked issue and a running check stop it to report, and
wait on something other than an answer.

- **A blocked issue, or an issue whose intent is genuinely ambiguous.** The
  constitution forbids guessing at intent; this is that rule at step 2.
- **The approach failing mid-implementation** — the constitution's *When I hit
  a wall*, at step 4. A pull request that documents a wrong turn is worse than
  no pull request.
- **CI still running**, at step 9. A wait, not a question — nothing is asked,
  and nothing proceeds on a check that has not reported.

The round at steps 7 and 8 has two stops of its own — its own wait on CI, and
a review finding whose fix is a real trade-off. Both are `review-cycle`'s, and
the second is `judgement-call`'s gate applied inside it.

Everything else runs through. No permission is asked to commit, to push, or to
open the draft.


Non-goals
=========

- **Does not merge.** Ready for review is where this ends.
- **Does not close the issue by hand.** The pull request body does that, and
  the merge does it.
- **Does not fire on reading an issue.** Discussing #191 is not undertaking
  it. "What does #191 say", "summarise #191", "is #191 still relevant" are
  questions; answer them, and do not cut a branch.
- **Does not fire on work that is not a tracked issue.** "Implement a retry
  loop" is ordinary work, and running nine steps and a review round over it
  would be the heaviest possible way to write ten lines. The issue reference is
  what distinguishes the two, and it is not optional.
- **Does not review, and does not answer a review.** The round is
  `review-cycle`'s, and it is reachable without this sequence: a pull request
  opened by hand, or one a reviewer has come back to, gets the same round
  without an issue anywhere near it.
