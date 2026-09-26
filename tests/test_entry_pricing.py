import pytest

from butterfly_guy.core.entry_pricing import (
    capped_entry_limit,
    entry_fill_within_limit,
    net_price_increment,
    round_credit_limit,
    round_debit_limit,
)


def test_capped_entry_limit_never_rounds_above_configured_maximum() -> None:
    assert capped_entry_limit(0.81, 0.40, "XSP") == 0.40
    assert capped_entry_limit(0.409, 0.405, "XSP") == 0.40
    assert capped_entry_limit(0.399, 0.40, "XSP") == 0.39


def test_spx_entry_limit_rounds_down_to_a_nickel() -> None:
    assert capped_entry_limit(2.37, 5.00, "SPX") == 2.35
    assert capped_entry_limit(2.37, 2.33, "SPX") == 2.30
    assert capped_entry_limit(2.40, 5.00, "SPX") == 2.40


def test_increment_table_per_underlying() -> None:
    assert str(net_price_increment("SPX")) == "0.05"
    assert str(net_price_increment("spx")) == "0.05"
    assert str(net_price_increment("XSP")) == "0.01"
    assert str(net_price_increment("NDX")) == "0.01"


def test_unknown_underlying_fails_closed() -> None:
    with pytest.raises(ValueError, match="RUT"):
        round_debit_limit(1.23, "RUT")


def test_debits_round_down_and_credits_round_up() -> None:
    assert round_debit_limit(1.37, "SPX") == 1.35
    assert round_credit_limit(1.37, "SPX") == 1.40
    assert round_debit_limit(1.37, "XSP") == 1.37
    assert round_credit_limit(1.371, "XSP") == 1.38


def test_float_noise_does_not_move_an_on_increment_price() -> None:
    assert round_credit_limit(3.2 + 0.15, "SPX") == 3.35
    assert round_debit_limit(0.3 - 0.1, "SPX") == 0.20
    assert round_debit_limit(0.1 + 0.2, "XSP") == 0.30


def test_entry_fill_limit_comparison_is_decimal_safe() -> None:
    assert entry_fill_within_limit(0.40, 0.40)
    assert not entry_fill_within_limit(0.4001, 0.40)
