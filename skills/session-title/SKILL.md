---
name: session-title
description: >-
  This skill should be used whenever the title of the current Claude session
  is being set or revised — including when the user says "/session-title",
  "set the session title", "rename this session", "name this session", or
  "that session name is wrong", and on Claude's own initiative when work on a
  GitHub issue begins, when the session's subject changes materially, or on
  any call to `mcp__Claude_Code_Remote__set_session_title`. Supplies the
  character budget the Claude mobile UI needs and the two forms a title may
  take. Not the title of a pull request — that is `pr-title`.
---

# Session title

The name this session carries in the Claude session lists, web and mobile
alike. It is read in a column of a dozen siblings, on a phone, at a glance.
That is the whole design constraint.


Budget: 40 characters
=====================

`set_session_title` accepts 500. Forty is this skill's own cap, chosen rather
than measured — short enough to survive the mobile list at the width it is
read on, long enough to say which session this is. A measurement, when someone
takes one, is what may move it.

- **Hard cap, 40 characters**, counting the whole string, `#123 ` prefix
  included. Past that the title is cut where the renderer reaches rather than
  where a writer would have chosen; shortening it here keeps the choice.
- **No ellipsis.** A title trimmed to fit reads as a title. One ending in `…`
  reads as a title that failed.


Working on an issue
===================

    #{number} {shortened issue title}

The number leads because it is the identifier — the half that must survive any
further clipping, and the half a reader matches against a branch name or a
browser tab.

Shortening is deletion, in this order, stopping as soon as the whole thing
fits, and capitalising whatever word ends up first:

1. Drop a leading prefix written for the tracker rather than the reader: a
   Conventional Commits type (`feat:`, `fix(api):`), or a label (`New skill:`,
   `Bug:`, `RFC:`).
2. Drop a trailing qualifier — a parenthesis, a clause after a dash.
3. Drop the words carrying no information, wherever they sit: articles,
   prepositions, an auxiliary verb, an adjective the title survives without.
4. Only then cut whole words from the end, never part of one, and never the
   noun naming the subject — which in an issue title is as often last as
   first.

Issue #40, *"New skill: set the Claude session title"*, needs step 1 alone:
`#40 Set the Claude session title`.

Issue #212, *"fix(storage): retry with exponential backoff for the S3 upload
client"*, loses its type prefix, then `with`, `exponential`, `the` and
`client`: `#212 Retry backoff for S3 upload`.


Not working on an issue
=======================

A short noun phrase naming what the session is actually doing.

- **Nouns, not narration.** `Flaky auth test triage`, not
  `Working on fixing the flaky auth test`.
- **Specific over generic.** `Postgres pool leak`, not `Debugging`.
- **No repository name.** The session records its own source; spending a
  quarter of the budget restating it buys nothing.


Setting it
==========

`mcp__Claude_Code_Remote__set_session_title` requires a `session_id`, and the
one that matters is this session's. Get it from
`mcp__Claude_Code_Remote__get_session` with `session_id` omitted, which
describes the caller.

Both tools exist only on the Claude Code Remote surface. Where they are
absent — a laptop session — there is no way to set the title from here, and
the skill says so and stops rather than reaching for a substitute.


When to set it
==============

Once, as soon as the subject is known: the turn work actually starts, not the
turn the session opens. Again when the subject genuinely changes — issue #40
closed, issue #41 begun.

Not on every commit, and not to record progress. A title that keeps moving is
one nobody reads twice.
