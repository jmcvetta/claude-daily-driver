#===============================================================================
#
# Makefile
#
#===============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -o pipefail -c

.PHONY: git_sync check check-plugin check-skills check-scripts check-infra mcp-usage

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
check: check-plugin check-skills check-scripts

# `claude plugin validate --strict` reads one manifest at a time and picks the
# marketplace when handed a directory, so the plugin manifest is named
# separately. --strict is what turns its warnings — unrecognized fields, a
# marketplace entry whose version disagrees with plugin.json — into failures.
check-plugin:
	claude plugin validate --strict .
	claude plugin validate --strict .claude-plugin/plugin.json

# The components, then the three things validate lets through. See the
# docstring in the script for which and why.
check-skills:
	claude plugin validate --strict skills
	python3 scripts/check-manifests.py

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
