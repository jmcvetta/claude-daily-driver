---
name: pr
description: >-
  This skill should be used whenever a GitHub pull request is being opened or
  its title or body is being written or revised — including when the user says
  "/pr", "open a PR", "create a PR", "update the PR", "fix the PR title", or
  "rewrite the PR description", and including any use of `gh pr create` or
  `gh pr edit` on Claude's own initiative. Supplies the required PR title
  convention, body structure, draft state, and issue-reference format.
---

# PR Workflow

Open or update Github PR for the current feature branch.


PR Guidelines
=============

Branch
------

- If the current branch is `master`:
  1. Stop working
  2. Emit an error
  3. Await input


Already Existing PR
-------------------

First check whether there is already a PR for this branch.  If there is, update
the existing PR.
- Update both title and body of existing PR


PR Title
--------

- **Concise**: _Just enough_ detail
- **Conventional Commits**: Title MUST conform to Conventional Commits, and
  must have an appropriate CC type for the contents of the PR.


Initial State
-------------

- Open the PR as a draft


Body
----

- **One-Line Summary**: PR should begin with a very concise, single line summary of
  the PR. This summary will be visible in certain Github web UI components;
  there is a strict 85 character limit.
- **Salutation**: A poetic summary. Immediately after the one-line summary,
  separated by a blank line. A brief poem, in classical style, conveying the
  gist of the PR. Formatted in italics.
- **Executive Summary**: After the salutation, under heading "Summary", give a
  concise high level executive summary of the PR.  If you understand the
  importance of the PR for the larger software development or business
  perspectives, include that positioning.
- **Details**: After the summaries, include as much engineering detail as seems
  fitting.
- **Unopinionated**: This is a short description of the branch, NOT a code
  review. Do NOT do opine on code quality or security.


Github Issues
-------------

If this PR was created to fix/implement a Github Issue, include a reference to
the Issue.  Use the format shown below:

```
Issues
------

- Closes #123

```


