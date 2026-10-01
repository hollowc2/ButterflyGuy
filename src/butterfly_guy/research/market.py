"""Per-session market view over dense chain arrays.

Quote rule (matching the DB replay's `_option_quote_from_row`): a leg quote exists at a
snapshot only when bid, ask and mark were all recorded. A fly is *observed* when all
three legs exist; decisions (marks, peaks, triggers) use observed snapshots only. A fly
is *executable* when it is observed and every leg has a finite, non-negative bid and
ask with bid <= ask (`execution_accounting.inspect_quote_market`).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import cached_property
from typing import Literal
from zoneinfo import ZoneInfo

import numpy as np

from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.position.position_manager import fly_settlement_value
from butterfly_guy.research.dataset import SessionChain

EASTERN = ZoneInfo("America/New_York")
Direction = Literal["CALL", "PUT"]
TYPE_CODE = {"CALL": "C", "PUT": "P"}


def et_us(date: dt.date, hour: int, minute: int, second: int = 0) -> int:
    """Epoch microseconds of an America/New_York wall-clock time on `date`."""
    stamp = dt.datetime(date.year, date.month, date.day, hour, minute, second, tzinfo=EASTERN)
    return int(stamp.timestamp()) * 1_000_000


_EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)


def us_to_datetime(ts_us: int) -> dt.datetime:
    return _EPOCH + dt.timedelta(microseconds=int(ts_us))


@dataclass(frozen=True)
class Fly:
    """A 1/-2/1 butterfly: long lower and upper, short two centers."""

    direction: Direction
    lower: float
    center: float
    upper: float

    @property
    def width(self) -> int:
        return int(round(self.center - self.lower))

    @classmethod
    def from_candidate(cls, c: ButterflyCandidate) -> Fly:
        return cls(c.direction, c.lower_strike, c.center_strike, c.upper_strike)

    def settlement_value(self, close: float) -> float:
        """Cash-settlement value via the paper runtime's `fly_settlement_value`."""
        stub = ButterflyCandidate(
            direction=self.direction, wing_width=self.width, center_strike=self.center,
            lower_strike=self.lower, upper_strike=self.upper, cost=0.0, max_profit=0.0,
            reward_risk=0.0, lower_be=0.0, upper_be=0.0, distance_from_spot=0.0,
            spot_price=0.0,
        )
        return fly_settlement_value(stub, close)


@dataclass(frozen=True)
class FlyPath:
    """Per-snapshot fly values; NaN where the value is not defined."""

    mark: np.ndarray  # lower.mark + upper.mark - 2 * center.mark where observed
    debit: np.ndarray  # lower.ask + upper.ask - 2 * center.bid where executable
    credit: np.ndarray  # lower.bid + upper.bid - 2 * center.ask where executable
    observed: np.ndarray  # bool
    missing: np.ndarray  # bool: some leg bid/ask absent, non-finite or negative
    crossed: np.ndarray  # bool: complete legs but some bid > ask

    @property
    def executable(self) -> np.ndarray:
        return ~(self.missing | self.crossed)


class DayMarket:
    """Snapshot lookup and fly pricing for one session's chain."""

    def __init__(self, chain: SessionChain) -> None:
        self.chain = chain
        self.date = chain.date
        self.ts = chain.ts
        self.strikes = chain.strikes
        self.spot = chain.spot

    def at_or_before(self, ts_us: int) -> int:
        """Index of the last snapshot recorded no later than `ts_us`, or -1."""
        return int(np.searchsorted(self.ts, ts_us, side="right")) - 1

    @cached_property
    def present(self) -> dict[str, np.ndarray]:
        out = {}
        for t in ("C", "P"):
            f = self.chain.fields
            out[t] = (np.isfinite(f[f"{t}_bid"]) & np.isfinite(f[f"{t}_ask"])
                      & np.isfinite(f[f"{t}_mark"]))
        return out

    def field(self, direction: Direction, name: str) -> np.ndarray:
        return self.chain.fields[f"{TYPE_CODE[direction]}_{name}"]

    def fly_path(self, fly: Fly) -> FlyPath | None:
        """Price `fly` at every snapshot, or None if a strike was never listed."""
        cols = [self.chain.column(k) for k in (fly.lower, fly.center, fly.upper)]
        if any(j is None for j in cols):
            return None
        t = TYPE_CODE[fly.direction]
        pres = self.present[t][:, cols]
        observed = pres.all(axis=1)
        bid = self.field(fly.direction, "bid")[:, cols]
        ask = self.field(fly.direction, "ask")[:, cols]
        mark = self.field(fly.direction, "mark")[:, cols]
        sides_ok = np.isfinite(bid) & np.isfinite(ask) & (bid >= 0) & (ask >= 0)
        missing = ~(pres & sides_ok).all(axis=1)
        crossed = ~missing & (bid > ask).any(axis=1)
        exe = ~(missing | crossed)
        with np.errstate(invalid="ignore"):
            m = mark[:, 0] + mark[:, 2] - 2 * mark[:, 1]
            debit = ask[:, 0] + ask[:, 2] - 2 * bid[:, 1]
            credit = bid[:, 0] + bid[:, 2] - 2 * ask[:, 1]
        return FlyPath(
            mark=np.where(observed, m, np.nan),
            debit=np.where(exe, debit, np.nan),
            credit=np.where(exe, credit, np.nan),
            observed=observed,
            missing=missing,
            crossed=crossed,
        )

    def first_at_or_after(self, ts_us: int) -> int | None:
        """Index of the first snapshot recorded at or after `ts_us`, or None."""
        i = int(np.searchsorted(self.ts, ts_us, side="left"))
        return i if i < len(self.ts) else None

    def atm_straddle(self, i: int) -> float | None:
        """ATM straddle mark at snapshot `i`: call plus put mark at the strike nearest the
        snapshot's spot (the lower strike on an exact tie); None if either is missing."""
        j = int(np.argmin(np.abs(self.strikes - self.spot[i])))
        c = self.chain.fields["C_mark"][i, j]
        p = self.chain.fields["P_mark"][i, j]
        if not (np.isfinite(c) and np.isfinite(p)):
            return None
        return float(c + p)

    def quotes_at(
        self, i: int, direction: Direction, near: float | None = None, span: float | None = None
    ) -> list[OptionQuote]:
        """Recorded quotes of one type at snapshot `i` as `OptionQuote`s for live selection.

        `near`/`span` limit strikes to |strike - near| <= span; callers pass a span that
        covers every strike the selector could use, so the result is unchanged.
        """
        t = TYPE_CODE[direction]
        ok = self.present[t][i]
        if near is not None and span is not None:
            ok = ok & (np.abs(self.strikes - near) <= span)
        f = self.chain.fields
        bid, ask, mark = f[f"{t}_bid"][i], f[f"{t}_ask"][i], f[f"{t}_mark"][i]
        iv, delta = f[f"{t}_iv"][i], f[f"{t}_delta"][i]
        out = []
        for j in np.flatnonzero(ok):
            out.append(OptionQuote(
                symbol="", underlying="SPX", expiration=self.date,
                strike=float(self.strikes[j]), option_type=direction,
                bid=float(bid[j]), ask=float(ask[j]), mark=float(mark[j]),
                iv=float(np.nan_to_num(iv[j])), delta=float(np.nan_to_num(delta[j])),
            ))
        return out


def restrict_view(
    chain: SessionChain,
    *,
    start_us: int | None = None,
    end_us: int | None = None,
    strike_band: float | None = None,
    integer_strikes: bool = False,
) -> SessionChain:
    """A copy of `chain` limited to a time window and/or a per-snapshot strike band.

    Quotes outside the band are removed (NaN), as if the source never exported them.
    Used to reproduce studies that ran on narrower exports.
    """
    keep_t = np.ones(len(chain.ts), dtype=bool)
    if start_us is not None:
        keep_t &= chain.ts >= start_us
    if end_us is not None:
        keep_t &= chain.ts <= end_us
    keep_k = np.ones(len(chain.strikes), dtype=bool)
    if integer_strikes:
        keep_k &= chain.strikes == np.round(chain.strikes)
    ts, spot, strikes = chain.ts[keep_t], chain.spot[keep_t], chain.strikes[keep_k]
    fields = {k: v[keep_t][:, keep_k].copy() for k, v in chain.fields.items()}
    if strike_band is not None:
        outside = np.abs(strikes[None, :] - spot[:, None]) > strike_band
        for v in fields.values():
            v[outside] = np.nan
    return SessionChain(date=chain.date, ts=ts, strikes=strikes, spot=spot, fields=fields)
