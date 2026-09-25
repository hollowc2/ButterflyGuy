import datetime as dt
import sys

import numpy as np
import pandas as pd

from sim import *

mkt = Market()
spot = pd.read_csv(D / "spot.csv"); spx = spot[spot.u == "SPX"].sort_values("ts")
spx_ts, spx_px = spx.ts.to_numpy(), spx.price.to_numpy()

def open_spot(d):
    i = np.searchsorted(spx_ts, et_ts(d, 9, 30))
    return float(spx_px[i]) if i < len(spx_ts) and spx_ts[i] < et_ts(d, 16, 0) else None

def baseline_entry(dv, start=(10, 0), minutes=45, direction=None, anchor="vix"):
    o = open_spot(dv.d)
    if o is None or dv.prev_close is None:
        return None
    typ = direction or ("C" if o >= dv.prev_close else "P")
    t0 = et_ts(dv.d, *start)
    for i in np.where((dv.ts >= t0) & (dv.ts <= t0 + minutes * 60))[0]:
        vix = mkt.vix_at(int(dv.ts[i]))
        if vix is None:
            continue
        move = None
        if anchor == "straddle":
            st = dv.straddle(i)
            if st is None:
                continue
            move = st * 1.25  # ATM straddle ~ 0.8 sigma of remaining-session move
        pick = select_anchor(dv, i, typ, vix, move=move)
        if pick:
            return open_trade(dv, pick[0], i, tag=typ)
    return None

if __name__ == "__main__":
    lo, hi = dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2])
    trades = []
    for d in mkt.dates:
        if not lo <= d <= hi: continue
        dv = DayView(mkt, d)
        t = baseline_entry(dv)
        if t: trades.append(exit_trade(dv, t, "trail"))
    for m in ("mid", "mkt", "stress"):
        print(summarize(trades, m, m))
    from collections import Counter
    print(Counter(t.exit_reason for t in trades), "sessions", sum(lo <= d <= hi for d in mkt.dates))
    settled = sum(t.pnl("mid") for t in trades if t.exit_reason == "settled")
    print("settled contribution mid", round(settled, 1))
