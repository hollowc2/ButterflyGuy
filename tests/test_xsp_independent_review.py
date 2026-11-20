"""Independent review regressions for forbidden late exits and unknown setups."""
import datetime as dt

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent import mean_reversion, trend_range


def ts(value):
    return pd.Timestamp(f"2026-04-01 {value}", tz="America/New_York")


def test_timed_exit_cannot_borrow_a_quote_after_hard_cutoff():
    signal = trend_range.Signal("T1", ts("12:40"), 600., "CALL", 1, 2.)
    path = pd.DataFrame({"timestamp": [ts("12:41"), ts("12:46")],
                         "entry_ask": [.5, .6], "liquidation_bid": [.3, .4],
                         "mark": [.4, .5]})
    result = trend_range.simulate(path, signal, 2., 600., cutoff=ts("12:45"))
    assert result["status"] != "completed"


def test_delayed_entry_after_cutoff_cannot_exit_backwards_in_time():
    signal = trend_range.Signal("T1", ts("12:44"), 600., "CALL", 1, 2.)
    path = pd.DataFrame({"timestamp": [ts("12:45"), ts("12:46")],
                         "entry_ask": [.5, .6], "liquidation_bid": [.3, .4],
                         "mark": [.4, .5]})
    result = trend_range.simulate(path, signal, 2., 600., cutoff=ts("12:45"))
    assert result["status"] != "completed"


def test_ending_data_before_setup_cutoff_is_unknown_not_no_trade():
    stamps = pd.date_range(ts("09:31"), ts("10:04"), freq="min")
    values = np.full(len(stamps), 600.)
    values[0], values[1] = 599., 601.
    result = mean_reversion.entry_signals(
        pd.DataFrame({"timestamp": stamps, "forward_proxy": values}), dt.date(2026, 4, 1))
    for arm in ("failed_breakout", "excursion_reversal"):
        assert result[arm]["status"].startswith("excluded")


def test_trend_no_trade_requires_coverage_through_signal_deadline():
    stamps = pd.date_range(ts("09:31"), ts("10:04"), freq="min")
    values = np.full(len(stamps), 600.)
    values[0], values[1] = 599., 601.
    found, reasons = trend_range.signals(
        pd.DataFrame({"timestamp": stamps, "forward_proxy": values}))
    assert "T1" not in found
    assert reasons["T1"] == "breakout_path_proxy_coverage_unknown_first_signal"
