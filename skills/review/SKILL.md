---
name: review
description: >-
  This skill should be used whenever changes are about to be judged ready —
  including when the user says "/review", "review this branch", "is this
  ready", "what do you think of these changes", "give me your opinion on this
  diff", or asks for a second opinion before merging; and on Claude's own
  initiative before marking a draft pull request ready for review
  (`mcp__github__update_pull_request` with `draft: false`), before requesting a
  reviewer (`mcp__github__request_copilot_review`), before declaring a branch
  finished, and before invoking the built-in `/code-review` or
  `/security-review` on a branch. Routes the diff — planning documents to the
  planning contract, everything else to `/code-review` at an effort level read
  off the diff — then walks the findings, applying the obvious ones and
  discussing the rest. Do NOT use this skill merely because a pull request is
  being opened — that is the `pr` skill's moment, and a draft opens the
  conversation rather than ending the work.
---

# Review

The built-in `/code-review` is the analysis. This skill is the three things it
does not do: **route** the diff to the right kind of review, apply the
**planning contract** to a diff made of plans rather than code, and **walk the
findings** with the obvious fixes separated from the judgement calls.

Two boundaries define it:

- **Expensive skills are pulled, never pushed.** This never fires on pull
  request *open*. Taxing every trivial branch to catch the occasional serious
  one trains the reflex that makes review worthless — skimming output that
  always appears. It fires on the *asking* moments enumerated in the
  description.
- **Findings are prose, not verse.** A finding someone has to act on is
  written to be acted on.


Pre-flight
==========

Mode and base branch
--------------------

1. **Base branch**: run `git symbolic-ref refs/remotes/origin/HEAD` and take
   the branch name. If that fails, use `master` when
   `git rev-parse --verify origin/master` succeeds, otherwise `main`. Call it
   `$BASE_BRANCH`.
2. **PR mode or Local mode**: find the pull request for the current branch with
   `mcp__github__list_pull_requests` (`head: <owner>:<branch>`, `state: open`).
   One result means **PR mode**; none means **Local mode**. A pull request
   number given explicitly by the user overrides the lookup. The difference is
   what can be *read* — CI status and what other reviewers already said — not
   where anything is written; nothing here posts to GitHub.
3. State the route and the effort level on one line before running anything, so
   it is visible which path was taken and why — e.g.
   `Verified review, PR mode #123 — 640 changed lines, touches .github/workflows/`.

Never shell out to `gh`. It is a laptop-only convenience, absent from web
workers entirely, so a `gh` call passes every test on the machine it was
written on and fails invisibly on the other surface. The GitHub MCP is the
client; `curl` against `api.github.com` with the ambient `GITHUB_TOKEN` is the
only fallback, for the endpoints the MCP does not reach.

Gathering the diff
------------------

**PR mode.** Run `git fetch`, then refuse to review a stale tree: if the local
branch is ahead of its remote, stop with "Local changes not pushed. Push
first."; if the remote is ahead, stop with "Remote has new commits. Pull
first." Then read the pull request through `mcp__github__pull_request_read`:

| Method | For |
| ------ | --- |
| `get` | title, body, draft state |
| `get_diff` | the diff under review |
| `get_files` | changed paths, for the routing signals below |
| `get_commits` | commit subjects |
| `get_status`, `get_check_runs` | CI, which the findings are read against |
| `get_comments`, `get_reviews`, `get_review_comments` | what other reviewers already said |

Read those last three rather than merely fetching them: do not re-report a
finding a human, a bot or Claude Approvals has already raised, and where you
disagree with one, say so rather than staying silent.

**Local mode.** Run `git fetch`, then verify there is something to review:
`git log origin/$BASE_BRANCH..HEAD --oneline`, and stop with "No commits ahead
of origin/$BASE_BRANCH. Nothing to review." if it is empty. Assemble the same
data from git — `--name-status` for changed paths, `git diff
origin/$BASE_BRANCH...HEAD` for the diff, `git log --format=%s` for subjects —
and say explicitly that CI status, pull request conversation and review threads
are unavailable, rather than treating an unread check as a passing one.

**Either mode**: if the diff changes no files, stop with "No changed files.
Nothing to review." A mode-only or empty commit is ahead of the base branch and
still has nothing in it, and every classification below is vacuously true on an
empty set of paths.


Routing
=======

Read off the diff. Kind decides *which* review runs; size and the sensitive
touch decide *how hard* it looks.

**Kind.** Classify the changed paths. The buckets overlap — a `README.md` is
both planning-class and docs-only — so test them **in this order** and take the
first that matches:

1. **Planning-class** — every path is planning-class; a path is planning-class
   if it lives under `docs/planning/` or `docs/proposals/`, or its basename is
   `README.md` or `CLAUDE.md` anywhere.
2. **Docs-only** — every path ends in `.md`, `.txt` or `.rst`, or is `LICENSE`.
3. **Code** — anything else.

Tests sit with code rather than with docs, and get no bucket of their own
because they fall through to Code already: a test that asserts the bug passes,
and nothing about it being a test file makes that cheaper to miss.

**Size.** Changed lines across non-generated files, ignoring lockfiles and
vendored trees. The thresholds below are a prior, not a rule: a thirty-line
change to a lock ordering earns the verified level, and an eight-hundred-line
rename does not.

**The sensitive touch.** If any changed path or hunk touches the list below,
the diff takes the Verified route whatever its size. This is the judgement a
human forgets to make, made from the diff instead. The five marked **§** are
the security-shaped half, which the analysis treats differently.

- **§** authentication, authorization, sessions, tokens, passwords, OAuth,
  SAML, JWT
- **§** cryptography — ciphers, hashing, TLS, certificates, key material,
  randomness
- **§** IAM and access policy, in any form: `*.tf` policy or role documents,
  security groups, Kubernetes RBAC, bucket policies
- **§** CI and release configuration under `.github/workflows/` — those files
  hold tokens and permissions
- **§** request boundaries: handlers, routes, controllers, deserialization,
  file-path and URL handling
- database migrations and schema changes
- dependency manifests, and any lockfile change that moves a dependency's
  version — a `--upgrade-package` bump with no manifest movement is a
  supply-chain decision wearing a lockfile. A lockfile regenerated without
  moving a version carries no decision at all, and Size ignores lockfiles, so
  it is a Skim.

**Take the first row that matches**, the way the kind buckets are read.

| Route | When | The analysis |
| ----- | ---- | ------------ |
| **Planning** | planning-class | `planning-fitness-reviewer`, under `references/planning-review.md`. No `/code-review`. |
| **Verified** | a sensitive touch | `/code-review max`, plus `/security-review` on the **§** half |
| **Skim** | docs-only, or under ~50 changed lines | `/code-review low` |
| **Standard** | code, under ~800 changed lines | `/code-review medium` |
| **Full** | over ~800 changed lines, or the user asked for depth | `/code-review xhigh` |

Skim is `low` deliberately: `low` caps findings hard — around four on most
families — which is proportionate to fifty lines, or to prose. Where the row
the table picks is wrong for the diff in front of you, **raise the level
yourself and say so on the pre-flight line, with the reason.** The case that
needs it most is nine hundred lines of `.rst`, which Skim catches before Full
ever sees it. That judgement is the *prior, not a rule* clause being used, not
overridden.

Planning-class is decided first and is never raised. A rollout plan that
discusses IAM is still prose, and `max` over nine hundred lines of it buys
findings about a document with no code in it.

A depth the user names wins over the size rows, and cannot go under the
Verified route. "Just skim it" on a diff that widens a workflow token is
precisely the judgement this skill is here to make on their behalf; say that
the sensitive touch is holding the level, and review it at `max`.


The analysis
============

Non-planning routes
-------------------

Run the session's built-in **`/code-review`**, naming both the level and the
target:

- **PR mode** — `/code-review <level> <PR number>`
- **Local mode** — `/code-review <level> <$BASE_BRANCH>`

Name the level, because `/code-review` reuses the last one typed in the session
by its own description. Name the target, because unnamed it reviews the
*working* diff — empty on a branch whose work is committed, and an empty diff
comes back clean.

Inside this skill `/code-review` is the analysis, not a trigger. The
description fires this skill when someone reaches for the built-in *instead of*
reviewing properly; it does not fire on this line.

**What a level buys depends on the session's model family**, because
`/code-review` resolves a model-family × effort cell: on Sonnet 5 `medium` is
eight angles with an adversarial verification vote, on Opus 5 a single careful
diff pass with neither. `high` is absent from the table above because on
`claude-opus-5` it resolves to the same cell as `medium`. `low`, `medium`,
`xhigh` and `max` are distinct on every family, and `max` is the only one that
verifies on all of them — which is why the sensitive touch selects it.

One known gap at Standard, worth carrying while #35 is open: per `0001` the
built-in's language-pitfall angle — the nearest thing it has to a
swallowed-error hunt — does not run at `medium` on any family. Read the diff
yourself for discarded returns, bare `except: pass` and errors logged in place
of being handled. Whether that deserves an agent is #35's question, not this
skill's.

On the **§** half of the sensitive list, also run the built-in
**`/security-review`**. The two do not overlap: per `0001` the angle bundles
`/code-review` runs are correctness, cleanup, altitude and conventions, with no
security angle at any level, while `/security-review` hunts injection, authz
bypass, crypto, deserialization and data exposure. `max` buys verification, not
a threat model. Migrations and dependency manifests get `max` alone — data loss
and supply chain are outside every category it hunts.

Two constraints, because it is not parameterised the way `/code-review` is.
**It takes no target**: it diffs the checked-out branch against `origin/HEAD`
and nothing else. So run it only where the diff under review *is* the checked-
out branch — not when a pull request number was supplied for some other branch,
and not where `origin/HEAD` was unresolvable in Pre-flight, since there it
reads an empty diff and reports clean. Skip it in a stated line rather than
silently.

**Merge its findings into the one list.** It returns its own report, graded
HIGH / MEDIUM / LOW: map those onto 🔴 / 🟡 / 🟢, de-duplicate against
`/code-review`'s findings rather than appending, and tag the survivors
`[obvious]` / `[judgment]` like any other. Two reports handed over whole is a
longer list that dilutes the real finding.

See [`docs/decisions/0001-built-in-review-surface.md`](../../docs/decisions/0001-built-in-review-surface.md)
for the full matrix and the CLI version it was read from. Re-confirm it when
that version moves; the table above is downstream of it.

If `/code-review` is not available in this session, say so in one line, then
read the diff yourself: grade against the **Severity** rubric below, and use
the sensitive-touch list above as the checklist for what to look hardest at.
An absent reviewer must never be mistaken for a clean one.

The planning route
------------------

Dispatch **`planning-fitness-reviewer`** through the Agent tool, passing the
diff, the changed paths, and
[`references/planning-review.md`](references/planning-review.md) — which holds
the contract and the severity rubric that replaces the four tiers below. Do not
pass a `model` parameter: the agent inherits the session's. A pin ages into a
cost decision nobody revisits.

`/code-review` does not run on this route. The question a planning document
faces is *"is this the right plan?"*, not *"is this ready to build?"*, and a
correctness reviewer reading prose has nothing to say about the first.


Severity
========

Classify every finding. `/code-review` ranks rather than grades, and
`/security-review` grades on a scale of its own; both land here.
Calibrate to the file type: an unhandled error in runtime code is more severe
than an imprecise instruction in a prompt, because the agent executing the
prompt has judgement.

- **🔴 Critical** — crashes, security vulnerabilities, data loss, broken
  builds, broken existing behaviour, wrong algorithms.
- **🟡 Important** — missing error handling for a recoverable case, missing
  tests for core functionality, significant technical debt, a configuration
  inconsistency, a poor performance pattern that still works.
- **🟢 Minor** — style inconsistencies, a misleading but functional name, a
  non-critical documentation gap.
- **🔵 Nitpick** — formatting, cosmetics, style-guide deviations.

When in doubt about runtime code, escalate. For prompts and configuration,
apply judgement about real-world impact.

Every finding carries `file:line` and the evidence for it. A claim without a
line number is a claim about code nobody has read.

**Do not manufacture a finding.** A diff that is genuinely clean is reported as
clean. A reviewer required to return something returns noise, and noise is what
teaches people to skim reviews.

Do not nitpick commit messages on the branch; they are squashed at merge.


The obvious / judgment split
============================

Tag every 🔴 and 🟡 `[obvious]` or `[judgment]`. 🟢 and 🔵 are not tagged; they
do not drive the walkthrough.

This is the discrimination `/code-review --fix` lacks — it applies every
finding or none, and the two kinds want different handling.

**Obvious-fix** requires all three: one sensible action with no competing
approach worth weighing; a local fix confined to the flagged files, with no API
or contract change and no cross-cutting refactor; and no design trade-off — no
performance-versus-clarity, no security-versus-UX, no scope question.

Qualifying: a missing test whose shape is clear from the code under test; a
swallowed error that should re-raise; mechanical correctness (wrong operator,
off-by-one with a known bound, a missing nil guard where the surrounding code
already treats the value as nullable); dead or duplicated code; a 🟢/🔵 nit
that got flagged 🟡.

Disqualifying: multiple plausible fixes; an architectural, layering or
pattern-fit concern; anything touching a public API, schema or migration; a
performance fix where the approach matters; a security fix where the threat
model decides the choice.

**When uncertain, `[judgment]`.** Unnecessary discussion costs one exchange;
auto-applying a fix the user would have shaped differently costs real work to
undo.


Display
=======

The audience is a developer at a terminal deciding what to fix.

1. **Overview** — one or two sentences on what the change does.
2. **Concerns & Risks** — every finding, grouped by severity, with `file:line`
   and evidence. Mark each 🔴/🟡 `[obvious]` or `[judgment]`.
3. **Obvious fixes preview** — if any `[obvious]` items exist, a compact
   `Obvious fixes (N):` list, one line each:
   `<severity> path/file.ext:LINE — <the single-sentence fix>`. Omit the
   section entirely when there are none.
4. **Bottom line** — one sentence naming the highest severity present and what
   it blocks, plus CI in PR mode. In Local mode say CI was unreadable rather
   than assuming it green. Nothing more: this skill reports what it found, it
   does not hold a merge gate, and a 🟡 is a thing to weigh rather than an
   automatic refusal.
5. **Next step** — with `O` = obvious count and `J` = judgment count, emit
   exactly one line:
   - `O > 0, J > 0` — "Apply the [O] obvious fix(es) and discuss the [J]
     judgment call(s) one at a time? (yes/no)"
   - `O > 0, J == 0` — "Apply the [O] obvious fix(es)? (yes/no)"
   - `O == 0, J > 0` — "Discuss the [J] judgment call(s) one at a time, then
     fix in batch? (yes/no)"
   - `O == 0, J == 0` — nothing to offer. Say so and stop.

No accolades, and no poems. This is the analysis, and it is read by someone
about to do work.


Walkthrough
===========

Runs only if step 5 emitted an offer line. Emit it, then **stop and wait**. An
affirmative reply starts the walkthrough; anything else does not, and the
conversation simply continues.

Routing: `[obvious]` items skip Phase 1 entirely and enter the Phase 2 plan as
`Fix` rows. Phase 1 runs over the `[judgment]` items only, and is skipped when
there are none.

Phase 1 — Discuss
-----------------

🔴 first, then 🟡, in the order they appeared. Per issue:

1. **Restate tersely**, at most ten lines:

   ```
   🟡 path/file.ext:LINE — <one-line summary>
   <1–3 short lines of evidence, or why it matters>
   Proposal: <one sentence>
   ```

   No restating the whole function, no long diff blocks, no re-explaining the
   codebase. Past ~5 lines of evidence, link by `file:line` instead. The user
   has already read the review; this is a reminder, not a re-presentation.
2. **Propose, don't lecture.** The `Proposal:` line *is* the discussion. Expand
   into trade-offs only if asked, or where approaches genuinely compete — then
   two or three one-line bullets. **Do not edit code yet.**
3. **Wait** for direction — fix as proposed, fix differently, defer, or skip —
   then record the decision as a todo. Do not start the work.
4. **Move to the next issue without asking permission.** The user opted into
   the whole walkthrough by saying yes. Announce the transition in one line and
   continue. Never ask "shall I continue?"

The only pause is step 3. The user can interrupt at any time.

Phase 2 — Execute
-----------------

1. **Print the plan** as a compact table: action (Fix / Defer / Skip),
   `file:line`, one-line summary — obvious items auto-routed as `Fix`, judgment
   items as decided. Do not ask for confirmation; those decisions were just
   made. State that execution is starting.
2. **Work the todos in order.** For each `Fix`: make the change, run the
   relevant validators, linters and tests for the touched files, and commit it
   as its own focused commit — one logical change per commit, never bundled.
   Defer and Skip produce no commit, just a one-line note.
3. **Stop and ask on conflict.** If the agreed approach turns out not to work —
   it collides with another agreed fix, breaks tests in a way that suggests the
   proposal was wrong, or rests on a wrong assumption — stop, explain, and wait.
   Do not push through.


Boundaries
==========

- Read-only until the walkthrough. The analysis edits nothing; the walkthrough
  edits only what the user accepted.
- **Nothing is posted to GitHub.** This skill reads a pull request and writes
  to the terminal. Posting a review comment is `/code-review --comment` or
  `/code-review ultra --post`, and both are the user's to reach for.
- Reading project files, and read-only commands over them, need no permission.
