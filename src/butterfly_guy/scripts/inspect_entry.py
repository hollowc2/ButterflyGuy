"""Inspect what the strategy saw at entry for a given date.

Replicates the synthetic chain, all butterfly candidates, and the selected fly
exactly as the simulation engine would have seen them.

Usage:
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --direction CALL
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --wing 10 --rr 8.0
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator
from butterfly_guy.strategy.bias_filter import BiasScoreFilter
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

setup_logging(log_level="WARNING", json_output=False)

EASTERN = ZoneInfo("America/New_York")
ENTRY_START = dt.time(10, 0)
ENTRY_END = dt.time(10, 30)

SPX_PATH = Path("data/spx_1min.csv")
VIX_PATH = Path("data/vix_1min.csv")


def parse_args() -> tuple[dt.date, str | None, int, float]:
    date_str = next((a for a in sys.argv[1:] if a.startswith("20")), None)
    if not date_str:
        print("Usage: inspect_entry.py YYYY-MM-DD [--direction CALL|PUT] [--wing N] [--rr F]")
        sys.exit(1)
    date = dt.date.fromisoformat(date_str)

    direction: str | None = None
    wing = 10
    rr = 8.0

    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--direction" and i + 1 < len(args):
            direction = args[i + 1].upper()
        elif a == "--wing" and i + 1 < len(args):
            wing = int(args[i + 1])
        elif a == "--rr" and i + 1 < len(args):
            rr = float(args[i + 1])

    return date, direction, wing, rr


def main() -> None:
    date, direction_override, wing_width, rr_min = parse_args()

    print(f"\nLoading CSV data...")
    loader = CsvDataLoader(SPX_PATH, VIX_PATH)
    day = loader.load_day(date)
    if not day:
        print(f"No data for {date}")
        sys.exit(1)

    print(f"Date: {date}  |  VIX: {day.vix:.2f}  |  Prev close: {day.prev_close:.2f}")
    print(f"Bars available: {len(day.bars)}")
    bar_times_et = [b.ts.astimezone(EASTERN).strftime("%H:%M") for b in day.bars]
    print(f"Time range: {bar_times_et[0]} → {bar_times_et[-1]} ET\n")

    synth = SyntheticChainGenerator()
    direction_filter = DirectionFilter()
    bias_filter = BiasScoreFilter()

    settings = StrategySettings(wing_widths=[wing_width], rr_min=rr_min, spot_range=100)
    builder = ButterflyBuilder(settings)
    selector = ButterflySelector(settings)

    entry_bar = None
    direction = None

    for bar in day.bars:
        bar_et = bar.ts.astimezone(EASTERN)
        bar_time = bar_et.time()
        if not (ENTRY_START <= bar_time <= ENTRY_END):
            continue

        if direction_override:
            direction = direction_override
        else:
            direction = direction_filter.get_direction(bar.close, day.prev_close)

        if direction is None:
            continue

        entry_bar = bar
        break

    if not entry_bar:
        print(f"No entry bar found in {ENTRY_START}–{ENTRY_END} ET window.")
        sys.exit(0)

    bar_et = entry_bar.ts.astimezone(EASTERN)
    print(f"{'=' * 70}")
    print(f"  ENTRY BAR")
    print(f"{'=' * 70}")
    print(f"  Time (ET):    {bar_et.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  SPX close:    {entry_bar.close:.2f}")
    print(f"  Direction:    {direction}")
    print(f"  VIX:          {day.vix:.2f}")
    print(f"  Wing width:   {wing_width}  |  RR min: {rr_min}")

    # Generate the synthetic chain
    quotes = synth.generate_chain(
        spot=entry_bar.close,
        vix=day.vix,
        expiration=date,
        snapshot_time=entry_bar.ts,
        strike_min=entry_bar.close - 110,
        strike_max=entry_bar.close + 110,
    )

    # Show ATM chain slice (±30 pts)
    atm_quotes = [
        q for q in quotes
        if q.option_type == direction and abs(q.strike - entry_bar.close) <= 30
    ]
    atm_quotes.sort(key=lambda q: q.strike)

    print(f"\n{'=' * 70}")
    print(f"  SYNTHETIC CHAIN ({direction}, ±30pts around spot)")
    print(f"{'=' * 70}")
    print(f"  {'Strike':>7}  {'Mark':>7}  {'Bid':>7}  {'Ask':>7}  {'IV':>6}  {'Delta':>7}  {'Dist':>6}")
    print(f"  {'-' * 65}")
    for q in atm_quotes:
        dist = q.strike - entry_bar.close
        marker = " <-- ATM" if abs(dist) < 2.5 else ""
        print(
            f"  {q.strike:>7.0f}  {q.mark:>7.4f}  {q.bid:>7.4f}  {q.ask:>7.4f}  "
            f"{q.iv*100:>5.1f}%  {q.delta:>+7.4f}  {dist:>+6.1f}{marker}"
        )

    # Build all candidates
    candidates = builder.build_candidates(quotes, entry_bar.close, direction)
    best = selector.select_best(candidates)

    print(f"\n{'=' * 70}")
    print(f"  ALL CANDIDATES (wing={wing_width}, RR>={rr_min})")
    print(f"{'=' * 70}")
    if not candidates:
        print("  No candidates passed the RR filter.")
    else:
        print(f"  {'Center':>7}  {'Lower':>7}  {'Upper':>7}  {'Cost':>6}  {'MaxP':>6}  {'RR':>5}  {'Dist':>6}  {'LowerBE':>8}  {'UpperBE':>8}")
        print(f"  {'-' * 78}")
        for c in candidates:
            marker = " <-- SELECTED" if best and c.center_strike == best.center_strike else ""
            print(
                f"  {c.center_strike:>7.0f}  {c.lower_strike:>7.0f}  {c.upper_strike:>7.0f}  "
                f"{c.cost:>6.4f}  {c.max_profit:>6.4f}  {c.reward_risk:>5.2f}  "
                f"{c.distance_from_spot:>+6.1f}  {c.lower_be:>8.2f}  {c.upper_be:>8.2f}{marker}"
            )

    if best:
        print(f"\n{'=' * 70}")
        print(f"  SELECTED BUTTERFLY")
        print(f"{'=' * 70}")
        print(f"  Direction:    {best.direction}")
        print(f"  Strikes:      {best.lower_strike:.0f} / {best.center_strike:.0f} / {best.upper_strike:.0f}")
        print(f"  Cost:         {best.cost:.4f}  (+slippage 0.05 → entry {best.cost+0.05:.4f})")
        print(f"  Max profit:   {best.max_profit:.4f}  (at {best.center_strike:.0f})")
        print(f"  Reward/risk:  {best.reward_risk:.2f}x")
        print(f"  Breakevens:   {best.lower_be:.2f} — {best.upper_be:.2f}")
        profit_tent_width = best.upper_be - best.lower_be
        print(f"  Tent width:   {profit_tent_width:.2f} pts  ({best.lower_be:.2f} to {best.upper_be:.2f})")
        print(f"  Distance:     {best.distance_from_spot:.2f} pts from spot ({entry_bar.close:.2f})")
        print(f"\n  To profit at expiry, SPX must finish between {best.lower_be:.2f} and {best.upper_be:.2f}.")


if __name__ == "__main__":
    main()
