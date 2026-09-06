---
name: pr
description: >-
  This skill should be used whenever a GitHub pull request is being opened for
  the current branch, or an existing one is being brought up to date as a
  whole — including when the user says "/pr", "open a PR", "create a PR",
  "raise a pull request", or "update the PR", and including any call Claude
  makes on its own initiative to `mcp__github__create_pull_request`, or to
  `mcp__github__update_pull_request` for anything wider than the title or the
  body alone. Supplies the branch guard, the existing-PR check, draft state
  and issue-reference format; the title comes from `pr-title` and the body
  from `pr-body`.
---

# PR Workflow

Open the GitHub PR for the current feature branch, or update the one that is
already open.

This skill is the orchestrator. The title convention lives in `pr-title` and
the body structure in `pr-body`; invoke each rather than restating it, so that
a later edit to a title or a body follows the same rules whether or not it
arrived through here.


Branch
------

- If the current branch is `master`:
  1. Stop working
  2. Emit an error
  3. Await input


Already Existing PR
-------------------

First check whether there is already a PR for this branch. If there is, update
the existing PR.
- Update both title and body of existing PR


Title
-----

Follow `pr-title`.


Body
----

Follow `pr-body`.


Initial State
-------------

- Open the PR as a draft


Github Issues
-------------

If this PR was created to fix/implement a Github Issue, include a reference to
the Issue. It goes last in the body, after the engineering detail. Use the
format shown below:

```
Issues
------

- Closes #123

```
