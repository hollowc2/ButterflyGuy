"""Multi-day backtest runner — single strategy iteration over a date range.

Runs one parameter set across a date range and prints a per-day table plus
aggregate stats.  All strategy knobs are exposed as CLI flags.

Data sources
------------
  --source schwab   (default) Schwab 1-min data; cache-first from data/schwab/
  --source csv      Historical SPX + VIX 1-min CSVs (2000–2025)

Usage examples
--------------
    # Last 45 days, all defaults
    uv run python src/butterfly_guy/scripts/run_multi_day.py

    # Custom date range
    uv run python src/butterfly_guy/scripts/run_multi_day.py 2026-01-20 2026-03-07

    # CSV data source, specific range
    uv run python src/butterfly_guy/scripts/run_multi_day.py 2020-01-01 2020-12-31 --source csv

    # Force direction + bias filter
    uv run python src/butterfly_guy/scripts/run_multi_day.py --direction CALL --bias-filter

    # Tune drawdown thresholds and VIX gate
    uv run python src/butterfly_guy/scripts/run_multi_day.py --morning-dd 0.60 --vix-max 22

    # Full example
    uv run python src/butterfly_guy/scripts/run_multi_day.py 2025-01-01 2025-12-31 \\
        --source csv --direction auto --bias-filter \\
        --wing 10 --rr-min 8.0 \\
        --morning-dd 0.50 --late-morning-dd 0.40 --afternoon-dd 0.30 \\
        --slippage 0.05 --vix-max 25 --no-cache
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_multi_day")

CACHE_DIR = Path("data/schwab")
SPX_PATH = Path("data/spx_1min.csv")
VIX_PATH = Path("data/vix_1min.csv")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Single-strategy multi-day backtest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Date range (positional, optional)
    p.add_argument("start", nargs="?", type=dt.date.fromisoformat,
                   help="Start date YYYY-MM-DD (default: 45 days ago)")
    p.add_argument("end", nargs="?", type=dt.date.fromisoformat,
                   help="End date YYYY-MM-DD (default: yesterday)")

    # Data source
    p.add_argument("--source", choices=["schwab", "csv"], default="schwab",
                   help="Data source")
    p.add_argument("--no-cache", action="store_true",
                   help="(Schwab) skip cache, fetch live")
    p.add_argument("--spx-csv", type=Path, default=SPX_PATH,
                   help="(CSV) SPX 1-min CSV path")
    p.add_argument("--vix-csv", type=Path, default=VIX_PATH,
                   help="(CSV) VIX 1-min CSV path")

    # Direction
    dir_grp = p.add_mutually_exclusive_group()
    dir_grp.add_argument("--direction", choices=["CALL", "PUT", "auto"], default="auto",
                         help="Force direction or let the filter decide (auto)")
    dir_grp.add_argument("--bias-filter", action="store_true",
                         help="Use multi-signal bias score instead of gap-only direction")

    # Strategy knobs
    p.add_argument("--wing", type=int, default=10, dest="wing_width",
                   help="Wing width in strikes")
    p.add_argument("--rr-min", type=float, default=8.0,
                   help="Minimum reward/risk ratio for entry")
    p.add_argument("--morning-dd", type=float, default=0.50, dest="morning_drawdown",
                   help="Max drawdown from peak before exit (morning regime, <2h after open)")
    p.add_argument("--late-morning-dd", type=float, default=0.40, dest="late_morning_drawdown",
                   help="Max drawdown from peak (late-morning regime, 2–4h after open)")
    p.add_argument("--afternoon-dd", type=float, default=0.30, dest="afternoon_drawdown",
                   help="Max drawdown from peak (afternoon regime, >4h after open)")
    p.add_argument("--slippage", type=float, default=0.05,
                   help="Per-spread slippage applied to both entry and exit")
    p.add_argument("--vix-max", type=float, default=None,
                   help="Skip days where VIX exceeds this threshold at entry time")
    p.add_argument("--hold-to-expiry", action="store_true",
                   help="Disable all drawdown exits; let butterfly expire at EOD or worthless")

    return p.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    dates, d = [], start
    while d <= end:
        if d.weekday() < 5:
            dates.append(d)
        d += dt.timedelta(days=1)
    return dates


def build_params(args: argparse.Namespace) -> SimulationParams:
    direction_override = None
    use_bias_filter = False

    if args.bias_filter:
        use_bias_filter = True
    elif args.direction != "auto":
        direction_override = args.direction

    return SimulationParams(
        wing_width=args.wing_width,
        rr_min=args.rr_min,
        morning_drawdown=args.morning_drawdown,
        late_morning_drawdown=args.late_morning_drawdown,
        afternoon_drawdown=args.afternoon_drawdown,
        slippage=args.slippage,
        direction_override=direction_override,
        use_bias_filter=use_bias_filter,
        vix_max=args.vix_max,
        hold_to_expiry=args.hold_to_expiry,
    )


def print_params(params: SimulationParams, source: str, dates: list[dt.date]) -> None:
    dir_str = (
        "bias_filter" if params.use_bias_filter
        else params.direction_override or "auto(gap)"
    )
    vix_str = f"  vix_max={params.vix_max}" if params.vix_max is not None else ""
    hold_str = "  hold_to_expiry=True" if params.hold_to_expiry else ""
    print(f"\nRunning {len(dates)} trading days: {dates[0]} → {dates[-1]}  [source={source}]")
    print(
        f"Params: wing={params.wing_width}  rr_min={params.rr_min}"
        f"  dir={dir_str}"
        f"  morning_dd={params.morning_drawdown}"
        f"  late_morning_dd={params.late_morning_drawdown}"
        f"  afternoon_dd={params.afternoon_drawdown}"
        f"  slippage={params.slippage}{vix_str}{hold_str}\n"
    )


def print_summary(results: list, n_days: int) -> None:
    pnls = [r.pnl for r in results]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100

    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    import statistics as _stats
    sharpe = 0.0
    if len(pnls) >= 2:
        mean = _stats.mean(pnls)
        stdev = _stats.stdev(pnls)
        sharpe = mean / stdev * (252 ** 0.5) if stdev > 0 else 0.0

    max_streak = streak = 0
    for p in pnls:
        streak = streak + 1 if p < 0 else 0
        max_streak = max(max_streak, streak)

    equity = peak = max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    reasons = Counter(r.exit_reason for r in results)

    print(f"\n{'=' * 64}")
    print(f"  SUMMARY  ({len(results)} trades across {n_days} days)")
    print(f"{'=' * 64}")
    print(f"  Total PnL:        {total:+.4f}")
    print(f"  Win rate:         {win_rate:.1f}%  ({len(wins)}W / {len(losses)}L)")
    print(f"  Avg win:          {sum(wins)/len(wins):+.4f}" if wins else "  Avg win:         --")
    print(f"  Avg loss:         {sum(losses)/len(losses):+.4f}" if losses else "  Avg loss:         --")
    print(f"  Profit factor:    {profit_factor:.2f}")
    print(f"  Sharpe (annlzd):  {sharpe:.3f}")
    print(f"  Max consec loss:  {max_streak}")
    print(f"  Max drawdown:     {max_dd:.4f}")
    print(f"\n  Exit breakdown:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason:<24} {count:>3}  ({count/len(results)*100:.0f}%)")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

async def load_schwab_days(
    dates: list[dt.date], no_cache: bool
) -> list:
    from butterfly_guy.backtest._cache_utils import day_cache_path, load_day, save_day
    from butterfly_guy.backtest.data_loader import DayData
    from dotenv import dotenv_values

    cache_hits = sum(1 for d in dates if day_cache_path(d, CACHE_DIR).exists() and not no_cache)
    cache_misses = len(dates) - cache_hits
    print(f"  cache hits: {cache_hits}  API fetches needed: {cache_misses}")

    loader = None
    if cache_misses > 0 or no_cache:
        from butterfly_guy.backtest.schwab_loader import SchwabDataLoader
        env = dotenv_values(".env")
        loader = SchwabDataLoader(
            token_path=env.get("SCHWAB_TOKEN_PATH", "tokens.json"),
            api_key=env.get("SCHWAB_API_KEY", ""),
            secret_key=env.get("SCHWAB_SECRET_KEY", ""),
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    day_data = []
    for date in dates:
        p = day_cache_path(date, CACHE_DIR)
        if p.exists() and not no_cache:
            try:
                day_data.append(load_day(p))
            except Exception as e:
                print(f"  {date}  cache read error: {e}")
        else:
            try:
                day = await loader.load_day(date)
                if day:
                    save_day(day, p)
                    day_data.append(day)
                else:
                    print(f"  {date}  no data from API")
            except Exception as e:
                print(f"  {date}  fetch error: {e}")

    if loader is not None:
        await loader.close()
    return day_data


def load_csv_days(
    dates: list[dt.date], spx_path: Path, vix_path: Path
) -> list:
    from butterfly_guy.backtest.csv_loader import CsvDataLoader

    if not spx_path.exists() or not vix_path.exists():
        print(f"Missing CSV files: {spx_path}, {vix_path}")
        sys.exit(1)

    print(f"  Loading CSVs... (takes a few seconds)")
    loader = CsvDataLoader(spx_path, vix_path)

    day_data = []
    for date in dates:
        day = loader.load_day(date)
        if day:
            day_data.append(day)
    return day_data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    args = parse_args()
    today = dt.date.today()

    if args.start and args.end:
        start, end = args.start, args.end
    elif args.start:
        start, end = args.start, today - dt.timedelta(days=1)
    else:
        start = today - dt.timedelta(days=45)
        end = today - dt.timedelta(days=1)

    dates = date_range(start, end)
    if not dates:
        print("No trading days in range.")
        return

    params = build_params(args)
    print_params(params, args.source, dates)

    # Load data
    if args.source == "schwab":
        day_data = await load_schwab_days(dates, args.no_cache)
    else:
        day_data = load_csv_days(dates, args.spx_csv, args.vix_csv)

    if not day_data:
        print("No data loaded.")
        return

    print(f"\n{len(day_data)} days loaded. Simulating...\n")

    # Run simulation
    engine = SimulationEngine()
    header = (
        f"{'Date':>12}  {'Dir':>4}  {'Center':>7}  {'Wing':>4}  "
        f"{'Entry':>6}  {'Exit':>6}  {'Peak':>6}  {'PnL':>7}  {'Reason':<22}"
    )
    print(header)
    print("-" * len(header))

    results = []
    skipped = 0
    for day in day_data:
        result = engine.simulate_day(day, params)

        if not result.traded:
            skipped += 1
            continue

        results.append(result)
        pnl_str = f"{result.pnl:+.4f}"
        print(
            f"{str(result.date):>12}  {result.direction:>4}  "
            f"{result.center_strike:>7.0f}  {result.wing_width:>4}  "
            f"{result.entry_price:>6.4f}  {result.exit_price:>6.4f}  "
            f"{result.peak_value:>6.4f}  {pnl_str:>7}  {result.exit_reason:<22}"
        )

    if skipped:
        print(f"\n  ({skipped} days skipped — no entry signal)")

    if not results:
        print("\nNo trades.")
        return

    print_summary(results, len(day_data))


if __name__ == "__main__":
    asyncio.run(main())
