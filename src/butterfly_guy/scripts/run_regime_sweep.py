"""Regime-aware parameter sweep using historical SPX + VIX 1-minute CSV data.

Runs the full parameter grid against three known market regimes and prints:
  1. Top combos per regime (sorted by profit factor)
  2. Cross-regime consensus: combos that rank in the top N across ALL regimes

Usage:
    uv run python src/butterfly_guy/scripts/run_regime_sweep.py
    uv run python src/butterfly_guy/scripts/run_regime_sweep.py --top 20
    uv run python src/butterfly_guy/scripts/run_regime_sweep.py --consensus 15
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
log = get_logger("run_regime_sweep")

SPX_PATH = Path("data/spx_1min.csv")
VIX_PATH = Path("data/vix_1min.csv")

REGIMES = [
    {
        "name": "Bullish",
        "label": "BULL  (Post-Election Momentum)",
        "start": dt.date(2024, 11, 1),
        "end": dt.date(2024, 12, 1),
    },
    {
        "name": "Bearish",
        "label": "BEAR  (Tariff/Trade Policy Fears)",
        "start": dt.date(2025, 2, 18),
        "end": dt.date(2025, 3, 20),
    },
    {
        "name": "Choppy",
        "label": "CHOP  (Technical Resistance at 6,469)",
        "start": dt.date(2025, 8, 15),
        "end": dt.date(2025, 9, 15),
    },
]

# Parameter grid (same as run_csv_sweep.py)
DIRECTIONS = [None, "CALL", "PUT"]
USE_BIAS_FILTERS = [False, True]
WING_WIDTHS = [10]
RR_MINS = [8.0, 10.0]
MORNING_DDS = [0.60]
LM_DDS = [0.30]
AFT_DDS = [0.20]
VIX_MAXES = [None, 20.0, 22.0, 25.0]

GRID = [
    (direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max)
    for direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max in itertools.product(
        DIRECTIONS, USE_BIAS_FILTERS, WING_WIDTHS, RR_MINS, MORNING_DDS, LM_DDS, AFT_DDS, VIX_MAXES,
    )
    if direction is None or not use_bias  # bias filter only meaningful for auto direction
]


def combo_key(params: SimulationParams) -> tuple:
    return (
        params.direction_override or "auto",
        "bias" if params.use_bias_filter else "gap_dir",
        params.wing_width,
        params.rr_min,
        params.morning_drawdown,
        params.late_morning_drawdown,
        params.afternoon_drawdown,
        params.vix_max,
    )


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

    return {
        "key": combo_key(params),
        "direction": params.direction_override or "auto",
        "filter": "bias" if params.use_bias_filter else "gap_dir",
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
    }


def print_regime_table(regime_label: str, rows: list[dict], top_n: int) -> None:
    rows = rows[:top_n]
    width = 140
    print(f"\n{'=' * width}")
    print(f"  {regime_label}  —  TOP {len(rows)} (sorted by profit factor)")
    print(f"{'=' * width}")
    hdr = (
        f"{'Dir':>5}  {'Filt':>7}  {'Wing':>4}  {'RR':>4}  {'VIXmax':>6}  "
        f"{'MDD':>4}  {'LDD':>4}  {'ADD':>4}  "
        f"{'N':>4}  {'W%':>5}  {'PnL':>9}  "
        f"{'AvgW':>7}  {'AvgL':>7}  {'PF':>5}  {'Sharpe':>6}  {'Streak':>6}"
    )
    print(hdr)
    print("-" * width)
    for r in rows:
        vix_str = f"{r['vix_max']:>6}" if r['vix_max'] != "-" else f"{'  -':>6}"
        print(
            f"{r['direction']:>5}  {r['filter']:>7}  {r['wing']:>4}  "
            f"{r['rr_min']:>4.1f}  {vix_str}  "
            f"{r['morn_dd']:>4.2f}  {r['lm_dd']:>4.2f}  {r['aft_dd']:>4.2f}  "
            f"{r['trades']:>4}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+9.4f}  "
            f"{r['avg_win']:>+7.4f}  {r['avg_loss']:>7.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}  {r['max_streak']:>6}"
        )


def print_consensus_table(
    regime_results: list[tuple[str, list[dict]]],
    top_per_regime: int,
    min_regimes: int,
) -> None:
    """Show combos that appear in the top N of at least min_regimes regimes."""
    # Map key → {regime_name: rank}
    key_to_ranks: dict[tuple, dict[str, int]] = {}
    for regime_name, rows in regime_results:
        for rank, row in enumerate(rows[:top_per_regime], start=1):
            key = row["key"]
            if key not in key_to_ranks:
                key_to_ranks[key] = {}
            key_to_ranks[key][regime_name] = rank

    # Only keep combos appearing in enough regimes
    consensus_keys = {
        k: ranks for k, ranks in key_to_ranks.items() if len(ranks) >= min_regimes
    }
    if not consensus_keys:
        print(f"\n  (no combo ranked in top {top_per_regime} across {min_regimes}+ regimes)")
        return

    # Build rows with avg rank as sort key
    consensus_rows = []
    for key, ranks in consensus_keys.items():
        avg_rank = sum(ranks.values()) / len(ranks)
        regime_cols = {r_name: ranks.get(r_name, "-") for r_name, _ in regime_results}
        # Pull display fields from first regime's row data
        row_data = None
        for _, rows in regime_results:
            for row in rows:
                if row["key"] == key:
                    row_data = row
                    break
            if row_data:
                break
        consensus_rows.append((avg_rank, regime_cols, row_data))

    consensus_rows.sort(key=lambda x: x[0])

    regime_names = [r_name for r_name, _ in regime_results]
    width = 130
    print(f"\n{'=' * width}")
    print(f"  CROSS-REGIME CONSENSUS  (ranked in top {top_per_regime} across {min_regimes}+ regimes, sorted by avg rank)")
    print(f"{'=' * width}")
    rank_cols = "  ".join(f"{n[:4]:>4}" for n in regime_names)
    hdr = (
        f"{'AvgRk':>5}  {rank_cols}  "
        f"{'Dir':>5}  {'Filt':>7}  {'Wing':>4}  {'RR':>4}  {'VIXmax':>6}  "
        f"{'MDD':>4}  {'LDD':>4}  {'ADD':>4}"
    )
    print(hdr)
    print("-" * width)
    for avg_rank, regime_cols, row in consensus_rows:
        rank_str = "  ".join(
            f"{regime_cols.get(n, '-'):>4}" for n in regime_names
        )
        vix_str = f"{row['vix_max']:>6}" if row['vix_max'] != "-" else f"{'  -':>6}"
        print(
            f"{avg_rank:>5.1f}  {rank_str}  "
            f"{row['direction']:>5}  {row['filter']:>7}  {row['wing']:>4}  "
            f"{row['rr_min']:>4.1f}  {vix_str}  "
            f"{row['morn_dd']:>4.2f}  {row['lm_dd']:>4.2f}  {row['aft_dd']:>4.2f}"
        )


def parse_args() -> tuple[int, int, int, str]:
    top_n = 15
    consensus_n = 20
    min_regimes = len(REGIMES)
    asset = "SPX"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--top" and i + 1 < len(args):
            try:
                top_n = int(args[i + 1])
            except ValueError:
                pass
        if a == "--consensus" and i + 1 < len(args):
            try:
                consensus_n = int(args[i + 1])
            except ValueError:
                pass
        if a == "--min-regimes" and i + 1 < len(args):
            try:
                min_regimes = int(args[i + 1])
            except ValueError:
                pass
        if a == "--asset" and i + 1 < len(args):
            asset = args[i + 1].upper()
    return top_n, consensus_n, min_regimes, asset


def main() -> None:
    top_n, consensus_n, min_regimes, asset = parse_args()
    spx_path = Path(f"data/{asset.lower()}_1min.csv")

    if not spx_path.exists() or not VIX_PATH.exists():
        print(f"Missing CSV files: {spx_path}, {VIX_PATH}")
        sys.exit(1)

    print(f"\nLoading CSV data for {asset} (this takes a few seconds)...")
    loader = CsvDataLoader(spx_path, VIX_PATH)
    engine = SimulationEngine()

    all_regime_results: list[tuple[str, list[dict]]] = []

    for regime in REGIMES:
        start, end = regime["start"], regime["end"]
        all_dates = loader.available_dates()
        dates = [d for d in all_dates if start <= d <= end]

        day_data: list[DayData] = []
        for date in dates:
            day = loader.load_day(date)
            if day:
                day_data.append(day)

        n_days = len(day_data)
        print(f"  {regime['name']:8s}: {n_days} days ({start} → {end})")

        rows = []
        for direction, use_bias, wing, rr, morn_dd, lm_dd, aft_dd, vix_max in GRID:
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

        rows.sort(key=lambda r: r["profit_factor"], reverse=True)
        all_regime_results.append((regime["name"], rows))

        print_regime_table(regime["label"], rows, top_n)

        # Save per-regime CSV
        Path("data/results").mkdir(exist_ok=True)
        out = Path(f"data/results/regime_sweep_{regime['name'].lower()}.csv")
        with open(out, "w", newline="") as f:
            save_rows = [{k: v for k, v in r.items() if k != "key"} for r in rows]
            writer = csv_mod.DictWriter(f, fieldnames=save_rows[0].keys())
            writer.writeheader()
            writer.writerows(save_rows)
        print(f"\n  Saved {out} ({len(rows)} rows)")

    print_consensus_table(all_regime_results, top_per_regime=consensus_n, min_regimes=min_regimes)
    print()


if __name__ == "__main__":
    main()
