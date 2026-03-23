"""Pydantic models for option data and trade records."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class OptionQuote:
    """A single option quote from a chain snapshot."""

    symbol: str
    underlying: str
    expiration: dt.date
    strike: float
    option_type: Literal["CALL", "PUT"]
    bid: float
    ask: float
    mark: float
    last: float = 0.0
    volume: int = 0
    open_interest: int = 0
    iv: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    rho: float = 0.0
    intrinsic_value: float = 0.0
    time_value: float = 0.0
    in_the_money: bool = False
    days_to_expiration: int = 0
    multiplier: float = 100.0
    theoretical_value: float = 0.0

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0


@dataclass
class ButterflyCandidate:
    """A butterfly spread candidate identified by the scanner."""

    direction: Literal["CALL", "PUT"]
    wing_width: int
    center_strike: float
    lower_strike: float
    upper_strike: float
    cost: float
    max_profit: float
    reward_risk: float
    lower_be: float
    upper_be: float
    distance_from_spot: float
    spot_price: float
    lower_symbol: str = ""
    center_symbol: str = ""
    upper_symbol: str = ""
    lower_quote: OptionQuote | None = None
    center_quote: OptionQuote | None = None
    upper_quote: OptionQuote | None = None


@dataclass
class TradeRecord:
    """A trade record for tracking entry/exit."""

    trade_id: int = 0
    trade_date: dt.date = field(default_factory=dt.date.today)
    direction: str = ""
    wing_width: int = 0
    center_strike: float = 0.0
    lower_strike: float = 0.0
    upper_strike: float = 0.0
    entry_price: float = 0.0
    entry_time: dt.datetime | None = None
    exit_price: float | None = None
    exit_time: dt.datetime | None = None
    exit_reason: str | None = None
    pnl: float | None = None
    peak_value: float = 0.0
    lower_symbol: str = ""
    center_symbol: str = ""
    upper_symbol: str = ""
    quantity: int = 1
    status: str = "OPEN"
