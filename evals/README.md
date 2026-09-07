# Evals

Four suites, run by [`coder_eval`](https://github.com/UiPath/coder_eval) rather
than by `claude plugin eval`. The reasoning for the harness is
[`docs/decisions/0002-eval-harness.md`](../docs/decisions/0002-eval-harness.md);
the short version is that the built-in cannot be run on this account, is
publicly undocumented, announces no changes, and — decisively — ships inside
the `claude` binary, so there is no version to hold back.

```
evals/
├── experiments/with-without.yaml   the ablation every case is measured under
├── tasks/
│   ├── pr/                does `pr` fire when a PR is being opened, and only then?
│   ├── pr-title/          … when a title is being written, and only then?
│   ├── pr-body/           … when a body is being written, and only then?
│   ├── constitution/      does the constitution reach a subagent?
│   └── review-depth/      does `review` dispatch the right panel for the diff?
└── fixtures/review-depth/ shell that builds a reviewable git repository
```

## Running them

```sh
make evals-install    # coder-eval, pinned; uv fetches Python 3.13 itself
make evals-plan       # validate every case. Costs ZERO tokens. Do this first.
make evals-run        # the whole suite, both arms. Costs real money.

make evals-run TASKS='tasks/pr/*.yaml'     # one suite
make evals-run TASKS='tasks/*/0[56]*.yaml' # just the no-fire half
```

Not part of `make check`. The cases need a live model and this repository's CI
is deliberately credential-free. What *is* part of `make check` is
`check-eval-fixtures`, which builds every review-depth fixture repository with
nothing but git — see "The git problem" below for why that leg exists.

**Run `plan` before every `run`.** It is free, and it catches the config errors
that otherwise cost a paid run to discover. `make evals-run` depends on
`evals-plan` for exactly that reason.

Three things the Makefile does that a hand-typed `coder-eval` will not:

- **`cd evals` first.** The plugin path in the experiment is relative and
  resolves against the *process* working directory. Point it at the wrong
  place and the SDK loads nothing, with no error, and every positive row scores
  0 — which reads exactly like a skill that never fires.
- **`-e experiments/with-without.yaml`, always.** A wheel install of
  `coder-eval` resolves its `--experiment` default to the copy packaged inside
  the wheel and never looks in the working directory. Omit `-e` and the tasks
  run as a single unlabelled arm on `coder-eval`'s own stale defaults, and the
  ablation silently is not measured.
- **`TELEMETRY_ENABLED=false`.** See "Two defaults, decided on purpose".

## What the suites are for

The three trigger-accuracy suites exist because `pr`, `pr-title` and `pr-body`
are siblings with overlapping vocabulary — every one of them has "PR" in its
description — so the thing that can actually break is *which* one fires. Each
has two halves, and the second is the one that earns its keep:

- **Fire cases** — four per skill, covering the literal `/pr`, natural
  phrasings, and Claude's own use of `mcp__github__create_pull_request` /
  `mcp__github__update_pull_request`.
- **No-fire cases** — two per skill, drawn from the *adjacent* skills rather
  than from unrelated work. "Fix just the title" asserts that `pr-title` fires
  and `pr` does not; a request to write a commit message asserts that none of
  the three does. A suite that only proved a skill fires would be green with
  all three descriptions collapsed into one.

`constitution/` is not a trigger-accuracy suite: it is the live half of the
constitution's own test, described under "Testing the constitution" in the
repository README. Its credential-free half is
`scripts/check-constitution.py`.

`review-depth/` asks whether `review` sends the *right panel* at the right
diff. Every case is anchored on something a person would notice if routing
broke — a security reviewer that never ran on the file holding the publishing
token, a full panel billed to a two-line typo fix — rather than on a restated
line from `skills/review/SKILL.md`. A suite that restates the spec catches
drift away from the depth table and can never catch the depth table being
wrong.

## Both arms, every criterion

Every criterion is scored under both variants: `bare` (nothing loaded) and
`with-plugin`. That is the point. A fire case's delta is the whole signal — 1
with the plugin, 0 without it, because without it there is no skill to fire —
and a number reported for the treated arm alone has nothing to compare itself
to. In the old format this took an explicit `arm: both` on every grader;
`coder_eval` does it by construction.

`repeats` is **5**, set explicitly, because `coder_eval` defaults it to 1. One
replicate of a non-deterministic agent is an anecdote. Even 3-of-3 — what the
old suites used — supports only a ~[0.37, 1.0] confidence interval on the rate.
Read `per_replicate_scores` in the report rather than the mean.

## How the graders ported

| `claude plugin eval` | here |
| --- | --- |
| `prompt.md` body | `initial_prompt` |
| `case.yaml` + `graders/*.md` | one `tasks/<suite>/<id>.yaml` |
| `runs: 3` | `defaults.repeats: 5` |
| `arm: both` | nothing — both variants are always scored |
| `tool_used` on `Skill` | `skill_triggered` |
| `tool_used` on `Agent` | `command_executed` with `tool_name: Agent` |
| `regex` on `last_message` | **nothing** — see below |
| `max_turns`, `timeout_seconds` | `run_limits.max_turns`, `run_limits.turn_timeout` |

Two entries there disagree with the mapping in `0002` and in issue #37, and the
disagreement is load-bearing:

- **`command_executed` is the generic tool-call criterion**, not a shell-only
  one. It filters on `tool_name` for *any* tool and, off `Bash`, matches
  `command_pattern` against the JSON-serialised tool parameters; Claude Code's
  adapter records one telemetry row per `tool_use` block. So `tool_used` on
  `Agent` — including `input_match`, which becomes `command_pattern` — ported
  after all, and the `constitution` suite lost one grader to redesign rather
  than three. It is also what lets `review-depth` grade **dispatch**: a
  criterion matching `"subagent_type": "security-reviewer"` in an `Agent` call
  is the routing decision itself, not a self-report of it.
- **`regex` on `last_message` genuinely has no equivalent.** Nothing in
  `coder_eval` matches the agent's final message deterministically —
  `file_matches_regex` needs a path and reads file content, and only
  `llm_judge` / `agent_judge` see the final message, as a scored judgment. That
  cost one grader a redesign and one intended check an omission; both are
  recorded below.

`skill_triggered` also improved a detail. The old graders matched the skill
name out of the tool input as a regex, so `pr` had to be written `(:|")pr"` to
avoid matching `pr-title`. `skill_name` is an exact match against the set of
engaged skills, plugin namespace stripped, so that class of near-miss is gone.

Each row carries an `expected_skill`: the ground truth for that row, repeated
on every criterion so the report can build a confusion matrix. `none` is a
legitimate value, and it is what the "neither of these should fire" rows use.

`stop_early` is armed where it is free. On a single-criterion fire case,
`on_pass: stop` ends the run the moment the skill fires. On a no-fire case the
distractor is armed bare (`stop_early: {}`): a misfire has already lost the
row, so there is nothing left to pay for — but the *positive* criterion beside
it is deliberately left unarmed, because a pass-stop there would truncate the
run before a later misfire could be observed, and the row would score green on
a trajectory nobody finished watching.

## The constitution suite: one grader redesigned

`subagent-reports-the-token` was `regex` on `last_message`, weight 2 — the
grader that *is* the finding. It now has the subagent write its answer to a
file, and `file_matches_regex` reads it. That keeps determinism, which is what
a criterion carrying the whole result needs, and it changes what is exercised:
a subagent that knows the token but cannot write now fails a test it used to
pass.

Its negative control survives intact — `command_executed` on `Agent` with
`max_count: 0` and the token as the pattern, asserting the parent did not hand
the token over in the prompt it sent.

One limitation is inherited rather than introduced. The parent holds the
constitution too, so it could write the token itself instead of relaying it.
The prompt forbids it, and no criterion can catch it: subagent tool calls
bubble into the parent's telemetry tagged with `parent_tool_use_id`, and
`command_executed` cannot filter on that, so nothing here tells a parent
`Write` from a subagent `Write`. The `last_message` version had exactly the
same hole — the parent could simply type the token. Closing it needs a token
the parent never sees, which is a change to the hook, not to the case.

## The review-depth suite

Seven cases, each one claim:

| Case | The claim | What a broken routing table would do |
| --- | --- | --- |
| `01-readme-is-planning-not-docs` | `README.md` is planning-class *before* it is docs-only | review a rewritten README for correctness bugs |
| `02-tests-sit-with-code` | a 104-line test-only diff gets the judgment tier | skim a hundred lines of new assertions |
| `03-mixed-diff-falls-through-to-code` | one `src/` path makes the whole branch code | judge a sign-handling fix by a planning rubric |
| `04-planning-class-outranks-size` | 904 lines of prose is still prose | bill a security review to a rollout schedule |
| `05-named-depth-outranks-inference` | a depth the user names wins | overrule a request for a full review with a heuristic |
| `06-sensitive-touch-on-a-tiny-diff` | 11 lines of release workflow still get security | miss the file holding the publishing token |
| `07-neg-opening-a-pr` | opening a PR is not a review | tax every branch and train the skimming reflex |

Every one of them grades `Agent` dispatch. The draft that existed in PR #36 was
dropped for grading the mode line the skill *announces*, which is a self-report:
a skill announcing "Standard" and then dispatching the Full panel would have
passed it.

**The mode line is not checked at all here, and that is a decision.** Keeping it
as a low-weight secondary signal was the plan, and it turns out to need an
`llm_judge` on every row — the final message has no deterministic matcher — which
would put a scored model judgment, and its cost, on seven cases whose whole
point is that they are deterministic. Dispatch is the outcome; the mode line is
the narration of it. If the announced depth is ever worth asserting, the cheap
way in is to have the skill write it somewhere `file_matches_regex` can read,
not to hire a judge.

Two case sizes are load-bearing and should not be "tidied". `02` is over the
~50-line skim threshold on purpose: under it, the case routes to Skim on size
alone no matter which bucket tests land in, and measures nothing. `03` is over
it for the same reason.

### The git problem

`review` needs a real repository — a base branch, a topic branch ahead of it, a
remote to diff against — and `coder_eval`'s sandbox does not build one:
`starter_files` and `template_dir` copy loose files, and `type: repo` clones a
URL onto a checked-out default branch, which is not the shape a branch under
review has. A `tempdir` of loose files makes `review` correctly refuse —
*"there's no branch, no commit history, nothing for the `review` skill to diff
against"* — which is a true negative from a bad case, and indistinguishable in
the report from the finding the suite exists to produce.

**`pre_run` is the seam.** It runs a shell command inside the sandbox after
setup and before the agent, and by default aborts the evaluation on a non-zero
exit, so a fixture that fails to build never reaches a model and never scores a
misleading 0. Each case mounts `fixtures/review-depth/` at `.fixture` via
`template_dir` and runs one script from it. The scripts `git init` the sandbox
root, exclude `.fixture/` through `.git/info/exclude` (a `.gitignore` would show
up as a changed path and shift the diff's *kind*, which is the one thing this
suite measures), commit a base tree, publish it to a bare `origin` under
`.fixture/`, then branch, change, commit and push. The push is not optional:
`review` stops at "Local changes not pushed" when the branch is ahead of its
remote, and would never reach the routing decision under test.

`scripts/check-eval-fixtures.sh` builds all six and asserts that shape. It runs
in `make check` because it needs only git and bash — and because a fixture that
stops building does not turn the suite red, it turns every case into a silent 0.

These cases run in **Local mode**: there is no GitHub MCP in the sandbox, so the
pull-request lookup finds nothing and the skill assembles the diff from git.

## Two defaults, decided on purpose

- **Telemetry is off.** `coder_eval` sends usage telemetry by default to a
  UiPath-controlled Application Insights endpoint, through a connection string
  base64-embedded in the package so that "a fresh install reports usage
  telemetry … with no configuration". It is ingestion-only and documented, and
  the base64 is explicitly not for secrecy. It is still not something a tool
  that may one day gate a merge should do without being asked. `TELEMETRY_ENABLED=false`
  lives in the Makefile so it cannot be forgotten at a prompt; pass it yourself
  if you invoke `coder-eval` directly.
- **The version is pinned**, in `CODER_EVAL_VERSION` in the Makefile.
  Pinnability is the whole reason these suites are not written for
  `claude plugin eval`; leaving the harness to float would give that reason
  away.

Two more defaults are overridden in `experiments/with-without.yaml` rather than
inherited: the agent model (`coder_eval` defaults to the stale
`claude-sonnet-4-6`) and `repeats`.

One to know about and not fix here: `coder_eval` calls
`load_dotenv(override=True)`, so a `.env` file beats your shell environment —
`ANTHROPIC_API_KEY` included. A stale `.env` in the working directory is a
surprising way to run a suite against the wrong account.

## Cost

`run_limits` caps turns and wall clock per task, but nothing caps the bill. The
18 trigger-accuracy cases are cheap: five turns each, `Skill` the only tool,
and the fire half stops the moment the skill fires. `review-depth` is not — each
of its 7 cases dispatches a real reviewer panel over a real diff, twice
(`bare` and `with-plugin`), five times each. Run one suite at a time with
`TASKS=` while iterating, and keep `make evals-plan` between edits, where the
mistakes are free.

## What is not here

CI gating. It was only ever blocked by CI having no credentials, which is a
separate decision from which harness runs the cases — so it is deferred, not
foreclosed.

`claude plugin eval`'s MCP mocking, with `expect:` frontmatter that aborts a run
on a wrong argument, has no equivalent in `coder_eval`. No suite here used it,
so this is a cost deferred rather than paid — but it is the thing to re-examine
if a suite ever needs to assert *"filed the ticket in the wrong project."*
