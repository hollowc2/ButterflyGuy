import numpy as np
import pandas as pd

from variants import *

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
BK = [0, 17, 24.5, 99]; LB = ["<17", "17-24.5", ">24.5"]
T = pd.read_csv("e0_trades_lowvix.csv", parse_dates=["d"]); T["b"] = pd.cut(T.vix, BK, labels=LB)
rng = np.random.default_rng(7)

print("=== payout/implied ratio (settlement value / mid debit), bootstrap 90% CI ===")
for b, g in T.groupby("b", observed=True):
    r = g.settle_val.values; c = g.cost.values
    bs = [r[i].sum() / c[i].sum() for i in (rng.integers(0, len(r), len(r)) for _ in range(5000))]
    print(f"{b:8} n={len(g):3} ratio={r.sum()/c.sum():.2f} CI90=[{np.percentile(bs,5):.2f}, {np.percentile(bs,95):.2f}]  cost_drag/debit={(g.cost_drag/(100*g.cost)).mean():.1%}")

print("\n=== confound check: expectancy per trade, half x bucket; OLS stress ~ lowvix + H2 ===")
T["H2"] = (T.d.dt.date > SPLIT).astype(int); T["low"] = (T.vix < 17).astype(int)
print(T.pivot_table(index="H2", columns="low", values="stress", aggfunc=["count", "mean"]).round(0))
X = np.column_stack([np.ones(len(T)), T.low, T.H2]); y = T.stress.values
beta, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ beta
cov = np.linalg.inv(X.T @ X) * (res @ res) / (len(y) - 3)
for n, bb, se in zip(["const", "lowVIX", "H2"], beta, np.sqrt(np.diag(cov))):
    print(f"  {n:7} {bb:8.1f}  se {se:6.1f}  t {bb/se:5.2f}")

# ---- market-wide fly grid: independent of gap direction and the RR filter ----
print("\n=== market-wide 10:00 fly grid (both sides, center k*sd OTM, width 0.9 sd), settle ===")
rows = []
for d in DATES:
    dv = DV[d]; i = first_idx(dv, 10, 0)
    if i is None: continue
    s = float(dv.spot[i]); st = dv.straddle(i); vix = mkt.vix_at(int(dv.ts[i]))
    if not st or vix is None: continue
    sd = 1.25 * st; w = max(5, int(round(0.9 * sd / 5) * 5))
    for k in (0.0, 0.5, 1.0, 1.5, 2.0):
        for typ, sg in (("C", 1), ("P", -1)):
            c = int(round((s + sg * k * sd) / 5) * 5)
            f = Fly(typ, c - w, c, c + w); p = dv.fly_paths(f)
            if p is None or not np.isfinite(p[0][i]) or not np.isfinite(p[1][i]): continue
            rows.append(dict(d=d, vix=vix, k=k, typ=typ, mid=p[0][i], ask=p[1][i], pay=f.settle(dv.settle), w=w))
G = pd.DataFrame(rows); G = G[G.mid > 0.05]
G["b"] = pd.cut(G.vix, BK, labels=LB); G["half"] = np.where(G.d <= SPLIT, "H1", "H2")
G["pnl_mid"] = 100 * (G.pay - G.mid - COMM); G["pnl_stress"] = 100 * (G.pay - G.ask - COMM - STRESS)
def tab(g):
    return pd.Series(dict(n=len(g), pay_over_mid=g.pay.sum() / g.mid.sum(), exp_mid=g.pnl_mid.mean(), exp_stress=g.pnl_stress.mean(),
                          spread_frac=((g.ask - g.mid) / g.mid).mean()))
print(G.groupby(["k", "b"], observed=True).apply(tab).round(2).unstack("b"))
print("\n-- same, split by half (pay/mid) --")
print(G.groupby(["k", "half", "b"], observed=True).apply(lambda g: round(g.pay.sum() / g.mid.sum(), 2)).unstack(["half", "b"]))
print("\n-- by side at k=1.5 (pay/mid) --")
print(G[G.k == 1.5].groupby(["typ", "half", "b"], observed=True).apply(lambda g: round(g.pay.sum() / g.mid.sum(), 2)).unstack(["half", "b"]))
S = pd.read_csv("sessions.csv", parse_dates=["d"])
print("\n=== drift: mean signed z (settle - 10:00 spot)/sd by half x bucket ===")
S["half"] = np.where(S.d.dt.date <= SPLIT, "H1", "H2"); S["b"] = pd.cut(S.vix, BK, labels=LB)
print(S.pivot_table(index="half", columns="b", values="z_close", aggfunc=["mean", "count"], observed=True).round(3))
print("\n=== skew: 1.5sd put fly vs call fly mid cost (same session), by bucket ===")
pc = G[G.k == 1.5].pivot_table(index=["d", "b"], columns="typ", values="mid", observed=True).dropna()
print((pc.P / pc.C).groupby(level="b", observed=True).describe()[["count", "mean", "50%"]].round(2))
