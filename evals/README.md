# Evals

Six suites, run by [`coder_eval`](https://github.com/UiPath/coder_eval) rather
than by `claude plugin eval`. The reasoning for the harness is
[`docs/decisions/0002-eval-harness.md`](../docs/decisions/0002-eval-harness.md);
the short version is that the built-in cannot be run on this account, is
publicly undocumented, announces no changes, and — decisively — ships inside
the `claude` binary, so there is no version to hold back.

```
evals/
├── experiments/with-without.yaml   the ablation every case is measured under
├── tasks/
│   ├── pr/              does `pr` fire when a PR is opened, and only then?
│   ├── pr-title/        … when a title is written, and only then?
│   ├── pr-body/         … when a body is written, and only then?
│   ├── undertake/       … when work is undertaken, and only when invoked?
│   ├── constitution/    does the constitution reach a subagent?
│   └── review-depth/    does `review` send the right panel at the diff?
└── fixtures/review-depth/
    ├── shared/          builds the git repository every case starts from
    └── cases/<name>/    one `case.sh`, mounted alone beside `shared/`
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

`undertake/` is a trigger-accuracy suite of a different shape: two cases over
one request, differing only in whether the skill was invoked. Step 0 opens an
issue for work that has none, which removes the issue reference as the thing
that distinguishes an undertaking from ordinary work and leaves the invocation
carrying that weight alone. The pair is what asserts it carries it — the fire
case and the no-fire case describe the same retry loop, so a description that
drifts in either direction fails one of them. Its numbering leaves a gap at
02–04: the `0[56]` in the no-fire glob above is the convention, so a no-fire
case is numbered into that range rather than after the case before it.

`constitution/` is not a trigger-accuracy suite: it is the live half of the
constitution's own test, described under "Testing the constitution" in the
repository README. Its credential-free half is
`scripts/check-constitution.py`.

`review-depth/` asks whether `review` sends the *right panel* at the right
diff. Every case is anchored on something a person would notice if routing
broke — a security reviewer that never ran on the file holding the publishing
token, a rewritten README judged for correctness bugs, a full panel billed to
every pull request opened — rather than on a restated line from
`skills/review/SKILL.md`. A suite that restates the spec catches
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
| `tool_used` on `Agent`, by `subagent_type` | **nothing** — see below |
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
  than three. Its limit is length, not tool kind: the haystack is truncated to
  2000 characters, which is why it can assert *that* a subagent ran and cannot
  assert *which* — see "Grading dispatch" below.
- **`regex` on `last_message` genuinely has no equivalent.** Nothing in
  `coder_eval` matches the agent's final message deterministically —
  `file_matches_regex` needs a path and reads file content, and only
  `llm_judge` / `agent_judge` see the final message, as a scored judgment. That
  cost one grader a redesign and one intended check an omission; both are
  recorded below.

One hazard `skill_triggered` carries, which the criterion's name hides: besides
the `Skill` tool call, it scans **every string parameter of every tool** for the
substring `skills/<name>/`, so a `Read` of
`skills/review/references/review-guidelines.md` counts as engaging `review`.
That is deliberate — it is how the criterion scores agents with no `Skill` tool
— but it means a row that grants file tools and expects a skill *not* to fire is
only as sound as the paths that row can plausibly touch. `allowed_tools` is not
the mitigation: it is a permission allowlist, the model
is still offered `Read`, and telemetry records a `tool_use` block when it is
generated — before any result — so a *denied* read of `skills/pr/SKILL.md`,
which is what a model weighing two sibling skills reaches for, still scores as
engaging `pr`. The trigger rows therefore carry an explicit `disallowed_tools`,
which is the field that actually removes a tool. `review-depth`'s no-fire row
needs file tools and keeps them, and relies instead on the `pr` skill having no
reason to name a path under `skills/review/` — which it does not — with the
empty-roster criterion beside it as the check that does not depend on paths at
all.

`skill_triggered` also improved a detail. The old graders matched the skill
name out of the tool input as a regex, so `pr` had to be written `(:|")pr"` to
avoid matching `pr-title`. `skill_name` is an exact match against the set of
engaged skills, plugin namespace stripped, so that class of near-miss is gone.

Each `skill_triggered` row carries an `expected_skill`: the ground truth for
that row, repeated on every criterion of that type. (`review-depth` 01–06 have
none — they are graded entirely on the dispatch roster.) What it does today is
set the polarity — a criterion passes
when the skill's engagement matches whether `expected_skill` names it — and
`none` is a legitimate value, which is what the "neither of these should fire"
rows use.

It is *also* the input to `coder_eval`'s per-suite classification rollup
(accuracy, recall, F1, a confusion matrix), and that rollup does **not** run
here: it is computed only for tasks carrying a `suite_id`, which is set in
exactly one place — the `dataset:` expander. Getting it would mean collapsing
each suite's six files into one dataset-fanned task, trading six readable cases
for one table. Worth doing when the per-skill numbers are what someone is
actually reading; not worth doing to make a sentence in this file true.

`stop_early` is armed where it is free. On a single-criterion fire case,
`on_pass: stop` ends the run the moment the skill fires. On a no-fire case the
distractor is armed bare (`stop_early: {}`) — a misfire has already lost the
row, so there is nothing left to pay for — **and so is the positive criterion
beside it**, which is the part that is easy to get backwards.

On the trigger suites this is free. On `review-depth`'s no-fire row it is not,
and that row says so: the fail-stop is deferred while the pass-capable `pr`
criterion is undecided, so on the very trajectory the row exists to catch —
`review` fires, `pr` never does — nothing decides it, the stop never comes, and
the run pays for a full reviewer panel up to its turn cap. Recall is worth that
there; `max_turns` is what bounds the bill.

Arming the positive cannot truncate anything: a bare `stop_early: {}` leaves
`on_pass` at its default `continue`. What it does is put the criterion in the
watcher's *pass-capable* set, and a fail-stop is deferred while any pass-capable
armed criterion is still undecided. Leave the positive unarmed and the watcher
cannot see it: the first distractor misfire ends the run, the positive is then
scored on a trajectory that stopped before the right skill could fire, and the
row records a false negative a full run would never have produced.

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

### Grading dispatch

Every one of them grades which agents were dispatched. The draft in PR #36 was
dropped for grading the mode line the skill *announces*, which is a self-report:
a skill announcing "Standard" and then dispatching the Full panel would have
passed it.

**No criterion in `coder_eval` 0.11.6 can be relied on to see `subagent_type`.**
`command_executed` matches against `json.dumps(parameters)` truncated to 2000
characters, so whether the field is inside the window depends on how long the
prompt is and on where the key lands in the serialisation — neither of which the
eval controls. When it falls outside, the criterion reports "not dispatched" for
a dispatch that happened: it silently zeroes a positive and *inverts* a negative
control, and both failures read exactly like a router that dispatched nothing.
`llm_judge` and `agent_judge` are no help either: their tool-call summariser
renders an `Agent` call as its `description`, a three-word label the model
writes.

**Measured, so the size of the risk is on the page rather than assumed.** Three
live `review` dispatches (CLI 2.1.263, `coder_eval` 0.11.6, `claude-opus-5`,
2026-09-07 — the three-agent panel over a 1,397-line diff) serialised to 1,437 /
1,382 / 1,387 characters with `subagent_type` as the **first** key, comfortably
inside the window: `review` hands its agents a summary and a file list, not the
diff. So the truncation does not bite this skill today, and an earlier reading of
this section — that key order is fixed at `description, prompt, subagent_type`
and the prompt therefore pushes the field past the window on *every* dispatch of
consequence — was wrong.

The hook below stays regardless, and the measurement is why it is worth its
weight rather than why it is unnecessary: argument order is the model's to
choose call by call, prompt length is the skill's to change without telling
anyone, and the failure mode is silent in the direction that looks like a
result.

So the observation is taken with a `PreToolUse` hook matching `^(Agent|Task)$`
— both names, because the harness has used both — wired through
each task's `claude_settings` and recorded by
`fixtures/review-depth/shared/record-dispatch.py`. It appends one
`subagent_type` per
line to `.fixture/dispatched.txt`, which `file_matches_regex` reads.

The hook is part of the **instrument**, not of the plugin under test: it is
configured by the eval, it fires identically in both arms, it reads the tool
input verbatim, and it emits nothing — so it cannot veto a dispatch or disagree
with the plugin's own `PreToolUse` hook on the same event. And it is still not
the mode line: the mode line is what the skill says it decided; the roster is
the argument it passed to the tool.

The roster is created empty by the fixture, so a `must_match: false` criterion
reads "nothing was dispatched" instead of erroring on a missing file — which is
the entire `bare` arm.

**What it proves, exactly.** `PreToolUse` fires before the tool resolves
`subagent_type`, so a roster line is a dispatch *requested*, not a subagent
confirmed to have run. A `review` that asks for `security-reviewer` under a name
the session cannot resolve records the line anyway. That is the routing decision
— which is what these cases grade — but it is not proof the reviewer ran, and no
criterion here claims otherwise. The old `command_executed`-on-`Agent` shape had
the same property, for the same reason.

**Two things the hook must never do**, both guarded rather than asserted in
prose. A `PreToolUse` hook that exits non-zero *blocks* the tool call, so a
recorder that failed would not merely lose the roster — it would veto every
dispatch, in both arms, and report a routing table that dispatched nobody. The
hook command is therefore absolute (via `$CLAUDE_PROJECT_DIR`, which Claude Code
puts in every hook's environment) and ends in `|| true`. And because `|| true`
would then hide a genuinely broken recorder behind an empty roster,
`scripts/check-eval-fixtures.sh` runs the recorder against the copy the sandbox
would get and fails `make check` if it does not record.

The hook also writes nothing to stdout, so it cannot contest the `updatedInput`
returned by the plugin's own `PreToolUse` hook on the same event.

### What the sandbox can see

The fixtures are mounted at `.fixture/` inside the sandbox and the agent under
test has `Read`, `Grep`, `Glob` and `Bash`, so anything there saying what a case
expects is an answer key one `cat` away. Three things follow, and they are
enforced rather than asked for:

- **The fixtures carry mechanics, not claims.** The reasoning lives here and in
  the task YAML. `evals/fixtures/review-depth/` is prose about `git`.
- **A task mounts the shared scaffolding plus its own case, and nothing else** —
  two `template_dir` sources at the same `mount_point`. The case script is
  `case.sh` in every case, because its *filename* is copied into the sandbox too
  and `sensitive-tiny.sh` names the routing rule being graded as loudly as any
  comment would.
- **No fixture file contains the substring `skills/`.**
  `scripts/check-eval-fixtures.sh` greps for it, because `skill_triggered`
  counts such a path in any tool parameter as engaging that skill — so a fixture
  carrying one would score as a skill firing the moment the agent read the file.
  (The check found its first offender immediately: a comment explaining the
  rule.)

**None of this is a boundary, and it should not be described as one.** The suite
runs on the default `driver: tempdir`, where `coder_eval`'s own note is that
"the agent under evaluation runs with the same filesystem view as the harness" —
its anti-cheat permission window is a documented no-op outside a container. So a
session with `Bash` can read this file, read the task YAML, and write to
`.fixture/dispatched.txt` directly. What the rules above buy is that nothing
*puts* the answer in front of a session going about its work; they buy nothing
at all against one that goes looking. `sandbox: {driver: docker}` is what would
make it a boundary, and moving the roster outside the sandbox needs the same
upstream fix as everything else here.

The upstream fixes that would retire this: make the truncation bound
configurable, or render `subagent_type` in the judge's tool-call summary.

**The mode line is not checked at all here, and that is a decision.** Keeping it
as a low-weight secondary signal was the plan, and it needs an `llm_judge` on
every row — the final message has no deterministic matcher — which would put a
scored model judgment, and its cost, on seven cases whose whole point is that
they are deterministic. Dispatch is the outcome; the mode line is the narration
of it, and the narration is what PR #36's draft was dropped for grading. If the
announced depth is ever worth asserting on its own, the way in is the roster's:
observe it where it is complete, not through a judge.

**Every case size is load-bearing and none should be "tidied".** The depth table
turns on ~50 and ~800 changed lines, so a case that drifts across a threshold
does not fail — it re-routes, and then measures a depth it was not written for.
`01`, `02` and `03` are over ~50 on purpose (under it they route to Skim on size
alone, whatever bucket their paths land in); `04` is over ~800; `05` and `06`
are deliberately under ~50, because "tiny and still reviewed" is the whole
claim. `scripts/check-eval-fixtures.sh` holds those bounds and fails on drift.

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
misleading 0. Each case mounts `fixtures/review-depth/shared/` and its own
`fixtures/review-depth/cases/<name>/` at `.fixture` — two `template_dir`
sources, one mount point, for the reason in "What the sandbox can see" — and
runs `.fixture/case.sh`. The scripts `git init` the sandbox
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

`plan` warns on every task here that `task_timeout` exceeds `turn_timeout`.
That is deliberate and the tasks say so: `turn_timeout` is the agent's budget,
`task_timeout` is a watchdog armed before the turn and still running while the
criteria are checked, so equal values mean a turn that uses its budget is killed
as a TIMEOUT before it can be graded. The headroom is the difference.

`run_limits` caps turns and wall clock per task, but nothing caps the bill. The
18 trigger-accuracy cases are cheap: five turns each, `Skill` the only tool,
and the fire half stops the moment the skill fires. `review-depth` is not: its six fire
cases each dispatch a real reviewer panel over a real diff, five times, in the
`with-plugin` arm. The `bare` arm is cheaper but not free: it has no `review`
skill and none of the plugin's reviewer agents, but it keeps the `Agent` tool
and thirty turns, so a session that decides to review the diff by hand can
still spend. Its no-fire case pays for a panel too, on exactly the trajectory
it is trying to catch. Run one suite at a time with
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
