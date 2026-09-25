import datetime as dt
import json
from collections import Counter

import numpy as np

from baseline import baseline_entry, mkt, open_spot
from sim import COMM, STRESS, VIX_BUCKETS, DayView, Fly, et_ts, exit_trade, open_trade, summarize

START, END = dt.date(2026, 3, 13), dt.date(2026, 9, 24)
SPLIT = dt.date(2026, 6, 18)
DATES = [d for d in mkt.dates if START <= d <= END]
DV = {d: DayView(mkt, d) for d in DATES}
FOMC = {dt.date(2026, 3, 18), dt.date(2026, 4, 29), dt.date(2026, 6, 17), dt.date(2026, 7, 29),
        dt.date(2026, 9, 16)}


def run(entry_fn, policy="trail", **kw):
    out = []
    for d in DATES:
        dv = DV[d]
        ts = entry_fn(dv)
        for t in ([] if ts is None else ts if isinstance(ts, list) else [ts]):
            out.append(exit_trade(dv, t, policy, **kw))
    return out


def first_idx(dv, hh, mm):
    idx = np.where(dv.ts >= et_ts(dv.d, hh, mm))[0]
    return int(idx[0]) if len(idx) else None


# ---------------- entry functions ----------------
def e0(dv):
    return baseline_entry(dv)


def c1(dv):
    return baseline_entry(dv, anchor="straddle")


def d1(dv):
    o = open_spot(dv.d)
    i = first_idx(dv, 10, 0)
    if o is None or i is None:
        return None
    return baseline_entry(dv, direction="C" if dv.spot[i] >= o else "P")


def d2(dv):
    o = open_spot(dv.d)
    if o is None or dv.prev_close is None:
        return None
    return baseline_entry(dv, direction="P" if o >= dv.prev_close else "C")


def d3(dv):
    return [t for t in (baseline_entry(dv, direction="C"), baseline_entry(dv, direction="P")) if t]


def d4(dv):
    for i in np.where((dv.ts >= et_ts(dv.d, 10, 0)) & (dv.ts <= et_ts(dv.d, 10, 45)))[0]:
        vix = mkt.vix_at(int(dv.ts[i]))
        if vix is None:
            continue
        w = next(w for vmax, w in VIX_BUCKETS if vix < vmax)[1]
        c = int(round(dv.spot[i] / 5) * 5)
        t = open_trade(dv, Fly("C", c - w, c, c + w), i, tag="ATM")
        if t:
            return t
    return None


def late(hh, mm):
    return lambda dv: baseline_entry(dv, start=(hh, mm), anchor="straddle")


# ---------------- EV selector ----------------
EV_WIDTHS = (10, 15, 20, 25, 30, 40, 50)
GH = np.quantile(np.random.default_rng(0).standard_normal(200_000), np.linspace(0.02, 0.98, 25))


def ev_entry_factory(hh, mm, bw=0.3, min_hist=20):
    hist = []  # (date, z) appended only after the day's decision

    def fn(dv):
        i = first_idx(dv, hh, mm)
        if i is None:
            return None
        s, st = float(dv.spot[i]), dv.straddle(i)
        decision = None
        prior = [z for d0, z in hist if d0 < dv.d]
        if st and len(prior) >= min_hist:
            zs = (np.array(prior)[:, None] + bw * GH[None, :]).ravel()
            ST = s + zs * st
            best = None
            for typ in ("C", "P"):
                mk, bid, ask = (dv.x[f"{typ}_{f}"][i] for f in ("mark", "bid", "ask"))
                col = {int(k): j for j, k in enumerate(dv.x["k"])}
                for c in col:
                    if abs(c - s) > 100 or c % 5:
                        continue
                    for w in EV_WIDTHS:
                        if c - w not in col or c + w not in col:
                            continue
                        jl, jc, jh = col[c - w], col[c], col[c + w]
                        m = mk[jl] + mk[jh] - 2 * mk[jc]
                        a = ask[jl] + ask[jh] - 2 * bid[jc]
                        if not (np.isfinite(m) and np.isfinite(a)) or m < 0.30:
                            continue
                        if bid[jl] > ask[jl] or bid[jc] > ask[jc] or bid[jh] > ask[jh]:
                            continue
                        ev = np.maximum(0.0, w - np.abs(ST - c)).mean() - (a + COMM + STRESS)
                        if best is None or ev > best[0]:
                            best = (ev, Fly(typ, c - w, c, c + w))
            if best and best[0] > 0:
                decision = open_trade(dv, best[1], i, tag=f"ev={best[0]:.2f}")
        if st:
            hist.append((dv.d, (dv.settle - s) / st))
        return decision

    return fn


# ---------------- metrics ----------------
def daily(trades, model="stress"):
    p = {d: 0.0 for d in DATES}
    for t in trades:
        v = t.pnl(model)
        if v is not None:
            p[t.d] += v
    return np.array([p[d] for d in DATES])


def boot_ci(diff, reps=5000, block=5, seed=1):
    rng = np.random.default_rng(seed)
    n = len(diff)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n]
    tot = diff[idx].sum(1)
    return np.percentile(tot, [5, 50, 95]), float((tot > 0).mean())


def report(name, trades, base_daily):
    h1 = [t for t in trades if t.d <= SPLIT]
    h2 = [t for t in trades if t.d > SPLIT]
    full = summarize(trades, "stress", name)
    s1, s2 = summarize(h1, "stress"), summarize(h2, "stress")
    mid = summarize(trades, "mid")
    dd = daily(trades)
    ci, pgt = boot_ci(dd - base_daily)
    exits = Counter(t.exit_reason for t in trades)
    unpriced = sum(t.entry_mkt is None for t in trades)
    return dict(**full, mid_net=mid.get("net"), h1_net=s1.get("net", 0), h2_net=s2.get("net", 0),
                h1_n=s1.get("n", 0), h2_n=s2.get("n", 0), vs_base_ci90=[round(x) for x in ci],
                p_better=round(pgt, 3), exits=dict(exits), unpriced=unpriced)


if __name__ == "__main__":
    res = {}
    base = run(e0)
    bd = daily(base)
    res["E0"] = report("E0", base, bd)
    res["X1"] = report("X1", run(e0, "none"), bd)
    res["X2"] = report("X2", run(e0, "none", tp=3.0), bd)
    res["X3"] = report("X3", run(e0, "none", tp=2.0), bd)
    res["X4"] = report("X4", run(e0, "none", stop=0.5), bd)
    res["X5"] = report("X5", run(e0, "trail", t_exit=(15, 0)), bd)
    res["C1"] = report("C1", run(c1), bd)
    res["C2"] = report("C2", run(c1, "none"), bd)
    res["D1"] = report("D1", run(d1), bd)
    res["D2"] = report("D2", run(d2), bd)
    res["D3"] = report("D3", run(d3), bd)
    res["D4"] = report("D4", run(d4, "none"), bd)
    for code, (hh, mm), pol in [("T1", (11, 30), "trail"), ("T2", (11, 30), "none"),
                                ("T3", (13, 0), "trail"), ("T4", (13, 0), "none"),
                                ("T5", (14, 30), "trail"), ("T6", (14, 30), "none")]:
        res[code] = report(code, run(late(hh, mm), pol), bd)
    # K1: threshold from H1 baseline trades only
    ratios = [(t.entry_mkt - t.entry_mid) / (t.entry_mid - COMM) for t in base
              if t.d <= SPLIT and t.entry_mkt is not None]
    thr = float(np.median(ratios))

    def k1(dv):
        t = e0(dv)
        if t and t.entry_mkt is not None and (t.entry_mkt - t.entry_mid) / (t.entry_mid - COMM) > thr:
            return None
        return t

    res["K1"] = report("K1", run(k1), bd) | {"threshold": round(thr, 3)}
    res["G1"] = report("G1", run(ev_entry_factory(10, 0), "none"), bd)
    res["G2"] = report("G2", run(ev_entry_factory(13, 0), "none"), bd)
    fomc = [t for t in base if t.d in FOMC]
    res["diag_FOMC"] = {"fomc": summarize(fomc, "stress"),
                        "non_fomc": summarize([t for t in base if t.d not in FOMC], "stress")}
    res["_meta"] = {"sessions": len(DATES), "h1_sessions": sum(d <= SPLIT for d in DATES),
                    "first": str(DATES[0]), "last": str(DATES[-1])}
    json.dump(res, open("results.json", "w"), indent=1, default=str)
    cols = ["n", "net", "exp", "pf", "win", "maxdd", "top3", "mid_net", "h1_net", "h2_net",
            "vs_base_ci90", "p_better"]
    print("code " + " ".join(f"{c:>12}" for c in cols))
    for k, v in res.items():
        if k.startswith(("_", "diag")):
            continue
        print(f"{k:4} " + " ".join(f"{str(v.get(c)):>12}" for c in cols), v["exits"])
    print(res["diag_FOMC"], res["_meta"], "K1 thr", res["K1"]["threshold"])
