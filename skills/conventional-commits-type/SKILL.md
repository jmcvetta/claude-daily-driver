---
name: conventional-commits-type
description: >-
  This skill should be used whenever the Conventional Commits type of a change
  is being chosen or checked — including when the user asks "is this a fix or
  a feat?", "what type should this PR be?", "should this be a refactor?",
  says "the type is wrong" or "that's not a fix", questions what version
  merging will cut, or when a Projected Releases comment on a pull request
  disagrees with what the author meant; and whenever `pr-title` needs the type
  for a title it is writing. Supplies the tests that pick the type from what
  the change does, the order they run in, the tie-break, and what the type
  decides about the next release. Not for writing the title itself — that is
  `pr-title` — and not for commit messages, which are not Conventional Commits
  in this toolkit.
---

# Conventional Commits Type

The type is a claim about what merging does to the people who use the thing.
It is read by a machine that reads nothing else: release-please turns `feat`
into a minor version, a breaking change into a major one, and everything else
into a patch or nothing. So the type is decided from the change's **effect**,
never from what the diff looks like or how the work felt.

Two titles this toolkit got wrong, and why:

- *"refactor: move the Terraform-shop review rules to project memory"*
  (#55). Moving is what the author did; what the change **does** is stop a
  reviewer applying Terraform rules in every repository it is loaded in. A
  reviewer that behaves differently after the merge has not been refactored.
  That is a `fix`.
- *"fix(agents): inline the planning severity rubric into
  planning-fitness-reviewer"* (#54). A broken pointer prompted it, but after
  the merge the reviewer applies a severity rubric it never carried before.
  Capability the thing did not have is a `feat`, whatever prompted it.

Both erred downward, and downward is the direction this skill exists to stop.


The question
============

> What does the thing do after the merge that it did not do before, or stop
> doing that it did?

"The thing" is whatever the repository ships, seen by whoever consumes it: a
caller of a library, a user of a CLI, CI running a workflow, a session
loading a plugin. **In a plugin whose product is prose, prose is code.** A
line changed in `skills/`, `agents/`, `context/` or `hooks/` changes what
Claude does, and is never `docs`; `docs` is `README.md`, `docs/` and their
kind.

Answer the question first, from the diff, before naming a type. The answer
decides the type; the diff's shape does not.


The tests, in order
===================

First match wins.

1. **Does it break anyone?** A caller, a configuration, or a workflow that
   worked before the merge and does not after it. Then the type it would
   otherwise have carries `!` — `feat!:`, `fix!:` — and the body carries a
   `BREAKING CHANGE:` footer saying what broke. Major bump.

2. **Does behaviour change at all?** If nothing a consumer can observe is
   different, the change is one of the silent types: `refactor` for code
   restructured to do the same thing, `perf` for the same thing done faster,
   `style` for formatting, `docs`, `test`, `build`, `ci`, `chore`. A
   `refactor` that changes an output, a decision or a side effect is not one.

3. **Was the old behaviour wrong?** The thing did what its own spec, its
   docs or its author's stated intent says it should not, or failed to do
   what they say it does. Correcting that is a `fix`. The test is against
   the intent, not the code: a rule shipping to repositories it does not
   describe is a defect, and removing it is a fix however much the diff
   reads as a move.

4. **Otherwise it is new.** Behaviour the thing did not have before is a
   `feat`. The issue's label, the branch name and the story of how the work
   started do not change that: a bug report that ends in a capability ends
   in a `feat`.

When two types still fit after the tests, **the one that says more wins**:
`feat` over `fix`, `fix` over `refactor`. Both errors above hedged downward,
and downward is the costly direction — an over-typed change cuts a version
one size too large, while an under-typed one hides from the changelog section
and the version where the people it matters to would look for it.

A check on the answer: write the changelog line. *"Bug Fixes: reviewers no
longer apply Terraform-shop rules in every repository"* reads true;
*"Features: …"* for the same change reads absurd. Whichever heading the line
belongs under is the type.


What does not decide it
=======================

- **The size of the diff.** One line can be a `feat`; five hundred can be a
  `fix`.
- **The proportion of it that is tests, docs or generated files.** The
  behaviour change is the type; the files carrying it are not.
- **What the author called it** in the issue, the branch name, the commit
  messages or the conversation. Commit messages here are prose by rule and
  carry no type at all.
- **How the work felt.** A move, a cleanup, a tidy-up — all descriptions of
  the doing, none of them of the effect.


One type for the whole pull request
===================================

Squash-merge makes the title the one commit master receives, so the type
describes everything merged. Where a pull request carries more than one kind
of change, the highest-impact one decides: breaking over `feat`, `feat` over
`fix`, `fix` over the silent types. A `feat` that includes a refactor is a
`feat`. Two unrelated changes of consequence are a pull request to split,
which is `pr`'s business.


What the type releases
======================

| Type | Release-please | In the changelog |
| ---- | -------------- | ---------------- |
| any type with `!` | major | yes, under *Breaking Changes* |
| `feat` | minor | yes, under *Features* |
| `fix` | patch | yes, under *Bug Fixes* |
| `perf` | patch | yes, under *Performance Improvements* |
| `revert` | patch | yes, under *Reverts* |
| `docs` `style` `chore` `refactor` `test` `build` `ci` | patch at most | hidden |

The list is release-please's, checked by the *PR Title Check* workflow; a
type outside it (`wip`, `hotfix`) is rejected there, and a miscased one
(`Feat:`) is worse — it passes the changelog and bumps a patch. `feature` is
accepted as a synonym for `feat`; write `feat`.

What a given title will actually cut is not worth reasoning out. In this
repository the *Projected Releases* check comments it on every pull request,
and that comment is the test: read it against what the change warrants, and
treat a bug fix that projects a minor version, or a new capability that
projects a patch, as a title to correct. Where the check does not run, the
table above is the best available answer.
