#!/usr/bin/env bash
#
# Shared fixture scaffolding for the review-depth suite.
#
# `review` needs a real repository — a base branch, a topic branch, a remote to
# diff against — and `coder_eval`'s sandbox does not build one: `starter_files`
# and `template_dir` copy loose files, and `type: repo` clones a URL onto a
# checked-out default branch, which is not the shape a branch under review has.
# A `tempdir` of loose files makes `review` correctly refuse ("there's no
# branch, no commit history, nothing to diff against") — a true negative from a
# bad case, which is the failure this file exists to prevent.
#
# `pre_run` is the seam that does build one. It runs a shell command inside the
# sandbox after setup and before the agent, and aborts the evaluation on a
# non-zero exit, so a fixture that fails to construct never reaches a model and
# never scores a misleading 0.
#
# `origin` is a bare repository under `.fixture/`, not a network remote: the
# skill's `git fetch` and `git symbolic-ref refs/remotes/origin/HEAD` both need
# a real remote, and the sandbox has no credentials and draws proxy 403s.
#
# Sourced, never executed. Every case script is
#     source "$(dirname "$0")/lib.sh"
# and then calls the four functions in order.

set -euo pipefail

FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX_DIR="$(cd "${FIXTURE_DIR}/.." && pwd)"

# Turn the sandbox root into a git repository and keep the fixture machinery out
# of it. `.git/info/exclude` rather than `.gitignore`: a `.gitignore` would show
# up as a changed path and shift the diff's *kind*, which is the one thing this
# suite measures.
fixture_init() {
	cd "${SANDBOX_DIR}"
	git init -q -b master .
	printf '/.fixture/\n' >>.git/info/exclude
	git config user.email "eval@example.invalid"
	git config user.name "Eval Fixture"
	git config commit.gpgsign false

	# The dispatch roster the PreToolUse recorder appends to. Created empty so a
	# `must_match: false` criterion reads "nothing was dispatched" rather than
	# failing on a missing file -- which is the whole `bare` arm, where there is
	# no `review` skill to dispatch anything.
	: >"${FIXTURE_DIR}/dispatched.txt"
}

# Commit whatever the case laid down as the base branch, publish it to a local
# bare `origin`, and set `origin/HEAD` — the ref the skill reads first to decide
# what to diff against.
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

# Commit the case's changes and push them. The push is not optional: `review`
# stops with "Local changes not pushed. Push first." when the local branch is
# ahead of its remote, and would never reach the routing decision under test.
fixture_publish_topic() {
	git add -A
	git commit -q -m "$1"
	git -c push.negotiate=false push -q -u origin HEAD
}

# Emit N lines of mundane prose to stdout, for cases whose signal is a line
# count rather than any particular content.
fixture_filler_lines() {
	local n="$1" i
	for ((i = 1; i <= n; i++)); do
		printf 'Step %d: warm the read-through cache for the tenant shard, then wait for the queue to drain.\n' "$i"
	done
}
