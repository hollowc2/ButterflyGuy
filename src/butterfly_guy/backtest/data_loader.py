"""Shared backtest market-data models."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


@dataclass
class MinuteBar:
    ts: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class DayData:
    date: dt.date
    bars: list[MinuteBar]
    vix: float
    prev_close: float
    vix_bars: list[MinuteBar] = field(default_factory=list)
    recent_closes: list[float] = field(default_factory=list)
