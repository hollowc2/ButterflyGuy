"""Date-extension normalization and provenance, not strategy retuning."""

import numpy as np
import pandas as pd
import pytest

from tools.research_studies.xsp_independent import batman
from tools.research_studies.xsp_independent.batman_history import (
    SOURCE_TYPE,
    native_values,
    owner_minutes,
    rules,
    summarize,
)


def bars(day, count=60):
    stamps = pd.date_range(f"{day} 08:31", periods=count, freq="min")
    p = 4000 + np.arange(count)*.01
    return pd.DataFrame({"ts": stamps.strftime("%Y-%m-%d %H:%M:%S"), "open": p-.1,
                         "high": p+.5, "low": p-.5, "close": p})


@pytest.mark.parametrize("day,offset", [("2022-01-03", -5), ("2022-03-14", -4)])
def test_central_bar_end_is_available_at_end_not_one_minute_earlier(day, offset):
    p, events = owner_minutes(bars(day))
    first = p.timestamp.iloc[0]
    assert first.strftime("%H:%M") == "09:30"
    assert first.utcoffset().total_seconds() == offset*3600
    assert first + pd.Timedelta(minutes=1) == pd.Timestamp(f"{day} 09:31", tz="America/New_York")
    assert p.forward_proxy.iloc[0] == 400.
    assert not events


def test_stale_signal_detection_preserves_earlier_entries_without_future_censoring():
    raw = bars("2022-01-03", 100)
    # First40 distinct, then31 identical OHLC: threshold detected at index70.
    raw.loc[41:80, ["open", "high", "low", "close"]] = raw.loc[
        40, ["open", "high", "low", "close"]].to_numpy()
    early, _ = owner_minutes(raw.iloc[:60])
    full, events = owner_minutes(raw)
    assert len(full) == 70
    assert full.iloc[:60].equals(early)
    assert events[0]["known_at"].startswith("2022-01-03T10:41")
    assert events[0]["consecutive_same_comparisons"] == 30
    assert events[0]["reason"] == "unchanged_ohlc_run"
    # Recovery at index81 does not reactivate same-day observations.
    assert full.timestamp.iloc[-1] == pd.Timestamp("2022-01-03 10:39", tz="America/New_York")


def test_invalid_ohlc_causes_causal_quarantine_and_resets_next_session():
    a = bars("2022-01-03", 3)
    a.loc[1, "high"] = a.loc[1, "low"]-1
    b = bars("2022-01-04", 3)
    result, events = owner_minutes(pd.concat([a, b], ignore_index=True))
    assert result.groupby("date").size().to_dict() == {"2022-01-03": 1, "2022-01-04": 3}
    assert events[0]["reason"] == "invalid_ohlc"
    duplicate = pd.concat([a.iloc[:1], a.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        owner_minutes(duplicate)


def record(value=400.12, trading="XSP", settlement="XSP"):
    return {"expiration_date": "2022-01-03", "trading_symbol": trading,
            "settlement_symbol": settlement, "settlement_value": value}


def test_settlement_requires_exact_native_instrument_and_missing_is_missing():
    values = native_values({"source": [record(), record(400.123, "NANOS", "NANOS"),
                                       record(400.12, "XSP", "XSR")]},
                           {"2022-01-03", "2022-01-04"})
    assert values[0]["settlement"] == "400.12"
    assert values[0]["source_type"] == SOURCE_TYPE
    assert values[1]["settlement"] is None
    assert values[1]["source_type"] == "missing_native_settlement"


def test_overlapping_native_sources_must_agree_and_no_source_can_duplicate_a_date():
    values = native_values({"W": [record()], "S": [record()]}, {"2022-01-03"})
    assert values[0]["source_url"] == "W|S"
    with pytest.raises(ValueError, match="Conflicting"):
        native_values({"W": [record()], "S": [record(400.13)]}, {"2022-01-03"})
    with pytest.raises(ValueError, match="Duplicate"):
        native_values({"W": [record(), record()]}, {"2022-01-03"})


def test_extension_preserves_economic_rules_and_original_eight_cells():
    new = rules()
    for field in ("geometry", "entry", "movement_hypothesis", "zone_exit", "costs", "sizing_risk"):
        assert new[field] == batman.RULES[field]
    assert len(batman.CELLS) == 8
    assert new["period_inclusive_et"] == ["2022-01-03", "2026-09-28"]


def test_unresolved_opening_keeps_risk_bounds_without_becoming_zero_pnl():
    row = {"date": "2022-01-03", "cell": "body_unconditional_settlement",
           "status": "unresolved_settlement", "source": "owner_spx_unknown_provider",
           "unresolved_pnl_bounds": [-100., 300.]}
    result = summarize([row])["cells"][row["cell"]]
    assert result["accepted_entries"] == 1
    assert result["trades"] == 0
    assert result["unresolved_entries"] == 1
    assert result["full_cohort_pnl_bounds"] == [-100., 300.]
    assert "stressed" not in result
    assert result["decision"] == "insufficient evidence"
