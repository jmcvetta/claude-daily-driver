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

Both skills trigger on the literal slash command, on natural phrasings ("open
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

## Layout

The plugin is the repository root — `"source": "./"` in the marketplace
manifest — so there is no nested plugin directory:

```
claude-daily-driver/
├── .claude-plugin/
│   ├── plugin.json         the plugin, and the version releases bump
│   └── marketplace.json    the pointer `claude plugin install` reads
├── .github/workflows/      CI, PR title check, infra, release automation
├── context/
│   └── constitution.md     the always-on layer, injected by the hooks
├── docs/planning/          the plan, and the record of decisions made under it
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the manifest checks CI runs
└── skills/
    ├── pr/SKILL.md
    └── issue-deps/
        ├── SKILL.md
        └── scripts/         plugin runtime, owned by the skill beside it
```

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
three things `validate` lets through: a skill whose frontmatter `name`
disagrees with its directory, a `description:` that is present but empty, and
a `name` disagreeing between the two manifests.

`make check-infra` parses the OpenTofu stack and is deliberately not part of
`make check`; see [infra/github/README.md](infra/github/README.md).

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
