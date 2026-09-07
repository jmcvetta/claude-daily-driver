---
name: undertake
description: >-
  This skill should be used whenever a GitHub issue, or a task this skill is
  explicitly invoked on, is being taken from its description to a pull request
  ready for review — including when the user says "/undertake", "undertake #34",
  "undertake adding a retry loop", "take #7", "work on issue 12", "start on
  that issue", "let's build #4", or "implement #191" — and on Claude's own
  move from reading an issue to writing code for it. Two things fire it: an
  issue handed over to be worked on, or an explicit invocation of this skill.
  The issue is no longer required — an invocation carrying none opens one at
  step 0 — but one of the two still is. "Implement a retry loop", "build the
  parser" and "fix this function", with neither an issue nor an invocation,
  are ordinary work and must NOT fire it. Supplies the order of the steps, the
  gates between them, and the ready gate the sequence ends on; the review round
  at steps 8 and 9 is `review-cycle`'s. Not for merely reading, summarising or
  discussing an issue, since "what does #191 say" is a question rather than an
  assignment.
---

# Undertake

An issue in, a pull request ready for review out. Eleven steps, and this skill
is the order they run in — the first of them, step 0, skipped in the common
case where the work already has an issue. Where it does not, step 0 opens one:
an issue is what this skill takes in, and untracked work is what running
without one leaves behind.

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
| 0 | Open the issue, where the work has none | this skill, `issue-deps` |
| 1 | Title the session from the issue | `session-title` |
| 2 | Read the issue and its edges | `mcp__github__issue_read`, `issue-deps` |
| 3 | Claim the issue for this session | this skill |
| 4 | Branch off the base branch | this skill |
| 5 | Implement | the constitution |
| 6 | Run the project's gates | the constitution |
| 7 | Push, and open the draft pull request | `pr` |
| 8 | Review | `review-cycle` |
| 9 | Fix, answer, resolve, push | `review-cycle` |
| 10 | Ready for review | `mcp__github__update_pull_request` |

0 — An issue, where there is none
---------------------------------

Skipped where an issue is already in hand — handed over in the request, which
is the common case, whether or not this skill was named. Where there is none,
this step is what supplies one, and the ten after it are unchanged: what would
otherwise happen is a branch, a review and a merge with no record of why any of
it was wanted, and a pull request body with nothing to close.

**Search before writing.** `mcp__github__search_issues` over the repository's
open issues first: work described in a prompt has often been described in an
issue already, and a second issue for it splits the trail in two. Where one
already covers the request, that is the issue — go on to step 1 with it, and
say which one it is, so a wrong match is corrected before the branch is cut.

Otherwise open one with `mcp__github__issue_write`. Title and body record what
was asked and no more: an issue is the statement of the request, and scope
invented for it is scope the pull request is then measured against. No
permission is asked — the invocation is the authorisation, and an issue is
cheap to close.

**A request too vague to write an issue for is a stop.** This is step 2's
intent gate arriving early, and the constitution's rule against guessing at
intent: an issue that guesses at what "done" means is worse than no issue,
because the guess then reads as settled.

Edges are `issue-deps`' business, and its confirm-before-write rule *does*
bite here — unlike the closing reference at step 7, a parent or a blocker for
a new issue is inferred from evidence rather than given by the assignment.

1 — Title the session
---------------------

As soon as there is an issue, and before anything else is read of it. Read the
issue *title* — that is all this step needs — and title the session from it
before reading the body. A web session otherwise takes its name from the first
prompt it received, which is the prompt that invoked this skill.
`session-title` has the form and the budget.

`session-title` stops where `set_session_title` does not exist, which on a
laptop it does not. That stop is the step's, not the sequence's: say so in a
line and go to step 2.

2 — Read the issue and its edges
--------------------------------

The body, and then the graph: parent, sub-issues, blocked-by. **An issue
blocked by an open one is a stop, not a start** — say which issue blocks it
and wait. Reading the graph is free and needs no confirmation; `issue-deps`
says so.

3 — Claim the issue
-------------------

One comment on the issue with `mcp__github__add_issue_comment`, saying that
this session has taken the work. It goes up before the branch is cut, because
an issue carrying no claim reads as unstarted, and two agents starting the same
issue is the waste the claim exists to prevent.

After step 2 rather than before it, because the edges decide whether there is
anything to claim: a blocked issue stops at step 2, and a claim on work that
is not starting is a false record.

Beyond the claim itself the comment carries two things, and both are read from
`mcp__Claude_Code_Remote__get_session` with `session_id` omitted, which
describes the caller:

- **The model serving the session** — its `session_context.model`, and its
  `external_metadata.last_served_model` where the two disagree, which is what
  a turn-scoped fallback looks like. Never a name recalled instead of read: the
  serving model is not always the configured one, and a provenance record that
  guesses is worse than one that says nothing.
- **The session**, as `https://claude.ai/code/session_…` built from the same
  call's session id. The identifier is what the reader needs; the link is that
  identifier and somewhere to go with it.

`get_session` exists only on the Claude Code Remote surface. On a laptop the
comment still goes up, and says the surface supplies neither — unlike
`session-title`, which has nothing to fall back on, a claim that names no model
is still a claim.

Once per run of this sequence. A second session undertaking the same issue
claims it too: that duplicate is the thing the claim makes visible, not a
thing to suppress.

4 — Branch
----------

Off the base branch, never off whatever happens to be checked out. `pr` guards
against opening a pull request from `master`; the guard belongs *here* too,
before a line of code is written rather than after — a branch cut from the
wrong place is cheap to fix at step 4 and expensive at step 7.

5 — Implement
-------------

The constitution governs, under *While I write code*, *Before I commit* and
*When I hit a wall*. Nothing about how to write or commit the code is decided
here.

6 — Gates
---------

The constitution's *Before I call it done*, run at this point rather than
after the pull request, so that the draft opens green.

7 — Push, and open the draft pull request
-----------------------------------------

Push the branch, then invoke `pr`: it owns the branch guard, the existing-PR
check, draft state, and the call on whether there is an issue to reference —
there is, and it is this one. The `Issues` section of the body closes it, and
`issue-deps` treats that line as the write into the graph — and its
confirm-before-write rule does not bite here, because the edge is given by the
assignment rather than inferred from evidence. The issue being implemented is
the issue the pull request closes.

8 and 9 — The review round
--------------------------

Invoke `review-cycle`. It owns the wait for CI on the pushed head, the built-in
`/code-review` at a level it names, the protocol every finding is answered and
resolved under, and the test for whether a later push has earned a second
review.

Two rows in the table above rather than one, because the ready gate tests them
separately: green CI on the head step 9 pushed, and every finding step 8 raised
answered. One round, two things to be true of it.

What is this skill's is where the round sits — after the draft is open, before
the ready gate, and once. `review-cycle` decides whether it goes again, and it
decides that from the head SHA it recorded, so step 10 never re-runs it and
never needs to ask.

10 — Ready for review
---------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional.

It does not review. Marking a draft ready is a natural moment to reach for one,
and the branch was already reviewed at step 8 — whether that review is stale is
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
  from the round at step 8.
- Every finding that round raised has been fixed, or rejected with a reason on
  its thread, or deferred with the user's agreement.

Red CI or an open thread means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. Five stop the
sequence. Three stop it to *ask* — the ambiguous issue, the request too vague
to write one for, and the failing approach. A blocked issue and a running check
stop it to report, and wait on something other than an answer.

- **A blocked issue, an issue whose intent is genuinely ambiguous, or a
  request too vague to write an issue for.** The constitution forbids guessing
  at intent; this is that rule, at steps 0 and 2.
- **The approach failing mid-implementation** — the constitution's *When I hit
  a wall*, at step 5. A pull request that documents a wrong turn is worse than
  no pull request.
- **CI still running**, at step 10. A wait, not a question — nothing is asked,
  and nothing proceeds on a check that has not reported.

The round at steps 8 and 9 has two stops of its own — its own wait on CI, and
a review finding whose fix is a real trade-off. Both are `review-cycle`'s, and
the second is `judgement-call`'s gate applied inside it.

Everything else runs through. No permission is asked to open the issue, to
commit, to push, or to open the draft.


Non-goals
=========

- **Does not merge.** Ready for review is where this ends.
- **Does not close the issue by hand.** The pull request body does that, and
  the merge does it.
- **Does not fire on reading an issue.** Discussing #191 is not undertaking
  it. "What does #191 say", "summarise #191", "is #191 still relevant" are
  questions; answer them, and do not cut a branch.
- **Does not fire on work it was not asked to undertake.** "Implement a retry
  loop", with neither an issue nor an invocation, is ordinary work, and running
  ten steps and a review round over it would be the heaviest possible way to
  write ten lines. Step 0 makes the issue reference optional; it does not make
  it the only thing that was ever doing the separating. An issue handed over,
  or this skill named — either fires it, and neither is ordinary work.
- **Does not open an issue for anything but the work in hand.** Step 0 tracks
  what was asked for. A bug noticed in passing is worth reporting to the user;
  it is not this run's second issue.
- **Does not review, and does not answer a review.** The round is
  `review-cycle`'s, and it is reachable without this sequence: a pull request
  opened by hand, or one a reviewer has come back to, gets the same round
  without an issue anywhere near it.
