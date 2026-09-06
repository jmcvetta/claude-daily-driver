# Daily Driver: Replacing the Global CLAUDE.md

**Status**: draft — under active discussion
**Branch**: `claude/daily-driver-plugin-brainstorm-x8azls`

## Goal

Make `claude-daily-driver` the *entire* Claude environment, so that a session
behaves identically whether it runs on the laptop CLI or on a Claude Code web
worker.

Today the environment is split. `dot-claude` *is* `~/.claude` — versioned, but
deployed only to the laptop. It holds the 17KB engineering philosophy plus
commands, agents, hooks and shell tooling. The plugin holds one skill. Web
workers get none of it.

The problem is therefore not that the global rules are unversioned. They are
versioned. The problem is **reach**: a repo of dotfiles is deployed by being
checked out onto a machine, and a web worker is not that machine. A plugin is
deployed by being installed, which both surfaces can do.

After this work, the plugin holds everything portable. `dot-claude` survives as
a laptop-settings repo and nothing more.

## Platform constraints

Established by reading the plugin and hooks references, not by assumption.

1. **A plugin cannot ship a `CLAUDE.md`.** Per the plugins reference: *"A
   `CLAUDE.md` file at the plugin root is not loaded as project context.
   Plugins contribute context through skills, agents, and hooks rather than
   CLAUDE.md."*

2. **Plugin `settings.json` supports only `agent` and `subagentStatusLine`.**
   So `permissions`, `model`, `effortLevel`, `editorMode` and `autoMode` cannot
   travel in the plugin. They stay in `~/.claude/settings.json`. This is fine —
   they are harness configuration, not memory, and a web worker neither needs
   nor wants the laptop's allowlist.

3. **The one mechanism for always-on context is a `SessionStart` hook** emitting
   `hookSpecificOutput.additionalContext`. The plugin ships `hooks/hooks.json`
   plus a script that reads `${CLAUDE_PLUGIN_ROOT}/context/*.md`. Being
   harness-executed, it behaves the same on CLI and web.

4. **`InstructionsLoaded` and `SubagentStart` are observation-only.** Neither
   supports decision control, so neither can inject or amend instructions.

5. **Subagent inheritance is undocumented and load-bearing.** The hooks
   reference states that plugin hooks run inside subagents and names *tool*
   events specifically — `SessionStart` is conspicuously absent, and whether
   `additionalContext` propagates to subagents is not documented either way.
   See Risks.

6. **Repo-level installation** is `.claude/settings.json` with
   `extraKnownMarketplaces` + `enabledPlugins`, applied once the folder is
   trusted. This is per-project, so every repo needs the stanza — a job for a
   `bootstrap` skill.

## Architecture

### Three tiers

| Tier | Contents | Cost |
| ---- | -------- | ---- |
| **0 — Constitution** | Injected into every session by the `SessionStart` hook. Identity and non-negotiables only, plus a one-line index of the plugin's skills. Target: ~50 lines. | Every session, forever |
| **1 — Skills** | Fired by activity: PR workflow, review, memory, language style, delegation. | Only when triggered |
| **2 — References** | Files inside skills, read on demand. | Only when read |

The filter for Tier 0: *if a line does not change behaviour in most sessions,
it is not Tier 0.*

A second filter, discovered while triaging `/godoc`:

> **A rule with no attachment point decays. A rule attached to a moment
> survives.**

"Always write GoDoc comments" applies at every line of code, therefore at no
particular moment, therefore never fires. "Before committing, GoDoc-comment
every exported symbol you added" hangs off an event that recurs constantly. Any
Tier-0 candidate for which no firing moment can be named is probably
decorative.

### Skills, not commands

The observation that drove this: of ten commands in `dot-claude`, roughly three
are remembered. That is a design signal, not a memory failure. Each command is
either a duty that should fire on its own, a rule already stated elsewhere, or a
genuine on-demand task. Only the third kind stays invocable.

Two house rules follow:

1. **Every skill description enumerates Claude's own tool calls as triggers**,
   not only human phrasings. The existing `pr` skill already does this and is
   the template.
2. **Skill is the knowledge; hook is the guarantee it gets consulted.** Where
   description-matching is merely a hope, a `PreToolUse` hook makes it a
   certainty.

## Decisions

### D1 — Drop the chained-`cd` rule, and invert its sibling

Both motivations are gone: permission approval (auto mode) and cwd confusion
(the harness now reports working-directory changes). The residual reason
survives only weakly — per the Bash tool description, *"prefer absolute paths —
`cd` in a compound command can trigger a permission prompt."*

That inverts the current guidance, which says to avoid absolute paths and `cd`
into place instead. For a tool-calling agent with a persistent but invisible
cwd, absolute paths are the robust form.

- Delete the rule, delete `hooks/block_chained_cd.sh`.
- Replace with one Tier-0 line preferring absolute paths.

### D2 — Adopt the GitHub MCP everywhere, including locally

This solves the CLI/web portability problem by deletion rather than
abstraction: one code path, both surfaces.

Second payoff: **hook enforcement becomes reliable.** A `PreToolUse` matcher on
`mcp__github__create_pull_request` is an exact string match. The `gh`
equivalent is a regex over a bash command line, defeated by a wrapper, a
heredoc, a variable, or a stray space.

Costs, acknowledged:

- ~55 tool definitions in context. Mitigate with the server's `--toolsets`
  flag; `pull_requests,issues,repos` covers the workflow.
- Local auth needs a PAT or `gh auth token`; web is wired automatically.
- Gaps remain: comment minimisation, `gh run watch`, log tailing.

`gh` stays installed as an escape hatch, demoted from default.

Tier-0 line: *GitHub work goes through the GitHub MCP. `gh` only for what MCP
cannot do, and say which.*

### D3 — Retire six of seven `pr-review` shell scripts

| Script | Replacement |
| ------ | ----------- |
| `pr-get-current-branch-number.sh` | trivial, inline |
| `pr-fetch-data.sh` | `pull_request_read` + `minimal_output` |
| `pr-post-comment.sh` | `add_issue_comment` |
| `pr-reply-thread.sh` | `add_reply_to_pull_request_comment` + `resolve_review_thread` |
| `pr-find-claude-comments.sh` | `search_issues` and listing tools |
| `pr-minimize-comments.sh` | **no MCP equivalent** — survives |
| `pr-minimize-previous-claude-comments.sh` | **no MCP equivalent** — survives |

Comment minimisation is `minimizeComment`, GraphQL-only and not exposed by the
GitHub MCP server. A real capability gap, not a legacy habit.

This yields a rule for the plugin's `scripts/` directory: **it holds only what
the MCP demonstrably cannot do, and each script's header says why it exists.**
A self-liquidating directory — as the MCP grows, scripts get deleted.

### D4 — Retire the haiku convention; keep poetry

`HAIKU.md` is a single mutable file at repo root that every branch rewrites.
That is a guaranteed conflict on every merge, by construction. A merge driver
(`merge=ours`, or union) would trade the conflict for a silently wrong file —
a workaround, and not worth it.

Poetry was never the cost; the tracked file was. PR bodies and review comments
are per-branch and never merged, so they carry poetry for free.

> **Poetry belongs on ephemeral artifacts, never on tracked files.**

- Remove: `commands/haiku.md`, the `Haiku` section of `CLAUDE.md`, the
  "plans always include a step for updating the haiku" clause, and `HAIKU.md`
  from both repos.
- Keep, already specified: the `pr-body` salutation — *a brief poem, in
  classical style, conveying the gist of the PR, formatted in italics.*
- Add, not yet specified: poetry in reviews. Currently a habit rather than a
  convention, and habits do not survive being ported into a skill. Needs one
  spec sentence. Open question Q1 settles its placement.

### D5 — The PR skill splits three ways

- `pr` — orchestrator for *opening*: branch guard, existing-PR check, draft
  state, issue references. Invokes the other two.
- `pr-title` — Conventional Commits, concise.
- `pr-body` — one-line summary (85 char limit), salutation, Summary, detail,
  unopinionated.

Real sibling skills with their own descriptions, so that a decision to edit a PR
body fires `pr-body` directly without routing through `pr`. Skill names are flat
within a plugin. Cost is two extra descriptions in context; negligible.

Further siblings: `pr-threads` (reply, resolve, minimise) and `pr-ci` (drive to
green).

### D6 — Collapse four review verbs into one skill

`/quick-review` states outright that it *is* `/deep-review quick` — *"Do not
duplicate the workflow here; follow `/deep-review` as the single source of
truth."* It exists only because a slash command cannot carry a remembered
default. A skill can. Add `/opinion` and the session built-in `/code-review`,
and there are four verbs for one activity, which is precisely why none of them
is remembered.

One `review` skill:

1. **Fires on its own moments** — about to open a PR, branch declared finished,
   about to request review, "is this ready".
2. **Depth is inferred, not typed** — from diff size and from what the diff
   touches. Anything in the sensitive list (auth, crypto, IAM, migrations)
   makes `security-reviewer` mandatory regardless of size. This kills
   `quick-review` properly, by automating the choice rather than deleting the
   alias.
3. **Feeds `pr-threads`** — findings are posted, then the thread lifecycle
   protocol runs. One pipeline, not two disconnected commands.
4. **Audit the 409 lines for rot** — hardcoded model assignments (the "two Opus
   reviewers" split will age badly), `Task` invocation syntax, `gh` calls, and
   overlap with the `code-review` and `security-review` skills that now ship in
   the session.

Open empirical question: whether four parallel reviewer agents still beat one
agent handed `review-guidelines.md`. Four was right when context was tighter
and models weaker; it may still be right, since independent passes genuinely
catch more. Worth measuring with `claude plugin eval` rather than inheriting.

### D7 — `/save` and `/restructure` become a memory skill on `PreCompact`

"Update project and local memory files" is a duty, not a command — and
remembering to save memory is the one thing that should never require
remembering.

`PreCompact` is the correct event: context is about to be discarded, which is
exactly when memory should be written. `SessionEnd` as a backstop for sessions
that end without compacting. `/restructure` is the same skill's other half —
compaction of memory rather than capture — triggered by a size threshold.

**The memory model loses its top tier.** Global `CLAUDE.md` becomes the plugin,
so "restructure your three memory files" now means three different things:

- project `CLAUDE.md` hygiene — unchanged
- `CLAUDE.local.md` compaction — the automatic half, fires on `PreCompact`
- global rules — a PR against `claude-daily-driver` instead of against
  `dot-claude`

The third is a relocation, not an upgrade: lessons-learned promotion is already
a reviewable commit today, because `dot-claude` is already a repo. What changes
is where the commit lands and, consequently, who sees the result — a rule
promoted into the plugin reaches web workers, a rule promoted into `dot-claude`
reaches one laptop.

One genuine gain does follow: the `pr` and `review` skills end up governing
changes to the constitution itself. Pleasingly self-hosted, and a real test of
whether the thing works.

### D8 — `/copilot` dies; its protocol is harvested

No Copilot subscription. But four sentences took thought and generalise to any
reviewer — human, Claude Approvals, or whatever bot comes next: *reply on the
thread, state implemented-or-rejected, resolve it, keep it concise and
technical, and re-resolve repeat findings with the identical message.* Those
move into `pr-threads`. The Copilot framing is the disposable half.

### D9 — `/godoc` survives as a manual sweep

It is a workaround for a rule that does not fire, and that is accepted
knowingly. The fix is at the source: give the rule an attachment point (before
committing), optionally enforced by a `PreToolUse` hook on `git commit`. Then
`/godoc` is what it should have been all along — a sweep over *old* code, a
legitimate on-demand task — rather than the primary mechanism for new code.

## Migration inventory

### `dot-claude/commands/`

| Command | Disposition |
| ------- | ----------- |
| `save.md` | → memory skill, `PreCompact` hook |
| `restructure.md` | → memory skill (compaction half) + PR-to-plugin (constitutional half) |
| `opinion.md` | delete — fourth review verb |
| `quick-review.md` | delete — alias |
| `deep-review.md` | → `review` skill, depth inferred |
| `post-deep-review.md` | → folded into `review` / `pr-threads` |
| `godoc.md` | → skill, manual sweep |
| `copilot.md` | delete; protocol harvested into `pr-threads` |
| `dependabot.md` | keep invocable — or a Routine (Q2) |
| `haiku.md` | delete |

### `dot-claude/agents/`

`architecture-reviewer`, `logic-reviewer`, `planning-fitness-reviewer`,
`security-reviewer` → plugin `agents/`, pending the D6 panel audit. Model
pinning to be removed.

### `dot-claude/hooks/`

`block_chained_cd.sh` → delete (D1).

### `dot-claude/tools/`

`pr-review/` → one surviving script (D3). `opencode-port/` is unrelated to this
work and stays put.

### `dot-claude/docs/`

`review-guidelines.md` → plugin, as a Tier-2 reference under the `review`
skill.

### `dot-claude/CLAUDE.md`

Split across Tier 0 (constitution), Tier 1 (skills) and Tier 2 (references) per
the architecture above. Most of the 17KB is conditional — Cinc/InSpec,
Terraform, `gh` API recipes, pr-review tool docs — and currently pays rent in
every session for nothing.

### `dot-claude/settings.json`

Stays. Permissions, model, effort, editor mode and `autoMode` cannot move
(constraint 2), and should not.

## Risks

### R1 — The `SessionStart` hook is a single point of failure

Today a missing `CLAUDE.md` is visible; the file is right there. A hook that
exits non-zero — bad path, missing `${CLAUDE_PLUGIN_ROOT}`, plugin not enabled
in this repo — yields a session with no constitution at all, and the failure is
silent.

Mitigation: fail loudly, and test it. A pleasing recursion — the rule *code
without tests is broken* is carried by a shell script that must itself be
tested, or the rule silently ceases to exist. Cheap safety net: end the
constitution with a checkable token and provide a `verify` skill.

### R2 — The constitution may not reach subagents

Per constraint 5, this is undocumented. It matters because delegation to
parallel background subagents is a core part of the workflow, and because today
the global `CLAUDE.md` *does* reach them.

**This must be settled empirically before anything else is designed around it**
— a constitution containing a nonsense token, a subagent asked to repeat it
back. Two minutes, and the answer determines whether the plugin can honestly
claim to replace the global `CLAUDE.md` or only replaces it in the main
session.

Mitigations if the answer is no, in order of preference:

1. Conduct rules in the plugin's own `agents/*.md` system prompts. Reliable,
   but covers only custom agents, not `Explore` / `Plan` / `general-purpose`.
2. A Tier-0 rule to restate the non-negotiables in every delegation prompt.
   Works everywhere; costs tokens per delegation; depends on compliance.
3. A `PreToolUse` hook on the `Agent` tool that appends the constitution.
   Actually enforceable, but fiddly.

### R3 — Always-on context is a permanent tax

Every Tier-0 line is paid for in every session, forever. The two filters above
(behaviour change in most sessions; a nameable firing moment) exist to keep
this honest.

### R4 — Per-repo bootstrap friction

Plugin installation on web is per-project (constraint 6). Every new repo needs
the `extraKnownMarketplaces` / `enabledPlugins` stanza, and a repo that lacks it
silently runs without the constitution — the same failure mode as R1, from a
different direction. A `bootstrap` skill should write the stanza; a repo
template should carry it.

## Open questions

- **Q1** — Poetry in reviews: opening salutation, or closing envoi after the
  findings? Inline comments stay prose either way; a poem on line 47 of a diff
  is noise in a thread someone has to act on.
- **Q2** — Should `dependabot` be a weekly Routine rather than something to
  remember to type?
- **Q3** — Should `review` fire automatically before *every* PR open? The
  purest expression of skill-not-command, and the one place it costs real
  latency on every single PR.
- **Q4** — How fat is Tier 0 allowed to get? Needs a number, or it will grow to
  17KB again.

## Sequencing

1. Settle R2 empirically. Everything else depends on the answer.
2. Draft the Tier-0 constitution and the `SessionStart` hook, with its test.
3. Split `pr` into `pr` / `pr-title` / `pr-body`; adopt MCP triggers (D2, D5).
4. Port `review` and the agent panel; audit for rot (D6).
5. Memory skill on `PreCompact` (D7).
6. Deletions (D1, D3, D4, D8) and the `bootstrap` skill (R4).
7. `claude plugin eval` suites for trigger accuracy across every skill.
