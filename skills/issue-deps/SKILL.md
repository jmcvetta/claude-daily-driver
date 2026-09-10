---
name: issue-deps
description: >-
  This skill should be used whenever a relationship between GitHub issues is
  being recorded, read, or relied upon — one issue blocking another, a
  sub-issue or parent, or which pull request closes an issue. It fires on the
  literal "/issue-deps", on natural phrasings ("this is blocked by #123",
  "what's blocking this", "make it a sub-issue of the epic", "what does this
  depend on"), on noticing while planning or while writing a PR body that some
  other work must land first, and on Claude's own use of `gh issue edit` with
  `--add-blocked-by`, `--add-blocking`, `--add-sub-issue` or `--parent`, of
  `mcp__github__sub_issue_write`, `mcp__github__issue_read` with
  `get_sub_issues` or `get_parent`, `mcp__github__issue_write` with
  `parent_issue_number`, or of a `Closes #123` line in a pull request body.
  Supplies the three clients these relationships need and the probe that picks
  one, the script for a token without `gh`, and the rule that a relationship
  is proposed from evidence and confirmed by the user, never asserted.
---

# Issue relationships

Three relationships, one graph, **three clients** — and which client is not a
preference. It is decided by what the environment has, and the wrong one does
not fail: it answers wrong-shaped, or answers with a count where the question
was *which*.

| Relationship | `gh` >= 2.94.0 | `scripts/issue-deps.sh` | The MCP |
| ------------ | -------------- | ----------------------- | ------- |
| **Blocked-by / blocking** — read | `--json blockedBy,blocking` | `blocked-by`, `blocking` | counts only |
| **Blocked-by / blocking** — write | `--add-blocked-by`, `--add-blocking`, and their `--remove-` pairs | `add`, `remove` | none |
| **Sub-issue / parent** — read | `--json subIssues,parent` | no | `issue_read` with `get_sub_issues` / `get_parent`; counts only on the older server |
| **Sub-issue / parent** — write | `--add-sub-issue` / `--remove-sub-issue`, `--parent`, `--remove-parent` | no | `sub_issue_write`, `issue_write` with `parent_issue_number`; none on the older server |
| **Which PR closes an issue** | `--json closedByPullRequestsReferences` | no | `issue_read` returns `closed_by_pull_requests`; nothing on the older server |

The one thing that is *written* as prose is the `Closes #123` line in a pull
request body. Treat the graph as the artifact and that line as one unvalidated
writer into it.


Which client
============

Probe, do not assume. Three branches, in this order, and the first that holds
is the client:

1. **`gh` at 2.94.0 or later, and authenticated.** The whole graph, both
   directions, one client.
   The floor is real and recent: the flags and the `--json` fields above
   arrived together in 2.94.0 (cli/cli#13057), and an older `gh` does not say
   so. It says `unknown flag: --add-blocked-by`, or `Unknown JSON field:
   "issueType"`, neither of which hints at the version. So read the version
   first — `gh --version` — rather than the error.

   **Installed is not authenticated, and this branch needs both.** An image
   that ships `gh` and injects no credential passes a version check and fails
   every call with *"To use GitHub CLI in a GitHub Actions workflow, set the
   GH_TOKEN environment variable"*. Committing to this branch on the version
   alone strands the session there, with branch 2 — which that same token
   would have served — never reached. So probe `gh auth status` too, and fall
   through where it fails.
2. **`gh` older, or absent, and `GITHUB_TOKEN` / `GH_TOKEN` present.** The
   script. This is the branch a Claude Code web worker lands on — `gh` is not
   installed there at all (measured 2026-09-06, and again 2026-09-09) while the
   token is — and it is the branch the script was written for. Load-bearing,
   not legacy.
3. **The MCP only.** Say plainly what it cannot do, before something fails
   trying. There are two generations of the GitHub MCP server, and the tool
   list says which one is present. The newer server has `issue_read`,
   `issue_write` and `sub_issue_write`, and reaches sub-issues and
   `closed_by_pull_requests` (measured 2026-09-09, from a web worker). The
   older server has `get_issue`, `create_issue` and `update_issue`, and reaches
   none of that. **Neither generation lists a blocked-by or blocking edge, and
   neither writes one.** What both return is a summary — counts with no
   members:

   ```json
   "sub_issues_summary": {"total": 0, "completed": 0, "percent_completed": 0},
   "issue_dependencies_summary": {"blocked_by": 0, "total_blocked_by": 0,
                                  "blocking": 0, "total_blocking": 0}
   ```

   So the MCP can say an issue has two blockers and cannot say which two. On
   the older server that is all a read gets for any of the three
   relationships, and the graph is **not writable** from there at all. Report
   that, rather than a session discovering it by failing.


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

None of this moved when the transport did. In the session that found the `gh`
path, this rule is what stopped an edge being written between two issues that
merely shared a subject.


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


The whole graph: `gh`
=====================

```sh
gh issue view 191 --json blockedBy,blocking,subIssues,parent,closedByPullRequestsReferences
gh issue edit 191 --add-blocked-by 199        # #191 waits on #199
gh issue edit 199 --add-blocking 191          # the same edge, stated from the other end
gh issue edit 191 --remove-blocked-by 199
gh issue edit 191 --parent 150                # #191 is part of #150
gh issue edit 150 --add-sub-issue 191         # the same edge, stated from the parent
gh issue edit 190 --add-blocked-by https://github.com/googleapis/release-please/issues/2853
```

Every flag that names an issue takes a number or a URL, never a database id,
so the id trap under `The traps` is closed by the client. **`--remove-parent`
is not one of them**: it is a boolean and takes no argument, unlike the
`--remove-` pairs of `--add-sub-issue`, `--add-blocked-by` and
`--add-blocking`, which all take the issue they remove. `gh issue edit 191
--remove-parent 150` reads `150` as a second positional argument and aborts on
argument count, having removed nothing. Both directions are offered: REST still
has no `POST .../dependencies/blocking`, and `gh` inverts a `--add-blocking`
client-side into the write REST does accept. State the edge from whichever end
the need arrives at.

**Refusals are honest and exit non-zero**, and none of them mutate the graph.
Measured, on 2.100.0:

- A self-edge: *"Target issue cannot be the same as the source issue
  (addBlockedBy)"*.
- A missing issue: *"Could not resolve to an Issue with the number of 9999"*.
- A duplicate: *"Target issue has already been taken"*.

**Read `$?` before anything is piped.** `gh issue edit … | tail` reports
`tail`'s status, not `gh`'s, and a failed write then reads as a success. That
is the trap that briefly made it look as if `gh` exited 0 on failure. It does
not; the pipe did.

**A read against a pull request still answers empty rather than refusing.**
`gh issue view <pr> --json blockedBy` returns
`{"blockedBy":{"nodes":[],"totalCount":0}}`, which is what an issue with no
edges returns too. The requested field is a key in that object, not the object
itself — `jq '.totalCount'` against it is `null`, and a `null` read as zero is
this same empty answer arriving by a second route. `gh` does not close this
trap. Check the kind of object before believing an empty answer, the way the
script does.


Blocked-by and blocking: the script
===================================

`scripts/issue-deps.sh` is the second branch of `Which client`: four REST
endpoints behind `curl` and the ambient token, and nothing else, because that
is all a web worker has. It closes the traps described below by construction —
it takes issue references, never raw ids, refuses a pull request at either
end, and verifies every write from the other end.

Always invoke it through the harness's own skill-directory path. A skill's
Bash runs in the user's project, not in the plugin, so a relative
`scripts/issue-deps.sh` is "No such file or directory" — or worse, silently
runs an unrelated file in a project that has its own `scripts/`. Each
harness injects the path differently:

- **Claude** — through `${CLAUDE_PLUGIN_ROOT}`, the plugin root the harness
  injects into a skill's Bash.
- **Omp** — through the injected skill-directory path, resolved as
  `skill://issue-deps/scripts/issue-deps.sh`; Omp's Bash resolves the
  `skill://` URL to the plugin's skill directory, which is where this script
  lives.

```sh
deps="${CLAUDE_PLUGIN_ROOT}/skills/issue-deps/scripts/issue-deps.sh"   # Claude
deps="skill://issue-deps/scripts/issue-deps.sh"                        # Omp

"$deps" blocked-by 191            # what #191 waits on
"$deps" blocking   188            # what waits on #188
"$deps" summary    191            # open and total, both directions
"$deps" add    191 199            # #191 is blocked by #199
"$deps" remove 191 199
"$deps" add 190 googleapis/release-please#2853
```

An issue is `123`, `#123`, `owner/repo#123`, or a github.com URL; a bare number
resolves against the origin remote, or against `--repo OWNER/REPO`. Auth is the
ambient `GITHUB_TOKEN` / `GH_TOKEN`, present on both the laptop and a web
worker.

The script states an edge **from the blocked side** only, because that is the
only side REST accepts it from — `POST .../dependencies/blocking` does not
exist. It is also the direction the need arrives in: you are writing the issue
that has to wait. `gh` offers the other direction as well, and inverts it
before REST sees it; the script does not, and does not need to.

Cross-repository blockers are ordinary. The blocker's repository only has to be
readable by the token; nothing needs write access there.

The script reaches blocked-by and blocking and nothing else. On a web worker
with the older MCP server, sub-issues and `closed_by_pull_requests` are out of
reach — say so, rather than reading the summary counts as an answer.


Sub-issues
==========

`gh` at the floor above, or the newer MCP server: `sub_issue_write`,
`issue_read` with `get_sub_issues` / `get_parent`, `issue_write` with
`parent_issue_number`, cross-repo included. There is no script and no reason
for one — the environment with neither client has no write path here, and the
answer to it is the third branch of `Which client`, not a fourth tool.

Parent/child is *decomposition* — this issue is part of that one — and is a
different claim from *this must close first*. An epic's children are not
automatically its blockers, and saying so in edges would be inventing
relationships.


Which PR closes an issue
========================

`gh issue view --json closedByPullRequestsReferences`, or the newer MCP
server's `issue_read`, which returns `closed_by_pull_requests`. Nothing in REST
answers this question: the issue timeline renders *"this PR closed it"* and
*"this PR mentioned it"* identically, so a REST answer here is a wrong answer,
not a missing one — and the script therefore does not offer one.

This is the skill's verification step, and it is worth running whenever an
issue's body claims a relationship: **does the structured graph match what the
prose says?** The `Closes #123` convention writes into this graph as an
unvalidated string, with no way to notice when it is wrong.


The traps, all of them silent
=============================

Every failure mode here returns a success. That is what makes verification
mandatory rather than fastidious.

- **A read cannot see the restriction.** `GET .../issues/<pr>/dependencies/blocked_by`
  answers `200` with an empty array, and `gh issue view <pr> --json blockedBy`
  answers `{"blockedBy":{"nodes":[],"totalCount":0}}` — either one
  indistinguishable from an issue with genuinely no edges. Only the write refuses, and only the write
  says so. The script therefore refuses a pull request rather than reporting
  emptiness; do not route around it by curling the endpoint directly, and do
  not read `gh`'s empty answer as evidence either.
- **`issue_id` is the database id, not the `#number`.** A `#number` in that
  field returns `200` and creates an edge pointing at a stranger's issue —
  low numbers are dense in the id space. The script never accepts a raw id,
  and `gh` never asks for one. The trap is REST's, and it is live for anyone
  who curls the endpoint by hand.
- **The POST response is the issue you modified**, so it confirms nothing.
  Verify from the blocking side; a wrong edge shows up as *silence* on the
  blocker. The script does this on every write. After a `gh` write, read the
  other end with `--json blocking` or `--json subIssues` — cheap, and the only
  confirmation there is.
- **A pipe eats the exit status.** `$?` after `gh … | tail` is `tail`'s.
  Check the write before anything is piped, or not at all.
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

The script exists for one environment: a token and no `gh` at 2.94.0 or
later. Today that is every Claude Code web worker. It rests on four endpoints:
one `POST`, one `DELETE`, two `GET`s. **Delete it the day that environment
stops existing** — the day the web worker ships a current `gh`, or the day the
MCP exposes those four endpoints — and keep this skill. The capability was
first expected to arrive through the MCP; it arrived through `gh` instead, and
the MCP still has not caught up. The expiry is the environment, not the
transport.

Background, endpoints and the probe tables:
[`jmcvetta/career`, `docs/issue-dependencies.md`](https://github.com/jmcvetta/career/blob/master/docs/issue-dependencies.md).
