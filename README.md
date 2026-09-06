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

The `pr` skill triggers on the literal `/pr`, on natural phrasings ("open a
PR", "fix the PR title"), and on Claude's own use of `gh pr create` and
`gh pr edit`. That last register is the point: a convention that only fires
when a human types a command quietly stops applying as more of the work runs
without one.

## Layout

The plugin is the repository root — `"source": "./"` in the marketplace
manifest — so there is no nested plugin directory:

```
claude-daily-driver/
├── .claude-plugin/
│   ├── plugin.json         the plugin, and the version releases bump
│   └── marketplace.json    the pointer `claude plugin install` reads
├── .github/workflows/      CI, PR title check, infra, release automation
├── infra/github/           the repository's own settings, as OpenTofu
├── scripts/                the manifest checks CI runs
└── skills/
    └── pr/SKILL.md
```

## Portability

The same tree is read by more than one harness:

- **Claude Code** discovers it as a plugin.
- **[oh-my-pi][omp]** (`omp`) reads Claude Code plugins natively through its
  `claude-plugins` discovery provider, so it needs no separate port. A
  checkout can be loaded directly with `omp --plugin-dir <path>`.

[omp]: https://omp.sh

## Enabling it in a repository

Claude Code enables plugins per project, so a repository turns this one on for
anyone working in it — laptop or web worker — by carrying the stanza in its own
`.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "claude-daily-driver": {
      "source": {
        "source": "github",
        "repo": "jmcvetta/claude-daily-driver"
      }
    }
  },
  "enabledPlugins": {
    "daily-driver@claude-daily-driver": true
  }
}
```

Copy it verbatim; commit it. Both names are load-bearing and both come from
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json):
`claude-daily-driver` is the marketplace `name`, and the `enabledPlugins` key is
the plugin `name` joined to it as `plugin@marketplace`. Note that the two differ
— the marketplace is `claude-daily-driver` and the plugin inside it is
`daily-driver` — and that a typo in either is not an error, it is silence.

There is nothing else to run. Once the project folder is trusted, the next
session adds the marketplace, clones it under `~/.claude/plugins/marketplaces/`,
and enables the plugin, with no separate prompt.

Three things about that are worth stating plainly.

**It is per-repository, not per-user.** Marketplace state is stored once per
user, in `~/.claude/plugins/known_marketplaces.json`, but the *enablement* rides
in each repository's `.claude/settings.json`. Adding the marketplace on the
laptop enables the plugin nowhere by itself; every repository worked in needs
its own copy of the stanza.

**It requires trusting the project folder.** Nothing above happens before trust.
On an untrusted folder — `hasTrustDialogAccepted: false` for that path in
`~/.claude.json` — the stanza is inert, and inert quietly: no marketplace, no
clone, no plugin, no complaint.

**A repository without the stanza fails silently.** This is R4 in [the planning
document](docs/planning/plugin-replaces-global-memory.md), and it is the reason
this section exists. A session in a repository that lacks the stanza runs with
no constitution at all and gives no sign of it — no warning, no degraded mode,
no missing-skill error, just a Claude that has never heard of any of this. So
when a session feels unusually unconstrained, verify before concluding it is
being disobedient. The check has to come from outside the session:

```sh
claude plugin list         # daily-driver@claude-daily-driver, project, enabled
cat .claude/settings.json  # the stanza above
```

### Web workers: verify, do not assume

The plugin documentation covers Claude Code generally and does not call out the
web surface separately, so this was measured rather than asserted. On
2026-09-06, against Claude Code 2.1.263, a Claude Code web worker was started
on a branch of this repository carrying exactly the stanza above. **The plugin
did not load.** `claude plugin marketplace list` reported no marketplaces,
`claude plugin list` reported nothing installed, `known_marketplaces.json` did
not exist, and no `daily-driver:pr` skill was present in the session. The
checkout showed `hasTrustDialogAccepted: false`: a container that clones a
repository and starts working never presents a trust dialog, so the gate above
is never passed. The same stanza in a trusted folder on the CLI does take
effect — the marketplace shows up in `claude plugin marketplace list` once a
session has started there — which locates the difference in trust rather than in
the stanza.

Read that as a dated observation of one environment and one version, not as a
permanent property of the platform; it is exactly the sort of thing that changes
between releases. Read it also as the reason the R4 habit is not optional: run
the two checks at the top of a web session before relying on the constitution
being there.

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
