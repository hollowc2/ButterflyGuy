"""Single-day simulation engine using synthetic option chains."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.chain_cache import load_chain_day, nearest_snapshot
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
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
class SimulationParams:
    wing_width: int = 10
    rr_min: float = 8.0
    entry_start: dt.time = field(default_factory=lambda: ENTRY_START)
    entry_end: dt.time = field(default_factory=lambda: ENTRY_END)
    morning_drawdown: float = 0.50
    late_morning_drawdown: float = 0.40
    afternoon_drawdown: float = 0.30
    slippage: float = 0.05  # per spread
    direction_override: str | None = None  # "CALL" or "PUT" to force direction
    use_bias_filter: bool = False
    vix_max: float | None = None
    hold_to_expiry: bool = False  # skip all drawdown exits; let butterfly expire
    skip_morning_exit: bool = False  # never exit on drawdown during morning regime (<2h after open)
    use_vix_center: bool = False  # anchor center to VIX-implied expected move; sigma from VIX_SIGMA_BY_WIDTH
    vix_center_sigma: float = 0.0  # override per-width sigma (0.0 = use VIX_SIGMA_BY_WIDTH lookup)


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

            if ENTRY_START <= bar_time <= ENTRY_END:
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
                best = selector.select_best(candidates, target_center=target_center)

                if best:
                    entry_candidate = best
                    entry_bar = bar
                    # Apply slippage
                    entry_price = best.cost + params.slippage
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
        minutes_since_open = 0.0

        for bar in day.bars:
            bar_et = bar.ts.astimezone(EASTERN)
            if bar.ts <= entry_bar.ts:
                continue

            # Skip bars before market open tracking
            open_dt = dt.datetime(
                day.date.year, day.date.month, day.date.day, 9, 30, tzinfo=EASTERN
            )
            mins_since_open = (bar_et - open_dt).total_seconds() / 60.0

            # Determine regime
            if mins_since_open < 120:
                regime = "morning"
                drawdown_threshold = params.morning_drawdown
            elif mins_since_open < 240:
                regime = "late_morning"
                drawdown_threshold = params.late_morning_drawdown
            else:
                regime = "afternoon"
                drawdown_threshold = params.afternoon_drawdown

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
                current_value = lower_q.mark - 2 * center_q.mark + upper_q.mark
                current_value = max(0.0, current_value)
            else:
                current_value = peak_value

            peak_value = max(peak_value, current_value)

            # Check end-of-day exit (5 min before close)
            minutes_to_close = (
                dt.datetime(day.date.year, day.date.month, day.date.day, 16, 0, tzinfo=EASTERN)
                - bar_et
            ).total_seconds() / 60.0

            if minutes_to_close <= 5:
                result.exit_time = bar.ts
                result.exit_price = max(0.05, current_value - params.slippage)
                result.exit_reason = "end_of_day"
                result.peak_value = peak_value
                result.pnl = result.exit_price - result.entry_price
                return result

            # Drawdown exit (only if we've been in profit tent)
            skip_exit = params.hold_to_expiry or (params.skip_morning_exit and regime == "morning")
            if not skip_exit and peak_value > result.entry_price and peak_value > 0:
                drawdown = (peak_value - current_value) / peak_value
                if drawdown >= drawdown_threshold:
                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = f"drawdown_{regime}"
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result

        # Data ended before 15:55 ET EOD trigger — exit at last available bar
        # (handles CSV sources that stop at 15:15 ET; no-op for full-day data
        # since the loop would have already returned via minutes_to_close <= 5)
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
                    current_value = max(
                        0.0, lower_q.mark - 2 * center_q.mark + upper_q.mark
                    )
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
