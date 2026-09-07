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
# Usage: scripts/check-eval-fixtures.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURES="${REPO_ROOT}/evals/fixtures/review-depth"

# Changed-line bounds per case, as `<min> <max>` (`-` for no bound). These are
# the thresholds each case sits against, not the counts it happens to have:
#
#   docs-typo                 the smallest diff in the suite; must stay a skim
#   mixed-planning-and-code   over ~50, so *kind* decides the depth, not size
#   planning-over-800-lines   over ~800, so the size row would fire on a code diff
#   readme-only               over ~50, for the same reason as mixed
#   sensitive-tiny            under ~50, so only the sensitive touch can explain
#                             a security reviewer
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

check_one() {
	local script="$1" name sandbox
	name="$(basename "${script}" .sh)"
	sandbox="$(mktemp -d)"
	# shellcheck disable=SC2064  # expand $sandbox now, not at trap time
	trap "rm -rf '${sandbox}'" RETURN

	cp -R "${FIXTURES}" "${sandbox}/.fixture"
	(cd "${sandbox}" && bash ".fixture/${name}.sh") ||
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

	[ -f "${sandbox}/.fixture/dispatched.txt" ] ||
		fail "${name}" "no dispatch roster; every file_matches_regex criterion would error on a missing file"
	[ ! -s "${sandbox}/.fixture/dispatched.txt" ] ||
		fail "${name}" "the dispatch roster is not empty before the agent has run"

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
	for script in "${FIXTURES}"/*.sh; do
		case "$(basename "${script}")" in
		lib.sh | _*) continue ;; # sourced, not a case
		esac
		found=$((found + 1))
		check_one "${script}"
	done

	[ "${found}" -gt 0 ] || {
		printf 'FAIL: no fixture case scripts found under %s\n' "${FIXTURES}" >&2
		exit 1
	}
	printf '\n%d review-depth fixture(s) build correctly.\n' "${found}"
}

main "$@"
