"""Write per-session baseline entries with B and T5 exits to CSV (for cross-source parity).

Run from this directory with SWEEP_DATA pointing at a dataset:
  SWEEP_DATA=data_theta/parity python dump_trades.py 2026-03-13 2026-09-18 out.csv
"""
import csv
import datetime as dt
import sys

from baseline import baseline_entry, mkt
from sim import DayView
from trail_compare import OURS, exit_variant

EXITS = {"B": dict(arm=1.0, basis="value", sched=OURS),
         "T5": dict(arm=1.75, basis="value", sched=OURS, floor_at=1.75)}

lo, hi, out = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]), sys.argv[3]
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "typ", "lo", "c", "hi", "entry_ts", "entry_mid", "B_exit", "B_mid", "B_stress",
                "T5_exit", "T5_mid", "T5_stress", "peak_x"])
    for d in [d for d in mkt.dates if lo <= d <= hi]:
        t0 = baseline_entry(DayView(mkt, d))
        if not t0:
            continue
        row = [d, t0.fly.typ, t0.fly.lo, t0.fly.c, t0.fly.hi, int(DayView(mkt, d).ts[t0.entry_i]),
               round(t0.entry_mid, 3)]
        peak = None
        for name, kw in EXITS.items():
            dv = DayView(mkt, d)
            t = exit_variant(dv, baseline_entry(dv), **kw)
            row += [t.exit_reason + ("/floor" if t.meta.get("floor") else ""), round(t.pnl("mid"), 1),
                    round(t.pnl("stress"), 1) if t.pnl("stress") is not None else ""]
            peak = round(t.peak / t.entry_mid, 2)
        w.writerow(row + [peak])
