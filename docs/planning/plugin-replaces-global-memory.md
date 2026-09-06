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

3. **Always-on context in the main session comes from a `SessionStart` hook**
   emitting
   `hookSpecificOutput.additionalContext`. The plugin ships `hooks/hooks.json`
   plus a script that reads `${CLAUDE_PLUGIN_ROOT}/context/*.md`. Being
   harness-executed, it behaves the same on CLI and web.

4. **`InstructionsLoaded` and `SubagentStart` are observation-only.** Neither
   supports decision control, so neither can inject or amend instructions.

5. **`SessionStart` `additionalContext` does not reach subagents.** The docs
   are silent on this; it was measured (see R2). A `CLAUDE.md` reaches both the
   main session and its subagents, so hook-delivered context is strictly weaker
   unless paired with a second hook.

6. **`PreToolUse` can rewrite tool input** via
   `hookSpecificOutput.updatedInput`. This is what closes the gap in
   constraint 5: a hook matching the `Agent` tool prepends the constitution to
   every subagent prompt. Measured, not assumed.

7. **Repo-level installation** is `.claude/settings.json` with
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

And a third, from D1:

> **Do not legislate what the harness already says.**

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

### D1 — Delete the chained-`cd` rules outright, replacing them with nothing

Both original motivations are gone: permission approval (auto mode) and cwd
confusion (the harness now reports working-directory changes).

The first instinct was to replace them with a constitutional line preferring
absolute paths, since the underlying behaviour has not entirely vanished — the
working directory does still get reset, and `cd` in a compound command can
still trigger a prompt. But the harness **already says so itself**, in the Bash
tool description: *"Working directory persists between calls, but prefer
absolute paths — `cd` in a compound command can trigger a permission prompt."*

Legislating it again would buy nothing and cost tokens in every session, so this
is a pure deletion:

- Delete the "no chained `cd`" rule.
- Delete the "do not use absolute paths unless necessary" rule, which was
  backwards anyway.
- Delete `hooks/block_chained_cd.sh`.
- Add nothing.

That yields a third admission filter, alongside the two in the architecture
section:

> **Do not legislate what the harness already says.** Duplicated guidance costs
> tokens every session and rots silently when the harness changes underneath it.

This filter deserves suspicion when the rest of the 17KB is triaged. A rule
written years ago to compensate for a weaker harness is exactly the kind that
survives on inertia — and the whole point of an amendment being a reviewable
pull request is that inertia has to be argued for.

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

### D3 — Retire `pr-review` scripts one at a time, on evidence

An earlier draft of this section retired six of the seven outright, on a table
mapping each to a plausible MCP tool. That was too fast. Only two of the seven
verdicts rested on evidence; the rest rested on a tool *name* looking like it
would do the job, which is not the same as it doing the job.

So the rule for this directory is a bar, not a list:

> **A script is retired when its replacement has been demonstrated on a real
> PR — not when a plausibly-named MCP tool exists.**

Current state of knowledge, honestly labelled:

| Script | Status |
| ------ | ------ |
| `pr-minimize-comments.sh` | **Keeps.** `minimizeComment` is GraphQL-only and unexposed by the MCP. A real capability gap. |
| `pr-minimize-previous-claude-comments.sh` | **Keeps**, same gap. |
| `pr-find-claude-comments.sh` | **Probably keeps.** It returns GraphQL node IDs (`IC_kwDO…`); `search_issues` does not. The surviving minimize scripts consume exactly those IDs, so retiring their supplier while keeping them makes no sense. |
| `pr-fetch-data.sh` | **Unknown, leaning keeps.** It emits review *thread* IDs (`PRRT_…`). `resolve_review_thread` requires one. Whether `pull_request_read` surfaces thread IDs at all is unverified, and the answer decides this. |
| `pr-reply-thread.sh` | **Unknown.** `add_reply_to_pull_request_comment` plus `resolve_review_thread` look equivalent, but only if thread IDs are obtainable — so this is blocked behind the row above. |
| `pr-post-comment.sh` | **Likely retires.** `add_issue_comment` is a straightforward equivalent; still wants one demonstration. |
| `pr-get-current-branch-number.sh` | **Likely retires**, but not free: there is no "PR for the current branch" MCP call, so it becomes `list_pull_requests` filtered by head ref. |

Two things follow. First, the dependency chain matters more than the individual
mappings: minimisation is a genuine gap, minimisation needs node IDs, and node
IDs come from a script. Cut the middle of that chain and the surviving ends stop
working — the kind of silent breakage that only shows up months later when an
old review comment fails to collapse.

Second, the surviving directory still needs its governing rule, which is
unchanged and is the point of the exercise:

> **`scripts/` holds only what the MCP demonstrably cannot do, and each
> script's header says why it exists.**

A self-liquidating directory. As the MCP grows, scripts get deleted — but each
deletion is earned by a demonstration, not by an assumption.

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

Open empirical question, narrowed in Q5: not whether the panel as a whole
earns its place — the cheap mechanical tier plainly does — but whether the two
Opus judgment reviewers are better as two roles or one.

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

### D13 — A relationship skill, wanted; the MCP is the gap, not the API

Promoted from candidate. Dependencies are a long-wanted capability, now
available, and intended for constant use — which settles the scope question
that would otherwise have gated this.

What the MCP surface actually offers, checked rather than assumed:

| Relationship | Status |
| ------------ | ------ |
| **Sub-issues** (parent/child) | Fully exposed. `sub_issue_write` adds, removes, reprioritises and re-parents; `issue_read` reads `get_sub_issues` and `get_parent`; `issue_write` can create an issue directly under a parent — **including cross-repo**, via `parent_owner` / `parent_repo`. |
| **PR closes issue** | Readable, and *only* here — REST has no such field. `issue_read` returns `closed_by_pull_requests` as a count plus up to five references. |
| **Blocked-by / blocking** | **Not exposed by this MCP** — no tool, no field. |

**The API does expose blocked-by / blocking programmatically**, and that
documentation now has an address:
[`jmcvetta/career`, `docs/issue-dependencies.md`](https://github.com/jmcvetta/career/blob/master/docs/issue-dependencies.md).
It carries the endpoints, the `issue_id`-is-the-database-id trap, cross-repo
edges, and a probe table of what the API refuses. Start there; do not
rediscover it.

So the gap is the **MCP's, not GitHub's**, and the shape follows: dependencies
become the first new resident of `scripts/` under D3's rule — a script that
exists because the MCP demonstrably cannot do the job, with a header saying
exactly that and a plausible expiry date for when the MCP catches up. That is
the self-liquidating directory working as designed rather than accumulating.

**Answered: issues only.** Probed 2026-09-06 and recorded in that document
under *Pull requests are not in this graph*. Both graphs refuse a pull request
at both ends — dependencies with "Source issue may only be an issue" and
"Target issue may only be an issue", sub-issues with "Parent may only be an
issue" and "Sub issue may only be an issue".

So the conditional stands as written: **this is an issue-graph skill that PRs
merely reference.** The PR half reduces to `closed_by_pull_requests` and the
`Closes #123` convention, and a pull request that must wait on another pull
request has nowhere structural to record it — that dependency belongs on the
issues the two PRs implement, where it also outlives both PRs being merged or
abandoned.

Three findings from the same probe change what gets built.

**A read cannot see the restriction, which promotes the verification step
below from good practice to necessary.** A `blocked_by` read against a pull
request answers `200` with an empty array — indistinguishable from an issue
that genuinely has no edges. Nothing in the read path ever says *wrong
kind of object*, so a skill that inspects relationships by reading them will
report a clean graph for a question the API declined to answer. Only the write
refuses, and only the write says so.

**The write surface is half what was assumed, which bounds the script.**
`POST .../dependencies/blocking` does not exist: `404` in GitHub's own error
shape, with `blocking` listed under reads only. So the first resident of
`scripts/` needs exactly one write route (`POST .../dependencies/blocked_by`),
one `DELETE`, and two `GET`s. Four endpoints is small enough to make D3's
expiry note concrete — the script goes the day the MCP exposes them.

**The skill's two halves read through different clients, which is not an
incidental detail.** `closed_by_pull_requests` is absent from REST entirely;
the MCP is where it surfaces (GraphQL underneath, on the evidence of the field
name — unverified, since the container it was probed from serves only a pinned
set of GraphQL operations). REST offers `cross-referenced` on the issue
timeline instead, which renders the PR that closed an issue and a PR that
merely mentioned it *identically* — measured on `jmcvetta/career#177`, where
`#178` closed it and `#176` only refers to it. So the verification this section
already wants — *does the structured relationship match what the body claims?*
— asks the MCP for the closes-link and `gh api` / `curl` for the dependency
edges. One skill, two clients, for a reason that is neither arbitrary nor going
away on its own.

Two design notes, both worth fixing before the skill is written.

**The graph is already being written to, badly.** The `pr` skill's
`Closes #123` convention is prose in a PR body, and that prose is exactly what
populates `closed_by_pull_requests`. So the relationship graph has a writer
today — an unvalidated string, with no way to notice when it is wrong. The skill
should treat the graph as the artifact and the text convention as one writer
into it, which also gives it a natural verification step: does the structured
relationship match what the body claims?

**Guard against manufactured relationships.** A skill whose description says
these relationships are wanted constantly will start inventing them, for exactly
the reason a role-framed security reviewer invents findings (Q5): an agent given
a job feels obliged to produce output. The firing moment is real and specific —
a dependency is discovered while planning work, or while writing a PR body and
realising it cannot merge first — but the skill must **propose from evidence and
let the user confirm**, never assert. A wrong dependency is worse than a missing
one: it blocks work silently, and nobody thinks to look for a relationship they
did not create.

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

`pr-review/` → an unknown number of surviving scripts, retired individually on
evidence (D3); at least two keep, probably three. `opencode-port/` is unrelated
to this work and stays put.

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

### R2 — RESOLVED: the constitution does not reach subagents, and a hook repairs it

Settled empirically on 2026-09-06 rather than left to the documentation, which
is silent. Method: a `SessionStart` hook injecting a nonsense passphrase, a
subagent asked for it, and the parent's `Agent` tool input inspected to confirm
the parent did not leak the answer into the subagent prompt.

| Delivery mechanism | Main session | Subagent |
| ------------------ | ------------ | -------- |
| `CLAUDE.md` | yes | **yes** |
| `SessionStart` `additionalContext` | yes | **no** |
| `SessionStart` + `PreToolUse` on `Agent` with `updatedInput` | yes | **yes** |

The middle row is the finding that matters: **a plugin-delivered constitution is
strictly weaker than the `CLAUDE.md` it replaces.** Delegation is central to the
workflow, so shipping the hook alone would have been a silent regression — the
worst kind of bug, invisible and only manifesting in the subagents doing the
actual work.

The third row is the repair, and it is verified rather than proposed. A
`PreToolUse` hook matching the `Agent` tool rewrites `tool_input.prompt` via
`hookSpecificOutput.updatedInput`, prepending the constitution. In the test the
prompt Claude *sent* contained no passphrase; the hook injected it in flight;
the subagent answered correctly.

This is the same house rule as everywhere else — *skill is the knowledge, hook
is the guarantee* — applied to the constitution itself.

**Consequence for the design (D12).** The constitution ships as one file in the
plugin with two injection points reading it:

1. `SessionStart` → `additionalContext`, for the main session.
2. `PreToolUse` on `Agent` → `updatedInput`, for every subagent.

One source of truth, two delivery paths, no drift. This supersedes the three
speculative mitigations previously listed here; agent-definition system prompts
and a "restate the rules when delegating" rule are both unnecessary now, the
first because it covered only custom agents and the second because it depended
on compliance rather than enforcement.

**Acceptance test, to be committed with the hook.** The experiment above *is*
the test, and it must ship as one: inject a known token, spawn a subagent, and
assert the token comes back. It covers R1 and R2 together — a constitution that
fails to load and a constitution that fails to propagate both show up as the
same red test. Given that the constitution carries the rule *code without tests
is broken*, it would be indefensible for its own delivery to be untested.

### R3 — Always-on context is a permanent tax

Every constitutional line is paid for in every session, forever. With no line
limit (deliberately), the two filters above — behaviour change in most
sessions, and a nameable firing moment — are the only thing holding the line.
They have to be applied honestly at each amendment, which is another argument
for amendments being reviewable pull requests.

### R4 — Per-repo bootstrap friction

Plugin installation on web is per-project (constraint 7). Every new repo needs
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

### Q5 — Is the Opus judgment layer better as two roles or one?

Narrowed from "does the panel beat a single agent", which was the wrong
framing. The panel is already heterogeneous — Haiku for mechanical checks,
Sonnet for judgment, Opus for `security-reviewer` and `logic-reviewer`. The
Haiku tier is not competing with a strong reviewer; it is doing cheap
mechanical work and should stay regardless. **The live question is only whether
the two Opus reviewers are better as two roles or one.**

A panel is not free, and the costs are structural rather than incidental:

1. **Cross-cutting findings are invisible to it.** The most valuable finding in
   a review is often an interaction — this security fix breaks the retry path.
   The security reviewer sees the fix, the logic reviewer sees the retry path,
   neither sees the seam. A single agent holding the whole diff can. Panels are
   structurally blind to precisely the findings that matter most.
2. **Role framing manufactures findings.** An agent told it is the security
   reviewer will find security issues, because a security reviewer reporting
   nothing feels like a failed security reviewer. Single-agent review carries no
   such quota pressure.
3. **Synthesis is lossy.** The synthesiser sees findings, not the reasoning
   behind them, and dedupes, ranks, softens and drops accordingly.
4. **Volume dilutes.** A longer union gets skimmed, and the real bug sits at
   position 14. Precision matters more than recall for a review someone
   actually reads — the same argument that settled D10.
5. **The independence is weaker than it looks.** Four instances of one base
   model reading one diff have correlated errors: four draws from a single
   distribution, not four experts.

Against which the panel genuinely wins on recall for specialist dimensions
where a checklist beats a generalist's skim, and on diffs longer than one
attentive pass can hold.

The reason to measure is not that the panel is wrong. It is that:

> The panel was compensating for a weaker single reviewer. As the single agent
> gets stronger, the panel's marginal recall gain shrinks while its precision
> cost stays flat. **The crossover point moves.**

`deep-review.md` was designed on the far side of that crossover. Nobody has
checked whether it still is.

### Q6 — Which GitHub MCP toolsets? Measure, do not guess

Downgraded from a design question to a setup task, since the MCP has never been
run locally.

Setup has two paths: `github/github-mcp-server` locally via Docker or binary
with a PAT, or GitHub's hosted remote server — **verify whether the hosted one
requires a Copilot seat** before depending on it, as that subscription is
cancelled. The local path certainly does not.

On the toolset itself: enable everything, use it for a fortnight, then narrow to
what was actually called. Choosing a toolset now would be exactly the kind of
premature decision that produced ten commands nobody remembers.

## Sequencing

1. ~~Settle R2 empirically.~~ **Done** — see R2. The answer requires a second
   hook, folded into step 2.
2. Draft the constitution plus *both* delivery hooks — `SessionStart` for the
   main session, `PreToolUse` on `Agent` for subagents — and the acceptance
   test that proves the token reaches both.
3. Split `pr` into `pr` / `pr-title` / `pr-body`; adopt MCP triggers (D2, D5).
4. Port `review` and the agent panel; audit for rot (D6).
5. Memory skill on `PreCompact` (D7).
6. Deletions (D1, D3, D4, D8) and the `bootstrap` skill (R4).
7. `claude plugin eval` suites for trigger accuracy across every skill.
