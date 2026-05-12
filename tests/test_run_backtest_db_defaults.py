import sys

from butterfly_guy.scripts.run_backtest_db import parse_args


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


def test_xsp_backtest_drawdown_defaults_match_live_config(monkeypatch):
    args = _parse_for_asset(monkeypatch, "XSP")

    assert args.morning_dd == [0.60]
    assert args.late_morning_dd == [0.90]
    assert args.afternoon_dd == [0.75]
