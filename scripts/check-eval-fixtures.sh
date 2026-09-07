#!/usr/bin/env bash
#
# Build every review-depth fixture and assert it has the shape the `review`
# skill needs. Needs git and bash; no model, no credentials, no network — so
# unlike the eval cases themselves this runs in CI.
#
# It exists because of a specific failure mode. `review` refuses to work on a
# directory that is not a git repository — "there's no branch, no commit
# history, nothing to diff against" — and a suite whose fixtures quietly stop
# building does not go red: every case scores 0 in both arms and reads exactly
# like a skill that never fires. That is a true negative from a bad case, and
# it is indistinguishable from the finding the suite exists to report. This is
# the leg that tells them apart, for the price of a few `git init`s.
#
# What each fixture must produce, because each is something `review` reads:
#
#   * `refs/remotes/origin/HEAD` — the base branch, resolved first of all
#   * a topic branch checked out, with an upstream, exactly one commit ahead
#   * nothing uncommitted, or the skill stops with "Local changes not pushed"
#   * a non-empty diff against the base
#
# It also exercises every arm of the dispatch recorder, which is the suite's
# only instrument: a broken recorder reports a review that routed nowhere.
#
# Usage: scripts/check-eval-fixtures.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="${REPO_ROOT}/evals/fixtures/review-depth"
SHARED="${FIXTURES}/shared"
CASES="${FIXTURES}/cases"

# Changed-line bounds per case, as `<min> <max>` (`-` for no bound). These are
# the thresholds each case sits against, not the counts it happens to have:
#
#   docs-typo                 the smallest diff in the suite; must stay a skim
#   mixed-planning-and-code   over ~50, so *kind* decides the depth, not size
#   planning-over-800-lines   over ~800, so the size row would fire on a code diff
#   readme-only               over ~50, for the same reason as mixed
#   sensitive-tiny            under ~50, so only the sensitive touch can explain
#                             a review at the verified effort level
#   tests-only                over ~50, so tests-bucket-with-code is what decides
case_bounds() {
	case "$1" in
	docs-typo) echo "- 49" ;;
	mixed-planning-and-code) echo "51 799" ;;
	planning-over-800-lines) echo "801 -" ;;
	readme-only) echo "51 799" ;;
	sensitive-tiny) echo "- 49" ;;
	tests-only) echo "51 799" ;;
	*) echo "" ;;
	esac
}

fail() {
	printf 'FAIL: %s: %s\n' "${1}" "${2}" >&2
	return 1
}

# Exercise every arm of the dispatch recorder against the copy the sandbox would
# actually get. It is invoked from a PreToolUse hook, where its failure is
# invisible twice over: `|| true` in the hook command stops a broken recorder
# from vetoing the call it watches, and an empty record then reads exactly like
# a review that routed nowhere.
#
# Each event below is one thing the recorder has to get right, and each is a way
# the instrument has actually been wrong:
#
#   * a subagent dispatch, which the planning route is graded on
#   * a skill call, which every other route is graded on
#   * the same call with the name slashed, which is what the CLI hands a hook
#     when the model writes `/code-review` -- it strips the prefix only after
#     the hook has seen the input, and SKILL.md writes the slash everywhere
#   * the same again behind a leading space, which shields the slash from the
#     strip unless the whitespace collapse runs first
#   * a name that is only whitespace, and one that is only the slash: both
#     empty once normalised, and neither may leave its `args` behind as a
#     record, where a criterion would read them as the name
#   * a doubled slash, which must keep one: `removeprefix` takes the single
#     slash the CLI accepts, where `lstrip` would eat the run and turn a name
#     the CLI never accepts into a record that scores
#   * a multi-line `args`, which must collapse to one line: the files are read
#     with re.MULTILINE, so an uncollapsed argument writes records of its own
probe_recorder() {
	local name="$1" sandbox="$2" recorder="$2/.fixture/record-dispatch.py"

	echo '{"tool_input":{"subagent_type":"check-eval-fixtures-probe"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a subagent event; in a run its hook would have nothing to record"
	grep -qx 'check-eval-fixtures-probe' "${sandbox}/.fixture/dispatched.txt" ||
		fail "${name}" "the recorder ran on a subagent event but wrote no roster line"

	echo '{"tool_input":{"skill":"code-review","args":"check-eval-fixtures-probe"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a skill event; in a run its hook would have nothing to record"
	grep -qx 'code-review check-eval-fixtures-probe' "${sandbox}/.fixture/invocations.txt" ||
		fail "${name}" "the recorder ran on a skill event but wrote no invocation line"

	echo '{"tool_input":{"skill":"/code-review","args":"slashed-probe"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a slashed skill name"
	grep -qx 'code-review slashed-probe' "${sandbox}/.fixture/invocations.txt" ||
		fail "${name}" "the recorder did not strip the leading slash, so every code-review criterion would miss"

	echo '{"tool_input":{"skill":" /code-review","args":"spaced-probe"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a space-then-slash skill name"
	grep -qx 'code-review spaced-probe' "${sandbox}/.fixture/invocations.txt" ||
		fail "${name}" "leading whitespace shielded the slash; the name must be stripped before removeprefix"

	echo '{"tool_input":{"skill":"   ","args":"code-review max master"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a whitespace-only skill name"
	echo '{"tool_input":{"skill":"/","args":"code-review max master"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a bare-slash skill name"
	grep -q 'code-review max master' "${sandbox}/.fixture/invocations.txt" &&
		fail "${name}" "an empty skill name promoted its arguments to the head of the line, where every criterion reads them as the name"

	echo '{"tool_input":{"skill":"//code-review","args":"doubled-probe"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a doubled-slash skill name"
	grep -qx '/code-review doubled-probe' "${sandbox}/.fixture/invocations.txt" ||
		fail "${name}" "more than one leading slash was stripped; lstrip would turn a name the CLI never accepts into a clean record"

	printf '%s\n' '{"tool_input":{"skill":"probe-skill","args":"one\ncode-review max\n"}}' |
		python3 "${recorder}" ||
		fail "${name}" "the recorder exited non-zero on a multi-line argument"
	grep -qx 'probe-skill one code-review max' "${sandbox}/.fixture/invocations.txt" ||
		fail "${name}" "the recorder did not collapse a multi-line argument, so a payload can forge a record"
}

check_one() {
	local script="$1" name sandbox
	# `<cases>/<name>/case.sh` — the case's name is its directory. The script
	# itself is `case.sh` in every case, because its filename is copied into the
	# sandbox and `sensitive-tiny.sh` would tell the agent what it is being
	# graded on.
	name="$(basename "$(dirname "${script}")")"
	sandbox="$(mktemp -d)"
	# shellcheck disable=SC2064  # expand $sandbox now, not at trap time
	trap "rm -rf '${sandbox}'" RETURN

	# Exactly what a task mounts: the shared scaffolding plus this one case,
	# both at `.fixture`. Copying the whole tree here would test a layout no
	# run ever gets.
	mkdir -p "${sandbox}/.fixture"
	cp -R "${SHARED}/." "${sandbox}/.fixture/"
	cp -R "${CASES}/${name}/." "${sandbox}/.fixture/"
	(cd "${sandbox}" && bash ".fixture/case.sh") ||
		fail "${name}" "fixture script exited non-zero"

	cd "${sandbox}"

	git symbolic-ref --quiet refs/remotes/origin/HEAD >/dev/null ||
		fail "${name}" "origin/HEAD is unset, so the skill cannot resolve a base branch"

	git rev-parse --abbrev-ref '@{upstream}' >/dev/null 2>&1 ||
		fail "${name}" "the topic branch has no upstream"

	local base ahead
	base="$(git symbolic-ref --short refs/remotes/origin/HEAD)"
	ahead="$(git rev-list --count "${base}..HEAD")"
	[ "${ahead}" = "1" ] ||
		fail "${name}" "expected exactly 1 commit ahead of ${base}, found ${ahead}"

	[ -z "$(git status --porcelain)" ] ||
		fail "${name}" "worktree is dirty, so the skill would stop at 'Local changes not pushed'"

	local changed
	changed="$(git diff --name-only "${base}...HEAD")"
	[ -n "${changed}" ] ||
		fail "${name}" "the topic branch changes nothing"

	local observed
	for observed in dispatched.txt invocations.txt; do
		[ -f "${sandbox}/.fixture/${observed}" ] ||
			fail "${name}" "no ${observed}; every file_matches_regex criterion would error on a missing file"
		[ ! -s "${sandbox}/.fixture/${observed}" ] ||
			fail "${name}" "${observed} is not empty before the agent has run"
	done

	probe_recorder "${name}" "${sandbox}"

	: >"${sandbox}/.fixture/dispatched.txt"
	: >"${sandbox}/.fixture/invocations.txt"

	local lines bounds min max
	lines="$(git diff --numstat "${base}...HEAD" | awk '{a += $1 + $2} END {print a + 0}')"
	bounds="$(case_bounds "${name}")"
	[ -n "${bounds}" ] ||
		fail "${name}" "no entry in case_bounds; add the thresholds this case sits against"
	read -r min max <<<"${bounds}"
	[ "${min}" = "-" ] || [ "${lines}" -ge "${min}" ] ||
		fail "${name}" "${lines} changed lines, below the ${min} this case needs; it now routes on size instead of on what it tests"
	[ "${max}" = "-" ] || [ "${lines}" -le "${max}" ] ||
		fail "${name}" "${lines} changed lines, above the ${max} this case allows; it now routes on size instead of on what it tests"

	printf 'ok  %-28s %4s changed line(s) across %s file(s), bounds [%s, %s]\n' \
		"${name}" "${lines}" \
		"$(printf '%s\n' "${changed}" | wc -l | tr -d ' ')" \
		"${min}" "${max}"
}

main() {
	local script found=0
	for script in "${CASES}"/*/case.sh; do
		found=$((found + 1))
		check_one "${script}"
	done

	[ "${found}" -gt 0 ] || {
		printf 'FAIL: no fixture case scripts found under %s\n' "${CASES}" >&2
		exit 1
	}

	# The one invariant the fixture *content* has to hold, asserted rather than
	# left to a comment. `skill_triggered` counts a `skills/<name>/` path in any
	# tool parameter as engaging that skill, so a fixture file carrying one would
	# score as a skill firing the moment the agent read it — including, as this
	# check found the first time it ran, a comment explaining the rule.
	local offenders
	if offenders="$(grep -rln "skills/" "${SHARED}" "${CASES}")"; then
		printf 'FAIL: fixture names a skills/ path, which skill_triggered would score as that skill firing:\n%s\n' \
			"${offenders}" >&2
		exit 1
	fi
	printf '\n%d review-depth fixture(s) build correctly.\n' "${found}"
}

main "$@"
