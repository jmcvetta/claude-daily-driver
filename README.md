# claude-daily-driver

Daily-driver skills for [Claude Code][cc], packaged as a plugin.

[cc]: https://claude.com/claude-code

This is one person's working toolkit, published rather than licensed. See
[ANTI-LICENSE.md](ANTI-LICENSE.md) before going further — and then, having
read it, do not go further.

## What's in it

The **constitution** — `context/constitution.md`, delivered to every session
by hook — plus nine skills:

| Skill | What it does |
| ----- | ------------ |
| `pr` | Opens the pull request for the current branch, or brings an open one up to date: branch guard, existing-PR check, draft state. Delegates the title and the body. |
| `pr-title` | The title: concise, and Conventional Commits, which is what release-please reads to decide the next version. |
| `conventional-commits-type` | Picks the type — `fix`, `feat`, `refactor` and the rest — from what the change *does*, never from what the diff looks like. |
| `pr-body` | The body: a one-line summary, a salutation in verse, an executive summary, engineering detail, and the `Issues` section that closes it. |
| `issue-deps` | Records and reads GitHub issue relationships — blocked-by, sub-issue, and which pull request closes what. |
| `session-title` | Names the session for the Claude web and mobile lists: forty characters, `#123 shortened issue title` while an issue is in hand. |
| `judgement-call` | The gate before a choice is put to you: where the correct, standard way already answers it, Claude answers it and says which way it went. |
| `review-cycle` | One round on a pull request: the built-in `/code-review`, a verdict on every finding, and the test for whether a later push has earned a second round. |
| `undertake` | Takes a piece of work from its description to a pull request ready for review, opening the issue first where there is none. |

A skill fires on its slash command, on natural phrasings of the work, and on
Claude's own tool calls — `mcp__github__create_pull_request` for `pr`,
`AskUserQuestion` for `judgement-call`. Each `description` carries its register.

[`agents/`](agents/) holds a reviewer panel, dormant while the `review` skill is
retired. [`attic/`](attic/) holds what no longer ships; nothing there is loaded,
and [its README](attic/README.md) says what is kept and why.

## The constitution

`context/constitution.md` is the always-on layer, in force in every session and
every subagent. Thirteen sections:

| Section | What it settles |
| ------- | --------------- |
| Identity | An engineering approach, whose taste, and Simplified Technical English for prose. |
| Non-negotiables | Never a production system; dangerous commands in a sandbox or not at all; code without tests is broken; problems are fixed, never hidden. |
| While I write code | The manual first, simplicity, no reinventing a library, no workarounds, correct over quick. |
| When I hit a wall | Stop on the error, re-assess an approach that is failing, ask rather than guess at intent. |
| Before I commit | A doc comment on every new exported symbol, focused commits, message style, named files staged. |
| Before I call it done | The project's own gates are run, not reasoned about. |
| Dependencies | Added and pinned through the package manager; never a hand-edited manifest or lockfile. |
| GitHub | The GitHub MCP, `curl` where it cannot reach, and the one `gh` invocation. |
| Delegation | Plan first, delegate the implementation, batch the subagents, watch the quota. |
| Memory | Global, project and local layers, and subsidiarity between them. |
| Temporary files | `.tmp.claude/`, unless the harness supplies a scratchpad. |
| Skills | One line on each skill above, so a session knows what it has. |
| Verification | How to prove the file arrived. |

**What belongs there** is the admission test the file states on itself: a rule
lives here only if it changes behaviour in most sessions, hangs off a nameable
moment, and says something the harness does not already say — it is paid for in
every session and every subagent, forever. Amendments are pull requests against
this repository.

**Whether a session got it**: the last line of the file is a token. Ask for it.
A session that cannot quote it did not get the constitution, whatever else it
may believe.

**How it arrives**: a plugin cannot ship a `CLAUDE.md`, so two hooks deliver
the file — `SessionStart` for the session, `PreToolUse` on the `Agent` tool for
every subagent, which `SessionStart` alone does not reach. Both read the one
file by exact path and fail loudly. The measurement behind the second hook is
in [the planning doc](docs/planning/plugin-replaces-global-memory.md) under
R2.

## Layout

The plugin is the repository root — `"source": "./"` in the marketplace
manifest — so there is no nested plugin directory.

```
claude-daily-driver/
├── .claude-plugin/         plugin.json (the version releases bump) and
│                           marketplace.json (what `claude plugin install` reads)
├── agents/                 the reviewer panel, dormant
├── attic/                  kept but not shipped; nothing here is loaded
├── context/constitution.md always-on rules, one file, read by both hooks
├── docs/                   how this repository is meant to be used
├── evals/                  the trigger suites, and the constitution's live half
├── hooks/                  SessionStart, and PreToolUse on the Agent tool
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the checks CI runs, the stanza, the MCP tally
├── skills/                 one directory per skill in the table above
└── template/.claude/       copied into a repository to enable the plugin
```

## Installing it

Installation is **per-machine — or, in the cloud, per-environment**. The
plugin's bytes land in `~/.claude` and are read from there; a repository can
point at a plugin, it can never carry one.

On a laptop, two commands, once per machine:

```sh
claude plugin marketplace add jmcvetta/claude-daily-driver
claude plugin install daily-driver@claude-daily-driver
```

In the cloud the same commands go in the environment's **Setup script**, which
is the one writer that beats the plugin scan. The environment dialog is behind
the cloud icon above the message box at [claude.ai/code][web].

[web]: https://claude.ai/code

```bash
#!/bin/bash
# CACHEBUST: 1
#
# The environment snapshots itself on this script's text and later sessions
# skip it. Bump the number to reinstall at the current release.
claude plugin marketplace add jmcvetta/claude-daily-driver
claude plugin install --yes daily-driver@claude-daily-driver

# Both commands can return 0 while leaving the plugin uncached, so check
# what the loader actually reads.
grep -qF '"daily-driver@claude-daily-driver"' ~/.claude/plugins/installed_plugins.json &&
  compgen -G ~/.claude/plugins/cache/claude-daily-driver/daily-driver/*/.claude-plugin/plugin.json >/dev/null
```

No `|| true`: a script that exits zero on a failed install snapshots the
failure. Then start a session there and **ask it what it got**, because nothing
announces a plugin that failed to load —

> Quote the last line of `context/constitution.md`. Then list the skills
> available to you whose names begin `daily-driver:`. Then run `ls
> ~/.claude/plugins/cache/claude-daily-driver/daily-driver/`.

Do **not** ask what plugins are installed: that question has a known wrong
answer. After a release, bump the `CACHEBUST` number and ask again — an
existing environment does not pick up a new release on its own.

[docs/bootstrapping-a-repository.md](docs/bootstrapping-a-repository.md) has
the mechanism under all of this, and *the stanza* a repository can carry in
`.claude/settings.json` to say it wants the plugin.

## Portability

The same tree is read by more than one harness. **Claude Code** discovers it as
a plugin. **[oh-my-pi][omp]** (`omp`) reads Claude Code plugins natively, so it
needs no separate port; a checkout loads with `omp --plugin-dir <path>`.

[omp]: https://omp.sh

## Checks

`make check` is what CI runs — the same target, not a restatement of it. It
runs `claude plugin validate --strict` over the manifests, the skills and the
agents; `scripts/check-manifests.py` for what `validate` lets through, such as
a skill whose frontmatter `name` disagrees with its directory; and
`scripts/check-constitution.py`, which drives both hooks against synthetic
event JSON and asserts the constitution comes back from each.

Two targets are deliberately outside it. `make check-infra` parses the OpenTofu
stack — see [infra/github/README.md](infra/github/README.md). `make evals-run`
needs a live model, and CI here is credential-free — see
[evals/README.md](evals/README.md); `TASKS='tasks/constitution/*.yaml'` is the
other half of the constitution's test, since only a real session can prove the
harness honours the subagent hook.

`make mcp-usage` is not a check. It counts which GitHub MCP tools this laptop
called, so the server's `--toolsets` list can be narrowed on evidence; see
[docs/github-mcp.md](docs/github-mcp.md).

## Releases

release-please cuts them from the Conventional Commit type in a merged pull
request's **title**, which squash-merge makes the commit subject. It bumps
`version` in `.claude-plugin/plugin.json` and the matching field on the
marketplace entry together — `claude plugin validate --strict` fails when
those two disagree. Each pull request gets a comment saying which tags merging
it would cut, from [release-please-projected-releases-action][prpra].

[prpra]: https://github.com/jmcvetta/release-please-projected-releases-action

## Don't install this

Genuinely: write your own. This fits its author the way a worn boot fits a
foot, and you have different feet.

If you disregard that, the mechanics are ordinary and the consequences are
enumerated at length in [ANTI-LICENSE.md](ANTI-LICENSE.md).
