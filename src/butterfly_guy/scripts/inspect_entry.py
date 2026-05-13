"""Inspect what the strategy saw at entry for a given date.

Replicates the synthetic chain, all butterfly candidates, and the selected fly
exactly as the simulation engine would have seen them.

Usage:
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --direction CALL
    uv run python src/butterfly_guy/scripts/inspect_entry.py 2025-06-03 --wing 10 --rr 8.0 --method TARGET_COST
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.backtest.db_loader import DbDataLoader
from butterfly_guy.core.config import StrategySettings, load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.quant_engine.synthetic_chain import SyntheticChainGenerator
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

setup_logging(log_level="WARNING", json_output=False)

EASTERN = ZoneInfo("America/New_York")
ENTRY_START = dt.time(10, 0)
ENTRY_END = dt.time(10, 30)


def print_help() -> None:
    print("\nButterfly Entry Inspector - Help")
    print("=" * 40)
    print("Replicates the strategy logic for a specific historical date.")
    print("\nUsage:")
    print("  uv run python src/butterfly_guy/scripts/inspect_entry.py YYYY-MM-DD [options]")
    print("\nRequired:")
    print("  YYYY-MM-DD          The date to inspect (e.g., 2026-03-30)")
    print("\nOptions:")
    print("  --direction D       Force 'CALL' or 'PUT' (default: automatic based on gap)")
    print("  --wing N            Wing width: 10, 20, or 30 (default: 10)")
    print("  --rr F              Minimum Reward/Risk ratio (default: 8.0)")
    print("  --asset A           'SPX', 'NDX', or 'XSP' (default: SPX)")
    print("  --method M          Selection method: 'TARGET_COST', 'VIX', or 'BEST_RR'")
    print("  --csv               Load from flat data/*.csv instead of the database")
    print("  --help              Show this screen")
    print("\nMethods:")
    print("  TARGET_COST         Pick the candidate closest to target debit ($3.00/30w, etc.)")
    print("  VIX                 Pick farthest OTM valid candidate near VIX target")
    print("  BEST_RR             Pick the candidate with the highest Reward/Risk ratio")
    print()


def parse_args():
    if "--help" in sys.argv:
        print_help()
        sys.exit(0)

    date_str = next((a for a in sys.argv[1:] if a.startswith("20")), None)
    if not date_str:
        print_help()
        sys.exit(1)

    date = dt.date.fromisoformat(date_str)

    direction: str | None = None
    wing = 10
    rr = 8.0
    asset = "SPX"
    method = "TARGET_COST"
    use_csv = False

    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--direction" and i + 1 < len(args):
            direction = args[i + 1].upper()
        elif a == "--wing" and i + 1 < len(args):
            wing = int(args[i + 1])
        elif a == "--rr" and i + 1 < len(args):
            rr = float(args[i + 1])
        elif a == "--asset" and i + 1 < len(args):
            asset = args[i + 1].upper()
        elif a == "--method" and i + 1 < len(args):
            method = args[i + 1].upper()
        elif a == "--csv":
            use_csv = True

    return date, direction, wing, rr, asset, method, use_csv


def main() -> None:
    date, direction_override, wing_width, rr_min, asset, method, use_csv = parse_args()

    if use_csv:
        spx_path = Path(f"data/{asset.lower()}_1min.csv")
        vix_path = Path("data/vix_1min.csv")
        print(f"\nLoading CSV data for {asset}...")
        loader = CsvDataLoader(spx_path, vix_path)
    else:
        cfg = load_config()
        print(f"\nLoading DB data for {asset} on {date}...")
        try:
            loader = DbDataLoader(cfg.database.dsn, underlying=asset)
        except Exception as e:
            print(f"DB connection failed: {e}")
            print("Tip: pass --csv to load from flat CSV files instead.")
            sys.exit(1)

    day = loader.load_day(date)
    if not day:
        print(f"No data found for {date} ({asset}) in the {'DB' if not use_csv else 'CSV'}.")
        sys.exit(1)

    print(f"Date: {date}  |  VIX: {day.vix:.2f}  |  Prev close: {day.prev_close:.2f}")
    print(f"Bars available: {len(day.bars)}")
    bar_times_et = [b.ts.astimezone(EASTERN).strftime("%H:%M") for b in day.bars]
    print(f"Time range: {bar_times_et[0]} → {bar_times_et[-1]} ET\n")

    synth = SyntheticChainGenerator()  # kept as fallback for days without DB chain data
    direction_filter = DirectionFilter()

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

    # ------------------------------------------------------------------ #
    # Option chain: real data from DB, synthetic as fallback              #
    # ------------------------------------------------------------------ #
    quotes: list = []
    chain_source = "SYNTHETIC"

    if not use_csv and hasattr(loader, "load_chain_at_time"):
        quotes = loader.load_chain_at_time(
            underlying=asset,
            expiration=date,
            at=entry_bar.ts,
            window_minutes=15,
        )
        if quotes:
            chain_source = "REAL (DB)"

    if not quotes:
        if chain_source == "REAL (DB)":
            print("  ⚠  No DB chain snapshot found near entry — falling back to synthetic chain.")
        quotes = synth.generate_chain(
            spot=entry_bar.close,
            vix=day.vix,
            expiration=date,
            snapshot_time=entry_bar.ts,
            strike_min=entry_bar.close - 110,
            strike_max=entry_bar.close + 110,
        )
        chain_source = "SYNTHETIC"

    # Show ATM chain slice (±30 pts)
    atm_quotes = [
        q for q in quotes
        if q.option_type == direction and abs(q.strike - entry_bar.close) <= 30
    ]
    atm_quotes.sort(key=lambda q: q.strike)

    print(f"\n{'=' * 70}")
    print(f"  OPTION CHAIN [{chain_source}] ({direction}, ±30pts around spot)")
    print(f"{'=' * 70}")
    print(f"  {'Strike':>7}  {'Mark':>7}  {'Bid':>7}  {'Ask':>7}  {'IV':>6}  {'Delta':>7}  {'Dist':>6}")
    print(f"  {'-' * 65}")
    for q in atm_quotes:
        dist = q.strike - entry_bar.close
        marker = " <-- ATM" if abs(dist) < 2.5 else ""
        iv_str = f"{q.iv*100:>5.1f}%" if q.iv else "   N/A"
        delta_str = f"{q.delta:>+7.4f}" if q.delta else "    N/A"
        print(
            f"  {q.strike:>7.0f}  {q.mark:>7.4f}  {q.bid:>7.4f}  {q.ask:>7.4f}  "
            f"{iv_str}  {delta_str}  {dist:>+6.1f}{marker}"
        )

    # Build all candidates (including those that fail filters for visualization)
    all_candidates = builder.build_candidates(quotes, entry_bar.close, direction, include_all=True)
    
    # Identify which ones would have actually passed the official filter
    def passes_filter(c):
        max_cost = settings.max_cost_per_width.get(c.wing_width, float("inf"))
        return c.cost >= 0.05 and c.cost <= max_cost and c.reward_risk >= settings.rr_min

    valid_candidates = [c for c in all_candidates if passes_filter(c)]

    if method == "TARGET_COST":
        best = selector.select_best_by_target_cost(valid_candidates)
    elif method == "VIX":
        from butterfly_guy.strategy.butterfly_builder import vix_target_center
        target_center = vix_target_center(
            vix=day.vix, spot=entry_bar.close,
            direction=direction, wing_width=wing_width,
        )
        best = selector.select_farthest_otm(valid_candidates, target_center=target_center)
    else:
        # Default / BEST_RR
        best = selector.select_best(valid_candidates)

    print(f"\n{'=' * 70}")
    print(f"  ALL CANDIDATES (wing={wing_width}, RR>={rr_min})")
    print(f"{'=' * 70}")
    
    # We want to show:
    # 1. All valid candidates
    # 2. Some rejected candidates that were closer to ATM than the selected one
    
    # Filter all_candidates to just the requested wing width
    width_candidates = [c for c in all_candidates if c.wing_width == wing_width]
    
    if not width_candidates:
        print("  No candidates found for this wing width.")
    else:
        print(f"  {'Center':>7}  {'Lower':>7}  {'Upper':>7}  {'Cost':>6}  {'MaxP':>6}  {'RR':>5}  {'Dist':>6}  {'LowerBE':>8}  {'UpperBE':>8}")
        print(f"  {'-' * 78}")
        
        # Sort by distance from spot
        width_candidates.sort(key=lambda c: c.distance_from_spot)
        
        # Only show candidates within a reasonable range of the "best" one
        # or that are closer to ATM.
        best_dist = best.distance_from_spot if best else 999
        
        for c in width_candidates:
            is_valid = passes_filter(c)
            is_selected = best and c.center_strike == best.center_strike
            
            # Show if it's valid, OR if it's closer to ATM than the selected one
            # (up to 5 strikes closer)
            should_show = is_valid or (c.distance_from_spot < best_dist and c.distance_from_spot >= best_dist - 25)
            
            if not should_show:
                continue

            marker = ""
            if is_selected:
                marker = " <-- SELECTED"
            elif not is_valid:
                if c.reward_risk < settings.rr_min:
                    marker = f" [REJECTED: RR {c.reward_risk:.1f} < {settings.rr_min}]"
                elif c.cost < 0.05:
                    marker = " [REJECTED: cost too low]"
                else:
                    marker = " [REJECTED: cost too high]"

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
