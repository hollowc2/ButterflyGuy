"""Market regime classifier for 0-DTE butterfly parameter dispatch.

Classifies each trading day as BULL, BEAR, CHOP, or UNKNOWN using two signals:
  - SPX N-day return  (recent_closes[-1] / recent_closes[-lookback] - 1)
  - VIX absolute level

Signal scoring (same pattern as BiasScoreFilter):
  spx_return < bear_return_thresh  → bear_score += 1
  spx_return > bull_return_thresh  → bull_score += 1
  vix > bear_vix_thresh            → bear_score += 1
  vix < bull_vix_thresh            → bull_score += 1

  bear_score >= 2  → BEAR
  bull_score >= 2  → BULL
  else             → CHOP   (mixed or no signal)
  insufficient data → UNKNOWN

Live integration note:
  In live trading, recent_closes must be sourced from Schwab's daily bar
  endpoint (get_price_history, frequencyType=daily, frequency=1,
  periodType=month) covering at least lookback_days + 5 prior trading days
  to guarantee a full lookback window. See TODO in run_live.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Regime(str, Enum):
    BULL    = "BULL"
    BEAR    = "BEAR"
    CHOP    = "CHOP"
    UNKNOWN = "UNKNOWN"


@dataclass
class RegimeClassifier:
    """Classifies market regime from SPX recent closes and daily VIX level."""

    lookback_days: int = 5
    bear_return_thresh: float = -0.02  # SPX N-day return below this → bear signal
    bull_return_thresh: float = 0.02   # SPX N-day return above this → bull signal
    bear_vix_thresh: float = 20.0      # VIX above this → bear signal
    bull_vix_thresh: float = 18.0      # VIX below this → bull signal

    def classify(self, recent_closes: list[float], vix: float) -> Regime:
        """Return Regime for today given prior daily closes and today's VIX.

        Args:
            recent_closes: Prior daily SPX closes in chronological order,
                           most recent last. Must have at least lookback_days
                           entries to produce a non-UNKNOWN result.
            vix: Today's VIX level (daily scalar, same as DayData.vix).

        Returns:
            Regime enum value.
        """
        if len(recent_closes) < self.lookback_days:
            return Regime.UNKNOWN

        spx_return = recent_closes[-1] / recent_closes[-self.lookback_days] - 1.0

        bear_score = 0
        bull_score = 0

        if spx_return < self.bear_return_thresh:
            bear_score += 1
        elif spx_return > self.bull_return_thresh:
            bull_score += 1

        if vix > self.bear_vix_thresh:
            bear_score += 1
        elif vix < self.bull_vix_thresh:
            bull_score += 1

        if bear_score >= 2:
            return Regime.BEAR
        if bull_score >= 2:
            return Regime.BULL
        return Regime.CHOP
