"""Tests for Schwab vs DB exit mark parity reporting."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.exit_mark_parity import build_exit_mark_parity


def _candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=20,
        center_strike=7430.0,
        lower_strike=7410.0,
        upper_strike=7450.0,
        cost=1.9,
        max_profit=18.1,
        reward_risk=10.0,
        lower_be=7411.9,
        upper_be=7448.1,
        distance_from_spot=51.0,
        spot_price=7379.0,
    )


def _quote(strike: float, mark: float) -> OptionQuote:
    return OptionQuote(
        symbol=f"C{int(strike)}",
        underlying="SPX",
        expiration=dt.date(2026, 5, 20),
        strike=strike,
        option_type="CALL",
        bid=mark - 0.05,
        ask=mark + 0.05,
        mark=mark,
    )


def test_build_exit_mark_parity_flags_replay_miss_on_lower_live_mark():
    candidate = _candidate()
    live_quotes = {
        7410.0: _quote(7410.0, 1.98),
        7430.0: _quote(7430.0, 0.73),
        7450.0: _quote(7450.0, 0.32),
    }
    snapshot = {
        "snapshot_time": dt.datetime(2026, 5, 20, 14, 13, 15, tzinfo=dt.timezone.utc),
        "lag_seconds": 44.0,
        "rows": [
            {
                "strike": 7410.0,
                "option_type": "CALL",
                "bid": 1.95,
                "ask": 2.0,
                "mark": 1.98,
            },
            {
                "strike": 7430.0,
                "option_type": "CALL",
                "bid": 0.70,
                "ask": 0.75,
                "mark": 0.73,
            },
            {
                "strike": 7450.0,
                "option_type": "CALL",
                "bid": 0.30,
                "ask": 0.35,
                "mark": 0.32,
            },
        ],
    }

    report = build_exit_mark_parity(
        candidate=candidate,
        live_quotes=live_quotes,
        live_fly_mark=0.76,
        live_peak=1.92,
        live_drawdown_pct=60.4,
        exit_reason="drawdown_morning",
        snapshot=snapshot,
        underlying="SPX",
        expiration=dt.date(2026, 5, 20),
    )

    assert report["available"] is True
    assert report["live_fly_mark"] == 0.76
    assert report["db_fly_mark"] == 0.84
    assert report["fly_mark_delta"] == -0.08
    assert report["replay_would_miss_drawdown"] is True


def test_build_exit_mark_parity_unavailable_without_snapshot():
    report = build_exit_mark_parity(
        candidate=_candidate(),
        live_quotes={},
        live_fly_mark=0.76,
        live_peak=1.92,
        live_drawdown_pct=60.4,
        exit_reason="drawdown_morning",
        snapshot=None,
        underlying="SPX",
        expiration=dt.date(2026, 5, 20),
    )

    assert report["available"] is False
    assert report["live_fly_mark"] == 0.76
