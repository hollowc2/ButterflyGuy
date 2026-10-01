"""Entry trigger: Ernie-style "bounce off a structural level" using GEX walls as the levels.

Rules written before running:
  Levels  : at the first snapshot >= 09:45 ET, per-strike net GEX = BS gamma (from chain IV)
            x SPXW open interest x 100 x S^2 x 0.01, calls +, puts -. Levels = the 3 strikes
            with the largest |GEX| within +/- 2 sigma (VIX daily move) of spot.
  Placebo : same trigger, levels = 25-point round numbers within +/- 2 sigma.
  Trigger : 09:45-12:30 ET, direction = gap rule. CALL: spot within 3 pts of a level, then a
            snapshot >= level + 5 within 15 min. PUT: mirrored (<= level - 5). Fly chosen with
            the baseline selector at the trigger snapshot or the next 5 minutes; if none
            qualifies, keep scanning. No trigger by 12:30 -> no trade.
  Control : baseline entry (10:00-10:45 first qualifying snapshot) on all days and on the
            trigger's days only.
Exits: B (ours) and T5 (start at +75%, breakeven floor).
Run from this directory: python gex_compare.py 2026-03-13 2026-09-18
"""
import datetime as dt
import math
import sys

import numpy as np
import pandas as pd

from baseline import baseline_entry, mkt
from sim import D, DayView, et_ts, open_trade, select_anchor, summarize
from trail_compare import H2_START, OURS, exit_variant

EXITS = {
    "B ours": dict(arm=1.0, basis="value", sched=OURS),
    "T5 +75%+floor": dict(arm=1.75, basis="value", sched=OURS, floor_at=1.75),
}
oi = pd.read_csv(D / "oi.csv")
oi["d"] = pd.to_datetime(oi.d).dt.date
OI = {d: g for d, g in oi.groupby("d")}


def bs_gamma(s, k, iv_pct, t_years):
    if not (iv_pct > 0) or t_years <= 0:
        return 0.0
    v = iv_pct / 100 * math.sqrt(t_years)
    d1 = (math.log(s / k) + 0.5 * v * v) / v
    return math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (s * v)


def gex_levels(dv, i, sig, n=3):
    g = OI.get(dv.d)
    if g is None:
        return None
    s = float(dv.spot[i])
    t_years = max(dv.close_ts - int(dv.ts[i]), 60) / (365 * 24 * 3600)
    oi_map = {(int(r.k), r.t): float(r.oi) for r in g.itertuples()}
    out = []
    for j, k in enumerate(dv.x["k"]):
        k = int(k)
        if abs(k - s) > 2 * sig:
            continue
        net = 0.0
        for typ, sign in (("C", 1), ("P", -1)):
            iv = float(dv.x[f"{typ}_iv"][i, j])
            net += sign * bs_gamma(s, k, iv, t_years) * oi_map.get((k, typ), 0.0) * 100 * s * s * 0.01
        out.append((abs(net), k))
    out.sort(reverse=True)
    return [k for _, k in out[:n]]


def round_levels(s, sig):
    lo, hi = math.ceil((s - 2 * sig) / 25) * 25, math.floor((s + 2 * sig) / 25) * 25
    return list(range(lo, hi + 1, 25))


def triggered_entry(dv, typ, kind):
    i0 = int(np.searchsorted(dv.ts, et_ts(dv.d, 9, 45)))
    if i0 >= len(dv.ts):
        return None
    vix0 = mkt.vix_at(int(dv.ts[i0]))
    if vix0 is None:
        return None
    s0 = float(dv.spot[i0])
    sig = s0 * (vix0 / 100) / math.sqrt(252)
    levels = gex_levels(dv, i0, sig) if kind == "gex" else round_levels(s0, sig)
    if not levels:
        return None
    end = et_ts(dv.d, 12, 30)
    touched = {}  # level -> ts of last touch
    i = i0
    while i < len(dv.ts) and dv.ts[i] <= end:
        s = float(dv.spot[i])
        ts = int(dv.ts[i])
        fire = False
        for L in levels:
            if abs(s - L) <= 3:
                touched[L] = ts
            elif L in touched and ts - touched[L] <= 900:
                if (typ == "C" and s >= L + 5) or (typ == "P" and s <= L - 5):
                    fire = True
                    touched.pop(L)
        if fire:
            for j in range(i, len(dv.ts)):
                if dv.ts[j] > ts + 300 or dv.ts[j] > end:
                    break
                vix = mkt.vix_at(int(dv.ts[j]))
                p = select_anchor(dv, j, typ, vix) if vix else None
                if p:
                    t = open_trade(dv, p[0], j, tag=typ)
                    if t:
                        t.meta["entry_ts"] = int(dv.ts[j])
                        return t
        i += 1
    return None


def main(lo, hi):
    days = [d for d in mkt.dates if lo <= d <= hi]
    rows, trig_days = {}, {"gex": set(), "round": set()}
    for d in days:
        dv = DayView(mkt, d)
        base = baseline_entry(dv)
        typ = base.tag if base else None
        if typ is None:
            o = dv.spot[0]
            typ = "C" if dv.prev_close and o >= dv.prev_close else "P"
        for kind in ("gex", "round"):
            t = triggered_entry(DayView(mkt, d), typ, kind)
            if t:
                trig_days[kind].add(d)
                for ex, kw in EXITS.items():
                    tt = triggered_entry(DayView(mkt, d), typ, kind)
                    rows.setdefault((f"E1 {kind} trigger", ex), []).append(exit_variant(DayView(mkt, d), tt, **kw))
        if base:
            for ex, kw in EXITS.items():
                rows.setdefault(("E0 ours 10:00 (all days)", ex), []).append(
                    exit_variant(DayView(mkt, d), baseline_entry(DayView(mkt, d)), **kw))
    for kind in ("gex", "round"):
        for ex in EXITS:
            rows[(f"E0 ours 10:00 on {kind}-trigger days", ex)] = [
                t for t in rows.get(("E0 ours 10:00 (all days)", ex), []) if t.d in trig_days[kind]]
    print(f"sessions {len(days)}; gex-trigger days {len(trig_days['gex'])}; round-trigger days {len(trig_days['round'])}\n")
    print("| Entry | Exit | Trades | Stressed net | Per trade | H1 | H2 | Midpoint net | Max DD | Settled |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    order = ["E0 ours 10:00 (all days)", "E1 gex trigger", "E0 ours 10:00 on gex-trigger days",
             "E1 round trigger", "E0 ours 10:00 on round-trigger days"]
    for name in order:
        for ex in EXITS:
            tr = rows.get((name, ex), [])
            if not tr:
                continue
            s_, m_ = summarize(tr, "stress"), summarize(tr, "mid")
            h1 = sum(t.pnl("stress") or 0 for t in tr if t.d < H2_START)
            h2 = sum(t.pnl("stress") or 0 for t in tr if t.d >= H2_START)
            st = sum(t.exit_reason == "settled" for t in tr)
            print(f"| {name} | {ex} | {len(tr)} | {s_['net']:,.0f} | {s_['exp']:,.0f} | {h1:,.0f} | {h2:,.0f} | {m_['net']:,.0f} | {s_['maxdd']:,.0f} | {st} |")
    times = [dt.datetime.fromtimestamp(t.meta["entry_ts"], tz=mkt_tz).strftime("%H:%M")
             for t in rows.get(("E1 gex trigger", "B ours"), [])]
    if times:
        hrs = pd.Series([int(x[:2]) for x in times]).value_counts().sort_index().to_dict()
        print(f"\ngex trigger entry hour (ET) counts: {hrs}")


from sim import ET as mkt_tz  # noqa: E402

if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
