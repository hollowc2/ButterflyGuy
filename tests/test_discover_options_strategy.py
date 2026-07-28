import datetime as dt

import pytest

from butterfly_guy.scripts.discover_options_strategy import (
    Leg,
    Quote,
    drawdown,
    max_risk_points,
    percentile,
    price_trade,
)


def quote(symbol: str, strike: float, bid: float, ask: float, option_type: str = "CALL") -> Quote:
    return Quote(symbol, strike, option_type, bid, ask, (bid + ask) / 2, 0.5, 20, 100, 100, 6000)


def test_debit_trade_crosses_spread_and_pays_commission():
    entry = quote("C1", 6000, 9.5, 10.0)
    exit_quote = quote("C1", 6000, 11.0, 11.5)

    trade = price_trade(
        "long_call",
        "SPX",
        dt.date(2026, 7, 1),
        [Leg(entry, 1)],
        {"C1": exit_quote},
        0.001,
        20,
        None,
        18,
        345,
    )

    assert trade is not None
    assert trade.pnl == pytest.approx(98.70)
    assert trade.max_risk == pytest.approx(1001.30)


def test_credit_risk_uses_wing_width_less_credit():
    short = quote("C1", 6000, 4.0, 4.2)
    long = quote("C2", 6010, 1.0, 1.2)

    assert max_risk_points([Leg(short, -1), Leg(long, 1)], -2.8) == pytest.approx(7.2)


def test_percentile_requires_prior_history_and_drawdown_compounds():
    assert percentile(10, [1] * 19) is None
    assert percentile(10, list(range(20))) == pytest.approx(11 / 20)
    maximum, curve = drawdown([0.10, -0.20])
    assert maximum == pytest.approx(-0.20)
    assert curve[-1] == pytest.approx(-0.20)
