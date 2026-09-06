---
name: pr-title
description: >-
  This skill should be used whenever the title of a GitHub pull request is
  being written or revised — including when the user says "fix the PR title",
  "rename the PR", "that title is wrong", or asks what a PR should be called,
  and including any call Claude makes on its own initiative to
  `mcp__github__create_pull_request`, or to
  `mcp__github__update_pull_request` that sets a `title`. Supplies the
  Conventional Commits convention the title must conform to. Not for commit
  messages, and not for the PR body — that is `pr-body`.
---

# PR Title

The title of a pull request, whether it is being opened or corrected.

- **Concise**: _Just enough_ detail
- **Conventional Commits**: Title MUST conform to Conventional Commits, and
  must have an appropriate CC type for the contents of the PR.

The type is not decoration. Releases are cut from it: the type in a merged
PR's title becomes the squashed commit subject, and that subject is what
decides the next version. A `feat:` that was really a `fix:` ships a minor
release nobody asked for, and a `fix:` that was really a `feat:` hides one
somebody needed.
