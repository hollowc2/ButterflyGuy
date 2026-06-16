import datetime as dt
import sys
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.scripts.run_backtest_db import (
    _find_entry_bar_at,
    _sim_parity_fields,
    candidate_from_trade_row,
    load_asset_config,
    parse_args,
    select_direction_bar,
)


def _parse_for_asset(monkeypatch, asset: str):
    monkeypatch.setattr(sys, "argv", ["run_backtest_db.py", "--asset", asset])
    return parse_args()


def test_ndx_backtest_drawdown_defaults_match_live_config(monkeypatch):
    args = _parse_for_asset(monkeypatch, "NDX")

    assert args.morning_dd == [1.00]
    assert args.late_morning_dd == [0.95]
    assert args.afternoon_dd == [0.90]


def test_spx_backtest_drawdown_defaults_match_live_config(monkeypatch):
    args = _parse_for_asset(monkeypatch, "SPX")

    assert args.morning_dd == [0.60]
    assert args.late_morning_dd == [0.90]
    assert args.afternoon_dd == [0.75]
    assert args.method == ["VIX"]
    assert args.profit_strategy == ["peakvaluetrailer"]
    assert args.wing_provided is False
    assert args.entry_time == [dt.time(7, 0)]
    assert args.use_abs_stop is False
    assert args.method_provided is False
    assert args.rr_min_provided is False


def test_backtest_tracks_explicit_selection_overrides(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_backtest_db.py", "--asset", "SPX", "--method", "BEST_RR", "--rr-min", "6.5"],
    )

    args = parse_args()

    assert args.method == ["BEST_RR"]
    assert args.rr_min == [6.5]
    assert args.method_provided is True
    assert args.rr_min_provided is True


def test_xsp_backtest_drawdown_defaults_match_live_config(monkeypatch):
    args = _parse_for_asset(monkeypatch, "XSP")

    assert args.morning_dd == [0.80]
    assert args.late_morning_dd == [0.90]
    assert args.afternoon_dd == [0.85]
    assert args.slippage == 0.005
    parity = _sim_parity_fields(load_asset_config("XSP"))
    assert parity["drawdown_confirmation_polls"] == 3
    assert parity["min_peak_profit_ratio"] == 1.25
    assert parity["min_hold_minutes"] == 45


def test_backtest_auto_direction_uses_first_regular_session_snapshot():
    eastern = ZoneInfo("America/New_York")
    bars = [
        MinuteBar(
            ts=dt.datetime(2026, 5, 13, 9, 30, tzinfo=eastern),
            open=7404.97,
            high=7404.97,
            low=7404.97,
            close=7404.97,
            volume=0,
        ),
        MinuteBar(
            ts=dt.datetime(2026, 5, 13, 9, 31, tzinfo=eastern),
            open=7398.31,
            high=7398.31,
            low=7398.31,
            close=7398.31,
            volume=0,
        ),
    ]

    assert select_direction_bar(bars).open == 7404.97


def test_default_entry_bar_lookup_rejects_late_fallback():
    eastern = ZoneInfo("America/New_York")
    bars = [
        MinuteBar(
            ts=dt.datetime(2026, 5, 18, 11, 23, tzinfo=eastern),
            open=5900.0,
            high=5900.0,
            low=5900.0,
            close=5900.0,
            volume=0,
        )
    ]
    target = dt.datetime(2026, 5, 18, 10, 0, tzinfo=eastern)

    assert _find_entry_bar_at(bars, target) is None
    assert _find_entry_bar_at(bars, target, max_lag_seconds=None) == bars[0]


def test_candidate_from_trade_row_pins_live_trade_fields():
    entry_time = dt.datetime(2026, 5, 20, 14, 0, tzinfo=dt.timezone.utc)
    trade = {
        "direction": "PUT",
        "wing_width": 30,
        "center_strike": 5900,
        "lower_strike": 5870,
        "upper_strike": 5930,
        "entry_price": 2.5,
        "entry_time": entry_time,
        "lower_symbol": "L",
        "center_symbol": "C",
        "upper_symbol": "U",
    }

    candidate = candidate_from_trade_row(trade)

    assert candidate.direction == "PUT"
    assert candidate.wing_width == 30
    assert candidate.center_strike == 5900
    assert candidate.lower_symbol == "L"
    assert candidate.cost == 2.5
