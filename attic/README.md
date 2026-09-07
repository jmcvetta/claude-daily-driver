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

  **Half of it came back.** The thread protocol, the reply-content rules and
  the reply-versus-resolve identifier trap ship in `skills/review-cycle/`,
  which is the live owner of all three. Bringing this directory back whole
  would give the protocol two owners and one of them would rot, so a revival
  here is the minimisation half only — the scripts, the self-identification
  line the matcher keys on, and the surface limitation that confines them to a
  laptop.
- `skills/review/` — the reviewer panel, with depth inferred from the diff.
  Retired 2026-09 as possibly obsolete. The agents it dispatched are still
  live under `agents/`; they are dormant, not deleted, because whether the
  panel outlives the skill is a separate question.
