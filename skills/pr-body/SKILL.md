---
name: pr-body
description: >-
  This skill should be used whenever the body of a GitHub pull request is
  being written or revised — including when the user says "rewrite the PR
  description", "update the PR body", "the PR description is thin", or asks
  for more detail in a PR, and including any call Claude makes on its own
  initiative to `mcp__github__create_pull_request`, to
  `mcp__github__update_pull_request` that sets a `body`, to
  `gh pr edit --body` on a harness that still reaches for it, or to Omp's
  `github` tool's `pr_create` op (`body`) and `gh pr edit --body` for
  revisions. Supplies the
  required structure: one-line summary, salutation in verse, executive
  summary, engineering detail, and the issue-reference section that closes it.
  Not for the PR title — that is `pr-title`.
---

# PR Body

The body of a pull request, whether it is being opened or rewritten. In order:

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

Opening a pull request is the `pr` skill's job. When the body is being written
as part of opening one, follow `pr` as well, for the branch guard, the
existing-PR check and draft state.


Issues
------

If the pull request fixes or implements a Github Issue, the body ends with an
`Issues` section, last, after the engineering detail. Use the format shown
below:

```
Issues
------

- Closes #123

```

When revising a body that already carries such a section, carry it across. A
rewrite that drops a `Closes #123` silently stops the merge from closing the
issue.
