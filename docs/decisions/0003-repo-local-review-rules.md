# Repo-local review rules live in the repository's own `CLAUDE.md`

**Status:** decided, 2026-09-07.
**Resolves:** [#53](https://github.com/jmcvetta/claude-daily-driver/issues/53).

Two review rules shipped in the global layer that describe two of the author's
Terraform repositories and nothing else: never flag `yor_*` / `git_*` tags in
Terraform resources as stale, and require a reason on every `checkov:skip`.
Both are correct, and both are genuinely unlearnable — a general-purpose
reviewer cannot infer either, which is why
[`0001`](0001-built-in-review-surface.md) put them out of scope for its
measurement rather than expecting a built-in to reproduce them.

Correctness was never the question. Placement was. The plugin loads on every
surface and in every repository; these two rules are meaningful in perhaps two
of them, and everywhere else they are context spent on Terraform conventions
for a repository with no Terraform. That is subsidiarity read backwards: a rule
belonging to one repository had come to sit in the layer that reaches all of
them.

## Decided

**The rules move to project memory** — `CLAUDE.md` in the repositories they
actually describe. They are removed here:

- `agents/security-reviewer.md` carried the Yor rule inline, so it shipped on
  every surface whether or not `review` ever returns from the attic. This is
  the live half of the change.
- `attic/skills/review/references/review-guidelines.md` carried both. Nothing
  under `attic/` is loaded, so this costs no context today — but the attic
  exists so that a `git mv` brings a skill back, and a rule left there is a
  rule that comes back with it.

**The plugin carries no mechanism for repo-local review rules.** `CLAUDE.md`
is already read on every surface, is already the level subsidiarity names, and
already reaches a reviewer subagent. A conventional path of our own — some
`.claude/review-rules.md` a reviewer is told to look for — would be a second
memory layer with the same job as the first, and the reviewer would have to be
told about it in the global layer, spending in every session exactly what this
decision set out to stop spending. YAGNI settles it, and the `judgement-call`
gate is why it is settled here rather than asked.

Nothing enforces the boundary but the author, in the same way nothing enforces
the GoDoc rule. The tempting guard is a blocklist of Terraform vocabulary in
CI, and it is declined: it would fail the day a legitimate mention landed, and
it teaches a future reader the wrong rule — the test is not *which words*, it
is *how many repositories does this describe*.

## The text to paste

Removal is not deletion; the rules are needed where they apply. Paste into the
`CLAUDE.md` of a repository that uses Yor, Checkov, or both:

```markdown
## Review

- **Yor tags are not stale.** Never flag `yor_*` or `git_*` tags in Terraform
  resources as outdated or needing update. Yor rewrites them during the
  release process; the hardcoded values are expected and correct.
- **Checkov suppressions carry a reason.** Every `checkov:skip` comment must
  state why the check is suppressed.
```

## What would change this

A third repository needing the same rules is not enough — it is a third paste.
What would reopen it is repo-local review rules that cannot be written as prose
in `CLAUDE.md`: rules a reviewer must *execute* rather than read, or a set large
enough that loading it unconditionally is the cost `CLAUDE.md` avoids. Neither
exists today.
