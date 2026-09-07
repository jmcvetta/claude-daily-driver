#!/usr/bin/env bash
# A rewrite of the root README and nothing else. `README.md` is planning-class
# and docs-only both; the buckets are tested in order, so planning-class wins.
# shellcheck source=./lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=./_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch docs/rewrite-readme

cat >README.md <<'EOF'
# ledger

A small double-entry ledger, in about six hundred lines of Python.

## Why integer minor units

Every amount in this repository is an integer count of minor units — cents,
pence, satoshi. There is no floating point in `src/`, and adding some would be
a defect rather than a simplification: a journal that does not balance to the
minor unit is not a journal.

## Layout

- `src/parser.py` — reads the on-disk journal format
- `tests/` — the journal round-trip suite

## What is deliberately missing

There is no currency conversion, and there will not be one here. Conversion is
a policy question with a rate source behind it, and a ledger that silently
picks a rate is worse than one that refuses to.

## Status

Usable. The format is not yet stable; assume a migration before 1.0.
EOF

fixture_publish_topic "docs: expand the README"
