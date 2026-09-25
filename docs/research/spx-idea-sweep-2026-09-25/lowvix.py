import math

import numpy as np
import pandas as pd

from variants import *

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
BK = [0, 17, 24.5, 99]; LB = ["<17", "17-24.5", ">24.5"]

# ---- session-level market behaviour (all sessions, independent of trades) ----
rows = []
for d in DATES:
    dv = DV[d]; i = first_idx(dv, 10, 0)
    if i is None: continue
    s = float(dv.spot[i]); st = dv.straddle(i); vix = mkt.vix_at(int(dv.ts[i]))
    if not st or vix is None: continue
    sd = 1.25 * st
    after = dv.spot[i:]
    o = open_spot(d)
    rows.append(dict(d=d, vix=vix, sd=sd, vixmove=s * vix / 100 / math.sqrt(252),
        z_close=(dv.settle - s) / sd, absz=abs(dv.settle - s) / sd,
        up_exc=(np.nanmax(after) - s) / sd, dn_exc=(s - np.nanmin(after)) / sd,
        gap=(o - dv.prev_close) / dv.prev_close * 100 if o else np.nan,
        gap_follow=np.sign(dv.settle - s) == np.sign(o - dv.prev_close) if o else np.nan,
        straddle_pnl=abs(dv.settle - s) - st))
S = pd.DataFrame(rows); S["b"] = pd.cut(S.vix, BK, labels=LB); S["half"] = np.where(S.d <= SPLIT, "H1", "H2")
S["ratio"] = S.vixmove / S.sd
print("=== sessions: realized vs chain-implied move after 10:00 ===")
print(S.groupby("b", observed=True).agg(n=("d", "size"), vix=("vix", "mean"), sd_pts=("sd", "mean"), vixmove=("vixmove", "mean"),
      ratio=("ratio", "mean"), absz=("absz", "mean"), p_absz_gt1=("absz", lambda x: (x > 1).mean()),
      p_absz_gt15=("absz", lambda x: (x > 1.5).mean()), up_exc=("up_exc", "mean"), dn_exc=("dn_exc", "mean"),
      gap_follow=("gap_follow", "mean"), straddle_pnl=("straddle_pnl", "mean")).round(3))
print(S.groupby(["half", "b"], observed=True).agg(n=("d", "size"), absz=("absz", "mean"), p15=("absz", lambda x: (x > 1.5).mean()), ratio=("ratio", "mean"), gap_follow=("gap_follow", "mean")).round(3))

# ---- trade-level decomposition ----
base = run(e0); T = []
for t in base:
    dv = DV[t.d]; i = t.entry_i; s = float(dv.spot[i]); st = dv.straddle(i); sd = 1.25 * st
    vix = mkt.vix_at(int(dv.ts[i])); typ = t.fly.typ; sign = 1 if typ == "C" else -1
    path = dv.spot[i:]
    fav = (np.nanmax(path) - s) if typ == "C" else (s - np.nanmin(path))
    T.append(dict(d=t.d, typ=typ, vix=vix, w=t.fly.width, off=abs(t.fly.c - s), off_sd=abs(t.fly.c - s) / sd,
        w_sd=t.fly.width / sd, cost=t.entry_mid - COMM, ask=t.entry_mkt - COMM, spr_frac=(t.entry_mkt - t.entry_mid) / (t.entry_mid - COMM),
        rr=(t.fly.width - (t.entry_mid - COMM)) / (t.entry_mid - COMM), dir_ok=sign * (dv.settle - s) > 0,
        touch_lo=fav >= abs(t.fly.lo - s) if typ == "C" else fav >= abs(t.fly.hi - s),
        touch_c=fav >= abs(t.fly.c - s), in_tent=t.fly.settle(dv.settle) > 0,
        settle_val=t.fly.settle(dv.settle), peak_x=t.peak / t.entry_mid, reason=t.exit_reason,
        mid=t.pnl("mid"), stress=t.pnl("stress"), cost_drag=t.pnl("mid") - t.pnl("stress"),
        # implied "probability" proxy: debit / max payoff; realized payout ratio of settle
        imp_p=(t.entry_mid - COMM) / t.fly.width, real_p=t.fly.settle(dv.settle) / t.fly.width))
T = pd.DataFrame(T); T["b"] = pd.cut(T.vix, BK, labels=LB); T["half"] = np.where(T.d <= SPLIT, "H1", "H2")
agg = dict(n=("d", "size"), stress=("stress", "sum"), mid=("mid", "sum"), exp=("stress", "mean"), w=("w", "mean"), off=("off", "mean"),
           off_sd=("off_sd", "mean"), w_sd=("w_sd", "mean"), cost=("cost", "mean"), spr=("spr_frac", "mean"), drag=("cost_drag", "mean"),
           dir_ok=("dir_ok", "mean"), touch_lo=("touch_lo", "mean"), touch_c=("touch_c", "mean"), in_tent=("in_tent", "mean"),
           imp_p=("imp_p", "mean"), real_p=("real_p", "mean"), peak_x=("peak_x", "median"))
print("\n=== baseline trades by VIX bucket ===")
print(T.groupby("b", observed=True).agg(**agg).round(3))
print(T.groupby(["half", "b"], observed=True).agg(**{k: agg[k] for k in ("n", "stress", "mid", "off_sd", "w_sd", "dir_ok", "touch_c", "in_tent", "imp_p", "real_p")}).round(3))
print(T.groupby(["b", "typ"], observed=True).agg(n=("d", "size"), stress=("stress", "sum"), dir_ok=("dir_ok", "mean"), in_tent=("in_tent", "mean")).round(3))
print(T.groupby(["b", "reason"], observed=True).agg(n=("d", "size"), stress=("stress", "sum"), mid=("mid", "sum")).round(0))
T.to_csv("e0_trades_lowvix.csv", index=False); S.to_csv("sessions.csv", index=False)
