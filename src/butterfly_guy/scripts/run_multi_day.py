"""Multi-day backtest runner with summary table.

Runs the simulation across a date range using Schwab 1-min data
(up to ~48 days history) and prints a per-day table + aggregate stats.

Usage:
    # Last 45 days, auto direction (default)
    uv run python src/butterfly_guy/scripts/run_multi_day.py

    # Custom date range
    uv run python src/butterfly_guy/scripts/run_multi_day.py 2026-01-20 2026-03-07

    # Force direction (CALL-only or PUT-only)
    uv run python src/butterfly_guy/scripts/run_multi_day.py --direction CALL
    uv run python src/butterfly_guy/scripts/run_multi_day.py 2026-01-20 2026-03-07 --direction PUT
"""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import dotenv_values

from butterfly_guy.backtest.schwab_loader import SchwabDataLoader
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging

setup_logging(log_level="WARNING", json_output=False)  # quiet — just show the table
log = get_logger("run_multi_day")


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    dates = []
    d = start
    while d <= end:
        if d.weekday() < 5:  # weekdays only
            dates.append(d)
        d += dt.timedelta(days=1)
    return dates


async def main() -> None:
    args = sys.argv[1:]

    # Parse --direction flag
    direction_override = None
    if "--direction" in args:
        idx = args.index("--direction")
        direction_override = args[idx + 1].upper()
        args = [a for i, a in enumerate(args) if i != idx and i != idx + 1]

    today = dt.date.today()
    if len(args) >= 2:
        start = dt.date.fromisoformat(args[0])
        end = dt.date.fromisoformat(args[1])
    elif len(args) == 1:
        start = dt.date.fromisoformat(args[0])
        end = today - dt.timedelta(days=1)
    else:
        # Default: last 45 days (within Schwab's ~48-day window)
        start = today - dt.timedelta(days=45)
        end = today - dt.timedelta(days=1)

    env = dotenv_values(".env")
    loader = SchwabDataLoader(
        token_path=env.get("SCHWAB_TOKEN_PATH", "tokens.json"),
        api_key=env.get("SCHWAB_API_KEY", ""),
        secret_key=env.get("SCHWAB_SECRET_KEY", ""),
    )

    params = SimulationParams(
        wing_width=10,
        rr_min=6.0,
        morning_drawdown=0.50,
        late_morning_drawdown=0.40,
        afternoon_drawdown=0.30,
        slippage=0.05,
        direction_override=direction_override,
    )

    engine = SimulationEngine()
    dates = date_range(start, end)

    direction_label = f"  direction_override={direction_override}" if direction_override else ""
    print(f"\nRunning {len(dates)} trading days: {start} → {end}")
    print(f"Params: wing={params.wing_width}  rr_min={params.rr_min}  "
          f"morning_dd={params.morning_drawdown}  "
          f"late_morning_dd={params.late_morning_drawdown}  "
          f"afternoon_dd={params.afternoon_drawdown}{direction_label}\n")

    header = (f"{'Date':>12}  {'Dir':>4}  {'Center':>7}  {'Entry':>6}  "
              f"{'Exit':>6}  {'Peak':>6}  {'PnL':>7}  {'Reason':<20}")
    print(header)
    print("-" * len(header))

    results = []
    for date in dates:
        try:
            day = await loader.load_day(date)
        except Exception as e:
            print(f"{str(date):>12}  -- no data ({e})")
            continue

        if not day:
            print(f"{str(date):>12}  -- no data")
            continue

        result = engine.simulate_day(day, params)

        if not result.traded:
            print(f"{str(date):>12}  -- no entry")
            continue

        results.append(result)
        pnl_str = f"{result.pnl:+.4f}"
        print(f"{str(result.date):>12}  {result.direction:>4}  "
              f"{result.center_strike:>7.0f}  {result.entry_price:>6.4f}  "
              f"{result.exit_price:>6.4f}  {result.peak_value:>6.4f}  "
              f"{pnl_str:>7}  {result.exit_reason:<20}")

    await loader.close()

    if not results:
        print("\nNo trades.")
        return

    # Summary stats
    pnls = [r.pnl for r in results]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100

    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max consecutive losses
    max_streak = streak = 0
    for p in pnls:
        streak = streak + 1 if p < 0 else 0
        max_streak = max(max_streak, streak)

    # Max drawdown on cumulative equity
    equity = peak = max_dd = 0.0
    for p in pnls:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    # Exit reason breakdown
    from collections import Counter
    reasons = Counter(r.exit_reason for r in results)

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY  ({len(results)} trades, {len(dates)} days)")
    print(f"{'=' * 60}")
    print(f"  Total PnL:        {total:+.4f}")
    print(f"  Win rate:         {win_rate:.1f}%  ({len(wins)}W / {len(losses)}L)")
    print(f"  Avg win:          {sum(wins)/len(wins):+.4f}" if wins else "  Avg win:         --")
    print(f"  Avg loss:         {sum(losses)/len(losses):+.4f}" if losses else "  Avg loss:         --")
    print(f"  Profit factor:    {profit_factor:.2f}")
    print(f"  Max consec loss:  {max_streak}")
    print(f"  Max drawdown:     {max_dd:.4f}")
    print(f"\n  Exit breakdown:")
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"    {reason:<22} {count:>3}  ({count/len(results)*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())
