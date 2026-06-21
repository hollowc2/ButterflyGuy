"""Sweep classifier thresholds to optimize regime-adaptive trading over 25 years.

Per-regime SimulationParams are fixed to the historical regime-sweep winners:
  BULL:    PUT  gap_dir  rr_min=10  vix_max=20.0  (TODO: revisit — CALL may be more intuitive)
  BEAR:    auto gap_dir  rr_min=8   vix_max=20.0
  CHOP:    auto gap_dir  rr_min=10  vix_max=None
  DEFAULT: auto gap_dir  rr_min=10  vix_max=20.0  (UNKNOWN fallback / cross-regime consensus)

Only classifier thresholds are swept (216 combos):
  lookback_days:      [3, 5, 10, 20]
  bear_return_thresh: [-0.01, -0.02, -0.03]
  bull_return_thresh: [+0.01, +0.02, +0.03]
  bear_vix_thresh:    [18.0, 20.0, 22.0]
  bull_vix_thresh:    [15.0, 18.0]

Output table: overall PF/Sharpe/trades + per-regime day count breakdown.
Baseline row (fixed DEFAULT_PARAMS, no dispatch) always shown first for comparison.

Usage:
    uv run python src/butterfly_guy/scripts/run_classifier_sweep.py
    uv run python src/butterfly_guy/scripts/run_classifier_sweep.py 2010-01-01 2025-12-10
    uv run python src/butterfly_guy/scripts/run_classifier_sweep.py 2020-01-01 2025-12-10 --top 30
"""

from __future__ import annotations

import argparse
import csv as csv_mod
import datetime as dt
import itertools
import sys
from pathlib import Path

from butterfly_guy.backtest.csv_loader import CsvDataLoader
from butterfly_guy.backtest.data_loader import DayData
from butterfly_guy.backtest.metrics import profit_factor, sharpe, win_pct
from butterfly_guy.backtest.simulation_engine import (
    SimulationEngine,
    SimulationParams,
)
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.strategy.regime_classifier import Regime, RegimeClassifier

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_classifier_sweep")

SPX_PATH = Path("data/spx_1min.csv")
VIX_PATH = Path("data/vix_1min.csv")

# Fixed per-regime params from the historical regime sweep.
# TODO: revisit BULL direction (PUT vs CALL) before deploying live
BULL_PARAMS = SimulationParams(
    wing_width=10, rr_min=10.0,
    morning_drawdown=0.60, late_morning_drawdown=0.30, afternoon_drawdown=0.20,
    slippage=0.05, direction_override="PUT", use_bias_filter=False, vix_max=20.0,
)
BEAR_PARAMS = SimulationParams(
    wing_width=10, rr_min=8.0,
    morning_drawdown=0.60, late_morning_drawdown=0.30, afternoon_drawdown=0.20,
    slippage=0.05, direction_override=None, use_bias_filter=False, vix_max=20.0,
)
CHOP_PARAMS = SimulationParams(
    wing_width=10, rr_min=10.0,
    morning_drawdown=0.60, late_morning_drawdown=0.30, afternoon_drawdown=0.20,
    slippage=0.05, direction_override=None, use_bias_filter=False, vix_max=None,
)
DEFAULT_PARAMS = SimulationParams(
    wing_width=10, rr_min=10.0,
    morning_drawdown=0.60, late_morning_drawdown=0.30, afternoon_drawdown=0.20,
    slippage=0.05, direction_override=None, use_bias_filter=False, vix_max=20.0,
)

# Classifier threshold grid
LOOKBACK_DAYS      = [3, 5, 10, 20]
BEAR_RETURN_THRESH = [-0.01, -0.02, -0.03]
BULL_RETURN_THRESH = [0.01,   0.02,  0.03]
BEAR_VIX_THRESH    = [18.0,  20.0,  22.0]
BULL_VIX_THRESH    = [15.0,  18.0]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sweep classifier thresholds over historical CSV data")
    p.add_argument("start", nargs="?", type=dt.date.fromisoformat, help="Start date (YYYY-MM-DD)")
    p.add_argument("end", nargs="?", type=dt.date.fromisoformat, help="End date (YYYY-MM-DD)")
    p.add_argument("--top", type=int, default=30, help="Number of top results to display")
    p.add_argument("--asset", default="SPX", help="Asset symbol (SPX, NDX, XSP)")
    return p.parse_args()


def summarize_adaptive(
    results: list[tuple],
    classifier: RegimeClassifier,
) -> dict | None:
    from collections import Counter
    traded_pairs = [(r, reg) for r, reg in results if r.traded]
    if not traded_pairs:
        return None

    pnls = [r.pnl for r, _ in traded_pairs]
    wins = [p for p in pnls if p > 0]
    regime_counts: Counter = Counter(reg for _, reg in results)

    return {
        "lookback":      classifier.lookback_days,
        "bear_ret":      classifier.bear_return_thresh,
        "bull_ret":      classifier.bull_return_thresh,
        "bear_vix":      classifier.bear_vix_thresh,
        "bull_vix":      classifier.bull_vix_thresh,
        "trades":        len(traded_pairs),
        "wins":          len(wins),
        "win_pct":       win_pct(pnls),
        "total_pnl":     round(sum(pnls), 4),
        "profit_factor": profit_factor(pnls),
        "sharpe":        sharpe(pnls),
        "n_bull":        regime_counts[Regime.BULL],
        "n_bear":        regime_counts[Regime.BEAR],
        "n_chop":        regime_counts[Regime.CHOP],
        "n_unknown":     regime_counts[Regime.UNKNOWN],
    }


def summarize_baseline(results: list, day_data: list[DayData]) -> dict | None:
    traded = [r for r in results if r.traded]
    if not traded:
        return None
    pnls = [r.pnl for r in traded]
    wins = [p for p in pnls if p > 0]
    return {
        "lookback": "BASE", "bear_ret": "-", "bull_ret": "-",
        "bear_vix": "-",    "bull_vix": "-",
        "trades":        len(traded),
        "wins":          len(wins),
        "win_pct":       win_pct(pnls),
        "total_pnl":     round(sum(pnls), 4),
        "profit_factor": profit_factor(pnls),
        "sharpe":        sharpe(pnls),
        "n_bull": 0, "n_bear": 0, "n_chop": 0, "n_unknown": 0,
    }


def print_table(rows: list[dict], top_n: int) -> None:
    rows = rows[:top_n]
    width = 135
    print(f"\n{'=' * width}")
    print(f"  TOP {len(rows)} CLASSIFIER THRESHOLD COMBINATIONS (sorted by profit factor)")
    print(f"{'=' * width}")
    hdr = (
        f"{'LBk':>3}  {'BearRet':>7}  {'BullRet':>7}  {'BearVIX':>7}  {'BullVIX':>7}  "
        f"{'N':>5}  {'W%':>5}  {'PnL':>10}  {'PF':>5}  {'Sharpe':>6}  "
        f"{'Bull':>5}  {'Bear':>5}  {'Chop':>5}  {'Unkn':>5}"
    )
    print(hdr)
    print("-" * width)
    for r in rows:
        lb_str = f"{r['lookback']:>3}" if isinstance(r['lookback'], int) else "BAS"
        bear_ret = f"{r['bear_ret']:>7}" if isinstance(r['bear_ret'], float) else f"{'  -':>7}"
        bull_ret = f"{r['bull_ret']:>7}" if isinstance(r['bull_ret'], float) else f"{'  -':>7}"
        bear_vix = f"{r['bear_vix']:>7}" if isinstance(r['bear_vix'], float) else f"{'  -':>7}"
        bull_vix = f"{r['bull_vix']:>7}" if isinstance(r['bull_vix'], float) else f"{'  -':>7}"
        print(
            f"{lb_str}  {bear_ret}  {bull_ret}  {bear_vix}  {bull_vix}  "
            f"{r['trades']:>5}  {r['win_pct']:>4.1f}%  {r['total_pnl']:>+10.4f}  "
            f"{r['profit_factor']:>5.2f}  {r['sharpe']:>6.3f}  "
            f"{r['n_bull']:>5}  {r['n_bear']:>5}  {r['n_chop']:>5}  {r['n_unknown']:>5}"
        )


def main() -> None:
    args = parse_args()
    start_arg, end_arg, top_n, asset = args.start, args.end, args.top, args.asset.upper()
    spx_path = Path(f"data/{asset.lower()}_1min.csv")

    if not spx_path.exists() or not VIX_PATH.exists():
        print(f"Missing CSV files: {spx_path}, {VIX_PATH}")
        sys.exit(1)

    print(f"\nLoading CSV data for {asset} (this takes a few seconds)...")
    loader = CsvDataLoader(spx_path, VIX_PATH)
    all_dates = loader.available_dates()

    start = start_arg or all_dates[0]
    end   = end_arg   or all_dates[-1]
    dates = [d for d in all_dates if start <= d <= end]

    print(f"Loading {len(dates)} days ({start} → {end})...")
    day_data: list[DayData] = []
    for date in dates:
        day = loader.load_day(date)
        if day:
            day_data.append(day)
    print(f"{len(day_data)} days loaded.")

    engine = SimulationEngine()

    # Pre-compute simulate_day() for each of the 4 fixed param sets once.
    # The classifier sweep only changes which result is picked per day — not
    # the sim itself — so we run 4×N sims total instead of 216×N.
    print("Pre-computing results for each param set (4 passes)...")
    named_params = {
        Regime.BULL:    BULL_PARAMS,
        Regime.BEAR:    BEAR_PARAMS,
        Regime.CHOP:    CHOP_PARAMS,
        Regime.UNKNOWN: DEFAULT_PARAMS,
    }
    precomputed: dict[Regime, list] = {
        regime: [engine.simulate_day(day, params) for day in day_data]
        for regime, params in named_params.items()
    }
    print("Pre-compute done.")

    # Baseline: DEFAULT_PARAMS on every day regardless of regime
    baseline_row = summarize_baseline(precomputed[Regime.UNKNOWN], day_data)

    grid = list(itertools.product(
        LOOKBACK_DAYS, BEAR_RETURN_THRESH, BULL_RETURN_THRESH,
        BEAR_VIX_THRESH, BULL_VIX_THRESH,
    ))
    print(f"Running {len(grid)} classifier threshold combinations...\n")

    rows = []
    for i, (lb, b_ret, bu_ret, b_vix, bu_vix) in enumerate(grid):
        clf = RegimeClassifier(
            lookback_days=lb,
            bear_return_thresh=b_ret,
            bull_return_thresh=bu_ret,
            bear_vix_thresh=b_vix,
            bull_vix_thresh=bu_vix,
        )
        # Classify each day then pick the pre-computed result for that regime
        day_results = [
            (precomputed[clf.classify(day.recent_closes, day.vix)][j],
             clf.classify(day.recent_closes, day.vix))
            for j, day in enumerate(day_data)
        ]
        row = summarize_adaptive(day_results, clf)
        if row:
            rows.append(row)

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(grid)} combos done...")

    if not rows:
        print("No results.")
        return

    rows.sort(key=lambda r: r["profit_factor"], reverse=True)

    all_rows = ([baseline_row] if baseline_row else []) + rows
    print_table(all_rows, top_n + 1)  # +1 to always show baseline

    Path("data/results").mkdir(exist_ok=True)
    out = Path("data/results/classifier_sweep_results.csv")
    with open(out, "w", newline="") as f:
        writer = csv_mod.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nFull results saved to {out} ({len(rows)} combos + 1 baseline)")


if __name__ == "__main__":
    main()
