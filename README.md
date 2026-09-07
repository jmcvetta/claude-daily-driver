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
| `pr-title` | The title convention: concise, and Conventional Commits with the type the contents actually warrant — which is what release-please reads to decide the next version. |
| `pr-body`  | The body structure: a one-line summary under 85 characters, a salutation in verse, an executive summary, as much engineering detail as fits, and the `Issues` section that closes it. |
| `pr-threads` | The review-thread lifecycle for any reviewer: reply with a verdict, resolve, re-resolve a repeat finding, never leave a thread open silently — plus the comment minimisation the GitHub MCP does not expose. |
| `issue-deps` | Records and reads GitHub issue relationships — blocked-by, sub-issue, and which PR closes what — proposing each edge from evidence and leaving the writing to a confirmation. |
| `review` | Reviews a branch or pull request with a panel of reviewer agents, infers how deep to go from the diff itself, walks the findings through with you, and posts the result in verse. |
| `judgement-call` | The gate before a choice is put to you: where the correct, standard way already answers it, Claude answers it and says which way it went. What survives the gate is intent, a real trade-off, scope, and anything irreversible. |

Three PR skills rather than one because skill names are flat within a plugin,
so siblings can be triggered independently: a decision to rewrite a PR body
fires `pr-body` directly, without routing through `pr` to get there. The cost
is two extra descriptions in context.

Each skill carries its own trigger register: the literal slash command, natural
phrasings — "open a PR" for `pr`, "fix the PR title" for `pr-title`, "rewrite
the PR description" for `pr-body`, "address the review feedback" for
`pr-threads`, "is this ready" for `review`, "this is blocked by #123" for
`issue-deps`, "just decide" for `judgement-call` — and Claude's own tool calls.
The PR skills split `mcp__github__create_pull_request` and
`mcp__github__update_pull_request` between them, `pr-title` on a call that sets
a `title`, `pr-body` on one that sets a `body`, `pr` on a create or on an
update wider than either alone, with `gh pr create` / `gh pr edit` as a
fallback on a harness that still reaches for them; `pr-threads` takes the reply
and resolve tools and `get_review_comments`; `review` takes the moments before
a branch is declared ready, marked non-draft, or sent to a reviewer;
`issue-deps` takes the GitHub MCP's sub-issue and issue-read tools; and
`judgement-call` takes `AskUserQuestion`. Those tool-call registers are the
point: a convention that only fires when a human types a command quietly stops
applying as more of the work runs without one.

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

`judgement-call` is the odd one out: it fires on a question about to be asked
rather than on a repository operation about to run. Its register is
`AskUserQuestion` and the sentences that stand in for it, because the thing it
exists to stop is a menu of one correct option and several hacks, which costs a
round trip to answer with the standard that was never in doubt. It is
deliberately not every offer of next steps — an offer to do *more* is a scope
question, and scope is the user's. The rule it applies is the constitution's
own: correct beats quick, no workarounds. The boundary is the interesting
half — intent, a genuine trade-off, scope and anything irreversible still go to
the user, and no confirmation another skill requires is waived by it.

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
│   ├── pr-body/SKILL.md
│   ├── pr-threads/
│   │   ├── SKILL.md
│   │   └── scripts/        the comment-minimisation path the MCP lacks
│   ├── issue-deps/
│   │   ├── SKILL.md
│   │   └── scripts/        plugin runtime, owned by the skill beside it
│   ├── review/
│   │   ├── SKILL.md
│   │   └── references/     the review guidelines, passed to every agent
│   └── judgement-call/SKILL.md
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
- **`claude plugin eval evals/`** runs the live half, which is the R2
  experiment itself: a subagent is asked for a token nobody put in its prompt.
  Only a real session can prove the harness honours `updatedInput`, and a
  credentialed run is the price of asking.

They fail for different reasons and deserve to fail separately: the first
tests this plugin, the second tests an assumption about the harness that a
future release could withdraw without telling anyone.
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
