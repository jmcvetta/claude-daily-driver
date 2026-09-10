# Omp routes — issue-deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

`scripts/issue-deps.sh` is invoked through the injected skill-directory path,
which Omp names as a `skill://` URL:

```sh
deps="skill://issue-deps/scripts/issue-deps.sh"
```

**Check that the path resolves before relying on it**, with `test -x "$deps"`.
A `skill://` URL is not a shell expansion the way `${CLAUDE_PLUGIN_ROOT}` is:
the shell knows the scheme only if Omp rewrites it inside a Bash command
string, and that this runtime does so is **not verified here**. Where the test
fails, the script is unreachable and the operation is unavailable — say so.
Never fall back to a relative `scripts/issue-deps.sh`, which is the trap
`SKILL.md` describes: in a project with its own `scripts/` it runs an unrelated
file rather than failing.

An unreachable script leaves `SKILL.md`'s probe with its third branch, the
GitHub MCP alone — the probe reached the script branch precisely because `gh`
was absent or too old, so there is no client above it to fall back to. That
branch reads counts and writes nothing, which is what to report.
