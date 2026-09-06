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

### Three layers

Named, not numbered — a layer whose name has to be decoded is a layer nobody
will remember the rules for.

| Layer | Contents | Cost |
| ----- | -------- | ---- |
| **Constitution** | Injected into every session by the `SessionStart` hook. Identity and non-negotiables only, plus a one-line index of the plugin's skills. | Every session, forever |
| **Skills** | Fired by activity: PR workflow, review, memory, language style, delegation. | Only when triggered |
| **References** | Files inside skills, read on demand. | Only when read |

"Constitution" is chosen deliberately, and earns its weight: supreme law, always
in force, and amended only by a deliberate reviewable process. Under D7 that
process is literally a pull request against this repository.

**There is no line limit.** A cap would be arbitrary and would get gamed by
compression rather than by cutting. Admission is governed by two filters
instead:

*Does this change behaviour in most sessions?*

And, discovered while triaging `/godoc`:

> **A rule with no attachment point decays. A rule attached to a moment
> survives.**

"Always write GoDoc comments" applies at every line of code, therefore at no
particular moment, therefore never fires. "Before committing, GoDoc-comment
every exported symbol you added" hangs off an event that recurs constantly. Any
constitutional candidate for which no firing moment can be named is probably
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
- Replace with one constitutional line preferring absolute paths.

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

Constitutional line: *GitHub work goes through the GitHub MCP. `gh` only for what MCP
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

Removals are wider than the file itself. `HAIKU.md` has accreted special-case
handling across the review tooling, all of which goes with it:

- `commands/haiku.md`
- the `Haiku` section of `CLAUDE.md`, and the "plans always include a step for
  updating the haiku" clause
- `HAIKU.md` from both repos
- the `HAIKU.md` skip rules in `deep-review.md` (three of them) and the
  "not subject to review at all" carve-out in `review-guidelines.md` — both
  exist only because the file changes on every branch
- the "Do NOT reuse the haiku from `HAIKU.md`" clause in `post-deep-review.md`

That the convention needed a carve-out in the review rules is itself evidence
against it.

**Poetry survives, and is already fully specified — no new spec needed.** The
existing convention is more precise than the "salutation or envoi" framing that
prompted this question, because it is both, and the second one is *earned*:

| Where | Spec | Source |
| ----- | ---- | ------ |
| PR body | A brief poem, classical style, conveying the gist of the PR, in italics. | `skills/pr/SKILL.md` |
| Review comment, opening | A formal poem, any style, max 6 lines, summarising the PR. | `post-deep-review.md:36` |
| Review comment, closing | Only on a 👍 verdict: a terse panegyric in formal verse, heroic style, in the Roman / Greek / Persian / Chinese tradition. | `post-deep-review.md:57` |
| Review *findings* | *"No poems. No accolades. Keep it terse."* | `deep-review.md:285` |

The distinction in the last row is the load-bearing one: poetry attaches to the
*posted artifact*, never to the analysis. A finding someone has to act on is
prose.

One coupling to preserve while porting: the review comment's `*Claude {model
version}*` self-identification line is not decoration. It is how
`pr-minimize-previous-claude-comments.sh` — one of the two scripts surviving D3
— recognises its own comments. Self-ID and the minimise script move together or
not at all.

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

### D10 — `review` never fires automatically on PR open

Rejected, and the rejection sets a boundary the rest of the design needs.

"Skill, not command" is about *duties that decay because nobody remembers to
invoke them*. It is not a mandate that every skill self-trigger. Review is
expensive in time, tokens and attention; a skill that costs that much should be
**pulled, not pushed**. Firing it on every PR open would tax every trivial
branch to catch the occasional serious one, and would train exactly the reflex
that makes review worthless — skimming the output because it always appears.

There is also a workflow reason. PRs open as **drafts** (D5). Opening a draft is
the start of the conversation, not the end of the work; review belongs on the
draft when the branch is actually ready, which is a judgement call, not an
event.

> **Cheap skills may push. Expensive skills must be pulled.**

So `review` keeps an explicit invocation, and its self-triggering descriptions
(D6.1) cover the *asking* moments — "is this ready", "review this branch",
"about to request review" — never the mechanical act of opening a PR.

### D11 — `dependabot` is a response, not a schedule

The premise behind Q2 was wrong. Dependabot **is already the Routine**: GitHub
runs it from `.github/dependabot.yml` and opens PRs on a schedule of its own.
Wrapping it in a second scheduler would be one cron job watching another.

What `dependabot.md` actually encodes is the *response* — batch the open
dependabot PRs, upgrade in a worktree, validate, open one consolidated PR. That
is a duty triggered by a condition (open dependabot PRs exist), which is exactly
the shape of a skill: it fires when the condition is noticed during ordinary PR
work, and stays invocable for when it is not.

Separately, and outside this work: `.github/dependabot.yml` is not configured in
this repository at all, so nothing is opening those PRs here yet.

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
| `dependabot.md` | → skill, fires on noticing open dependabot PRs (D11) |
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

`review-guidelines.md` → plugin, as a reference under the `review` skill.

### `dot-claude/CLAUDE.md`

Split across constitution, skills and references per the architecture above. Most of the 17KB is conditional — Cinc/InSpec,
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
2. A constitutional rule to restate the non-negotiables in every delegation
   prompt.
   Works everywhere; costs tokens per delegation; depends on compliance.
3. A `PreToolUse` hook on the `Agent` tool that appends the constitution.
   Actually enforceable, but fiddly.

### R3 — Always-on context is a permanent tax

Every constitutional line is paid for in every session, forever. With no line
limit (deliberately), the two filters above — behaviour change in most
sessions, and a nameable firing moment — are the only thing holding the line.
They have to be applied honestly at each amendment, which is another argument
for amendments being reviewable pull requests.

### R4 — Per-repo bootstrap friction

Plugin installation on web is per-project (constraint 6). Every new repo needs
the `extraKnownMarketplaces` / `enabledPlugins` stanza, and a repo that lacks it
silently runs without the constitution — the same failure mode as R1, from a
different direction. A `bootstrap` skill should write the stanza; a repo
template should carry it.

## Settled questions

Kept for the reasoning, since three of the four were resolved by finding the
answer already existed rather than by deciding anything.

- **Q1 — poetry in reviews: salutation or envoi?** Neither; both, already
  specified in `post-deep-review.md`, with the envoi conditional on approval.
  See D4.
- **Q2 — should `dependabot` be a Routine?** Bad premise: GitHub already runs
  that schedule. See D11.
- **Q3 — should `review` fire before every PR open?** No, definitively, and the
  reasoning generalises into a rule about which skills may self-trigger. See
  D10.
- **Q4 — how fat may the constitution get?** No limit, and the numbered "tiers"
  are renamed to named layers. See the architecture section.

## Open questions

- **Q5** — Does the four-agent review panel still beat one agent handed
  `review-guidelines.md`? Empirical; measure with `claude plugin eval` rather
  than inherit. Raised in D6.
- **Q6** — Which of the ~55 GitHub MCP tools does the workflow actually need?
  Determines the `--toolsets` setting, and therefore the standing context cost
  of D2.

## Sequencing

1. Settle R2 empirically. Everything else depends on the answer.
2. Draft the constitution and the `SessionStart` hook, with its test.
3. Split `pr` into `pr` / `pr-title` / `pr-body`; adopt MCP triggers (D2, D5).
4. Port `review` and the agent panel; audit for rot (D6).
5. Memory skill on `PreCompact` (D7).
6. Deletions (D1, D3, D4, D8) and the `bootstrap` skill (R4).
7. `claude plugin eval` suites for trigger accuracy across every skill.
