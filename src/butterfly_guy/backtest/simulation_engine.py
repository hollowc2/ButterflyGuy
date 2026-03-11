"""Single-day simulation engine using synthetic option chains."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

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

    def simulate_day(self, day: DayData, params: SimulationParams) -> DayResult:
        """Simulate one trading day."""
        result = DayResult(date=day.date)
        expiration = day.date

        # Only simulate Monday–Friday
        if day.date.weekday() >= 5:
            return result

        # Find entry bar
        entry_candidate: ButterflyCandidate | None = None
        entry_bar: MinuteBar | None = None

        for bar in day.bars:
            bar_et = bar.ts.astimezone(EASTERN)
            bar_time = bar_et.time()

            if ENTRY_START <= bar_time <= ENTRY_END:
                # Generate synthetic chain at this bar
                quotes = self.synth.generate_chain(
                    spot=bar.close,
                    vix=day.vix,
                    expiration=expiration,
                    snapshot_time=bar.ts,
                    strike_min=bar.close - 80,
                    strike_max=bar.close + 80,
                )

                direction = self.direction_filter.get_direction(
                    bar.close, day.prev_close
                )

                # Override settings to use single wing_width from params
                settings_override = StrategySettings(
                    wing_widths=[params.wing_width],
                    rr_min=params.rr_min,
                    spot_range=60,
                )
                builder = ButterflyBuilder(settings_override)
                candidates = builder.build_candidates(quotes, bar.close, direction)
                best = self.selector.select_best(candidates)

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
            quotes = self.synth.generate_chain(
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
            if peak_value > result.entry_price and peak_value > 0:
                drawdown = (peak_value - current_value) / peak_value
                if drawdown >= drawdown_threshold:
                    result.exit_time = bar.ts
                    result.exit_price = max(0.05, current_value - params.slippage)
                    result.exit_reason = f"drawdown_{regime}"
                    result.peak_value = peak_value
                    result.pnl = result.exit_price - result.entry_price
                    return result

        # Expired worthless
        result.exit_reason = "expired"
        result.exit_price = 0.0
        result.peak_value = peak_value
        result.pnl = -result.entry_price
        return result
