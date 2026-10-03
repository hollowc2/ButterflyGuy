"""H-TR1 one-shot test runner (see docs/research/ernie-comparison-2026-10-01/H-TR1-registration.md).

SWEEP_DATA=data_theta/htr1 python htr1_run.py 2022-05-02 2024-06-28
"""
import csv
import datetime as dt
import sys

import numpy as np

from baseline import baseline_entry, mkt
from sim import VIX_BUCKETS, DayView, summarize
from trail_compare import OURS, exit_variant

EXITS = {
    "B": dict(arm=1.0, basis="value", sched=OURS),
    "T5": dict(arm=1.75, basis="value", sched=OURS, floor_at=1.75),
    "T6": dict(arm=1.0, basis="value", sched=OURS, floor_at=1.75),
}


def maxdd(p):
    eq = np.concatenate([[0], np.cumsum(p)])
    return float(np.max(np.maximum.accumulate(eq) - eq))


def main(lo, hi):
    days = [d for d in mkt.dates if lo <= d <= hi]
    res = {k: [] for k in EXITS}
    vix_at_entry = {}
    for d in days:
        for name, kw in EXITS.items():
            dv = DayView(mkt, d)
            t = baseline_entry(dv)
            if not t:
                break
            if name == "B":
                vix_at_entry[d] = mkt.vix_at(int(dv.ts[t.entry_i]))
            res[name].append(exit_variant(dv, t, **kw))
    by = {k: {t.d: t for t in v} for k, v in res.items()}
    sess = sorted(set(by["B"]) & set(by["T5"]))
    stress = {k: np.array([by[k][d].pnl("stress") for d in sess]) for k in EXITS}
    diff = stress["T5"] - stress["B"]
    med = sess[len(sess) // 2]
    h1 = np.array([d < med for d in sess])
    top3 = np.sort(diff)[-3:].sum()
    c1 = diff.sum()
    c2a, c2b = diff[h1].sum(), diff[~h1].sum()
    c3 = c1 - top3
    ddb, ddt = maxdd(stress["B"]), maxdd(stress["T5"])
    crit = [("1 full window T5-B > 0", c1, c1 > 0),
            (f"2a first half (< {med}) T5-B > 0", c2a, c2a > 0),
            (f"2b second half (>= {med}) T5-B > 0", c2b, c2b > 0),
            ("3 without top-3 sessions T5-B > 0", c3, c3 > 0),
            ("4 T5 maxDD <= B maxDD", ddt - ddb, ddt <= ddb)]
    print(f"sessions with trades: {len(sess)} ({sess[0]} .. {sess[-1]}); data sessions {len(days)}\n")
    print("| Criterion | Value | Pass |\n|---|---:|---|")
    for lab, v, ok in crit:
        print(f"| {lab} | {v:+,.0f} | {'PASS' if ok else 'FAIL'} |")
    print(f"\nH-TR1: {'PASS' if all(c[2] for c in crit) else 'FAIL'}\n")
    print("| Exit | Trades | Stressed net | Midpoint net | Marketable net | Max DD | Settled | Floor exits |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in EXITS:
        tr = [by[k][d] for d in sess]
        s_, m_, k_ = summarize(tr, "stress"), summarize(tr, "mid"), summarize(tr, "mkt")
        fl = sum(bool(t.meta.get("floor")) for t in tr)
        st = sum(t.exit_reason == "settled" for t in tr)
        print(f"| {k} | {len(tr)} | {s_['net']:,.0f} | {m_['net']:,.0f} | {k_['net']:,.0f} | {maxdd(stress[k]):,.0f} | {st} | {fl} |")
    print("\n| Group | Sessions | B stressed | T5 stressed | T5-B |\n|---|---:|---:|---:|---:|")
    edges = [b[0] for b in VIX_BUCKETS]
    names = ["Zombieland <17", "Goldilocks 1 17-24.5", "Goldilocks 2 24.5-32", "Chaos >32"]
    for gi, nm in enumerate(names):
        sel = np.array([(vix_at_entry[d] is not None) and next(i for i, e in enumerate(edges) if vix_at_entry[d] < e) == gi
                        for d in sess])
        print(f"| {nm} | {sel.sum()} | {stress['B'][sel].sum():,.0f} | {stress['T5'][sel].sum():,.0f} | {diff[sel].sum():+,.0f} |")
    for y in sorted({d.year for d in sess}):
        sel = np.array([d.year == y for d in sess])
        print(f"| {y} | {sel.sum()} | {stress['B'][sel].sum():,.0f} | {stress['T5'][sel].sum():,.0f} | {diff[sel].sum():+,.0f} |")
    with open("htr1_sessions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "vix", "typ", "c", "width", "B_exit", "B_stress", "T5_exit", "T5_stress", "T6_stress", "peak_x"])
        for d in sess:
            b, t = by["B"][d], by["T5"][d]
            w.writerow([d, vix_at_entry[d], b.fly.typ, b.fly.c, b.fly.width, b.exit_reason, round(b.pnl("stress"), 1),
                        t.exit_reason + ("/floor" if t.meta.get("floor") else ""), round(t.pnl("stress"), 1),
                        round(by["T6"][d].pnl("stress"), 1), round(t.peak / t.entry_mid, 2)])


if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
