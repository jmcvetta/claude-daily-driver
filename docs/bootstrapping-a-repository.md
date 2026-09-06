# Bootstrapping a repository

Plugin installation is **per-project**. A repository enables this plugin for
everyone who works in it — a laptop CLI session and a Claude Code web worker
alike — by carrying one stanza in its `.claude/settings.json`. A repository
without the stanza runs without the plugin, and says nothing about it.

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
settings, the block above — has drifted from the manifests:

```sh
python3 scripts/stanza.py
```

## Getting it into a repository

Three writers, in the order to reach for them.

**A new repository: copy the template.** `template/` holds the stanza and
nothing else, so it can be copied wholesale into a repository that has no
`.claude/` yet:

```sh
cp -R /path/to/claude-daily-driver/template/.claude .
```

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
enabled when the project folder is trusted, with no separate prompt — but not
before. Measured: an identical stanza in an untrusted folder registers no
marketplace, downloads nothing, and the session runs happily with none of the
plugin loaded.

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

Two checks, and one that looks like a check but is not:

**Read the file.** Cold-start-proof, works from anywhere, and answers the
question the stanza is responsible for:

```sh
grep -n enabledPlugins .claude/settings.json
```

It proves the file says so, which is all it proves.

**Ask the CLI, from inside the repository.**

```sh
claude plugin details daily-driver@claude-daily-driver
```

In a repository whose settings enable it, this prints the plugin's component
inventory. Run anywhere else it says `not found`, which is the discrimination
that makes it useful. It needs a machine that has already cached the
marketplace — one prior session in a repository carrying the stanza — so it
answers "did this load here", not "is my stanza correct".

**`claude plugin list` does not answer this.** Measured, and worth knowing
before it misleads someone: a repository-enabled plugin is served from
`~/.claude/plugins/cache/` and is never recorded in `installed_plugins.json`,
so `claude plugin list` prints `No plugins installed` in a repository where the
plugin is loading perfectly well. `list` reports what was installed by hand.

## What none of this covers

A web worker, in a repository with no stanza, with no laptop in reach. Nothing
inside the plugin can report its own absence, and no command on that machine
will have anything to say. Only the habit above reaches that case at all —
which is the argument for the template, whose whole value is that the question
is settled before anyone is in a position to ask it.

## Measurements

Established on 2026-09-06 against Claude Code 2.1.263, by running the CLI with
a scratch `HOME` rather than by reading the documentation.

| Question | Answer |
| -------- | ------ |
| Marketplace name registered from `jmcvetta/claude-daily-driver` | `claude-daily-driver` |
| Stanza in a **trusted** folder | marketplace registered, plugin cached and loaded |
| Stanza in an **untrusted** folder | ignored entirely, silently |
| `claude plugin list` in a repository where it loaded | `No plugins installed` |
| `claude plugin details daily-driver@claude-daily-driver` in that repository | full component inventory |
| The same command outside it | `not found` |
