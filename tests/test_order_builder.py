"""Tests for butterfly order builder."""

import datetime as dt

import pytest

from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder


def make_candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=10,
        center_strike=5500.0,
        lower_strike=5490.0,
        upper_strike=5510.0,
        cost=0.80,
        max_profit=9.20,
        reward_risk=11.5,
        lower_be=5490.80,
        upper_be=5509.20,
        distance_from_spot=0.0,
        spot_price=5500.0,
        lower_symbol="SPXW  260310C05490000",
        center_symbol="SPXW  260310C05500000",
        upper_symbol="SPXW  260310C05510000",
    )


def test_build_open_order_structure():
    builder = ButterflyOrderBuilder()
    candidate = make_candidate()
    order = builder.build_butterfly_open(candidate, limit_price=0.85)

    assert order["orderType"] == "NET_DEBIT"
    assert order["complexOrderStrategyType"] == "BUTTERFLY"
    assert order["duration"] == "DAY"
    assert order["session"] == "NORMAL"
    assert order["price"] == "0.85"

    legs = order["orderLegCollection"]
    assert len(legs) == 3


def test_build_open_order_legs():
    builder = ButterflyOrderBuilder()
    candidate = make_candidate()
    order = builder.build_butterfly_open(candidate, limit_price=0.85)
    legs = order["orderLegCollection"]

    # Lower leg: BUY 1
    assert legs[0]["instruction"] == "BUY_TO_OPEN"
    assert legs[0]["quantity"] == 1
    assert legs[0]["instrument"]["symbol"] == "SPXW  260310C05490000"

    # Center leg: SELL 2
    assert legs[1]["instruction"] == "SELL_TO_OPEN"
    assert legs[1]["quantity"] == 2
    assert legs[1]["instrument"]["symbol"] == "SPXW  260310C05500000"

    # Upper leg: BUY 1
    assert legs[2]["instruction"] == "BUY_TO_OPEN"
    assert legs[2]["quantity"] == 1
    assert legs[2]["instrument"]["symbol"] == "SPXW  260310C05510000"


def test_build_close_order_structure():
    builder = ButterflyOrderBuilder()
    candidate = make_candidate()
    order = builder.build_butterfly_close(candidate, limit_price=2.50)

    assert order["orderType"] == "NET_CREDIT"
    assert order["price"] == "2.5"

    legs = order["orderLegCollection"]
    assert legs[0]["instruction"] == "SELL_TO_CLOSE"
    assert legs[1]["instruction"] == "BUY_TO_CLOSE"
    assert legs[2]["instruction"] == "SELL_TO_CLOSE"


def test_build_order_with_quantity():
    builder = ButterflyOrderBuilder()
    candidate = make_candidate()
    order = builder.build_butterfly_open(candidate, limit_price=0.85, quantity=3)
    legs = order["orderLegCollection"]
    assert legs[0]["quantity"] == 3
    assert legs[1]["quantity"] == 6
    assert legs[2]["quantity"] == 3
