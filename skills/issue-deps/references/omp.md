# Omp routes — issue-deps

`SKILL.md` names each operation in words. This file names the call, for a
session running in Oh My Pi. Claude Code's routes are in
[`claude.md`](claude.md).

`scripts/issue-deps.sh` is invoked through the injected skill-directory
path, resolved as a `skill://` URL. Omp's Bash resolves that URL to the
plugin's skill directory, which is where this script lives:

```sh
deps="skill://issue-deps/scripts/issue-deps.sh"
```
