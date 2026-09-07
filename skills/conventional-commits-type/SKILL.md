---
name: conventional-commits-type
description: >-
  This skill should be used whenever the Conventional Commits type of a change
  is being chosen or checked — including when the user asks "is this a fix or
  a feat?", "what type should this PR be?", "should this be a refactor?",
  says "the type is wrong" or "that's not a fix", questions what version
  merging will cut, or when a Projected Releases comment on a pull request
  disagrees with what the author meant; and whenever `pr-title` needs the type
  for a title it is writing. Supplies the two gates and the one test that
  pick the type from what the change does, and what the type decides about
  the next release. Not for writing the title itself — that is `pr-title` —
  and not for commit messages, which are not Conventional Commits in this
  toolkit.
---

# Conventional Commits Type

The type is a claim about what merging does to the people who use the thing.
It is read by a machine that reads nothing else: release-please turns `feat`
into a minor version, a breaking change into a major one, and everything else
into a patch or nothing. So the type is decided from the change's **effect**,
never from what the diff looks like or how the work felt.

Two titles this toolkit reached for, and why both were too small:

- *"refactor: move the Terraform-shop review rules to project memory"* — the
  title #55 was written with, and corrected to `fix:` before it merged.
  Moving is what the author did; what the change **does** is stop a reviewer
  applying Terraform rules in every repository it is loaded in. A reviewer
  that behaves differently after the merge has not been refactored.
- *"fix(agents): inline the planning severity rubric into
  planning-fitness-reviewer"* — the title #54 merged with, where a `feat:`
  was warranted. A broken pointer prompted it, but the rubric it named was
  unreachable on every run, so no review had ever applied it. After the
  merge one does.

Both reached for the smaller word, and that is the direction this skill
exists to stop. An over-typed change cuts a version one size too large; an
under-typed one hides from the changelog section and the version where the
people it matters to would look for it.


The question
============

> What does the thing do after the merge that it did not do before, or stop
> doing that it did?

"The thing" is whatever the repository ships, seen by whoever consumes it: a
caller of a library, a user of a CLI, CI running a workflow, a session
loading a plugin. **In a plugin whose product is prose, prose is code.** What
Claude reads and acts on is `skills/`, `agents/`, `context/` and `hooks/`, so
a change there goes to the tests below exactly as code would, and one that
changes what Claude does is never `docs` however much it reads as writing. A
typo or a rewording there that changes nothing still is. Outside those
directories — `README.md`, `docs/` and their kind — prose is documentation.

Answer the question first, from the diff, before naming a type. The answer
decides the type; the diff's shape does not.


The tests
=========

One case skips them. A **wholesale undo** of a change already merged is a
`revert`, whatever the undone change was typed — patch, with its own
changelog section. Where the undone change had already been released, gate 1
below applies on top of it: `revert!:`, with the footer, because taking back
what a consumer may already be using breaks them. A *partial* undo is not a
revert; it is an ordinary change, and the gates type it.

Otherwise the first two are gates: where one fires it settles the type, and
nothing below it runs.

1. **Does it break anyone?** A caller, a configuration, or a workflow that
   worked before the merge and does not after it. Then the type it would
   otherwise have carries `!` — `feat!:`, `fix!:` — and the body carries a
   `BREAKING CHANGE:` footer saying what broke. Major bump.

2. **Does the behaviour change — what the thing returns, what it decides,
   what it does as a side effect?** If none of those move, the change is one
   of the silent types: `refactor` for code restructured to do the same
   thing, `perf` for the same thing done faster, `chore` for a dependency
   bump or a housekeeping change, `style` for formatting, and `docs`,
   `test`, `build`, `ci`. Speed, formatting and internal
   shape are not behaviour here — that is what lets `perf` and `refactor` be
   silent at all — but an output, a decision or a side effect is, and a
   `refactor` that moves one is not a refactor.

Past both gates the behaviour changes, and the only question left is `fix` or
`feat`. One test settles it:

3. **Could the thing already do this, and merely do it wrong?**

   - **Yes — `fix`.** The behaviour was promised and delivered incorrectly.
     The test is against the intent, not the code: a rule shipping to
     repositories it does not describe is a defect, and removing it is a fix
     however much the diff reads as a move.
   - **No — `feat`.** The thing can now do something it could not do before.
     The issue's label, the branch name and the story of how the work started
     do not change that: a bug report that ends in a capability ends in a
     `feat`.

The trap sits between the two, and it is what got #54 wrong: **a capability
that was specified but never once worked has not regressed.** The agent's own
text named a rubric, which reads like a promise broken — but no run had ever
applied it, so nothing was restored and something arrived for the first time.
Ask what a consumer *observed*, never what a document promised. Where even
that cannot settle it, prefer `feat`, for the reason the two examples give.

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
`feat`.

`revert` takes no part in that ranking, because it describes a whole pull
request or none of it. An undo carrying unrelated work alongside it — like
any two changes of consequence in one pull request — wants splitting, which
is `pr`'s business.


What the type releases
======================

| Type | Release-please | In the changelog |
| ---- | -------------- | ---------------- |
| any type with `!` | major | yes, under *Breaking Changes* |
| `feat` | minor | yes, under *Features* |
| `fix` | patch | yes, under *Bug Fixes* |
| `perf` | patch | yes, under *Performance Improvements* |
| `revert` | patch | yes, under *Reverts* |
| `docs` `style` `chore` `refactor` `test` `build` `ci` | patch | hidden |

The list is release-please's, checked by the *PR Title Check* workflow; a
type outside it (`wip`, `hotfix`) is rejected there, and a miscased one
(`Feat:`) is worse — it passes the changelog and bumps a patch. `feature` is
accepted as a synonym for `feat`; write `feat`.

What a given title will actually cut is not worth reasoning out. In this
repository the *Projected Releases* check comments it on every pull request
but release-please's own, and that comment is the test: read it against what
the change warrants, and treat a bug fix that projects a minor version, or a
new capability that projects a patch, as a title to correct. Where the check
does not run, the table above is the best available answer.
