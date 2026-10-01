"""Data-quality gates Q1-Q6 for a vendor dataset, with the same checks run on Helios side by
side, and a matched-instant comparison of the two.

The plan, the principles (data quality first, no derived data) and the thresholds are in
`docs/research/vendor-data-quality-plan-2026-09-28.md`, approved by the owner on 2026-09-28
before any of these metrics was computed. The thresholds below are copied from it. A pass
over the whole validation window (`holdout.VALIDATION`) is recorded in the vendor dataset's
manifest history, and `history.write_history` requires it before any earlier pull.

Operational details the plan leaves open, fixed here:

- **Cells.** Chain rows from 09:31 ET to the session close; integer strikes within
  `BAND` of that row's SPX level. A cell is *quoted* when bid and ask are finite and, where
  the dataset records a quote age, the quote is at most `FRESH_S` old.
- **Q2** counts crossed quotes (bid > ask) among quoted cells.
- **Q3** checks, on quoted, uncrossed cells of one row: each pair of neighbouring strikes
  for both vertical bounds (the lower strike's call is worth at least the higher's and at
  most the strike gap more; mirrored for puts), and each 5-point butterfly. A violation is
  one you could trade at the quoted prices for a riskless credit.
- **Q4** looks at contracts within `STALE_BAND` of SPX quoted with an ask of at least
  `STALE_MIN_ASK` (amendment 2, 2026-09-28: a quote pinned at the minimum tick legitimately
  stays put). A run of rows with identical bid and ask, all within the band, starting at
  such an ask, lasting `STALE_MIN` minutes or more while SPX's range over the run is
  `STALE_MOVE` points or more, makes that contract-session stale.
- **Q5** needs SPX prints exactly on the grid minutes (the owner's bar-end minute files).
  With the call nearest the session's median SPX, it finds the lag (-3..+3 min) at which
  the call mid's 1-minute changes correlate best with SPX's. A session without exact-minute
  SPX prints (Schwab ticks land at random seconds) is *not evaluable*; with no evaluable
  session, Q5 is `n/a` and gates nothing, and it must then pass on the development data.
- **Q6** compares every session's SPX close in the vendor's `daily_bars` with Cboe's.
- **DST-change weeks** (development data): Q5's best lag is listed for every session in the
  weeks starting `DST_WEEKS`, where a time-zone mistake would show first.
- **Minute-file cross-check** (report only, no threshold): the owner's SPX and VIX files'
  daily high and low (09:31-16:00 ET, stale days excluded) against independent daily OHLC
  (Yahoo `^GSPC` for SPX, Cboe for VIX).
- **Matched instants** (report only): Helios snapshots taken 0-`MATCH_S` s after a minute
  mark against the vendor's row at that minute, and, for each disagreement beyond `TOL`,
  whether the vendor cell, the Helios cell, both or neither breaks a Q2/Q3 rule then.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import AGE_FIELD, OPTION_TYPES, Dataset, SessionChain
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.history import session_close
from butterfly_guy.research.holdout import VALIDATION, guard
from butterfly_guy.research.market import et_us

DST_WEEKS = (dt.date(2022, 3, 14), dt.date(2022, 11, 7), dt.date(2023, 3, 13),
             dt.date(2023, 11, 6), dt.date(2024, 3, 11))

PLAN = "docs/research/vendor-data-quality-plan-2026-09-28.md"
BAND = 200.0
FRESH_S = 60.0
STALE_BAND = 50.0
STALE_MIN = 30
STALE_MOVE = 10.0
STALE_MIN_ASK = 0.50  # amendment 2: below this a quote may sit at the minimum tick
LAGS = tuple(range(-3, 4))
EXACT_SHARE = 0.9  # share of grid minutes with an exact SPX print for Q5 to be evaluable
MATCH_S = 5
TOL = 0.05
MIN_US = 60_000_000
EPS = 1e-9  # float slack on price comparisons (prices are in cents)

THRESHOLDS = {
    "Q1_min_session_share": 0.99,
    "Q2_max_share": 0.001,
    "Q3_max_share": 0.001,
    "Q4_max_share": 0.001,
    "Q4_min_ask": STALE_MIN_ASK,
    "Q5_min_lag0_share": 0.95,
    "Q5_max_abs_lag": 1,
    "Q6_max_mismatches": 0,
}
CRITERIA = {
    "Q1": "Coverage: share of grid cells (09:31 -> close, integer strikes within ±200 of SPX) "
          "with a quote >= 99% per session, on every session",
    "Q2": "Crossed quotes (bid > ask) among quoted cells <= 0.1% overall",
    "Q3": "Executable arbitrage (vertical buyable for a credit or beyond its width; 5-point "
          "butterfly buyable for a credit) <= 0.1% of checks overall",
    "Q4": "Stale quotes: contract within ±50 of SPX, ask >= $0.50 (amendment 2), with bid and "
          "ask unchanged for 30+ minutes while SPX moves 10+ points <= 0.1% of "
          "contract-sessions",
    "Q5": "Timestamps: best lag of the nearest-to-SPX call's 1-minute mid changes against "
          "SPX's is 0 on >= 95% of sessions, none beyond ±1 min",
    "Q6": "Official closes equal Cboe's SPX close: 0 mismatches",
}


# ---------------------------------------------------------------------------
# One session
# ---------------------------------------------------------------------------


def _row_window(chain: SessionChain, d: dt.date, close: dt.time) -> np.ndarray:
    return (chain.ts >= et_us(d, 9, 31)) & (chain.ts <= et_us(d, close.hour, close.minute))


def _cells(chain: SessionChain, rows: np.ndarray) -> tuple[np.ndarray, dict]:
    """(in-band mask over rows x strikes, {type: quoted mask}) for the selected rows."""
    ks = chain.strikes
    spot = chain.spot[rows]
    band = (np.isfinite(spot)[:, None] & (np.abs(ks[None, :] - spot[:, None]) <= BAND)
            & (ks == np.round(ks))[None, :])
    quoted = {}
    for t in OPTION_TYPES:
        bid, ask = chain.fields[f"{t}_bid"][rows], chain.fields[f"{t}_ask"][rows]
        q = np.isfinite(bid) & np.isfinite(ask)
        age = chain.fields.get(f"{t}_observation_age_s", chain.fields.get(f"{t}_{AGE_FIELD}"))
        if age is not None:
            q &= np.nan_to_num(age[rows], nan=np.inf) <= FRESH_S
        quoted[t] = q & band
    return band, quoted


def arbitrage(bid: np.ndarray, ask: np.ndarray, ks: np.ndarray, ok: np.ndarray, t: str
              ) -> tuple[int, int, np.ndarray]:
    """(checks, violations, per-cell flag) for one type on rows x strikes. `ok` marks the
    quoted, uncrossed cells that may take part."""
    bad = np.zeros_like(ok)
    checks = violations = 0
    for j in range(len(ks) - 1):
        both = ok[:, j] & ok[:, j + 1]
        if not both.any():
            continue
        gap = ks[j + 1] - ks[j]
        lo_b, lo_a, hi_b, hi_a = bid[:, j], ask[:, j], bid[:, j + 1], ask[:, j + 1]
        if t == "C":  # C(lo) >= C(hi) and C(lo) - C(hi) <= gap
            v = (lo_a < hi_b - EPS) | (lo_b - hi_a > gap + EPS)
        else:  # P(hi) >= P(lo) and P(hi) - P(lo) <= gap
            v = (hi_a < lo_b - EPS) | (hi_b - lo_a > gap + EPS)
        v &= both
        checks += 2 * int(both.sum())
        violations += int(v.sum())
        bad[v, j] = bad[v, j + 1] = True
    pos = {float(k): i for i, k in enumerate(ks)}
    for j, k in enumerate(ks):
        lo, hi = pos.get(float(k) - 5.0), pos.get(float(k) + 5.0)
        if lo is None or hi is None:
            continue
        three = ok[:, lo] & ok[:, j] & ok[:, hi]
        v = three & (ask[:, lo] - 2 * bid[:, j] + ask[:, hi] < -EPS)
        checks += int(three.sum())
        violations += int(v.sum())
        bad[v, lo] = bad[v, j] = bad[v, hi] = True
    return checks, violations, bad


def _stale(chain: SessionChain, rows: np.ndarray, quoted: dict) -> tuple[int, int]:
    """(contract-sessions near SPX with an ask of at least `STALE_MIN_ASK`, stale ones)."""
    ts, spot, ks = chain.ts[rows], chain.spot[rows], chain.strikes
    near = np.isfinite(spot)[:, None] & (np.abs(ks[None, :] - spot[:, None]) <= STALE_BAND)
    evaluated = stale = 0
    for t in OPTION_TYPES:
        bid, ask = chain.fields[f"{t}_bid"][rows], chain.fields[f"{t}_ask"][rows]
        ok = quoted[t] & near
        priced = ok & (ask >= STALE_MIN_ASK)
        for j in np.flatnonzero(priced.any(axis=0)):
            evaluated += 1
            m, b, a = ok[:, j], bid[:, j], ask[:, j]
            start = None
            for i in range(len(ts) + 1):
                same = (i < len(ts) and m[i] and start is not None
                        and b[i] == b[start] and a[i] == a[start])
                if same:
                    continue
                if start is not None and i - 1 > start:
                    run = slice(start, i)
                    if (a[start] >= STALE_MIN_ASK
                            and ts[i - 1] - ts[start] >= STALE_MIN * MIN_US
                            and np.nanmax(spot[run]) - np.nanmin(spot[run]) >= STALE_MOVE):
                        stale += 1
                        break
                start = i if i < len(ts) and m[i] else None
    return evaluated, stale


def _lag(chain: SessionChain, rows: np.ndarray, spx: tuple[np.ndarray, np.ndarray]
         ) -> dict:
    """Q5 for one session: best lag, or why it is not evaluable. Lag L pairs the option's
    change over minute t with SPX's over minute t+L, so a negative best lag means the
    option timestamps trail SPX (quotes stamped late)."""
    grid = chain.ts[rows]
    tick_ts, tick_px = spx
    pos = np.searchsorted(tick_ts, grid)
    exact = (pos < len(tick_ts)) & (tick_ts[np.minimum(pos, len(tick_ts) - 1)] == grid)
    if len(grid) < 30 or exact.mean() < EXACT_SHARE:
        return {"evaluable": False, "reason": "no exact-minute SPX prints"}
    s = np.where(exact, tick_px[np.minimum(pos, len(tick_ts) - 1)], np.nan)
    ks = chain.strikes
    k = int(np.argmin(np.abs(ks - np.nanmedian(s))))
    mid = (chain.fields["C_bid"][rows, k] + chain.fields["C_ask"][rows, k]) / 2
    do, ds = np.diff(mid), np.diff(s)
    corr = {}
    for lag in LAGS:
        a = do[max(0, -lag):len(do) - max(0, lag)]
        b = ds[max(0, lag):len(ds) - max(0, -lag)]
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < 30 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
            continue
        corr[lag] = float(np.corrcoef(a[ok], b[ok])[0, 1])
    if not corr:
        return {"evaluable": False, "reason": "too few quoted minutes"}
    best = max(corr, key=lambda x: (corr[x], -abs(x)))
    return {"evaluable": True, "strike": float(ks[k]), "best_lag": best,
            "corr": {str(x): round(c, 4) for x, c in corr.items()}}


def session_quality(ds: Dataset, d: dt.date, calendar: EventCalendar, *, lag: bool) -> dict:
    chain = ds.chain(d)
    rows = _row_window(chain, d, session_close(d, calendar))
    band, quoted = _cells(chain, rows)
    out: dict = {"date": d.isoformat(), "rows": int(rows.sum()),
                 "cells": int(band.sum()) * len(OPTION_TYPES)}
    out["quoted"] = int(sum(q.sum() for q in quoted.values()))
    crossed = checks = violations = 0
    for t in OPTION_TYPES:
        bid, ask = chain.fields[f"{t}_bid"][rows], chain.fields[f"{t}_ask"][rows]
        x = quoted[t] & (bid > ask)
        crossed += int(x.sum())
        c, v, _ = arbitrage(bid, ask, chain.strikes, quoted[t] & ~x, t)
        checks, violations = checks + c, violations + v
    out.update(crossed=crossed, arb_checks=checks, arb_violations=violations)
    out["near_contracts"], out["stale_contracts"] = _stale(chain, rows, quoted)
    if lag:
        out["q5"] = _lag(chain, rows, ds.spot_ticks("SPX"))
    return out


# ---------------------------------------------------------------------------
# Matched instants (report only)
# ---------------------------------------------------------------------------


def _bad_cells(chain: SessionChain, rows: np.ndarray) -> dict[str, np.ndarray]:
    """Per type, cells on `rows` that are crossed or take part in a Q3 violation."""
    _, quoted = _cells(chain, rows)
    out = {}
    for t in OPTION_TYPES:
        bid, ask = chain.fields[f"{t}_bid"][rows], chain.fields[f"{t}_ask"][rows]
        x = quoted[t] & (bid > ask)
        out[t] = x | arbitrage(bid, ask, chain.strikes, quoted[t] & ~x, t)[2]
    return out


def matched_instants(vendor: Dataset, helios: Dataset, d: dt.date) -> dict:
    v, h = vendor.chain(d), helios.chain(d)
    sec = (h.ts % MIN_US) / 1e6
    minute = h.ts - (h.ts % MIN_US)
    vi = np.searchsorted(v.ts, minute)
    hit = (sec < MATCH_S) & (vi < len(v.ts)) & (v.ts[np.minimum(vi, len(v.ts) - 1)] == minute)
    counts = {"pairs": 0, "agree": 0, "vendor_only_bad": 0, "helios_only_bad": 0,
              "both_bad": 0, "neither_bad": 0}
    if not hit.any():
        return counts
    hr, vr = np.flatnonzero(hit), vi[hit]
    ks = np.intersect1d(h.strikes, v.strikes)
    hk, vk = np.searchsorted(h.strikes, ks), np.searchsorted(v.strikes, ks)
    h_rows = np.zeros(len(h.ts), dtype=bool)
    h_rows[hr] = True
    v_rows = np.zeros(len(v.ts), dtype=bool)
    v_rows[vr] = True
    hb, vb = _bad_cells(h, h_rows), _bad_cells(v, v_rows)
    # _bad_cells returns rows in ascending order; map each matched pair onto them.
    h_at = np.searchsorted(np.flatnonzero(h_rows), hr)
    v_at = np.searchsorted(np.flatnonzero(v_rows), vr)
    spot = h.spot[hr]
    near = np.isfinite(spot)[:, None] & (np.abs(ks[None, :] - spot[:, None]) <= BAND)
    for t in OPTION_TYPES:
        hbid, hask = h.fields[f"{t}_bid"][hr][:, hk], h.fields[f"{t}_ask"][hr][:, hk]
        vbid, vask = v.fields[f"{t}_bid"][vr][:, vk], v.fields[f"{t}_ask"][vr][:, vk]
        both = (near & np.isfinite(hbid) & np.isfinite(hask) & np.isfinite(vbid)
                & np.isfinite(vask))
        agree = both & (np.abs(hbid - vbid) <= TOL + EPS) & (np.abs(hask - vask) <= TOL + EPS)
        dis = both & ~agree
        h_bad = hb[t][h_at][:, hk] & dis
        v_bad = vb[t][v_at][:, vk] & dis
        counts["pairs"] += int(both.sum())
        counts["agree"] += int(agree.sum())
        counts["vendor_only_bad"] += int((v_bad & ~h_bad).sum())
        counts["helios_only_bad"] += int((h_bad & ~v_bad).sum())
        counts["both_bad"] += int((v_bad & h_bad).sum())
        counts["neither_bad"] += int((dis & ~v_bad & ~h_bad).sum())
    return counts


# ---------------------------------------------------------------------------
# Whole run
# ---------------------------------------------------------------------------


def _summary(rows: list[dict]) -> dict:
    def share(num: str, den: str) -> float | None:
        n, dd = sum(r[num] for r in rows), sum(r[den] for r in rows)
        return None if dd == 0 else n / dd

    q1 = [r["quoted"] / r["cells"] for r in rows if r["cells"]]
    floor = THRESHOLDS["Q1_min_session_share"]
    return {
        "sessions": len(rows),
        "Q1_min_session_share": min(q1) if q1 else None,
        "Q1_median_session_share": float(np.median(q1)) if q1 else None,
        "Q1_sessions_below": [r["date"] for r in rows
                              if r["cells"] and r["quoted"] / r["cells"] < floor],
        "Q2_share": share("crossed", "quoted"),
        "Q3_share": share("arb_violations", "arb_checks"),
        "Q3_checks": sum(r["arb_checks"] for r in rows),
        "Q4_share": share("stale_contracts", "near_contracts"),
        "Q4_contract_sessions": sum(r["near_contracts"] for r in rows),
    }


def _dst_week(d: dt.date) -> bool:
    return any(0 <= (d - w).days <= 4 for w in DST_WEEKS)


def _q5(rows: list[dict]) -> dict:
    dst = {r["date"]: (r["q5"].get("best_lag") if r["q5"].get("evaluable") else r["q5"]["reason"])
           for r in rows if "q5" in r and _dst_week(dt.date.fromisoformat(r["date"]))}
    ev = [r["q5"] for r in rows if r.get("q5", {}).get("evaluable")]
    if not ev:
        return {"status": "n/a", "evaluable": 0, "sessions": len(rows), "dst_weeks": dst}
    lags = [e["best_lag"] for e in ev]
    share0 = sum(x == 0 for x in lags) / len(lags)
    worst = max(abs(x) for x in lags)
    ok = share0 >= THRESHOLDS["Q5_min_lag0_share"] and worst <= THRESHOLDS["Q5_max_abs_lag"]
    return {"status": "pass" if ok else "fail", "evaluable": len(ev), "sessions": len(rows),
            "lag0_share": share0, "max_abs_lag": worst,
            "lag_counts": {str(x): lags.count(x) for x in sorted(set(lags))}, "dst_weeks": dst}


def _q6(vendor: Dataset, dates: list[dt.date], cboe_spx: pd.DataFrame) -> dict:
    bars = vendor.daily_bars()
    spx = bars[bars["underlying"] == "SPX"].set_index("date")["close"]
    cboe = dict(zip(cboe_spx["date"], cboe_spx["close"], strict=True))
    mismatches, missing = [], []
    for d in dates:
        v, c = spx.get(d), cboe.get(d)
        if v is None or c is None or not np.isfinite(v):
            missing.append(d.isoformat())
        elif round(float(v), 2) != round(float(c), 2):
            mismatches.append({"date": d.isoformat(), "vendor": float(v), "cboe": float(c)})
    return {"compared": len(dates) - len(missing), "mismatches": mismatches, "missing": missing}


def run(vendor: Dataset, helios: Dataset, start: dt.date, end: dt.date,
        cboe_spx: pd.DataFrame) -> dict:
    """All gates on `vendor`, Q1-Q4 on `helios` side by side, and the matched instants."""
    guard(start, end, what="vendor-quality", dataset=vendor.name)
    cal = EventCalendar()
    v_dates = [d for d in vendor.sessions()["date"] if start <= d <= end]
    h_dates = [d for d in helios.sessions()["date"] if start <= d <= end]
    v_rows = [session_quality(vendor, d, cal, lag=True) for d in v_dates]
    h_rows = [session_quality(helios, d, cal, lag=False) for d in h_dates]
    both = sorted(set(v_dates) & set(h_dates))
    match = {k: 0 for k in ("pairs", "agree", "vendor_only_bad", "helios_only_bad",
                            "both_bad", "neither_bad")}
    for d in both:
        for k, n in matched_instants(vendor, helios, d).items():
            match[k] += n
    vs, hs = _summary(v_rows), _summary(h_rows)
    q5, q6 = _q5(v_rows), _q6(vendor, v_dates, cboe_spx)
    t = THRESHOLDS
    gates = {
        "Q1": vs["Q1_min_session_share"] is not None
        and vs["Q1_min_session_share"] >= t["Q1_min_session_share"],
        "Q2": vs["Q2_share"] is not None and vs["Q2_share"] <= t["Q2_max_share"],
        "Q3": vs["Q3_share"] is not None and vs["Q3_share"] <= t["Q3_max_share"],
        "Q4": vs["Q4_share"] is not None and vs["Q4_share"] <= t["Q4_max_share"],
        "Q5": None if q5["status"] == "n/a" else q5["status"] == "pass",
        "Q6": not q6["mismatches"] and not q6["missing"],
    }
    passed = bool(v_dates) and all(g is not False for g in gates.values())
    return {
        "plan": PLAN, "criteria": CRITERIA, "thresholds": THRESHOLDS,
        "range": [start.isoformat(), end.isoformat()],
        "full_validation_window": (start, end) == VALIDATION,
        "meta": {"vendor": {"dataset": vendor.name, "dataset_hash": vendor.hash},
                 "helios": {"dataset": helios.name, "dataset_hash": helios.hash}},
        "gates": gates, "pass": passed,
        "vendor": {"summary": vs, "q5": q5, "q6": q6, "sessions": v_rows},
        "helios": {"summary": hs, "sessions": h_rows},
        "matched_instants": {**match, "agree_share": (match["agree"] / match["pairs"]
                                                      if match["pairs"] else None)},
    }


def index_file_crosscheck(minutes: dict[str, pd.DataFrame], daily: dict[str, pd.DataFrame],
                          start: dt.date, end: dt.date) -> dict:
    """Report only: per symbol, the minute file's daily high/low (`minutes[sym]`: rows `date,
    high, low` from `thetadata.load_minute_file`) against independent daily OHLC
    (`daily[sym]`: `date, high, low`)."""
    out = {}
    for sym, m in minutes.items():
        m = m[(m["date"] >= start) & (m["date"] <= end)]
        mine = m.groupby("date").agg(high=("high", "max"), low=("low", "min"))
        ref = daily.get(sym)
        if ref is None or mine.empty:
            out[sym] = {"compared": 0}
            continue
        j = mine.join(ref.set_index("date")[["high", "low"]], rsuffix="_ref", how="inner")
        dh, dl = (j["high"] - j["high_ref"]).abs(), (j["low"] - j["low_ref"]).abs()
        rel = pd.concat([dh / j["high_ref"], dl / j["low_ref"]], axis=1).max(axis=1)
        worst = rel.sort_values(ascending=False).head(10)
        out[sym] = {
            "compared": len(j), "file_days_without_reference": int(len(mine) - len(j)),
            "high_abs_diff": {"median": round(float(dh.median()), 4),
                              "p99": round(float(dh.quantile(0.99)), 4)},
            "low_abs_diff": {"median": round(float(dl.median()), 4),
                             "p99": round(float(dl.quantile(0.99)), 4)},
            "days_over_0.5pct": int((rel > 0.005).sum()),
            "worst": {d.isoformat(): round(float(x), 5) for d, x in worst.items()},
        }
    return out


def history_entry(results: dict, run_id: str, at: str) -> dict:
    """The manifest `history` record of a run (no `holdout_sessions` key: it registers
    nothing for the unseal). Only a pass over the whole validation window opens earlier
    pulls (`history.quality_passed` checks the range)."""
    return {"at": at, "mode": "vendor_quality", "run_id": run_id, "range": results["range"],
            "pass": results["pass"],
            "gates": results["gates"], "dataset_hash": results["meta"]["vendor"]["dataset_hash"],
            "helios_dataset_hash": results["meta"]["helios"]["dataset_hash"], "plan": PLAN}


def _pct(x: float | None, digits: int = 3) -> str:
    return "—" if x is None else f"{100 * x:.{digits}f}%"


def markdown(results: dict, provenance: dict) -> str:
    v, h = results["vendor"], results["helios"]
    vs, hs = v["summary"], h["summary"]
    g = results["gates"]

    def res(key: str) -> str:
        return "n/a" if g[key] is None else ("PASS" if g[key] else "FAIL")

    q5 = v["q5"]
    q5m = ("not evaluable (no exact-minute SPX prints)" if q5["status"] == "n/a" else
           f"lag 0 on {_pct(q5['lag0_share'], 1)} of {q5['evaluable']}; max |lag| "
           f"{q5['max_abs_lag']}; {q5['lag_counts']}")
    m = results["matched_instants"]
    x = results.get("index_files_crosscheck")
    extra = []
    if q5.get("dst_weeks"):
        extra += ["", "## Q5 on DST-change weeks", "",
                  "Best lag per session (0 = aligned; a string = not evaluable): "
                  + ", ".join(f"{d}: {v}" for d, v in sorted(q5["dst_weeks"].items())) + "."]
    if x:
        extra += ["", "## Minute-file cross-check (report only)", ""]
        for sym, r in x.items():
            if sym == "sources":
                continue
            if not r.get("compared"):
                extra.append(f"- {sym}: {r}")
                continue
            extra.append(
                f"- {sym}: {r['compared']} days; |Δhigh| median {r['high_abs_diff']['median']}, "
                f"p99 {r['high_abs_diff']['p99']}; |Δlow| median {r['low_abs_diff']['median']}, "
                f"p99 {r['low_abs_diff']['p99']}; days over 0.5%: {r['days_over_0.5pct']}; "
                f"worst: {r['worst']}")
    lines = [
        f"# Vendor data quality ({provenance['run_id']})", "",
        f"- Vendor: `{results['meta']['vendor']['dataset']}` @ "
        f"`{results['meta']['vendor']['dataset_hash'][:12]}`; Helios: "
        f"`{results['meta']['helios']['dataset']}` @ "
        f"`{results['meta']['helios']['dataset_hash'][:12]}`",
        f"- Range: {results['range'][0]} → {results['range'][1]}; vendor sessions "
        f"{vs['sessions']}, Helios sessions {hs['sessions']}.",
        f"- Thresholds: `{PLAN}` (approved 2026-09-28, before any metric was computed).",
        f"- **Overall: {'PASS' if results['pass'] else 'FAIL'}**"
        + ("" if results["full_validation_window"] else
           " (not the full validation window: it does not open earlier pulls)") + ".", "",
        "| Gate | Criterion | Vendor | Helios (report only) | Result |",
        "|---|---|---|---|---|",
        f"| Q1 | {CRITERIA['Q1']} | min {_pct(vs['Q1_min_session_share'])}, median "
        f"{_pct(vs['Q1_median_session_share'])}; below: {vs['Q1_sessions_below'] or 'none'} | "
        f"min {_pct(hs['Q1_min_session_share'])}, median {_pct(hs['Q1_median_session_share'])} "
        f"| {res('Q1')} |",
        f"| Q2 | {CRITERIA['Q2']} | {_pct(vs['Q2_share'], 4)} | {_pct(hs['Q2_share'], 4)} | "
        f"{res('Q2')} |",
        f"| Q3 | {CRITERIA['Q3']} | {_pct(vs['Q3_share'], 4)} of {vs['Q3_checks']:,} | "
        f"{_pct(hs['Q3_share'], 4)} of {hs['Q3_checks']:,} | {res('Q3')} |",
        f"| Q4 | {CRITERIA['Q4']} | {_pct(vs['Q4_share'], 3)} of {vs['Q4_contract_sessions']:,} "
        f"| {_pct(hs['Q4_share'], 3)} of {hs['Q4_contract_sessions']:,} | {res('Q4')} |",
        f"| Q5 | {CRITERIA['Q5']} | {q5m} | — | {res('Q5')} |",
        f"| Q6 | {CRITERIA['Q6']} | {v['q6']['compared']} compared, "
        f"{len(v['q6']['mismatches'])} mismatches, {len(v['q6']['missing'])} missing | — | "
        f"{res('Q6')} |", "",
        "## Matched instants (report only)", "",
        f"Helios snapshots 0–{MATCH_S} s after a minute mark vs the vendor's row at that minute, "
        f"integer strikes within ±{BAND:.0f} of Helios SPX: {m['pairs']:,} pairs quoted in "
        f"both; {_pct(m['agree_share'], 2)} agree within ${TOL:.2f} on bid and ask. "
        f"Disagreements where a Q2/Q3 rule is broken by: the vendor only "
        f"{m['vendor_only_bad']:,}; Helios only {m['helios_only_bad']:,}; both "
        f"{m['both_bad']:,}; neither {m['neither_bad']:,}.",
        *extra,
    ]
    return "\n".join(lines) + "\n"
