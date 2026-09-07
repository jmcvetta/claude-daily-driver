# attic

Components that are kept but not shipped.

The plugin loads skills from `skills/` and agents from `agents/`. Nothing
under `attic/` is loaded, validated, or advertised: `claude plugin validate`
is pointed at the two live directories, and `scripts/check-manifests.py`
globs `skills/*/SKILL.md`, so a component moved here stops being part of the
plugin the moment it lands.

The point of the attic is that the move is cheap in both directions. A skill
whose usefulness has run out does not have to be deleted to stop shipping,
and one that turns out to have been retired early comes back with a `git mv`
rather than an archaeology session.

## What is here

- `skills/pr-threads/` — the review-thread lifecycle: reply with a verdict,
  resolve, re-resolve a repeat finding, plus the comment minimisation the
  GitHub MCP does not expose. Retired 2026-09 as possibly obsolete.

`skills/review/` was here too, and came back — reshaped rather than restored.
What returned is the half that never depended on the panel measurement:
routing, the walkthrough, and the planning route — whose contract now lives in
`planning-fitness-reviewer` itself, which ships and can be invoked without the
skill. The built-in `/code-review` is the analysis. Three of the four reviewer agents stay dormant
under `agents/` until that measurement is taken. This is the round trip the
attic was built for: a `git mv` out, and a rewrite back.
