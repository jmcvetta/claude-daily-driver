#!/usr/bin/env bash
#
# issue-deps.sh — GitHub issue dependency edges (blocked-by / blocking).
#
# WHY THIS EXISTS
#
#   The GitHub MCP exposes sub-issues and `closed_by_pull_requests`, but has
#   no tool and no field for the blocked-by / blocking graph. The REST API
#   does. So this is the one relationship the skill cannot reach through the
#   MCP, and this script is the whole of the gap.
#
#   The client is `curl`, deliberately and not incidentally. `gh` is not
#   installed on a Claude Code web worker at all (measured 2026-09-06), while
#   `GITHUB_TOKEN` / `GH_TOKEN` are present on both surfaces. A script reaching
#   for `gh api` would work on the laptop and fail on the web — invisibly, on
#   the surface nobody develops on.
#
# EXPIRY
#
#   Four endpoints hold this script up:
#
#       POST   /repos/{o}/{r}/issues/{n}/dependencies/blocked_by
#       DELETE /repos/{o}/{r}/issues/{n}/dependencies/blocked_by/{id}
#       GET    /repos/{o}/{r}/issues/{n}/dependencies/blocked_by
#       GET    /repos/{o}/{r}/issues/{n}/dependencies/blocking
#
#   Delete this script the day the MCP exposes them. Nothing else here is
#   worth keeping: the id lookups and the guards below all exist to make those
#   four calls safe, and go with them.
#
# THE TRAPS IT CLOSES
#
#   - `issue_id` in the POST body is the opaque database id, NOT the #number.
#     Passing a #number returns 200 and creates an edge pointing at a stranger's
#     issue — database id 34 belongs to `davglass/yui-examples#1`. So this
#     script never accepts a raw id: it takes issue references and resolves
#     them itself.
#   - A read against a pull request answers 200 with an empty array,
#     indistinguishable from an issue with no edges. Only the write refuses.
#     So every subcommand checks the kind of object first and refuses to
#     present that emptiness as an answer.
#   - `POST .../dependencies/blocking` does not exist (404). An edge is stated
#     from the blocked side only, which is also the direction the need arrives
#     in.
#   - The POST response is the issue you just modified, so it confirms nothing.
#     Every write here is verified by a separate read from the other end.
#
# Reference: jmcvetta/career, docs/issue-dependencies.md

set -euo pipefail

API=https://api.github.com
PROG=${0##*/}

STATUS=
BODY=

die() {
	printf '%s: %s\n' "$PROG" "$*" >&2
	exit 1
}

usage() {
	cat >&2 <<EOF
usage: $PROG [--repo OWNER/REPO] <command> [args]

  blocked-by <issue>             what <issue> waits on
  blocking   <issue>             what waits on <issue>
  summary    <issue>             issue_dependencies_summary, open and total
  add        <issue> <blocker>   record that <issue> is blocked by <blocker>
  remove     <issue> <blocker>   remove that edge
  id         <issue>             the database id, for a call this script
                                 does not make

An <issue> is 123, #123, owner/repo#123, or a github.com issue URL. A bare
number resolves against --repo, or against the origin remote of the current
repository. Cross-repository edges are ordinary: name the other repository.

Auth comes from GITHUB_TOKEN or GH_TOKEN.
EOF
	exit 2
}

# ---------------------------------------------------------------- transport

request() { # request METHOD PATH [JSON-BODY]
	local method=$1 path=$2 body=${3-} out
	local -a args=(
		-sS -X "$method"
		-H "Authorization: Bearer $TOKEN"
		-H "Accept: application/vnd.github+json"
		-H "X-GitHub-Api-Version: 2022-11-28"
		-w '\n%{http_code}'
	)
	if [[ -n $body ]]; then
		args+=(-H "Content-Type: application/json" -d "$body")
	fi
	out=$(curl "${args[@]}" "$API/$path") || die "curl failed: $method $path"
	STATUS=${out##*$'\n'}
	BODY=${out%$'\n'*}
}

# The API's own words are more useful than a status code on its own — the
# refusals here name which end of the edge they inspected.
api_message() {
	printf '%s' "$BODY" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("(unparseable response)"); raise SystemExit
parts = [d.get("message", "")]
for e in d.get("errors", []):
    parts.append(e.get("message") or e.get("code", ""))
print("; ".join(p for p in parts if p))
'
}

# ------------------------------------------------------------------- refs

REF_OWNER=
REF_REPO=
REF_NUM=

parse_ref() {
	local ref=$1
	if [[ $ref =~ ^(https?://github\.com/)?([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)(/(issues|pull)/|#)([0-9]+)/?$ ]]; then
		REF_OWNER=${BASH_REMATCH[2]}
		REF_REPO=${BASH_REMATCH[3]}
		REF_NUM=${BASH_REMATCH[6]}
	elif [[ $ref =~ ^#?([0-9]+)$ ]]; then
		[[ -n $DEFAULT_OWNER ]] || die \
			"no default repository for '$ref' — pass --repo OWNER/REPO, or write it as owner/repo#${BASH_REMATCH[1]}"
		REF_OWNER=$DEFAULT_OWNER
		REF_REPO=$DEFAULT_REPO
		REF_NUM=${BASH_REMATCH[1]}
	else
		die "cannot read '$ref' as an issue reference"
	fi
}

default_repo_from_git() {
	local url
	url=$(git remote get-url origin 2>/dev/null) || return 0
	if [[ $url =~ github\.com[:/]([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+?)(\.git)?/?$ ]]; then
		DEFAULT_OWNER=${BASH_REMATCH[1]}
		DEFAULT_REPO=${BASH_REMATCH[2]}
	fi
}

# ------------------------------------------------------------------ issues

# Every fact this script needs about one end of an edge, from a single GET:
# the database id the write path wants, whether the object is a pull request
# (which no read further down would ever reveal), and the summary counts.
I_ID=
I_KIND=
I_STATE=
I_TITLE=
I_SUMMARY=

fetch_issue() { # fetch_issue OWNER REPO NUMBER
	request GET "repos/$1/$2/issues/$3"
	case $STATUS in
	200) ;;
	404) die "$1/$2#$3 not found, or the token cannot read it" ;;
	*) die "$1/$2#$3: HTTP $STATUS — $(api_message)" ;;
	esac
	local line
	line=$(printf '%s' "$BODY" | python3 -c '
import json, sys
d = json.load(sys.stdin)
s = d.get("issue_dependencies_summary") or {}
counts = "blocked_by %s/%s open/total, blocking %s/%s" % (
    s.get("blocked_by", 0), s.get("total_blocked_by", 0),
    s.get("blocking", 0), s.get("total_blocking", 0),
)
print(d["id"],
      "pull request" if "pull_request" in d else "issue",
      d.get("state", "?"),
      counts,
      (d.get("title") or "").replace("\t", " ").replace("\n", " "),
      sep="\t")
')
	IFS=$'\t' read -r I_ID I_KIND I_STATE I_SUMMARY I_TITLE <<<"$line"
}

# A pull request is not in this graph, at either end of either relationship —
# "Source issue may only be an issue", "Target issue may only be an issue".
# The write says so; the read never does, so this is where it gets said.
refuse_pull_request() { # refuse_pull_request LABEL OWNER REPO NUMBER
	[[ $I_KIND == "pull request" ]] || return 0
	die "$2/$3#$4 is a pull request, and $1 of a dependency may only be an issue.
  A read against a pull request answers 200 with an empty array — that emptiness
  is not evidence of anything, which is why this is refused rather than reported.
  The dependency belongs on the issues the pull requests implement, where it also
  outlives both of them being merged or abandoned."
}

# ------------------------------------------------------------------- edges

list_edges() { # list_edges OWNER REPO NUMBER blocked_by|blocking
	request GET "repos/$1/$2/issues/$3/dependencies/$4"
	[[ $STATUS == 200 ]] || die "$1/$2#$3 $4: HTTP $STATUS — $(api_message)"
	# Print the repository on both ends, always. A bare "#2853" under an edge
	# reads as a local issue and need not be one.
	printf '%s' "$BODY" | python3 -c '
import json, sys
rows = json.load(sys.stdin)
if not rows:
    print("  (none)")
for r in rows:
    print("  %s#%s  [%s]  %s" % (
        r.get("repository", {}).get("full_name", "?"),
        r.get("number"), r.get("state", "?"), r.get("title", "")))
'
}

has_edge() { # has_edge OWNER REPO NUMBER blocked_by|blocking OTHER_FULL#NUM
	request GET "repos/$1/$2/issues/$3/dependencies/$4"
	[[ $STATUS == 200 ]] || die "$1/$2#$3 $4: HTTP $STATUS — $(api_message)"
	printf '%s' "$BODY" | python3 -c '
import json, sys
want = sys.argv[1]
rows = json.load(sys.stdin)
found = any("%s#%s" % (r.get("repository", {}).get("full_name"), r.get("number")) == want
            for r in rows)
raise SystemExit(0 if found else 1)
' "$5"
}

# ------------------------------------------------------------- subcommands

cmd_read() { # cmd_read blocked_by|blocking REF
	parse_ref "$2"
	fetch_issue "$REF_OWNER" "$REF_REPO" "$REF_NUM"
	refuse_pull_request "either end" "$REF_OWNER" "$REF_REPO" "$REF_NUM"
	printf '%s/%s#%s  [%s]  %s\n' "$REF_OWNER" "$REF_REPO" "$REF_NUM" "$I_STATE" "$I_TITLE"
	printf '%s:\n' "$1"
	list_edges "$REF_OWNER" "$REF_REPO" "$REF_NUM" "$1"
}

cmd_summary() {
	parse_ref "$1"
	fetch_issue "$REF_OWNER" "$REF_REPO" "$REF_NUM"
	refuse_pull_request "either end" "$REF_OWNER" "$REF_REPO" "$REF_NUM"
	printf '%s/%s#%s  [%s]  %s\n' "$REF_OWNER" "$REF_REPO" "$REF_NUM" "$I_STATE" "$I_TITLE"
	# The two numbers are not a duplicate of each other: total counts every
	# edge, the other counts only the edges still open. An edge to a closed
	# issue stops blocking without anyone editing anything.
	printf '  %s\n' "$I_SUMMARY"
}

cmd_id() {
	parse_ref "$1"
	fetch_issue "$REF_OWNER" "$REF_REPO" "$REF_NUM"
	printf '%s\n' "$I_ID"
}

cmd_add() { # cmd_add BLOCKED BLOCKER
	parse_ref "$1"
	local b_owner=$REF_OWNER b_repo=$REF_REPO b_num=$REF_NUM
	fetch_issue "$b_owner" "$b_repo" "$b_num"
	refuse_pull_request "the blocked side" "$b_owner" "$b_repo" "$b_num"
	local blocked="$b_owner/$b_repo#$b_num" blocked_title=$I_TITLE

	parse_ref "$2"
	local k_owner=$REF_OWNER k_repo=$REF_REPO k_num=$REF_NUM
	fetch_issue "$k_owner" "$k_repo" "$k_num"
	refuse_pull_request "the blocker" "$k_owner" "$k_repo" "$k_num"
	local blocker="$k_owner/$k_repo#$k_num" blocker_id=$I_ID blocker_title=$I_TITLE

	[[ $blocked != "$blocker" ]] || die "an issue cannot block itself"

	if has_edge "$b_owner" "$b_repo" "$b_num" blocked_by "$blocker"; then
		printf 'already recorded: %s is blocked by %s\n' "$blocked" "$blocker"
		return 0
	fi

	# issue_id is a JSON number. Quoted, it earns a 422.
	request POST "repos/$b_owner/$b_repo/issues/$b_num/dependencies/blocked_by" \
		"{\"issue_id\": $blocker_id}"
	[[ $STATUS == 201 || $STATUS == 200 ]] ||
		die "POST blocked_by: HTTP $STATUS — $(api_message)"

	# The response body is the issue just modified, so it confirms nothing.
	# Read the other end: a wrong edge shows up as silence on the blocker.
	has_edge "$k_owner" "$k_repo" "$k_num" blocking "$blocked" ||
		die "wrote the edge but $blocker does not list $blocked under blocking — verify by hand before trusting it"

	printf 'recorded: %s  %s\n' "$blocked" "$blocked_title"
	printf '  blocked by %s  %s\n' "$blocker" "$blocker_title"
	printf '  verified from the blocking side.\n'
}

cmd_remove() { # cmd_remove BLOCKED BLOCKER
	parse_ref "$1"
	local b_owner=$REF_OWNER b_repo=$REF_REPO b_num=$REF_NUM
	fetch_issue "$b_owner" "$b_repo" "$b_num"
	refuse_pull_request "the blocked side" "$b_owner" "$b_repo" "$b_num"
	local blocked="$b_owner/$b_repo#$b_num"

	parse_ref "$2"
	local k_owner=$REF_OWNER k_repo=$REF_REPO k_num=$REF_NUM
	fetch_issue "$k_owner" "$k_repo" "$k_num"
	refuse_pull_request "the blocker" "$k_owner" "$k_repo" "$k_num"
	local blocker="$k_owner/$k_repo#$k_num" blocker_id=$I_ID

	# DELETE answers 200 for an edge that was never there, so a bare "removed"
	# would be the same false confirmation this script exists to avoid. Ask
	# first, and say which of the two things happened.
	if ! has_edge "$b_owner" "$b_repo" "$b_num" blocked_by "$blocker"; then
		printf 'not recorded: %s is not blocked by %s — nothing to remove\n' "$blocked" "$blocker"
		return 0
	fi

	# DELETE takes the database id in the path, not the #number.
	request DELETE "repos/$b_owner/$b_repo/issues/$b_num/dependencies/blocked_by/$blocker_id"
	case $STATUS in
	200 | 204) ;;
	404) die "no such edge: $blocked is not recorded as blocked by $blocker" ;;
	*) die "DELETE blocked_by: HTTP $STATUS — $(api_message)" ;;
	esac

	if has_edge "$k_owner" "$k_repo" "$k_num" blocking "$blocked"; then
		die "deleted the edge but $blocker still lists $blocked under blocking"
	fi
	printf 'removed: %s is no longer blocked by %s\n' "$blocked" "$blocker"
}

# ------------------------------------------------------------------- main

DEFAULT_OWNER=
DEFAULT_REPO=

while [[ ${1-} == --* ]]; do
	case $1 in
	--repo)
		[[ ${2-} == */* ]] || die "--repo wants OWNER/REPO"
		DEFAULT_OWNER=${2%%/*}
		DEFAULT_REPO=${2##*/}
		shift 2
		;;
	--help) usage ;;
	*) die "unknown option $1" ;;
	esac
done

[[ $# -ge 1 ]] || usage

TOKEN=${GITHUB_TOKEN:-${GH_TOKEN:-}}
[[ -n $TOKEN ]] || die "no GITHUB_TOKEN or GH_TOKEN in the environment"
command -v curl >/dev/null || die "curl is not installed"
command -v python3 >/dev/null || die "python3 is not installed"

[[ -n $DEFAULT_OWNER ]] || default_repo_from_git

command=$1
shift
case $command in
blocked-by)
	[[ $# -eq 1 ]] || usage
	cmd_read blocked_by "$1"
	;;
blocking)
	[[ $# -eq 1 ]] || usage
	cmd_read blocking "$1"
	;;
summary)
	[[ $# -eq 1 ]] || usage
	cmd_summary "$1"
	;;
add)
	[[ $# -eq 2 ]] || usage
	cmd_add "$1" "$2"
	;;
remove)
	[[ $# -eq 2 ]] || usage
	cmd_remove "$1" "$2"
	;;
id)
	[[ $# -eq 1 ]] || usage
	cmd_id "$1"
	;;
*) usage ;;
esac
