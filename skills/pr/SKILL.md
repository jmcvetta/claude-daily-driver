---
name: pr
description: >-
  This skill should be used whenever a GitHub pull request is being opened for
  the current branch, or an existing one is being brought up to date as a
  whole — including when the user says "/pr", "open a PR", "create a PR",
  "raise a pull request", or "update the PR", and including any call Claude
  makes on its own initiative to `mcp__github__create_pull_request`, to
  `mcp__github__update_pull_request` for anything wider than the title or the
  body alone, or to `gh pr create` / `gh pr edit` on a harness that still
  reaches for them. Supplies the branch guard, the existing-PR check, draft
  state and the call on whether there is an issue to reference; the title
  comes from `pr-title` and the body, issue reference included, from
  `pr-body`.
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
- Update both title and body of existing PR — the title under `pr-title`,
  which does not rewrite a type this session did not write


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

If this PR was created to fix/implement a Github Issue, reference it. Deciding
that there is an issue to reference is this skill's call; the section's format
and placement in the body belong to `pr-body`.
