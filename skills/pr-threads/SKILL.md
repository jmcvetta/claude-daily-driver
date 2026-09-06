---
name: pr-threads
description: >-
  This skill should be used whenever pull request review threads are being
  read, answered, resolved, or tidied — including when the user says
  "/pr-threads", "reply to the review comments", "address the review
  feedback", "resolve those threads", or "minimise the old Claude comments",
  and including any use of `mcp__github__add_reply_to_pull_request_comment`,
  `mcp__github__resolve_review_thread`, or `pull_request_read` with the
  `get_review_comments` method on Claude's own initiative. Supplies the reply
  protocol, the resolve rule, the repeat-finding rule, the self-identification
  line, and the comment-minimisation path the GitHub MCP does not offer.
---

# PR Review Threads

The lifecycle of a review thread: read it, act on it, answer it, close it.
Applies to **every** reviewer — a human, Claude Approvals, a lint bot,
whatever comes next. None of what follows is reviewer-specific.

This fires on seeing open review threads, not on being asked about them. A
thread nobody answered is the failure this skill exists to prevent.


The Protocol
============

Four rules. They are the whole protocol.

1. **Implemented** — when the finding is fixed, reply on the thread saying it
   was implemented, and resolve the thread.
2. **Rejected** — when the suggestion is declined, reply on the thread saying
   why, and resolve the thread.
3. **Repeat finding** — when a reviewer opens a new thread for something
   already rejected in an earlier round, resolve it with the same message. The
   reviewer gets the same answer because the answer has not changed; writing a
   fresh variation invites a fresh argument.
4. **Nothing is left open silently.** A thread is answered or it is
   outstanding, and an outstanding thread gets said out loud — never dropped.

Rules 1 and 2 are one rule seen from two sides: **reply, then resolve.** A
resolution with no reply hides the reasoning; a reply with no resolution
leaves the reviewer to guess whether anything happened.


Reply Content
-------------

- **Concise.** Not chatty. No thanks, no apologies, no restating the finding
  back at the reviewer.
- **Technical and accurate.** Say what changed, or what was measured, and
  where.
- **Verdict-first.** The reply must state *implemented* or *rejected*
  unmistakably. A reader skimming twenty threads should never have to parse a
  paragraph to learn which.
- **No poems.** Poetry attaches to the posted review artifact, never to a
  finding someone has to act on. The review comment's opening and closing
  verse are specified elsewhere; a thread reply is prose.

A rejection carries its reason and stops. "Rejected — `n` is bounded by the
caller's `len(items)` check at `loader.go:88`" is a complete reply. Softening
it into a discussion reopens a thread the rule just closed.


Whose Thread Is It
------------------

Answering and resolving is for threads on **a pull request you opened, or one
you were asked to drive**. On a pull request you are merely watching, a reply
proposing what you would do is the whole action — the author resolves their
own threads.


Clients
=======

Two clients, for a reason that is not arbitrary. The MCP does what the MCP
exposes; a script exists only where it demonstrably does not.

| Task | Client |
| ---- | ------ |
| Read review threads and their IDs | `pull_request_read`, `get_review_comments` |
| Reply on a thread | `mcp__github__add_reply_to_pull_request_comment` |
| Resolve a thread | `mcp__github__resolve_review_thread` |
| Minimise a superseded comment | `scripts/pr-minimize-previous-claude-comments.sh` |

**Reply takes a numeric comment ID, resolve takes a GraphQL thread node ID.**
They are different identifiers for the same conversation and are not
interchangeable — `add_reply_to_pull_request_comment` wants the number from a
`#discussion_r…` anchor, `resolve_review_thread` wants `PRRT_…`. Both come out
of `get_review_comments`; take them from the same response rather than
reconstructing either.


Self-Identification
===================

A review comment Claude posts ends with a self-identification line:

```
*Claude {model version}*
```

**This is not decoration.** It is the only marker by which the minimise path
recognises Claude's own earlier comments, and the matcher in
`scripts/pr-find-claude-comments.sh` keys on exactly this shape. Drop the line
and superseded comments stop collapsing — silently, months later, with nothing
to point at.

Self-identification and minimisation move together or not at all. Changing the
line means changing that matcher in the same commit.


Minimisation
============

When a fresh review supersedes an earlier one, the earlier comment is
collapsed rather than left to pad the conversation. **The GitHub MCP has no
tool for this** — `minimizeComment` is a GraphQL mutation and nothing in the
MCP surface reaches it. Verified by absence, not assumed; see
`docs/planning/plugin-replaces-global-memory.md` (D3).

That gap is what the scripts in `scripts/` are for, and the only thing they
are for. Each one's header says why it exists and what deletes it.

```
skills/pr-threads/scripts/pr-minimize-previous-claude-comments.sh <pr-number>
```

The dependency chain behind that one line, which must not be cut in the
middle:

> minimisation is a real MCP gap → minimisation needs GraphQL node IDs
> (`IC_kwDO…`) → those come from a script, because no MCP tool returns them.

Retire any link only when its replacement has been demonstrated on a real pull
request. Retiring the supplier while keeping the consumers leaves a chain that
still reads correctly and no longer works.


Surface Limitation
------------------

**Minimisation does not work from a Claude Code web worker**, and the scripts
say so rather than failing obscurely. Measured on 2026-09-06: the session's
ambient `GITHUB_TOKEN` is brokered, and `POST api.github.com/graphql` answers
every operation with

> This GraphQL query is not enabled for this session — only the pinned set of
> PR-review operations is served.

REST is unaffected, so finding the comments works everywhere; only the
mutation is gated. `gh` is not an escape hatch — it is not installed on a web
worker at all, which is why these scripts use `curl`.

So minimisation is a laptop capability, on a personal token. Everything else
in this skill — read, reply, resolve — runs identically on both surfaces
through the MCP.
