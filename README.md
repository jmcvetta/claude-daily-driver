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

Claude Code enables plugins per project, so a repository can carry its own
enablement and turn this plugin on for anyone working in it — on a laptop, at
least; the web-worker case is measured below and does not currently work. The
stanza goes in the repository's `.claude/settings.json`:

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

The stanza is not the whole job. Once the project folder is trusted, the next
session registers the marketplace and clones it under
`~/.claude/plugins/marketplaces/`, with no separate prompt — but on 2026-09-06,
against Claude Code 2.1.263, that is where it stopped. The plugin itself was
not installed: `claude plugin list` reported nothing installed,
`~/.claude/plugins/installed_plugins.json` stayed empty, and no
`daily-driver:pr` skill was present in the session. Installing it explicitly,
once, is what made the skills appear:

```sh
claude plugin install daily-driver@claude-daily-driver
```

Read that the same way as the web-worker result below — a dated observation of
one version, measured with `claude -p` sessions against an isolated
`CLAUDE_CONFIG_DIR`, not a permanent property of the platform. If a newer
release installs from the stanza alone, the command above is a no-op.

Three things about that are worth stating plainly.

**Marketplace and install state are per-user; the stanza is what travels.**
`known_marketplaces.json` and `installed_plugins.json` both live under
`~/.claude/plugins/` and are shared by every project on the machine, so the
install above is a once-per-machine step — and at user scope, which is what
`claude plugin install` chose, it makes the plugin available even in
repositories carrying no stanza at all. What the stanza buys is that a fresh
checkout on a fresh machine knows where the marketplace lives without anyone
having to be told. Put it in every repository that expects the plugin.

**It requires trusting the project folder.** Nothing above happens before trust.
On an untrusted folder — `hasTrustDialogAccepted: false` for that path in
`~/.claude.json` — the stanza is inert, and inert quietly: no marketplace, no
clone, no plugin, no complaint.

**A repository without the stanza fails silently.** This is R4 in [the planning
document](docs/planning/plugin-replaces-global-memory.md), and it is the reason
this section exists. On a machine that has not already installed the plugin, a
session in a repository lacking the stanza runs with no constitution at all and
gives no sign of it — no warning, no degraded mode,
no missing-skill error, just a Claude that has never heard of any of this. So
when a session feels unusually unconstrained, verify before concluding it is
being disobedient. Asking the session is no use — a Claude that never loaded
the plugin has nothing to report — so run the check in a shell:

```sh
claude plugin list
```

The output is several lines per plugin; what matters is that
`daily-driver@claude-daily-driver` is listed at all and that its `Status:` line
reads enabled. "No plugins installed." is the failure. Note that reading
`.claude/settings.json` is *not* this check: it proves the stanza is committed,
which the web-worker result below shows is a different thing from the plugin
being loaded.

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
`claude plugin list` at the top of a web session before relying on the
constitution being there. The stanza sitting in the checkout is not evidence
that it took effect.

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
