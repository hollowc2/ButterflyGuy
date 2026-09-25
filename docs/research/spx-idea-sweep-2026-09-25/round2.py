import json
import math

import numpy as np

from sim import VIX_BUCKETS
from variants import *

base = run(e0); bd = daily(base)

def ror(trades):
    risk = sum(100 * (t.entry_mkt + STRESS) for t in trades if t.entry_mkt is not None)
    return round(100 * summarize(trades, "stress")["net"] / risk, 1) if risk else None

def ratio_at(dv, i):
    s = float(dv.spot[i]); st = dv.straddle(i); vix = mkt.vix_at(int(dv.ts[i]))
    return (s * vix / 100 / math.sqrt(252)) / (1.25 * st) if st and vix else None

def r1(dv):
    t = e0(dv)
    return t if t and mkt.vix_at(int(dv.ts[t.entry_i])) >= 17.0 else None

thr = float(np.median([ratio_at(DV[t.d], t.entry_i) for t in base if t.d <= SPLIT]))
def r2(dv):
    t = e0(dv)
    return t if t and ratio_at(dv, t.entry_i) <= thr else None

def r5(dv):
    t = e0(dv)
    return t if t and t.fly.typ == "C" else None

def ev_rank_factory(bw=0.3, min_hist=20):
    hist = []
    def fn(dv):
        o = open_spot(dv.d)
        decision = None
        prior = [z for d0, z in hist if d0 < dv.d]
        i10 = first_idx(dv, 10, 0)
        if o is None or dv.prev_close is None or i10 is None:
            return None
        typ = "C" if o >= dv.prev_close else "P"
        if len(prior) >= min_hist:
            for i in np.where((dv.ts >= et_ts(dv.d, 10, 0)) & (dv.ts <= et_ts(dv.d, 10, 45)))[0]:
                vix = mkt.vix_at(int(dv.ts[i])); st = dv.straddle(i)
                if vix is None or not st:
                    continue
                s = float(dv.spot[i])
                widths = next(w for vmax, w in VIX_BUCKETS if vix < vmax)
                cands = dv.candidates(i, typ, widths)
                if not cands:
                    continue
                ST = s + (np.array(prior)[:, None] + bw * GH[None, :]).ravel() * st
                best = max(cands, key=lambda c: np.maximum(0, c[0].width - np.abs(ST - c[0].c)).mean() - c[1])
                decision = open_trade(dv, best[0], i, tag="evrank")
                break
        st10 = dv.straddle(i10)
        if st10:
            hist.append((dv.d, (dv.settle - float(dv.spot[i10])) / st10))
        return decision
    return fn

res = {"E0": report("E0", base, bd) | {"ror": ror(base)}}
for code, fn, pol in [("R1", r1, "trail"), ("R2", r2, "trail"), ("R5", r5, "trail")]:
    tr = run(fn, pol); res[code] = report(code, tr, bd) | {"ror": ror(tr)}
tr = run(ev_rank_factory(), "trail"); res["R3"] = report("R3", tr, bd) | {"ror": ror(tr)}
tr = run(ev_rank_factory(), "none"); res["R4"] = report("R4", tr, bd) | {"ror": ror(tr)}
for code, fn, pol, kw in [("G1", ev_entry_factory(10, 0), "none", {}), ("X1", e0, "none", {}), ("K1", None, None, None)]:
    if fn: tr = run(fn, pol); res[code] = report(code, tr, bd) | {"ror": ror(tr)}
json.dump(res, open("results_round2.json", "w"), indent=1, default=str)
cols = ["n", "net", "exp", "pf", "win", "maxdd", "top3", "h1_net", "h2_net", "h1_n", "h2_n", "vs_base_ci90", "p_better", "ror"]
print("code " + " ".join(f"{c:>11}" for c in cols))
for k, v in res.items():
    print(f"{k:4} " + " ".join(f"{str(v.get(c)):>11}" for c in cols))
print("R2 ratio threshold", round(thr, 3))
