# The judge runs on the subscription

**Status:** decided, 2026-09-11.
**Provenance:** found while running
[#158](https://github.com/jmcvetta/claude-daily-driver/issues/158)'s nine
`references` rows, on the second attempt at that run.
**Supersedes:** the premise of
[`0012`](0012-the-judge-needs-its-own-transport.md), not its decision. The
pre-run guard `0012` added is still right and still runs. What changed is that
no row in this repository trips it any more, because no row uses `llm_judge`.

`0012` treated a missing `ANTHROPIC_API_KEY` as a configuration gap — something
an operator sets before a run. It is not. This project's only Claude access is
a Max subscription, and it will not acquire a metered API key. `llm_judge`
calls the Anthropic API directly, so on the DIRECT backend it needs that key by
construction, and the two remedies `0012` names are both out of reach:
`ANTHROPIC_API_KEY` is metered, and `API_BACKEND=bedrock` wants
`AWS_BEARER_TOKEN_BEDROCK` and `AWS_REGION`, which is a Bedrock API key and
metered too.

Eight of the nine `references` rows carried their finding in a weight-2
`llm_judge`. Written that way, those findings could never execute here. That is
not a run waiting on credentials; it is a criterion chosen wrongly.

## Decided

**Every judge in this suite is `agent_judge`, never `llm_judge`.**

`coder_eval`'s `agent_judge` spawns a Claude Code SDK agent as the judge
instead of calling the API. It builds that agent through the same
`ClaudeCodeAgent` and the same route as the agent under test
(`evaluation/sub_agent.py:193`), and the DIRECT branch of the environment
builder (`agents/claude_code_agent.py:817`) leaves `ANTHROPIC_API_KEY` alone
and lets the SDK inherit the environment. So the judge authenticates exactly
the way the agent under test already does, which on this project is the
subscription.

`AgentJudgeCriterion` mirrors `LLMJudgeCriterion`'s prompt and context fields —
`prompt`, `include_agent_output`, `include_reference`, `weight` are all shared
— so the eight findings ported across unchanged. Only the `type` line and a new
`agent` block differ.

### Two settings in that block, both load-bearing

**`allowed_tools: []`.** These rows grade a reply, and
`include_agent_output: true` pre-attaches the whole transcript to the judge's
prompt. There is nothing for the judge to go and look at, so it is given
nothing to look with. That is also the narrowest available answer to the
prompt-injection surface `AgentJudgeCriterion`'s own docstring warns about: the
transcript being graded is untrusted text, and the criterion's default tool
surface is `[Bash, Read, Glob, Grep]`. The `submit_verdict` MCP tool is
force-added by the criterion itself and is unaffected by the empty list.

**`permission_mode: default`.** `AgentJudgeCriterion` defaults to
`bypassPermissions`, which the CLI refuses outright when it runs as root:

```
agent_judge: sub-agent crashed: CLI process failed (exit code 1):
--dangerously-skip-permissions cannot be used with root/sudo privileges
for security reasons
```

A container runs as root, so the default makes the judge unusable in half the
places this suite runs. Nothing here needs it, because the tool surface is
empty.

## Why this is better than the criterion it replaces

`agent_judge` fails **loudly**. The crash above scored 0.0 with
`AgentCrashError: CLI process failed …` in the report. That is the whole
defect `0012` was written about, inverted: `llm_judge` with no transport
returns 0.0 with `details="(judge transport unconfigured)"` and lets the run
continue, and nothing in `experiment.md` says the criterion never executed.
A judge that cannot run should say so where the reader looks, and this one
does.

## What is kept

`scripts/evals-preflight.py` stays, and `make evals-run` still depends on it.
It reports `no enabled llm_judge criteria` on this suite today, which is the
answer it should give. It is a guard against the criterion coming back — by a
row copied from upstream's examples, or written from memory — not a guard
against a missing key.

## What this does not claim

Nothing here says `agent_judge` grades *as well as* `llm_judge` would. It is a
different instrument: a full agent turn rather than a single completion, with
its own system prompt and its own verdict channel. The rows' rubrics were
written for a one-shot judge and were not retuned. Whether any of them needs
retuning is a question the scores answer, not this note.
