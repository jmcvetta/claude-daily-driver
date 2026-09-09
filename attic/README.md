# attic

Components that are kept but not shipped.

The plugin loads skills from `skills/` and agents from `agents/`. Nothing
under `attic/` is loaded, validated, or advertised: `claude plugin validate`
is pointed at the two live directories, and `scripts/check-manifests.py`
globs `skills/*/SKILL.md`, so a component moved here stops being part of the
plugin the moment it lands.

`agents/` is currently empty, and the two checks that read it are written to
survive that. `make check-agents` validates the directory only when it holds
a component, because `claude plugin validate` handed an empty directory looks
for a manifest instead and fails; `check-manifests.py` treats zero agents as
a valid count, unlike zero skills. Both are what make the revival below a
`git mv` and nothing else.

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
  Retired 2026-09 as possibly obsolete. The agents it dispatched followed it
  here; see the entry below.
- `agents/` — `architecture-reviewer`, `logic-reviewer`, `security-reviewer`
  and `planning-fitness-reviewer`, the four roles `skills/review/` dispatched.
  Retired 2026-09.

  They outlived the skill by one release, on the open question of whether the
  panel outlives the skill. Nothing answered it in the affirmative: #35 closed,
  `review-cycle` shipped as the live review path and routes the analysis to
  the built-in `/code-review` under a heading that says *A reviewer, not a
  subagent*, and no shipped skill has dispatched any of the four since. Four
  definitions that load into every session and are never invoked are what the
  attic is for.

  Retiring them decides nothing about whether the panel was right. The
  measurement #35 designed was never run, so its question is still open — it
  is just no longer open at the cost of shipping the answer's subject.
