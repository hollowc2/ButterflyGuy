"""Causal timing, missing-data semantics and independently calculated fly cash ledger."""

import datetime as dt

import pandas as pd
import pytest

from tools.research_studies.xsp_independent.mean_reversion import (
    account,
    entry_signals,
    first_quote,
    wall,
)

DAY = dt.date(2026, 3, 13)


def proxy(bar_closes):
    bar_closes = list(bar_closes) + [bar_closes[-1]] * (36 - len(bar_closes))
    stamps = pd.date_range(wall(DAY, "09:31"), periods=29 + 5 * len(bar_closes), freq="min")
    values = [100.] * 29
    values[1] = 99.
    values[2] = 101.
    for value in bar_closes:
        values += [value] * 5
    return pd.DataFrame({"timestamp": stamps, "forward_proxy": values})


def test_failed_breakout_waits_for_completed_reentry_bar():
    p = proxy([102., 101.5, 100.5])
    result = entry_signals(p, DAY)
    signal = result["failed_breakout"]
    assert signal["signal_time"] == wall(DAY, "10:15")
    assert signal["right"] == "PUT"
    assert signal["target"] == 100.
    incomplete = entry_signals(p[p.timestamp < wall(DAY, "10:10")], DAY)
    assert incomplete["failed_breakout"]["status"] == "excluded_signal_proxy_coverage"


def test_excursion_needs_full_range_from_midpoint_and_later_reversal():
    result = entry_signals(proxy([101.5, 102., 101.75]), DAY)
    assert result["excursion_reversal"]["signal_time"] == wall(DAY, "10:15")
    assert result["excursion_reversal"]["right"] == "PUT"
    assert entry_signals(proxy([101.5, 101.25]), DAY)["excursion_reversal"]["status"] == "no_signal"


def test_missing_prefix_is_excluded_instead_of_no_trade():
    p = proxy([102., 100.5])
    p = p[~p.timestamp.between(wall(DAY, "10:00"), wall(DAY, "10:04"))]
    assert entry_signals(p, DAY)["failed_breakout"]["status"] == "excluded_signal_proxy_gap"


def test_future_changes_cannot_change_first_signal():
    p = proxy([102., 100.5, 100., 99.])
    first = entry_signals(p, DAY)["failed_breakout"]
    p.loc[p.timestamp >= wall(DAY, "10:10"), "forward_proxy"] = 500
    assert entry_signals(p, DAY)["failed_breakout"] == first


def test_execution_is_strictly_after_signal_and_bounded_to_two_minutes():
    stamp = wall(DAY, "10:15")
    p = pd.DataFrame({"timestamp": [stamp, stamp + pd.Timedelta(minutes=1)], "mark": [9., 1.]})
    assert first_quote(p, stamp, strict=True)["mark"] == 1.
    assert first_quote(p.iloc[:1], stamp, strict=True) is None
    assert first_quote(p.iloc[1:], stamp - pd.Timedelta(minutes=2), strict=True) is None


def test_signed_negative_exit_cash_is_not_floored_and_fees_count_four_contracts():
    # Pay $30+2.60 at entry and $10+2.60 to close: -$45.20 cash total.
    result = account(.30, -.10, .20, .05)
    assert result["marketable"] == pytest.approx(-45.20)
    assert result["stressed"] == pytest.approx(-55.20)
    assert result["midpoint"] == pytest.approx(-20.20)
    assert result["initial_risk_dollars"] == pytest.approx(32.60)


def test_future_proxy_gap_does_not_erase_existing_signal():
    p = proxy([102., 100.5, 100., 99., 99.])
    p = p[~p.timestamp.between(wall(DAY, "10:15"), wall(DAY, "10:19"))]
    assert entry_signals(p, DAY)["failed_breakout"]["signal_time"] == wall(DAY, "10:10")
