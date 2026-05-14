import datetime as dt
import sys
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.scripts.run_backtest_db import parse_args, select_direction_bar


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


def test_xsp_backtest_drawdown_defaults_match_live_config(monkeypatch):
    args = _parse_for_asset(monkeypatch, "XSP")

    assert args.morning_dd == [0.60]
    assert args.late_morning_dd == [0.90]
    assert args.afternoon_dd == [0.75]
    assert args.slippage == 0.005


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
