# Claude Code routes — issue-deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Claude Code. Omp's routes are in [`omp.md`](omp.md).

`scripts/issue-deps.sh` is invoked through `${CLAUDE_PLUGIN_ROOT}`, the
plugin root the harness injects into a skill's Bash:

```sh
deps="${CLAUDE_PLUGIN_ROOT}/skills/issue-deps/scripts/issue-deps.sh"
```
