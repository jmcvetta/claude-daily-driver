#!/usr/bin/env bash
# Changes one word in one file under docs/.
# shellcheck source=./lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=./_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch docs/fix-typo

cat >docs/guide.md <<'EOF'
# Using the ledger

Run `ledger check` against a journal to validate it. The exit status is 0 when
every transaction balances and 1 when any of them does not.
EOF

fixture_publish_topic "docs: fix a typo in the guide"
