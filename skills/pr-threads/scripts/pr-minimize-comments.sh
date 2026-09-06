#!/usr/bin/env bash
#
# pr-minimize-comments.sh — collapse GitHub comments by GraphQL node ID.
#
# WHY THIS EXISTS
#   `minimizeComment` is a GraphQL mutation with no REST equivalent, and the
#   GitHub MCP does not expose it. A genuine capability gap, established by
#   absence from the MCP tool surface rather than assumed.
#
# DELETE THIS WHEN
#   the GitHub MCP grows a comment-minimisation tool. Nothing else here is
#   worth keeping — this script is one mutation and its error handling.
#
# CLIENT
#   `curl`, never `gh`. `gh` is not installed on a Claude Code web worker
#   (measured 2026-09-06).
#
# SURFACE LIMITATION
#   A web worker's brokered GITHUB_TOKEN serves only a pinned set of GraphQL
#   PR-review operations; `minimizeComment` is not among them (measured
#   2026-09-06). The gate is detected below and reported as itself rather than
#   as a mystery failure. Minimisation is a laptop capability, on a personal
#   token.
#
# Usage: pr-minimize-comments.sh [--classifier TYPE] <node-id> [<node-id> ...]

set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: pr-minimize-comments.sh [--classifier TYPE] <node-id> [<node-id> ...]

Collapses one or more GitHub comments.

  <node-id>         GraphQL node ID, e.g. IC_kwDOPMFYs864jCKn
  --classifier TYPE OUTDATED (default), DUPLICATE, SPAM, RESOLVED,
                    OFF_TOPIC or ABUSE

Node IDs come from pr-find-claude-comments.sh.
Requires GITHUB_TOKEN (or GH_TOKEN) in the environment.
EOF
}

CLASSIFIER="OUTDATED"
NODE_IDS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --classifier)
            [ $# -ge 2 ] || { echo "error: --classifier needs a value" >&2; exit 2; }
            CLASSIFIER="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            NODE_IDS+=("$1")
            shift
            ;;
    esac
done

if [ ${#NODE_IDS[@]} -eq 0 ]; then
    usage
    exit 2
fi

case "$CLASSIFIER" in
    OUTDATED|DUPLICATE|SPAM|RESOLVED|OFF_TOPIC|ABUSE) ;;
    *)
        echo "error: invalid classifier '$CLASSIFIER'" >&2
        echo "valid: OUTDATED, DUPLICATE, SPAM, RESOLVED, OFF_TOPIC, ABUSE" >&2
        exit 2
        ;;
esac

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
    echo "error: neither GITHUB_TOKEN nor GH_TOKEN is set" >&2
    exit 2
fi

MUTATION='mutation($subjectId: ID!, $classifier: ReportedContentClassifiers!) {
  minimizeComment(input: {subjectId: $subjectId, classifier: $classifier}) {
    minimizedComment { isMinimized }
  }
}'

minimize() {
    local node_id="$1" payload response

    payload=$(jq -n \
        --arg query "$MUTATION" \
        --arg subjectId "$node_id" \
        --arg classifier "$CLASSIFIER" \
        '{query: $query, variables: {subjectId: $subjectId, classifier: $classifier}}')

    response=$(curl -sS \
        -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        https://api.github.com/graphql)

    # A gated token answers with a bare `message` and no `data` key at all --
    # not with GraphQL's `errors` array. Distinguished here because the
    # remedy is different: this one is not retryable and not a bad node ID.
    if [ "$(printf '%s' "$response" | jq 'has("data")')" != "true" ]; then
        echo "  ✗ GraphQL unavailable on this surface:" >&2
        printf '%s' "$response" | jq -r '.message // .' >&2
        echo "    minimizeComment needs a personal token; a Claude Code web" >&2
        echo "    worker's brokered token serves only pinned PR-review" >&2
        echo "    operations. Run this from the laptop." >&2
        return 1
    fi

    if [ "$(printf '%s' "$response" | jq 'has("errors")')" = "true" ]; then
        echo "  ✗ $(printf '%s' "$response" | jq -r '[.errors[].message] | join("; ")')" >&2
        return 1
    fi

    if [ "$(printf '%s' "$response" | jq -r '.data.minimizeComment.minimizedComment.isMinimized')" != "true" ]; then
        echo "  ✗ API reported the comment was not minimised" >&2
        return 1
    fi

    echo "  ✓ minimised"
}

minimized=0
failed=0

for node_id in "${NODE_IDS[@]}"; do
    echo "$node_id ($CLASSIFIER)"
    if minimize "$node_id"; then
        minimized=$((minimized + 1))
    else
        failed=$((failed + 1))
    fi
done

echo
echo "$minimized minimised, $failed failed"
[ "$failed" -eq 0 ]
