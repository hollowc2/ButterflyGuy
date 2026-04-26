from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from butterfly_guy.strategy.regime_classifier import Regime


@dataclass
class GapRegimeFilter:
    bull_call_bias: bool = False
    min_gap_pct: float | None = None

    def apply(
        self, spot: float, prev_close: float, regime: Regime
    ) -> tuple[Literal["CALL", "PUT"] | None, str | None]:
        gap_pct = (spot - prev_close) / prev_close
        if self.min_gap_pct is not None and abs(gap_pct) < self.min_gap_pct:
            return None, "gap_below_min"
        if self.bull_call_bias and regime == Regime.BULL and gap_pct < 0:
            return "CALL", None
        return None, None
