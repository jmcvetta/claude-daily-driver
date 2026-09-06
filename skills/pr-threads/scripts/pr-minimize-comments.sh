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
#   PR-review operations; `minimizeComment` is not among them — HTTP 403 with
#   a bare `message`, measured 2026-09-06. That one failure is named below,
#   because its remedy is a different machine rather than a different token.
#   Every other failure reports its own HTTP status and GitHub's own message,
#   which is why the gate is matched on its text rather than inferred from the
#   absence of a `data` key: on a web worker the proxy answers *every*
#   GraphQL request that way, a bad token included, so "no data key" does not
#   identify anything. Minimisation is a laptop capability, on a personal
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

# shellcheck disable=SC2016  # GraphQL variables, not shell ones
MUTATION='mutation($subjectId: ID!, $classifier: ReportedContentClassifiers!) {
  minimizeComment(input: {subjectId: $subjectId, classifier: $classifier}) {
    minimizedComment { isMinimized }
  }
}'

minimize() {
    local node_id="$1" payload response status body message

    payload=$(jq -n \
        --arg query "$MUTATION" \
        --arg subjectId "$node_id" \
        --arg classifier "$CLASSIFIER" \
        '{query: $query, variables: {subjectId: $subjectId, classifier: $classifier}}')

    # Status separated from body, as in pr-find-claude-comments.sh, so a
    # failure reports what GitHub said instead of one guess for every cause.
    response=$(curl -sS \
        -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -w $'\n%{http_code}' \
        -d "$payload" \
        https://api.github.com/graphql)
    status=${response##*$'\n'}
    body=${response%$'\n'*}

    # A GraphQL answer is a 200 carrying a `data` key, whatever else it says.
    # Anything else -- 401 on a stale token, 403 from the web worker's broker,
    # a 502 HTML page from a proxy -- failed before the mutation ran, and its
    # status and message are the diagnosis.
    if [ "$status" != "200" ] ||
       [ "$(printf '%s' "$body" | jq -e 'has("data")' 2>/dev/null)" != "true" ]; then
        echo "  ✗ POST /graphql returned HTTP $status" >&2
        # Read into a variable rather than piping straight to stderr: the
        # redirection order that silences jq's own complaint also silences
        # its output.
        message=$(printf '%s' "$body" | jq -r '.message? // .' 2>/dev/null) || message=""
        [ -n "$message" ] || message="$body"
        printf '    %s\n' "$message" >&2
        # The one cause worth naming, because its remedy is a different
        # machine rather than a different token.
        if printf '%s' "$body" | grep -qiE 'not enabled for this session|pinned set'; then
            echo "    minimizeComment needs a personal token; a Claude Code web" >&2
            echo "    worker's brokered token serves only pinned PR-review" >&2
            echo "    operations. Run this from the laptop." >&2
        fi
        return 1
    fi

    if [ "$(printf '%s' "$body" | jq 'has("errors")')" = "true" ]; then
        echo "  ✗ $(printf '%s' "$body" | jq -r '[.errors[].message] | join("; ")')" >&2
        return 1
    fi

    if [ "$(printf '%s' "$body" | jq -r '.data.minimizeComment.minimizedComment.isMinimized')" != "true" ]; then
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
