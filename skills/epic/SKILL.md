---
name: epic
description: >-
  This skill should be used whenever a piece of work is being broken into more
  than one issue, or an epic issue is being opened, read or corrected —
  including when the user says "/epic", "break this down", "this is too big for
  one PR", "split #142", "plan the epic", "make an epic for this", "what can be
  worked in parallel", or "which of these has to land first", and on Claude's
  own move from a request that will not fit one pull request to writing issues
  for it. It is also where `undertake`'s `Open the issue` sends work too big for
  the one issue that step writes, and it fires on an attempt to undertake an
  epic, which carries no code. Supplies the two gates that decide whether there
  is an epic at all, what a task issue is, the one stop where the plan is agreed
  before anything is written, and the shape of the epic body — the sequencing
  and the waves that neither the sub-issue panel nor the dependency graph
  renders. The graph writes themselves are `issue-deps`'. Not for taking a task
  issue to a pull request, which is `undertake`, and never fired on work that
  fits one pull request.
---

# Epic planning

Work too big for one pull request becomes several task issues and one epic to
coordinate them. This skill is the order that happens in, the two gates that
decide whether it should happen at all, and what the epic body carries.

It is an orchestrator, in the same shape as `undertake` and `pr`: **it invokes,
it does not restate**. The graph writes are `issue-deps`', taking a task issue
to a pull request is `undertake`'s, and whether the plan is the user's to agree
is `judgement-call`'s. Where a step below names a rule one of those owns, it
names it as a pointer and cites the owner — a rule that acquires a second home
is one whose copy goes stale.

What this skill owns is the decomposition: what a task is, what an edge is for,
and what the epic body says that nothing else can render.

**The routes are per harness, and they live beside this file.** Every call the
steps below need is named in words here and resolved to a route there:
[`references/claude.md`](references/claude.md) for Claude Code,
[`references/omp.md`](references/omp.md) for Oh My Pi. Read the one for the
harness in use before `Open the issues`, which is the first step that writes
anything.

**Every step has a name, and the name is how it is cited.** The numbers order
the sequence and do nothing else: insert a step and all of them move, while a
name stays where it was put.
[`0005`](../../docs/notes/0005-steps-are-cited-by-name.md) is the decision and
`scripts/check-step-names.py` is what enforces it.


The sequence
============

| # | Step | Owner |
| - | ---- | ----- |
| 0 | `Size the work` | this skill |
| 1 | `Draft the plan` | this skill |
| 2 | `Agree the plan` | this skill, `judgement-call`, `issue-deps` |
| 3 | `Open the issues` | this skill, `undertake` |
| 4 | `Write the graph` | `issue-deps` |
| 5 | `Fill in the epic` | this skill |
| 6 | `Hand off` | `undertake` |

0 — Size the work
-----------------

An epic has to earn itself. One issue is the default, and it stays the default
unless **both** gates below open. Where either closes, say which one and carry
on as ordinary work — `undertake` where there is an issue or an invocation,
plain work where there is neither.

**Gate one: more than one pull request.** Would the whole change land as one
diff a reviewer reads in one sitting? Where it would, there is nothing to
coordinate. Size is measured in reviewable diff, never in hours or in files.

**Gate two: two parts that can merge separately.** Take each candidate part and
ask one question of it:

> Merge this part alone, and nothing else. Is the repository better off, and is
> CI still green?

A part answering no to either half is not a task. Where fewer than two parts
answer yes, the work is one issue however large it is: an epic over parts that
cannot merge separately is a table of contents. It costs everyone the issues
and buys a reader nothing.

An issue already in hand is sized the same way, and the answer is the same
answer. Where the gates close on it, it stays one issue and nothing is opened.

1 — Draft the plan
------------------

Nothing reaches GitHub here. The plan is drafted, and then it is agreed.

**A task is one pull request.** Where a candidate task needs two, split it
again rather than making it a second epic. This skill does not nest: a graph
two levels deep is read by nobody, and the second level is always a split
somebody declined to make.

**Each task issue records what was asked and no more**, the way `undertake`'s
`Open the issue` writes one. Scope invented to round out a plan is scope every
pull request is then measured against. A plan padded to look thorough is this
skill's manufacturing failure, and it is the same instinct `issue-deps` names
for edges.

**The order is edges, and the default is no edge.** Write a blocked-by edge
only where one task's code cannot be written until the other has landed — a
function that does not exist yet, a schema the second task reads. Two tasks
touching the same file is not a blocker. That is a merge conflict, and a merge
conflict is cheap. `issue-deps` owns what an edge means and what it must not
be used to record.

**Parallel is the absence of an edge.** Tasks with no open blocker run at the
same time, in their own sessions, and nothing has to be written for that to be
true. What the epic body carries is the *reading* of it, under `The epic body`
below.

2 — Agree the plan
------------------

The one stop. Put the plan in the reply — each task as a title and a line,
each edge as what it waits on, and the gates' answer from `Size the work` —
and write nothing until the user agrees.

It clears `judgement-call`'s gate twice over. A decomposition is a statement of
scope: it says what the pieces are and what done means for each, and craft does
not pick one split over another. And `issue-deps` writes an edge only on
confirmation, which `judgement-call` explicitly does not waive.

**One agreement covers the whole plan**, edges included. They are not confirmed
again, one at a time, at `Write the graph`.

3 — Open the issues
-------------------

**Search before writing**, for the reason `undertake`'s `Open the issue` gives:
a change described in a prompt has often been described in an issue already,
and a second issue for it splits the trail in two.

Where an issue already describes the whole change, **that issue becomes the
epic**. Rewrite its body to the shape below and give it the tasks as children.
Do not open a second one beside it.

The epic first, then the tasks, because a task names the epic as its parent and
the parent must exist to be named. The epic's body at this point is `End state`
and `Decisions` only — the waves are made of issue numbers that do not exist
yet, which is why `Fill in the epic` is a step of its own.

No permission is asked here. It was asked once at `Agree the plan`, and asking
again per issue is the same question eight times.

4 — Write the graph
-------------------

Two relationships, and `issue-deps` picks a client for each. They are not
always the same client, and on a web worker they are not.

- **Parent.** Every task is a sub-issue of the epic. Where the harness's issue
  client sets the parent as the task is created, that write already happened at
  `Open the issues`.
- **Blocked-by.** Only the edges `Draft the plan` named.

**An epic's children are not its blockers.** `issue-deps` says why:
decomposition and *must close first* are different claims. Do not write the
second because you wrote the first.

Verify from the other end, which `issue-deps` requires and explains — the write
response is the issue you modified, so it confirms nothing.

5 — Fill in the epic
--------------------

Replace the epic's body with the whole of `The epic body`, now that every task
has a number to put in it.

6 — Hand off
------------

Every task whose blockers are closed can start now, each in its own session,
each through `undertake`. Name them, rather than leaving the reader to derive
the list the first time.

**The epic is never undertaken.** It carries no code, so there is no branch to
cut and no pull request to open. `undertake` aimed at an epic is a stop: say
which issue is the epic, name the tasks that are ready, and undertake one of
those instead.

**The epic closes when its children close.** Nothing closes it by hand, and no
pull request body says it closes the epic — a pull request implements one task,
and that is the issue it closes.


The epic body
=============

Five parts. The first two are written at `Open the issues` and the rest at
`Fill in the epic`.

**End state.** One paragraph: what is true of the repository when every task
has merged. Not a list of the tasks — the waves below are that.

**Decisions.** The calls made while planning, one line each, with the task that
carries each one. This is the part no graph can hold: an edge is binary and
says nothing about why, and `issue-deps` names exactly this as where prose
stays. It is also what stops the same question being re-litigated in each
task's own thread.

**Delivery waves.** One heading per wave, naming what the wave waits on, and
under it the tasks with a line each:

```markdown
### Wave 1 — done
- #143 — Parse the manifest. Merged in PR #160.

### Wave 2 — in progress
- #144 — Validate against the schema. Needs #143's parsed manifest.
- #146 — Document the format. Independent of all of it; runs in parallel.

### Wave 3 — after #144
- #145 — Report a validation failure.
```

A wave is the set of tasks whose blockers have all closed, so **the waves are
what answers "which of these can be worked in parallel"**: everything inside
one heading runs at the same time, in its own session. Say so in the body for
anything a reader would not assume, the way the line on #146 above does.

**Optional.** Work that came out of the planning and is not a completion
criterion. It sits outside the waves so that it never blocks one, and so that
nobody reads it as owed.

**Completion criteria.** What has to be true for the epic to close. The tasks
closing is one of them and rarely all of them: an epic that changes how
something is installed is not done until somebody has installed it.

Two things the body does not carry. **No implementation detail** — that belongs
to each task's own issue, where the person doing the work is reading. And **no
checklist of the tasks**: the sub-issue panel renders progress from the graph,
for free and always correctly, and a hand-kept copy beside it rots.

**The waves are a rendering of the graph, and the graph wins.** Where the two
disagree the body is wrong and is fixed in the same turn. That is `issue-deps`'
own verification step — does the structured graph match what the prose says —
and an epic body is the largest prose claim about a graph this toolkit writes.


Where it stops and waits
========================

Three, and only the first is routine.

- **The plan**, at `Agree the plan`. One stop by design, covering the scope
  question and every edge at once.
- **A request too vague to decompose.** The constitution forbids guessing at
  intent, and a decomposition guesses harder than an issue does: it invents the
  boundaries, and then every pull request is measured against boundaries nobody
  chose. Ask what the whole change is for, and do not draft a plan around the
  answer you would have preferred.
- **A gate closing at `Size the work`.** A report rather than a question: say
  which gate closed, and carry on as ordinary work.


Non-goals
=========

- **Does not implement anything.** It writes issues, edges and one body.
  `undertake` takes each task from there.
- **Does not fire on work that fits one pull request.** That is `Size the
  work`'s first gate, and it is first for this reason. An epic over a two-file
  change costs a reader more than the change does.
- **Does not nest.** A task too big for one pull request is split again, never
  promoted to a second epic.
- **Does not keep a second copy of what the panel shows.** A wave heading
  carries its own state, because a wave is not something the sub-issue panel
  knows about. A checkbox beside each task is, and it rots.
- **Does not close the epic**, and does not close a task. Merging does both.
- **Does not sweep the issue list.** An epic is drafted for the work in hand.
  Reading through open issues looking for a set that could be grouped under one
  is `issue-deps`' manufacturing failure, one level up.
