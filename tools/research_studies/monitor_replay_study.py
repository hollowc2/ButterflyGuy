"""Exploratory: do one-poll quote glitches drive live peaks and drawdown exits?

The live position monitor values the fly from REST chain polls about every 2.6 s and
stores each poll's three legs in `monitoring_leg_quotes`. Exit rules were tuned on
1-minute data. This replays the runtime `PeakTrailer` (research.exits, the same rule code
and config) over the stored polls of closed SPX trades and compares:

- live:      raw polls, configured confirmation (must reproduce the recorded exits)
- legfilter: drop polls with a leg whose spread blows out vs that leg's recent spreads
- conf2/3:   two or three consecutive polls beyond the threshold
- med5:      causal median of the last five poll marks (~13 s)
- minute:    only the last poll in each clock minute (the backtest cadence)
- legfilter+conf2

After the recorded exit a variant still holding continues on post-exit polls
(`post_exit_leg_quotes`, recorded since migration 012) when the trade has them, else on the
1-minute collector snapshots; then cash settlement at the last snapshot spot (approximate).

Input: a directory with trades.csv.gz, polls.csv.gz, minute.csv.gz and optionally
post_exit.csv.gz (same columns as polls, minus peak/drawdown) extracted from the
SPX database (see the 2026-11-16 study note). Reads only those files.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from butterfly_guy.research.entry import load_spx_config
from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.exits import Observation, PeakTrailer

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "reports/research/spx-monitor-replay-20261116"
ET = ZoneInfo("America/New_York")
COMMISSION = 4 * 1.15 / 100  # per fly side, points (paper_commission_per_contract)
LEG_SPREAD_FLOOR, LEG_SPREAD_MULT, LEG_HISTORY = 0.50, 4.0, 30
VARIANTS = ("live", "legfilter", "conf2", "conf3", "med5", "minute", "legfilter+conf2")


def legs_wide(df: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """One row per (trade, ts) with lower/center/upper bid/ask/mark."""
    t = trades.set_index("id")
    df = df.join(t[["lower_strike", "center_strike", "upper_strike"]], on="trade_id")
    df["leg"] = np.select(
        [df.strike == df.lower_strike, df.strike == df.center_strike,
         df.strike == df.upper_strike], ["lo", "ce", "up"], "x")
    df = df[df.leg != "x"]
    w = df.pivot_table(index=["trade_id", "ts"], columns="leg",
                       values=["bid", "ask", "mark"], aggfunc="last")
    w.columns = [f"{leg}_{f}" for f, leg in w.columns]
    spot = df.groupby(["trade_id", "ts"]).spot_price.last()
    w = w.join(spot).reset_index().dropna(subset=[f"{x}_{f}" for x in ("lo", "ce", "up")
                                                  for f in ("bid", "ask", "mark")])
    w["mark"] = w.lo_mark + w.up_mark - 2 * w.ce_mark
    w["credit"] = w.lo_bid + w.up_bid - 2 * w.ce_ask
    for x in ("lo", "ce", "up"):
        w[f"{x}_spr"] = w[f"{x}_ask"] - w[f"{x}_bid"]
    return w.sort_values(["trade_id", "ts"])


def leg_filter_ok(p: pd.DataFrame) -> np.ndarray:
    """Causal: reject a poll when any leg is crossed or its spread exceeds
    max(floor, mult x median of that leg's previous accepted spreads)."""
    ok = np.ones(len(p), bool)
    hist: dict[str, list[float]] = {"lo": [], "ce": [], "up": []}
    for i, row in enumerate(p.itertuples(index=False)):
        bad = False
        for x in ("lo", "ce", "up"):
            s = getattr(row, f"{x}_spr")
            if s < 0:
                bad = True
            elif len(hist[x]) >= 5:
                if s > max(LEG_SPREAD_FLOOR, LEG_SPREAD_MULT * float(np.median(hist[x]))):
                    bad = True
        ok[i] = not bad
        if not bad:
            for x in ("lo", "ce", "up"):
                hist[x] = (hist[x] + [getattr(row, f"{x}_spr")])[-LEG_HISTORY:]
    return ok


def settlement(tr, spot: float) -> float:
    lo, ce, up = tr.lower_strike, tr.center_strike, tr.upper_strike
    if tr.direction == "PUT":
        v = max(lo - spot, 0) - 2 * max(ce - spot, 0) + max(up - spot, 0)
    else:
        v = max(spot - lo, 0) - 2 * max(spot - ce, 0) + max(spot - up, 0)
    return max(0.0, v)


def replay(tr, polls: pd.DataFrame, minute: pd.DataFrame, rule: PeakTrailer,
           variant: str) -> dict:
    entry = float(tr.entry_price)
    entry_us = pd.Timestamp(tr.entry_time).value // 1000
    d = pd.Timestamp(tr.entry_time).tz_convert(ET).date()
    open_us = pd.Timestamp(dt_et(d, 9, 30)).value // 1000
    close_us = pd.Timestamp(dt_et(d, 16, 0)).value // 1000
    p = polls
    ok = np.ones(len(p), bool)
    if "legfilter" in variant:
        ok = leg_filter_ok(p)
    if variant == "minute":
        keep = p.ts.dt.floor("min")
        ok = ~keep.duplicated(keep="last").to_numpy()
    vals = p.mark.to_numpy(float)
    if variant == "med5":
        vals = pd.Series(vals).rolling(5, min_periods=1).median().to_numpy()
    if variant in ("conf2", "legfilter+conf2"):
        rule = dataclasses.replace(rule, confirmation_polls=2)
    if variant == "conf3":
        rule = dataclasses.replace(rule, confirmation_polls=3)
    memo: dict = {}
    peak = entry
    seq = [(int(t.value // 1000), v, c, "poll") for t, v, c, k in
           zip(p.ts, vals, p.credit, ok, strict=True) if k]
    last_poll = p.ts.iloc[-1].value // 1000 if len(p) else entry_us
    seq += [(int(t.value // 1000), v, c, "minute") for t, v, c in
            zip(minute.ts, minute.mark, minute.credit, strict=True)
            if t.value // 1000 > last_poll]
    for ts, v, credit, src in seq:
        if ts > close_us or not np.isfinite(v):
            continue
        value = max(0.0, float(v))
        peak = max(peak, value)
        obs = Observation(ts_us=ts, minutes_since_open=(ts - open_us) / 60e6,
                          minutes_to_close=(close_us - ts) / 60e6,
                          entry_age_minutes=(ts - entry_us) / 60e6,
                          value=value, peak=peak, entry_price=entry)
        why = rule.reason(obs, memo)
        if why:
            return {"reason": why, "ts_us": ts, "src": src, "peak": peak, "exit_mark": value,
                    "pnl_mid": value - entry - COMMISSION,
                    "pnl_bid": max(float(credit), 0.0) - entry - COMMISSION}
    spot = float(minute.spot_price.iloc[-1]) if len(minute) else float(p.spot_price.iloc[-1])
    s = settlement(tr, spot)
    return {"reason": "cash_settled", "ts_us": None, "src": "settle", "peak": max(peak, s),
            "exit_mark": s, "pnl_mid": s - entry, "pnl_bid": s - entry}


def dt_et(d, h, m):
    import datetime as dt
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ET)


def spike_stats(p: pd.DataFrame) -> dict:
    """Is the raw peak poll an isolated spike vs its +/-3 neighbours?"""
    m = p.mark.to_numpy(float)
    if len(m) < 7:
        return {"peak_spike": False, "peak_excess": 0.0}
    i = int(np.nanargmax(m))
    nb = np.r_[m[max(0, i - 3):i], m[i + 1:i + 4]]
    ref = float(np.nanmax(nb)) if len(nb) else m[i]
    excess = m[i] - ref
    return {"peak_spike": bool(excess > max(0.30, 0.15 * ref)), "peak_excess": float(excess)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    trades = pd.read_csv(a.data / "trades.csv.gz", parse_dates=["entry_time", "exit_time"])
    raw = pd.read_csv(a.data / "polls.csv.gz", parse_dates=["ts"])
    mraw = pd.read_csv(a.data / "minute.csv.gz", parse_dates=["ts"])
    polls = legs_wide(raw, trades)
    minute = legs_wide(mraw, trades)
    post_path = a.data / "post_exit.csv.gz"
    post = (legs_wide(pd.read_csv(post_path, parse_dates=["ts"]), trades)
            if post_path.exists() else minute.iloc[0:0])
    # Stale repeats: every leg's bid/ask identical to the previous poll (cache reuse).
    cols = [f"{x}_{f}" for x in ("lo", "ce", "up") for f in ("bid", "ask")]
    rule = PeakTrailer.from_config(load_spx_config())
    rows = []
    for tr in trades.itertuples(index=False):
        p = polls[polls.trade_id == tr.id].reset_index(drop=True)
        pe = post[post.trade_id == tr.id].reset_index(drop=True)
        mi = pe if len(pe) else minute[minute.trade_id == tr.id].reset_index(drop=True)
        if len(p) < 10:
            continue
        stale = float((p[cols].diff().abs().sum(axis=1) == 0).iloc[1:].mean())
        row = {"trade_id": tr.id, "date": str(tr.trade_date), "entry": tr.entry_price,
               "db_reason": tr.exit_reason, "db_exit": str(tr.exit_time),
               "db_pnl": tr.pnl, "db_peak": tr.peak_value, "polls": len(p),
               "stale_share": round(stale, 3),
               "continuation": "post_exit_polls" if len(pe) else "minute",
               "poll_gap_med": float(p.ts.diff().dt.total_seconds().median()),
               "filtered_share": round(1 - float(leg_filter_ok(p).mean()), 4),
               **spike_stats(p)}
        for v in VARIANTS:
            r = replay(tr, p, mi, rule, v)
            row.update({f"{v}_{k}": r[k] for k in ("reason", "ts_us", "src", "peak",
                                                   "exit_mark", "pnl_mid", "pnl_bid")})
        rows.append(row)
    df = pd.DataFrame(rows)
    db_us = pd.to_datetime(df.db_exit, utc=True, format="ISO8601").astype("datetime64[us, UTC]").astype("int64")
    df["live_match"] = ((df.live_reason == df.db_reason)
                        & ((df.live_ts_us.isna() & (df.db_reason == "cash_settled"))
                           | ((df.live_ts_us - db_us).abs() <= 10e6)))
    a.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "trades.csv", index=False)

    s: dict = {"trades": len(df), "live_replay_matches_db": int(df.live_match.sum()),
               "stale_share_median": float(df.stale_share.median()),
               "poll_gap_median_s": float(df.poll_gap_med.median()),
               "polls_rejected_by_legfilter_share": float(df.filtered_share.mean()),
               "peak_is_one_poll_spike": int(df.peak_spike.sum())}
    m = df[df.live_match]
    s["matched"] = len(m)
    s["continuation_on_post_exit_polls"] = int((m.continuation == "post_exit_polls").sum())
    idx = block_bootstrap_indices(len(m), 5000, 5, seed=20261116)
    for v in VARIANTS:
        out = {}
        for col in ("pnl_mid", "pnl_bid"):
            x = m[f"{v}_{col}"].to_numpy(float) * 100
            base = m[f"live_{col}"].to_numpy(float) * 100
            diff = x - base
            boot = diff[idx].mean(axis=1)
            out[col] = {"total": round(float(x.sum())), "mean": round(float(x.mean()), 1),
                        "diff_vs_live_total": round(float(diff.sum())),
                        "diff_ci95_per_trade": [round(float(np.percentile(boot, q)), 1)
                                                for q in (2.5, 97.5)]}
        out["exits_changed"] = int((m[f"{v}_ts_us"].fillna(-1)
                                    != m["live_ts_us"].fillna(-1)).sum())
        out["held_to_settle"] = int((m[f"{v}_reason"] == "cash_settled").sum())
        out["continued_on_minute_data"] = int((m[f"{v}_src"] == "minute").sum())
        s[v] = out
    (a.out / "summary.json").write_text(json.dumps(s, indent=2))
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
