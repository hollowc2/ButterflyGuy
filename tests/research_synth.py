"""Synthetic chains for research-core unit tests."""

from __future__ import annotations

import datetime as dt

import numpy as np

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
