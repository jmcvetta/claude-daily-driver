# claude-daily-driver

Daily-driver skills for [Claude Code][cc], packaged as a plugin.

[cc]: https://claude.com/claude-code

This is one person's working toolkit, published rather than licensed. See
[ANTI-LICENSE.md](ANTI-LICENSE.md) before going further — and then, having
read it, do not go further.

## What's in it

| Skill | What it does |
| ---------- | ------------ |
| `pr`       | Opens the pull request for the current branch, or brings an open one up to date: branch guard, existing-PR check, draft by default, and the call on whether there is an issue to reference. Delegates the title and the body to the two below. |
| `pr-title` | The title convention: concise, and Conventional Commits with the type the contents actually warrant — which is what release-please reads to decide the next version. |
| `pr-body`  | The body structure: a one-line summary under 85 characters, a salutation in verse, an executive summary, as much engineering detail as fits, and the `Issues` section that closes it. |

Three skills rather than one because skill names are flat within a plugin, so
siblings can be triggered independently: a decision to rewrite a PR body fires
`pr-body` directly, without routing through `pr` to get there. The cost is two
extra descriptions in context.

Each carries its own trigger register. `pr` takes the literal `/pr` and
phrasings like "open a PR"; `pr-title` takes "fix the PR title"; `pr-body`
takes "rewrite the PR description". Alongside those, each takes Claude's own
calls to `mcp__github__create_pull_request` and
`mcp__github__update_pull_request`, narrowed to its own half — `pr-title` on a
call that sets a `title`, `pr-body` on one that sets a `body`, `pr` on a create
or on an update wider than either alone — and `gh pr create` / `gh pr edit` on
a harness that still reaches for them. That last register is the point: a
convention that only fires when a human types a command quietly stops applying
as more of the work runs without one.

Naming the MCP tools is also a stronger trigger than naming `gh pr create` is —
an exact tool name where the fallback is, in effect, a regex over a bash
command line that a wrapper, a heredoc, a variable or a stray space would
defeat.

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
├── context/
│   └── constitution.md     the always-on layer, injected by the hooks
├── docs/                   decisions, and the measurements behind them
│   └── planning/           the plan, and the record of decisions made under it
├── evals/                  `claude plugin eval` suites, one per skill
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the manifest checks CI runs, the stanza, the MCP tally
├── skills/
│   ├── pr/SKILL.md
│   ├── pr-title/SKILL.md
│   └── pr-body/SKILL.md
└── template/.claude/       copied into a repository to enable the plugin
```

## Enabling it in a repository

Plugin installation is per-project: a repository enables the plugin for
everyone who works in it — a web worker included — by carrying an
`extraKnownMarketplaces` + `enabledPlugins` stanza in its
`.claude/settings.json`. A repository without it runs without the plugin and
gives no sign of it.

[docs/bootstrapping-a-repository.md](docs/bootstrapping-a-repository.md) has
the stanza to copy, the two names that are easy to get wrong, the three ways
to write it into a repository, and how to tell whether it actually loaded.
`python3 scripts/stanza.py` prints the same stanza, derived from the
manifests, and `python3 scripts/stanza.py --write <repo>` merges it into
another checkout.

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
plugin manifest and the components, then `scripts/check-manifests.py` for the
four things `validate` lets through: a skill whose frontmatter `name`
disagrees with its directory, a `description:` that is present but empty, a
`name` disagreeing between the two manifests, and a copy of the repository
stanza that has drifted from the names it enables.

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
