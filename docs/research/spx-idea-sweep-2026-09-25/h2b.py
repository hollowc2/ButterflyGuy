import numpy as np
import pandas as pd

from variants import *

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
S = pd.read_csv("sessions.csv", parse_dates=["d"]); S["half"] = np.where(S.d.dt.date <= SPLIT, "H1", "H2")
S["m"] = S.d.dt.to_period("M")
S["zg"] = np.sign(S.gap) * S.z_close  # move after 10:00 in the gap direction
# landing zone of the baseline fly: centre ~1.58 sd, wings +-0.88 sd => profitable roughly 0.7..2.5 sd in gap dir
S["land"] = S.zg.between(0.9, 2.3)
def f(g):
    return pd.Series(dict(n=len(g), vix=g.vix.mean(), sd_pts=g.sd.mean(), absz=g.absz.mean(), rv_ratio=np.sqrt((g.z_close**2).mean()) / 1.0,
        gap_abs=g.gap.abs().mean(), zg_mean=g.zg.mean(), p_follow=(g.zg > 0).mean(), p_land=g.land.mean(),
        p_z_gt1=(g.absz > 1).mean(), exc_gapdir=np.where(g.gap > 0, g.up_exc, g.dn_exc).mean(), straddle_pnl=g.straddle_pnl.mean()))
print(f(S).round(3).to_frame("all").T)
print(S.groupby("half").apply(f).round(3))
print(S.groupby("m").apply(f).round(3))
# first-hour trend (09:30->10:00) vs rest of day: persistence
rows = []
for d in DATES:
    dv = DV[d]; i = first_idx(dv, 10, 0); j = first_idx(dv, 12, 0); o = open_spot(d)
    if None in (i, j, o) or not dv.straddle(i): continue
    sd = 1.25 * dv.straddle(i); s10 = dv.spot[i]
    rows.append(dict(d=d, early=(s10 - o) / sd, mid=(dv.spot[j] - s10) / sd, late=(dv.settle - dv.spot[j]) / sd, gap=np.sign(o - dv.prev_close)))
P = pd.DataFrame(rows); P["half"] = np.where(P.d <= SPLIT, "H1", "H2")
for hf, g in P.groupby("half"):
    print(hf, "corr(gap, 10->close)", round(np.corrcoef(g.gap, g.mid + g.late)[0, 1], 3), "corr(10->12, 12->close)", round(np.corrcoef(g.mid, g.late)[0, 1], 3),
          "corr(open->10, 10->close)", round(np.corrcoef(g.early, g.mid + g.late)[0, 1], 3))
