"""Vendor history adapter: mapping onto the research schema, the vendor_1m clock, the
writer's manifest history and cost check. All on a synthetic source (no provider is
chosen yet)."""

from __future__ import annotations

import datetime as dt
import io

import numpy as np
import pandas as pd
import pytest

from butterfly_guy.research.dataset import Dataset, SessionChain
from butterfly_guy.research.entry import PROFILES, SessionLoader
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.history import (
    PROVIDER_NOT_CHOSEN,
    SOURCES,
    CostNotApprovedError,
    HistoryPlan,
    carry_quotes,
    coverage,
    daily_range,
    get_source,
    index_on_grid,
    minute_grid,
    parity_spot,
    session_close,
    strike_range,
    write_history,
)
from butterfly_guy.research.market import et_us
from tests.research_synth import FakeSource, synthetic_day

D = dt.date(2023, 11, 22)  # a regular session
EARLY = dt.date(2023, 11, 24)  # the day after Thanksgiving: 13:00 close
CAL = EventCalendar()
PRIOR = [{"date": dt.date(2023, 11, 21), "underlying": "SPX", "open": 5990.0, "high": 5999.0,
          "low": 5980.0, "close": 5995.0},
         {"date": dt.date(2023, 11, 21), "underlying": "$VIX", "open": 17.0, "high": 18.0,
          "low": 16.0, "close": 17.5}]


def _updates(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["ts_us", "strike", "t", "bid", "ask"])


def _plan(tmp_path, start=D, end=EARLY, **kw) -> HistoryPlan:
    return HistoryPlan(start, end, "spx_0dte_fake", log=io.StringIO(), **kw)


# ---------------------------------------------------------------------------
# Provider marker
# ---------------------------------------------------------------------------


def test_no_provider_is_registered_and_asking_for_one_says_so():
    assert SOURCES == {}
    with pytest.raises(NotImplementedError, match="Data provider not chosen"):
        get_source("thetadata")
    assert "history-vendor-readiness.md" in PROVIDER_NOT_CHOSEN


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------


def test_minute_grid_runs_0931_to_1600_et_in_utc():
    grid = minute_grid(D)
    assert len(grid) == 390
    # 2023-11-22 is EST (UTC-5): 09:31 ET = 14:31 UTC, 16:00 ET = 21:00 UTC.
    assert grid[0] == int(dt.datetime(2023, 11, 22, 14, 31, tzinfo=dt.UTC).timestamp()) * 10**6
    assert grid[-1] == int(dt.datetime(2023, 11, 22, 21, 0, tzinfo=dt.UTC).timestamp()) * 10**6
    assert set(np.diff(grid)) == {60_000_000}


def test_early_close_ends_the_grid_at_1300_et_including_under_dst():
    assert session_close(EARLY, CAL) == dt.time(13, 0)
    assert session_close(D, CAL) == dt.time(16, 0)
    assert len(minute_grid(EARLY, session_close(EARLY, CAL))) == 210
    july = dt.date(2023, 7, 3)  # EDT (UTC-4)
    grid = minute_grid(july, session_close(july, CAL))
    assert grid[-1] == int(dt.datetime(2023, 7, 3, 17, 0, tzinfo=dt.UTC).timestamp()) * 10**6


def test_vendor_1m_profile_replays_the_written_grid_with_official_inputs(tmp_path):
    src = FakeSource({D: synthetic_day(D), EARLY: synthetic_day(EARLY, close=(13, 0))},
                     extra_bars=PRIOR)
    write_history(src, _plan(tmp_path), tmp_path)
    ds = Dataset.open("spx_0dte_fake", tmp_path)
    loader = SessionLoader(ds, PROFILES["vendor_1m"])
    assert loader.dates() == [D, EARLY]
    s = loader.load(EARLY)
    assert len(s.clock_ts) == 210 and s.clock_ts[-1] == et_us(EARLY, 13, 0)
    assert s.clock_ts[0] == et_us(EARLY, 9, 31)
    assert s.open == 5999.0  # official open, not the first grid spot
    assert s.prev_close == 6002.0  # D's official close
    regular = loader.load(D)
    assert len(regular.clock_ts) == 390 and regular.prev_close == 5995.0


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def test_quote_state_is_carried_within_the_session_with_its_age():
    grid = minute_grid(D)[:4]  # 09:31 .. 09:34
    prior_day = et_us(D - dt.timedelta(days=1), 15, 59)
    rows = carry_quotes(_updates([
        (et_us(D, 9, 30, 10), 6000.0, "C", 1.0, 1.2),
        (et_us(D, 9, 33, 30), 6000.0, "C", 1.1, 1.3),
        (prior_day, 6010.0, "C", 0.5, 0.6),  # never carried into D
        (et_us(D, 9, 32, 40), 6005.0, "P", 2.0, 2.2),  # first quote at 09:32:40
    ]), grid, D, (5600.0, 6400.0))
    c = rows[(rows["t"] == "C") & (rows["strike"] == 6000.0)]
    assert list(c["bid"]) == [1.0, 1.0, 1.0, 1.1]
    assert list(c["quote_age_s"]) == [50.0, 110.0, 170.0, 30.0]
    assert 6010.0 not in set(rows["strike"])
    p = rows[rows["t"] == "P"]
    assert list(p["ts_us"]) == list(grid[2:])  # nothing before its first quote of the day
    assert list(p["quote_age_s"]) == [20.0, 80.0]


def test_missing_crossed_and_zero_bid_quotes_are_kept_as_quoted_and_mark_is_the_mid():
    grid = minute_grid(D)[:1]
    t = et_us(D, 9, 30, 30)
    updates = _updates([
        (t, 6000.0, "C", 2.0, 1.9),  # crossed
        (t, 6005.0, "C", 0.0, 0.05),  # zero bid
        (t, 6010.0, "C", np.nan, np.nan),  # the vendor had no quote
        (t, 6002.5, "C", 1.0, 1.1),  # not an integer strike
        (t, 7000.0, "C", 0.0, 0.05),  # outside the band
    ]).assign(mark=123.0)  # a vendor mark is ignored
    rows = carry_quotes(updates, grid, D, (5600.0, 6400.0)).set_index("strike")
    assert (rows.loc[6000.0, "bid"], rows.loc[6000.0, "ask"]) == (2.0, 1.9)
    assert rows.loc[6000.0, "mark"] == pytest.approx(1.95)
    assert rows.loc[6005.0, "bid"] == 0.0 and rows.loc[6005.0, "mark"] == pytest.approx(0.025)
    assert np.isnan(rows.loc[6010.0, "bid"]) and np.isnan(rows.loc[6010.0, "mark"])
    assert 6002.5 not in rows.index and 7000.0 not in rows.index


def test_strike_band_is_integer_strikes_within_400_of_the_spot_range():
    assert strike_range(5990.3, 6011.7) == (5590.0, 6412.0)


def test_index_level_is_the_last_print_of_the_same_session():
    grid = minute_grid(D)[:3]
    bars = pd.DataFrame({"ts_us": [et_us(D - dt.timedelta(days=1), 15, 59),
                                   et_us(D, 9, 31, 30)], "price": [5000.0, 6001.0]})
    out = index_on_grid(bars, grid, D)
    assert np.isnan(out[0]) and list(out[1:]) == [6001.0, 6001.0]


def test_parity_spot_is_the_forward_at_the_closest_call_put_pair():
    strikes = np.array([5990.0, 6000.0, 6010.0])
    c = np.array([[14.0, 7.0, 3.0]])
    p = np.array([[3.5, 6.0, 12.0]])
    fields = {f"{t}_{f}": np.full((1, 3), np.nan) for t in "CP" for f in
              ("bid", "ask", "mark", "iv", "delta")}
    fields["C_mark"], fields["P_mark"] = c, p
    chain = SessionChain(D, np.array([0]), strikes, np.array([np.nan]), fields)
    assert parity_spot(chain)[0] == pytest.approx(6000.0 + 7.0 - 6.0)


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------


def test_write_history_records_every_request_and_the_quote_age(tmp_path):
    src = FakeSource({D: synthetic_day(D), EARLY: synthetic_day(EARLY, close=(13, 0))}, cost=12.5)
    m = write_history(src, _plan(tmp_path, max_cost=20.0), tmp_path)
    (h,) = m.history
    assert h["mode"] == "vendor_pull" and h["cost_estimate"] == 12.5
    assert h["holdout_sessions"] == 0 and h["sessions_added"] == [D.isoformat(), EARLY.isoformat()]
    assert h["source"]["vendor"] == "fake" and h["dataset_hash"] == m.dataset_hash
    calls = [r["call"] for r in h["requests"]]
    assert calls[:3] == ["cost_estimate", "daily_bars", "sessions"]
    q = [r for r in h["requests"] if r["call"] == "quotes"]
    assert q[0]["strikes"] == [5600.0, 6400.0]  # the band from the index range
    ds = Dataset.open("spx_0dte_fake", tmp_path)
    chain = ds.chain(D)
    assert "C_quote_age_s" in chain.fields
    age = chain.fields["C_quote_age_s"][:, chain.column(6000.0)]
    assert np.nanmax(age) < 300 and age[0] == 30.0  # 09:31 carries the 09:30:30 quote
    assert chain.fields["C_mark"][0, chain.column(5990.0)] == pytest.approx(12.0)
    assert ds.sessions()["spot_source"].tolist() == ["index", "index"]
    assert ds.verify() == []
    # A second pull adds nothing and still logs a history entry.
    m2 = write_history(FakeSource(src.days), _plan(tmp_path), tmp_path)
    assert len(m2.history) == 2 and m2.history[-1]["sessions_added"] == []
    assert m2.dataset_hash == m.dataset_hash


def test_a_session_without_index_levels_uses_the_flagged_parity_spot(tmp_path):
    src = FakeSource({D: synthetic_day(D, index=False)})
    write_history(src, _plan(tmp_path, end=D), tmp_path)
    ds = Dataset.open("spx_0dte_fake", tmp_path)
    assert ds.sessions()["spot_source"].tolist() == ["parity"]
    # Band from the official high/low when there is no index level.
    q = [c for c in src.calls if c[0] == "quotes"][0]
    assert q[2] == (5595.0, 6405.0)
    assert ds.chain(D).spot[0] == pytest.approx(6000.0)
    assert ds.clock(D).spot[0] == pytest.approx(6000.0)


def test_vendor_data_never_goes_into_the_helios_dataset(tmp_path):
    src = FakeSource({D: synthetic_day(D)})
    for name in ("spx_0dte", "other"):
        with pytest.raises(ValueError, match="its own dataset"):
            write_history(src, HistoryPlan(D, D, name, log=io.StringIO()), tmp_path)
    assert src.calls == []


def test_a_usage_billed_pull_over_the_approved_cost_stops_before_any_data(tmp_path):
    src = FakeSource({D: synthetic_day(D)}, cost=250.0)
    with pytest.raises(CostNotApprovedError, match="ask the owner"):
        write_history(src, _plan(tmp_path, end=D, max_cost=100.0), tmp_path)
    with pytest.raises(CostNotApprovedError):
        write_history(src, _plan(tmp_path, end=D), tmp_path)  # nothing approved
    assert [c[0] for c in src.calls] == ["cost_estimate", "cost_estimate"]


def test_the_daily_lookback_is_clipped_at_the_holdout_for_the_validation_window():
    (lo, hi), clipped = daily_range(HistoryPlan(dt.date(2026, 3, 13), dt.date(2026, 9, 25), "x"))
    assert clipped and lo == dt.date(2026, 3, 13) and hi == dt.date(2026, 9, 25)
    (lo, _), clipped = daily_range(HistoryPlan(dt.date(2022, 1, 3), dt.date(2024, 6, 28), "x"))
    assert not clipped and lo == dt.date(2021, 12, 24)


def test_coverage_reports_rates_and_sources(tmp_path):
    day = synthetic_day(D)
    q = day["quotes"]
    first = q["ts_us"] == q["ts_us"].min()
    q.loc[first & (q["strike"] == 6000.0) & (q["t"] == "C"), ["bid", "ask"]] = [2.2, 2.1]
    src = FakeSource({D: day})
    write_history(src, _plan(tmp_path, end=D), tmp_path)
    out = coverage(Dataset.open("spx_0dte_fake", tmp_path))
    (row,) = out["sessions"]
    assert row["timestamps"] == 390 and row["spot_source"] == "index"
    assert row["C_crossed_rate"] > 0 and row["P_crossed_rate"] == 0
    assert row["C_missing_rate"] == 0  # every quoted strike has a state from 09:31
    assert row["vix_at_10"] and row["spx_official_close"]
    assert out["summary"]["sessions"] == 1
