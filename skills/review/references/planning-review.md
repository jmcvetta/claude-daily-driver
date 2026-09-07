Planning-Doc Review Contract
============================

The contract for reviewing a **planning-class** diff: a proposal under
`docs/planning/` or `docs/proposals/`, any `README.md`, or any `CLAUDE.md`.
The `review` skill passes this file to `planning-fitness-reviewer` at dispatch
time; this copy is the canonical version.

It replaces the four-tier code rubric in `SKILL.md` rather than supplementing
it. A planning finding graded on the code rubric lands in the wrong tier
every time, because the two rubrics measure different things.


What the document is for
------------------------

These are bird's-eye documents, not implementation specs. A planning proposal
becomes an epic after merge, with subissues carrying the implementation
detail. The doc's job is **fitness for purpose, direction, scope, goals, and
the general shape of how the parts fit together** — what goes where, and how
the pieces relate.

A planning doc is **not meant to be mechanically buildable**. If it were, it
would be enormous — and it would be doing the subissues' job. Demanding enough
detail that an implementer could code from the doc alone is asking the wrong
document to do the wrong job.

Review on planning terms. Good questions: Is the problem framed clearly? Are
goals and non-goals explicit? Is the scope right-sized? Are the major
components and their relationships sound? Are there strategic risks or
alternatives unaddressed? Is this the right direction?

**Do not** flag the absence of implementation detail; that belongs in the
subissues. The test is *"is this the right plan?"*, not *"is this ready to
build?"*


Severity rubric
---------------

- **🔴 Critical — Wrong-spec.** The plan itself is unsound: wrong direction,
  can't deliver its goal, ignores a strictly better alternative, solves the
  wrong problem, or is a probable wild goose chase.
- **🟡 Important — Over-spec or significant omission.** Any descent below
  planning altitude (implementation detail in a planning doc), or a
  load-bearing piece of planning content missing (goals, non-goals,
  alternatives, scope).
- **🟢 Minor — Grammar, phrasing, tersity, quasi-mechanical nits in the
  prose.** Never used for altitude issues — wrong altitude is always 🟡 or 🔴.
- **🔵 Nitpick — Cosmetic polish below the Minor threshold.**

**Altitude never grades below 🟡.** That floor is the point of the rubric: a
paragraph of implementation detail reads like a prose nit and is not one, and
grading it 🟢 is how a planning doc quietly turns into a spec nobody agreed to
write.


Evidence
--------

Cite the section heading or line range, and quote short evidence — a clause,
not a passage. A finding about a document is as answerable as a finding about
code, and it is answerable only if the reader can find what it refers to.

Be willing to call a plan unsound if it is. Diplomatic hedging that lets a
wild goose chase through is the failure this review exists to prevent.
