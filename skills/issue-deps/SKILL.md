---
name: issue-deps
description: >-
  This skill should be used whenever a relationship between GitHub issues is
  being recorded, read, or relied upon — one issue blocking another, a
  sub-issue or parent, or which pull request closes an issue. It fires on the
  literal "/issue-deps", on natural phrasings ("this is blocked by #123",
  "what's blocking this", "make it a sub-issue of the epic", "what does this
  depend on"), on noticing while planning or while writing a PR body that some
  other work must land first, and on Claude's own use of
  `mcp__github__sub_issue_write`, `mcp__github__issue_read` with
  `get_sub_issues` or `get_parent`, `mcp__github__issue_write` with
  `parent_issue_number`, or of a `Closes #123` line in a pull request body.
  Supplies the two clients these relationships need, the script for the half
  the MCP cannot reach, and the rule that a relationship is proposed from
  evidence and confirmed by the user, never asserted.
---

# Issue relationships

Three relationships, one graph, **two clients** — and the split between the
clients is not incidental. Reach for the wrong one and the answer comes back
wrong-shaped rather than absent.

| Relationship | How to reach it |
| ------------ | --------------- |
| **Blocked-by / blocking** | `scripts/issue-deps.sh`. No MCP tool, no MCP field. |
| **Sub-issue / parent** | The MCP: `sub_issue_write`, `issue_read` with `get_sub_issues` / `get_parent`, `issue_write` with `parent_issue_number`. Cross-repo works. |
| **Which PR closes an issue** | The MCP only: `issue_read` returns `closed_by_pull_requests`. REST has no such field. |

The one thing that is *written* as prose is the `Closes #123` line in a pull
request body. Treat the graph as the artifact and that line as one unvalidated
writer into it.


Propose from evidence; never assert
===================================

The failure mode of this skill is **inventing relationships**. An agent handed
a job feels obliged to produce output, and this job's output is edges.

- A wrong edge is worse than a missing one. It blocks work silently, and nobody
  thinks to look for a relationship they did not create.
- So: state the evidence, name the edge it implies, and **ask**. Write only on
  confirmation.
- Reading is free and needs no confirmation. Writing never is.

The firing moment is real and specific — a dependency is *discovered* while
planning work, or while writing a PR body and realising it cannot merge first.
That is when to speak. A sweep of the issue list looking for edges to add is
the manufacturing failure, not the skill working.


What is a blocker
=================

An edge means **another issue must close first**. It is not a place to record:

- A dependency on a person, a purchase, or a decision. There is no issue to
  point at, and inventing one makes the graph say something false about what
  unblocks the work.
- A pull request. The API refuses it at both ends of both graphs — *"Source
  issue may only be an issue"*, *"Target issue may only be an issue"*, *"Parent
  may only be an issue"*, *"Sub issue may only be an issue"*.

**A pull request that must wait on another pull request has nowhere structural
to record it.** That dependency belongs on the issues the two PRs implement,
where it is an ordinary edge and where it outlives both PRs being merged or
abandoned. In the PR itself it stays prose, and prose is all it can be.


Blocked-by and blocking: the script
===================================

`scripts/issue-deps.sh` is the whole of the MCP's gap here, and closes the
traps described below by construction — it takes issue references, never raw
ids, and verifies every write from the other end.

```sh
scripts/issue-deps.sh blocked-by 191            # what #191 waits on
scripts/issue-deps.sh blocking   188            # what waits on #188
scripts/issue-deps.sh summary    191            # open and total, both directions
scripts/issue-deps.sh add    191 199            # #191 is blocked by #199
scripts/issue-deps.sh remove 191 199
scripts/issue-deps.sh add 190 googleapis/release-please#2853
```

An issue is `123`, `#123`, `owner/repo#123`, or a github.com URL; a bare number
resolves against the origin remote, or against `--repo OWNER/REPO`. Auth is the
ambient `GITHUB_TOKEN` / `GH_TOKEN`, present on both the laptop and a web
worker.

State an edge **from the blocked side**. That is the only side it can be stated
from — `POST .../dependencies/blocking` does not exist — and it is also the
direction the need arrives in: you are writing the issue that has to wait.

Cross-repository blockers are ordinary. The blocker's repository only has to be
readable by the token; nothing needs write access there.


Sub-issues: the MCP
===================

Fully exposed, including across repositories, so there is no script and no
reason for one. Parent/child is *decomposition* — this issue is part of that
one — and is a different claim from *this must close first*. An epic's children
are not automatically its blockers, and saying so in edges would be inventing
relationships.


Which PR closes an issue
========================

`issue_read` returns `closed_by_pull_requests`. Nothing in REST answers this
question: the issue timeline renders *"this PR closed it"* and *"this PR
mentioned it"* identically, so a REST answer here is a wrong answer, not a
missing one.

This is the skill's verification step, and it is worth running whenever an
issue's body claims a relationship: **does the structured graph match what the
prose says?** The `Closes #123` convention writes into this graph as an
unvalidated string, with no way to notice when it is wrong.


The traps, all of them silent
=============================

Every failure mode here returns a success. That is what makes verification
mandatory rather than fastidious.

- **A read cannot see the restriction.** `GET .../issues/<pr>/dependencies/blocked_by`
  answers `200` with an empty array — indistinguishable from an issue with
  genuinely no edges. Only the write refuses, and only the write says so. The
  script therefore refuses a pull request rather than reporting emptiness; do
  not route around it by curling the endpoint directly.
- **`issue_id` is the database id, not the `#number`.** A `#number` in that
  field returns `200` and creates an edge pointing at a stranger's issue — low
  numbers are dense in the id space. The script never accepts a raw id.
- **The POST response is the issue you modified**, so it confirms nothing.
  Verify from the blocking side; a wrong edge shows up as *silence* on the
  blocker. The script does this on every write.
- **Print the repository on both ends when reporting an edge.** A bare `#2853`
  reads as local and need not be.

An edge to a closed issue stops blocking without anyone editing anything —
which is the argument for edges over a `⛔ BLOCKED ON #189` banner, and the
reason a banner should be deleted once the edge exists.


When prose stays
================

An edge is binary and carries no reason. Keep a note in the body when it says
something the edge cannot: that the block covers only part of the issue, or
which of a blocker's several defects actually bite. Delete the line whose whole
content is "blocked on #199" — that is duplicate state, and it will rot.


Expiry
======

The script exists because the MCP exposes no blocked-by / blocking tool. It
rests on four endpoints: one `POST`, one `DELETE`, two `GET`s. **Delete it the
day the MCP exposes them**, and keep this skill.

Background, endpoints and the probe tables:
[`jmcvetta/career`, `docs/issue-dependencies.md`](https://github.com/jmcvetta/career/blob/master/docs/issue-dependencies.md).
