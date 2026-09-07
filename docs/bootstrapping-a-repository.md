# Bootstrapping a repository

Enablement is **per-repository**. Installation is **per-machine** — or, in the
cloud, per-environment. A repository can declare that it wants this plugin; it
can never carry one. A repository that declares a plugin nothing has installed
loads nothing, and says nothing about it.

Declares, not guarantees. The stanza below is the whole of what a repository
can contribute; whether that is *sufficient* is a measurement rather than a
reading of the documentation, and on the version measured below it was not.

That silence is the whole reason this page exists. There is no error, no
warning, and no missing file to notice; the session simply behaves as though
the plugin had never been written. It is the same failure as a broken
`SessionStart` hook, arriving from a direction no check inside the plugin can
see — a skill that would report the problem ships *inside* the plugin, so in
the one repository that needs it, it is not there to run. **Bootstrapping is
an act performed from outside the repository being bootstrapped.**

## What an install actually is

`claude plugin install --scope project daily-driver@claude-daily-driver` — the
explicitly project-scoped form — splits its state across two places:

| Written into the repository | Written into `~/.claude` |
| --------------------------- | ------------------------ |
| `enabledPlugins` — a pointer | `extraKnownMarketplaces` — the registration |
| | `plugins/cache/claude-daily-driver/daily-driver/<version>/` — the bytes |

Even asked for project scope, the marketplace and the plugin itself land in
user config. The committable half is a pointer at something the machine has to
already have. The two halves fail independently, they are gated differently
(below), and only one of them travels with a `git clone`.

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
checkout, no tooling — a session and this page. It is the only one of the
three that survives that, which is why it is written out in full even though
nobody will use it twice. Like the other two it writes enablement, and
enablement is not the half a cloud environment is missing: see the setup
script below, which is reached from a browser rather than from here.

Whichever route, commit the file.

## What has to be true for it to work

**The trust gate sits on exactly one key, and it is the key that fetches
things.** The two halves of the stanza are not gated alike. Measured one key
at a time, with the same stanza, untrusted and trusted:

| Project-scope key | Untrusted | Trusted |
| ----------------- | --------- | ------- |
| `enabledPlugins` | honoured — all six skills it then carried loaded | honoured |
| `extraKnownMarketplaces` | ignored: `installPluginsForHeadless` logs `no marketplaces declared` | `installed marketplace claude-daily-driver` |

The `enabledPlugins` row was measured with the marketplace already registered
and cached in user config: a pointer is honoured untrusted, and fetching is
not. `~/.claude/settings.json` is read unconditionally, being the user's own
file rather than a cloned repository's.

**Registering the marketplace is — measured — not enough to load the
plugin.** In a *trusted* folder carrying exactly the stanza above, on a
machine with nothing cached, the marketplace was registered and the plugin
cached during that session, and the session still loaded nothing: its `init`
payload reported `plugins: []`, with no `daily-driver:pr` skill. That is the
difference from the untrusted row above, which loaded: there the cache was
already populated when the session started. Running

```sh
claude plugin install daily-driver@claude-daily-driver
```

once flipped the same repository to a payload naming the plugin, with the skill
present. That install lands at **user** scope, so it then applies on the whole
machine, in repositories carrying no stanza at all — which is what makes it a
once-per-machine step rather than a per-repository one.

Everything in this section was measured with headless `claude -p` sessions
against scratch `CLAUDE_CONFIG_DIR`s; the cloud section below is real cloud
sessions. An interactive session may behave differently, and a later release
may make the install a no-op; re-run the third check below rather than
inheriting this conclusion.

**A cloud container is missing the cached half, not the enablement half.**
The cached half is precisely what a stanza cannot supply: a repository can
point at a marketplace, and can neither register nor fetch one. So the stanza alone loads
nothing there, whatever it says; the environment has to install the plugin,
once, before Claude Code starts.

That install lands at user scope, in a `~/.claude` the environment keeps, so
an environment is bootstrapped once rather than once per repository — though
the laptop's measurement below, that a user-scope install loads the plugin in
a repository carrying no stanza at all, was not repeated in the cloud.

## Cloud sessions: the environment's Setup script

A Claude Code cloud container carries `"hasTrustDialogAccepted": false`
permanently. It clones a repository and starts working; no dialog is ever
presented, and there is nothing to accept. So the `extraKnownMarketplaces`
half of the stanza is dead on that surface by the table above, and the
`enabledPlugins` half points at a cache nothing filled.

Nor does the startup installer fill it. Granted a registered marketplace,
`installed_plugins.json` stays `{"version": 2, "plugins": {}}`, and every later
run logs `Plugin "daily-driver" not cached ... run /plugin to refresh` —
`/plugin` being [unavailable in cloud sessions][cloud-docs]. Upstream:
[anthropics/claude-code#88214][88214], and [#78119][78119], [#83422][83422],
[#88248][88248].

[cloud-docs]: https://code.claude.com/docs/en/claude-code-on-the-web
[88214]: https://github.com/anthropics/claude-code/issues/88214
[78119]: https://github.com/anthropics/claude-code/issues/78119
[83422]: https://github.com/anthropics/claude-code/issues/83422
[88248]: https://github.com/anthropics/claude-code/issues/88248

What works is the environment's **Setup script**, which runs before Claude Code
launches and is therefore the only writer that beats the plugin scan:

```bash
#!/bin/bash
claude plugin marketplace add jmcvetta/claude-daily-driver
claude plugin install --yes daily-driver@claude-daily-driver

# Both commands can return 0 while leaving the plugin uncached, so check what
# the loader actually reads.
grep -qF '"daily-driver@claude-daily-driver"' ~/.claude/plugins/installed_plugins.json &&
  compgen -G ~/.claude/plugins/cache/claude-daily-driver/daily-driver/*/.claude-plugin/plugin.json >/dev/null
```

The field is in the environment dialog at claude.ai/code: cloud icon above the
message box, hover the environment, gear. No settings page, no direct URL.

**The verification line is load-bearing.** The failure it exists for returns 0
from both commands above, so nothing else in the script can see it. Tested
isolated: a working install exits 0, a bad marketplace source 2, a
registered-but-never-cached plugin 1.

**No `|| true`**, against the [docs' generic advice][script-requirements],
because the reasoning inverts here. Exiting zero on a failed install snapshots
the failure, and every later session skips the script and starts with no plugin
for the seven days the cache lasts — silently, which is the failure this page
exists to prevent. Exiting non-zero fails the session, builds no snapshot, and
the next attempt re-runs the script, so a transient failure cures itself. A
permanent one fails that environment until someone clears the field from a
browser, which is the right trade here.

[script-requirements]: https://code.claude.com/docs/en/cloud-environments#script-requirements

`~/.claude` persists: confirmed over two consecutive sessions in a fresh cloud
environment, the skills, the agents and the constitution hook present in both,
the second one skipping the setup script entirely and booting from the
filesystem snapshot. #88214's separate claim that the plugin tree rebuilds from
empty each boot did not reproduce.

**Verify anyway, at the top of a cloud session.** The stanza sitting in the
checkout is never evidence that anything took effect, and a setup script that
worked a week ago is evidence only about the snapshot it built. Run the third
check below before relying on the constitution being there.

## The route that would be genuinely per-repository, and is blocked

A plugin tree carrying `.claude-plugin/plugin.json` loads as `<name>@skills-dir`
with no marketplace, no install and no network:

| Location | Scope | Trust required | Measured |
| -------- | ----- | -------------- | -------- |
| `~/.claude/skills/<name>/` | user | **no** | `Status: ✓ loaded`, all six skills |
| `.claude/skills/<name>/` in the repo | project | **yes** | skipped: *"…was skipped because this workspace was not trusted when plugins were scanned"* |

The second row is the only arrangement in which a repository genuinely carries
its own plugin: fully in-repo, offline, surviving a fork, with no environment
configuration anywhere. Workspace trust is the single thing in the way — which
makes it the thing to re-test whenever Claude Code changes how cloud containers
handle trust.

## Checking whether it is actually enabled

The habit worth having: **when a session feels unusually unconstrained, verify
before assuming it is being disobedient.** A session with no plugin is not
ignoring the rules, it does not have them.

Three checks, in increasing order of what they actually prove, and two
readers that are routinely mistaken for one of them:

**Read the file.** Cold-start-proof, works from anywhere, and answers the
question the stanza is responsible for:

```sh
grep -n enabledPlugins .claude/settings.json
```

It proves the file says so, which is all it proves — and the file is the half
that does not fetch anything.

**Ask the CLI what it has on this machine.**

```sh
claude plugin details daily-driver@claude-daily-driver
```

In a repository whose settings name it, on a machine that has already cached
the marketplace — one prior session in a *trusted* repository carrying the
stanza, or the setup script above — this prints the plugin's component
inventory; run anywhere else it says `not found`. Read that as "the names are right and the plugin is
on this machine", not as "it loaded here". Measured: it printed the full
inventory for a session whose `init` payload reported no plugins at all.

**Ask a session what it loaded.** The only one of the three that answers the
question the others are proxies for:

```sh
claude -p "say ok" --output-format stream-json --verbose | python3 -c \
  "import sys,json;[print(d.get('plugins')) for d in map(json.loads,sys.stdin) if d.get('subtype')=='init']"
```

An empty list is the failure, whatever the first two say; a loaded plugin
appears with its name, cache path and version.

**The harness `ListPlugins` tool answers a different question.** In two
separate cloud environments it returned an empty list while the plugin was
live — skills firing, constitution injected. It is not evidence of anything
here, which is why every check above asks the CLI or the session itself.

**`claude plugin list` reads one route only.** It reports
`installed_plugins.json`, so it is honest about a plugin the setup script
installed and says nothing about one arriving by stanza. Measured: in the
trusted stanza-only repository, where the marketplace was registered and the
plugin cached, `list` still said `No plugins installed`. Its `No plugins
installed` is therefore not proof of failure on a laptop — though it is not
proof of success either, and on the version measured the two coincided. On a
cloud container it is worth reading, `installed_plugins.json` being the file
the setup script's verification line greps.

## What none of this covers

A session, in a repository with no stanza, on a machine or in an environment
where nothing is installed, with no laptop in reach. Nothing inside the plugin
can report its own absence, and no command there will have anything to say.
Only the habit above reaches that case at all — which is the argument for the
template and for putting the setup script in the environment before it is
needed, both of whose value is that the question is settled before anyone is in
a position to ask it.

## Measurements

Established against Claude Code 2.1.263 by running the CLI, rather than by
reading the documentation: with a scratch `HOME` and, for the rows about what a
session loads, headless `claude -p` against a scratch `CLAUDE_CONFIG_DIR`.

On 2026-09-06, on the laptop:

| Question | Answer |
| -------- | ------ |
| Marketplace name registered from `jmcvetta/claude-daily-driver` | `claude-daily-driver` |
| Stanza in a **trusted** folder | marketplace registered, plugin cached |
| …and what that session loaded | nothing: `init` reports no plugins, no `daily-driver:pr` |
| …after `claude plugin install` once, same repository | plugin loaded, skill present, scope `user` |
| …and in a repository with no stanza after that install | still loaded — the install is per-machine |
| Stanza in an **untrusted** folder | ignored entirely, silently |
| Stanza in a Claude Code **cloud session** | not loaded; `hasTrustDialogAccepted: false`, nothing cached |
| `claude plugin list` in the stanza-only repository | `No plugins installed` |
| `claude plugin details daily-driver@claude-daily-driver` in that repository | full component inventory, though nothing had loaded |
| The same command outside it | `not found` |

On 2026-09-07, isolating which half of the stanza the trust gate holds, and
then confirmed across two consecutive real cloud sessions:

| Question | Answer |
| -------- | ------ |
| Where `--scope project` writes its state | `enabledPlugins` in the repository; marketplace and cache in `~/.claude` |
| Project `enabledPlugins`, **untrusted**, marketplace already cached | honoured: all six skills loaded |
| Project `extraKnownMarketplaces`, **untrusted** | ignored: `no marketplaces declared` |
| …the same, **trusted** | `installed marketplace claude-daily-driver` |
| Startup installer, marketplace registered, nothing cached | `installed_plugins.json` stays empty; `Plugin "daily-driver" not cached` |
| Setup script installing the plugin before launch | loaded, all components present |
| …and the next session in that environment, script skipped | still loaded — `~/.claude` survives in the snapshot |
| Setup script verification line, isolated | 0 working, 2 bad marketplace source, 1 registered but never cached |
| Plugin tree at `~/.claude/skills/<name>/` | `Status: ✓ loaded` as `<name>@skills-dir`, no marketplace |
| The same tree at `.claude/skills/<name>/`, untrusted | skipped: workspace not trusted when plugins were scanned |
| Harness `ListPlugins` in a cloud session with the plugin live | empty list |

The full record, including the four routes that do not work, is in
[jmcvetta/career#260](https://github.com/jmcvetta/career/issues/260).
