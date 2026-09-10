---
name: undertake
description: >-
  This skill should be used whenever a GitHub issue, or a task this skill is
  explicitly invoked on, is being taken from its description to a pull request
  ready for review — including when the user says "/undertake", "undertake #34",
  "undertake adding a retry loop", "take #7", "work on issue 12", "start on
  that issue", "let's build #4", or "implement #191" — and on Claude's own
  move from reading an issue to writing code for it. It covers keeping that
  pull request current after it goes ready too — "the PR is behind master",
  "the branch is out of date", "bring the branch up to date with master".
  Two things fire the sequence from its start: an issue handed over to be
  worked on, or an explicit invocation of this skill.
  The issue is no longer required — an invocation carrying none opens one
  itself — but one of the two still is. "Implement a retry loop", "build the
  parser" and "fix this function", with neither an issue nor an invocation,
  are ordinary work and must NOT fire it. Supplies the order of the steps, the
  gates between them, the ready gate — which a branch behind its base does not
  pass — and the base merge that keeps the branch current before ready and
  after it; the review round it runs is `review-cycle`'s. Not for merely reading, summarising or
  discussing an issue, since "what does #191 say" is a question rather than an
  assignment.
---

# Undertake

An issue in, a pull request ready for review out, and kept current with its
base branch after that. Eleven steps, and this skill is the order they run in
— the first of them, `Open the issue`, skipped in the
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
| 6 | `Open the draft` | `pr` |
| 7 | `Review the head` | `review-cycle` |
| 8 | `Fix, answer, resolve, push` | `review-cycle` |
| 9 | `Ready for review` | `mcp__github__update_pull_request` |
| 10 | `Keep it current` | this skill, `review-cycle` |

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

The constitution governs, under *While you write code*, *Before you commit* and
*When you hit a wall*. Nothing about how to write or commit the code is decided
here.

6 — Open the draft
------------------

Push the branch, then invoke `pr`: it owns the branch guard, the existing-PR
check, draft state, and the call on whether there is an issue to reference —
there is, and it is this one. The `Issues` section of the body closes it, and
`issue-deps` treats that line as the write into the graph — and its
confirm-before-write rule does not bite here, because the edge is given by the
assignment rather than inferred from evidence. The issue being implemented is
the issue the pull request closes.

**The push is what runs the project's gates.** The constitution's *Before you
call it done* sends them to CI rather than to this machine, so no local gate
step comes before this one. The draft may open red, and `Review the head`
waits for the result either way. A red check is answered at `Fix, answer,
resolve, push`, and the ready gate below is what it has to satisfy in the end.

7 and 8 — Review the head, then fix, answer, resolve, push
----------------------------------------------------------

Invoke `review-cycle`. It owns the wait for CI on the pushed head — the
mechanism as well as the rule, under `How to wait` — the built-in
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
it and never needs to ask. A later round is `Keep it current`'s to earn, on the
same test and from the same mark.

9 — Ready for review
--------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional, and `Keep it current` runs before it — the
gate's first condition is that step's merge, so the sequence reaches it once
out of the table's order and then again on its own cadence.

It does not review. Marking a draft ready is a natural moment to reach for one,
and the branch was already reviewed at `Review the head` — whether that review
is stale is `review-cycle`'s provenance test and is answered inside the round,
not here.
Where `review` is live rather than in `attic/skills/`, this is also what
discharges the `draft: false` trigger in its description: it fires on exactly
the moment this step occupies, and a round already run on this head is that
trigger already answered.

10 — Keep it current
--------------------

Commits land on the base branch while the work is written and while a
reviewer reads, and a branch behind its base was reviewed and tested against a
tree nobody will merge into. This step brings the base branch in, and it is the
only step that runs more than once.

**Its first run is before `Ready for review`, not after it.** The gate below
carries the condition; this step carries the merge that satisfies it, and the
step is written once for both. Ready is not the end either, so it runs again on
the cadence under `When it looks`.

**The merge is `mcp__github__update_pull_request_branch`.** It merges the base
branch into the head server-side, so it needs no checkout: by the time this
runs, the session may be on another branch, and the working tree it had may be
gone. The call is the test as well as the merge — GitHub answers that the
branch is already up to date when there is nothing to bring in, so nothing
here has to compute how far behind the branch is.

**A merge, never a rebase.** A rebase rewrites history somebody is reading,
and it voids the mark `review-cycle` recorded at `Review the head`. A merge
commit leaves both intact.

When it looks
-------------

Once before `Ready for review`, as the gate's look rather than the cadence's.
The cadence itself starts from the ready pull request, unchanged: a check-in
every two minutes, one
`mcp__Claude_Code_Remote__send_later` at a time, carrying the instruction to
look again — the discipline `review-cycle`'s `The backstop` states for the same
reason.

**Never end a turn with the wake slot empty while the check-ins are running.**
They run from `Ready for review` until the pull request is merged or closed or
the user says to stop, and on a surface that has the scheduler at all — the
three exits below, and nothing narrower. Inside them the slot is that one
timer, held by the `trigger_id` the call returned, and it empties two ways: the
timer fires, or a CI wait cancels it at `End the wait`. Both are the same
instruction — fill it before the turn ends. What arms a check-in is therefore
an empty slot rather than a particular kind of wake: a wake with the timer
still in flight arms nothing, and a wake that found nothing to do still leaves
a wake behind it. A turn that ends with no timer and no subscription is a
session asleep on a pull request nobody else is watching, which is the report
[`0010`](../../docs/notes/0010-the-wake-slot-is-never-empty.md) records, and
[`0011`](../../docs/notes/0011-two-harnesses-one-skill-tree.md) scopes to
Claude Code.

**Two minutes, the same interval `review-cycle` waits on CI with.** A busy
`master` takes a commit every few minutes, so a slower check-in is a branch
kept behind on purpose, and the merge itself costs a call and a CI run that
this repository answers in seconds. Behind is the state to leave as briefly as
the scheduler allows.

**The one floor is a run in flight.** A check-in that finds CI from the last
merge still going does nothing: merging again restarts the run it is waiting
on. Where CI answers in seconds that floor almost never bites, and where it
answers in twenty minutes it is what keeps the branch from never being green.

A merge-conflict notice does not wait for the cadence either. It is the case
where behind has already cost something, and it is answered on the wake that
reports it.

The check-ins end when the pull request is merged or closed, or when the user
says to stop. A pull request nobody merges is not a reason to wake a session
for ever.

Where the scheduler is absent — a laptop — there are no check-ins. Do the step
whenever the session is next on the pull request, and say so once, rather than
claiming a watch the surface cannot keep.

After the merge
---------------

The head moved, so CI runs again. Wait for it the way `review-cycle`'s
`How to wait` says, and answer a red check under `Fix, answer, resolve, push`.
That wait borrows the wake slot for its backstop and gives it back at
`End the wait`: the check-ins above are armed again before that turn ends,
whichever way the wait ended, and after the round the wait was clearing the way
for rather than into it.
**Red CI is how a base merge reports that it broke something**: the base
changed what the branch depends on, the branch's own diff is untouched, and no
review of that diff would have found it.

**A clean merge does not earn a round.** `review-cycle`'s `Does it go again?`
classifies it under `Neither`, and the reason is what `/code-review` reads —
the pull request's three-dot diff, which after a clean merge is byte-identical
to what `Review the head` already reviewed. A base branch that moves daily
would otherwise buy a review a day for a diff nobody changed.

**A conflict resolution does.** Resolving a conflict rewrites the branch's own
files, which is `Changing what the code does` in that same classification.
One round over it, and `review-cycle` decides anything further.

A round after ready goes back to draft
--------------------------------------

`mcp__github__update_pull_request` with `draft: true` before `Review the head`
runs, and ready again through `The gate` below when the round closes — the
same gate, not a second one. A pull request under review is not ready for
review, and a reviewer must not be reading a branch that is changing
underneath them.


The gate
========

The hand-typed prompt this skill replaces got three things wrong. Two of them
were about the round rather than the sequence and left with it — `review-cycle`
carries *review once per diff* and *a reviewer, not a subagent*. The third is
this skill's, and it is the one `Ready for review` turns on.

Ready is a gate, not a step
---------------------------

"After fixing, set the PR to ready" reads as unconditional. It is not. The
pull request goes to ready only when **all** of these hold:

- The branch is current with its base branch and merges cleanly. `Keep it
  current` owns the merge that makes this true, and it is tested first because
  the merge moves the head: every condition below is about the head a reviewer
  will actually read, and a merge run after them would leave them answered
  about a commit nobody sees. A conflict is that step's stop, arriving early.
- CI is green on the head commit. **Pending is not green** — wait for it the
  way `review-cycle`'s `How to wait` says, rather than treating an unreported
  check as either answer. The mechanism has one home, and it is not this one.
- No review thread is unanswered or unresolved — from any reviewer, not only
  from the round at `Review the head`.
- Every finding that round raised has been fixed, or rejected with a reason on
  its thread, or deferred with the user's agreement.

A branch behind its base, red CI, or an open thread means it **stays a
draft**, and the reason is stated in one line. A red pull request marked ready
is a claim about the work that is not true, and so is a ready one that does not
merge.

The gate is also what a round at `Keep it current` returns through. That round
sends the pull request back to draft, and these four conditions are what let
it out again — the same four, tested again, rather than a second gate written
for the second round.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. Seven stop the
sequence. Five stop it to *ask* — the ambiguous issue, the request too vague
to write one for, the failing approach, a designated branch the harness states
ambiguously, and a base merge whose conflict is a real one. A blocked issue and
a running check stop it to report, and wait on something other than an answer.

- **A blocked issue, an issue whose intent is genuinely ambiguous, or a
  request too vague to write an issue for.** The constitution forbids guessing
  at intent; this is that rule, at `Open the issue` and at `Read the issue and
  its edges`.
- **More than one designated branch** for this repository, at `Cut the
  branch`'s first source. Guessing which one the harness will accept risks a
  claim already posted at `Claim the issue` that no push can honour.
- **The approach failing mid-implementation** — the constitution's *When you
  hit a wall*, at `Implement`. A pull request that documents a wrong turn is
  worse than no pull request.
- **CI still running**, at `Ready for review`. A wait, not a question —
  nothing is asked, and nothing proceeds on a check that has not reported.
- **A base merge that conflicts**, at `Keep it current`.
  `mcp__github__update_pull_request_branch` cannot resolve a conflict: it fails
  and changes nothing, so a resolution is a local merge, resolved and pushed.
  Resolve it where the resolution is plain — a moved import, two files that
  never met. Where both sides changed the same logic, picking either loses
  behaviour, and that is the constitution's rule against guessing at intent:
  name the conflicting files and wait.

The round at `Review the head` and `Fix, answer, resolve, push` has two stops
of its own — its own wait on CI, and a review finding whose fix is a real
trade-off. Both are `review-cycle`'s, and the second is `judgement-call`'s gate
applied inside it.

Everything else runs through. No permission is asked to open the issue, to
claim it, to commit, to push, or to open the draft.


Non-goals
=========

- **Does not merge the pull request.** `Keep it current` merges the base
  branch *into* the pull request and never the other way. Landing it is
  somebody else's.
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
