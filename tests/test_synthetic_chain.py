"""Tests for the synthetic chain generator."""

import datetime as dt
from zoneinfo import ZoneInfo

from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator

EASTERN = ZoneInfo("America/New_York")


def make_snapshot_time(minutes_to_close: float = 120.0) -> dt.datetime:
    """Create a snapshot time N minutes before 4pm ET."""
    base = dt.datetime(2026, 3, 10, 16, 0, tzinfo=EASTERN)
    return base - dt.timedelta(minutes=minutes_to_close)


def test_generate_chain_has_both_types():
    gen = SyntheticChainGenerator()
    snap_time = make_snapshot_time(120)
    quotes = gen.generate_chain(
        spot=5500.0,
        vix=18.0,
        expiration=dt.date(2026, 3, 10),
        snapshot_time=snap_time,
        strike_min=5450.0,
        strike_max=5550.0,
    )
    types = {q.option_type for q in quotes}
    assert "CALL" in types
    assert "PUT" in types


def test_generate_chain_strike_count():
    gen = SyntheticChainGenerator()
    snap_time = make_snapshot_time(120)
    quotes = gen.generate_chain(
        spot=5500.0,
        vix=18.0,
        expiration=dt.date(2026, 3, 10),
        snapshot_time=snap_time,
        strike_min=5490.0,
        strike_max=5510.0,
        strike_step=5.0,
    )
    # 5 strikes (5490, 5495, 5500, 5505, 5510) * 2 types = 10 quotes
    assert len(quotes) == 10


def test_atm_call_price_reasonable():
    gen = SyntheticChainGenerator()
    snap_time = make_snapshot_time(120)  # 2 hours to close
    quotes = gen.generate_chain(
        spot=5500.0,
        vix=18.0,
        expiration=dt.date(2026, 3, 10),
        snapshot_time=snap_time,
        strike_min=5499.0,
        strike_max=5501.0,
        strike_step=1.0,
    )
    calls = [q for q in quotes if q.option_type == "CALL" and q.strike == 5499.0]
    assert len(calls) == 1
    assert 0.1 < calls[0].mark < 50  # sanity range for 2-hour ATM call


def test_spread_positive():
    gen = SyntheticChainGenerator()
    snap_time = make_snapshot_time(60)
    quotes = gen.generate_chain(
        spot=5500.0, vix=20.0,
        expiration=dt.date(2026, 3, 10),
        snapshot_time=snap_time,
        strike_min=5480.0, strike_max=5520.0,
    )
    for q in quotes:
        assert q.ask > q.bid >= 0
        assert q.mark >= 0


def test_otm_put_iv_higher_than_otm_call():
    """Volatility skew: OTM puts should have higher IV than equidistant OTM calls."""
    gen = SyntheticChainGenerator()
    snap_time = make_snapshot_time(120)
    quotes = gen.generate_chain(
        spot=5500.0, vix=18.0,
        expiration=dt.date(2026, 3, 10),
        snapshot_time=snap_time,
        strike_min=5450.0, strike_max=5550.0,
    )
    q_map = {(q.strike, q.option_type): q for q in quotes}
    otm_put = q_map.get((5475.0, "PUT"))
    otm_call = q_map.get((5525.0, "CALL"))
    if otm_put and otm_call:
        assert otm_put.iv > otm_call.iv


def test_price_decreases_as_dte_shrinks():
    """Option price should decrease as expiration approaches."""
    gen = SyntheticChainGenerator()
    snap_240 = make_snapshot_time(240)  # 4 hours out
    snap_60 = make_snapshot_time(60)    # 1 hour out

    def get_atm_call(snap_time):
        quotes = gen.generate_chain(
            spot=5500.0, vix=18.0,
            expiration=dt.date(2026, 3, 10),
            snapshot_time=snap_time,
            strike_min=5499.0, strike_max=5501.0,
            strike_step=1.0,
        )
        calls = [q for q in quotes if q.option_type == "CALL" and q.strike == 5499.0]
        return calls[0].mark if calls else 0

    price_far = get_atm_call(snap_240)
    price_near = get_atm_call(snap_60)
    assert price_far > price_near
