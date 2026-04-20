"""Parameter sweep using historical SPX + VIX 1-minute CSV data (2000–2025).

Loads SPX/VIX CSVs once into memory, then runs every parameter combination.
Outputs a table sorted by profit factor and saves full results to CSV.

Usage:
    uv run python src/butterfly_guy/scripts/run_csv_sweep.py
    uv run python src/butterfly_guy/scripts/run_csv_sweep.py 2008-01-01 2021-12-31
    uv run python src/butterfly_guy/scripts/run_csv_sweep.py 2020-01-01 2025-12-10 --top 50
"""

from __future__ import annotations

import csv as csv_mod
import datetime as dt
import itertools
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.backtest.data_loader import DayData
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_csv_sweep")

SPX_PATH = Path("data/spx_1min.csv")
VIX_PATH = Path("data/vix_1min.csv")


def parse_args() -> tuple[dt.date | None, dt.date | None, int, str]:
    date_args = [a for a in sys.argv[1:] if a.startswith("20")]
    top_n = 30
    asset = "SPX"
    for i, a in enumerate(sys.argv[1:]):
        if a == "--top" and i + 2 <= len(sys.argv) - 1:
            try:
                top_n = int(sys.argv[i + 2])
            except ValueError:
                pass
        elif a == "--asset" and i + 1 < len(sys.argv):
            asset = sys.argv[i + 1].upper()
    start = dt.date.fromisoformat(date_args[0]) if len(date_args) >= 1 else None
    end = dt.date.fromisoformat(date_args[1]) if len(date_args) >= 2 else None
    return start, end, top_n, asset


def summarize(params: SimulationParams, results: list) -> dict | None:
    traded = [r for r in results if r.traded]
    if not traded:
        return None

    pnls = [r.pnl for r in traded]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = round(gross_profit / gross_loss, 3) if gross_loss > 0 else 999.0

    if len(pnls) >= 2:
        mean = statistics.mean(pnls)
        stdev = statistics.stdev(pnls)
        sharpe = round(mean / stdev * (252 ** 0.5), 3) if stdev > 0 else 0.0
    else:
        sharpe = 0.0

    max_streak = streak = 0
    for p in pnls:
        streak = streak + 1 if p < 0 else 0
        max_streak = max(max_streak, streak)

    reasons = Counter(r.exit_reason for r in traded)
    direction_str = params.direction_override or "auto"
    filter_str = "bias" if params.use_bias_filter else "gap_dir"

    return {
        "direction": direction_str,
        "filter": filter_str,
        "wing": params.wing_width,
        "rr_min": params.rr_min,
        "vix_max": params.vix_max if params.vix_max is not None else "-",
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
        "eod_exits": reasons.get("end_of_day", 0),
        "dd_exits": sum(v for k, v in reasons.items() if k.startswith("drawdown")),
        "expired": reasons.get("expired", 0),
    }


def print_table(rows: list[dict], top_n: int) -> None:
    rows = rows[:top_n]
    width = 135
    print(f"\n{'=' * width}")
    print(f"  TOP {len(rows)} PARAMETER COMBINATIONS (sorted by profit factor)")
    print(f"{'=' * width}")
    hdr = (
        f"{'Dir':>5}  {'Filt':>5}  {'Wing':>4}  {'RR':>4}  {'VIXmax':>6}  "
        f"{'MDD':>4}  {'LDD':>4}  {'ADD':>4}  "
        f"{'N':>4}  {'W%':>5}  {'PnL':>9}  "
        f"{'AvgW':>7}  {'AvgL':>7}  {'PF':>5}  {'Sharpe':>6}  {'Streak':>6}"
    )
    print(hdr)
    print("-" * width)
    for r in rows:
        vix_str = f"{r['vix_max']:>6}" if r['vix_max'] != "-" else f"{'  -':>6}"
        print(
            f"{r['direction']:>5}  {r['filter']:>5}  {r['wing']:>4}  "
            f"{r['rr_min']:>4.1f}  {vix_str}  "
            f"{r['morn_dd']:>4.2f}  {r['lm_dd']:>4.2f}  {r['aft_dd']:>4.2f}  "
            f"{r['trades']:>4}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+9.4f}  "
            f"{r['avg_win']:>+7.4f}  {r['avg_loss']:>7.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}  {r['max_streak']:>6}"
        )


def main() -> None:
    start_arg, end_arg, top_n, asset = parse_args()
    spx_path = Path(f"data/{asset.lower()}_1min.csv")

    if not spx_path.exists() or not VIX_PATH.exists():
        print(f"Missing CSV files: {spx_path}, {VIX_PATH}")
        sys.exit(1)

    print(f"\nLoading CSV data for {asset} (this takes a few seconds)...")
    loader = CsvDataLoader(spx_path, VIX_PATH)
    all_dates = loader.available_dates()

    # Filter to requested date range
    start = start_arg or all_dates[0]
    end = end_arg or all_dates[-1]
    dates = [d for d in all_dates if start <= d <= end]

    print(f"Loading {len(dates)} days ({start} → {end})...")
    day_data: list[DayData] = []
    for date in dates:
        day = loader.load_day(date)
        if day:
            day_data.append(day)

    print(f"{len(day_data)} days loaded. Running parameter sweep...\n")

    # Parameter grid
    directions = [None, "CALL", "PUT"]
    use_bias_filters = [False, True]
    wing_widths = [10, 20, 30]
    rr_mins = [8.0, 10.0]
    morning_dds = [0.40, 0.50, 0.60]
    lm_dds = [0.30, 0.40]
    aft_dds = [0.20, 0.30]
    vix_maxes = [None, 20.0, 22.0, 25.0]

    grid = [
        (direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max)
        for direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max in itertools.product(
            directions, use_bias_filters, wing_widths, rr_mins,
            morning_dds, lm_dds, aft_dds, vix_maxes,
        )
        if direction is None or not use_bias  # bias filter only meaningful for auto direction
    ]
    print(f"Testing {len(grid)} parameter combinations...\n")

    engine = SimulationEngine()
    rows = []

    for i, (direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max) in enumerate(grid):
        params = SimulationParams(
            wing_width=wing,
            rr_min=rr,
            morning_drawdown=morn_dd,
            late_morning_drawdown=lm_dd,
            afternoon_drawdown=aft_dd,
            slippage=0.05,
            direction_override=direction,
            use_bias_filter=use_bias,
            vix_max=vix_max,
        )
        results = [engine.simulate_day(day, params) for day in day_data]
        row = summarize(params, results)
        if row:
            rows.append(row)

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(grid)} combos done...")

    if not rows:
        print("No results.")
        return

    rows.sort(key=lambda r: r["profit_factor"], reverse=True)
    print_table(rows, top_n)

    print(f"\n--- WORST 5 ---")
    for r in rows[-5:]:
        vix_str = f"{r['vix_max']:>6}" if r['vix_max'] != "-" else f"{'  -':>6}"
        print(
            f"{r['direction']:>5}  {r['filter']:>5}  {r['wing']:>4}  "
            f"{r['rr_min']:>4.1f}  {vix_str}  "
            f"{r['morn_dd']:>4.2f}  {r['lm_dd']:>4.2f}  {r['aft_dd']:>4.2f}  "
            f"{r['trades']:>4}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+9.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}"
        )

    Path("results").mkdir(exist_ok=True)
    out = Path("results/csv_sweep_results.csv")
    with open(out, "w", newline="") as f:
        writer = csv_mod.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nFull results saved to {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
