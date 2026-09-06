#!/usr/bin/env bash
#
# pr-minimize-previous-claude-comments.sh — collapse every Claude review
# comment on a pull request except the most recent one.
#
# WHY THIS EXISTS
#   It is the one entry point the `pr-threads` skill calls. The two halves it
#   composes are each an MCP gap in their own right (see their headers); this
#   joins them and applies the one policy that matters — keep the latest
#   review readable, collapse what it superseded.
#
# DELETE THIS WHEN
#   either half is retired. With minimisation in the MCP there is nothing
#   left to compose.
#
# The PR number is required rather than inferred. `gh pr view` inferred it
# once; the MCP has no "PR for the current branch" call, and reconstructing
# one here would add a third MCP gap this directory has not established.
# The caller knows the number.
#
# Usage: pr-minimize-previous-claude-comments.sh <pr-number> [--repo owner/name] [--classifier TYPE]

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat >&2 <<'EOF'
Usage: pr-minimize-previous-claude-comments.sh <pr-number> [options]

Collapses every Claude comment on the pull request except the newest.

  <pr-number>       the pull request number
  --repo OWNER/NAME the repository; defaults to the `origin` remote
  --classifier TYPE OUTDATED (default), DUPLICATE, SPAM, RESOLVED,
                    OFF_TOPIC or ABUSE

Requires GITHUB_TOKEN (or GH_TOKEN) in the environment.
EOF
}

PR_NUMBER=""
FIND_ARGS=()
MINIMIZE_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)
            [ $# -ge 2 ] || { echo "error: --repo needs a value" >&2; exit 2; }
            FIND_ARGS+=(--repo "$2")
            shift 2
            ;;
        --classifier)
            [ $# -ge 2 ] || { echo "error: --classifier needs a value" >&2; exit 2; }
            MINIMIZE_ARGS+=(--classifier "$2")
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

comments=$("$HERE/pr-find-claude-comments.sh" "$PR_NUMBER" "${FIND_ARGS[@]+"${FIND_ARGS[@]}"}")
total=$(printf '%s' "$comments" | jq 'length')

if [ "$total" -eq 0 ]; then
    echo "No Claude comments on PR #$PR_NUMBER"
    exit 0
fi

# pr-find-claude-comments.sh returns oldest first, so dropping the tail keeps
# the newest review visible and collapses everything it superseded.
mapfile -t node_ids < <(printf '%s' "$comments" | jq -r '.[:-1] | .[].node_id')

if [ ${#node_ids[@]} -eq 0 ]; then
    echo "One Claude comment on PR #$PR_NUMBER (the newest) — nothing to minimise"
    exit 0
fi

echo "PR #$PR_NUMBER: $total Claude comment(s); minimising ${#node_ids[@]}, keeping the newest"
echo

exec "$HERE/pr-minimize-comments.sh" "${MINIMIZE_ARGS[@]+"${MINIMIZE_ARGS[@]}"}" "${node_ids[@]}"
