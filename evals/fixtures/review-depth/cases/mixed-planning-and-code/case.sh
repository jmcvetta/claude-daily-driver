#!/usr/bin/env bash
# Adds a planning document and rewrites a source module.
# shellcheck source=../../shared/lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=../../shared/_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch feat/negative-amounts

cat >docs/planning/negative-amounts.md <<'EOF'
# Negative amounts

Today `parse_amount` multiplies the whole part by 100 and adds the fraction,
which is wrong for "-0.50": the whole part is zero, so the sign is lost and the
posting comes back as +50 minor units. Every journal with a sub-unit credit is
silently wrong, and nothing in the round-trip suite catches it.

## Plan

Parse the sign separately and apply it to the assembled total, rather than
letting `int()` carry it on the whole part alone.

## Rejected: Decimal

`decimal.Decimal` would handle the sign for free, and it would also introduce a
type whose equality and rounding rules differ from `int` everywhere else in the
codebase. The ledger is integer minor units end to end; one module speaking
`Decimal` is a seam that will leak.

## Migration

None needed. The stored format is text, and the fix changes only how that text
is read.
EOF

cat >src/parser.py <<'EOF'
"""Journal parsing: text in, postings out."""

from __future__ import annotations

from dataclasses import dataclass


class ParseError(ValueError):
    """Raised when a journal line cannot be read."""


@dataclass(frozen=True)
class Posting:
    account: str
    amount: int


def parse_amount(text: str) -> int:
    """Parse "12.34" into 1234 minor units, sign included.

    The sign is taken off the front and applied to the assembled total. Reading
    it off the whole part alone loses it whenever the whole part is zero.
    """
    text = text.strip()
    if not text:
        raise ParseError("empty amount")
    sign = -1 if text.startswith("-") else 1
    text = text.lstrip("+-")
    whole, _, frac = text.partition(".")
    if whole and not whole.isdigit():
        raise ParseError(f"not a number: {text!r}")
    if frac and not frac.isdigit():
        raise ParseError(f"not a number: {text!r}")
    return sign * (int(whole or 0) * 100 + int((frac + "00")[:2]))


def parse_line(line: str) -> tuple[str, int]:
    account, _, amount = line.strip().rpartition(" ")
    if not account:
        raise ParseError(f"no account in {line!r}")
    return account, parse_amount(amount)


def parse_journal(text: str) -> list[Posting]:
    postings: list[Posting] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        try:
            account, amount = parse_line(line)
        except ParseError as exc:
            raise ParseError(f"line {lineno}: {exc}") from exc
        postings.append(Posting(account, amount))
    return postings


def balance(postings: list[Posting]) -> int:
    """Net of every posting, in minor units. Zero means the journal balances."""
    return sum(posting.amount for posting in postings)


def format_amount(amount: int) -> str:
    """Inverse of `parse_amount`, sign and all."""
    sign = "-" if amount < 0 else ""
    whole, frac = divmod(abs(amount), 100)
    return f"{sign}{whole}.{frac:02d}"
EOF

fixture_publish_topic "fix: keep the sign on sub-unit negative amounts"
