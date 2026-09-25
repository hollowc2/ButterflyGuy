"""Standalone SPX 0-DTE butterfly research replay (read-only export, no repo source changes).

Accounting (per one-lot fly, in option points; x100 for dollars):
  mid      : entry = fly mark + 0.026 commission; intraday exit = mark - 0.026; settlement free.
  mkt      : entry = ask_l + ask_u - 2*bid_c + 0.026; exit = bid_l + bid_u - 2*ask_c - 0.026.
  stress   : mkt with every contract fill 0.05 worse (0.20 per fly per executed side).
Decisions (entries, triggers) always use marks; fills never peek past the decision snapshot.
"""
from __future__ import annotations

import datetime as dt
import math
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
D = Path(os.environ.get("SWEEP_DATA", Path(__file__).resolve().parent / "data"))
COMM = 4 * 0.65 / 100
STRESS = 4 * 0.05

VIX_BUCKETS = [(17.0, [20, 25, 30]), (24.5, [20, 30, 40]), (32.0, [40, 45, 50]), (9999.0, [50, 55, 65])]
SIGMAS = (0.25, 0.50, 0.75)
MAX_COST = {10: 1.0, 20: 2.0, 25: 2.5, 30: 3.0, 35: 3.5, 40: 4.0, 45: 4.5, 50: 5.0, 55: 5.5, 65: 6.5}
RR_MIN, RR_TARGET, RR_MAX = 8.0, 10.0, 12.0
SPOT_RANGE = 100
TRAIL = ((120, 0.60), (240, 0.90), (10_000, 0.75))


def et_ts(d: dt.date, hh: int, mm: int) -> int:
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).timestamp())


class Market:
    def __init__(self) -> None:
        self.days = pickle.load(open(D / "chain_days.pkl", "rb"))
        spot = pd.read_csv(D / "spot.csv")
        v = spot[spot.u == "$VIX"].sort_values("ts")
        self.vix_ts = v.ts.to_numpy()
        self.vix_px = v.price.to_numpy()
        daily = pd.read_csv(D / "daily.csv", parse_dates=["date"])
        s = daily[daily.u == "SPX"].sort_values("date")
        self.close = {r.date.date(): float(r.close) for r in s.itertuples()}
        self.open_ = {r.date.date(): float(r.open) for r in s.itertuples()}
        self.dates = sorted(d for d in self.days if d in self.close)  # settlement known

    def prev_close(self, d):
        prior = [x for x in self.close if x < d]
        return self.close[max(prior)] if prior else None

    def vix_at(self, ts: int, max_age: int = 300):
        i = np.searchsorted(self.vix_ts, ts, side="right") - 1
        if i < 0 or ts - self.vix_ts[i] > max_age:
            return None
        return float(self.vix_px[i])


@dataclass
class Fly:
    typ: str  # C or P
    lo: int
    c: int
    hi: int

    @property
    def width(self):
        return self.c - self.lo

    def settle(self, s: float) -> float:
        f = (lambda k: max(0.0, s - k)) if self.typ == "C" else (lambda k: max(0.0, k - s))
        return max(0.0, f(self.lo) - 2 * f(self.c) + f(self.hi))


class DayView:
    def __init__(self, mkt: Market, d: dt.date):
        self.d = d
        self.x = mkt.days[d]
        self.kidx = {int(k): i for i, k in enumerate(self.x["k"])}
        self.ts = self.x["ts"]
        self.spot = self.x["spot"]
        self.settle = mkt.close[d]
        self.prev_close = mkt.prev_close(d)
        self.mkt = mkt
        self.open_ts = et_ts(d, 9, 30)
        self.close_ts = et_ts(d, 16, 0)

    def idx_at(self, ts: int) -> int:
        """Last snapshot at or before ts (-1 if none)."""
        return int(np.searchsorted(self.ts, ts, side="right") - 1)

    def leg(self, typ, k, f):
        j = self.kidx.get(k)
        if j is None:
            return None
        return self.x[f"{typ}_{f}"][:, j]

    def fly_paths(self, fly: Fly):
        """Return (mark, entry_ask, exit_bid) arrays over snapshots; NaN where any leg missing."""
        g = {}
        for f in ("mark", "bid", "ask"):
            legs = [self.leg(fly.typ, k, f) for k in (fly.lo, fly.c, fly.hi)]
            if any(a is None for a in legs):
                return None
            g[f] = legs
        m = g["mark"][0] + g["mark"][2] - 2 * g["mark"][1]
        ask = g["ask"][0] + g["ask"][2] - 2 * g["bid"][1]
        bid = g["bid"][0] + g["bid"][2] - 2 * g["ask"][1]
        bad = np.zeros_like(m, dtype=bool)
        for f in ("bid", "ask"):
            for a in g[f]:
                bad |= ~np.isfinite(a)
        for i in range(3):
            bad |= g["bid"][i] > g["ask"][i]
        ask = np.where(bad, np.nan, ask)
        bid = np.where(bad, np.nan, bid)
        return m.astype(float), ask.astype(float), bid.astype(float)

    def straddle(self, i: int):
        """ATM straddle mid at snapshot i (nearest strike to spot)."""
        s = self.spot[i]
        ks = self.x["k"]
        j = int(np.argmin(np.abs(ks - s)))
        c, p = self.x["C_mark"][i, j], self.x["P_mark"][i, j]
        if not (np.isfinite(c) and np.isfinite(p)):
            return None
        return float(c + p)

    def candidates(self, i: int, typ: str, widths, spot_range=SPOT_RANGE, otm=True,
                   rr_filter=True, max_cost=True):
        """All flies buildable at snapshot i: yields (Fly, mark_cost)."""
        s = float(self.spot[i])
        ks = self.x["k"]
        mk = self.x[f"{typ}_mark"][i]
        have = {int(k): float(mk[j]) for j, k in enumerate(ks) if np.isfinite(mk[j])}
        out = []
        for c in have:
            if abs(c - s) > spot_range:
                continue
            if otm and ((typ == "C" and c <= s) or (typ == "P" and c >= s)):
                continue
            for w in widths:
                lo, hi = c - w, c + w
                if lo not in have or hi not in have:
                    continue
                cost = have[lo] + have[hi] - 2 * have[c]
                if cost < 0.05:
                    continue
                if max_cost and cost > MAX_COST.get(w, math.inf):
                    continue
                rr = (w - cost) / cost
                if rr_filter and rr < RR_MIN:
                    continue
                out.append((Fly(typ, lo, c, hi), cost, rr))
        return out


def rr_pick(cands):
    if not cands:
        return None
    pool = [c for c in cands if c[2] <= RR_MAX] or cands
    return min(pool, key=lambda c: (abs(c[2] - RR_TARGET), -c[0].width))


def select_anchor(dv: DayView, i: int, typ: str, vix: float, move: float | None = None,
                  tol: float = 15.0, widths=None):
    """Baseline selection: per width, center within tol of spot +/- sigma*move; RR closest to 10."""
    s = float(dv.spot[i])
    if widths is None:
        widths = next(w for vmax, w in VIX_BUCKETS if vix < vmax)
    if move is None:
        move = s * (vix / 100) / math.sqrt(252)
    cands = dv.candidates(i, typ, widths)
    bests = []
    for w, sig in zip(widths, SIGMAS):
        tgt = s + sig * move if typ == "C" else s - sig * move
        tgt = round(tgt / 5) * 5
        pool = [c for c in cands if c[0].width == w and abs(c[0].c - tgt) <= tol]
        b = rr_pick(pool)
        if b:
            bests.append(b)
    return rr_pick(bests)


@dataclass
class Trade:
    d: dt.date
    fly: Fly
    entry_i: int
    entry_mid: float  # includes commission
    entry_mkt: float | None
    exit_reason: str = ""
    exit_i: int | None = None
    exit_mid: float | None = None  # after commission
    exit_mkt: float | None = None
    peak: float = 0.0
    tag: str = ""
    meta: dict = field(default_factory=dict)

    def pnl(self, model: str) -> float | None:
        if model == "mid":
            e = self.entry_mid
            x = self.exit_mid
        else:
            if self.entry_mkt is None:
                return None
            e = self.entry_mkt + (STRESS if model == "stress" else 0)
            x = self.exit_mkt
            if self.exit_reason != "settled" and model == "stress":
                x = x - STRESS
        return 100 * (x - e)


def open_trade(dv: DayView, fly: Fly, i: int, tag="") -> Trade | None:
    p = dv.fly_paths(fly)
    if p is None:
        return None
    m, ask, bid = p
    if not np.isfinite(m[i]):
        return None
    ea = ask[i] + COMM if np.isfinite(ask[i]) else None
    return Trade(dv.d, fly, i, float(m[i]) + COMM, ea, tag=tag, meta={"paths": p})


def _mins(dv, i):
    return (dv.ts[i] - dv.open_ts) / 60


def exit_trade(dv: DayView, t: Trade, policy: str = "trail", **kw) -> Trade:
    """Exit policies. Trigger on marks; executable fill = first usable bid-side obs at/after trigger."""
    m, ask, bid = t.meta.pop("paths")
    peak = t.entry_mid
    trig = None
    n = len(m)
    tp = kw.get("tp")            # take profit as multiple of entry mid (mark >= tp*entry)
    t_exit = kw.get("t_exit")    # ET (hh,mm) time exit
    stop = kw.get("stop")        # fraction loss of entry on mark
    t_exit_ts = et_ts(dv.d, *t_exit) if t_exit else None
    for j in range(t.entry_i + 1, n):
        if not np.isfinite(m[j]):
            continue
        v = max(0.0, m[j])
        peak = max(peak, v)
        if t_exit_ts is not None and dv.ts[j] >= t_exit_ts:
            trig = (j, "time")
            break
        if tp is not None and v >= tp * t.entry_mid:
            trig = (j, "tp")
            break
        if stop is not None and v <= (1 - stop) * t.entry_mid:
            trig = (j, "stop")
            break
        if policy == "trail" and peak > t.entry_mid:
            mins = _mins(dv, j)
            thr = next(th for lim, th in TRAIL if mins < lim)
            if (peak - v) / peak >= thr:
                trig = (j, "trail")
                break
    t.peak = peak
    if trig is None:
        t.exit_reason = "settled"
        t.exit_mid = t.exit_mkt = t.fly.settle(dv.settle)
        return t
    j, why = trig
    t.exit_reason, t.exit_i = why, j
    t.exit_mid = max(0.05, m[j] - COMM)
    jj = j
    while jj < n and not np.isfinite(bid[jj]):
        jj += 1
    t.meta["exit_roll"] = jj - j
    t.exit_mkt = (bid[jj] - COMM) if jj < n else t.fly.settle(dv.settle)
    return t


def summarize(trades, model="stress", label="", sessions=None):
    rows = [(t.d, t.pnl(model)) for t in trades]
    rows = [(d, p) for d, p in rows if p is not None]
    if not rows:
        return dict(label=label, n=0)
    p = np.array([r[1] for r in rows])
    eq = np.cumsum(p)
    dd = float(np.max(np.maximum.accumulate(np.concatenate([[0], eq])) - np.concatenate([[0], eq])))
    wins = p[p > 0]
    gross_w, gross_l = wins.sum(), -p[p < 0].sum()
    top3 = np.sort(wins)[-3:].sum() / gross_w if gross_w > 0 else float("nan")
    return dict(label=label, n=len(p), net=round(float(p.sum()), 1), exp=round(float(p.mean()), 2),
                pf=round(float(gross_w / gross_l), 3) if gross_l > 0 else float("inf"),
                win=round(100 * len(wins) / len(p), 1), med=round(float(np.median(p)), 1),
                maxdd=round(dd, 0), top3=round(100 * float(top3), 1))
