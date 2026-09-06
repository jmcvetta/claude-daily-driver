# claude-daily-driver

Daily-driver skills for [Claude Code][cc], packaged as a plugin.

[cc]: https://claude.com/claude-code

This is one person's working toolkit, published rather than licensed. See
[ANTI-LICENSE.md](ANTI-LICENSE.md) before going further — and then, having
read it, do not go further.

## What's in it

| Skill | What it does |
| ----- | ------------ |
| `pr`  | Opens and updates GitHub pull requests: Conventional Commits title, draft by default, and a body with a one-line summary, a salutation in verse, an executive summary, and engineering detail. |
| `issue-deps` | Records and reads GitHub issue relationships — blocked-by, sub-issue, and which PR closes what — proposing each edge from evidence and leaving the writing to a confirmation. |
| `review` | Reviews a branch or pull request with a panel of reviewer agents, infers how deep to go from the diff itself, walks the findings through with you, and posts the result in verse. |

Each skill triggers on the literal slash command, on natural phrasings ("open
a PR", "this is blocked by #123"), and on Claude's own tool calls —
`mcp__github__create_pull_request` and `mcp__github__update_pull_request` for
`pr`, or `gh pr create` and `gh pr edit` on a harness that still reaches for
them; the GitHub MCP's sub-issue and issue-read tools for `issue-deps`. That
last register is the point: a convention that only fires when a human types a
command quietly stops applying as more of the work runs without one.

`issue-deps` carries the plugin's first runtime script,
`skills/issue-deps/scripts/issue-deps.sh`. It is `curl` against REST rather
than `gh`, because `gh` is not installed on a Claude Code web worker at all
while the ambient token is present on both surfaces — and it exists only
because the GitHub MCP exposes no blocked-by / blocking tool. Four endpoints
hold it up, and it is deleted the day the MCP exposes them.

`review` replaced four verbs — `/deep-review`, `/quick-review`, `/opinion`,
and the session's own `/code-review` — which were four names for one activity,
which is precisely why none of them was ever remembered. There is nothing left
to choose: depth comes off the diff, and anything touching auth, crypto, IAM or
a migration pulls in the security reviewer whatever its size. Two rules shape
the rest of it. It never fires when a pull request is *opened*, because
expensive skills must be pulled rather than pushed — output that always appears
gets skimmed, and a draft PR opens the conversation rather than ending the
work. And its poetry attaches only to the comment it posts, never to the
findings: a finding someone has to act on is prose.

The panel it dispatches lives in [`agents/`](agents/) — `logic-reviewer`,
`architecture-reviewer`, `security-reviewer`, `planning-fitness-reviewer` — and
none of them pins a model. A pin ages into a cost decision nobody revisits.

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
├── agents/                 the reviewer panel the `review` skill dispatches
├── context/
│   └── constitution.md     the always-on layer, injected by the hooks
├── docs/                   decisions, and the measurements behind them
│   └── planning/           the plan, and the record of decisions made under it
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the manifest checks CI runs, the stanza, the MCP tally
├── skills/
│   ├── pr/SKILL.md
│   ├── issue-deps/
│   │   ├── SKILL.md
│   │   └── scripts/        plugin runtime, owned by the skill beside it
│   └── review/
│       ├── SKILL.md
│       └── references/     the review guidelines, passed to every agent
└── template/.claude/       copied into a repository to enable the plugin
```

## Enabling it in a repository

Plugin installation is per-project: a repository declares the plugin for
everyone who works in it — a web worker included — by carrying an
`extraKnownMarketplaces` + `enabledPlugins` stanza in its
`.claude/settings.json`. A repository without it runs without the plugin and
gives no sign of it. Declares, not guarantees: carrying the stanza is necessary
and, on the version measured, was not sufficient.

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
plugin manifest, the skills and the agents — one invocation each, because
`validate` reads a single directory at a time and would otherwise never see the
panel — then `scripts/check-manifests.py` for what `validate` lets through: a
skill whose frontmatter `name` disagrees with its directory, an agent whose
`name` disagrees with its filename, two agents claiming one `name` so that only
one of them is reachable, a `description:` that is present but empty, a `name`
disagreeing between the two manifests, and a copy of the repository stanza that
has drifted from the names it enables.

`make check-infra` parses the OpenTofu stack and is deliberately not part of
`make check`; see [infra/github/README.md](infra/github/README.md).

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
