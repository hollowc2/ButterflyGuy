"""Trail start/basis comparison: current peak-value trailer vs Ernie's (@0DTE) rule.

Same entries and accounting as baseline.py; only the exit rule changes.
  arm    : trail activates once peak mark >= arm * entry (1.0 = any profit, 1.75 = +75%)
  basis  : "value"  -> exit when (peak - v) / peak >= thr
           "profit" -> exit when (peak - v) >= thr * (peak - entry)
  sched  : ((minutes_after_open_limit, thr), ...)
Run from this directory: python trail_compare.py 2026-03-13 2026-09-18
"""
import csv
import datetime as dt
import sys
from collections import Counter

import numpy as np

from baseline import baseline_entry, mkt
from sim import COMM, DayView, _mins, summarize

OURS = ((120, 0.60), (240, 0.90), (10_000, 0.75))
ERNIE = ((120, 0.75), (270, 0.45), (10_000, 0.20))  # 9:30-11:30, 11:30-14:00, 14:00-close
VARIANTS = {
    "B  ours (value, any profit)": dict(arm=1.0, basis="value", sched=OURS),
    "T1 ours + start at +75%": dict(arm=1.75, basis="value", sched=OURS),
    "T2 Ernie giveback, any profit": dict(arm=1.0, basis="profit", sched=ERNIE),
    "T3 Ernie full (+75%, giveback)": dict(arm=1.75, basis="profit", sched=ERNIE),
}
H2_START = dt.date(2026, 6, 19)


def exit_variant(dv, t, arm, basis, sched, floor_at=None):
    """floor_at: once peak >= floor_at * entry, also exit if the mark falls to entry (breakeven)."""
    m, ask, bid = t.meta.pop("paths")
    e = t.entry_mid
    peak, trig, n = e, None, len(m)
    for j in range(t.entry_i + 1, n):
        if not np.isfinite(m[j]):
            continue
        v = max(0.0, m[j])
        peak = max(peak, v)
        if floor_at is not None and peak >= floor_at * e and v <= e:
            trig = j
            t.meta["floor"] = True
            break
        if peak > e and peak >= arm * e:
            thr = next(th for lim, th in sched if _mins(dv, j) < lim)
            given = (peak - v) / peak if basis == "value" else (peak - v) / (peak - e)
            if given >= thr:
                trig = j
                break
    t.peak = peak
    if trig is None:
        t.exit_reason = "settled"
        t.exit_mid = t.exit_mkt = t.fly.settle(dv.settle)
        return t
    t.exit_reason, t.exit_i = "trail", trig
    t.exit_mid = max(0.05, m[trig] - COMM)
    jj = trig
    while jj < n and not np.isfinite(bid[jj]):
        jj += 1
    t.exit_mkt = (bid[jj] - COMM) if jj < n else t.fly.settle(dv.settle)
    return t


def main(lo, hi):
    days = [d for d in mkt.dates if lo <= d <= hi]
    per_trade = {}
    for name, kw in VARIANTS.items():
        trades = []
        for d in days:
            dv = DayView(mkt, d)
            t = baseline_entry(dv)
            if t:
                trades.append(exit_variant(dv, t, **kw))
        print(f"\n=== {name}")
        for model in ("mid", "mkt", "stress"):
            print(" ", summarize(trades, model, model))
        h1 = sum(t.pnl("stress") or 0 for t in trades if t.d < H2_START)
        h2 = sum(t.pnl("stress") or 0 for t in trades if t.d >= H2_START)
        tr = [t.pnl("stress") for t in trades if t.exit_reason == "trail" and t.pnl("stress") is not None]
        st = [t.pnl("stress") for t in trades if t.exit_reason == "settled" and t.pnl("stress") is not None]
        print(f"  stress H1 {h1:,.0f}  H2 {h2:,.0f}  exits {dict(Counter(t.exit_reason for t in trades))}")
        print(f"  trailed: n={len(tr)} net={sum(tr):,.0f}   settled: n={len(st)} net={sum(st):,.0f}")
        for t in trades:
            per_trade.setdefault(t.d, {})[name] = (t.exit_reason, round(t.peak / t.entry_mid, 2), t.pnl("stress"))
    with open("trail_compare_trades.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date"] + [f"{n}|{c}" for n in VARIANTS for c in ("exit", "peak_x", "stress")])
        for d in sorted(per_trade):
            row = [d]
            for n in VARIANTS:
                row += list(per_trade[d].get(n, ("", "", "")))
            w.writerow(row)


if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
