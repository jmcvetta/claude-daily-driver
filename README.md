# claude-daily-driver

Daily-driver skills for [Claude Code][cc], packaged as a plugin.

[cc]: https://claude.com/claude-code

This is one person's working toolkit, published rather than licensed. See
[ANTI-LICENSE.md](ANTI-LICENSE.md) before going further — and then, having
read it, do not go further.

## What's in it

The **constitution** — `context/constitution.md`, delivered to every session by
hook — plus skills that fire on activity:

| Skill | What it does |
| ---------- | ------------ |
| `pr`       | Opens the pull request for the current branch, or brings an open one up to date: branch guard, existing-PR check, draft by default, and the call on whether there is an issue to reference. Delegates the title and the body to the two below. |
| `pr-title` | The title convention: concise, and Conventional Commits with the type the contents actually warrant — which is what release-please reads to decide the next version. Delegates the type to the one below. |
| `conventional-commits-type` | Picks the type — `fix`, `feat`, `refactor` and the rest — from what the change *does*, never from what the diff looks like: two gates, the one test that separates a `fix` from a `feat`, and what each type releases. |
| `pr-body`  | The body structure: a one-line summary under 85 characters, a salutation in verse, an executive summary, as much engineering detail as fits, and the `Issues` section that closes it. |
| `issue-deps` | Records and reads GitHub issue relationships — blocked-by, sub-issue, and which PR closes what — proposing each edge from evidence and leaving the writing to a confirmation. |
| `session-title` | Names the session in the Claude web and mobile lists: a forty-character budget, chosen rather than measured, `#123 shortened issue title` while an issue is in hand, a short noun phrase otherwise. |
| `judgement-call` | The gate before a choice is put to you: where the correct, standard way already answers it, Claude answers it and says which way it went. What survives the gate is intent, a real trade-off, scope, and any confirmation another rule requires. |
| `review-cycle` | One round on a pull request: wait for CI on the head, run the built-in `/code-review` at a level it names, answer and resolve every finding, then decide from the reviewed head SHA whether a later push has earned a second round. |
| `undertake` | Takes an issue from its description to a pull request ready for review: the order of the nine steps, the gates between them, and the ready gate the sequence ends on. Invokes the skills above, directly or through `pr` and `review-cycle`. |

Four PR skills rather than one because skill names are flat within a plugin,
so siblings can be triggered independently: a decision to rewrite a PR body
fires `pr-body` directly, without routing through `pr` to get there. The type
is split out of `pr-title` for the same reason — "is this a fix or a feat?"
is asked with no title in hand. The cost is three extra descriptions in
context.

Each skill carries its own trigger register: the slash command where the skill
has one, natural phrasings — "open a PR" for `pr`, "fix the PR title" for
`pr-title`, "is this a fix or a feat?" for `conventional-commits-type`,
"rewrite the PR description" for `pr-body`, "this is blocked by
#123" for `issue-deps`, "rename this session" for `session-title`, "just
decide" for `judgement-call`, "address the review feedback" for
`review-cycle`, "undertake #34" or "implement #191" for `undertake` — and
Claude's own tool calls. The PR skills split
`mcp__github__create_pull_request` and `mcp__github__update_pull_request`
between them, `pr-title` on a call that sets a `title`, `pr-body` on one that
sets a `body`, `pr` on a create or on an update wider than either alone, with
`gh pr create` / `gh pr edit` as a fallback on a harness that still reaches
for them; `issue-deps` takes the GitHub MCP's sub-issue and issue-read tools;
`session-title` takes `mcp__Claude_Code_Remote__set_session_title`;
`judgement-call` takes `AskUserQuestion`; `review-cycle` takes the built-in
`/code-review` and the two thread calls, `add_reply_to_pull_request_comment`
and `resolve_review_thread`; and `undertake` takes the move from reading an
issue to writing code for it. Those registers are the point: a convention that
only fires when a human types a command quietly stops applying as more of the
work runs without one.

Naming the MCP tools is also a stronger trigger than naming `gh pr create` is —
an exact tool name where the fallback is, in effect, a regex over a bash
command line that a wrapper, a heredoc, a variable or a stray space would
defeat.

`issue-deps` carries the plugin's first runtime script,
`skills/issue-deps/scripts/issue-deps.sh`. It is `curl` against REST rather
than `gh`, because `gh` is not installed on a Claude Code web worker at all
while the ambient token is present on both surfaces — and it exists only
because the GitHub MCP exposes no blocked-by / blocking tool. Four endpoints
hold it up, and it is deleted the day the MCP exposes them.

Two skills that used to be here — `pr-threads` and `review` — no longer ship.
They are in [`attic/skills/`](attic/), kept rather than deleted, because
"possibly obsolete" is not the same judgement as "obsolete" and the second one
is cheaper to make once the first has been lived with. Nothing under `attic/`
is loaded, so retiring them costs nothing in context; bringing either back is
a `git mv`.

`pr-threads` is the half-exception. Its thread protocol — reply with a verdict,
resolve, re-resolve a repeat finding — ships again inside `review-cycle`, which
is where a protocol with a live caller belongs. What is still in the attic is
the comment minimisation the GitHub MCP does not expose, and that is all a
revival should bring back.

The reviewer panel `review` dispatched is still in [`agents/`](agents/) —
`logic-reviewer`, `architecture-reviewer`, `security-reviewer`,
`planning-fitness-reviewer` — dormant rather than deleted, and none of them
pins a model. A pin ages into a cost decision nobody revisits.

`judgement-call` is the odd one out: every other skill here fires on work
about to be done, and this one fires on a question about to be asked. Its register is
`AskUserQuestion`, the sentences that stand in for it, and your own "just
decide", because the thing it exists to stop is a menu of one correct option
and several hacks, which costs a round trip to answer with the standard that
was never in doubt. The rule it applies is the constitution's own: correct
beats quick, no workarounds. The boundary is the interesting half — intent, a
genuine trade-off and scope still come to you, an offer to do *more* is a scope
question and scope is yours, and no confirmation another rule requires is
waived. Anything irreversible, destructive or outward-facing is outside the
gate altogether, where the non-negotiables already govern it.

## Layout

The plugin is the repository root — `"source": "./"` in the marketplace
manifest — so there is no nested plugin directory:

```
claude-daily-driver/
├── .claude/settings.json   the stanza, applied to this repository too
├── .claude-plugin/
│   ├── plugin.json         the plugin, and the version releases bump
│   └── marketplace.json    the pointer `claude plugin install` reads
├── .github/workflows/      CI, PR title check, infra, release automation
├── agents/                 the reviewer panel, dormant while `review` is retired
├── attic/                  kept but not shipped; nothing here is loaded
├── context/
│   └── constitution.md     always-on rules, one file, read by both hooks
├── docs/                   decisions, and the measurements behind them
│   └── planning/           the plan, and the record of decisions made under it
├── evals/                  the trigger suites, and the constitution's live half
├── hooks/
│   ├── hooks.json          SessionStart, and PreToolUse on the Agent tool
│   └── inject-constitution.py
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the checks CI runs, the stanza, the MCP tally
├── skills/
│   ├── pr/SKILL.md
│   ├── pr-title/SKILL.md
│   ├── conventional-commits-type/SKILL.md
│   ├── pr-body/SKILL.md
│   ├── issue-deps/
│   │   ├── SKILL.md
│   │   └── scripts/        plugin runtime, owned by the skill beside it
│   ├── session-title/SKILL.md
│   ├── judgement-call/SKILL.md
│   ├── review-cycle/SKILL.md
│   └── undertake/SKILL.md
└── template/.claude/       copied into a repository to enable the plugin
```

## The constitution

`context/constitution.md` is the always-on layer: identity and
non-negotiables, in force in every session. A plugin cannot ship a
`CLAUDE.md` — plugins contribute context through skills, agents and hooks —
so it is delivered by hook, and it takes **two** hooks rather than one:

| Delivery | Main session | Subagent |
| -------- | ------------ | -------- |
| `CLAUDE.md` | yes | yes |
| `SessionStart` `additionalContext` | yes | **no** |
| `SessionStart` + `PreToolUse` on `Agent` | yes | **yes** |

That middle row was measured, not assumed, and it is why shipping only the
first hook would have been a silent regression against the `CLAUDE.md` this
replaces — invisible, and manifesting only in the subagents doing the actual
work. The repair is a `PreToolUse` hook that rewrites the subagent's prompt
through `hookSpecificOutput.updatedInput`. The evidence and method are in
[the planning doc](docs/planning/plugin-replaces-global-memory.md) under R2.

Both hooks are one script reading one file by exact path — never a glob over
`context/`, which is how two injection points come to disagree the day a
second file lands. When the file cannot be read, the hooks say so in the
model's context, in a `systemMessage` to the terminal, and on stderr, rather
than handing back a session that quietly has no constitution.

The last line of the file is a token. Ask a session for it: a session that
cannot quote it did not get the constitution, whatever else it may believe.

## Testing the constitution

The rule *code without tests is broken* is carried by the very hooks that
deliver it, so the delivery is tested in two halves, split where the
credential requirement starts:

- **`make check`** runs `scripts/check-constitution.py`: both hooks against
  synthetic event JSON, asserting the constitution comes back from each — and
  that the subagent's prompt is *exactly* the main session's context plus the
  original prompt, which is the assertion that catches drift between the two
  injection points. No model, no credentials.
- **`make evals-run TASKS='tasks/constitution/*.yaml'`** runs the live half,
  which is the R2 experiment itself: a subagent is asked for a token nobody put
  in its prompt. Only a real session can prove the harness honours
  `updatedInput`, and a credentialed run is the price of asking. See
  [`evals/README.md`](evals/README.md).

They fail for different reasons and deserve to fail separately: the first
tests this plugin, the second tests an assumption about the harness that a
future release could withdraw without telling anyone.

## Installing it

Installation is **per-machine — or, in the cloud, per-environment**. The
plugin's bytes land in `~/.claude` and are read from there; a repository can
point at a plugin, it can never carry one.

On a laptop that is two commands, once per machine:

```sh
claude plugin marketplace add jmcvetta/claude-daily-driver
claude plugin install daily-driver@claude-daily-driver
```

In the cloud there is no interactive `/plugin` to reach for and no shell of
your own to run the commands from, so they go in the environment's **Setup
script**, which is the one writer that beats the plugin scan.

### A cloud environment, in five steps

All of it in the Claude Code web UI at [claude.ai/code][web]. The environment
dialog is behind the cloud icon above the message box: hover an environment,
then the gear. There is no settings page and no direct URL.

[web]: https://claude.ai/code

1. **Create the environment.** Point it at the repository you want the plugin
   in. The install lands in a `~/.claude` the environment keeps, so it is done
   once per environment rather than once per repository — measured on a
   laptop, and *not* repeated in the cloud, so if you open a second repository
   in the same environment, run step 4 there too before relying on it.

2. **Give it this Setup script.**

   ```bash
   #!/bin/bash
   # CACHEBUST: 1
   #
   # The environment snapshots itself when this script succeeds, keyed on the
   # script's text, and later sessions skip it. Bump the number above to bust
   # that cache and reinstall the plugin at its current release.
   claude plugin marketplace add jmcvetta/claude-daily-driver
   claude plugin install --yes daily-driver@claude-daily-driver

   # Both commands can return 0 while leaving the plugin uncached, so check
   # what the loader actually reads.
   grep -qF '"daily-driver@claude-daily-driver"' ~/.claude/plugins/installed_plugins.json &&
     compgen -G ~/.claude/plugins/cache/claude-daily-driver/daily-driver/*/.claude-plugin/plugin.json >/dev/null
   ```

   No `|| true`. A script that exits zero on a failed install snapshots the
   failure, and every later session then starts with no plugin and no sign of
   it; exiting non-zero fails the session, builds no snapshot, and the next
   attempt tries again.

3. **Start a web session on that environment.**

4. **Ask it what it got.** Nothing announces a plugin that failed to load, so
   this step is the whole point of the other four. Ask for three things, in
   this order:

   > Quote the last line of `context/constitution.md`. Then list the skills
   > available to you whose names begin `daily-driver:`. Then run `ls
   > ~/.claude/plugins/cache/claude-daily-driver/daily-driver/`.

   The constitution arrives by hook rather than as a skill, so its last line
   is the one answer no other check reaches; a session that cannot quote it
   did not get it, whatever else it believes. The skills should be the ones in
   the table above. The directory name is the installed version — which is
   what step 5 turns on.

   Do **not** ask what plugins are installed. A session answers that from the
   harness, which — measured, in two separate cloud environments — reported an
   empty list while the plugin was live and its skills were firing. It is the
   one question here with a known wrong answer.

5. **After a release, bump the `CACHEBUST` number.** An existing environment
   does not pick up a new release on its own, and this is the only way to make
   it. The environment snapshots itself the first time the Setup script
   succeeds and every later session boots from that snapshot with the script
   skipped — so the install line runs once, pins whatever release was current
   that day, and never runs again. The snapshot is keyed on the script's
   *text*, so changing any byte of it invalidates the key and the install runs
   again at the current release; the comment exists to be that byte. Asking a
   session inside the environment to update the plugin does not work: the
   session is downstream of the snapshot, not the thing that builds it.

   Then repeat step 4 and read the version off the cache directory. The
   script's verification line cannot do this for you — it greps for the plugin
   key and globs the cache for *any* version, so a bump that failed to fetch
   anything new satisfies it, exits 0, and snapshots itself looking exactly
   like a bump that worked.

[docs/bootstrapping-a-repository.md](docs/bootstrapping-a-repository.md) has
the mechanism under all of this — where an install puts its state, the three
ways to check whether the plugin loaded, and the two readers that look like
checks and are not. It also has *the stanza*: the `extraKnownMarketplaces` +
`enabledPlugins` block a repository can carry in `.claude/settings.json` to
declare that it wants the plugin, what it is worth (less than it looks, and
nothing at all in the cloud), and the two writers for it — `template/.claude/`
to copy into a repository that has none, and `python3 scripts/stanza.py
--write <repo>` to merge it into one that already has settings.

## Portability

The same tree is read by more than one harness:

- **Claude Code** discovers it as a plugin.
- **[oh-my-pi][omp]** (`omp`) reads Claude Code plugins natively through its
  `claude-plugins` discovery provider, so it needs no separate port. A
  checkout can be loaded directly with `omp --plugin-dir <path>`.

[omp]: https://omp.sh

## Checks

`make check` is what CI runs — the same target, not a restatement of it, so a
leg added here is a leg the required check gains:

```sh
make check
```

It runs `claude plugin validate --strict` over the marketplace manifest, the
plugin manifest, the skills and the agents — one invocation each, because
`validate` reads a single directory at a time and would otherwise never see the
panel — then `scripts/check-manifests.py` for what `validate` lets through: a
skill whose frontmatter `name` disagrees with its directory, an agent whose
`name` disagrees with its filename, two agents claiming one `name` so that only
one of them is reachable, a `description:` that is present but empty, a `name`
disagreeing between the two manifests, and a copy of the repository stanza that
has drifted from the names it enables. Then `scripts/check-constitution.py`,
described above.

`make check-infra` parses the OpenTofu stack and is deliberately not part of
`make check`; see [infra/github/README.md](infra/github/README.md).

The trigger-accuracy evals are out for the same reason twice over: they need a
live model, and CI here is deliberately credential-free. See
[evals/README.md](evals/README.md) for what they assert and how to run them.

`make mcp-usage` is not a check at all. It counts which GitHub MCP tools this
laptop actually called, so the server's `--toolsets` list can be narrowed on
evidence rather than taste; see [docs/github-mcp.md](docs/github-mcp.md).

## Releases

release-please cuts them from the Conventional Commit type in a merged pull
request's **title**, which squash-merge makes the commit subject. The version
it bumps is `version` in `.claude-plugin/plugin.json`, and it bumps the
matching field on the marketplace entry in the same commit — `claude plugin
validate --strict` fails when those two disagree, so they cannot be released
apart.

The first release is `0.1.0`. Until it is cut, both manifests read `0.0.0`,
which is release-please's way of spelling "nothing released yet".

Each pull request also gets a comment saying which tags merging it would cut,
from [release-please-projected-releases-action][prpra] — the type in the title
being otherwise invisible until it is too late to change.

[prpra]: https://github.com/jmcvetta/release-please-projected-releases-action

## Don't install this

Genuinely: write your own. This fits its author the way a worn boot fits a
foot, and you have different feet.

If you disregard that, the mechanics are ordinary and the consequences are
enumerated at length in [ANTI-LICENSE.md](ANTI-LICENSE.md).
