"""Multi-signal directional bias filter for 0-DTE butterfly entries."""

from __future__ import annotations

import datetime as dt
from typing import Literal
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

EASTERN = ZoneInfo("America/New_York")
_OR_END = dt.time(9, 45)  # Opening range: [09:30, 09:45) ET


class BiasScoreFilter:
    """Scores market direction using 4 signals; returns CALL, PUT, or None."""

    def get_direction(
        self,
        bars: list[MinuteBar],
        prev_close: float,
        entry_close: float,
    ) -> Literal["CALL", "PUT"] | None:
        """
        Compute bias score from 4 signals:
          gap          : +1 if entry_close > prev_close, -1 if below
          VWAP         : +1 if entry_close > vwap, -1 if below
          EMA9 vs EMA21: +1 if ema9 > ema21, -1 if below (0 if insufficient bars)
          OR breakout  : +2 if entry_close > or_high, -2 if below or_low (0 if no OR)

        score >= 2  → CALL
        score <= -2 → PUT
        else        → None (no trade)
        """
        score = 0

        # --- Gap signal ---
        if entry_close > prev_close:
            score += 1
        elif entry_close < prev_close:
            score -= 1

        # --- VWAP signal ---
        vwap = self._compute_vwap(bars, fallback=entry_close)
        if entry_close > vwap:
            score += 1
        elif entry_close < vwap:
            score -= 1

        # --- EMA signal ---
        closes = [b.close for b in bars]
        ema9 = self._ema(closes, 9)
        ema21 = self._ema(closes, 21)
        if ema9 is not None and ema21 is not None:
            if ema9 > ema21:
                score += 1
            elif ema9 < ema21:
                score -= 1

        # --- Opening-range breakout signal ---
        or_high, or_low = self._compute_or(bars)
        if or_high > 0.0:
            if entry_close > or_high:
                score += 2
            elif entry_close < or_low:
                score -= 2

        # --- Determine direction ---
        if score >= 2:
            direction: Literal["CALL", "PUT"] | None = "CALL"
        elif score <= -2:
            direction = "PUT"
        else:
            direction = None

        log.info(
            "bias_score_computed",
            score=score,
            direction=direction,
            vwap=round(vwap, 4),
            ema9=round(ema9, 4) if ema9 is not None else None,
            ema21=round(ema21, 4) if ema21 is not None else None,
            or_high=or_high,
            or_low=or_low,
            entry_close=entry_close,
            prev_close=prev_close,
        )
        return direction

    @staticmethod
    def _compute_vwap(bars: list[MinuteBar], fallback: float) -> float:
        """Volume-weighted average price using close as typical price.

        Edge case: all volume == 0 → return fallback.
        """
        total_vol = sum(b.volume for b in bars)
        if total_vol == 0:
            return fallback
        return sum(b.close * b.volume for b in bars) / total_vol

    @staticmethod
    def _compute_or(bars: list[MinuteBar]) -> tuple[float, float]:
        """High and low of the opening range (bars with ET time < 09:45).

        Edge case: no OR bars → return (0.0, 0.0), OR signal skipped.
        """
        or_bars = [b for b in bars if b.ts.astimezone(EASTERN).time() < _OR_END]
        if not or_bars:
            return 0.0, 0.0
        return max(b.high for b in or_bars), min(b.low for b in or_bars)

    @staticmethod
    def _ema(closes: list[float], period: int) -> float | None:
        """Exponential moving average seeded with SMA of first `period` bars.

        Returns None if len(closes) < period.
        """
        if len(closes) < period:
            return None
        k = 2.0 / (period + 1)
        ema = sum(closes[:period]) / period  # seed with SMA
        for price in closes[period:]:
            ema = price * k + ema * (1 - k)
        return ema
