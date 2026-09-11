# The judge needs its own transport

**Status:** decided, 2026-09-11.
**Provenance:** found while running
[#158](https://github.com/jmcvetta/claude-daily-driver/issues/158)'s nine
`references` rows — the run the issue asked for surfaced a defect the issue
did not anticipate.
**Resolves:** the `llm_judge` half of
[#158](https://github.com/jmcvetta/claude-daily-driver/issues/158#issuecomment-5634289151)'s
first finding.

`coder_eval`'s `llm_judge` criterion needs a transport to a judge model, and
that transport is separate from whatever authenticates the agent under test.
On the default DIRECT backend,
`models/routing.py::_resolve_direct_judge_transport` picks `"anthropic"` iff
`ANTHROPIC_API_KEY` is set, and `None` otherwise. `criteria/llm_judge.py` does
not fail the run when it gets `None` — it returns score 0.0 with
`details="(judge transport unconfigured)"`, logs one `ERROR` line, and the run
**continues**. Only the DIRECT backend can be unconfigured this way; BEDROCK
and LITELLM always carry a usable transport.

Running `tasks/session-title/01-get-session-before-set.yaml` with no
`ANTHROPIC_API_KEY` set made this concrete. `experiment.md` reported `Score
0.000 (bare) / 0.333 (with-plugin)`, `Best: with-plugin`, `Win Rates —
with-plugin: 1/1 tasks (100%)`. That reads as a clean ablation. The row's
entire 0.333 was the weight-1 `skill_triggered` criterion; the weight-2
`llm_judge` — the criterion actually carrying the row's finding — never ran.
Nothing in the report says so. The per-replicate log does
(`API routing: anthropic_direct (judge transport: none)`, then the `ERROR`
line), and `task.json` records `environment_info["judge_transport"]`, but
neither reaches `experiment.md`, which is the file anyone actually reads.
Eight of the nine `references`-tagged rows carry their finding in a weight-2
`llm_judge`, so this one missing key silently voids most of that suite.

## Decided

**A pre-run guard, `scripts/evals-preflight.py`, not a `make check` leg.**
`make evals-run` now depends on it: it reads every task file `$(TASKS)`
would pass to `coder-eval`, and where an enabled `llm_judge` criterion exists
and the resolution rule above says its transport would be unconfigured, it
exits 1 before a model is called — naming the offending rows and the same two
remedies (`ANTHROPIC_API_KEY`, or `--backend bedrock`) `llm_judge` itself
would give if it were allowed to fail instead of scoring 0.0.

**Why before the run rather than after.** The alternative — read the report
more carefully, or grep `task.json` for `judge_transport` — is exactly what
already failed here: the information is in the run's own output and a reader
still missed it, because a 0.333 with a `Best:` line does not look like
something to double-check. A guard ahead of the run saves the run's own cost:
every replicate of every row in an unconfigured `llm_judge` run gets paid for
and produces a number nobody can trust.

**The guard duplicates a rule that lives upstream, and that is a real cost,
not a free one.** `_resolve_direct_judge_transport` is `coder_eval`'s call to
make, and this repository pins `CODER_EVAL_VERSION` specifically so it does
not move without being asked (`docs/notes/0002-eval-harness.md`). A future
pin bump could change the rule out from under this guard without either
Makefile target saying so. `scripts/check-evals-preflight.py` exists for
exactly this: it is the thing that would need updating — and would visibly
fail if it were not — the day `coder_eval`'s own resolution rule changes.

## What it deliberately does not do

**Does not patch or call into `coder_eval`.** It mirrors the resolution rule
in a small, independent script rather than importing `coder_eval` (a
`uv tool install`, not a dependency of this repository) to ask it directly.

**Does not catch every way the transport could fail.** Only the
"unconfigured" case — a present-but-wrong key, an expired one, a network
error, all fail the same way any other API error does, mid-run, and this
guard has nothing to say about them. It exists for the one failure mode that
is silent by design upstream.

**Does not fully resolve where `coder_eval` would read a `.env` from.**
`coder_eval` calls `load_dotenv(override=True)` at import, which — established
empirically, not assumed, by instrumenting `dotenv.main._walk_to_root` against
the real `coder-eval` entry point — searches upward from the *installed*
`coder_eval` package's own directory, not from the process's working
directory. Where that lands depends on how `coder-eval` happens to be
installed on a given machine, which this script cannot know in general. What
it does check is the mechanism that actually decides `ANTHROPIC_API_KEY`
regardless: `config.py` separately reads a cwd-relative `.env` for that one
key and force-overrides it, the same way `Settings.model_config`'s own
`env_file=".env"` would, and `evals-run` always runs both `coder-eval` and
this guard from `evals/`. The gap is real and is documented in the script's
own `WHAT IT DOES NOT CATCH`, not papered over.

**Not part of `make check`.** Like `evals-plan` and `evals-run` themselves, it
needs task YAML in hand to mean anything; `check-evals-preflight` — the
acceptance test for the guard itself, run against synthetic fixtures — is
the leg that is.
