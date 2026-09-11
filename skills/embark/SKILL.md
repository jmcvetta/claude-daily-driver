---
name: embark
description: >-
  This skill should be used whenever an epic's task issues are being put to
  work in more than one session at once, or a fleet already at sea is being
  watched — including when the user says "/embark", "work the epic", "launch
  the wave", "start the next wave", "run these issues in parallel", "open a
  session for each of these", or "how is the epic going", and on Claude's own
  move from an epic whose plan is written to opening a session per task —
  `mcp__Claude_Code_Remote__create_session` on Claude Code. Supplies the wave
  it reads off the graph, the session it opens per task on the model that task
  issue records, the muster roll it posts to the epic instead of asking, the
  watch it keeps through the pull requests rather than through the session
  client, and the backstop for a session that has gone quiet. Not for breaking
  work into task issues, which is `epic`, and not for taking one task issue to
  a pull request, which is `undertake` — and never fired on a single issue.
---

# Embark

An epic in, a fleet of sessions out, and the epic reported ready to close when
the last of them is home. `epic` decomposes the work and stops; this skill is
what then works it, wave after wave, one session per task issue.

It is an orchestrator, in the same shape as `epic` and `undertake`: **it
invokes, it does not restate**. The decomposition is `epic`'s, taking one task
issue to a pull request is `undertake`'s, the graph reads are `issue-deps`',
the name a session carries is `session-title`'s, and the engineering standard
is the constitution's. Where a step below names a rule one of those owns, it
names it as a pointer and cites the owner — a rule that acquires a second home
is one whose copy goes stale.

What this skill owns is the dispatch and the watch: which tasks sail together,
what is written down as they sail, and what is done about one that does not
come back.

**The routes are per harness, and they live beside this file.** Every call the
steps below need is named in words here and resolved to a route there:
[`references/claude.md`](references/claude.md) for Claude Code,
[`references/omp.md`](references/omp.md) for Oh My Pi. Read the one for the
harness in use before `Read the epic`, which is the first step with a route in
either table. Omp has no session-opening client at all, so that file is a stop
rather than a table, and it says so.

**Every step has a name, and the name is how it is cited.** The numbers order
the sequence and do nothing else: insert one and all of them move, while a name
stays where it was put.
[`0005`](../../docs/notes/0005-steps-are-cited-by-name.md) is the decision and
`scripts/check-step-names.py` is what enforces it.


The sequence
============

| # | Step | Owner |
| - | ---- | ----- |
| 0 | `Read the epic` | this skill, `issue-deps` |
| 1 | `Title the session` | `session-title` |
| 2 | `Take the wave` | this skill, `epic` |
| 3 | `Open the sessions` | this skill, `undertake` |
| 4 | `Post the muster roll` | this skill |
| 5 | `Watch the wave` | this skill |
| 6 | `Recover a session` | this skill |
| 7 | `Report the epic ready` | this skill |

`Take the wave` is the loop point rather than `Read the epic`: a wave that
comes in returns there, and the epic is read again from GitHub each time,
because the graph moved while the wave was at sea. `Recover a session` is
reached from `Watch the wave` and returns to it.

0 — Read the epic
-----------------

The epic's body, its sub-issues, and the blocked-by edges among them. Reading
the graph is free and needs no confirmation; `issue-deps` says so.

**An issue with no sub-issues is not an epic**, and that is the stop of that
name below. A task issue handed over is `undertake`'s, and work not decomposed
yet is `epic`'s.

Read the epic's comments too, because `Take the wave` needs to know which tasks
are at sea already.

1 — Title the session
---------------------

`session-title` has the form and the budget, and the epic's number and title
are what the title is built from. This session is the one the user watches the
fleet from, so it is named for the epic rather than for any task in it.

Where the harness cannot set a title, that stop is the step's rather than the
sequence's: say so in a line and go on to `Take the wave`.

2 — Take the wave
-----------------

The batch that sails together: every open task issue of this epic whose
blockers are all closed, less the ones already at sea.

**The graph decides what can run; the epic's `Sequencing` decides what does.**
The two are not the same question, and `epic` writes both on purpose:

- **Blocked in the graph, placed early in the body** is a disagreement. The
  graph wins — `epic` says so, and says the body is fixed in the same turn.
- **Unblocked in the graph, placed in a later wave by the body** is not a
  disagreement. It is the scheduling choice `epic` requires that task's line to
  state, and it is honoured: the task waits for its wave.

**Already at sea is read from the record, never assumed.** A task is at sea
when a muster roll on the epic names a session for it, or when its own issue
carries an `undertake` claim comment. Either is enough, and the second is what
covers a task somebody started by hand. A session is opened once per task, not
once per invocation of this skill — re-entering after the watching session died
is the case this rule exists for, and launching a second session on a task
already claimed is two agents writing one branch.

**A claim from a session this skill did not open is worth a line to the user**,
and is still not a reason to launch a second one. That collision is the thing
`undertake`'s claim exists to make visible.

Where every open task is blocked by something open, there is no wave, and that
is a stop that reports.

3 — Open the sessions
---------------------

One session per task issue in the wave, opened in the same environment as this
one, all of them before the watch starts. Each carries four things and no more:

- **A prompt naming its task issue and asking for it to be undertaken**, and
  nothing else. The issue is the statement of the work; a summary of it in the
  prompt is a second copy that can disagree with the first, and the session
  reads the issue itself at `undertake`'s `Read the issue and its edges`.
- **The model the task issue records**, taken from the `Model:` line `epic`
  writes as the last line of the body. Where there is no such line the session
  inherits this one's model, which `epic` states is the working default.
  **This skill does not choose**, and does not second-guess a line it is given:
  the judgement was made when the task was sized, and re-making it here on less
  information is how it gets made worse.
- **A title**, in `session-title`'s form for the task issue. It is what makes a
  list of five running sessions readable at the moment the wave launches, which
  is before any of them has reached its own `Title the session` and set the same
  string.
- **The environment's own permissions**, inherited rather than narrowed or
  named. A task session runs unattended, and a session opened in a mode that
  blocks for a human approval is a session that never starts work.

**A model identifier the session client rejects sinks one ship, not the
fleet.** The call fails rather than falling back; report that task, launch the
rest of the wave, and do not substitute an identifier of your own — the
constitution forbids the guess, and `epic` owns the line that was wrong.

No permission is asked here. `Waves launch without confirmation` below is why.

4 — Post the muster roll
------------------------

One comment on the epic as the wave launches, and it goes up **after** the
sessions are open, because it records their identifiers.

It is what this skill does instead of asking, so it has to be readable by
somebody who did not ask for it. The wave's heading from `Sequencing`, and then
one row per task:

```markdown
### Wave 2 — after #143 · at sea

| Task | Session | Model |
| ---- | ------- | ----- |
| #144 — Validate against the schema. | [session_01AbC…](https://claude.ai/code/session_01AbC…) | `claude-sonnet-5` |
| #147 — Document the format. | [session_01DeF…](https://claude.ai/code/session_01DeF…) | `claude-opus-5`, inherited |
```

**Say which model was inherited.** A reader cannot otherwise tell a judgement
`epic` made from a default nobody chose, and the difference is the whole reason
the `Model:` line exists.

**The wave headings carry state, and nothing else moves it.** `epic` writes
`done` and `in progress` into the epic's `Sequencing` at decomposition time and
never returns. This skill marks the wave as it launches and again as it comes
in, in the epic's own body and in `epic`'s own form. That is the one edit this
skill makes to an epic body; everything else about it is `epic`'s.

5 — Watch the wave
------------------

**The watch runs through GitHub, not through the session client.** Sessions can
be opened, interrupted, archived and messaged, and none of that reads back what
one is doing. Pull requests do: each task session produces a branch and a pull
request, and a pull request reports its own checks, its review threads and its
merge. It is also where the user is already looking, and it outlives the session
that opened it.

So on every wake:

- **Subscribe to each task's pull request** as it appears, once. Events then
  start a turn on their own.
- **Read the epic's graph.** A task issue closes when the pull request that
  names it merges, and that is the test for a task being home — not the session
  status, which reports a session that has stopped, never a job that is done.
- **The wave is in when every task issue in it is closed.** Mark the wave `done`
  in the epic's body, and go back to `Take the wave`.

**This skill does not manage the branches.** `undertake`'s `Keep it current`
already merges the base branch into each head on its own two-minute cadence, so
a sibling whose base moved heals itself, and a real content conflict stops that
session rather than this one. An orchestrator resolving a conflict in code it
never wrote is the wrong hand on the tiller.

**One wake slot, and a turn never ends with it empty** while a wave is at sea.
[`0010`](../../docs/notes/0010-the-wake-slot-is-never-empty.md) is the rule,
and it is the same one `undertake` and `review-cycle` hold — one durable timer,
kept by the identifier the call returned, filled again before the turn ends
whenever it is empty. A wake that finds the timer still in flight arms nothing.

**Ten minutes, not two.** `undertake` checks in every two because its branch
goes stale while it waits and the merge that fixes that is cheap. Nothing here
decays that way: this backstop catches a dropped event and a dead session, the
worst case it bounds is one wave delayed by one interval, and a wave of five is
already holding five two-minute cadences of its own. A second-by-second watch
over the top of them is quota spent on nothing, and the constitution's
*Delegation* rule says whose money that is.

**A quiet pull request is what the backstop is for.** Quiet means its session is
no longer running while its pull request is open and unmerged, or its pull
request has not moved across two check-ins while its session says it is.
Neither is a verdict on its own — a session can be running and stuck, and a
pull request can be legitimately waiting on a person — so read the pull request
before acting, and act at `Recover a session`.

**A pull request green, ready for review and unmerged is waiting on a person.**
Say so once, and then let the check-ins run silently. Repeating it on every
wake is a session shouting at somebody who has already been told.

6 — Recover a session
---------------------

Reached from `Watch the wave`, and it returns there.

- **Steer a running session**: interrupt it first, then send the correction.
  A message to a session mid-turn queues behind whatever that turn is doing,
  which is usually the thing being corrected.
- **Messaging is one way.** The session receives it and cannot answer, so the
  result of a correction is read from the pull request, never from the session.
- **Reopen a session that cannot be recovered**: archive it, and open a fresh
  one on the same task issue, pushing to the **same branch** rather than to one
  of its own. The branch is recorded twice already — in the claim comment
  `undertake` posted on the task issue, and as the head of the pull request if
  one is open — and either is read rather than guessed. Given that branch the
  new session re-enters `undertake` on work in progress: the claim is found,
  the open pull request is found, and the work is resumed rather than started
  again beside itself.
- **A session that stopped to ask is a stop**, and it is this skill's fourth.
  The question cannot be read from here, so it cannot be answered from here.

7 — Report the epic ready
-------------------------

When the last wave is in: one comment on the epic saying it is ready to be
closed, and stop. The check-ins end there.

**The epic is not closed here.** `epic` states that no pull request closes an
epic and that it is closed by hand against its own `Summary`, which is a test
about the repository rather than about the tasks. This skill has merged nothing
and is the wrong judge of it.


Waves launch without confirmation
=================================

`epic` stops once, at `Agree the plan`, and what it agrees there is the whole
decomposition — the tasks, the edges, and therefore the waves. Asking again
before each wave asks the same question a second time, and a plan that has to
be re-agreed wave by wave was not agreed.

So the first wave and every wave after it launches unasked. `Post the muster
roll` is what goes up instead: the user sees five sessions start without having
been asked to approve them starting, and sees on the epic which task each is
on, which session is which, and what each is running. A record written as the
thing happens is worth more than a question answered before it.

This does not relax anything else. The stops below still stop, and nothing here
touches the constitution's own gates.


Where it stops and waits
========================

Five, and two of them are reports rather than questions.

- **An issue that is not an epic**, at `Read the epic`. A report: say which
  issue it is and which skill takes it — `undertake` for a task issue, `epic`
  for work not yet decomposed.
- **A harness with no session-opening client.** The whole skill, not one step.
  Say so, name the tasks whose blockers are closed, and stop — which is `epic`'s
  `Hand off` reached without a fleet.
  [`references/omp.md`](references/omp.md) is the harness this is written for.
- **No wave to take**, at `Take the wave`. A report: every open task is blocked
  by something open, so name the issue that blocks and wait for it.
- **A session that stopped to ask**, at `Recover a session`. Name the task, its
  session and its pull request, and hand the question to the user. Guessing at
  the answer is guessing at intent twice over — the constitution forbids it
  once, and this skill did not write the code being asked about.
- **The epic's graph disagreeing with its body about a blocker**, at `Take the
  wave`. The graph wins, so the wave is not in doubt; the body is wrong, and
  fixing it is `epic`'s `Fill in the epic` rather than an edit made in passing
  here.

Everything else runs through. No permission is asked to open a session, to
comment on the epic, to subscribe to a pull request, or to launch the next
wave.


Non-goals
=========

- **Does not decompose.** The tasks, the edges and the waves are `epic`'s, and
  an epic whose plan is wrong is corrected there rather than worked around
  here.
- **Does not implement, review, or answer a review.** Each task session does
  its own, through `undertake` and the round that skill runs.
- **Does not choose a model.** The task issue records one and this skill passes
  it on. Staying dumb is the point: the planner knew which task was a
  documentation edit, and this skill does not.
- **Does not manage the branches.** It does not serialise merges and it does not
  resolve a conflict between two sibling branches. `undertake`'s `Keep it
  current` does the first, and the session that owns the code does the second.
- **Does not merge a pull request.** `undertake` does not either, for the same
  reason: what lands is the one decision worth a person. A green, ready pull
  request is reported, once.
- **Does not close the epic.** It says the epic is ready and stops there.
- **Does not fire on one issue.** Opening a session to undertake a single task
  is the task session's own job, and running a fleet of one costs an epic, a
  muster roll and a watch to save nothing.
- **Does not sweep for epics.** It works the epic in hand. Reading the issue
  list for others to put to sea is `epic`'s manufacturing failure, one level up.
