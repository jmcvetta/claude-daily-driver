# Claude Code routes — epic

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md).


The issues
==========

| Step | Operation | Call |
| ---- | --------- | ---- |
| `Size the work` | Read an issue already in hand | `mcp__github__issue_read` |
| `Open the issues` | Search the open issues | `mcp__github__search_issues` |
| `Open the issues` | Open the epic, and each task | `mcp__github__issue_write`, `method: create`, with `labels` |
| `Open the issues` | Turn an existing issue into the epic | read `labels` with `mcp__github__issue_read`, then `mcp__github__issue_write`, `method: update`, sending that set with the old standard label swapped for `epic` |
| `Fill in the epic` | Replace the epic's body | `mcp__github__issue_write`, `method: update` |

`method: update` replaces `body` outright rather than appending to it, so
`Fill in the epic` sends the whole of `The epic body` and not the part that is
new.


The parent, at creation
=======================

**The read in that row is not optional.** `labels` replaces the whole set, so
an update sending `["epic"]` deletes every other label the issue had — the
stock and bot-owned ones `issue-labels` says to leave alone included. A new
issue has nothing to lose and needs no read; a converted one does.

`mcp__github__issue_write` with `method: create` takes `parent_issue_number`,
and attaches the new issue to that parent in the same operation. Where that
field is available, a task opened at `Open the issues` arrives parented and
`Write the graph` has only the edge to verify — it still verifies, because the
write response is the issue you modified and `issue-deps` requires the read
from the other end regardless of which call made the edge.

**It is not available everywhere.** `issue-deps` records two generations of
the GitHub MCP server, and the older one has no sub-issue write at all: there,
`Write the graph` has no parent route and says so rather than reporting a
parent it did not set. Read that skill's routes before believing this one.

The field cannot be combined with `issue_fields`, and it is read on `create`
only. An issue that already exists is re-parented through `issue-deps`' own
routes, not here.


The graph
=========

`issue-deps` owns both relationships and picks its own client — which for
blocked-by on a Claude Code web worker is its script rather than the MCP,
because neither generation of the GitHub MCP server writes that edge at all.
Read that skill's routes before `Write the graph`.


The model a task records
========================

`Draft the plan` writes a `Model:` line into each task issue, and `embark`
passes that identifier to `mcp__Claude_Code_Remote__create_session`. So the
identifier has to be one that call accepts — a marketing name recalled from
training is not one, and the session it opens fails rather than falling back.

**Read one rather than recall one.** `mcp__Claude_Code_Remote__get_session`,
with `session_id` omitted, reports this session's own identifier at
`session_context.model` — the model the session is currently set to run, and
the right answer for a task no lighter than the planning session.

**`configured_model` is not that field and is not safe to copy.** The call's
own contract says it is echoed as stored, so it may be an alias or carry a
context-window suffix — which is exactly the identifier `create_session`
rejects, written into a `Model:` line that reads as correct. Take
`session_context.model`, and where only `configured_model` is available,
write no line.

The family, as the harness named it on 2026-09-11:

| Weight | Identifier |
| ------ | ---------- |
| Heaviest | `claude-opus-5` |
| Middle | `claude-sonnet-5` |
| Lightest | `claude-haiku-4-5-20251001` |

`claude-fable-5-1` exists beside these and is not a weight on that scale.
Model identifiers move; this table is a measurement with a date on it, not a
contract. Where it disagrees with what the harness reports, the harness is
right and this table is stale.

**`create_session` takes `model` and has no effort parameter.** Effort is
session configuration — `session_context.effort_level` — rather than a
dispatch argument, so it cannot be carried on a task issue. `SKILL.md` says
not to write an `Effort:` line, and this is why.
