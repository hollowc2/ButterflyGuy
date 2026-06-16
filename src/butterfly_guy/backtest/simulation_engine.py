"""Single-day simulation engine using synthetic option chains."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Literal
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.chain_cache import load_chain_day, nearest_snapshot
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.config import ProfitProtectorSettings, StrategySettings, TimeRegime
from butterfly_guy.core.time_utils import get_time_regime
from butterfly_guy.data.schemas import ButterflyCandidate, fly_mark_value
from butterfly_guy.position.profit_policy import (
    ProfitManagementStrategy,
    effective_drawdown_threshold,
    profitprotector_floor_decision,
)
from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator
from butterfly_guy.strategy.bias_filter import BiasScoreFilter
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder, vix_target_center
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter
from butterfly_guy.strategy.regime_classifier import Regime, RegimeClassifier
from butterfly_guy.strategy.regime_filter import RegimeFilter

EASTERN = ZoneInfo("America/New_York")
PACIFIC = ZoneInfo("America/Los_Angeles")

ENTRY_START = dt.time(10, 0)   # PST 7:00 = EST 10:00
ENTRY_END = dt.time(10, 30)    # PST 7:30 = EST 10:30
MONITOR_INTERVAL_MINUTES = 10


@dataclass
class DrawdownWindow:
    start_min: float
    end_min: float
    threshold: float
    label: str


@dataclass
class SimulationParams:
    wing_width: int = 10
    rr_min: float = 8.0
    entry_start: dt.time = field(default_factory=lambda: ENTRY_START)
    entry_end: dt.time = field(default_factory=lambda: ENTRY_END)
    morning_drawdown: float = 0.50
    late_morning_drawdown: float = 0.40
    afternoon_drawdown: float = 0.30
    slippage: float = 0.05  # per spread
    exit_before_close_minutes: int = 0
    paper_commission_per_contract: float = 0.65
    quantity: int = 1
    direction_override: str | None = None  # "CALL" or "PUT" to force direction
    use_bias_filter: bool = False
    vix_max: float | None = None
    hold_to_expiry: bool = False  # skip all drawdown exits; let butterfly expire
    # Never exit on drawdown during morning regime (<2h after open).
    skip_morning_exit: bool = False
    # Anchor center to VIX-implied expected move.
    use_vix_center: bool = False
    selection_method: Literal["VIX", "TARGET_COST", "BEST_RR"] = "VIX"
    max_cost_per_width: dict[int, float] = field(default_factory=dict)
    # Override per-width sigma (0.0 = use VIX_SIGMA_BY_WIDTH lookup).
    vix_center_sigma: float = 0.0
    # Exit if position loses this fraction of cost (no profit required).
    max_loss_from_cost: float = 0.50
    use_absolute_loss_stop: bool = True  # set False to disable the absolute loss stop entirely
    drawdown_schedule: tuple[DrawdownWindow, ...] | None = None
    drawdown_confirmation_polls: int = 1
    min_peak_profit_ratio: float = 1.0
    min_hold_minutes: float = 0.0
    profit_management_strategy: ProfitManagementStrategy = "peakvaluetrailer"
    profitprotector: ProfitProtectorSettings = field(default_factory=ProfitProtectorSettings)

    def paper_entry_commission(self) -> float:
        """Paper trading commission: 4 legs × quantity × rate."""
        return 4 * self.quantity * self.paper_commission_per_contract / 100


@dataclass
class RegimeDispatch:
    """Maps Regime → SimulationParams for use with simulate_day_adaptive().

    Per-regime params should be set to known-optimal values from regime sweep.
    default_params is the fallback for UNKNOWN (insufficient history).
    """

    classifier: RegimeClassifier
    bull_params: SimulationParams
    bear_params: SimulationParams
    chop_params: SimulationParams
    default_params: SimulationParams

    def params_for(self, regime: Regime) -> SimulationParams:
        if regime == Regime.BULL:
            return self.bull_params
        if regime == Regime.BEAR:
            return self.bear_params
        if regime == Regime.CHOP:
            return self.chop_params
        return self.default_params  # UNKNOWN


@dataclass
class DayResult:
    date: dt.date
    traded: bool = False
    direction: str = ""
    entry_time: dt.datetime | None = None
    entry_price: float = 0.0
    exit_time: dt.datetime | None = None
    exit_price: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0
    peak_value: float = 0.0
    center_strike: float = 0.0
    wing_width: int = 0


class SimulationEngine:
    """Runs full strategy on a single day using synthetic options."""

    def __init__(self, settings: StrategySettings | None = None) -> None:
        self.synth = SyntheticChainGenerator()
        self.builder = ButterflyBuilder(settings or StrategySettings())
        self.selector = ButterflySelector()
        self.direction_filter = DirectionFilter()
        self.bias_filter = BiasScoreFilter()
        self._regime_filter_cache: dict[float, RegimeFilter] = {}

    @staticmethod
    def _drawdown_rule(
        params: SimulationParams,
        mins_since_open: float,
    ) -> tuple[float, str, str]:
        regime = get_time_regime(mins_since_open)
        if params.drawdown_schedule:
            for window in params.drawdown_schedule:
                if window.start_min <= mins_since_open < window.end_min:
                    return window.threshold, window.label, regime
        return {
            "morning": params.morning_drawdown,
            "late_morning": params.late_morning_drawdown,
            "afternoon": params.afternoon_drawdown,
        }[regime], regime, regime

    @staticmethod
    def _profit_exit_reason(
        params: SimulationParams,
        *,
        entry_price: float,
        current_value: float,
        peak_value: float,
        drawdown: float,
        drawdown_threshold: float,
        drawdown_label: str,
    ) -> str | None:
        if params.profit_management_strategy == "profitprotector":
            floor_decision = profitprotector_floor_decision(
                entry_price=entry_price,
                current_value=current_value,
                peak_value=peak_value,
                settings=params.profitprotector,
            )
            if floor_decision is not None:
                return floor_decision.reason

        regime_config = TimeRegime(
            start_minutes_after_open=0,
            end_minutes_after_open=0,
            drawdown_threshold=drawdown_threshold,
        )
        threshold = effective_drawdown_threshold(
            strategy=params.profit_management_strategy,
            entry_price=entry_price,
            peak_value=peak_value,
            regime_config=regime_config,
            protector_settings=params.profitprotector,
        )
        if drawdown >= threshold:
            return f"drawdown_{drawdown_label}"
        return None

    def simulate_day(self, day: DayData, params: SimulationParams) -> DayResult:
        """Simulate one trading day."""
        result = DayResult(date=day.date)
        expiration = day.date

        # Only simulate Monday–Friday
        if day.date.weekday() >= 5:
            return result

        # Load real chain cache for this day (None if not available)
        real_chains = load_chain_day(day.date)

        # Find entry bar
        entry_candidate: ButterflyCandidate | None = None
        entry_bar: MinuteBar | None = None

        for bar in day.bars:
            bar_et = bar.ts.astimezone(EASTERN)
            bar_time = bar_et.time()

            if params.entry_start <= bar_time <= params.entry_end:
                # Use real chain if available, else synthetic
                real_quotes = nearest_snapshot(real_chains, bar.ts) if real_chains else None
                quotes = real_quotes if real_quotes else self.synth.generate_chain(
                    spot=bar.close,
                    vix=day.vix,
                    expiration=expiration,
                    snapshot_time=bar.ts,
                    strike_min=bar.close - 110,
                    strike_max=bar.close + 110,
                )

                if params.direction_override:
                    direction = params.direction_override
                elif params.use_bias_filter:
                    bars_so_far = [b for b in day.bars if b.ts <= bar.ts]
                    direction = self.bias_filter.get_direction(
                        bars=bars_so_far, prev_close=day.prev_close, entry_close=bar.close
                    )
                else:
                    direction = self.direction_filter.get_direction(bar.close, day.prev_close)

                if direction is None:
                    continue  # bias filter said no trade; try next bar in entry window

                if params.vix_max is not None and day.vix_bars:
                    rf = self._regime_filter_cache.setdefault(
                        params.vix_max, RegimeFilter(params.vix_max)
                    )
                    if not rf.should_trade(day.vix_bars, bar.ts):
                        continue  # VIX too high at this bar; try next bar in window

                settings_override = StrategySettings(
                    wing_widths=[params.wing_width],
                    rr_min=params.rr_min,
                    spot_range=100,
                    max_cost_per_width=params.max_cost_per_width,
                )
                builder = ButterflyBuilder(settings_override)
                candidates = builder.build_candidates(quotes, bar.close, direction)

                target_center = None
                if params.use_vix_center and day.vix:
                    target_center = vix_target_center(
                        vix=day.vix,
                        spot=bar.close,
                        direction=direction,
                        wing_width=params.wing_width,
                        sigma_fraction=params.vix_center_sigma or None,
                    )

                selector = ButterflySelector(settings_override)
                if params.selection_method == "TARGET_COST":
                    best = selector.select_best_by_target_cost(candidates)
                elif params.selection_method == "BEST_RR":
                    best = selector.select_best(candidates, target_center=None)
                else:  # VIX (default)
                    best = selector.select_best(
                        candidates,
                        target_center=target_center,
                    )

                if best:
                    entry_candidate = best
                    entry_bar = bar
                    # Debit at composite ask (natural buy), plus slippage/commission
                    entry_debit = best.ask if best.ask > 0 else best.cost
                    entry_price = entry_debit + params.slippage + params.paper_entry_commission()
                    result.traded = True
                    result.direction = direction
                    result.entry_time = bar.ts
                    result.entry_price = entry_price
                    result.center_strike = best.center_strike
                    result.wing_width = best.wing_width
                    break

        if not entry_candidate or not entry_bar:
            return result

        # Monitor position until exit
        peak_value = result.entry_price
        pending_drawdown_reason: str | None = None
        pending_drawdown_count = 0

        for bar in day.bars:
            bar_et = bar.ts.astimezone(EASTERN)
            if bar.ts <= entry_bar.ts:
                continue

            # Skip bars before market open tracking
            open_dt = dt.datetime(
                day.date.year, day.date.month, day.date.day, 9, 30, tzinfo=EASTERN
            )
            mins_since_open = (bar_et - open_dt).total_seconds() / 60.0

            # Determine drawdown rule
            drawdown_threshold, drawdown_label, regime = self._drawdown_rule(
                params,
                mins_since_open,
            )

            # Calculate current butterfly value
            real_quotes = nearest_snapshot(real_chains, bar.ts) if real_chains else None
            quotes = real_quotes if real_quotes else self.synth.generate_chain(
                spot=bar.close,
                vix=day.vix,
                expiration=expiration,
                snapshot_time=bar.ts,
                strike_min=entry_candidate.lower_strike - 5,
                strike_max=entry_candidate.upper_strike + 5,
            )
            quote_map = {q.strike: q for q in quotes if q.option_type == entry_candidate.direction}

            lower_q = quote_map.get(entry_candidate.lower_strike)
            center_q = quote_map.get(entry_candidate.center_strike)
            upper_q = quote_map.get(entry_candidate.upper_strike)

            if lower_q and center_q and upper_q:
                current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
            else:
                current_value = peak_value

            peak_value = max(peak_value, current_value)

            # Optional pre-close exit; disabled by default for cash-settled indexes.
            minutes_to_close = (
                dt.datetime(day.date.year, day.date.month, day.date.day, 16, 0, tzinfo=EASTERN)
                - bar_et
            ).total_seconds() / 60.0

            if (
                params.exit_before_close_minutes > 0
                and minutes_to_close <= params.exit_before_close_minutes
            ):
                result.exit_time = bar.ts
                result.exit_price = max(0.05, current_value - params.slippage)
                result.exit_reason = "end_of_day"
                result.peak_value = peak_value
                result.pnl = result.exit_price - result.entry_price
                return result

            # Absolute loss stop — fires regardless of peak (no profit required)
            if (
                not params.hold_to_expiry
                and params.use_absolute_loss_stop
                and result.entry_price > 0
            ):
                loss_from_cost = (result.entry_price - current_value) / result.entry_price
                if loss_from_cost >= params.max_loss_from_cost:
                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = "absolute_loss_stop"
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result

            # Drawdown exit (only if we've been in profit tent)
            skip_exit = params.hold_to_expiry or (params.skip_morning_exit and regime == "morning")
            entry_age_minutes = (bar.ts - entry_bar.ts).total_seconds() / 60.0
            if (
                not skip_exit
                and entry_age_minutes >= params.min_hold_minutes
                and peak_value >= result.entry_price * params.min_peak_profit_ratio
                and peak_value > result.entry_price
                and peak_value > 0
            ):
                drawdown = (peak_value - current_value) / peak_value
                exit_reason = self._profit_exit_reason(
                    params,
                    entry_price=result.entry_price,
                    current_value=current_value,
                    peak_value=peak_value,
                    drawdown=drawdown,
                    drawdown_threshold=drawdown_threshold,
                    drawdown_label=drawdown_label,
                )
                if exit_reason:
                    if pending_drawdown_reason == exit_reason:
                        pending_drawdown_count += 1
                    else:
                        pending_drawdown_reason = exit_reason
                        pending_drawdown_count = 1

                    if pending_drawdown_count < max(1, params.drawdown_confirmation_polls):
                        continue

                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = exit_reason
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result
                pending_drawdown_reason = None
                pending_drawdown_count = 0
            else:
                pending_drawdown_reason = None
                pending_drawdown_count = 0

        # Data ended before the session close — exit at last available bar
        # (handles CSV sources that stop at 15:15 ET; no-op for full-day data
        # when no explicit pre-close exit was configured)
        if day.bars:
            last_bar = day.bars[-1]
            last_bar_et = last_bar.ts.astimezone(EASTERN)
            if last_bar_et.time() >= dt.time(10, 30):
                real_quotes = nearest_snapshot(real_chains, last_bar.ts) if real_chains else None
                quotes = real_quotes if real_quotes else self.synth.generate_chain(
                    spot=last_bar.close,
                    vix=day.vix,
                    expiration=expiration,
                    snapshot_time=last_bar.ts,
                    strike_min=entry_candidate.lower_strike - 5,
                    strike_max=entry_candidate.upper_strike + 5,
                )
                quote_map = {
                    q.strike: q
                    for q in quotes
                    if q.option_type == entry_candidate.direction
                }
                lower_q = quote_map.get(entry_candidate.lower_strike)
                center_q = quote_map.get(entry_candidate.center_strike)
                upper_q = quote_map.get(entry_candidate.upper_strike)
                if lower_q and center_q and upper_q:
                    current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
                else:
                    current_value = 0.0
                result.exit_time = last_bar.ts
                result.exit_price = max(0.05, current_value - params.slippage)
                result.exit_reason = "end_of_day"
                result.peak_value = peak_value
                result.pnl = result.exit_price - result.entry_price
                return result

        # Expired worthless (no usable bars after entry)
        result.exit_reason = "expired"
        result.exit_price = 0.0
        result.peak_value = peak_value
        result.pnl = -result.entry_price
        return result

    def simulate_day_from_entry(
        self,
        day: DayData,
        params: SimulationParams,
        entry_candidate: ButterflyCandidate,
        entry_price: float,
        entry_time: dt.datetime,
    ) -> DayResult:
        """Simulate intraday using BS pricing, pinned to a pre-selected real entry.

        Skips entry selection entirely. Uses the passed candidate's strikes as the
        position and entry_price as the PnL baseline. Intended for --compare-synthetic-
        same-entry: caller patches load_chain_day to None before calling so all
        intraday pricing falls through to self.synth.
        """
        result = DayResult(date=day.date)
        result.traded = True
        result.direction = entry_candidate.direction
        result.entry_time = entry_time
        result.entry_price = entry_price
        result.center_strike = entry_candidate.center_strike
        result.wing_width = entry_candidate.wing_width

        expiration = day.date
        real_chains = load_chain_day(day.date)  # None when caller patches it out
        peak_value = entry_price
        pending_drawdown_reason: str | None = None
        pending_drawdown_count = 0
        open_dt = dt.datetime(day.date.year, day.date.month, day.date.day, 9, 30, tzinfo=EASTERN)

        for bar in day.bars:
            bar_et = bar.ts.astimezone(EASTERN)
            if bar.ts <= entry_time:
                continue

            mins_since_open = (bar_et - open_dt).total_seconds() / 60.0
            drawdown_threshold, drawdown_label, regime = self._drawdown_rule(
                params,
                mins_since_open,
            )

            real_quotes = nearest_snapshot(real_chains, bar.ts) if real_chains else None
            quotes = real_quotes if real_quotes else self.synth.generate_chain(
                spot=bar.close,
                vix=day.vix,
                expiration=expiration,
                snapshot_time=bar.ts,
                strike_min=entry_candidate.lower_strike - 5,
                strike_max=entry_candidate.upper_strike + 5,
            )
            quote_map = {q.strike: q for q in quotes if q.option_type == entry_candidate.direction}
            lower_q = quote_map.get(entry_candidate.lower_strike)
            center_q = quote_map.get(entry_candidate.center_strike)
            upper_q = quote_map.get(entry_candidate.upper_strike)

            if lower_q and center_q and upper_q:
                current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
            else:
                current_value = peak_value

            peak_value = max(peak_value, current_value)

            minutes_to_close = (
                dt.datetime(day.date.year, day.date.month, day.date.day, 16, 0, tzinfo=EASTERN)
                - bar_et
            ).total_seconds() / 60.0

            if (
                params.exit_before_close_minutes > 0
                and minutes_to_close <= params.exit_before_close_minutes
            ):
                result.exit_time = bar.ts
                result.exit_price = max(0.05, current_value - params.slippage)
                result.exit_reason = "end_of_day"
                result.peak_value = peak_value
                result.pnl = result.exit_price - result.entry_price
                return result

            if (
                not params.hold_to_expiry
                and params.use_absolute_loss_stop
                and result.entry_price > 0
            ):
                loss_from_cost = (result.entry_price - current_value) / result.entry_price
                if loss_from_cost >= params.max_loss_from_cost:
                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = "absolute_loss_stop"
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result

            skip_exit = params.hold_to_expiry or (params.skip_morning_exit and regime == "morning")
            entry_age_minutes = (bar.ts - entry_time).total_seconds() / 60.0
            if (
                not skip_exit
                and entry_age_minutes >= params.min_hold_minutes
                and peak_value >= result.entry_price * params.min_peak_profit_ratio
                and peak_value > result.entry_price
                and peak_value > 0
            ):
                drawdown = (peak_value - current_value) / peak_value
                exit_reason = self._profit_exit_reason(
                    params,
                    entry_price=result.entry_price,
                    current_value=current_value,
                    peak_value=peak_value,
                    drawdown=drawdown,
                    drawdown_threshold=drawdown_threshold,
                    drawdown_label=drawdown_label,
                )
                if exit_reason:
                    if pending_drawdown_reason == exit_reason:
                        pending_drawdown_count += 1
                    else:
                        pending_drawdown_reason = exit_reason
                        pending_drawdown_count = 1

                    if pending_drawdown_count < max(1, params.drawdown_confirmation_polls):
                        continue

                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = exit_reason
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result
                pending_drawdown_reason = None
                pending_drawdown_count = 0
            else:
                pending_drawdown_reason = None
                pending_drawdown_count = 0

        if day.bars:
            last_bar = day.bars[-1]
            last_bar_et = last_bar.ts.astimezone(EASTERN)
            if last_bar_et.time() >= dt.time(10, 30):
                real_quotes = nearest_snapshot(real_chains, last_bar.ts) if real_chains else None
                quotes = real_quotes if real_quotes else self.synth.generate_chain(
                    spot=last_bar.close,
                    vix=day.vix,
                    expiration=expiration,
                    snapshot_time=last_bar.ts,
                    strike_min=entry_candidate.lower_strike - 5,
                    strike_max=entry_candidate.upper_strike + 5,
                )
                quote_map = {
                    q.strike: q
                    for q in quotes
                    if q.option_type == entry_candidate.direction
                }
                lower_q = quote_map.get(entry_candidate.lower_strike)
                center_q = quote_map.get(entry_candidate.center_strike)
                upper_q = quote_map.get(entry_candidate.upper_strike)
                if lower_q and center_q and upper_q:
                    current_value = max(0.0, fly_mark_value(lower_q, center_q, upper_q))
                else:
                    current_value = 0.0
                result.exit_time = last_bar.ts
                result.exit_price = max(0.05, current_value - params.slippage)
                result.exit_reason = "end_of_day"
                result.peak_value = peak_value
                result.pnl = result.exit_price - result.entry_price
                return result

        result.exit_reason = "expired"
        result.exit_price = 0.0
        result.peak_value = peak_value
        result.pnl = -result.entry_price
        return result

    def simulate_day_adaptive(
        self, day: DayData, dispatch: RegimeDispatch
    ) -> tuple[DayResult, Regime]:
        """Classify regime then delegate to simulate_day() with matching params.

        Returns (DayResult, Regime) so callers can accumulate per-regime stats.
        """
        regime = dispatch.classifier.classify(day.recent_closes, day.vix)
        params = dispatch.params_for(regime)
        result = self.simulate_day(day, params)
        return result, regime
