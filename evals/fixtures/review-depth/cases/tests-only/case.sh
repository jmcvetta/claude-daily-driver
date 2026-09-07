#!/usr/bin/env bash
# Rewrites the test module. Nothing else changes.
# shellcheck source=../../shared/lib.sh
source "$(dirname "$0")/lib.sh"
# shellcheck source=../../shared/_common_base.sh
source "$(dirname "$0")/_common_base.sh"

fixture_init
fixture_write_base_tree
fixture_publish_base
fixture_branch test/rounding-cases

cat >tests/test_parser.py <<'EOF'
import pytest

from src.parser import parse_amount, parse_line


def test_parse_amount_whole():
    assert parse_amount("12.34") == 1234


def test_parse_amount_no_fraction():
    assert parse_amount("7") == 700


def test_parse_amount_single_decimal():
    assert parse_amount("7.5") == 750


def test_parse_amount_three_decimals():
    # The third decimal is dropped rather than rounded. Asserting the current
    # behaviour, whatever it turns out to be worth.
    assert parse_amount("7.567") == 756


def test_parse_amount_negative():
    assert parse_amount("-3.20") == -320


def test_parse_amount_negative_sub_unit():
    assert parse_amount("-0.50") == -50


def test_parse_amount_leading_plus():
    assert parse_amount("+3.20") == 320


def test_parse_amount_zero():
    assert parse_amount("0.00") == 0


def test_parse_amount_large():
    assert parse_amount("1000000.01") == 100000001


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0.01", 1),
        ("0.10", 10),
        ("0.99", 99),
        ("1.00", 100),
        ("1.01", 101),
        ("9.99", 999),
    ],
)
def test_parse_amount_table(text, expected):
    assert parse_amount(text) == expected


def test_parse_line():
    assert parse_line("assets:cash 5.00") == ("assets:cash", 500)


def test_parse_line_account_with_spaces():
    assert parse_line("assets:petty cash 5.00") == ("assets:petty cash", 500)


def test_parse_line_strips_surrounding_whitespace():
    assert parse_line("   assets:cash 5.00   ") == ("assets:cash", 500)


def test_parse_line_negative_posting():
    assert parse_line("income:salary -2500.00") == ("income:salary", -250000)


@pytest.mark.parametrize(
    "line",
    [
        "assets:cash 1.00",
        "assets:bank 2.50",
        "expenses:rent 900.00",
        "income:salary -901.50",
    ],
)
def test_parse_line_round_trip(line):
    account, amount = parse_line(line)
    assert account
    assert isinstance(amount, int)


def test_journal_of_two_postings_balances():
    postings = [parse_line("assets:cash 10.00"), parse_line("income:gift -10.00")]
    assert sum(amount for _, amount in postings) == 0


def test_journal_of_two_postings_does_not_balance():
    postings = [parse_line("assets:cash 10.00"), parse_line("income:gift -9.99")]
    assert sum(amount for _, amount in postings) == 1


@pytest.mark.parametrize(
    ("account", "text"),
    [
        ("assets:cash", "0.01"),
        ("assets:bank:checking", "1234.56"),
        ("expenses:travel:flights", "0.00"),
        ("liabilities:card", "-42.00"),
    ],
)
def test_parse_line_accounts_survive_colons(account, text):
    parsed_account, amount = parse_line(f"{account} {text}")
    assert parsed_account == account
    assert amount == parse_amount(text)

EOF

fixture_publish_topic "test: cover rounding, signs and account names"
