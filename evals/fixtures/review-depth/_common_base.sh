#!/usr/bin/env bash
# Not a case. The base-branch tree every case starts from, so the cases differ
# only in the diff they put on top of it.
#
# Nothing here contains the substring `skills/` or the name of any reviewer
# agent: both would be read back out of tool telemetry by the criteria and
# scored as a skill engagement or a dispatch that never happened.

fixture_write_base_tree() {
	mkdir -p src tests docs/planning .github/workflows

	cat >README.md <<'EOF'
# ledger

A small double-entry ledger. Amounts are integer minor units; there is no
floating point anywhere in `src/`.

## Layout

- `src/parser.py` — reads the on-disk journal format
- `tests/` — the journal round-trip suite
EOF

	cat >src/parser.py <<'EOF'
"""Journal parsing: text in, postings out."""

from __future__ import annotations


def parse_amount(text: str) -> int:
    """Parse "12.34" into 1234 minor units."""
    whole, _, frac = text.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def parse_line(line: str) -> tuple[str, int]:
    account, _, amount = line.strip().rpartition(" ")
    return account, parse_amount(amount)
EOF

	cat >tests/test_parser.py <<'EOF'
from src.parser import parse_amount, parse_line


def test_parse_amount_whole():
    assert parse_amount("12.34") == 1234


def test_parse_line():
    assert parse_line("assets:cash 5.00") == ("assets:cash", 500)
EOF

	cat >docs/guide.md <<'EOF'
# Using the ledger

Run `ledger check` against a journal to validate it. The exit status is 0 when
every transaction balances and 1 when any does not.
EOF

	cat >.github/workflows/release.yml <<'EOF'
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: python -m build
      - run: python -m twine upload dist/*
EOF
}
