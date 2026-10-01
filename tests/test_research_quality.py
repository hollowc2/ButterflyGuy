"""Data-quality gates Q1-Q6 on synthetic, arbitrage-free 1-minute days."""

from __future__ import annotations

import datetime as dt
import io

import numpy as np
import pandas as pd
import pytest

from butterfly_guy.research import quality
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.history import HistoryPlan, quality_passed, write_history
from butterfly_guy.research.holdout import VALIDATION
from butterfly_guy.research.market import et_us
from tests.research_synth import FakeSource

D1, D2 = dt.date(2026, 3, 16), dt.date(2026, 3, 17)
STRIKES = np.arange(5800.0, 6201.0, 5.0)


def _value(s: float, k: np.ndarray, t: str) -> np.ndarray:
    """Convex, monotone and slope-bounded in the strike: no arbitrage at any spread."""
    x = (s - k) / 5.0 if t == "C" else (k - s) / 5.0
    return 5.0 * np.logaddexp(0.0, x) + 1.0


def _day(d: dt.date, *, option_lag: int = 0, freeze: tuple[float, str] | None = None,
         crossed: int = 0, gap: tuple[float, ...] = ()) -> dict:
    """Quotes every minute 09:30-16:00; SPX a seeded random walk printed exactly on each
    minute (bar end), rising 15 points over minutes 60-110."""
    n = 391
    ts = et_us(d, 9, 30) + np.arange(n, dtype=np.int64) * 60_000_000
    steps = np.random.default_rng(d.toordinal()).normal(0.0, 1.0, n)
    steps[60:110] += 0.3
    spot = 6000.0 + np.cumsum(steps)
    rows = []
    for i in range(n):
        s = spot[max(0, i - option_lag)]
        for t in ("C", "P"):
            mid = _value(s, STRIKES, t)
            bid, ask = mid - 0.05, mid + 0.05
            for j, k in enumerate(STRIKES):
                if k in gap and 100 <= i < 200:
                    continue
                b, a = bid[j], ask[j]
                if freeze and freeze == (k, t) and 60 <= i < 110:
                    b, a = rows_frozen.setdefault((k, t), (b, a))
                if crossed and t == "C" and j < crossed and i == 50:
                    b, a = a + 0.10, b
                rows.append((int(ts[i]), float(k), t, float(b), float(a)))
    return {
        "quotes": pd.DataFrame(rows, columns=["ts_us", "strike", "t", "bid", "ask"]),
        "spx": pd.DataFrame({"ts_us": ts, "price": spot}),
        "vix": pd.DataFrame({"ts_us": ts, "price": 18.0}),
        "bars": [{"date": d, "underlying": "SPX", "open": spot[0], "high": spot.max(),
                  "low": spot.min(), "close": round(float(spot[-1]), 2)},
                 {"date": d, "underlying": "$VIX", "open": 18.0, "high": 18.0, "low": 18.0,
                  "close": 18.0}],
    }


rows_frozen: dict = {}


def _write(tmp_path, days: dict, name: str = "spx_0dte_fake") -> Dataset:
    rows_frozen.clear()
    prior = [{"date": dt.date(2026, 3, 13), "underlying": u, "open": 1.0, "high": 1.0,
              "low": 1.0, "close": 1.0} for u in ("SPX", "$VIX")]
    write_history(FakeSource(days, extra_bars=prior),
                  HistoryPlan(min(days), max(days), name, log=io.StringIO()), tmp_path)
    return Dataset.open(name, tmp_path)


def _cboe(ds: Dataset) -> pd.DataFrame:
    b = ds.daily_bars()
    return b[b["underlying"] == "SPX"][["date", "close"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Single checks
# ---------------------------------------------------------------------------


def test_arbitrage_flags_executable_violations_only():
    ks = np.array([6000.0, 6005.0, 6010.0])
    ok = np.ones((1, 3), dtype=bool)
    # A 0.05 / 0.10 / 0.05 fly nets exactly zero at the quotes: not a violation.
    bid, ask = np.array([[0.0, 0.05, 0.0]]), np.array([[0.05, 0.10, 0.05]])
    checks, v, _ = quality.arbitrage(bid, ask, ks, ok, "C")
    assert v == 0 and checks == 2 * 2 + 1
    # Higher call bid above the lower call ask: buy 6000, sell 6005 for a credit.
    bid, ask = np.array([[3.0, 3.2, 1.0]]), np.array([[3.1, 3.3, 1.1]])
    _, v, bad = quality.arbitrage(bid, ask, ks, ok, "C")
    assert v >= 1 and bad[0, 0] and bad[0, 1]
    # A vertical worth more than its width.
    bid, ask = np.array([[9.0, 3.0, 1.0]]), np.array([[9.1, 3.1, 1.1]])
    assert quality.arbitrage(bid, ask, ks, ok, "C")[1] >= 1
    # A butterfly buyable for a credit (put side).
    bid, ask = np.array([[1.0, 3.0, 5.0]]), np.array([[1.1, 3.1, 5.1]])
    assert quality.arbitrage(bid, ask, ks, ok, "P")[1] == 0
    bid, ask = np.array([[1.0, 3.9, 5.0]]), np.array([[1.1, 4.0, 5.1]])
    assert quality.arbitrage(bid, ask, ks, ok, "P")[1] == 1


def test_a_clean_day_passes_every_gate(tmp_path):
    ds = _write(tmp_path, {D1: _day(D1), D2: _day(D2)})
    r = quality.run(ds, ds, D1, D2, _cboe(ds))
    assert r["gates"] == {"Q1": True, "Q2": True, "Q3": True, "Q4": True, "Q5": True,
                          "Q6": True}
    assert r["pass"] is True
    s = r["vendor"]["summary"]
    assert s["Q1_min_session_share"] == 1.0 and s["Q2_share"] == 0 and s["Q3_share"] == 0
    assert r["vendor"]["q5"]["lag_counts"] == {"0": 2}
    # Compared with itself at the exact minute, every pair agrees.
    m = r["matched_instants"]
    assert m["pairs"] > 0 and m["agree_share"] == 1.0
    assert r["full_validation_window"] is False
    entry = quality.history_entry(r, "abc", "t")
    assert entry["pass"] is True and not quality_passed(type("M", (), {"history": [entry]}))


def test_coverage_crossed_stale_and_timestamp_failures_are_caught(tmp_path):
    gap = (5990.0, 5995.0, 6000.0, 6005.0, 6010.0)
    ds = _write(tmp_path, {D1: _day(D1, gap=gap, crossed=3, freeze=(6020.0, "C")),
                           D2: _day(D2, option_lag=2)})
    r = quality.run(ds, ds, D1, D2, _cboe(ds))
    s = r["vendor"]["summary"]
    assert s["Q1_sessions_below"] == [D1.isoformat()]  # 5 strikes unquoted for 100 minutes
    assert s["Q2_share"] > 0
    assert r["vendor"]["sessions"][0]["stale_contracts"] == 1
    assert r["vendor"]["q5"]["lag_counts"] == {"-2": 1, "0": 1}  # quotes trail SPX by 2
    assert r["gates"]["Q1"] is False and r["gates"]["Q4"] is False
    assert r["gates"]["Q5"] is False and r["pass"] is False


def test_q5_is_not_evaluable_without_exact_minute_spx_prints(tmp_path):
    day = _day(D1)
    day["spx"] = day["spx"].assign(ts_us=day["spx"]["ts_us"] - 17_000_000)  # off-minute ticks
    ds = _write(tmp_path, {D1: day})
    r = quality.run(ds, ds, D1, D1, _cboe(ds))
    assert r["vendor"]["q5"]["status"] == "n/a"
    assert r["gates"]["Q5"] is None and r["pass"] is True  # n/a gates nothing


def test_q6_catches_a_close_that_differs_from_cboe(tmp_path):
    ds = _write(tmp_path, {D1: _day(D1)})
    cboe = _cboe(ds).assign(close=lambda x: x["close"] + 0.01)
    r = quality.run(ds, ds, D1, D1, cboe)
    assert r["gates"]["Q6"] is False and len(r["vendor"]["q6"]["mismatches"]) == 1


def test_only_a_full_window_pass_opens_earlier_pulls(tmp_path):
    ds = _write(tmp_path, {D1: _day(D1)})
    r = quality.run(ds, ds, D1, D1, _cboe(ds))
    r_full = {**r, "range": [VALIDATION[0].isoformat(), VALIDATION[1].isoformat()],
              "full_validation_window": True}
    ds.manifest.history.append(quality.history_entry(r, "a", "t"))
    assert not quality_passed(ds.manifest)
    entry = quality.history_entry(r_full, "b", "t")
    assert "holdout_sessions" not in entry  # registers nothing for the unseal
    ds.manifest.history.append(entry)
    assert quality_passed(ds.manifest)


def test_a_quality_run_never_reads_the_holdout(tmp_path):
    ds = _write(tmp_path, {D1: _day(D1)})
    with pytest.raises(Exception, match="holdout"):
        quality.run(ds, ds, dt.date(2026, 3, 1), D1, _cboe(ds))


def test_q4_ignores_quotes_pinned_near_the_minimum_tick():
    from butterfly_guy.research.dataset import SessionChain

    n = 45
    ts = et_us(D1, 14, 0) + np.arange(n, dtype=np.int64) * 60_000_000
    spot = 6000.0 + np.linspace(0.0, 12.0, n)
    ks = np.array([6030.0])

    def chain(bid: float, ask: float) -> SessionChain:
        f = {f"{t}_{x}": np.full((n, 1), np.nan) for t in "CP" for x in ("bid", "ask")}
        f["C_bid"][:], f["C_ask"][:] = bid, ask
        return SessionChain(D1, ts, ks, spot, f)

    rows = np.ones(n, dtype=bool)
    for (bid, ask), expected in (((0.05, 0.10), (0, 0)), ((1.00, 1.10), (1, 1))):
        c = chain(bid, ask)
        _, quoted = quality._cells(c, rows)
        assert quality._stale(c, rows, quoted) == expected


def test_dst_weeks_are_listed_and_the_minute_file_crosscheck_reports_differences():
    rows = [{"date": "2022-03-15", "q5": {"evaluable": True, "best_lag": 0}},
            {"date": "2022-03-22", "q5": {"evaluable": True, "best_lag": 0}}]
    assert quality._q5(rows)["dst_weeks"] == {"2022-03-15": 0}
    d = dt.date(2022, 3, 15)
    minutes = {"SPX": pd.DataFrame({"date": [d, d], "high": [4300.0, 4310.0],
                                    "low": [4290.0, 4280.0]})}
    ref = {"SPX": pd.DataFrame({"date": [d], "high": [4310.5], "low": [4280.0]})}
    r = quality.index_file_crosscheck(minutes, ref, d, d)["SPX"]
    assert r["compared"] == 1 and r["high_abs_diff"]["median"] == 0.5
    assert r["low_abs_diff"]["median"] == 0.0 and r["days_over_0.5pct"] == 0
