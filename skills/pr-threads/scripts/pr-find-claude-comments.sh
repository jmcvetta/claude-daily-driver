#!/usr/bin/env bash
#
# pr-find-claude-comments.sh — list Claude's own PR conversation comments,
# with the GraphQL node IDs the minimise mutation needs.
#
# WHY THIS EXISTS
#   `pr-minimize-comments.sh` takes `IC_kwDO…` node IDs, and nothing in the
#   GitHub MCP returns them: `search_issues` does not carry node IDs, and
#   `pull_request_read` with `get_comments` does not surface them either. The
#   node ID is in the REST payload, so this reads REST directly.
#
# DELETE THIS WHEN
#   the GitHub MCP exposes comment minimisation, which removes the need for
#   node IDs entirely — or exposes node IDs on a comment-listing tool, which
#   removes the need for this script while `pr-minimize-comments.sh` survives.
#
# CLIENT
#   `curl`, never `gh`. `gh` is not installed on a Claude Code web worker
#   (measured 2026-09-06), so a script reaching for it passes on the laptop
#   and fails invisibly on the other surface.
#
# Usage: pr-find-claude-comments.sh <pr-number> [--repo owner/name]
# Output: a JSON array of {id, node_id, created_at, user, excerpt}, oldest
#         first.

set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: pr-find-claude-comments.sh <pr-number> [--repo owner/name]

Lists Claude's own comments on a pull request conversation, including the
GraphQL node IDs required to minimise them.

  <pr-number>       the pull request number
  --repo OWNER/NAME the repository; defaults to the `origin` remote

Requires GITHUB_TOKEN (or GH_TOKEN) in the environment.
EOF
}

PR_NUMBER=""
REPO=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)
            [ $# -ge 2 ] || { echo "error: --repo needs a value" >&2; exit 2; }
            REPO="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            [ -z "$PR_NUMBER" ] || { echo "error: unexpected argument '$1'" >&2; usage; exit 2; }
            PR_NUMBER="$1"
            shift
            ;;
    esac
done

if [ -z "$PR_NUMBER" ]; then
    usage
    exit 2
fi

if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "error: PR number must be numeric, got '$PR_NUMBER'" >&2
    exit 2
fi

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
    echo "error: neither GITHUB_TOKEN nor GH_TOKEN is set" >&2
    exit 2
fi

# Repository from the `origin` remote when not given. Handles both
# `https://github.com/owner/name(.git)` and `git@github.com:owner/name(.git)`.
if [ -z "$REPO" ]; then
    origin=$(git remote get-url origin 2>/dev/null || true)
    if [ -z "$origin" ]; then
        echo "error: no --repo given and no 'origin' remote to infer one from" >&2
        exit 2
    fi
    REPO=${origin%.git}
    REPO=${REPO#*github.com[:/]}
    REPO=${REPO#https://}
    REPO=${REPO#git@}
fi

if ! [[ "$REPO" =~ ^[^/]+/[^/]+$ ]]; then
    echo "error: repository must be owner/name, got '$REPO'" >&2
    exit 2
fi

# One REST call, body and status separated so a non-2xx reports GitHub's own
# message instead of curl's exit code.
rest() {
    local path="$1" response status body
    response=$(curl -sS \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        -w $'\n%{http_code}' \
        "https://api.github.com/$path")
    status=${response##*$'\n'}
    body=${response%$'\n'*}
    if [ "$status" != "200" ]; then
        echo "error: GET /$path returned HTTP $status" >&2
        echo "$body" >&2
        return 1
    fi
    printf '%s' "$body"
}

# The signature the review comment carries, per the `pr-threads` skill's
# self-identification rule: "Claude", any words or version numbers, then a
# model id in brackets or parentheses. Kept deliberately loose across model
# generations — `Claude 4.1 Opus (claude-opus-4-1-…)` and
# `Claude Opus 5 [claude-opus-5]` must both match.
#
# This regex and that rule are one thing in two files. Change either and the
# other changes in the same commit, or superseded comments stop collapsing.
#
# Passed to jq by `--arg`, so it is the regex verbatim -- single backslashes,
# not the doubled ones an inlined jq program would need.
SIGNATURE='Claude\s+.*[\[(]claude-[a-z0-9.-]+[\])]'

page=1
all='[]'
while :; do
    batch=$(rest "repos/$REPO/issues/$PR_NUMBER/comments?per_page=100&page=$page")
    count=$(printf '%s' "$batch" | jq 'length')
    all=$(printf '%s\n%s' "$all" "$batch" | jq -s 'add')
    [ "$count" -lt 100 ] && break
    page=$((page + 1))
done

printf '%s' "$all" | jq --arg signature "$SIGNATURE" '
    [ .[]
      | select(.body | test($signature; "i"))
      | {
          id: .id,
          node_id: .node_id,
          created_at: .created_at,
          user: .user.login,
          excerpt: (.body | split("\n") | .[0:3] | join(" ") | .[0:100])
        }
    ] | sort_by(.created_at)'
