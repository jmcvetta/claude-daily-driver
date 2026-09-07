---
name: session-title
description: >-
  This skill should be used whenever the title of the current Claude session
  is being set or revised — including when the user says "/session-title",
  "set the session title", "rename this session", "name this session", or
  "that title is wrong", and on Claude's own initiative when work on a GitHub
  issue begins, when the session's subject changes materially, or on any call
  to `mcp__Claude_Code_Remote__set_session_title`. Supplies the character
  budget the Claude mobile UI needs and the two forms a title may take. Not
  the title of a pull request — that is `pr-title`.
---

# Session title

The name this session carries in the Claude session lists, web and mobile
alike. It is read in a column of a dozen siblings, on a phone, at a glance.
That is the whole design constraint.


Budget: 40 characters
=====================

`set_session_title` accepts 500. Forty is what the mobile list shows before it
clips, so the cap is this skill's rather than the API's.

- **Hard cap, 40 characters.** A longer title is not truncated by the UI in
  the place I would have chosen; it is truncated in the place the renderer
  reaches. Shortening it here keeps that choice.
- **No ellipsis.** A title trimmed to fit reads as a title. One ending in `…`
  reads as a title that failed.


Working on an issue
===================

    #{number} {shortened issue title}

The number leads because it is the identifier — the half that must survive any
clipping a narrower screen still applies, and the half that a human matches
against a browser tab.

Shorten the issue title in this order, stopping as soon as it fits:

1. Drop the Conventional Commits type prefix — `feat:`, `fix(api):`.
2. Drop the leading noise a title carries for the issue tracker's benefit and
   not the reader's — `New skill:`, `Bug:`, `RFC:`.
3. Drop trailing qualifiers: a parenthesis, a clause after a dash.
4. Cut whole words from the end, never part of one.

Issue #40, *"New skill: set the Claude session title"*, becomes
`#40 Session title skill`.


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

Both tools exist only on the Claude Code Remote surface. Where they are absent
— a laptop session — there is no title to set, and the skill says so and stops
rather than reaching for a substitute.


When to set it
==============

Once, as soon as the subject is known: the turn work actually starts, not the
turn the session opens. Again when the subject genuinely changes — issue #40
closed, issue #41 begun.

Not on every commit, and not to record progress. A title that keeps moving is
one nobody reads twice.
