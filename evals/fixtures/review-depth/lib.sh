#!/usr/bin/env bash
#
# Builds a small git repository in the sandbox root: a base branch published to
# a local bare remote, then a topic branch one commit ahead of it and pushed.
#
# Sourced, never executed. Each case script is
#     source "$(dirname "$0")/lib.sh"
# and then calls these functions in order. See `evals/README.md` for why the
# repository is built this way and what depends on its shape.

set -euo pipefail

FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX_DIR="$(cd "${FIXTURE_DIR}/.." && pwd)"

# Turn the sandbox root into a git repository and keep this directory out of it.
# `.git/info/exclude` rather than `.gitignore`, which would itself show up as a
# changed path.
fixture_init() {
	cd "${SANDBOX_DIR}"
	git init -q -b master .
	printf '/.fixture/\n' >>.git/info/exclude
	git config user.email "eval@example.invalid"
	git config user.name "Eval Fixture"
	git config commit.gpgsign false

	# Created empty rather than left absent; see evals/README.md.
	: >"${FIXTURE_DIR}/dispatched.txt"
}

# Commit whatever the case laid down as the base branch, publish it to a local
# bare `origin`, and set `origin/HEAD`.
fixture_publish_base() {
	git add -A
	git commit -q -m "chore: baseline"
	git init -q --bare "${FIXTURE_DIR}/origin.git"
	git remote add origin "${FIXTURE_DIR}/origin.git"
	git -c push.negotiate=false push -q -u origin master
	git remote set-head origin master
}

fixture_branch() {
	git checkout -q -b "$1"
}

# Commit the case's changes and push them. The push is not optional; see
# evals/README.md.
fixture_publish_topic() {
	git add -A
	git commit -q -m "$1"
	git -c push.negotiate=false push -q -u origin HEAD
}

# Emit N lines of mundane prose to stdout.
fixture_filler_lines() {
	local n="$1" i
	for ((i = 1; i <= n; i++)); do
		printf 'Step %d: warm the read-through cache for the tenant shard, then wait for the queue to drain.\n' "$i"
	done
}
