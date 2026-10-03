"""Diagnostic: decompose the frozen baseline's P&L into midpoint edge and execution costs.

Per trade (baseline entry, baseline exit B), in $ per one-lot fly:
  mid        : P&L at marks, commissions included ($0.65 x 4 legs per executed side)
  entry_spr  : (fly ask - fly mid) at entry           (marketable entry)
  exit_spr   : (fly mid - fly bid) at exit, trailed only (settled trades exit free)
  stress     : $0.05 per contract per executed side   ($20 entry, $20 more if trailed)
  stressed   = mid - entry_spr - exit_spr - stress
Run from this directory with SWEEP_DATA set:  python cost_breakdown.py START END
"""
import datetime as dt
import sys
from collections import defaultdict

import numpy as np

from baseline import baseline_entry, mkt
from sim import STRESS, DayView
from trail_compare import OURS, exit_variant

B = dict(arm=1.0, basis="value", sched=OURS)
EDGES = [(17.0, "Zombieland <17"), (24.5, "Goldilocks 1"), (32.0, "Goldilocks 2"), (1e9, "Chaos >32")]


def bucket(v):
    return next(n for e, n in EDGES if v < e)


def main(lo, hi):
    rows = []
    days = [d for d in mkt.dates if lo <= d <= hi]
    for d in days:
        dv = DayView(mkt, d)
        t = baseline_entry(dv)
        if not t or t.entry_mkt is None:
            continue
        vix = mkt.vix_at(int(dv.ts[t.entry_i]))
        t = exit_variant(dv, t, **B)
        trailed = t.exit_reason != "settled"
        mid = t.pnl("mid")
        entry_spr = 100 * (t.entry_mkt - t.entry_mid)
        exit_spr = 100 * (t.exit_mid - t.exit_mkt) if trailed else 0.0
        stress = 100 * STRESS * (2 if trailed else 1)
        rows.append(dict(d=d, vix=vix, b=bucket(vix), exit="trailed" if trailed else "settled",
                         debit=100 * (t.entry_mid - 0.026), width=t.fly.width, mid=mid, entry_spr=entry_spr,
                         exit_spr=exit_spr, stress=stress, stressed=t.pnl("stress")))
    n = len(rows)
    print(f"traded sessions {n} of {len(days)}\n")

    def table(key, title):
        g = defaultdict(list)
        for r in rows:
            g[key(r)].append(r)
        print(f"| {title} | Trades | Midpoint | Entry spread | Exit spread | Stress | Stressed | "
              f"Midpoint/trade | Cost/trade | Avg debit | Entry spread % debit |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for k in sorted(g, key=str):
            rs = g[k]
            s = {f: sum(r[f] for r in rs) for f in ("mid", "entry_spr", "exit_spr", "stress", "stressed")}
            cost = s["entry_spr"] + s["exit_spr"] + s["stress"]
            deb = np.mean([r["debit"] for r in rs])
            pct = 100 * np.mean([r["entry_spr"] / r["debit"] for r in rs])
            print(f"| {k} | {len(rs)} | {s['mid']:,.0f} | −{s['entry_spr']:,.0f} | −{s['exit_spr']:,.0f} | "
                  f"−{s['stress']:,.0f} | {s['stressed']:,.0f} | {s['mid'] / len(rs):,.0f} | {cost / len(rs):,.0f} | "
                  f"{deb:,.0f} | {pct:.0f}% |")
        print()

    table(lambda r: "all", "Group")
    table(lambda r: r["b"], "VIX zone")
    table(lambda r: r["exit"], "Exit")
    table(lambda r: r["d"].year, "Year")
    table(lambda r: f"{r['b']} / {r['exit']}", "Zone / exit")
    # how much of the spread can be paid before the edge is gone
    mid = sum(r["mid"] for r in rows)
    spr = sum(r["entry_spr"] + r["exit_spr"] for r in rows)
    print(f"midpoint {mid:,.0f}; full spread paid {spr:,.0f}; break-even share of the spread = {mid / spr:.0%}")
    tr = [r for r in rows if r["exit"] == "trailed"]
    print(f"trailed exits: {len(tr)}, midpoint {sum(r['mid'] for r in tr):,.0f}, "
          f"round-trip spread {sum(r['entry_spr'] + r['exit_spr'] for r in tr):,.0f}")


if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
