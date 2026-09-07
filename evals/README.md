# Trigger-accuracy evals

One `claude plugin eval` suite per skill, under a directory named for it:

```
evals/
├── pr/           does `pr` fire when a PR is being opened, and only then?
├── pr-title/     … when a title is being written, and only then?
├── pr-body/      … when a body is being written, and only then?
└── implement/    … when an issue is being taken on, and only then?
```

`evals/constitution-reaches-subagent/` sits beside them and is not a
trigger-accuracy suite: it is the live half of the constitution's own test,
described under "Testing the constitution" in the repository README. It runs
under the same commands.

The three PR skills are siblings with overlapping vocabulary — every one of
them has "PR" in its description — so the thing that can actually break is
*which* one fires. Each suite therefore has two halves, and the second is the
one that earns its keep:

- **Fire cases** (`tags: [<skill>, fire]`) — four per skill, covering the
  literal `/pr`, natural phrasings, and Claude's own use of
  `mcp__github__create_pull_request` / `mcp__github__update_pull_request`.
- **No-fire cases** (`tags: [<skill>, no-fire]`) — two per skill, drawn from
  the *adjacent* skills rather than from unrelated work. "Fix just the title"
  asserts that `pr-title` fires and `pr` does not; a request to write a commit
  message asserts that neither does. A suite that only proved a skill fires
  would be green with all three descriptions collapsed into one.

`implement/` has the same two halves and one more no-fire case, because its
confusable neighbour is not a sibling skill but a *mood*: an issue number in
the prompt reads the same whether the issue is being taken on or merely asked
about. "What does #191 say", "summarise #191" and "is #191 still relevant" are
questions, and a skill that cuts a branch on any of them is worse than no
skill.

Graders are all `tool_used` on the `Skill` tool, matched against the skill name
in the tool input: deterministic, no LLM judge, no cost beyond the runs.

They carry `arm: both` deliberately. Left at its default a `tool_used: Skill`
grader is a with-only *indicator* — displayed, not scored — which is right for
a suite measuring the quality of a skill's output and wrong for one measuring
whether it fires at all. Scored in both arms, a fire case's Δ is the whole
signal: 1 with the plugin, 0 without it, because without it there is no skill
to fire.

## Running them

Not part of `make check`. The cases need a live model, and this repository's CI
is deliberately credential-free.

```sh
claude plugin eval . --ablation with-without          # everything
claude plugin eval . --tag pr-body                    # one skill's suite
claude plugin eval . --case '*neg*' --runs 1          # just the no-fire half
```

`claude plugin eval` is in early access; the command reports as much where the
account does not have it.
