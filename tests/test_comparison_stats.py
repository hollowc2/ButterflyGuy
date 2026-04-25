"""Tests for _print_comparison_table aggregate stats."""
import io
import sys
import datetime as dt
from butterfly_guy.scripts.run_backtest_db import _print_comparison_table
from butterfly_guy.backtest.simulation_engine import DayResult


def _make_result(traded, pnl, center, exit_reason):
    r = DayResult(date=dt.date(2026, 3, 13))
    r.traded = traded
    r.pnl = pnl
    r.center_strike = center
    r.exit_reason = exit_reason
    r.entry_price = 1.0
    r.peak_value = 1.5
    r.exit_price = pnl + 1.0
    r.wing_width = 10
    r.direction = "CALL"
    return r


def _capture(day_rows):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _print_comparison_table(day_rows)
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_stats_block_present():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(True, 0.30, 5500.0, "end_of_day"),
         "synth_result": _make_result(True, 0.20, 5500.0, "end_of_day")},
        {"data": {"date": dt.date(2026, 3, 14)},
         "result": _make_result(True, -0.10, 5490.0, "drawdown_morning"),
         "synth_result": _make_result(True, -0.05, 5495.0, "drawdown_morning")},
    ]
    out = _capture(rows)
    assert "AGGREGATE COMPARISON STATS" in out
    assert "PnL correlation" in out
    assert "Trade match" in out
    assert "Exit match" in out
    assert "Avg divergence" in out


def test_perfect_correlation():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(True, 0.30, 5500.0, "end_of_day"),
         "synth_result": _make_result(True, 0.30, 5500.0, "end_of_day")},
        {"data": {"date": dt.date(2026, 3, 14)},
         "result": _make_result(True, -0.10, 5490.0, "drawdown_morning"),
         "synth_result": _make_result(True, -0.10, 5490.0, "drawdown_morning")},
    ]
    out = _capture(rows)
    assert any("PnL correlation" in ln and "1.00" in ln for ln in out.splitlines())  # perfect correlation


def test_no_trade_days_handled():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(False, 0.0, 0.0, ""),
         "synth_result": _make_result(False, 0.0, 0.0, "")},
    ]
    out = _capture(rows)
    assert "AGGREGATE COMPARISON STATS" in out
