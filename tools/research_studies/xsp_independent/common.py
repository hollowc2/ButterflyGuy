"""Offline XSP research mechanics, independent of runtime strategy selection.

The derived forward is a zero-carry put/call-parity approximation, NOT observed
index spot or official settlement. NBBO observation time does not establish the
last update time of either leg. Component prices are estimates, not complex fills.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.research.event_calendar import EventCalendar

FEE_PER_CONTRACT = 0.65  # provisional research assumption, not verified broker tariff
CONTRACTS_PER_FLY = 4
PROXY_MAX_DISPERSION = 0.50
PROXY_MIN_PAIRS = 3
PROXY_MAX_PAIRS = 5


@lru_cache(maxsize=1)
def calendar() -> EventCalendar:
    return EventCalendar()


def session_end(day: dt.date | str) -> pd.Timestamp:
    """Scheduled ET close; use close - 15 minutes for last research liquidation."""
    day = dt.date.fromisoformat(day) if isinstance(day, str) else day
    close = dt.time(16)
    for event in calendar().events_for(day):
        if event.event_type == "EARLY_CLOSE" and event.release_time_et is not None:
            close = event.release_time_et
    return pd.Timestamp(dt.datetime.combine(day, close), tz="America/New_York")


def load_session(path: Path | str) -> pd.DataFrame:
    """Read a single genuine XSP expiry session; never interpolate gaps.

    Raw vendor grids can extend beyond expiry and scheduled early close. Only
    09:31 <= timestamp < official scheduled close is admitted. Mixed identities
    and duplicate contract/timestamp observations fail closed.
    """
    path = Path(path)
    day = dt.date.fromisoformat(path.stem)
    quotes = pd.read_parquet(path)
    required = {"symbol", "expiration", "timestamp", "strike", "right", "bid", "ask",
                "bid_size", "ask_size"}
    if not required.issubset(quotes.columns):
        raise ValueError("missing XSP quote fields")
    if set(quotes.symbol) != {"XSP"} or set(pd.to_datetime(quotes.expiration).dt.date) != {day}:
        raise ValueError("mixed or incorrect XSP identity/expiration")
    if quotes.timestamp.dt.tz is None:
        raise ValueError("quote timestamps require explicit timezone")
    quotes["timestamp"] = quotes.timestamp.dt.tz_convert("America/New_York")
    if set(quotes.timestamp.dt.date) != {day}:
        raise ValueError("quote timestamps do not match requested session")
    if not set(quotes.right).issubset({"CALL", "PUT"}):
        raise ValueError("unknown option right")
    if quotes.duplicated(["timestamp", "strike", "right"]).any():
        raise ValueError("duplicate contract/timestamp quote")
    start = pd.Timestamp(f"{day} 09:31", tz="America/New_York")
    end = session_end(day)
    raw_rows = len(quotes)
    quotes = quotes.loc[(quotes.timestamp >= start) & (quotes.timestamp < end)].copy()
    quotes = quotes.sort_values(["timestamp", "right", "strike"]).reset_index(drop=True)
    quotes.attrs.update(raw_rows=raw_rows, filtered_rows=raw_rows - len(quotes),
                        session_end=end.isoformat(), source_path=str(path))
    return quotes


def valid_quotes(quotes: pd.DataFrame, size: int = 1) -> pd.Series:
    """Two-sided price/size usability. A zero bid with a positive ask is retained
    only when a real displayed bid size exists; 0/0 is always unavailable.
    """
    return (np.isfinite(quotes.bid) & np.isfinite(quotes.ask) & (quotes.bid >= 0)
            & (quotes.ask > 0) & (quotes.ask >= quotes.bid)
            & (quotes.bid_size >= size) & (quotes.ask_size >= size))


def derive_proxy(quotes: pd.DataFrame) -> pd.DataFrame:
    """Same-minute median approximate forward of up to five lowest-cost
    straddles. At least three pairs and <=0.50-point pair dispersion are required.
    No values are filled across missing/rejected timestamps.
    """
    good = quotes.loc[valid_quotes(quotes)].copy()
    good["mid"] = (good.bid + good.ask) / 2
    pairs = good.loc[good.right == "CALL", ["timestamp", "strike", "bid", "ask", "mid"]].merge(
        good.loc[good.right == "PUT", ["timestamp", "strike", "bid", "ask", "mid"]],
        on=["timestamp", "strike"], suffixes=("_c", "_p"), validate="one_to_one")
    columns = ["timestamp", "forward_proxy", "pair_count", "dispersion", "parity_width"]
    if pairs.empty:
        return pd.DataFrame(columns=columns)
    pairs["straddle"] = pairs.mid_c + pairs.mid_p
    pairs["forward_proxy"] = pairs.strike + pairs.mid_c - pairs.mid_p
    pairs["parity_width"] = pairs.ask_c - pairs.bid_c + pairs.ask_p - pairs.bid_p
    pairs = pairs.sort_values(["timestamp", "straddle", "strike"]).groupby(
        "timestamp", sort=False).head(PROXY_MAX_PAIRS)
    proxy = pairs.groupby("timestamp").agg(
        forward_proxy=("forward_proxy", "median"), pair_count=("forward_proxy", "size"),
        proxy_min=("forward_proxy", "min"), proxy_max=("forward_proxy", "max"),
        parity_width=("parity_width", "median"))
    proxy["dispersion"] = proxy.proxy_max - proxy.proxy_min
    proxy = proxy.loc[(proxy.pair_count >= PROXY_MIN_PAIRS)
                      & (proxy.dispersion <= PROXY_MAX_DISPERSION)]
    return proxy.reset_index()[columns]


def fly_quotes(quotes: pd.DataFrame, center: float, width: float,
               right: str = "CALL") -> pd.DataFrame:
    """Observed component prices for one long symmetric butterfly.

    Both calls and puts use +1 lower, -2 center, +1 upper. Entry is asks on
    wings less twice body bid; liquidation is wing bids less twice body ask.
    Negative liquidation is a payable close and MUST NOT be clipped to zero.
    Body displayed sizes must cover two contracts. No filling missing minutes.
    """
    if right not in {"CALL", "PUT"} or not np.isfinite(center) or width <= 0:
        raise ValueError("invalid symmetric butterfly")
    cols = ["timestamp", "mark", "entry_ask", "liquidation_bid"]
    pieces = []
    for label, strike, size in (("lower", center - width, 1), ("body", center, 2),
                                ("upper", center + width, 1)):
        leg = quotes.loc[(quotes.right == right) & (quotes.strike == strike)].copy()
        leg = leg.loc[valid_quotes(leg, size), ["timestamp", "bid", "ask"]]
        leg = leg.rename(columns={"bid": f"bid_{label}", "ask": f"ask_{label}"})
        pieces.append(leg)
    merged = pieces[0].merge(pieces[1], on="timestamp", validate="one_to_one").merge(
        pieces[2], on="timestamp", validate="one_to_one")
    merged["entry_ask"] = merged.ask_lower - 2 * merged.bid_body + merged.ask_upper
    merged["liquidation_bid"] = merged.bid_lower - 2 * merged.ask_body + merged.bid_upper
    merged["mark"] = (merged.entry_ask + merged.liquidation_bid) / 2
    return merged[cols].sort_values("timestamp").reset_index(drop=True)


def round_trip_pnl(entry_ask: float, liquidation_bid: float, *,
                   stress_per_side: float = 0.0) -> float:
    """One fly, dollars; stress is additional adverse NET package points per side.

    Four option contracts incur fees at entry AND liquidation. Settlement is
    intentionally unsupported here; it requires attributed official evidence.
    """
    if not np.isfinite(entry_ask) or not np.isfinite(liquidation_bid) or entry_ask <= 0:
        raise ValueError("invalid observed component prices")
    if stress_per_side < 0:
        raise ValueError("adverse stress must be nonnegative")
    return (liquidation_bid - entry_ask - 2 * stress_per_side) * 100 - (
        2 * CONTRACTS_PER_FLY * FEE_PER_CONTRACT)
