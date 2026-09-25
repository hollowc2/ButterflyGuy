import numpy as np
import pandas as pd

from variants import *

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
T = pd.read_csv("e0_trades_lowvix.csv", parse_dates=["d"]); T["half"] = np.where(T.d.dt.date <= SPLIT, "H1", "H2")
rng = np.random.default_rng(11)

# 1. Is the split beyond chance?  permutation of trade labels + contiguous-block null
p = T.stress.values; h = (T.half == "H2").values; obs = p[~h].mean() - p[h].mean()
perm = np.array([(lambda m: p[~m].mean() - p[m].mean())(rng.permutation(h)) for _ in range(20000)])
print(f"H1-H2 expectancy diff ${obs:.0f}; permutation p(one-sided)={np.mean(perm >= obs):.3f}")
n2 = h.sum(); roll = [p[i:i + n2].sum() for i in range(len(p) - n2 + 1)]
boot = np.array([rng.choice(p, n2).sum() for _ in range(20000)])
print(f"P(a random {n2}-trade draw from the full-sample distribution nets <= {p[h].sum():.0f}) = {np.mean(boot <= p[h].sum()):.3f}")

# 2. Decompose: winners count/size, loser size, hit rates
def dec(g):
    w = g[g.stress > 0]
    return pd.Series(dict(n=len(g), net=g.stress.sum(), wins=len(w), big_wins=(g.stress > 1000).sum(), avg_win=w.stress.mean(),
        avg_loss=g[g.stress <= 0].stress.mean(), settled=(g.reason == "settled").sum(), settled_pnl=g[g.reason == "settled"].stress.sum(),
        trail_pnl=g[g.reason == "trail"].stress.sum(), in_tent=g.in_tent.mean(), touch_c=g.touch_c.mean(), dir_ok=g.dir_ok.mean(),
        cost=g.cost.mean(), imp_p=g.imp_p.mean(), real_p=g.real_p.mean(), spr=g.spr_frac.mean(), drag=g.cost_drag.mean(),
        peak_x=g.peak_x.median(), calls=(g.typ == "C").mean(), off_sd=g.off_sd.mean()))
print(T.groupby("half").apply(dec).T.round(3))

# 3. Counterfactual exits per half: did the trailer start costing more?
base = run(e0); hold = run(e0, "none")
for nm, tr in (("trail", base), ("hold", hold)):
    for hf in ("H1", "H2"):
        sub = [t for t in tr if (t.d <= SPLIT) == (hf == "H1")]
        print(nm, hf, summarize(sub, "stress"))
# trailed-out trades that would have settled in the money
lost = [(t.d, t.pnl("stress"), 100 * (t.fly.settle(DV[t.d].settle) - t.entry_mkt - STRESS)) for t in base
        if t.exit_reason == "trail" and t.fly.settle(DV[t.d].settle) > t.entry_mkt]
L = pd.DataFrame(lost, columns=["d", "trail_pnl", "hold_pnl"]); L["half"] = np.where(L.d <= SPLIT, "H1", "H2")
print("trailed out of an eventual settlement winner:\n", L.groupby("half").agg(n=("d", "size"), trail=("trail_pnl", "sum"), hold=("hold_pnl", "sum")).round(0))
