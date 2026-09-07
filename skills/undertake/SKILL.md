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
  The issue is no longer required — an invocation carrying none opens one
  itself — but one of the two still is. "Implement a retry loop", "build the
  parser" and "fix this function", with neither an issue nor an invocation,
  are ordinary work and must NOT fire it. Supplies the order of the steps, the
  gates between them, and the ready gate the sequence ends on; the review round
  it runs is `review-cycle`'s. Not for merely reading, summarising or
  discussing an issue, since "what does #191 say" is a question rather than an
  assignment.
---

# Undertake

An issue in, a pull request ready for review out. Eleven steps, and this skill
is the order they run in — the first of them, `Open the issue`, skipped in the
common case where the work already has an issue. Where it does not, that step
supplies one: an issue is what this skill takes in, and untracked work is what
running without one leaves behind.

It is an orchestrator, in the same shape as `pr`: **it invokes, it does not
restate**. The title convention lives in `pr-title`, the pull request itself in
`pr`, the review round in `review-cycle`, what is worth asking the user in
`judgement-call`, and the engineering standard in the constitution. Where a
step below names a rule one of those owns, it names it as a pointer and cites
the owner — a rule that acquires a second home here is one whose copy goes
stale, and a citation is what makes the drift visible. There is no exception.

What this skill owns is the sequencing and the gates between the steps.

**Every step has a name, and the name is how it is cited** — here and in every
other file that refers to one. The numbers order the sequence and do nothing
else: insert a step and all of them move, while a name stays where it was put.
That is why `review-cycle` names `Open the draft` and `Ready for review`
rather than the positions those two occupy today.
[`0005`](../../docs/notes/0005-steps-are-cited-by-name.md) is the decision and
`scripts/check-step-names.py` is what enforces it.


The sequence
============

| # | Step | Owner |
| - | ---- | ----- |
| 0 | `Open the issue` | this skill, `issue-deps` |
| 1 | `Title the session` | `session-title` |
| 2 | `Read the issue and its edges` | `mcp__github__issue_read`, `issue-deps` |
| 3 | `Claim the issue` | this skill |
| 4 | `Cut the branch` | this skill |
| 5 | `Implement` | the constitution |
| 6 | `Run the gates` | the constitution |
| 7 | `Open the draft` | `pr` |
| 8 | `Review the head` | `review-cycle` |
| 9 | `Fix, answer, resolve, push` | `review-cycle` |
| 10 | `Ready for review` | `mcp__github__update_pull_request` |

`Review the head` and `Fix, answer, resolve, push` are `review-cycle`'s own
first two stages, named identically on purpose: they are the same work, and one
name for it is what lets either skill cite it without reaching into the other's
numbering. `Ready for review` is not among them — that gate is this skill's,
and `review-cycle` says so.

0 — Open the issue
------------------

Skipped where an issue is already in hand — handed over in the request, which
is the common case, whether or not this skill was named. Where there is none,
this step is what supplies one, and the ten after it are unchanged: what would
otherwise happen is a branch, a review and a merge with no record of why any of
it was wanted, and a pull request body with nothing to close.

**Search before writing.** `mcp__github__search_issues` over the repository's
open issues first: work described in a prompt has often been described in an
issue already, and a second issue for it splits the trail in two. Where one
already covers the request, that is the issue — go on to `Title the session`
with it, and say which one it is, so a wrong match is corrected before the
branch is cut.

Otherwise open one with `mcp__github__issue_write`. Title and body record what
was asked and no more: an issue is the statement of the request, and scope
invented for it is scope the pull request is then measured against. No
permission is asked — the invocation is the authorisation, and an issue is
cheap to close.

**A request too vague to write an issue for is a stop.** This is the intent
gate of `Read the issue and its edges` arriving early, and the constitution's
rule against guessing at intent: an issue that guesses at what "done" means is
worse than no issue, because the guess then reads as settled.

Edges are `issue-deps`' business, and its confirm-before-write rule *does*
bite here — unlike the closing reference at `Open the draft`, a parent or a
blocker for a new issue is inferred from evidence rather than given by the
assignment.

1 — Title the session
---------------------

As soon as there is an issue, and before anything else is read of it. Read the
issue *title* — that is all this step needs — and title the session from it
before reading the body. A web session otherwise takes its name from the first
prompt it received, which is the prompt that invoked this skill.
`session-title` has the form and the budget.

`session-title` stops where `set_session_title` does not exist, which on a
laptop it does not. That stop is the step's, not the sequence's: say so in a
line and go on to `Read the issue and its edges`.

2 — Read the issue and its edges
--------------------------------

The body, and then the graph: parent, sub-issues, blocked-by. **An issue
blocked by an open one is a stop, not a start** — say which issue blocks it
and wait. Reading the graph is free and needs no confirmation; `issue-deps`
says so.

The comments too, because `Claim the issue` needs to know whether it is claimed
already — by this session, which means the sequence is being re-entered, or by
another.

3 — Claim the issue
-------------------

One comment on the issue with `mcp__github__add_issue_comment`, saying that
this session has taken the work. It goes up before the branch is cut, because
an issue carrying no claim reads as unstarted, and two agents starting the same
issue is the waste the claim exists to prevent.

After `Read the issue and its edges` rather than before it, because the edges
decide whether there is anything to claim: a blocked issue stops there, and a
claim on work that is not starting is a false record.

Beyond the claim itself the comment carries three things:

- **The branch** the work will be committed on, named before it is cut and
  **linked** — `[branch](https://github.com/OWNER/REPO/tree/BRANCH)`.
  `OWNER/REPO` is the repository the branch will be **pushed to**, which on a
  fork is not the repository the issue is in: read it from
  `session_context.outcomes[].git_repository.git_info.repo`, the same entry
  `Cut the branch`'s first source reads, or from the `origin` remote where
  there is no
  call. Built from the issue's repository instead, the link 404s for good
  rather than only until the push, and the trade below stops holding. A reader
  of the issue can otherwise reach the session but not the code: until the pull
  request opens at `Open the draft` nothing on GitHub ties the issue to a
  branch, and the
  whole implementation happens inside that window. The link 404s until that
  push. Write it anyway: the cost is a dead link over the window where there is
  nothing to see, and the alternative is a name the reader must build a URL
  from by hand. `Cut the branch` owns where the name comes from; this step
  announces it, and is bound to what was announced.
- **The model that served the turn** — `external_metadata.last_served_model`,
  which is what actually ran and moves with a fallback that leaves the rest of
  the session untouched. Where `session_context.model` or `configured_model`
  disagrees with it, name that too: the gap between what a session was set to
  run and what ran is the half of the record worth having. Never a name
  recalled instead of read — a provenance record that guesses is worse than
  one that says nothing.
- **The session**, as `https://claude.ai/code/session_…` built from the same
  call's session id. The identifier is what the reader needs; the link is that
  identifier and somewhere to go with it.

The model and the session are read from `mcp__Claude_Code_Remote__get_session`
— the call `session-title` documents, on the one surface it says supplies it —
and so is the branch, where the harness designated one.

Where that call is unavailable the comment still goes up, and says the surface
supplied neither. `session-title` stops there because a title it cannot set is
nothing; a claim that names no model is still a claim. The branch is not lost
with them: `Cut the branch`'s second and third sources need no call at all —
the project's convention where it documents one, and `issue-<number>-<slug>`
otherwise.

**Once per session, not once per run.** A sequence re-entered — its blocker
cleared, the issue handed over again — does not claim what it has claimed
already, and the comments read at `Read the issue and its edges` are what show
it. A claim from a *different* session is not suppressed: that collision is the
thing the claim exists to make visible, and it is worth a line to the user
before the branch is cut.

4 — Cut the branch
------------------

Off the base branch, never off whatever happens to be checked out. `pr` guards
against opening a pull request from `master`; the guard belongs *here* too,
before a line of code is written rather than after — a branch cut from the
wrong place is cheap to fix here and expensive at `Open the draft`.

The *name* is settled one step earlier, because `Claim the issue` announced
it. This step uses the announced name and does not choose a fresh one — a claim
naming a
branch nobody pushed to is worse than a claim naming none. Three sources, in
this order:

1. **The branch the harness designated for this session**, where it designated
   one. `mcp__Claude_Code_Remote__get_session` reports it at
   `session_context.outcomes[].git_repository.git_info.branches`. Both of those
   are arrays: read the outcome whose `git_info.repo` names the repository this
   work will be pushed to, and take the one branch it lists. Where it lists
   more than one, the source has not answered — that is the stop below, not a
   pick. Nothing is chosen here otherwise: a web worker refuses a push
   anywhere else.
   `external_metadata.current_branches` is a different field and answers a
   different question — what is checked out, which before this step need not
   be the designated branch.
2. **The project's own convention**, where it documents one.
3. **`issue-<number>-<slug>`**, failing both. The number leads for the reason
   `session-title` gives it the lead in a session title: it is the identifier
   a reader matches a branch against. The slug is two or three words from the
   issue title.

5 — Implement
-------------

The constitution governs, under *While I write code*, *Before I commit* and
*When I hit a wall*. Nothing about how to write or commit the code is decided
here.

6 — Run the gates
-----------------

The constitution's *Before I call it done*, run at this point rather than
after the pull request, so that the draft opens green.

7 — Open the draft
------------------

Push the branch, then invoke `pr`: it owns the branch guard, the existing-PR
check, draft state, and the call on whether there is an issue to reference —
there is, and it is this one. The `Issues` section of the body closes it, and
`issue-deps` treats that line as the write into the graph — and its
confirm-before-write rule does not bite here, because the edge is given by the
assignment rather than inferred from evidence. The issue being implemented is
the issue the pull request closes.

8 and 9 — Review the head, then fix, answer, resolve, push
----------------------------------------------------------

Invoke `review-cycle`. It owns the wait for CI on the pushed head, the built-in
`/code-review` at a level it names, the protocol every finding is answered and
resolved under, and the test for whether a later push has earned a second
review.

Two rows in the table above rather than one, because the ready gate tests them
separately: green CI on the head `Fix, answer, resolve, push` left behind, and
every finding `Review the head` raised answered. One round, two things to be
true of it.

What is this skill's is where the round sits — after the draft is open, before
the ready gate, and once. `review-cycle` decides whether it goes again, and it
decides that from the head SHA it recorded, so `Ready for review` never re-runs
it and never needs to ask.

10 — Ready for review
---------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional.

It does not review. Marking a draft ready is a natural moment to reach for one,
and the branch was already reviewed at `Review the head` — whether that review
is stale is `review-cycle`'s provenance test and is answered inside the round,
not here.
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
  from the round at `Review the head`.
- Every finding that round raised has been fixed, or rejected with a reason on
  its thread, or deferred with the user's agreement.

Red CI or an open thread means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. Six stop the
sequence. Four stop it to *ask* — the ambiguous issue, the request too vague
to write one for, the failing approach, and a designated branch the harness
states ambiguously. A blocked issue and a running check stop it to report, and
wait on something other than an answer.

- **A blocked issue, an issue whose intent is genuinely ambiguous, or a
  request too vague to write an issue for.** The constitution forbids guessing
  at intent; this is that rule, at `Open the issue` and at `Read the issue and
  its edges`.
- **More than one designated branch** for this repository, at `Cut the
  branch`'s first source. Guessing which one the harness will accept risks a
  claim already posted at `Claim the issue` that no push can honour.
- **The approach failing mid-implementation** — the constitution's *When I hit
  a wall*, at `Implement`. A pull request that documents a wrong turn is worse
  than no pull request.
- **CI still running**, at `Ready for review`. A wait, not a question —
  nothing is asked, and nothing proceeds on a check that has not reported.

The round at `Review the head` and `Fix, answer, resolve, push` has two stops
of its own — its own wait on CI, and a review finding whose fix is a real
trade-off. Both are `review-cycle`'s, and the second is `judgement-call`'s gate
applied inside it.

Everything else runs through. No permission is asked to open the issue, to
claim it, to commit, to push, or to open the draft.


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
  eleven steps and a review round over it would be the heaviest possible way
  to write ten lines. `Open the issue` makes the issue reference optional; it
  does not make it the only thing that was ever doing the separating. An issue
  handed over, or this skill named — either fires it, and neither is ordinary
  work.
- **Does not open an issue for anything but the work in hand.** `Open the
  issue` tracks what was asked for. A bug noticed in passing is worth reporting
  to the user; it is not this run's second issue.
- **Does not review, and does not answer a review.** The round is
  `review-cycle`'s, and it is reachable without this sequence: a pull request
  opened by hand, or one a reviewer has come back to, gets the same round
  without an issue anywhere near it.
