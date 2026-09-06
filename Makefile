#===============================================================================
#
# Makefile
#
#===============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

.PHONY: git_sync check check-plugin check-skills check-agents check-scripts \
	check-manifests check-constitution check-infra mcp-usage

# git_sync: sync master with origin and delete local branches whose upstream
# is gone. Branches checked out in a linked worktree (marked '+' by
# `git branch -vv`) are reported as a warning rather than deleted — removal
# needs an explicit `git worktree remove`
git_sync:
	git checkout master
	git pull
	git fetch --prune
	git branch -vv | awk '/: gone\]/ && !/^\+/ {print $$1}' | xargs -r git branch -D
	@git branch -vv | awk '/: gone\]/ && /^\+/ {printf "WARN: worktree-linked branch kept (upstream gone): %s\n", $$2}' >&2


# check: everything CI asserts about this plugin. CI runs this target rather
# than restating its legs, so a leg added here is a leg CI gains — and there
# is no second command line to fall behind this one.
check: check-plugin check-skills check-agents check-scripts check-manifests \
	check-constitution

# `claude plugin validate --strict` reads one manifest at a time and picks the
# marketplace when handed a directory, so the plugin manifest is named
# separately. --strict is what turns its warnings — unrecognized fields, a
# marketplace entry whose version disagrees with plugin.json — into failures.
check-plugin:
	claude plugin validate --strict .
	claude plugin validate --strict .claude-plugin/plugin.json

check-skills:
	claude plugin validate --strict skills

# `validate` reads one directory at a time, and skills and agents are separate
# component kinds, so the agent panel needs its own invocation or it is never
# checked at all.
check-agents:
	claude plugin validate --strict agents

# `validate --strict` is a floor, not a ceiling: measured against the CLI, it
# passes an agent with an empty description, one whose name disagrees with its
# filename, and two agents claiming the same name — the last of which makes one
# of them permanently unreachable. This is the leg that catches those, for
# skills and agents alike. See the docstring in the script.
check-manifests:
	python3 scripts/check-manifests.py

# The credential-free half of the constitution's acceptance test: run both
# delivery hooks against synthetic event JSON and assert the constitution comes
# back, identically, from each. The live half needs a model and therefore
# credentials, so it is a `claude plugin eval` case under evals/ rather than a
# leg here -- see the script's docstring for where the seam is and why.
check-constitution:
	python3 scripts/check-constitution.py

# check-scripts: lint the shell a skill ships. `claude plugin validate` reads
# manifests and never opens a `scripts/` file, so without this leg the plugin's
# executable half is the only part of the repository nothing checks.
#
# Unlike check-infra, this *is* part of `check`: shellcheck is a single small
# package present in the CI image, not a toolchain, so the laptop cost is one
# `apt install` rather than a reason to split the target.
check-scripts:
	shellcheck skills/*/scripts/*.sh

# check-infra: parse the OpenTofu stack without credentials. Not part of
# `check`, which must not start requiring OpenTofu on a laptop that is only
# editing a skill.
check-infra:
	$(MAKE) -C infra/github check-fmt validate

# mcp-usage: which GitHub MCP tools were actually called, rolled up to the
# toolsets that supply them. Laptop-only like git_sync — it reads Claude
# Code's session transcripts, which CI does not have — and deliberately not
# part of `check`. See docs/github-mcp.md for what the answer is for.
mcp-usage:
	python3 scripts/github-mcp-usage.py
