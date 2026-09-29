"""Synthetic chains for research-core unit tests."""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from butterfly_guy.research.dataset import SessionChain
from butterfly_guy.research.market import et_us

DAY = dt.date(2026, 6, 10)
STRIKES = np.array([5950.0, 5960.0, 5970.0, 5980.0, 5990.0, 6000.0])


def minute(hh: int, mm: int, ss: int = 0) -> int:
    return et_us(DAY, hh, mm, ss)


def make_chain(
    times: list[int],
    quotes: dict[tuple[int, float], tuple[float, float, float]],
    typ: str = "C",
    spot: float = 5960.0,
) -> SessionChain:
    """Dense chain where quotes[(ts, strike)] = (bid, ask, mark); everything else NaN."""
    ts = np.array(sorted(times), dtype=np.int64)
    fields = {f"{t}_{f}": np.full((len(ts), len(STRIKES)), np.nan)
              for t in ("C", "P") for f in ("bid", "ask", "mark", "iv", "delta")}
    for (when, strike), (bid, ask, mark) in quotes.items():
        i = int(np.searchsorted(ts, when))
        j = int(np.searchsorted(STRIKES, strike))
        fields[f"{typ}_bid"][i, j] = bid
        fields[f"{typ}_ask"][i, j] = ask
        fields[f"{typ}_mark"][i, j] = mark
    return SessionChain(date=DAY, ts=ts, strikes=STRIKES.copy(),
                        spot=np.full(len(ts), spot), fields=fields)


def fly_quotes(
    when: int, lo: tuple[float, float], c: tuple[float, float], hi: tuple[float, float],
    strikes: tuple[float, float, float] = (5970.0, 5980.0, 5990.0),
) -> dict[tuple[int, float], tuple[float, float, float]]:
    """Three legs with the given (bid, ask); mark is the midpoint."""
    out = {}
    for k, (b, a) in zip(strikes, (lo, c, hi), strict=True):
        out[(when, k)] = (b, a, (b + a) / 2)
    return out


# ---------------------------------------------------------------------------
# A synthetic vendor history source (history.HistorySource)
# ---------------------------------------------------------------------------


def synthetic_day(d: dt.date, spot: float = 6000.0, strikes: tuple[float, ...] = (),
                  close: tuple[int, int] = (16, 0), index: bool = True) -> dict:
    """One session of vendor data: quote updates every 5 minutes from 09:30:30 ET for the
    given strikes (calls and puts, mid = intrinsic + 2.0, spread 0.10), SPX and VIX
    index prints every minute from 09:30, and the official bars."""
    strikes = strikes or tuple(float(k) for k in range(5980, 6021, 5))
    end = et_us(d, *close)
    times = np.arange(et_us(d, 9, 30, 30), end + 1, 300_000_000)
    rows = []
    for ts in times:
        for k in strikes:
            for t, intrinsic in (("C", max(spot - k, 0.0)), ("P", max(k - spot, 0.0))):
                mid = intrinsic + 2.0
                rows.append({"ts_us": int(ts), "strike": k, "t": t, "bid": mid - 0.05,
                             "ask": mid + 0.05, "iv": 0.2, "delta": 0.5, "mark": 999.0})
    minutes = np.arange(et_us(d, 9, 30), end + 1, 60_000_000)
    return {
        "quotes": pd.DataFrame(rows),
        "spx": pd.DataFrame({"ts_us": minutes, "price": spot}) if index else pd.DataFrame(
            columns=["ts_us", "price"]),
        "vix": pd.DataFrame({"ts_us": minutes, "price": 18.0}),
        "bars": [{"date": d, "underlying": "SPX", "open": spot - 1, "high": spot + 5,
                  "low": spot - 5, "close": spot + 2},
                 {"date": d, "underlying": "$VIX", "open": 18.0, "high": 19.0, "low": 17.0,
                  "close": 18.5}],
    }


class FakeSource:
    """In-memory `HistorySource`; logs every call so tests can prove what was asked."""

    def __init__(self, days: dict[dt.date, dict], cost: float | None = None,
                 extra_bars: list[dict] | None = None) -> None:
        self.days, self.cost, self.extra_bars = days, cost, extra_bars or []
        self.calls: list[tuple] = []

    def describe(self) -> dict:
        return {"vendor": "fake", "product": "synthetic", "plan": "test", "licence": "none"}

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        self.calls.append(("sessions", start, end))
        return [d for d in sorted(self.days) if start <= d <= end]

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        self.calls.append(("quotes", d, strikes))
        return self.days[d]["quotes"]

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        self.calls.append(("index_bars", d, symbol))
        return self.days[d]["spx" if symbol == "SPX" else "vix"]

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        self.calls.append(("daily_bars", start, end))
        rows = [b for day in self.days.values() for b in day["bars"]] + self.extra_bars
        return pd.DataFrame([b for b in rows if start <= b["date"] <= end])

    def cost_estimate(self, start: dt.date, end: dt.date) -> float | None:
        self.calls.append(("cost_estimate", start, end))
        return self.cost
