"""Position value tracking and management."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import position_peak_value, position_pnl, position_value
from butterfly_guy.core.time_utils import get_time_regime, minutes_since_open, minutes_to_close
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, fly_mark_value
from butterfly_guy.quant_engine.black_scholes import bs_call_price, bs_put_price, implied_vol

log = get_logger(__name__)


def fly_bid_value(lower: OptionQuote, center: OptionQuote, upper: OptionQuote) -> float:
    """Butterfly value at market bid (what a MM pays to buy it from you)."""
    return lower.bid + upper.bid - 2 * center.ask


def fly_settlement_value(candidate: ButterflyCandidate, spot_price: float) -> float:
    """Butterfly cash-settlement value from the underlying index close."""
    def leg_value(strike: float) -> float:
        if candidate.direction == "PUT":
            return max(0.0, strike - spot_price)
        return max(0.0, spot_price - strike)

    value = (
        leg_value(candidate.lower_strike)
        - 2 * leg_value(candidate.center_strike)
        + leg_value(candidate.upper_strike)
    )
    return max(0.0, round(value, 4))


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
    # spread_bid / current_value; lower means worse liquidity.
    bid_to_mark_ratio: float | None = None
    position_age_minutes: float | None = None
    peak_update_rejected: bool = False
    peak_rejection_reason: str | None = None
    pending_peak_value: float | None = None
    pending_peak_confirmation_count: int = 0
    max_leg_spread_to_mark_ratio: float | None = None
    max_leg_spread_abs: float | None = None


def compute_tent_boundaries(
    candidate: ButterflyCandidate,
    lower_q: OptionQuote,
    center_q: OptionQuote,
    upper_q: OptionQuote,
    t_years: float,
    r: float = 0.05,
) -> tuple[float | None, float | None]:
    """Find the two spot prices where the fly's BS mark equals entry cost.

    These are the dynamic breakevens that start wide and converge to the
    at-expiry breakevens as T approaches zero.

    Returns (None, None) if the fly's theoretical max (at center) is below
    entry cost or if IV data is unavailable.
    """
    if t_years <= 0:
        return None, None

    entry_cost = candidate.cost
    kl, kc, ku = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
    wing = float(candidate.wing_width)
    spot_price = candidate.spot_price

    # Schwab returns volatility as a percentage (e.g. 15.3 → σ=0.153).
    # For index options (SPX, NDX) Schwab often returns null/-999; fall back to
    # BS-implied vol from the mark price so tent lines still appear.
    def _resolve_iv(raw_iv: float | None, mark: float, strike: float) -> float:
        v = float(raw_iv) if raw_iv is not None else 0.0
        if math.isfinite(v) and v > 0:
            return v
        imp = implied_vol(mark, spot_price, strike, t_years, r, candidate.direction)
        return imp * 100.0 if imp is not None else 0.0

    iv_l = _resolve_iv(lower_q.iv, lower_q.mark, kl)
    iv_c = _resolve_iv(center_q.iv, center_q.mark, kc)
    iv_u = _resolve_iv(upper_q.iv, upper_q.mark, ku)

    if iv_l <= 0 or iv_c <= 0 or iv_u <= 0:
        return None, None

    σl = max(iv_l / 100.0, 0.001)
    σc = max(iv_c / 100.0, 0.001)
    σu = max(iv_u / 100.0, 0.001)

    pricer = bs_call_price if candidate.direction == "CALL" else bs_put_price

    def fly_val(spot: float) -> float:
        return (
            pricer(spot, kl, t_years, r, σl)
            - 2 * pricer(spot, kc, t_years, r, σc)
            + pricer(spot, ku, t_years, r, σu)
        )

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

    def __init__(
        self,
        underlying: str,
        profit_settings: ProfitManagementSettings | None = None,
    ) -> None:
        self._underlying = underlying
        self._profit_settings = profit_settings or ProfitManagementSettings()
        self._peak_value: float = 0.0
        self._peak_bid: float = 0.0
        self._entry_price: float = 0.0
        self._last_mark_value: float | None = None
        self._pending_peak_value: float | None = None
        self._pending_peak_count: int = 0

    def reset(self, entry_price: float, peak_value: float | None = None) -> None:
        """Reset for a new position. Optionally restore a persisted peak (e.g. after restart)."""
        self._entry_price = entry_price
        self._peak_value = peak_value if (peak_value and peak_value > 0) else entry_price
        self._peak_bid = 0.0
        self._last_mark_value = None
        self._pending_peak_value = None
        self._pending_peak_count = 0

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
        max_leg_spread_to_mark_ratio: float | None = None
        max_leg_spread_abs: float | None = None
        peak_update_rejected = False
        peak_rejection_reason: str | None = None

        if not all([lower_q, center_q, upper_q]):
            # Use last known value if quotes missing
            current_value = self._peak_value
            log.warning("missing_quotes_for_position")
        else:
            current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
            spread_bid = max(0.0, fly_bid_value(lower_q, center_q, upper_q))
            spread_ask = lower_q.ask + upper_q.ask - 2 * center_q.bid
            max_leg_spread_to_mark_ratio = _max_leg_spread_to_mark_ratio(
                lower_q,
                center_q,
                upper_q,
            )
            max_leg_spread_abs = max(q.ask - q.bid for q in (lower_q, center_q, upper_q))

        # Update mark peak only after configured confirmation and quote-quality gates.
        if current_value > self._peak_value:
            peak_accepted, peak_rejection_reason = self._maybe_update_peak(
                current_value=current_value,
                spread_bid=spread_bid,
                spread_ask=spread_ask,
                max_leg_spread_to_mark_ratio=max_leg_spread_to_mark_ratio,
                max_leg_spread_abs=max_leg_spread_abs,
            )
            peak_update_rejected = not peak_accepted and peak_rejection_reason is not None
        else:
            self._pending_peak_value = None
            self._pending_peak_count = 0

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
        self._last_mark_value = current_value

        # Determine time regime
        mins_open = minutes_since_open()
        regime = get_time_regime(mins_open)
        mins_left = minutes_to_close()

        # Compute dynamic tent boundaries (BS-derived; converge to at-expiry BE as T→0)
        lower_tent: float | None = None
        upper_tent: float | None = None
        if all([lower_q, center_q, upper_q]) and mins_left > 0:
            t_years = mins_left / (365 * 24 * 60)
            lower_tent, upper_tent = compute_tent_boundaries(
                candidate, lower_q, center_q, upper_q, t_years
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
            peak_update_rejected=peak_update_rejected,
            peak_rejection_reason=peak_rejection_reason,
            pending_peak_value=round(self._pending_peak_value, 4)
            if self._pending_peak_value is not None
            else None,
            pending_peak_confirmation_count=self._pending_peak_count,
            max_leg_spread_to_mark_ratio=round(max_leg_spread_to_mark_ratio, 4)
            if max_leg_spread_to_mark_ratio is not None
            else None,
            max_leg_spread_abs=round(max_leg_spread_abs, 4)
            if max_leg_spread_abs is not None
            else None,
        )

    def _maybe_update_peak(
        self,
        *,
        current_value: float,
        spread_bid: float | None,
        spread_ask: float | None,
        max_leg_spread_to_mark_ratio: float | None,
        max_leg_spread_abs: float | None,
    ) -> tuple[bool, str | None]:
        peak_settings = self._profit_settings.peak_tracking
        quote_settings = self._profit_settings.quote_quality

        if current_value < quote_settings.min_mark_value:
            self._clear_pending_peak()
            return False, "mark_below_minimum"

        if peak_settings.require_quote_quality and not _quote_quality_ok(
            current_value=current_value,
            spread_bid=spread_bid,
            spread_ask=spread_ask,
            bid_to_mark_ratio=(spread_bid / current_value)
            if spread_bid is not None and current_value > 0
            else None,
            max_leg_spread_to_mark_ratio=max_leg_spread_to_mark_ratio,
            max_leg_spread_abs=max_leg_spread_abs,
            settings=quote_settings,
        ):
            self._clear_pending_peak()
            return False, "quote_quality"

        if self._last_mark_value is not None and self._last_mark_value > 0:
            jump = current_value - self._last_mark_value
            jump_ratio = jump / self._last_mark_value
            if (
                peak_settings.max_jump_ratio is not None
                and peak_settings.max_jump_abs is not None
                and jump_ratio > peak_settings.max_jump_ratio
                and jump > peak_settings.max_jump_abs
            ):
                self._clear_pending_peak()
                log.info(
                    "peak_update_rejected",
                    reason="mark_jump",
                    current=current_value,
                    previous=self._last_mark_value,
                    jump=jump,
                    jump_ratio=jump_ratio,
                )
                return False, "mark_jump"

        confirmation_polls = max(1, peak_settings.confirmation_polls)
        if confirmation_polls == 1:
            self._peak_value = current_value
            self._clear_pending_peak()
            return True, None

        tolerance = max(0.0, peak_settings.confirmation_tolerance_ratio)
        if (
            self._pending_peak_value is None
            or current_value < self._pending_peak_value * (1 - tolerance)
        ):
            self._pending_peak_value = current_value
            self._pending_peak_count = 1
            return False, "pending_confirmation"

        self._pending_peak_value = max(self._pending_peak_value, current_value)
        self._pending_peak_count += 1
        if self._pending_peak_count < confirmation_polls:
            return False, "pending_confirmation"

        self._peak_value = self._pending_peak_value
        self._clear_pending_peak()
        return True, None

    def _clear_pending_peak(self) -> None:
        self._pending_peak_value = None
        self._pending_peak_count = 0


def _max_leg_spread_to_mark_ratio(
    lower_q: OptionQuote,
    center_q: OptionQuote,
    upper_q: OptionQuote,
) -> float | None:
    ratios = []
    for quote in (lower_q, center_q, upper_q):
        if quote.mark <= 0:
            continue
        ratios.append((quote.ask - quote.bid) / quote.mark)
    return max(ratios) if ratios else None


def _quote_quality_ok(
    *,
    current_value: float,
    spread_bid: float | None,
    spread_ask: float | None,
    bid_to_mark_ratio: float | None,
    max_leg_spread_to_mark_ratio: float | None,
    max_leg_spread_abs: float | None,
    settings,
) -> bool:
    if current_value < settings.min_mark_value:
        return False
    if spread_bid is None or spread_ask is None or bid_to_mark_ratio is None:
        return False
    if spread_bid <= 0:
        return False
    if bid_to_mark_ratio < settings.min_bid_to_mark_ratio:
        return False
    if settings.max_spread_width_ratio is not None and current_value > 0:
        spread_width_ratio = (spread_ask - spread_bid) / current_value
        if spread_width_ratio > settings.max_spread_width_ratio:
            return False
    if (
        settings.max_leg_spread_to_mark_ratio is not None
        and max_leg_spread_to_mark_ratio is not None
        and max_leg_spread_to_mark_ratio > settings.max_leg_spread_to_mark_ratio
    ):
        return False
    if (
        settings.max_leg_spread_abs is not None
        and max_leg_spread_abs is not None
        and max_leg_spread_abs > settings.max_leg_spread_abs
    ):
        return False
    return True
