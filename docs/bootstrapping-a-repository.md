# Bootstrapping a repository

Plugin installation is **per-project**. A repository declares this plugin for
everyone who works in it — a laptop CLI session and a Claude Code web worker
alike — by carrying one stanza in its `.claude/settings.json`. A repository
without the stanza runs without the plugin, and says nothing about it.

Declares, not guarantees. The stanza is necessary; whether it is *sufficient*
is a measurement rather than a reading of the documentation, and on the version
measured below it was not.

That silence is the whole reason this page exists. There is no error, no
warning, and no missing file to notice; the session simply behaves as though
the plugin had never been written. It is the same failure as a broken
`SessionStart` hook, arriving from a direction no check inside the plugin can
see — a skill that would report the problem ships *inside* the plugin, so in
the one repository that needs it, it is not there to run. **Bootstrapping is
an act performed from outside the repository being bootstrapped.**

## The stanza

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

Two of those names are easy to get wrong, and getting either wrong fails the
same silent way:

- **The marketplace is `claude-daily-driver`, not `daily-driver`.** A
  marketplace is named by its manifest's `name`, which is the repository's
  name; the plugin inside it is `daily-driver`. Measured, not assumed: `claude
  plugin marketplace add jmcvetta/claude-daily-driver` records it under
  `claude-daily-driver` in `~/.claude/plugins/known_marketplaces.json`.
- **The enablement key is `plugin@marketplace`** — so
  `daily-driver@claude-daily-driver`. The symmetrical-looking
  `daily-driver@daily-driver` names a marketplace that does not exist, and an
  `enabledPlugins` entry whose marketplace is not registered is skipped as
  orphaned.

Nobody has to hold that straight. `scripts/stanza.py` derives the stanza from
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, and
`make check` fails if any copy of it — the template, this repository's own
settings, the block above — has drifted from the manifests. Prose may quote
half the stanza, or one entry of it, and still pass; what fails is a name or a
value the manifests do not agree with. A block that shows a *wrong* stanza on
purpose is exempted with `<!-- stanza-check: ignore -->` on the line above it.

The stanza itself is one command away:

```sh
python3 scripts/stanza.py
```

## Getting it into a repository

Three writers, in the order to reach for them.

**A new repository: copy the template.** `template/` holds the stanza and
nothing else, so it can be copied wholesale into a repository that has no
`.claude/` yet:

```sh
cp -R /path/to/claude-daily-driver/template/.claude/. .claude/
```

The trailing `/.` matters. `cp -R .../template/.claude .` writes
`.claude/.claude/settings.json` in a repository that already has a `.claude/`,
silently, and the plugin then loads nowhere; the form above copies the
*contents* either way, creating `.claude/` when there is none. If the
repository already has a `.claude/settings.json` worth keeping, use the helper
below instead — this copy would replace it.

Better still, keep the same file in whatever GitHub template repository new
work starts from, so the question never comes up.

**An existing repository: run the helper from this checkout.**

```sh
python3 /path/to/claude-daily-driver/scripts/stanza.py --write ~/src/some-repo
```

It merges into an existing `.claude/settings.json` rather than replacing it,
says what it changed, and is a no-op when the stanza is already there. It runs
from *this* repository's checkout precisely because it must not depend on the
plugin being enabled in the repository it is fixing.

**A genuinely cold start: copy the block above by hand.** No plugin, no
checkout, no laptop — a web worker and this page. It is the only route that
survives that, which is why it is written out in full even though nobody will
use it twice.

Whichever route, commit the file. The stanza is a property of the repository,
not of the machine.

## What has to be true for it to work

**The folder has to be trusted.** The marketplace is registered and the plugin
cached when the project folder is trusted, with no separate prompt — but not
before. Measured: an identical stanza in an untrusted folder registers no
marketplace, downloads nothing, and the session runs happily with none of the
plugin loaded.

**Trust is necessary and — measured — not sufficient.** In a *trusted* folder
carrying exactly the stanza above, the marketplace was registered and the
plugin cached, and the session still loaded nothing: its `init` payload
reported `plugins: []`, with no `daily-driver:pr` skill. Running

```sh
claude plugin install daily-driver@claude-daily-driver
```

once flipped the same repository to a payload naming the plugin, with the skill
present. That install lands at **user** scope, so it then applies on the whole
machine, in repositories carrying no stanza at all — which is why the stanza is
what travels and the install is a once-per-machine step, not a substitute.

Both halves were measured with headless `claude -p` sessions against a scratch
`CLAUDE_CONFIG_DIR`. An interactive session may behave differently, and a later
release may make the install a no-op; re-run the third check below rather than
inheriting this conclusion.

**It is per-repository, not per-user.** Marketplace state is cached once per
user under `~/.claude/plugins/`, but the *enablement* rides in each
repository's `.claude/settings.json`. Every repository worked in from the web
needs its own stanza. A laptop can enable the plugin once in
`~/.claude/settings.json` and forget about it; a web worker has no such
settings to inherit, which is exactly the gap the stanza closes.

## Checking whether it is actually enabled

The habit worth having: **when a session feels unusually unconstrained, verify
before assuming it is being disobedient.** A session with no plugin is not
ignoring the rules, it does not have them.

Three checks, in increasing order of what they actually prove, and one that
looks like a check but is not:

**Read the file.** Cold-start-proof, works from anywhere, and answers the
question the stanza is responsible for:

```sh
grep -n enabledPlugins .claude/settings.json
```

It proves the file says so, which is all it proves.

**Ask the CLI what it has on this machine.**

```sh
claude plugin details daily-driver@claude-daily-driver
```

In a repository whose settings name it, on a machine that has already cached
the marketplace — one prior session in a repository carrying the stanza — this
prints the plugin's component inventory; run anywhere else it says `not found`.
Read that as "the names are right and the plugin is on this machine", not as
"it loaded here". Measured: it printed the full inventory for a session whose
`init` payload reported no plugins at all.

**Ask a session what it loaded.** The only one of the three that answers the
question the others are proxies for:

```sh
claude -p "say ok" --output-format stream-json --verbose | python3 -c \
  "import sys,json;[print(d.get('plugins')) for d in map(json.loads,sys.stdin) if d.get('subtype')=='init']"
```

An empty list is the failure, whatever the first two say; a loaded plugin
appears with its name, cache path and version.

**`claude plugin list` does not answer this either.** A plugin arriving by
stanza is served from `~/.claude/plugins/cache/` and never recorded in
`installed_plugins.json`, so `list` reports only what was installed by hand.
Its `No plugins installed` is therefore not proof of failure — but it is not
proof of success either, and on the version measured the two coincided.

## Web workers: verify, do not assume

The plugin documentation covers Claude Code generally and does not call out the
web surface separately, so this too was measured. A Claude Code web worker was
started on a branch of this repository carrying exactly the stanza above.
**The plugin did not load.** `claude plugin marketplace list` reported no
marketplaces, `claude plugin list` reported nothing installed,
`known_marketplaces.json` did not exist, and no `daily-driver:pr` skill was
present in the session. The checkout showed `hasTrustDialogAccepted: false`: a
container that clones a repository and starts working never presents a trust
dialog, so the trust gate above is never passed. The same stanza in a trusted
folder on the CLI does register the marketplace, which locates the difference
in trust rather than in the stanza.

So the web worker is currently the case the stanza does *not* rescue, which is
the sharpest form of the argument for checking rather than assuming: run the
third check above at the top of a web session before relying on the
constitution being there. The stanza sitting in the checkout is not evidence
that it took effect.

## What none of this covers

A web worker, in a repository with no stanza, with no laptop in reach. Nothing
inside the plugin can report its own absence, and no command on that machine
will have anything to say. Only the habit above reaches that case at all —
which is the argument for the template, whose whole value is that the question
is settled before anyone is in a position to ask it.

## Measurements

Established on 2026-09-06 against Claude Code 2.1.263, by running the CLI with
a scratch `HOME` — and, for the rows about what a session loads, headless
`claude -p` against a scratch `CLAUDE_CONFIG_DIR` — rather than by reading the
documentation.

| Question | Answer |
| -------- | ------ |
| Marketplace name registered from `jmcvetta/claude-daily-driver` | `claude-daily-driver` |
| Stanza in a **trusted** folder | marketplace registered, plugin cached |
| …and what that session loaded | nothing: `init` reports no plugins, no `daily-driver:pr` |
| …after `claude plugin install` once, same repository | plugin loaded, skill present, scope `user` |
| …and in a repository with no stanza after that install | still loaded — the install is per-machine |
| Stanza in an **untrusted** folder | ignored entirely, silently |
| Stanza in a Claude Code **web worker** | not loaded; `hasTrustDialogAccepted: false` |
| `claude plugin list` in the stanza-only repository | `No plugins installed` |
| `claude plugin details daily-driver@claude-daily-driver` in that repository | full component inventory, though nothing had loaded |
| The same command outside it | `not found` |
