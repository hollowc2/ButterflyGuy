"""Parameter sweep using Schwab 1-minute SPY data.

Loads all days from Schwab once, then runs every parameter combination
in memory. Outputs a table sorted by profit factor.

Sweeps:
  - direction_override: auto (gap signal), CALL-only, PUT-only
  - entry_start: 10:00, 10:05, 10:10, 10:15 ET
  - wing_width: 5, 10, 15, 20
  - rr_min: 6.0, 8.0, 10.0
  - morning_drawdown: 0.40, 0.50, 0.60
  - late_morning_drawdown: 0.30, 0.40
  - afternoon_drawdown: 0.20, 0.30

Usage:
    uv run python src/butterfly_guy/scripts/run_schwab_sweep.py
    uv run python src/butterfly_guy/scripts/run_schwab_sweep.py 2026-01-26 2026-03-10
"""

from __future__ import annotations

import asyncio
import datetime as dt
import itertools
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import dotenv_values

from butterfly_guy.backtest.data_loader import DayData
from butterfly_guy.backtest.schwab_loader import SchwabDataLoader
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_schwab_sweep")

EASTERN_OFFSET = dt.timezone(dt.timedelta(hours=-5))  # ET (approximate, for time parsing)


def parse_time(s: str) -> dt.time:
    h, m = s.split(":")
    return dt.time(int(h), int(m))


def date_range(start: dt.date, end: dt.date) -> list[dt.date]:
    dates, d = [], start
    while d <= end:
        if d.weekday() < 5:
            dates.append(d)
        d += dt.timedelta(days=1)
    return dates


def summarize(params: SimulationParams, results: list) -> dict:
    traded = [r for r in results if r.traded]
    if not traded:
        return None

    pnls = [r.pnl for r in traded]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = round(gross_profit / gross_loss, 3) if gross_loss > 0 else 999.0

    # Sharpe on trade PnLs
    if len(pnls) >= 2:
        import statistics
        mean = statistics.mean(pnls)
        stdev = statistics.stdev(pnls)
        sharpe = round(mean / stdev * (252 ** 0.5), 3) if stdev > 0 else 0.0
    else:
        sharpe = 0.0

    # Max consecutive losses
    max_streak = streak = 0
    for p in pnls:
        streak = streak + 1 if p < 0 else 0
        max_streak = max(max_streak, streak)

    reasons = Counter(r.exit_reason for r in traded)
    morning_dd_exits = reasons.get("drawdown_morning", 0)
    eod_exits = reasons.get("end_of_day", 0)

    direction_str = params.direction_override or "auto"
    entry_str = params.entry_start.strftime("%H:%M")

    return {
        "direction": direction_str,
        "entry_start": entry_str,
        "wing": params.wing_width,
        "rr_min": params.rr_min,
        "morn_dd": params.morning_drawdown,
        "lm_dd": params.late_morning_drawdown,
        "aft_dd": params.afternoon_drawdown,
        "trades": len(traded),
        "wins": len(wins),
        "win_pct": round(len(wins) / len(traded) * 100, 1),
        "total_pnl": round(sum(pnls), 4),
        "avg_win": round(gross_profit / len(wins), 4) if wins else 0.0,
        "avg_loss": round(-gross_loss / len(losses), 4) if losses else 0.0,
        "profit_factor": profit_factor,
        "sharpe": sharpe,
        "max_streak": max_streak,
        "eod_exits": eod_exits,
        "morning_dd_exits": morning_dd_exits,
    }


async def main() -> None:
    args = [a for a in sys.argv[1:] if a.startswith("20")]
    today = dt.date.today()

    if len(args) >= 2:
        start = dt.date.fromisoformat(args[0])
        end = dt.date.fromisoformat(args[1])
    elif len(args) == 1:
        start = dt.date.fromisoformat(args[0])
        end = today - dt.timedelta(days=1)
    else:
        start = today - dt.timedelta(days=45)
        end = today - dt.timedelta(days=1)

    env = dotenv_values(".env")
    loader = SchwabDataLoader(
        token_path=env.get("SCHWAB_TOKEN_PATH", "tokens.json"),
        api_key=env.get("SCHWAB_API_KEY", ""),
        secret_key=env.get("SCHWAB_SECRET_KEY", ""),
    )

    dates = date_range(start, end)
    print(f"\nLoading {len(dates)} days from Schwab ({start} → {end})...")

    day_data: list[DayData] = []
    for date in dates:
        try:
            day = await loader.load_day(date)
            if day:
                day_data.append(day)
                print(f"  loaded {date} ({len(day.bars)} bars)")
            else:
                print(f"  skipped {date} — no data")
        except Exception as e:
            print(f"  skipped {date} — {e}")

    await loader.close()
    print(f"\n{len(day_data)} days loaded. Running parameter sweep...\n")

    # Parameter grid
    directions = [None, "CALL", "PUT"]
    entry_starts = [
        parse_time("10:00"),
        parse_time("10:05"),
        parse_time("10:10"),
        parse_time("10:15"),
    ]
    entry_end = parse_time("10:30")
    wing_widths = [5, 10, 15, 20]
    rr_mins = [6.0, 8.0, 10.0]
    morning_dds = [0.40, 0.50, 0.60]
    lm_dds = [0.30, 0.40]
    aft_dds = [0.20, 0.30]

    grid = list(itertools.product(directions, entry_starts, wing_widths,
                                  rr_mins, morning_dds, lm_dds, aft_dds))
    total_combos = len(grid)
    print(f"Testing {total_combos} parameter combinations...\n")

    engine = SimulationEngine()
    rows = []

    for i, (direction, entry_start_t, wing, rr, morn_dd, lm_dd, aft_dd) in enumerate(grid):
        params = SimulationParams(
            wing_width=wing,
            rr_min=rr,
            entry_start=entry_start_t,
            entry_end=entry_end,
            morning_drawdown=morn_dd,
            late_morning_drawdown=lm_dd,
            afternoon_drawdown=aft_dd,
            slippage=0.05,
            direction_override=direction,
        )
        results = [engine.simulate_day(day, params) for day in day_data]
        row = summarize(params, results)
        if row:
            rows.append(row)

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{total_combos} combos done...")

    if not rows:
        print("No results.")
        return

    # Sort by profit factor descending
    rows.sort(key=lambda r: r["profit_factor"], reverse=True)

    # Print top 30
    top_n = min(30, len(rows))
    print(f"\n{'=' * 110}")
    print(f"  TOP {top_n} PARAMETER COMBINATIONS (sorted by profit factor)")
    print(f"{'=' * 110}")
    hdr = (f"{'Dir':>5}  {'Start':>5}  {'Wing':>4}  {'RR':>4}  "
           f"{'MDD':>4}  {'LDD':>4}  {'ADD':>4}  "
           f"{'N':>3}  {'W%':>5}  {'PnL':>8}  "
           f"{'AvgW':>7}  {'AvgL':>7}  {'PF':>5}  {'Sharpe':>6}  {'Streak':>6}")
    print(hdr)
    print("-" * 110)

    for r in rows[:top_n]:
        print(
            f"{r['direction']:>5}  {r['entry_start']:>5}  {r['wing']:>4}  "
            f"{r['rr_min']:>4.1f}  "
            f"{r['morn_dd']:>4.2f}  {r['lm_dd']:>4.2f}  {r['aft_dd']:>4.2f}  "
            f"{r['trades']:>3}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+8.4f}  "
            f"{r['avg_win']:>+7.4f}  {r['avg_loss']:>7.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}  {r['max_streak']:>6}"
        )

    # Also show worst for contrast
    print(f"\n--- WORST 5 ---")
    for r in rows[-5:]:
        print(
            f"{r['direction']:>5}  {r['entry_start']:>5}  {r['wing']:>4}  "
            f"{r['rr_min']:>4.1f}  "
            f"{r['morn_dd']:>4.2f}  {r['lm_dd']:>4.2f}  {r['aft_dd']:>4.2f}  "
            f"{r['trades']:>3}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+8.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}"
        )

    # Save full results to CSV
    import csv
    out = Path("schwab_sweep_results.csv")
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nFull results saved to {out} ({len(rows)} rows)")


if __name__ == "__main__":
    asyncio.run(main())
