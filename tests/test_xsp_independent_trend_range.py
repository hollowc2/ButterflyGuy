"""Causality, signed liquidation and scheduled-close semantics of XSP research."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "xsp_trend_range",
    Path(__file__).resolve().parents[1] / "tools/research_studies/xsp_independent/trend_range.py",
)
study = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = study
spec.loader.exec_module(study)


def ts(s):
    return pd.Timestamp("2026-04-01 " + s, tz="America/New_York")


def proxy_frame():
    stamps = pd.date_range(ts("09:31"), ts("14:00"), freq="1min")
    values = np.full(len(stamps), 600.0)
    values[:29] = np.linspace(599.0, 601.0, 29)
    values[(stamps >= ts("10:05")) & (stamps < ts("10:10"))] = 602.0
    return pd.DataFrame({"timestamp": stamps, "forward_proxy": values})


def test_future_breakout_cannot_trigger_previous_completed_bar():
    f = proxy_frame()
    found, _ = study.signals(f)
    assert found["T1"].timestamp == ts("10:10")
    assert found["T1"].target == pytest.approx(603.0)
    altered = f.copy()
    altered.loc[altered.timestamp >= ts("10:10"), "forward_proxy"] = -1000
    assert study.signals(altered)[0]["T1"] == found["T1"]


def test_missing_opening_inputs_are_not_valid_no_trade():
    found, reasons = study.signals(proxy_frame().iloc[15:])
    assert not found
    assert reasons == {"all": "opening_proxy_coverage"}


def test_entry_strictly_after_signal_and_negative_liquidation_not_floored():
    signal = study.Signal("T1", ts("10:10"), 603.0, "CALL", 1, 2.0)
    path = pd.DataFrame(
        {
            "timestamp": [ts("10:10"), ts("10:11"), ts("11:11")],
            "entry_ask": [0.01, 0.5, 0.6],
            "liquidation_bid": [0.0, 0.0, -0.1],
            "mark": [0.005, 0.25, 0.25],
        }
    )
    got = study.simulate(path, signal, 2.0, 603.0)
    assert got["entry_time"] == str(ts("10:11"))
    assert got["net"] == pytest.approx(-65.2)
    assert got["stressed_net"] == pytest.approx(-75.2)
    assert got["initial_risk"] == pytest.approx(52.6)


def test_scheduled_early_close_caps_exit_and_rejects_late_signal():
    signal = study.Signal("T1", ts("12:20"), 603.0, "CALL", 1, 2.0)
    path = pd.DataFrame(
        {
            "timestamp": [ts("12:21"), ts("12:45"), ts("13:21")],
            "entry_ask": [0.5, 0.6, 1.0],
            "liquidation_bid": [0.2, 0.4, 0.9],
            "mark": [0.35, 0.5, 0.95],
        }
    )
    got = study.simulate(path, signal, 2.0, 603.0, ts("12:45"))
    assert got["exit_time"] == str(ts("12:45"))
    late = study.Signal("T1", ts("12:45"), 603.0, "CALL", 1, 2.0)
    assert study.simulate(path, late, 2.0, 603.0, ts("12:45"))["status"] == "signal_after_deadline"


def test_window_handles_microsecond_parquet_timestamps():
    f = proxy_frame()
    f["timestamp"] = f.timestamp.dt.as_unit("us")
    assert study.window(f, ts("09:31"), ts("10:00"), 25) is not None


def test_liquidation_never_uses_snapshot_after_research_deadline():
    signal = study.Signal("T1", ts("12:20"), 603.0, "CALL", 1, 2.0)
    path = pd.DataFrame(
        {
            "timestamp": [ts("12:21"), ts("12:46")],
            "entry_ask": [0.5, 0.6],
            "liquidation_bid": [0.2, 0.4],
            "mark": [0.35, 0.5],
        }
    )
    assert study.simulate(path, signal, 2.0, 603.0, ts("12:45"))["status"] == "missing_exit"


def test_removing_top_winners_does_not_remove_losses():
    rows = [
        {
            "date": "2026-04-01",
            "net": -30.0,
            "stressed_net": -40.0,
            "midpoint_net": -10.0,
            "risk_units": -0.3,
            "initial_risk": 100.0,
            "exposure_minutes": 60.0,
            "liquidation_bid": 0.7,
        }
    ]
    result = study.metrics(rows)
    assert result["top3_removed_net"] == -30.0
    assert result["stressed_top3_removed_net"] == -40.0
