# The GitHub MCP server: configuration, and the toolset measurement

**Status**: the setup half of [Q6][plan] is done and recorded here. The
narrowing half is a measurement in flight — it has a start date, an
instrument, and a place for its answer, and nothing else. See the
[Decision](#decision-pending) section for what is deliberately still blank.

[plan]: planning/plugin-replaces-global-memory.md

## Which server

**Local, not hosted** — `github/github-mcp-server` run as a subprocess.

The hosted server exists, is generally available, and was the more attractive
option on paper: no binary to build, no PAT to store, per-toolset URLs
(`…/mcp/x/actions`) instead of a flag. The question that had to be settled
first was whether it requires a Copilot seat, since that subscription is
cancelled.

**It does not.** The endpoint is `https://api.githubcopilot.com/mcp/` and the
hostname is misleading: it authenticates with a PAT or with OAuth, the
org-level MCP policy that gates it applies only to Copilot Business and
Enterprise seats, and the editor-preview policy that once gated OAuth access
stopped applying at general availability. What a Copilot licence buys is
individual *tools* that front Copilot features — `create_pull_request_with_copilot`,
the Copilot Spaces toolset — and those are precisely the tools this workflow
has no use for.

That answer is documentary, not measured, and the distinction is worth
keeping. It could not be probed from a Claude Code web worker: the egress
proxy refuses `api.githubcopilot.com` outright (`CONNECT tunnel failed,
response 403`), and the worker's `GITHUB_TOKEN` is proxy-issued rather than a
real GitHub credential, so a probe would have measured the proxy and told us
nothing about the seat. The first laptop connection settles it for real.

Local wins anyway, for reasons that survive the answer:

- It is certainly free of the question, now and after whatever GitHub does to
  the hosted server's pricing next.
- The measurement below wants one process whose tool list is a function of one
  flag. Per-toolset URLs are a nicer interface and a worse experiment.
- Nothing here is on a laptop that would rather not run a 30MB Go binary.

## Configuration

Install the server — Docker, a release binary, or from source:

```sh
go install github.com/github/github-mcp-server/cmd/github-mcp-server@latest
```

Register it with Claude Code at user scope, so every project on the laptop
gets it and no project has to carry an `.mcp.json`:

```sh
claude mcp add --scope user github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token)" \
  -e GITHUB_TOOLSETS=all \
  -- github-mcp-server stdio
```

Two notes on that command line, both of which matter more than they look.

**`$(gh auth token)` is expanded once, by the shell, and the resulting PAT is
written into `~/.claude.json` in plaintext.** That is a real secret in a
real file, and the trade is being made knowingly rather than accidentally. The
alternative — a wrapper script on `PATH` that execs the binary with a token
fetched at start-up — keeps the config file clean and costs a file. Claude
Code does expand `${VAR}` in `.mcp.json`; whether it does so for user-scope
entries is **unverified**, and worth ten minutes before trusting it.

**`GITHUB_TOOLSETS=all` is the measurement, not a preference.** It is the
fortnight's instrumentation and it is meant to be narrowed. What it costs is
the next section.

`gh` stays installed. It is the escape hatch for what the MCP cannot do — `gh
run watch`, log tailing, comment minimisation — and it is a **laptop-only
convenience, never a portable fallback**: re-measured on a web worker on
2026-09-06, `gh` is not installed there at all, while `docker`, `go`,
`GITHUB_TOKEN` and `GH_TOKEN` all are. Anything that must run on both surfaces
has two clients and no others: the MCP, and `curl` against the REST or GraphQL
API with the ambient token.

## What `all` costs, measured

The plan estimated *"~55 tool definitions"*. That was low by sixty percent.

Measured on 2026-09-06 against **v1.12.0** (commit `9205304`, 2026-09-03), by
launching `github-mcp-server stdio` once per toolset and reading its own
`tools/list` — the server's answer, not the README's table, which is generated
separately and can lag:

| Setting | Tools | Definition chars | ≈ tokens |
| ------- | ----: | ---------------: | -------: |
| `all` | 89 | 254,511 | ~64k |
| `default` (i.e. setting nothing) | 44 | 120,975 | ~30k |
| `issues,pull_requests,repos` | 38 | 106,017 | ~27k |

Sizes are the compact JSON of each full tool definition, input schema
included, since that is what context actually pays for. The token column is
the usual four-characters-per-token rule of thumb and should be read as an
order of magnitude, not a number.

Per toolset:

| Toolset | Tools | Chars | | Toolset | Tools | Chars |
| ------- | ----: | ----: |-| ------- | ----: | ----: |
| `repos` | 19 | 40,571 | | `code_security` | 2 | 6,032 |
| `pull_requests` | 10 | 33,423 | | `copilot` | 2 | 5,837 |
| `issues` | 9 | 32,023 | | `secret_protection` | 2 | 5,610 |
| `governance` | 4 | 20,572 | | `copilot_issue_intents` | 1 | 4,030 |
| `projects` | 3 | 14,891 | | `dependabot` | 2 | 3,852 |
| `notifications` | 6 | 14,435 | | `users` | 1 | 3,078 |
| `gists` | 4 | 12,219 | | `git` | 1 | 2,717 |
| `actions` | 4 | 11,993 | | `orgs` | 1 | 2,240 |
| `discussions` | 5 | 11,290 | | `code_quality` | 1 | 1,914 |
| `security_advisories` | 4 | 10,716 | | | | |
| `stargazers` | 3 | 6,884 | | | | |
| `labels` | 3 | 6,582 | | | | |
| `context` | 3 | 6,043 | | | | |

Three things fall out of that table, and each of them is a thing a guess would
have got wrong.

**The saving is concentrated in one decision, not twenty-two.** `repos`,
`pull_requests` and `issues` are 42% of the total between them and are exactly
the three nobody would drop. Everything a narrowing plausibly removes —
`governance`, `projects`, `notifications`, `gists`, `discussions`,
`security_advisories`, `stargazers` — comes to ~91k chars. The lever is real,
worth about half the budget, and it is one lever rather than a dial per
toolset.

**Narrowing to the obvious guess is worth almost nothing over doing nothing.**
`issues,pull_requests,repos` costs 106k against `default`'s 121k: a 12%
saving, for a configuration that has thrown away `actions` and `context` in
exchange. The interesting comparison is not narrow-versus-`default`, it is
either-versus-`all`. This is the strongest argument in the file for
measurement over taste, and it was invisible before the numbers existed.

**The server's `default` is not what the README's toolset table implies.** It
is `context,copilot,issues,pull_requests,repos,users` — 44 tools — and it
includes `get_label`, which the docs file under `labels`. `get_label` is
registered in *both* `issues` and `labels`; it is the only tool in the server
that belongs to two toolsets, and reconstructing a toolset list from an
observed tool name is wrong for exactly that one tool.

## The measurement

Running since **2026-09-06**. Read it no earlier than **2026-09-20**.

```sh
make mcp-usage                                        # everything on the laptop
python3 scripts/github-mcp-usage.py --since 2026-09-06 # just this window
```

[`scripts/github-mcp-usage.py`](../scripts/github-mcp-usage.py) reads Claude
Code's session transcripts, counts `mcp__github__*` calls, rolls them up to
the toolsets that supply them, and prints the `--toolsets` line those calls
justify next to what it saves. The tool-to-toolset table is embedded and
carries its provenance; a tool called but missing from it is reported in its
own section rather than dropped, so the table going stale shows up as output
instead of as a quietly wrong recommendation.

It also counts `gh` invocations by subcommand. That is not a side quest: the
residual `gh` use *is* the list of things the MCP did not do, measured instead
of assumed, and it is the input to the next round of retirements in the plan's
D3. The detector only counts `gh` in command position, which makes it a small
live demonstration of D2's argument — recognising a command inside a shell
string is guesswork, and that guesswork is exactly why the hook that enforces
MCP use matches an MCP tool name instead of a bash regex.

Read the result against three questions, in this order:

1. Is any toolset outside `default` being called? If not, the answer is to set
   nothing at all and delete the flag — a smaller configuration than any
   explicit list, and it tracks the server's own defaults as they change.
2. Is `actions` among them? The plan predicts it will be, because a `pr-ci`
   skill is defined in terms of it, and a toolset list written before that
   skill existed would have omitted it. If the fortnight says otherwise, the
   prediction was wrong and should be recorded as wrong.
3. What did `gh` still do? Each row is either an MCP gap worth reporting
   upstream or a habit worth breaking.

## A measured limit: the server rewrites `@` mentions

Every write path rewrites a literal `@` mention before it reaches GitHub —
issue bodies and issue comments alike, and inside a code span as readily as in
prose. What lands is the name broken up by separator characters, which renders
as text and addresses nobody.

Measured on 2026-09-09 against issue #130: an issue body carrying the
Dependabot rebase command, and then a comment carrying the same command on its
own line, both arrived mangled and were read back from the browser to confirm
it. A code span and an `&#64;` entity were tried and neither survived.

The consequence is a capability a skill cannot assume. **A session using this
server cannot drive a bot that takes commands by mention** — Dependabot's
`rebase`, `recreate` and `merge` among them. Where such a prod is wanted, the
paths left are a workflow posting the comment with the Actions token, or a
person typing it. The `deps` skill met this limit and chose neither, and its
`The superseded pull requests are left alone` section says why.

## Decision (pending)

Nothing is decided yet, and the blank is the point: a toolset chosen before
the workflow exists is the premature decision this whole exercise was written
to avoid.

When the window closes, this section records the list, the counts it rests on,
and — most importantly for the *next* narrowing — which toolsets were kept
despite low call counts, and why. A toolset kept for a reason nobody wrote
down is a toolset that gets re-litigated from scratch every six months.
