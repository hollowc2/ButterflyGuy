"""Strike placement: our VIX-sigma anchor vs Ernie's (@0DTE) price-based placement.

Each session keeps the baseline's entry snapshot, direction and width; only the center
strike changes. Selection uses marks; P&L uses the 09-25 accounting.
  P0 ours        : baseline select_anchor pick
  P1 ernie 10%   : closest-to-money OTM center with mark <= 10% of width
  P2 ernie 7.5%  : closest-to-money OTM center with mark <= 7.5% of width
  P3 convexity   : from P1 walk outward; take the step with the largest relative price
                   drop, keeping mark >= 5% of width
Exits: B (ours) and T5 (start at +75%, breakeven floor).
Run from this directory: python placement_compare.py 2026-03-13 2026-09-18
"""
import datetime as dt
import math
import sys

import numpy as np

from baseline import baseline_entry, mkt
from sim import DayView, open_trade, summarize
from trail_compare import H2_START, OURS, exit_variant

EXITS = {
    "B ours": dict(arm=1.0, basis="value", sched=OURS),
    "T5 +75%+floor": dict(arm=1.75, basis="value", sched=OURS, floor_at=1.75),
}


def ladder(dv, i, typ, w):
    """OTM centers ordered from the money outward: [(fly, cost)]."""
    c = dv.candidates(i, typ, [w], rr_filter=False, max_cost=False)
    s = float(dv.spot[i])
    return sorted(((f, cost) for f, cost, _ in c), key=lambda x: abs(x[0].c - s))


def pick(dv, i, typ, w, rule):
    lad = ladder(dv, i, typ, w)
    if rule == "P1":
        return next((f for f, cost in lad if cost <= 0.10 * w), None)
    if rule == "P2":
        return next((f for f, cost in lad if cost <= 0.075 * w), None)
    if rule == "P3":
        k = next((n for n, (f, cost) in enumerate(lad) if cost <= 0.10 * w), None)
        if k is None:
            return None
        best, best_drop = lad[k][0], 0.0
        for n in range(k + 1, len(lad)):
            prev, cur = lad[n - 1][1], lad[n][1]
            if cur < 0.05 * w:
                break
            drop = (prev - cur) / prev if prev > 0 else 0.0
            if drop > best_drop:
                best, best_drop = lad[n][0], drop
        return best
    raise ValueError(rule)


def main(lo, hi):
    days = [d for d in mkt.dates if lo <= d <= hi]
    rows = {}
    for d in days:
        dv = DayView(mkt, d)
        base = baseline_entry(dv)
        if not base:
            continue
        i, typ, w = base.entry_i, base.fly.typ, base.fly.width
        s, vix = float(dv.spot[i]), mkt.vix_at(int(dv.ts[i]))
        sig = s * (vix / 100) / math.sqrt(252)
        flies = {"P0 ours": base.fly}
        for r in ("P1", "P2", "P3"):
            f = pick(dv, i, typ, w, r)
            if f:
                flies[{"P1": "P1 ernie 10%", "P2": "P2 ernie 7.5%", "P3": "P3 convexity"}[r]] = f
        for name, fly in flies.items():
            for ex, kw in EXITS.items():
                t = open_trade(DayView(mkt, d), fly, i, tag=typ)
                if t is None:
                    continue
                dv2 = DayView(mkt, d)
                t = exit_variant(dv2, t, **kw)
                t.meta["dist_sigma"] = abs(fly.c - s) / sig
                t.meta["cost_pct"] = (t.entry_mid - 0.026) / w
                rows.setdefault((name, ex), []).append(t)
    print("| Placement | Exit | Trades | Stressed net | H1 | H2 | Midpoint net | Max DD | Avg distance (σ) | Avg cost % width | Settled |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for (name, ex), tr in rows.items():
        s_ = summarize(tr, "stress")
        m_ = summarize(tr, "mid")
        h1 = sum(t.pnl("stress") or 0 for t in tr if t.d < H2_START)
        h2 = sum(t.pnl("stress") or 0 for t in tr if t.d >= H2_START)
        dist = np.mean([t.meta["dist_sigma"] for t in tr])
        cp = 100 * np.mean([t.meta["cost_pct"] for t in tr])
        st = sum(t.exit_reason == "settled" for t in tr)
        print(f"| {name} | {ex} | {len(tr)} | {s_['net']:,.0f} | {h1:,.0f} | {h2:,.0f} | {m_['net']:,.0f} | {s_['maxdd']:,.0f} | {dist:.2f} | {cp:.1f}% | {st} |")


if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
