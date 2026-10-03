"""Direction: our gap rule vs Ernie's (@0DTE) trend indicators.

Same entry machinery as baseline.py (first qualifying snapshot 10:00-10:45, VIX buckets,
anchor, cost caps); only the CALL/PUT choice changes. Rules written before running:
  D0 gap          : open >= prior close -> CALL (baseline)
  D1 1h EMA50     : spot at 10:00 >= EMA50 of completed 9:30-aligned hourly closes -> CALL
  D2 1h Hull55    : HMA55 of completed hourly closes rising vs 2 bars earlier -> CALL
  D3 daily EMA50  : prior close >= EMA50 of daily closes through prior day -> CALL
  D4 daily Hull55 : daily HMA55 through prior day rising vs 2 bars earlier -> CALL
Daily closes: FRED SP500 (data/fred_sp500.csv). Hourly: Helios spot_prices (from 2026-03-13).
Rules are compared on the sessions where every rule has a value.
Run from this directory: python direction_compare.py 2026-03-13 2026-09-18
"""
import datetime as dt
import math
import sys

import numpy as np
import pandas as pd

from baseline import baseline_entry, mkt, open_spot, spx_px, spx_ts
from sim import D, DayView, et_ts, summarize
from trail_compare import H2_START, OURS, exit_variant

EXITS = {
    "B ours": dict(arm=1.0, basis="value", sched=OURS),
    "T5 +75%+floor": dict(arm=1.75, basis="value", sched=OURS, floor_at=1.75),
}


def ema(x, n):
    if len(x) < n:
        return None
    a = 2 / (n + 1)
    e = float(np.mean(x[:n]))
    for v in x[n:]:
        e = a * v + (1 - a) * e
    return e


def wma(x, n):
    w = np.arange(1, n + 1)
    return np.array([np.dot(x[i - n + 1:i + 1], w) / w.sum() for i in range(n - 1, len(x))])


def hma_series(x, n):
    x = np.asarray(x, float)
    h, s = n // 2, int(round(math.sqrt(n)))
    if len(x) < n + s + 2:
        return None
    a, b = wma(x, h), wma(x, n)
    diff = 2 * a[len(a) - len(b):] - b
    return wma(diff, s)


def hull_rising(x, n=55):
    hs = hma_series(x, n)
    if hs is None or len(hs) < 3:
        return None
    return hs[-1] > hs[-3]


fred = pd.read_csv(D / "fred_sp500.csv").dropna()
fred = fred[pd.to_numeric(fred.SP500, errors="coerce").notna()]
daily = {dt.date.fromisoformat(r.observation_date): float(r.SP500) for r in fred.itertuples()}
ddates = sorted(daily)


def hourly_closes_before(ts_cut):
    """Completed 9:30-aligned RTH hourly closes (bar ends 10:30 ... 15:30, 16:00) before ts_cut."""
    out = []
    days = sorted({dt.datetime.fromtimestamp(int(t), tz=mkt_tz).date() for t in spx_ts if t < ts_cut})
    for d in days:
        ends = [et_ts(d, h, 30) for h in range(10, 16)] + [et_ts(d, 16, 0)]
        for e in ends:
            if e > ts_cut:
                break
            j = np.searchsorted(spx_ts, e, side="right") - 1
            if j >= 0 and spx_ts[j] >= e - 3600:
                out.append(float(spx_px[j]))
    return out


from sim import ET as mkt_tz  # noqa: E402


def directions(d):
    t0 = et_ts(d, 10, 0)
    o = open_spot(d)
    prev = [x for x in ddates if x < d]
    if o is None or not prev:
        return None
    j = np.searchsorted(spx_ts, t0, side="right") - 1
    spot10 = float(spx_px[j])
    hc = hourly_closes_before(t0)
    dc = [daily[x] for x in prev]
    out = {"D0 gap": "C" if o >= mkt.prev_close(d) else "P"}
    e1 = ema(hc, 50)
    h1 = hull_rising(hc)
    e3 = ema(dc, 50)
    h4 = hull_rising(dc)
    if None in (e1, h1, e3, h4):
        return None
    out["D1 1h EMA50"] = "C" if spot10 >= e1 else "P"
    out["D2 1h Hull55"] = "C" if h1 else "P"
    out["D3 daily EMA50"] = "C" if dc[-1] >= e3 else "P"
    out["D4 daily Hull55"] = "C" if h4 else "P"
    return out


def main(lo, hi):
    rows, agree, ndays, first = {}, {}, 0, None
    for d in [d for d in mkt.dates if lo <= d <= hi]:
        dirs = directions(d)
        if dirs is None:
            continue
        ndays += 1
        first = first or d
        for name, typ in dirs.items():
            agree.setdefault(name, []).append(typ == dirs["D0 gap"])
            for ex, kw in EXITS.items():
                dv = DayView(mkt, d)
                t = baseline_entry(dv, direction=typ)
                if t:
                    rows.setdefault((name, ex), []).append(exit_variant(DayView(mkt, d), t, **kw))
    print(f"common sessions: {ndays} from {first}\n")
    print("| Rule | Exit | Trades | Stressed net | H1 | H2 | Midpoint net | Max DD | Calls/Puts | Same side as gap |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for (name, ex), tr in rows.items():
        s_, m_ = summarize(tr, "stress"), summarize(tr, "mid")
        h1 = sum(t.pnl("stress") or 0 for t in tr if t.d < H2_START)
        h2 = sum(t.pnl("stress") or 0 for t in tr if t.d >= H2_START)
        c = sum(t.fly.typ == "C" for t in tr)
        ag = 100 * np.mean(agree[name])
        print(f"| {name} | {ex} | {len(tr)} | {s_['net']:,.0f} | {h1:,.0f} | {h2:,.0f} | {m_['net']:,.0f} | {s_['maxdd']:,.0f} | {c}/{len(tr) - c} | {ag:.0f}% |")


if __name__ == "__main__":
    main(dt.date.fromisoformat(sys.argv[1]), dt.date.fromisoformat(sys.argv[2]))
