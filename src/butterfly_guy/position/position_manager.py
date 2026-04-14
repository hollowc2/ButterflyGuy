"""Position value tracking and management."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from scipy.optimize import brentq

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import position_peak_value, position_pnl, position_value
from butterfly_guy.core.time_utils import get_time_regime, minutes_since_open, minutes_to_close
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord, fly_mark_value
from butterfly_guy.quant_engine.black_scholes import bs_call_price, bs_put_price

log = get_logger(__name__)


def fly_bid_value(lower: OptionQuote, center: OptionQuote, upper: OptionQuote) -> float:
    """Butterfly value at market bid (what a MM pays to buy it from you)."""
    return lower.bid + upper.bid - 2 * center.ask


@dataclass
class PositionState:
    """Current state of an open position."""

    entry_price: float
    current_value: float
    peak_value: float
    pnl: float
    drawdown_from_peak: float  # 0.0 to 1.0
    time_regime: str
    minutes_to_close: float
    minutes_since_open: float
    lower_tent: float | None = None
    upper_tent: float | None = None
    # Bid-side tracking for slippage analysis
    spread_bid: float | None = None   # fly bid = lower.bid + upper.bid - 2*center.ask
    spread_ask: float | None = None   # fly ask = lower.ask + upper.ask - 2*center.bid
    peak_bid: float | None = None     # highest spread_bid seen since entry
    bid_to_mark_ratio: float | None = None  # spread_bid / current_value; <1 always, lower = worse liquidity


def compute_tent_boundaries(
    candidate: ButterflyCandidate,
    lower_q: OptionQuote,
    center_q: OptionQuote,
    upper_q: OptionQuote,
    T_years: float,
    r: float = 0.05,
) -> tuple[float | None, float | None]:
    """Find the two spot prices where the fly's BS mark equals entry cost.

    These are the dynamic breakevens that start wide and converge to the
    at-expiry breakevens as T approaches zero.

    Returns (None, None) if the fly's theoretical max (at center) is below
    entry cost or if IV data is unavailable.
    """
    if T_years <= 0:
        return None, None

    entry_cost = candidate.cost
    kl, kc, ku = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
    wing = float(candidate.wing_width)

    # Schwab returns volatility as a percentage (e.g. 15.3 → σ=0.153)
    iv_l = lower_q.iv
    iv_c = center_q.iv
    iv_u = upper_q.iv
    if iv_l <= 0 or iv_c <= 0 or iv_u <= 0:
        return None, None

    σl = max(iv_l / 100.0, 0.001)
    σc = max(iv_c / 100.0, 0.001)
    σu = max(iv_u / 100.0, 0.001)

    pricer = bs_call_price if candidate.direction == "CALL" else bs_put_price

    def fly_val(S: float) -> float:
        return pricer(S, kl, T_years, r, σl) - 2 * pricer(S, kc, T_years, r, σc) + pricer(S, ku, T_years, r, σu)

    if fly_val(kc) <= entry_cost:
        return None, None

    try:
        lower_tent = brentq(lambda s: fly_val(s) - entry_cost, kl - wing, kc, xtol=0.01)
        upper_tent = brentq(lambda s: fly_val(s) - entry_cost, kc, ku + wing, xtol=0.01)
        return round(lower_tent, 2), round(upper_tent, 2)
    except ValueError:
        return None, None


class PositionManager:
    """Tracks position value from chain data and manages peak tracking."""

    def __init__(self, underlying: str) -> None:
        self._underlying = underlying
        self._peak_value: float = 0.0
        self._peak_bid: float = 0.0
        self._entry_price: float = 0.0

    def reset(self, entry_price: float, peak_value: float | None = None) -> None:
        """Reset for a new position. Optionally restore a persisted peak (e.g. after restart)."""
        self._entry_price = entry_price
        self._peak_value = peak_value if (peak_value and peak_value > 0) else entry_price
        self._peak_bid = 0.0

    def update_position_value(
        self,
        candidate: ButterflyCandidate,
        current_quotes: dict[float, OptionQuote],
    ) -> PositionState:
        """
        Calculate current butterfly value from latest chain quotes.
        Value = lower_mark - 2 * center_mark + upper_mark
        """
        lower_q = current_quotes.get(candidate.lower_strike)
        center_q = current_quotes.get(candidate.center_strike)
        upper_q = current_quotes.get(candidate.upper_strike)

        spread_bid: float | None = None
        spread_ask: float | None = None

        if not all([lower_q, center_q, upper_q]):
            # Use last known value if quotes missing
            current_value = self._peak_value
            log.warning("missing_quotes_for_position")
        else:
            current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
            spread_bid = max(0.0, fly_bid_value(lower_q, center_q, upper_q))
            spread_ask = lower_q.ask + upper_q.ask - 2 * center_q.bid

        # Update mark peak
        if current_value > self._peak_value:
            self._peak_value = current_value

        # Update bid peak
        if spread_bid is not None and spread_bid > self._peak_bid:
            self._peak_bid = spread_bid

        pnl = current_value - self._entry_price
        drawdown = 0.0
        if self._peak_value > 0:
            drawdown = (self._peak_value - current_value) / self._peak_value

        bid_to_mark_ratio: float | None = None
        if spread_bid is not None and current_value > 0:
            bid_to_mark_ratio = round(spread_bid / current_value, 4)

        # Determine time regime
        mins_open = minutes_since_open()
        regime = get_time_regime(mins_open)
        mins_left = minutes_to_close()

        # Compute dynamic tent boundaries (BS-derived; converge to at-expiry BE as T→0)
        lower_tent: float | None = None
        upper_tent: float | None = None
        if all([lower_q, center_q, upper_q]) and mins_left > 0:
            T_years = mins_left / (365 * 24 * 60)
            lower_tent, upper_tent = compute_tent_boundaries(
                candidate, lower_q, center_q, upper_q, T_years
            )

        # Update metrics
        position_value.labels(underlying=self._underlying).set(current_value)
        position_peak_value.labels(underlying=self._underlying).set(self._peak_value)
        position_pnl.labels(underlying=self._underlying).set(pnl)

        return PositionState(
            entry_price=self._entry_price,
            current_value=round(current_value, 4),
            peak_value=round(self._peak_value, 4),
            pnl=round(pnl, 4),
            drawdown_from_peak=round(drawdown, 4),
            time_regime=regime,
            minutes_to_close=mins_left,
            minutes_since_open=mins_open,
            lower_tent=lower_tent,
            upper_tent=upper_tent,
            spread_bid=round(spread_bid, 4) if spread_bid is not None else None,
            spread_ask=round(spread_ask, 4) if spread_ask is not None else None,
            peak_bid=round(self._peak_bid, 4) if self._peak_bid > 0 else None,
            bid_to_mark_ratio=bid_to_mark_ratio,
        )

