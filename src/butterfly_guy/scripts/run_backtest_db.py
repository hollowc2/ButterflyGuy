"""Unified DB backtest for SPX and NDX butterflies.

Supports single-config mode (detailed per-day output) and parameter sweep
mode (grid search over comma-separated param lists, sorted by Sharpe, with
CSV export).

Usage
-----
    # All available NDX dates, live defaults
    uv run python -m butterfly_guy.scripts.run_backtest_db --asset NDX

    # Specific date range, SPX, CALL direction
    uv run python -m butterfly_guy.scripts.run_backtest_db 2026-03-25 2026-03-27 \\
        --asset SPX --direction CALL

    # Parameter sweep across NDX widths, rr-mins, drawdown levels, both directions
    uv run python -m butterfly_guy.scripts.run_backtest_db --asset NDX --sweep \\
        --wing 25,50,75 --rr-min 7.0,8.0,9.0 \\
        --morning-dd 0.50,0.60 --late-morning-dd 0.40,0.60 --afternoon-dd 0.30,0.40 \\
        --direction CALL,PUT
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import itertools
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
import yfinance as yf

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.parameter_sweeper import (
    _max_consecutive_losses,
    _max_drawdown,
    _profit_factor,
    _sharpe,
)
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    VIX_SIGMA_BY_WIDTH,
    ButterflyBuilder,
    vix_expected_move,
    vix_target_center,
)
from butterfly_guy.strategy.butterfly_selector import ButterflySelector

setup_logging(log_level="ERROR", json_output=False)
log = get_logger("run_backtest_db")

EASTERN = ZoneInfo("America/New_York")
DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

YFINANCE_TICKER = {"SPX": "^GSPC", "NDX": "^NDX"}

ASSET_DEFAULTS: dict[str, dict] = {
    "SPX": dict(
        wing_widths=[10, 20, 30],
        spot_range=100,
        center_tolerance=15.0,
        max_cost={10: 1.00, 20: 2.00, 30: 3.00},
    ),
    "NDX": dict(
        wing_widths=[25, 50, 75],
        spot_range=250,
        center_tolerance=100.0,
        max_cost={25: 2.00, 50: 4.00, 75: 6.00},
    ),
    "XSP": dict(
        wing_widths=[1, 2, 3],
        spot_range=10,
        center_tolerance=1.5,
        max_cost={1: 0.10, 2: 0.20, 3: 0.30},
    ),
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _floatlist(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",")]


def _intlist(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",")]


def _strlist(s: str) -> list[str]:
    return [x.strip().upper() for x in s.split(",")]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Unified SPX/NDX/XSP DB backtest — single-config or parameter sweep",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Comma-separated values (e.g. --wing 25,50,75) are only meaningful in "
            "--sweep mode; without --sweep the first value is used."
        ),
    )
    p.add_argument("start", nargs="?", type=dt.date.fromisoformat,
                   help="Start date YYYY-MM-DD (default: all available DB dates)")
    p.add_argument("end", nargs="?", type=dt.date.fromisoformat,
                   help="End date YYYY-MM-DD (default: all available DB dates)")

    p.add_argument("--asset", choices=["SPX", "NDX", "XSP"], default="SPX",
                   help="Underlying asset to backtest")
    p.add_argument("--direction", type=_strlist, default=None,
                   metavar="PUT|CALL|auto[,...]",
                   help="Direction(s). Default: PUT. Use 'auto' to derive from spot vs prev close each day.")

    p.add_argument("--wing", type=_intlist, default=None,
                   metavar="W[,W]",
                   help="Wing width(s). Default: asset widths (SPX:10,20,30  NDX:25,50,75). "
                        "Sweep mode tests each width independently.")
    p.add_argument("--rr-min", type=_floatlist, default=None,
                   metavar="RR[,RR]",
                   help="Min reward/risk ratio(s). Default: 8.0.")
    p.add_argument("--morning-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Morning drawdown threshold(s). Default: 0.60.")
    p.add_argument("--late-morning-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Late-morning drawdown threshold(s). Default: 0.60.")
    p.add_argument("--afternoon-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Afternoon drawdown threshold(s). Default: 0.40.")
    p.add_argument("--method", type=_strlist, default=None,
                   metavar="M[,M]",
                   help="Selection method(s): VIX, TARGET_COST, BEST_RR. Default: VIX.")

    p.add_argument("--slippage", type=float, default=0.05,
                   help="Per-spread slippage applied to entry and exit.")
    p.add_argument("--vix-max", type=float, default=None,
                   help="Skip days where VIX at entry exceeds this threshold.")
    p.add_argument("--use-abs-stop", action="store_true", default=False,
                   help="Enable absolute loss stop (default: off, matching live config).")

    p.add_argument("--sweep", action="store_true",
                   help="Run grid search over all comma-separated param combos.")
    p.add_argument("--top", type=int, default=20,
                   help="(Sweep) top N rows to print, sorted by Sharpe.")
    p.add_argument("--csv", type=Path, default=None,
                   help="(Sweep) CSV output path. Default: auto-named in current dir.")
    p.add_argument("--thinkback", action="store_true",
                   help="Print ToS ThinkBack validation checklists after per-day results.")

    args = p.parse_args()

    # Apply defaults that depend on asset (must be done after parsing)
    asset_cfg = ASSET_DEFAULTS[args.asset]
    if args.wing is None:
        args.wing = list(asset_cfg["wing_widths"])
    if args.direction is None:
        args.direction = ["auto"]
    if args.rr_min is None:
        args.rr_min = [8.0]
    if args.morning_dd is None:
        args.morning_dd = [0.60]
    if args.late_morning_dd is None:
        args.late_morning_dd = [0.60]
    if args.afternoon_dd is None:
        args.afternoon_dd = [0.40]
    if args.method is None:
        args.method = ["VIX"]

    return args


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def discover_dates(
    conn: asyncpg.Connection,
    underlying: str,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dt.date]:
    """All dates in [start, end] with >= 50 snapshots for `underlying`."""
    rows = await conn.fetch(
        """
        SELECT snapshot_time::date AS trade_date,
               COUNT(DISTINCT snapshot_time) AS snap_count
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = snapshot_time::date
          AND ($2::date IS NULL OR snapshot_time::date >= $2)
          AND ($3::date IS NULL OR snapshot_time::date <= $3)
        GROUP BY trade_date
        HAVING COUNT(DISTINCT snapshot_time) >= 50
        ORDER BY trade_date
        """,
        underlying, start, end,
    )
    return [r["trade_date"] for r in rows]


async def load_chains_from_db(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> dict[dt.datetime, list[OptionQuote]]:
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time::date = $2
        ORDER BY snapshot_time, strike, option_type
        """,
        underlying, date,
    )
    chains: dict[dt.datetime, list[OptionQuote]] = defaultdict(list)
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        chains[ts].append(
            OptionQuote(
                symbol=r["symbol"] or f"DB_{r['option_type'][0]}{int(r['strike'])}",
                underlying=underlying,
                expiration=date,
                strike=float(r["strike"]),
                option_type=r["option_type"],
                bid=float(r["bid"] or 0),
                ask=float(r["ask"] or 0),
                mark=float(r["mark"] or 0),
                last=float(r["last"] or 0),
                volume=int(r["volume"] or 0),
                open_interest=int(r["open_interest"] or 0),
                iv=float(r["iv"] or 0),
                delta=float(r["delta"] or 0),
                gamma=float(r["gamma"] or 0),
                theta=float(r["theta"] or 0),
                vega=float(r["vega"] or 0),
            )
        )
    return dict(chains)


async def load_bars_from_db(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> list[MinuteBar]:
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (snapshot_time)
            snapshot_time,
            spot_price
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND snapshot_time::date = $2
          AND spot_price IS NOT NULL
          AND spot_price > 0
        ORDER BY snapshot_time
        """,
        underlying, date,
    )
    bars: list[MinuteBar] = []
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        price = float(r["spot_price"])
        bars.append(MinuteBar(ts=ts, open=price, high=price, low=price, close=price, volume=0))
    return bars


async def get_prev_close(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> float:
    """Return the last spot price at or before 16:00 ET on the previous trading day."""
    row = await conn.fetchval(
        """
        SELECT price FROM spot_prices
        WHERE underlying = $1
          AND (ts AT TIME ZONE 'America/New_York')::date < $2
          AND (ts AT TIME ZONE 'America/New_York')::time <= '16:00:00'
        ORDER BY ts DESC
        LIMIT 1
        """,
        underlying, date,
    )
    if row:
        return float(row)
    return 5500.0


async def get_vix_at(conn: asyncpg.Connection, at_time: dt.datetime) -> float:
    row = await conn.fetchval(
        "SELECT price FROM spot_prices WHERE underlying = '$VIX' AND ts <= $1 ORDER BY ts DESC LIMIT 1",
        at_time,
    )
    if row:
        return float(row)
    date = at_time.date()
    hist = yf.Ticker("^VIX").history(start=date, end=date + dt.timedelta(days=1), interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[0])
    return 18.0


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------

def nearest_snapshot(
    chains: dict[dt.datetime, list[OptionQuote]],
    bar_ts: dt.datetime,
) -> list[OptionQuote] | None:
    candidates = [ts for ts in chains if ts <= bar_ts]
    if not candidates:
        return None
    return chains[max(candidates)]


def select_for_width(
    quotes: list[OptionQuote],
    spot: float,
    direction: str,
    vix: float,
    wing_width: int,
    rr_min: float,
    spot_range: int,
    center_tolerance: float,
    rr_target: float = 10.0,
    method: str = "VIX",
    max_cost_per_width: dict[int, float] | None = None,
) -> ButterflyCandidate | None:
    """Select the best butterfly candidate for a single wing width."""
    settings = StrategySettings(
        wing_widths=[wing_width],
        rr_min=rr_min,
        spot_range=spot_range,
        max_cost_per_width=max_cost_per_width or {},
    )
    builder = ButterflyBuilder(settings)
    selector = ButterflySelector(settings)
    candidates = builder.build_candidates(quotes, spot, direction)
    width_candidates = [c for c in candidates if c.wing_width == wing_width]
    
    if method == "TARGET_COST":
        return selector.select_best_by_target_cost(width_candidates)
    
    target_center = None
    if method == "VIX":
        target_center = vix_target_center(vix=vix, spot=spot, direction=direction, wing_width=wing_width)
    
    return selector.select_best(width_candidates, target_center=target_center, center_tolerance=center_tolerance)


def select_live_width(
    quotes: list[OptionQuote],
    spot: float,
    direction: str,
    vix: float,
    wing_widths: list[int],
    rr_min: float,
    spot_range: int,
    center_tolerance: float,
    rr_target: float = 10.0,
    method: str = "VIX",
    max_cost_per_width: dict[int, float] | None = None,
) -> ButterflyCandidate | None:
    """Cross-width selection."""
    if method == "TARGET_COST":
        settings = StrategySettings(
            wing_widths=wing_widths,
            rr_min=rr_min,
            spot_range=spot_range,
            max_cost_per_width=max_cost_per_width or {},
        )
        builder = ButterflyBuilder(settings)
        selector = ButterflySelector(settings)
        candidates = builder.build_candidates(quotes, spot, direction)
        return selector.select_best_by_target_cost(candidates)

    per_width_bests: list[ButterflyCandidate] = []
    for width in wing_widths:
        best = select_for_width(
            quotes, spot, direction, vix, width, rr_min, spot_range, center_tolerance, rr_target,
            method=method, max_cost_per_width=max_cost_per_width,
        )
        if best:
            per_width_bests.append(best)
    if not per_width_bests:
        return None
    return min(per_width_bests, key=lambda c: abs(c.reward_risk - rr_target))


# ---------------------------------------------------------------------------
# Chain cache patching
# ---------------------------------------------------------------------------

def _patch_chain_cache(chains: dict, date: dt.date):
    """Inject DB chains into the chain cache for `date`. Returns restore callable.

    Must patch both the chain_cache module AND simulation_engine's local binding,
    because simulation_engine uses `from chain_cache import load_chain_day` which
    creates a local reference that won't see module-level monkey-patches.
    """
    import butterfly_guy.backtest.chain_cache as _cc
    import butterfly_guy.backtest.simulation_engine as _se

    _original_cc_load = _cc.load_chain_day
    _original_se_load = _se.load_chain_day  # type: ignore[attr-defined]

    def _patched(d, cache_dir=None):
        if d == date:
            return chains
        return _original_cc_load(d, cache_dir) if cache_dir else _original_cc_load(d)

    _cc.load_chain_day = _patched  # type: ignore[assignment]
    _se.load_chain_day = _patched  # type: ignore[assignment]

    def restore():
        _cc.load_chain_day = _original_cc_load  # type: ignore[assignment]
        _se.load_chain_day = _original_se_load  # type: ignore[assignment]

    return restore


# ---------------------------------------------------------------------------
# Per-date data loading (shared between single and sweep modes)
# ---------------------------------------------------------------------------

async def load_date_data(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> dict | None:
    """Load all data for one date. Returns None if insufficient data."""
    chains = await load_chains_from_db(conn, date, underlying)
    bars = await load_bars_from_db(conn, date, underlying)
    if not chains or not bars:
        return None
    prev_close = await get_prev_close(conn, date, underlying)
    entry_bar = next(
        (b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(10, 0)),
        bars[0],
    )
    vix = await get_vix_at(conn, entry_bar.ts)
    return dict(
        date=date,
        chains=chains,
        bars=bars,
        prev_close=prev_close,
        entry_bar=entry_bar,
        entry_spot=entry_bar.close,
        vix=vix,
        day=DayData(date=date, bars=bars, vix=vix, prev_close=prev_close),
    )


# ---------------------------------------------------------------------------
# Sweep metrics
# ---------------------------------------------------------------------------

def _summarize_combo(
    combo_label: dict,
    day_results: list,  # list of (date, DayResult | None)
) -> dict:
    traded = [(date, r) for date, r in day_results if r is not None and r.traded]
    pnls = [r.pnl for _, r in traded]
    wins = sum(1 for p in pnls if p > 0)
    exit_reasons = [r.exit_reason for _, r in traded]

    base = {**combo_label, "trade_count": len(traded)}
    if not traded:
        return {
            **base,
            "win_rate": 0.0, "total_pnl": 0.0, "avg_pnl": 0.0,
            "sharpe": 0.0, "max_drawdown": 0.0, "profit_factor": 0.0,
            "max_consec_losses": 0,
            "exit_morning_dd": 0, "exit_late_morning_dd": 0,
            "exit_afternoon_dd": 0, "exit_eod": 0, "exit_expired": 0,
            "exit_abs_stop": 0,
        }
    return {
        **base,
        "win_rate": round(wins / len(traded), 4),
        "total_pnl": round(sum(pnls), 4),
        "avg_pnl": round(sum(pnls) / len(traded), 4),
        "sharpe": round(_sharpe(pnls), 4),
        "max_drawdown": round(_max_drawdown(pnls), 4),
        "profit_factor": _profit_factor(pnls),
        "max_consec_losses": _max_consecutive_losses(pnls),
        "exit_morning_dd": exit_reasons.count("drawdown_morning"),
        "exit_late_morning_dd": exit_reasons.count("drawdown_late_morning"),
        "exit_afternoon_dd": exit_reasons.count("drawdown_afternoon"),
        "exit_eod": exit_reasons.count("end_of_day"),
        "exit_expired": exit_reasons.count("expired"),
        "exit_abs_stop": exit_reasons.count("absolute_loss_stop"),
    }


# ---------------------------------------------------------------------------
# ThinkBack validation output
# ---------------------------------------------------------------------------

def print_thinkback_checklist(day_rows: list[dict], asset: str) -> None:
    """Print a per-trade ToS ThinkBack validation checklist."""
    traded_rows = [r for r in day_rows if r["result"].traded]
    if not traded_rows:
        return

    border = "\u2550" * 52
    print(f"\n{border}")
    print(f"  THINKBACK VALIDATION CHECKLISTS  \u2014  {asset}")
    print(border)

    for row in traded_rows:
        r = row["result"]
        d = row["data"]

        lower = int(r.center_strike - r.wing_width)
        center = int(r.center_strike)
        upper = int(r.center_strike + r.wing_width)
        opt = r.direction[0]  # 'C' or 'P'

        entry_et = r.entry_time.astimezone(EASTERN).strftime("%I:%M %p ET") if r.entry_time else "?"
        exit_et = r.exit_time.astimezone(EASTERN).strftime("%I:%M %p ET") if r.exit_time else "?"
        pnl_ct = r.pnl * 100

        print(f"\n  {d['date']}  {asset}  {r.direction}  ({r.wing_width}-wide)")
        print(f"  {'─'*48}")
        print(f"  Butterfly : {lower}{opt} / {center}{opt} / {upper}{opt}")
        print(f"  Entry     : {entry_et:<14}  mark = ${r.entry_price:.2f}")
        print(f"  Peak      : ${r.peak_value:.2f}")
        print(f"  Exit      : {exit_et:<14}  mark = ${r.exit_price:.2f}   ({r.exit_reason})")
        print(f"  PnL/ct    : ${pnl_ct:+.2f}")
        print(f"")
        print(f"  ThinkBack steps:")
        print(f"    1. Set date to {d['date']}")
        print(f"    2. Load {asset} 0-DTE {r.direction} butterfly:")
        print(f"         Buy  1x  {lower}{opt}")
        print(f"         Sell 2x  {center}{opt}")
        print(f"         Buy  1x  {upper}{opt}")
        print(f"    3. Mark at {entry_et} \u2192 expect ~${r.entry_price:.2f}")
        print(f"    4. Mark at {exit_et} \u2192 expect ~${r.exit_price:.2f}")

    print(f"\n{border}\n")


# ---------------------------------------------------------------------------
# Single-config mode
# ---------------------------------------------------------------------------

async def run_single(args: argparse.Namespace) -> None:
    asset_cfg = ASSET_DEFAULTS[args.asset]
    direction_arg = args.direction[0]
    wing_widths = args.wing
    rr_min = args.rr_min[0]
    morning_dd = args.morning_dd[0]
    late_morning_dd = args.late_morning_dd[0]
    afternoon_dd = args.afternoon_dd[0]
    method = args.method[0]
    center_tolerance = asset_cfg["center_tolerance"]
    spot_range = asset_cfg["spot_range"]

    print(f"\n{'='*72}")
    print(f"  DB BACKTEST  |  {args.asset}  {direction_arg} butterfly")
    print(f"  Widths: {wing_widths}  rr_min: {rr_min}  DD: {morning_dd}/{late_morning_dd}/{afternoon_dd}")
    print(f"  Method: {method}  abs_stop: {'ON' if args.use_abs_stop else 'OFF'}  "
          f"slippage: {args.slippage}  vix_max: {args.vix_max or 'none'}")
    print(f"{'='*72}\n")

    conn = await asyncpg.connect(DB_DSN)
    try:
        dates = await discover_dates(conn, args.asset, args.start, args.end)
    finally:
        await conn.close()

    if not dates:
        print("ERROR: No full trading days found in DB for the specified range.")
        return

    print(f"  {len(dates)} trading day(s): {dates[0]} → {dates[-1]}\n")

    engine = SimulationEngine()
    day_rows: list[dict] = []

    for date in dates:
        print(f"  Loading {date}...", end="", flush=True)
        conn = await asyncpg.connect(DB_DSN)
        try:
            d = await load_date_data(conn, date, args.asset)
        finally:
            await conn.close()

        if d is None:
            print(" SKIPPED (no data)")
            continue

        if args.vix_max and d["vix"] > args.vix_max:
            print(f" SKIPPED (VIX {d['vix']:.1f} > {args.vix_max})")
            continue

        if direction_arg == "auto":
            direction = "CALL" if d["entry_spot"] >= d["prev_close"] else "PUT"
        else:
            direction = direction_arg

        entry_quotes = nearest_snapshot(d["chains"], d["entry_bar"].ts) or []
        chosen = select_live_width(
            quotes=entry_quotes,
            spot=d["entry_spot"],
            direction=direction,
            vix=d["vix"],
            wing_widths=wing_widths,
            rr_min=rr_min,
            spot_range=spot_range,
            center_tolerance=center_tolerance,
            method=method,
            max_cost_per_width=asset_cfg["max_cost"],
        )

        if not chosen:
            print(f" SKIPPED (no qualifying butterfly)")
            continue

        print(f" {chosen.wing_width}W {direction} center={chosen.center_strike:.0f}  "
              f"R/R={chosen.reward_risk:.1f}  cost=${chosen.cost:.2f}")

        params = SimulationParams(
            wing_width=chosen.wing_width,
            direction_override=direction,
            rr_min=rr_min,
            morning_drawdown=morning_dd,
            late_morning_drawdown=late_morning_dd,
            afternoon_drawdown=afternoon_dd,
            slippage=args.slippage,
            use_vix_center=(method == "VIX"),
            selection_method=method,
            max_cost_per_width=asset_cfg["max_cost"],
            use_absolute_loss_stop=args.use_abs_stop,
        )

        restore = _patch_chain_cache(d["chains"], date)
        result = engine.simulate_day(d["day"], params)
        restore()

        day_rows.append({"data": d, "chosen": chosen, "result": result})

    if not day_rows:
        print("\nNo tradeable days found.")
        return

    # ── Per-day table ────────────────────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"  PER-DAY RESULTS  —  {args.asset}  {direction}")
    print(f"{'='*90}")
    print(f"  {'Date':>10}  {'VIX':>5}  {'Spot':>7}  {'W':>2}  {'Center':>7}  "
          f"{'Entry$':>7}  {'Peak$':>6}  {'Exit$':>6}  {'Exit Reason':<22}  {'PnL/ct':>8}")
    print("  " + "-" * 88)

    pnls_ct: list[float] = []
    exit_counts: dict[str, int] = defaultdict(int)

    for row in day_rows:
        d = row["data"]
        r = row["result"]
        if not r.traded:
            print(f"  {d['date']!s:>10}  {d['vix']:>5.1f}  {d['entry_spot']:>7.0f}  "
                  f"  NO TRADE")
            continue
        pnl_ct = r.pnl * 100
        pnls_ct.append(pnl_ct)
        exit_counts[r.exit_reason] += 1
        print(f"  {d['date']!s:>10}  {d['vix']:>5.1f}  {d['entry_spot']:>7.0f}  "
              f"{r.wing_width:>2}  {r.center_strike:>7.0f}  "
              f"${r.entry_price:>6.2f}  ${r.peak_value:>5.2f}  ${r.exit_price:>5.2f}  "
              f"{r.exit_reason:<22}  ${pnl_ct:>+7.2f}")

    # ── Summary ──────────────────────────────────────────────────────────────
    n_traded = len(pnls_ct)
    if n_traded == 0:
        print("\n  No trades executed.\n")
        return

    wins = [p for p in pnls_ct if p > 0]
    print(f"\n{'='*90}")
    print(f"  SUMMARY  ({len(day_rows)} days loaded, {n_traded} traded)")
    print(f"{'='*90}")
    print(f"  Win rate    : {len(wins)}/{n_traded}  ({len(wins)/n_traded*100:.0f}%)")
    print(f"  Total PnL   : ${sum(pnls_ct):+.2f} / contract")
    print(f"  Avg PnL     : ${sum(pnls_ct)/n_traded:+.2f} / contract")
    print(f"  Best day    : ${max(pnls_ct):+.2f} / contract")
    print(f"  Worst day   : ${min(pnls_ct):+.2f} / contract")
    print(f"  Sharpe      : {_sharpe([p/100 for p in pnls_ct]):.3f}")
    print(f"  Profit factor: {_profit_factor(pnls_ct):.3f}")
    print(f"  Exit reasons: "
          + "  ".join(f"{k}={v}" for k, v in sorted(exit_counts.items())))
    print(f"{'='*90}\n")

    if args.thinkback:
        print_thinkback_checklist(day_rows, args.asset)


# ---------------------------------------------------------------------------
# Sweep mode
# ---------------------------------------------------------------------------

async def run_sweep(args: argparse.Namespace) -> None:
    asset_cfg = ASSET_DEFAULTS[args.asset]
    center_tolerance = asset_cfg["center_tolerance"]
    spot_range = asset_cfg["spot_range"]

    # Build combo grid
    param_grid = list(itertools.product(
        args.wing,
        args.direction,
        args.rr_min,
        args.morning_dd,
        args.late_morning_dd,
        args.afternoon_dd,
        args.method,
    ))
    total_combos = len(param_grid)

    print(f"\n{'='*72}")
    print(f"  PARAMETER SWEEP  |  {args.asset}  |  {total_combos} combos")
    print(f"  Wings: {args.wing}  Directions: {args.direction}  rr_min: {args.rr_min}")
    print(f"  Methods: {args.method}  morning_dd: {args.morning_dd}  late_morning_dd: {args.late_morning_dd}")
    print(f"  afternoon_dd: {args.afternoon_dd}  abs_stop: {'ON' if args.use_abs_stop else 'OFF'}  slippage: {args.slippage}")
    print(f"{'='*72}\n")

    # Discover dates and pre-load all data from DB
    conn = await asyncpg.connect(DB_DSN)
    try:
        dates = await discover_dates(conn, args.asset, args.start, args.end)
    finally:
        await conn.close()

    if not dates:
        print("ERROR: No full trading days found in DB for the specified range.")
        return

    print(f"  {len(dates)} trading day(s): {dates[0]} → {dates[-1]}")
    print(f"  Pre-loading chain data from DB...")

    all_date_data: dict[dt.date, dict] = {}
    for date in dates:
        conn = await asyncpg.connect(DB_DSN)
        try:
            d = await load_date_data(conn, date, args.asset)
        finally:
            await conn.close()

        if d is None:
            print(f"    {date} SKIPPED (no data)")
            continue
        if args.vix_max and d["vix"] > args.vix_max:
            print(f"    {date} SKIPPED (VIX {d['vix']:.1f} > {args.vix_max})")
            continue
        print(f"    {date}  VIX={d['vix']:.1f}  spot={d['entry_spot']:.0f}")
        all_date_data[date] = d

    if not all_date_data:
        print("\nNo usable dates loaded.")
        return

    print(f"\n  Running {total_combos} combos across {len(all_date_data)} dates...\n")

    engine = SimulationEngine()
    sweep_results: list[dict] = []

    for i, (wing, direction, rr_min, morning_dd, late_morning_dd, afternoon_dd, method) in enumerate(param_grid, 1):
        combo_label = dict(
            wing_width=wing,
            direction=direction,
            rr_min=rr_min,
            morning_dd=morning_dd,
            late_morning_dd=late_morning_dd,
            afternoon_dd=afternoon_dd,
            method=method,
        )
        params = SimulationParams(
            wing_width=wing,
            direction_override=direction,
            rr_min=rr_min,
            morning_drawdown=morning_dd,
            late_morning_drawdown=late_morning_dd,
            afternoon_drawdown=afternoon_dd,
            slippage=args.slippage,
            use_vix_center=(method == "VIX"),
            selection_method=method,
            max_cost_per_width=asset_cfg["max_cost"],
            use_absolute_loss_stop=args.use_abs_stop,
        )

        day_results: list[tuple[dt.date, object]] = []
        for date, d in all_date_data.items():
            # Resolve "auto" direction per-date (same logic as single-config mode)
            resolved_direction = (
                ("CALL" if d["entry_spot"] >= d["prev_close"] else "PUT")
                if direction == "auto"
                else direction
            )

            entry_quotes = nearest_snapshot(d["chains"], d["entry_bar"].ts) or []
            chosen = select_for_width(
                quotes=entry_quotes,
                spot=d["entry_spot"],
                direction=resolved_direction,
                vix=d["vix"],
                wing_width=wing,
                rr_min=rr_min,
                spot_range=spot_range,
                center_tolerance=center_tolerance,
                method=method,
                max_cost_per_width=asset_cfg["max_cost"],
            )
            if chosen is None:
                day_results.append((date, None))
                continue

            restore = _patch_chain_cache(d["chains"], date)
            sim_params = SimulationParams(
                wing_width=chosen.wing_width,
                direction_override=resolved_direction,
                rr_min=rr_min,
                morning_drawdown=morning_dd,
                late_morning_drawdown=late_morning_dd,
                afternoon_drawdown=afternoon_dd,
                slippage=args.slippage,
                use_vix_center=(method == "VIX"),
                selection_method=method,
                max_cost_per_width=asset_cfg["max_cost"],
                use_absolute_loss_stop=args.use_abs_stop,
            )
            result = engine.simulate_day(d["day"], sim_params)
            restore()
            day_results.append((date, result))

        row = _summarize_combo(combo_label, day_results)
        sweep_results.append(row)

        # Progress every 10 combos
        if i % 10 == 0 or i == total_combos:
            print(f"  [{i:>{len(str(total_combos))}}/{total_combos}]  last: "
                  f"{wing}W {direction} rr={rr_min} dd={morning_dd}/{late_morning_dd}/{afternoon_dd}  "
                  f"→ trades={row['trade_count']}  sharpe={row['sharpe']:.3f}  "
                  f"win={row['win_rate']*100:.0f}%")

    # Sort by Sharpe; push zero-trade combos to bottom
    sweep_results.sort(
        key=lambda r: (r["trade_count"] > 0, r["sharpe"]),
        reverse=True,
    )

    # ── Console table ────────────────────────────────────────────────────────
    top_n = min(args.top, len(sweep_results))
    print(f"\n{'='*105}")
    print(f"  TOP {top_n} COMBOS BY SHARPE  (of {total_combos})")
    print(f"{'='*105}")
    print(f"  {'W':>3}  {'Dir':>4}  {'RR':>5}  {'Morn':>5}  {'LtMrn':>6}  {'Aftn':>5}  "
          f"{'Trd':>4}  {'Win%':>5}  {'TotPnL':>8}  {'AvgPnL':>8}  "
          f"{'Sharpe':>7}  {'PF':>5}  {'MaxDD':>7}  {'MaxCL':>6}")
    print("  " + "-" * 103)

    for row in sweep_results[:top_n]:
        print(f"  {row['wing_width']:>3}  {row['direction']:>4}  "
              f"{row['rr_min']:>5.1f}  {row['morning_dd']:>5.2f}  "
              f"{row['late_morning_dd']:>6.2f}  {row['afternoon_dd']:>5.2f}  "
              f"{row['trade_count']:>4}  {row['win_rate']*100:>4.0f}%  "
              f"${row['total_pnl']*100:>+7.2f}  ${row['avg_pnl']*100:>+7.2f}  "
              f"{row['sharpe']:>7.3f}  {row['profit_factor']:>5.3f}  "
              f"${row['max_drawdown']*100:>6.2f}  {row['max_consec_losses']:>6}")

    print(f"{'='*105}\n")

    # ── CSV output ────────────────────────────────────────────────────────────
    ts_str = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    start_str = (args.start or dates[0]).strftime("%Y%m%d")
    end_str = (args.end or dates[-1]).strftime("%Y%m%d")
    csv_path = args.csv or Path(f"sweep_{args.asset}_{start_str}_{end_str}_{ts_str}.csv")

    fieldnames = [
        "wing_width", "direction", "method", "rr_min", "morning_dd", "late_morning_dd", "afternoon_dd",
        "trade_count", "win_rate", "total_pnl", "avg_pnl",
        "sharpe", "max_drawdown", "profit_factor", "max_consec_losses",
        "exit_morning_dd", "exit_late_morning_dd", "exit_afternoon_dd",
        "exit_eod", "exit_expired", "exit_abs_stop",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sweep_results)

    print(f"  Full sweep results written to: {csv_path}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    args = parse_args()
    if args.sweep:
        await run_sweep(args)
    else:
        await run_single(args)


if __name__ == "__main__":
    asyncio.run(main())
