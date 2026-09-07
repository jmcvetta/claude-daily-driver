#!/usr/bin/env bash
# Rewrites the root README. Nothing else changes.
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

## Reading a journal

A journal is a text file of postings, one per line, blank lines and `;`
comments ignored:

    assets:cash        10.00
    income:gift       -10.00

Every posting is an account and an amount. The account is everything up to the
last space, so `assets:petty cash 5.00` is one account, not two. The amount is
signed, and the sign belongs to the whole amount rather than to its whole part
-- `-0.50` is fifty minor units owed, not fifty owed in the other direction.

A journal balances when its postings sum to zero. `ledger check` says so with
its exit status; it prints the residual when they do not, in the same minor
units, so the number in the error is the number to go looking for.

## What the parser will not do

It will not guess. An amount it cannot read is an error naming the line, not a
zero quietly folded into the total -- a ledger that swallows a malformed
posting is worse than one that refuses the file, because the refusal is
visible and the swallowed line is not.

It will not accept a currency symbol. There is no currency here at all, which
is the same decision as the one about conversion above, arrived at from the
other end: a symbol implies a rate, and a rate implies a source.

## Testing

`pytest` over `tests/`. The round-trip suite is the one that matters: parse a
journal, format it back, and compare byte for byte. A parser that is wrong in
a way the formatter is also wrong about will pass it, which is why the table
cases in `test_parser.py` assert absolute values rather than round trips.

## Status

Usable. The format is not yet stable; assume a migration before 1.0.

Unstable in the specific sense that the on-disk journal format may change
before 1.0, not that the API will churn under you week to week. When it does
change there will be a migration, and the migration will be a script in this
repository rather than a paragraph telling you what to do by hand.
EOF

fixture_publish_topic "docs: expand the README"
