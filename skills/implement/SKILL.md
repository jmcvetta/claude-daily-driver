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
the constitution. Nothing here repeats them. A rule that starts being restated
here is a rule with two homes, and the copy is the one that goes stale.

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
| 6 | Open the draft pull request | `pr` |
| 7 | Review | `review` |
| 8 | Fix, answer, resolve | `review`'s walkthrough, then `pr-threads` |
| 9 | Ready for review | `mcp__github__update_pull_request` |

1 — Title the session
---------------------

Before anything else, including before reading the issue body in full. A web
session otherwise takes its name from the first prompt it received, which is
the prompt that invoked this skill. `session-title` has the form and the
budget.

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

The constitution governs: tests ship in the same commit as the code they
cover, commits are focused, named files are staged. No permission is asked to
commit.

5 — Gates
---------

The project's own tests, linters, formatters, and whatever validation it
defines — **run, not reasoned about**. This is the constitution's "before I
call it done", and it sits before the pull request rather than after it, so
that the draft opens green.

6 — Draft pull request
----------------------

`pr` owns it: the branch guard, the existing-PR check, draft state, and the
call on whether there is an issue to reference — there is, and it is this one.
The `Issues` section of the body closes it, and `issue-deps` treats that line
as the write into the graph.

7 — Review
----------

Invoke `review`. Not "dispatch a subagent to code review the branch": a bare
subagent gets no depth inference, no sensitive-path override, no synthesis,
and no handoff to `pr-threads`.

8 — Fix, answer, resolve
------------------------

`review`'s walkthrough owns the fixing; `pr-threads` owns the threads. A
finding is implemented or rejected with a reason, on the thread, and the
thread is resolved. **Never left open silently.**

Findings arriving from anyone else — a human reviewer, Claude Approvals, a
lint bot — are the same protocol, and are `pr-threads`'s from the moment they
appear.

9 — Ready for review
--------------------

`mcp__github__update_pull_request` with `draft: false`. See the gate below
first: this step is conditional, and the review it would normally trigger has
already run.


Three corrections
=================

The hand-typed prompt this skill replaces got three things wrong. They are the
only original content here.

`draft: false` does not re-trigger `review`
-------------------------------------------

`review` fires on its own initiative before a draft is marked ready. Step 9 is
exactly that moment — and the review already ran, at step 7, on this same
branch.

**The step-7 review discharges it.** Do not review twice. If the branch has
changed since step 7 in any way beyond the fixes that review itself agreed —
new feature work, a rebase that pulled in someone else's change, a scope
addition — that is a new diff, and step 7 runs again over it before step 9.
Fixes made under `review`'s own walkthrough do not count as such a change;
re-reviewing the answer to a review is the loop this rule exists to cut.

Ready is a gate, not a step
---------------------------

"After fixing, set the PR to ready" reads as unconditional. It is not. The
pull request goes to ready only when **all** of these hold:

- CI is green on the head commit.
- No review thread is unanswered or unresolved.
- The step-7 review's verdict is 👍, or every 🔴 and 🟡 behind a 👎 has been
  fixed or explicitly deferred with the user's agreement.

Any one of them failing means it **stays a draft**, and the reason is stated
in one line. A red pull request marked ready is a claim about the work that is
not true.

The review is a skill, not a subagent
-------------------------------------

Restated as step 7 because this is the correction most likely to be lost:
"dispatch a subagent" was written before `review` existed. It is `review`.


Where it stops and waits
========================

Autonomy is the point, so each pause has to earn itself. There are three.

- **A blocked issue, or an issue whose intent is genuinely ambiguous.** The
  constitution forbids guessing at intent; this is that rule at step 2.
- **A `[judgment]` finding.** `review`'s own walkthrough owns this pause — do
  not pre-empt it, and do not add a second one around it.
- **The approach failing mid-implementation.** Cascading complexity, an
  assumption turning out wrong: stop and re-assess rather than pushing through
  to a pull request that documents a wrong turn.

Everything else runs through. No permission is asked to commit, to open the
draft, or to apply an `[obvious]` fix.


Non-goals
=========

- **Does not merge.** Ready for review is where this ends.
- **Does not close the issue by hand.** The pull request body does that, and
  the merge does it.
- **Does not fire on reading an issue.** Discussing #191 is not implementing
  it. "What does #191 say", "summarise #191", "is #191 still relevant" are
  questions; answer them, and do not cut a branch.
