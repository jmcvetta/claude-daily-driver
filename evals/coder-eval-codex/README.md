# `coder-eval-codex`

A `codex-daily-driver` agent kind for
[`coder_eval`](https://github.com/UiPath/coder_eval), so the suites in
[`evals/tasks/`](../tasks) can be run against
[Codex](https://github.com/openai/codex) as well as Claude Code and Omp. It is a
test instrument, not part of the plugin: nothing here ships to a user, and
nothing here is imported by a skill.

```
coder-eval-codex/
├── pyproject.toml                  the `coder_eval.plugins` entry point
└── src/coder_eval_codex/
    ├── transcript.py               the judge's anchor — pure, and tested
    ├── agent.py                    the built-in agent, subclassed
    └── plugin.py                   register(registry)
```

## Why it exists, and why it is so small

`coder_eval` 0.11.6 already ships a `codex` kind. It drives the Codex SDK, links
a `plugins:` root's skills into `<cwd>/.agents/skills/`, and records command
telemetry in the vocabulary the criteria are written in. This package inherits
all of it. What it adds is one normalisation and one record.

**The judge must find the reply.** Every judge rubric under `evals/tasks/`
locates the reply at the last `[RESULT - …]` tag and scores 0.0 where there is
none — deliberately, so a drifted harness reports nothing rather than something
plausible. `coder_eval` builds that tagged transcript for its Claude Code agent
only; its Codex agent hands the judge `result_text`, the turn's assistant
deltas joined and nothing else. `transcript.render_agent_output` emits the
tagged shape, so one rubric reads the same on all three harnesses.

**It is registered as a new kind, not as a replacement for `codex`.** The
registry rejects two implementations claiming one kind, so shadowing the
built-in would change what every other `coder_eval` user's `codex` means. The
distinct kind also makes the routing readable: `scripts/check-eval-arms.py` maps
a pinned `agent.type` to the arm tag it must carry.

## The normalisation that is not here

Issue #185 asked for a second one: a mapping of `skill://<name>`, the URL Omp
engages a skill through, so `skill_triggered` could see it. Codex does not use
that spelling, and the criterion already sees the one it does.

The spike in [#181](https://github.com/jmcvetta/claude-daily-driver/issues/181)
measured both halves. Codex has no skill tool: the model is handed a skills
table in a developer message and opens `SKILL.md` with an ordinary shell call,
and a `skill://` mention in a prompt reaches the model as literal text. On the
other side, `coder_eval`'s `skill_triggered` matches `skills/<name>/` in any
string tool parameter — its own docstring names Codex as the agent that branch
was written for. `CodexAgent._setup_skills` links each skill at
`.agents/skills/<name>/`, the Codex SDK types `CommandExecutionThreadItem.command`
as `str`, and `_extract_command_telemetry` puts that string in
`parameters["command"]`. The substring is there to match, with nothing to
rename.

## What it records

`0013`'s rule for the Omp arm holds here too: a red arm and an arm whose plugin
never arrived must not read alike. Two fields land in each run's
`environment_info`, beside the routing keys the built-in already records.

| Field | What it answers |
| --- | --- |
| `codex_skills_linked` | the skills found under `.agents/skills/` after `start()` |
| `codex_transcripts_retagged` | turns whose transcript this package rendered |
| `codex_transcripts_already_tagged` | turns that arrived tagged — should be zero |

`codex_skills_linked` is read from the directory, not from the session. The
Codex app-server exposes no query for the skills it discovered, so unlike the
Omp arm's `omp_skills_loaded` this says what was *offered* rather than what was
taken up.

`codex_transcripts_already_tagged` is a drift alarm. Under the pinned
`CODER_EVAL_VERSION` it is zero on every run. Any other number means the
built-in has started rendering the transcript itself and this package has become
a no-op worth deleting.

## What is tested, and what is not

`transcript.py` imports nothing — not `coder_eval`, not the Codex SDK — and
`scripts/check-codex-agent.py` drives it in `make check`. That leg also asserts
the rendered shape is byte-identical to `coder_eval_omp.rpc.render_agent_output`
for one block, which is what keeps one rubric readable on both harnesses without
either package depending on the other.

`agent.py` cannot be reached without a `coder-eval` install and the Codex SDK,
and CI here has neither. What it holds is the subclass: the two overrides above
and a directory read.

## Installing it

`make evals-install` does it, with `uv tool install --with`, so the kind lands in
the same environment as the pinned `coder-eval`. The Codex SDK comes with it —
this package depends on `coder-eval[codex]`, because the built-in agent imports
`openai_codex` inside `start()` and fails at run time without it. There is
nothing to publish and nothing to release.
