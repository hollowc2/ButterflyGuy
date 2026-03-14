"""Intraday VIX regime filter — skips entry when volatility is too elevated."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.backtest.data_loader import MinuteBar


class RegimeFilter:
    """Filter entries based on intraday VIX level at the time of entry."""

    def __init__(self, vix_max: float) -> None:
        self.vix_max = vix_max

    def vix_at_entry(self, vix_bars: list[MinuteBar], entry_ts: dt.datetime) -> float | None:
        """Most recent VIX bar close at or before entry_ts. None if no bars."""
        candidates = [b for b in vix_bars if b.ts <= entry_ts]
        return max(candidates, key=lambda b: b.ts).close if candidates else None

    def should_trade(self, vix_bars: list[MinuteBar], entry_ts: dt.datetime) -> bool:
        """True = safe to trade. False = skip (VIX too high).

        Returns True if no VIX bars are available (pass-through for loaders
        that don't provide intraday VIX data).
        """
        v = self.vix_at_entry(vix_bars, entry_ts)
        return v is None or v <= self.vix_max
