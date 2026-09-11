# Omp routes — issue-deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

`scripts/issue-deps.sh` is invoked through the injected skill-directory path,
which Omp names as a `skill://` URL:

```sh
deps="skill://issue-deps/scripts/issue-deps.sh"
```

**Omp rewrites that URL before the shell sees it.** The Bash tool expands every
internal URL in the command string to a shell-escaped absolute path, so the
assignment above reaches `bash` as `deps='/abs/path/to/issue-deps.sh'`. This is
verified from the Omp source rather than assumed: `tools/bash.ts` calls
`expandInternalUrls()` on the command before it runs, and
`tools/bash-skill-urls.ts` does the substitution. The quotes are part of the
token Omp replaces, so the single- and double-quoted forms both work.

**The skill name is the bare directory name, even inside a plugin.** Omp
registers this skill as `issue-deps`, not `daily-driver:issue-deps`: its
Claude-plugin loader deliberately does not prefix skill names, because a colon
is ambiguous in a `skill://` URL.

Two properties of the rewrite decide how this file is used.

**An unresolvable URL is left alone, silently.** Omp does not fail the command
when a `skill://` URL names an unknown skill or a missing file — it leaves the
literal text in place and runs it. The literal `skill://…` then reaches the
shell as an ordinary word. So **check that the path resolves before relying on
it**, with `test -x "$deps"`. Where the test fails, the script is unreachable
and the operation is unavailable — say so. Never fall back to a relative
`scripts/issue-deps.sh`, which is the trap `SKILL.md` describes: in a project
with its own `scripts/` it runs an unrelated file rather than failing.

**The URL must be its own token.** Omp skips a bare `skill://` URL that sits
inside a larger shell quote, so it stays literal in `bash -c "… skill://… …"`
and in any string built around it. Write the assignment above as its own
statement, and use `"$deps"` everywhere after it.

An unreachable script leaves `SKILL.md`'s probe with its third branch, the
GitHub MCP alone — the probe reached the script branch precisely because `gh`
was absent or too old, so there is no client above it to fall back to. That
branch reads counts and writes nothing, which is what to report.
