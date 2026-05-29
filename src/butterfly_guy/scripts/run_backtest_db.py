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
import bisect
import csv
import datetime as dt
import html
import itertools
import math
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
import yfinance as yf

from butterfly_guy.backtest.chain_cache import ChainDay
from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.metrics import (
    max_consecutive_losses as _max_consecutive_losses,
)
from butterfly_guy.backtest.metrics import (
    max_drawdown as _max_drawdown,
)
from butterfly_guy.backtest.metrics import (
    profit_factor as _profit_factor,
)
from butterfly_guy.backtest.metrics import (
    sharpe as _sharpe,
)
from butterfly_guy.backtest.simulation_engine import (
    DrawdownWindow,
    SimulationEngine,
    SimulationParams,
)
from butterfly_guy.core.config import AppConfig, load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.entry_selection import select_entry_candidate
from butterfly_guy.strategy.gap_regime_filter import GapRegimeFilter
from butterfly_guy.strategy.regime_classifier import Regime, RegimeClassifier

_regime_classifier = RegimeClassifier()

setup_logging(log_level="ERROR", json_output=False)
log = get_logger("run_backtest_db")

EASTERN = ZoneInfo("America/New_York")

YFINANCE_TICKER = {"SPX": "^GSPC", "NDX": "^NDX"}

ASSET_DEFAULTS: dict[str, dict] = {
    "SPX": dict(
        wing_widths=[10, 20, 30],
        spot_range=100,
        center_tolerance=15.0,
        max_cost={10: 1.00, 20: 2.00, 30: 3.00},
        drawdowns=(0.60, 0.90, 0.75),
    ),
    "NDX": dict(
        wing_widths=[25, 50, 75],
        spot_range=250,
        center_tolerance=100.0,
        max_cost={25: 2.00, 50: 4.00, 75: 6.00},
        drawdowns=(1.00, 0.95, 0.90),
    ),
    "XSP": dict(
        wing_widths=[2, 3, 4, 5, 6, 7],
        spot_range=10,
        center_tolerance=1.5,
        max_cost={2: 0.20, 3: 0.30, 4: 0.40, 5: 0.50, 6: 0.60, 7: 0.70},
        drawdowns=(0.60, 0.90, 0.75),
    ),
}

ASSET_CONFIG_PATHS = {
    "SPX": "configs/config.yaml",
    "NDX": "configs/config_ndx.yaml",
    "XSP": "configs/config_xsp.yaml",
}


def load_asset_config(asset: str) -> AppConfig:
    """Load the live config for an asset so DB replays share runtime defaults."""
    return load_config(config_path=ASSET_CONFIG_PATHS[asset])


def _asset_drawdowns(
    config: AppConfig,
    fallback: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Return live morning/late/afternoon drawdown thresholds."""
    regimes = config.profit_management.regimes
    return (
        regimes.get("morning").drawdown_threshold if regimes.get("morning") else fallback[0],
        (
            regimes.get("late_morning").drawdown_threshold
            if regimes.get("late_morning")
            else fallback[1]
        ),
        regimes.get("afternoon").drawdown_threshold if regimes.get("afternoon") else fallback[2],
    )


def _parse_config_time(value: str) -> dt.time:
    """Parse an HH:MM config time."""
    hour, minute = value.split(":", 1)
    return dt.time(int(hour), int(minute))


def _live_width_label(
    *,
    wing_provided: bool,
    method: str,
    config: AppConfig,
    wing_widths: list[int] | None,
) -> str:
    if not wing_provided and method == "VIX" and config.strategy.vix_width_buckets:
        return "live VIX bucket"
    return str(wing_widths or config.strategy.wing_widths)


def resolve_db_dsn() -> str:
    """Resolve the DB connection string for local backtests.

    Backtests follow the repo's normal config loading so `.env` works without
    manual shell exporting and stale `DATABASE_URL` values cannot override it.
    """
    return load_config().database.dsn


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _floatlist(s: str) -> list[float]:
    return [float(x.strip()) for x in s.split(",")]


def _intlist(s: str) -> list[int]:
    return [int(x.strip()) for x in s.split(",")]


def _strlist(s: str) -> list[str]:
    return [x.strip().upper() for x in s.split(",")]


def _timelist_pst(s: str) -> list[dt.time]:
    result = []
    for t in s.split(","):
        h, m = t.strip().split(":")
        result.append(dt.time(int(h), int(m)))
    return result


def _pst_to_et(t: dt.time) -> dt.time:
    total = t.hour * 60 + t.minute + 180  # PT is always ET-3
    return dt.time(total // 60, total % 60)


def _find_bar_at(bars: list[MinuteBar], target_et: dt.datetime) -> MinuteBar | None:
    for bar in bars:
        if bar.ts >= target_et:
            return bar
    return None


def _find_entry_bar_at(
    bars: list[MinuteBar],
    target_et: dt.datetime,
    *,
    max_lag_seconds: int | None = 120,
) -> MinuteBar | None:
    bar = _find_bar_at(bars, target_et)
    if bar is None or max_lag_seconds is None:
        return bar
    lag = (bar.ts.astimezone(EASTERN) - target_et).total_seconds()
    if lag > max_lag_seconds:
        return None
    return bar


def _parse_dd_schedule(value: str) -> tuple[DrawdownWindow, ...] | None:
    if value.lower() in {"default", "baseline", "current"}:
        return None
    windows: list[DrawdownWindow] = []
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        pieces = part.split(":")
        if len(pieces) not in (2, 3):
            raise argparse.ArgumentTypeError(
                "drawdown schedule windows must be START-END:THRESHOLD[:LABEL]"
            )
        range_part, threshold_part = pieces[0], pieces[1]
        try:
            start_s, end_s = range_part.split("-", 1)
            start_min = float(start_s)
            end_min = float(end_s)
            threshold = float(threshold_part)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "drawdown schedule windows must use numeric START-END:THRESHOLD[:LABEL]"
            ) from exc
        if start_min < 0 or end_min <= start_min:
            raise argparse.ArgumentTypeError("drawdown schedule windows must have 0 <= START < END")
        if threshold <= 0 or threshold > 1:
            raise argparse.ArgumentTypeError("drawdown schedule thresholds must be in (0, 1]")
        label = pieces[2] if len(pieces) == 3 else f"{int(start_min)}_{int(end_min)}"
        windows.append(DrawdownWindow(start_min, end_min, threshold, label))
    if not windows:
        raise argparse.ArgumentTypeError("drawdown schedule cannot be empty")
    windows.sort(key=lambda w: w.start_min)
    return tuple(windows)


def _dd_schedule_label(schedule: tuple[DrawdownWindow, ...] | None) -> str:
    if not schedule:
        return "default"
    return ",".join(f"{w.start_min:g}-{w.end_min:g}:{w.threshold:g}:{w.label}" for w in schedule)


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
                   help="Direction(s). Default: PUT. Use 'auto' to derive from "
                        "spot vs prev close each day.")

    p.add_argument("--wing", type=_intlist, default=None,
                   metavar="W[,W]",
                   help="Wing width(s). Default: asset live config. "
                        "Sweep mode tests each width independently.")
    p.add_argument("--rr-min", type=_floatlist, default=None,
                   metavar="RR[,RR]",
                   help="Min reward/risk ratio(s). Default: 8.0.")
    p.add_argument("--morning-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Morning drawdown threshold(s). Default: asset live config.")
    p.add_argument("--late-morning-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Late-morning drawdown threshold(s). Default: asset live config.")
    p.add_argument("--afternoon-dd", type=_floatlist, default=None,
                   metavar="DD[,DD]",
                   help="Afternoon drawdown threshold(s). Default: asset live config.")
    p.add_argument("--dd-schedule", type=_parse_dd_schedule, action="append", default=None,
                   metavar="START-END:DD[:LABEL],...",
                   help="Optional minutes-since-open drawdown schedule. Can be passed multiple "
                        "times in --sweep mode to compare named policies. Use 'default' to include "
                        "the legacy morning/late-morning/afternoon thresholds. Example: "
                        "0-150:0.60:early,150-300:0.90:mid,300-330:0.75:noon,330-390:0.50:late")
    p.add_argument("--profit-strategy", type=_strlist, default=None,
                   metavar="peakvaluetrailer|profitprotector[,..]",
                   help="Profit-management strategy for live/backtest parity. "
                        "Use comma-separated values with --sweep to compare policies.")
    p.add_argument("--method", type=_strlist, default=None,
                   metavar="M[,M]",
                   help=(
                       "Selection method(s): VIX, TARGET_COST, BEST_RR. "
                       "Default: asset live config."
                   ))
    p.add_argument("--entry-time", type=_timelist_pst, default=None,
                   metavar="T[,T]",
                   help="Entry window start time(s) in PST, e.g. 7:00,7:10,7:30. "
                        "Each defines a 10-minute entry window. Default: 7:00.")

    p.add_argument("--slippage", type=float, default=None,
                   help=(
                       "Per-spread slippage applied to entry and exit. "
                       "Default: asset live config."
                   ))
    p.add_argument("--vix-max", type=float, default=None,
                   help="Skip days where VIX at entry exceeds this threshold.")
    p.add_argument("--use-abs-stop", action=argparse.BooleanOptionalAction, default=None,
                   help="Enable absolute loss stop. Default: asset live config.")

    p.add_argument("--sweep", action="store_true",
                   help="Run grid search over all comma-separated param combos.")
    p.add_argument("--top", type=int, default=20,
                   help="(Sweep) top N rows to print, sorted by Sharpe.")
    p.add_argument("--csv", type=Path, default=None,
                   help="(Sweep) CSV output path. Default: auto-named in current dir.")
    p.add_argument("--html-report", type=Path, default=None,
                   help="(Single-config) Write a self-contained HTML trade report.")
    p.add_argument("--thinkback", action="store_true",
                   help="Print ToS ThinkBack validation checklists after per-day results.")
    p.add_argument("--compare-synthetic", action="store_true",
                   help="Run a second synthetic-only pass and print side-by-side comparison. "
                        "Single-config mode only; ignored with --sweep.")
    p.add_argument("--compare-synthetic-same-entry", action="store_true",
                   help="Run a BS-only intraday pass pinned to the real entry's "
                        "center/width/price. "
                        "Isolates intraday BS pricing error from entry selection. "
                        "Single-config mode only; ignored with --sweep.")
    p.add_argument("--live-pinned-replay", action="store_true",
                   help="Replay exit behavior from actual butterfly_trades rows. "
                        "Uses live direction, strikes, width, entry price, and entry time.")
    p.add_argument("--selection-parity-report", action="store_true",
                   help="For each live trade date, compare the live trade row to "
                        "backtest selection "
                        "at the live entry timestamp.")
    p.add_argument("--allow-late-entry-fallback", action="store_true",
                   help="Allow the default backtest to use any later snapshot when the configured "
                        "entry-time snapshot is missing. By default, entry snapshots must be "
                        "within "
                        "120 seconds of the requested time.")
    p.add_argument("--gap-filter", type=float, default=None,
                   metavar="MIN_PCT",
                   help="Only enter CALL butterflies on days where the gap vs prior close is "
                        ">= MIN_PCT "
                        "(e.g. 0.0 = any gap up, 0.0025 = gap up >=0.25%%). "
                        "Days below the threshold are skipped entirely.")
    p.add_argument("--strategy-f", action="store_true",
                   help="Strategy F: all three filters must pass to enter a CALL butterfly — "
                        "(1) regime=BULL, (2) VIX at entry < VIX prev close, (3) SPX gap >=0.25%%.")
    p.add_argument("--bull-call-bias", action="store_true",
                   help="Override to CALL in BULL regime on gap-down days.")
    p.add_argument("--min-gap-pct", type=float, default=None,
                   metavar="PCT",
                   help="Skip days where |gap vs prev close| < PCT (e.g. 0.0025 = 0.25%%).")

    args = p.parse_args()

    # Apply defaults that depend on asset (must be done after parsing)
    asset_cfg = ASSET_DEFAULTS[args.asset]
    live_config = load_asset_config(args.asset)
    args.wing_provided = args.wing is not None
    if args.wing is None:
        args.wing = list(live_config.strategy.wing_widths)
    if args.direction is None:
        args.direction = ["auto"]
    args.direction = [d if d.upper() != "AUTO" else "auto" for d in args.direction]
    if args.rr_min is None:
        args.rr_min = [live_config.strategy.rr_min]
    morning_dd, late_morning_dd, afternoon_dd = _asset_drawdowns(
        live_config,
        asset_cfg["drawdowns"],
    )
    if args.morning_dd is None:
        args.morning_dd = [morning_dd]
    if args.late_morning_dd is None:
        args.late_morning_dd = [late_morning_dd]
    if args.afternoon_dd is None:
        args.afternoon_dd = [afternoon_dd]
    if args.method is None:
        args.method = [live_config.entry.strike_selection_method]
    if args.entry_time is None:
        args.entry_time = [_parse_config_time(live_config.entry.start_time)]
    if args.dd_schedule is None:
        args.dd_schedule = [None]
    if args.profit_strategy is None:
        args.profit_strategy = [live_config.profit_management.strategy]
    if args.use_abs_stop is None:
        args.use_abs_stop = live_config.profit_management.use_absolute_loss_stop
    if args.slippage is None:
        args.slippage = live_config.execution.paper_slippage_per_spread
    valid_profit_strategies = {"peakvaluetrailer", "profitprotector"}
    args.profit_strategy = [s.lower() for s in args.profit_strategy]
    invalid_profit_strategies = [
        s for s in args.profit_strategy if s not in valid_profit_strategies
    ]
    if invalid_profit_strategies:
        p.error(
            "--profit-strategy must be one of: "
            + ", ".join(sorted(valid_profit_strategies))
        )

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
    return ChainDay(chains)


async def load_entry_chains(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> ChainDay:
    """Load only the entry-window snapshots (09:30–10:45 ET) for butterfly selection."""
    start_utc = dt.datetime(
        date.year, date.month, date.day, 9, 30, tzinfo=EASTERN
    ).astimezone(dt.timezone.utc)
    end_utc = dt.datetime(
        date.year, date.month, date.day, 12, 15, tzinfo=EASTERN
    ).astimezone(dt.timezone.utc)
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time >= $3
          AND snapshot_time <= $4
        ORDER BY snapshot_time, strike, option_type
        """,
        underlying, date, start_utc, end_utc,
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
    return ChainDay(chains)


async def load_monitoring_chains(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
    strikes: list[float],
    option_types: list[str],
) -> ChainDay:
    """Load full-day snapshots for specific strikes only (3 legs of a butterfly)."""
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time::date = $2
          AND strike = ANY($3::numeric[])
          AND option_type = ANY($4)
        ORDER BY snapshot_time, strike, option_type
        """,
        underlying, date, strikes, option_types,
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
    return ChainDay(chains)


async def load_live_trades(
    conn: asyncpg.Connection,
    underlying: str,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT *
        FROM butterfly_trades
        WHERE underlying = $1
          AND ($2::date IS NULL OR trade_date >= $2)
          AND ($3::date IS NULL OR trade_date <= $3)
        ORDER BY entry_time, id
        """,
        underlying, start, end,
    )
    return [dict(row) for row in rows]


def merge_chains(entry: ChainDay, monitoring: ChainDay) -> ChainDay:
    """Merge entry-window (all strikes) and monitoring (3 strikes, full day) chains.

    Entry wins on overlapping timestamps so butterfly selection sees full strike data.
    """
    merged = {**monitoring, **entry}
    return ChainDay(merged)


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


async def get_recent_closes(
    conn: asyncpg.Connection, date: dt.date, underlying: str, n: int = 30
) -> list[float]:
    """Up to *n* daily closes strictly before *date*, chronological order."""
    rows = await conn.fetch(
        """
        SELECT close FROM daily_bars
        WHERE  underlying = $1 AND date < $2
        ORDER  BY date DESC LIMIT $3
        """,
        underlying, date, n,
    )
    return [float(r["close"]) for r in reversed(rows)]


async def get_vix_prev_close(conn: asyncpg.Connection, date: dt.date) -> float:
    """Return VIX daily close strictly before *date* from daily_bars."""
    val = await conn.fetchval(
        """
        SELECT close
        FROM daily_bars
        WHERE underlying = '$VIX' AND date < $1
        ORDER BY date DESC
        LIMIT 1
        """,
        date,
    )
    return float(val) if val is not None else 18.0


async def get_vix_at(conn: asyncpg.Connection, at_time: dt.datetime) -> float:
    row = await conn.fetchval(
        """
        SELECT price
        FROM spot_prices
        WHERE underlying = '$VIX' AND ts <= $1
        ORDER BY ts DESC
        LIMIT 1
        """,
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
    if isinstance(chains, ChainDay):
        keys = chains._sorted_keys
        i = bisect.bisect_right(keys, bar_ts) - 1
        return chains[keys[i]] if i >= 0 else None
    candidates = [ts for ts in chains if ts <= bar_ts]
    return chains[max(candidates)] if candidates else None


def candidate_from_trade_row(trade: dict) -> ButterflyCandidate:
    return ButterflyCandidate(
        direction=trade["direction"],
        wing_width=int(trade["wing_width"]),
        center_strike=float(trade["center_strike"]),
        lower_strike=float(trade["lower_strike"]),
        upper_strike=float(trade["upper_strike"]),
        cost=float(trade["entry_price"]),
        ask=float(trade["entry_price"]),
        max_profit=float(trade["wing_width"]) - float(trade["entry_price"]),
        reward_risk=(
            (float(trade["wing_width"]) - float(trade["entry_price"]))
            / float(trade["entry_price"])
            if float(trade["entry_price"]) > 0
            else 0.0
        ),
        lower_be=float(trade["lower_strike"]) + float(trade["entry_price"]),
        upper_be=float(trade["upper_strike"]) - float(trade["entry_price"]),
        distance_from_spot=0.0,
        spot_price=0.0,
        lower_symbol=trade.get("lower_symbol") or "",
        center_symbol=trade.get("center_symbol") or "",
        upper_symbol=trade.get("upper_symbol") or "",
    )


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


def _force_synthetic_for_date(date: dt.date):
    """Patch load_chain_day to return None for `date`, forcing BS synthetic fallback.
    Returns a restore callable.
    """
    import butterfly_guy.backtest.chain_cache as _cc
    import butterfly_guy.backtest.simulation_engine as _se

    _original_cc_load = _cc.load_chain_day
    _original_se_load = _se.load_chain_day  # type: ignore[attr-defined]

    def _patched(d, cache_dir=None):
        if d == date:
            return None
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

def select_direction_bar(bars: list[MinuteBar]) -> MinuteBar:
    """Use the first regular-session snapshot for gap direction."""
    return next(
        (b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(9, 30)),
        bars[0],
    )


async def load_date_data(
    conn: asyncpg.Connection,
    date: dt.date,
    underlying: str,
) -> dict | None:
    """Load all data for one date. Returns None if insufficient data."""
    chains = await load_entry_chains(conn, date, underlying)
    bars = await load_bars_from_db(conn, date, underlying)
    if not chains or not bars:
        return None
    prev_close = await get_prev_close(conn, date, underlying)
    direction_bar = select_direction_bar(bars)
    entry_bar = next(
        (b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(10, 0)),
        bars[0],
    )
    vix = await get_vix_at(conn, entry_bar.ts)
    vix_prev_close = await get_vix_prev_close(conn, date)
    recent_closes = await get_recent_closes(conn, date, underlying)
    return dict(
        date=date,
        chains=chains,
        bars=bars,
        prev_close=prev_close,
        direction_bar=direction_bar,
        open_spot=direction_bar.open,
        entry_bar=entry_bar,
        entry_spot=entry_bar.close,
        vix=vix,
        vix_prev_close=vix_prev_close,
        day=DayData(
            date=date,
            bars=bars,
            vix=vix,
            prev_close=prev_close,
            recent_closes=recent_closes,
        ),
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
            "exit_drawdown": 0, "exit_abs_stop": 0,
            "exit_profit_floor": 0, "exit_breakeven_floor": 0,
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
        "exit_drawdown": sum(1 for reason in exit_reasons if reason.startswith("drawdown_")),
        "exit_eod": exit_reasons.count("end_of_day"),
        "exit_expired": exit_reasons.count("expired"),
        "exit_abs_stop": exit_reasons.count("absolute_loss_stop"),
        "exit_profit_floor": exit_reasons.count("profitprotector_profit_floor"),
        "exit_breakeven_floor": exit_reasons.count("profitprotector_breakeven_floor"),
    }


# ---------------------------------------------------------------------------
# Trade value histogram
# ---------------------------------------------------------------------------

def _fitted_density_counts(
    pnls_ct: list[float],
    *,
    start: float,
    bucket_w: int,
    n_buckets: int,
) -> list[float]:
    """Return bucket-height estimates from a Gaussian KDE fit."""
    n = len(pnls_ct)
    if n < 3 or n_buckets <= 0:
        return []

    mean = sum(pnls_ct) / n
    variance = sum((p - mean) ** 2 for p in pnls_ct) / (n - 1)
    stdev = math.sqrt(variance)
    if stdev <= 0:
        return []

    bandwidth = 1.06 * stdev * (n ** -0.2)
    if bandwidth <= 0:
        return []

    inv_norm = 1 / math.sqrt(2 * math.pi)
    fitted: list[float] = []
    for i in range(n_buckets):
        mid = start + (i + 0.5) * bucket_w
        density = sum(
            inv_norm * math.exp(-0.5 * ((mid - p) / bandwidth) ** 2) / bandwidth
            for p in pnls_ct
        ) / n
        fitted.append(density * n * bucket_w)
    return fitted


def _print_pnl_histogram(pnls_ct: list[float]) -> None:
    """ASCII histogram with a fitted density curve overlaid on the trade buckets."""
    if len(pnls_ct) < 2:
        return

    lo, hi = min(pnls_ct), max(pnls_ct)

    # Pick smallest fixed bucket width that covers the data in ≤14 buckets
    bucket_w = 50
    for bucket_w in (50, 100, 200, 250, 500, 1000):
        start = math.floor(lo / bucket_w) * bucket_w
        n_buckets = math.ceil((hi - start) / bucket_w)
        if n_buckets <= 14:
            break
    if n_buckets <= 0:
        return

    counts = [0] * n_buckets
    for p in pnls_ct:
        idx = min(int((p - start) / bucket_w), n_buckets - 1)
        counts[idx] += 1

    fitted = _fitted_density_counts(
        pnls_ct,
        start=start,
        bucket_w=bucket_w,
        n_buckets=n_buckets,
    )
    curve_rows = [max(1, round(v)) if v >= 0.35 else 0 for v in fitted]
    if not curve_rows:
        curve_rows = [0] * n_buckets
    max_h = max(max(counts), max(curve_rows, default=0))
    col_w = 6  # chars per column

    print(
        "\n  TRADE DISTRIBUTION  "
        "(▒▒▒▒ = loss  ████ = win  ╳╳╳╳ = fitted density,  each row = 1 trade)\n"
    )

    for h in range(max_h, 0, -1):
        row = f"  {h:>2} │"
        for i, cnt in enumerate(counts):
            mid = start + (i + 0.5) * bucket_w
            if curve_rows[i] == h:
                blk = " ╳╳╳╳ "
            elif cnt >= h:
                blk = " ▒▒▒▒ " if mid < 0 else " ████ "
            else:
                blk = " " * col_w
            row += blk
        print(row)

    print("     └" + "──────" * n_buckets)

    lbl = "      "
    for i in range(n_buckets):
        b = start + i * bucket_w
        lbl += f"${b:.0f}".center(col_w)
    print(lbl)


# ---------------------------------------------------------------------------
# HTML trade report
# ---------------------------------------------------------------------------

def _format_et(value: dt.datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(EASTERN).strftime("%H:%M")


def _duration_min(start: dt.datetime | None, end: dt.datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 60)


def _report_bar_svg(values: list[float]) -> str:
    if not values:
        return ""
    width = max(760, len(values) * 18)
    height = 240
    pad = 30
    max_abs = max(abs(v) for v in values) or 1
    zero_y = height / 2
    slot = (width - pad * 2) / len(values)
    rects = []
    for idx, value in enumerate(values):
        bar_h = abs(value) / max_abs * (height / 2 - pad)
        x = pad + idx * slot + 2
        y = zero_y - bar_h if value >= 0 else zero_y
        color = "#168a4a" if value >= 0 else "#b42318"
        rects.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(slot - 4, 4):.1f}" '
            f'height="{bar_h:.1f}" fill="{color}"><title>'
            f"Trade {idx + 1}: ${value:+.0f}</title></rect>"
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Per-trade PnL bars">'
        f'<line x1="{pad}" y1="{zero_y}" x2="{width - pad}" y2="{zero_y}" '
        f'stroke="#8a8f98" stroke-width="1"/>'
        + "".join(rects)
        + "</svg>"
    )


def _report_equity_svg(values: list[float]) -> str:
    if not values:
        return ""
    equity = []
    running = 0.0
    for value in values:
        running += value
        equity.append(running)
    points = [0.0, *equity]
    width = max(760, len(points) * 18)
    height = 260
    pad = 34
    lo = min(points)
    hi = max(points)
    span = hi - lo or 1
    step = (width - pad * 2) / (len(points) - 1)
    coords = []
    for idx, value in enumerate(points):
        x = pad + idx * step
        y = height - pad - ((value - lo) / span) * (height - pad * 2)
        coords.append(f"{x:.1f},{y:.1f}")
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Cumulative PnL equity curve">'
        f'<polyline points="{" ".join(coords)}" fill="none" '
        f'stroke="#2563eb" stroke-width="3"/>'
        f'<text x="{pad}" y="22">${hi:+.0f}</text>'
        f'<text x="{pad}" y="{height - 8}">${lo:+.0f}</text>'
        + "</svg>"
    )


def _report_histogram_svg(values: list[float]) -> str:
    if not values:
        return ""

    lo = min(values)
    hi = max(values)
    bucket_w = 50
    for bucket_w in (50, 100, 200, 250, 500, 1000):
        start = math.floor(lo / bucket_w) * bucket_w
        n_buckets = max(1, math.ceil((hi - start) / bucket_w))
        if n_buckets <= 14:
            break

    buckets = [0] * n_buckets
    for value in values:
        idx = min(int((value - start) / bucket_w), n_buckets - 1)
        buckets[idx] += 1

    width = max(760, n_buckets * 74)
    height = 280
    pad_x = 44
    pad_top = 28
    pad_bottom = 62
    plot_h = height - pad_top - pad_bottom
    max_count = max(buckets) or 1
    slot = (width - pad_x * 2) / n_buckets
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Return distribution histogram">',
        f'<line x1="{pad_x}" y1="{height - pad_bottom}" '
        f'x2="{width - pad_x}" y2="{height - pad_bottom}" '
        f'stroke="#8a8f98" stroke-width="1"/>',
    ]

    for idx, count in enumerate(buckets):
        bucket_start = start + idx * bucket_w
        bucket_end = bucket_start + bucket_w
        mid = bucket_start + bucket_w / 2
        bar_h = count / max_count * plot_h if count else 0
        x = pad_x + idx * slot + 8
        y = height - pad_bottom - bar_h
        color = "#168a4a" if mid >= 0 else "#b42318"
        label = f"${bucket_start:.0f} to ${bucket_end:.0f}"
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(slot - 16, 8):.1f}" '
            f'height="{bar_h:.1f}" fill="{color}"><title>'
            f"{label}: {count} trade{'s' if count != 1 else ''}</title></rect>"
        )
        parts.append(
            f'<text x="{x + max(slot - 16, 8) / 2:.1f}" y="{y - 6:.1f}" '
            f'text-anchor="middle">{count}</text>'
        )
        parts.append(
            f'<text x="{x + max(slot - 16, 8) / 2:.1f}" '
            f'y="{height - pad_bottom + 18:.1f}" text-anchor="middle">'
            f'${bucket_start:.0f}</text>'
        )
    parts.append(
        f'<text x="{width - pad_x}" y="{height - pad_bottom + 38}" '
        f'text-anchor="end">bucket = ${bucket_w}</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _write_single_html_report(
    *,
    path: Path,
    asset: str,
    direction: str,
    day_rows: list[dict],
    exit_counts: dict[str, int],
    pnls_ct: list[float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wins = [p for p in pnls_ct if p > 0]
    total = sum(pnls_ct)
    avg = total / len(pnls_ct) if pnls_ct else 0.0
    best = max(pnls_ct) if pnls_ct else 0.0
    worst = min(pnls_ct) if pnls_ct else 0.0
    win_rate = len(wins) / len(pnls_ct) * 100 if pnls_ct else 0.0

    rows_html = []
    for row in day_rows:
        data = row["data"]
        result = row["result"]
        chosen = row["chosen"]
        if not result.traded:
            continue
        pnl_ct = result.pnl * 100
        duration = _duration_min(result.entry_time, result.exit_time)
        rows_html.append(
            "<tr>"
            f"<td>{data['date']}</td>"
            f"<td>{html.escape(result.direction)}</td>"
            f"<td>{result.wing_width:.0f}W</td>"
            f"<td>{result.center_strike:.0f}</td>"
            f"<td>{chosen.lower_strike:.0f} / {chosen.center_strike:.0f} / "
            f"{chosen.upper_strike:.0f}</td>"
            f"<td>{data['vix']:.1f}</td>"
            f"<td>{data['entry_spot']:.0f}</td>"
            f"<td>{_format_et(result.entry_time)}</td>"
            f"<td>{_format_et(result.exit_time)}</td>"
            f"<td>{duration if duration is not None else ''}</td>"
            f"<td>${result.entry_price:.2f}</td>"
            f"<td>${result.peak_value:.2f}</td>"
            f"<td>${result.exit_price:.2f}</td>"
            f"<td>{html.escape(result.exit_reason)}</td>"
            f"<td class=\"{'pos' if pnl_ct >= 0 else 'neg'}\">"
            f"${pnl_ct:+.0f}</td>"
            "</tr>"
        )

    exit_rows = "".join(
        f"<tr><td>{html.escape(reason)}</td><td>{count}</td></tr>"
        for reason, count in sorted(exit_counts.items())
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{asset} Backtest Trade Report</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f9;
      color: #20242c;
    }}
    body {{ margin: 0; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 28px; }}
    h1 {{ font-size: 28px; margin: 0 0 4px; font-weight: 720; }}
    h2 {{ font-size: 16px; margin: 30px 0 10px; }}
    .sub {{ color: #626a77; margin-bottom: 22px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(6, minmax(120px, 1fr));
      gap: 10px;
    }}
    .stat {{
      background: #fff;
      border: 1px solid #d9dde5;
      border-radius: 8px;
      padding: 12px;
    }}
    .label {{ color: #687080; font-size: 12px; }}
    .value {{ font-size: 21px; font-weight: 720; margin-top: 4px; }}
    .panel {{
      background: #fff;
      border: 1px solid #d9dde5;
      border-radius: 8px;
      padding: 14px;
      overflow-x: auto;
    }}
    svg {{ width: 100%; min-width: 760px; height: auto; display: block; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
    }}
    th, td {{
      border-bottom: 1px solid #e4e7ec;
      padding: 8px 10px;
      text-align: right;
    }}
    th {{
      color: #4b5563;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0;
      background: #fafbfc;
      position: sticky;
      top: 0;
    }}
    td:first-child, th:first-child,
    td:nth-child(2), th:nth-child(2),
    td:nth-child(5), th:nth-child(5),
    td:nth-child(14), th:nth-child(14) {{ text-align: left; }}
    .pos {{ color: #067647; font-weight: 700; }}
    .neg {{ color: #b42318; font-weight: 700; }}
    @media (max-width: 860px) {{
      main {{ padding: 16px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
    }}
  </style>
</head>
<body>
<main>
  <h1>{asset} Backtest Trade Report</h1>
  <div class="sub">
    {html.escape(direction)} direction mode · {len(day_rows)} days loaded ·
    {len(pnls_ct)} trades
  </div>
  <section class="stats">
    <div class="stat">
      <div class="label">Total PnL</div><div class="value">${total:+.0f}</div>
    </div>
    <div class="stat">
      <div class="label">Win Rate</div><div class="value">{win_rate:.0f}%</div>
    </div>
    <div class="stat">
      <div class="label">Average</div><div class="value">${avg:+.0f}</div>
    </div>
    <div class="stat">
      <div class="label">Best</div><div class="value">${best:+.0f}</div>
    </div>
    <div class="stat">
      <div class="label">Worst</div><div class="value">${worst:+.0f}</div>
    </div>
    <div class="stat">
      <div class="label">Profit Factor</div>
      <div class="value">{_profit_factor(pnls_ct):.2f}</div>
    </div>
  </section>
  <h2>Equity Curve</h2>
  <section class="panel">{_report_equity_svg(pnls_ct)}</section>
  <h2>Per-Trade PnL</h2>
  <section class="panel">{_report_bar_svg(pnls_ct)}</section>
  <h2>Return Distribution</h2>
  <section class="panel">{_report_histogram_svg(pnls_ct)}</section>
  <h2>Exit Reasons</h2>
  <section class="panel">
    <table>
      <thead><tr><th>Reason</th><th>Count</th></tr></thead>
      <tbody>{exit_rows}</tbody>
    </table>
  </section>
  <h2>Trades</h2>
  <section class="panel">
    <table>
      <thead>
        <tr>
          <th>Date</th><th>Dir</th><th>Width</th><th>Center</th><th>Strikes</th>
          <th>VIX</th><th>Spot</th><th>Entry</th><th>Exit</th><th>Min</th>
          <th>Entry$</th><th>Peak$</th><th>Exit$</th><th>Exit Reason</th><th>PnL/ct</th>
        </tr>
      </thead>
      <tbody>{''.join(rows_html)}</tbody>
    </table>
  </section>
</main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


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
        print("")
        print("  ThinkBack steps:")
        print(f"    1. Set date to {d['date']}")
        print(f"    2. Load {asset} 0-DTE {r.direction} butterfly:")
        print(f"         Buy  1x  {lower}{opt}")
        print(f"         Sell 2x  {center}{opt}")
        print(f"         Buy  1x  {upper}{opt}")
        print(f"    3. Mark at {entry_et} \u2192 expect ~${r.entry_price:.2f}")
        print(f"    4. Mark at {exit_et} \u2192 expect ~${r.exit_price:.2f}")

    print(f"\n{border}\n")


# ---------------------------------------------------------------------------
# Comparison table (real vs synthetic)
# ---------------------------------------------------------------------------

def _print_comparison_table(day_rows: list[dict]) -> None:
    w = 92
    print(f"\n{'='*w}")
    print("  REAL vs SYNTHETIC COMPARISON")
    print(f"{'='*w}")
    print(f"  {'Date':>10}  {'Run':>4}  {'W':>2}  {'Center':>7}  "
          f"{'Entry$':>7}  {'Peak$':>6}  {'Exit$':>6}  {'Exit Reason':<22}  {'PnL/ct':>8}")
    print("  " + "─" * (w - 2))

    real_total = 0.0
    synth_total = 0.0

    # Collect data for stats
    real_pnls: list[float] = []
    synth_pnls: list[float] = []
    real_wins = 0
    synth_wins = 0
    real_trades = 0
    synth_trades = 0
    trade_matches = 0      # same center strike
    exit_matches = 0       # same exit reason
    matched_days = 0       # days both sides traded
    matched_real_pnls: list[float] = []
    matched_synth_pnls: list[float] = []

    for row in day_rows:
        d = row["data"]
        r = row["result"]
        sr = row["synth_result"]
        date = d["date"]

        for label, res in (("REAL", r), ("SYNT", sr)):
            if res is None or not res.traded:
                print(f"  {date!s:>10}  {label:>4}   -       -         -       -       -    "
                      f"{'NO TRADE':<22}")
            else:
                pnl_ct = res.pnl * 100
                if label == "REAL":
                    real_total += pnl_ct
                else:
                    synth_total += pnl_ct
                print(
                    f"  {date!s:>10}  {label:>4}  {res.wing_width:>2}  "
                    f"{res.center_strike:>7.0f}  ${res.entry_price:>6.2f}  "
                    f"${res.peak_value:>5.2f}  ${res.exit_price:>5.2f}  "
                    f"{res.exit_reason:<22}  ${pnl_ct:>+7.2f}"
                )

        # Accumulate stats
        r_traded = r is not None and r.traded
        s_traded = sr is not None and sr.traded

        if r_traded:
            real_trades += 1
            real_pnls.append(r.pnl * 100)
            if r.pnl > 0:
                real_wins += 1
        if s_traded:
            synth_trades += 1
            synth_pnls.append(sr.pnl * 100)
            if sr.pnl > 0:
                synth_wins += 1
        if r_traded and s_traded:
            matched_days += 1
            matched_real_pnls.append(r.pnl * 100)
            matched_synth_pnls.append(sr.pnl * 100)
            if abs(r.center_strike - sr.center_strike) < 0.5:
                trade_matches += 1
            if r.exit_reason == sr.exit_reason:
                exit_matches += 1

    print(f"\n  Real total: ${real_total:+.2f}  /  Synth total: ${synth_total:+.2f}")
    print(f"{'='*w}\n")

    # ── Aggregate stats block ────────────────────────────────────────────────
    sw = 60
    print(f"\n{'='*sw}")
    print("  AGGREGATE COMPARISON STATS")
    print(f"{'='*sw}")
    print(f"  {'':20}  {'REAL':>8}  {'SYNTH':>8}")
    print(f"  {'─'*56}")
    print(f"  {'Trades':20}  {real_trades:>8}  {synth_trades:>8}")

    real_wr = f"{real_wins/real_trades*100:.0f}%" if real_trades else "n/a"
    synth_wr = f"{synth_wins/synth_trades*100:.0f}%" if synth_trades else "n/a"
    print(f"  {'Win rate':20}  {real_wr:>8}  {synth_wr:>8}")

    real_tot = f"${real_total:+.2f}" if real_trades else "n/a"
    synth_tot = f"${synth_total:+.2f}" if synth_trades else "n/a"
    print(f"  {'Total PnL/ct':20}  {real_tot:>8}  {synth_tot:>8}")

    real_avg = f"${real_total/real_trades:+.2f}" if real_trades else "n/a"
    synth_avg = f"${synth_total/synth_trades:+.2f}" if synth_trades else "n/a"
    print(f"  {'Avg PnL/ct':20}  {real_avg:>8}  {synth_avg:>8}")

    real_sh = f"{_sharpe([p/100 for p in real_pnls]):.3f}" if real_trades >= 2 else "n/a"
    synth_sh = f"{_sharpe([p/100 for p in synth_pnls]):.3f}" if synth_trades >= 2 else "n/a"
    print(f"  {'Sharpe':20}  {real_sh:>8}  {synth_sh:>8}")

    print(f"  {'─'*56}")

    # Pearson r on matched days
    if matched_days >= 2:
        r_series = matched_real_pnls
        s_series = matched_synth_pnls
        n = len(r_series)
        mean_r = sum(r_series) / n
        mean_s = sum(s_series) / n
        cov = sum((a - mean_r) * (b - mean_s) for a, b in zip(r_series, s_series)) / n
        std_r = (sum((a - mean_r) ** 2 for a in r_series) / n) ** 0.5
        std_s = (sum((b - mean_s) ** 2 for b in s_series) / n) ** 0.5
        corr = cov / (std_r * std_s) if std_r > 0 and std_s > 0 else 0.0
        corr_str = f"{corr:.2f}"
        avg_div = sum(a - b for a, b in zip(r_series, s_series)) / n
        div_str = f"${avg_div:+.2f}/ct"
    else:
        corr_str = "n/a"
        div_str = "n/a"

    trade_match_str = f"{trade_matches/matched_days*100:.0f}%" if matched_days else "n/a"
    exit_match_str = f"{exit_matches/matched_days*100:.0f}%" if matched_days else "n/a"

    print(f"  {'PnL correlation':20}  {corr_str:>8}  (matched days: {matched_days})")
    print(f"  {'Trade match %':20}  {trade_match_str:>8}  (same center strike)")
    print(f"  {'Exit match %':20}  {exit_match_str:>8}  (same exit reason)")
    print(f"  {'Avg divergence':20}  {div_str:>8}  (real − synth, matched)")
    print(f"{'='*sw}\n")


def _print_same_entry_comparison_table(day_rows: list[dict]) -> None:
    """Print real vs same-entry-synthetic comparison (pinned center/price, BS intraday only)."""
    w = 92
    sw = 60
    print(f"\n{'='*w}")
    print("  REAL vs SAME-ENTRY SYNTHETIC  (identical entry; BS intraday only)")
    print(f"{'='*w}")
    print(f"  {'Date':>10}  {'Run':>5}  {'W':>2}  {'Center':>7}  "
          f"{'Entry$':>7}  {'Peak$':>6}  {'Exit$':>6}  {'Exit Reason':<22}  {'PnL/ct':>8}")
    print("  " + "─" * (w - 2))

    real_total = 0.0
    se_total = 0.0
    real_pnls: list[float] = []
    se_pnls: list[float] = []
    real_wins = real_trades = 0
    se_wins = se_trades = 0
    exit_matches = 0
    peak_diffs: list[float] = []
    exit_diffs: list[float] = []
    matched_days = 0

    for row in day_rows:
        d = row["data"]
        r = row["result"]
        se = row.get("same_entry_result")
        date = d["date"]

        for label, res in (("REAL", r), ("SE-SY", se)):
            if res is None or not res.traded:
                print(f"  {date!s:>10}  {label:>5}   -       -         -       -       -    "
                      f"{'NO TRADE':<22}")
            else:
                pnl_ct = res.pnl * 100
                if label == "REAL":
                    real_total += pnl_ct
                else:
                    se_total += pnl_ct
                print(
                    f"  {date!s:>10}  {label:>5}  {res.wing_width:>2}  "
                    f"{res.center_strike:>7.0f}  ${res.entry_price:>6.2f}  "
                    f"${res.peak_value:>5.2f}  ${res.exit_price:>5.2f}  "
                    f"{res.exit_reason:<22}  ${pnl_ct:>+7.2f}"
                )

        r_traded = r is not None and r.traded
        s_traded = se is not None and se.traded
        if r_traded:
            real_trades += 1
            real_pnls.append(r.pnl * 100)
            if r.pnl > 0:
                real_wins += 1
        if s_traded:
            se_trades += 1
            se_pnls.append(se.pnl * 100)
            if se.pnl > 0:
                se_wins += 1
        if r_traded and s_traded:
            matched_days += 1
            if r.exit_reason == se.exit_reason:
                exit_matches += 1
            peak_diffs.append(abs(r.peak_value - se.peak_value))
            exit_diffs.append(r.exit_price - se.exit_price)

    print(f"\n  Real total: ${real_total:+.2f}  /  SE-Synth total: ${se_total:+.2f}")
    print(f"{'='*w}\n")

    print(f"\n{'='*sw}")
    print("  SAME-ENTRY AGGREGATE STATS")
    print(f"{'='*sw}")
    print(f"  {'':20}  {'REAL':>8}  {'SE-SY':>8}")
    print(f"  {'─'*56}")
    print(f"  {'Trades':20}  {real_trades:>8}  {se_trades:>8}")

    real_wr = f"{real_wins/real_trades*100:.0f}%" if real_trades else "n/a"
    se_wr = f"{se_wins/se_trades*100:.0f}%" if se_trades else "n/a"
    print(f"  {'Win rate':20}  {real_wr:>8}  {se_wr:>8}")

    real_tot = f"${real_total:+.2f}" if real_trades else "n/a"
    se_tot = f"${se_total:+.2f}" if se_trades else "n/a"
    print(f"  {'Total PnL/ct':20}  {real_tot:>8}  {se_tot:>8}")

    real_avg = f"${real_total/real_trades:+.2f}" if real_trades else "n/a"
    se_avg = f"${se_total/se_trades:+.2f}" if se_trades else "n/a"
    print(f"  {'Avg PnL/ct':20}  {real_avg:>8}  {se_avg:>8}")

    real_sh = f"{_sharpe([p/100 for p in real_pnls]):.3f}" if real_trades >= 2 else "n/a"
    se_sh = f"{_sharpe([p/100 for p in se_pnls]):.3f}" if se_trades >= 2 else "n/a"
    print(f"  {'Sharpe':20}  {real_sh:>8}  {se_sh:>8}")

    print(f"  {'─'*56}")

    if matched_days >= 2:
        n = matched_days
        mean_r = sum(real_pnls) / n
        mean_s = sum(se_pnls) / n
        cov = sum((a - mean_r) * (b - mean_s) for a, b in zip(real_pnls, se_pnls)) / n
        std_r = (sum((a - mean_r) ** 2 for a in real_pnls) / n) ** 0.5
        std_s = (sum((b - mean_s) ** 2 for b in se_pnls) / n) ** 0.5
        corr = cov / (std_r * std_s) if std_r > 0 and std_s > 0 else 0.0
        corr_str = f"{corr:.2f}"
        avg_exit_div = sum(exit_diffs) / n
        avg_peak_div = sum(peak_diffs) / n
    else:
        corr_str = avg_exit_div = avg_peak_div = "n/a"

    exit_match_str = f"{exit_matches/matched_days*100:.0f}%" if matched_days else "n/a"
    print(f"  {'PnL correlation':20}  {corr_str:>8}  (matched days: {matched_days})")
    print(f"  {'Exit match %':20}  {exit_match_str:>8}  (same exit reason)")
    if isinstance(avg_peak_div, float):
        print(f"  {'Avg peak divergence':20}  ${avg_peak_div:>6.2f}   (abs diff real vs SE-synth)")
        print(
            f"  {'Avg exit divergence':20}  ${avg_exit_div:>+6.2f}   "
            "(real exit$ − SE-synth exit$)"
        )
    else:
        print(f"  {'Avg peak divergence':20}  {'n/a':>8}")
        print(f"  {'Avg exit divergence':20}  {'n/a':>8}")
    print(f"{'='*sw}\n")


# ---------------------------------------------------------------------------
# Live-pinned replay and parity diagnostics
# ---------------------------------------------------------------------------

async def run_live_pinned_replay(args: argparse.Namespace) -> None:
    live_config = load_asset_config(args.asset)
    rr_min = args.rr_min[0]
    morning_dd = args.morning_dd[0]
    late_morning_dd = args.late_morning_dd[0]
    afternoon_dd = args.afternoon_dd[0]
    dd_schedule = args.dd_schedule[0]
    profit_strategy = args.profit_strategy[0]
    method = args.method[0]

    print(f"\n{'='*94}")
    print(f"  LIVE-PINNED REPLAY  |  {args.asset}")
    print("  Source: butterfly_trades rows; entry selection is bypassed; exits are replayed.")
    print(f"{'='*94}\n")

    conn = await asyncpg.connect(resolve_db_dsn())
    day_rows: list[dict] = []
    try:
        trades = await load_live_trades(conn, args.asset, args.start, args.end)
        if not trades:
            print("No live trade rows found for the specified range.")
            return

        engine = SimulationEngine()
        for trade in trades:
            date = trade["trade_date"]
            entry_time = trade["entry_time"]
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=dt.timezone.utc)

            print(f"  Loading live trade {trade['id']} {date}...", end="", flush=True)
            d = await load_date_data(conn, date, args.asset)
            if d is None:
                print(" SKIPPED (no chain/bar data)")
                continue

            pinned = candidate_from_trade_row(trade)
            monitoring = await load_monitoring_chains(
                conn,
                date,
                args.asset,
                [pinned.lower_strike, pinned.center_strike, pinned.upper_strike],
                [pinned.direction],
            )
            if not monitoring:
                print(" SKIPPED (no monitoring chain data for live legs)")
                continue

            params = SimulationParams(
                wing_width=pinned.wing_width,
                direction_override=pinned.direction,
                rr_min=rr_min,
                morning_drawdown=morning_dd,
                late_morning_drawdown=late_morning_dd,
                afternoon_drawdown=afternoon_dd,
                slippage=args.slippage,
                use_vix_center=(method == "VIX"),
                selection_method=method,
                max_cost_per_width=live_config.strategy.max_cost_per_width,
                max_loss_from_cost=live_config.profit_management.max_loss_from_cost,
                use_absolute_loss_stop=args.use_abs_stop,
                drawdown_schedule=dd_schedule,
                profit_management_strategy=profit_strategy,
                profitprotector=live_config.profit_management.profitprotector,
            )
            restore = _patch_chain_cache(monitoring, date)
            result = engine.simulate_day_from_entry(
                d["day"],
                params,
                entry_candidate=pinned,
                entry_price=float(trade["entry_price"]),
                entry_time=entry_time,
            )
            restore()

            live_exit = trade.get("exit_reason") or "-"
            live_pnl = float(trade["pnl"]) * 100 if trade.get("pnl") is not None else None
            replay_pnl = result.pnl * 100
            print(
                f" {pinned.wing_width}W {pinned.direction} center={pinned.center_strike:.0f} "
                f"live_exit={live_exit} replay_exit={result.exit_reason}"
            )
            day_rows.append(
                {
                    "trade": trade,
                    "data": {"date": date, "vix": d["vix"], "entry_spot": d["entry_spot"]},
                    "chosen": pinned,
                    "result": result,
                    "live_pnl": live_pnl,
                    "replay_pnl": replay_pnl,
                }
            )
    finally:
        await conn.close()

    if not day_rows:
        print("\nNo live trades were replayed.")
        return

    print(f"\n{'='*104}")
    print("  LIVE-PINNED REPLAY RESULTS")
    print(f"{'='*104}")
    print(
        f"  {'ID':>4}  {'Date':>10}  {'Dir':>4}  {'W':>2}  {'Center':>7}  "
        f"{'Entry ET':>8}  {'Entry$':>7}  {'Live Exit':<22}  {'Replay Exit':<22}  "
        f"{'LivePnL':>8}  {'ReplayPnL':>9}"
    )
    print("  " + "-" * 102)

    replay_pnls: list[float] = []
    exit_matches = 0
    comparable = 0
    for row in day_rows:
        trade = row["trade"]
        result = row["result"]
        entry_et = trade["entry_time"].astimezone(EASTERN).strftime("%H:%M")
        live_exit = trade.get("exit_reason") or "-"
        live_pnl = row["live_pnl"]
        replay_pnl = row["replay_pnl"]
        replay_pnls.append(replay_pnl)
        if trade.get("exit_reason"):
            comparable += 1
            if trade["exit_reason"] == result.exit_reason:
                exit_matches += 1
        live_pnl_s = f"${live_pnl:+.2f}" if live_pnl is not None else "n/a"
        print(
            f"  {trade['id']:>4}  {trade['trade_date']!s:>10}  {trade['direction']:>4}  "
            f"{int(trade['wing_width']):>2}  {float(trade['center_strike']):>7.0f}  "
            f"{entry_et:>8}  ${float(trade['entry_price']):>6.2f}  "
            f"{live_exit:<22}  {result.exit_reason:<22}  "
            f"{live_pnl_s:>8}  ${replay_pnl:>+8.2f}"
        )

    print(f"{'='*104}")
    print(
        f"  Replayed: {len(day_rows)}  Total replay PnL: ${sum(replay_pnls):+.2f}/ct  "
        f"Exit match: {exit_matches}/{comparable if comparable else 0}"
    )


async def run_selection_parity_report(args: argparse.Namespace) -> None:
    live_config = load_asset_config(args.asset)

    print(f"\n{'='*118}")
    print(f"  SELECTION PARITY REPORT  |  {args.asset}")
    print("  Compares live trade rows with backtest selection at each live entry timestamp.")
    print(f"{'='*118}\n")

    conn = await asyncpg.connect(resolve_db_dsn())
    try:
        trades = await load_live_trades(conn, args.asset, args.start, args.end)
        if not trades:
            print("No live trade rows found for the specified range.")
            return

        print(
            f"  {'ID':>4}  {'Date':>10}  {'Entry ET':>8}  {'Spot':>8}  {'VIX':>5}  "
            f"{'Live':>17}  {'Replay':>17}  {'Bucket':<14}  Per-width winners"
        )
        print("  " + "-" * 116)

        for trade in trades:
            date = trade["trade_date"]
            entry_time = trade["entry_time"]
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=dt.timezone.utc)
            d = await load_date_data(conn, date, args.asset)
            if d is None:
                print(f"  {trade['id']:>4}  {date!s:>10}  SKIPPED (no data)")
                continue

            entry_bar = _find_bar_at(d["bars"], entry_time.astimezone(EASTERN))
            if entry_bar is None:
                print(f"  {trade['id']:>4}  {date!s:>10}  SKIPPED (no bar at live entry)")
                continue
            entry_quotes = nearest_snapshot(d["chains"], entry_bar.ts) or []
            vix_at_entry = await get_vix_at(conn, entry_time)

            selection = select_entry_candidate(
                quotes=entry_quotes,
                spot=entry_bar.close,
                direction=trade["direction"],
                vix=vix_at_entry,
                config=live_config,
                asset=args.asset,
                wing_widths=list(args.wing) if args.wing_provided else None,
            )
            winners = list(selection.per_width_bests)
            replay = selection.candidate
            bucket_label = str(list(selection.active_widths))
            live_s = (
                f"{int(trade['wing_width'])}W/"
                f"{float(trade['center_strike']):.0f}/"
                f"${float(trade['entry_price']):.2f}"
            )
            replay_s = (
                f"{replay.wing_width}W/{replay.center_strike:.0f}/${replay.cost:.2f}"
                if replay
                else "NO TRADE"
            )
            winners_s = ", ".join(
                f"{w.wing_width}W:{w.center_strike:.0f}@{w.cost:.2f}" for w in winners
            ) or "-"
            print(
                f"  {trade['id']:>4}  {date!s:>10}  "
                f"{entry_time.astimezone(EASTERN).strftime('%H:%M'):>8}  "
                f"{entry_bar.close:>8.2f}  {vix_at_entry:>5.1f}  "
                f"{live_s:>17}  {replay_s:>17}  {bucket_label:<14}  {winners_s}"
            )
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Single-config mode
# ---------------------------------------------------------------------------

async def run_single(args: argparse.Namespace) -> None:
    live_config = load_asset_config(args.asset)
    direction_arg = args.direction[0]
    wing_widths = args.wing
    rr_min = args.rr_min[0]
    morning_dd = args.morning_dd[0]
    late_morning_dd = args.late_morning_dd[0]
    afternoon_dd = args.afternoon_dd[0]
    dd_schedule = args.dd_schedule[0]
    profit_strategy = args.profit_strategy[0]
    method = args.method[0]
    max_cost_per_width = live_config.strategy.max_cost_per_width
    width_label = _live_width_label(
        wing_provided=args.wing_provided,
        method=method,
        config=live_config,
        wing_widths=wing_widths,
    )

    print(f"\n{'='*72}")
    print(f"  DB BACKTEST  |  {args.asset}  {direction_arg} butterfly")
    print(f"  Live config: {ASSET_CONFIG_PATHS[args.asset]}")
    print(
        f"  Widths: {width_label}  rr_min: {rr_min}  "
        f"DD: {morning_dd}/{late_morning_dd}/{afternoon_dd}"
    )
    print(f"  DD schedule: {_dd_schedule_label(dd_schedule)}")
    print(f"  Profit strategy: {profit_strategy}")
    print(f"  Method: {method}  abs_stop: {'ON' if args.use_abs_stop else 'OFF'}  "
          f"slippage: {args.slippage}  vix_max: {args.vix_max or 'none'}")
    print(f"{'='*72}\n")

    conn = await asyncpg.connect(resolve_db_dsn())
    try:
        dates = await discover_dates(conn, args.asset, args.start, args.end)

        if not dates:
            print("ERROR: No full trading days found in DB for the specified range.")
            return

        print(f"  {len(dates)} trading day(s): {dates[0]} → {dates[-1]}\n")

        engine = SimulationEngine()
        day_rows: list[dict] = []

        for date in dates:
            print(f"  Loading {date}...", end="", flush=True)
            d = await load_date_data(conn, date, args.asset)

            if d is None:
                print(" SKIPPED (no data)")
                continue

            if args.vix_max and d["vix"] > args.vix_max:
                print(f" SKIPPED (VIX {d['vix']:.1f} > {args.vix_max})")
                continue

            if direction_arg == "auto":
                direction = "CALL" if d["open_spot"] >= d["prev_close"] else "PUT"
            else:
                direction = direction_arg

            if args.gap_filter is not None:
                gap_pct = (d["open_spot"] - d["prev_close"]) / d["prev_close"]
                if gap_pct < args.gap_filter:
                    print(f" SKIPPED (gap {gap_pct:.3%} < {args.gap_filter:.3%})")
                    continue
                direction = "CALL"

            if args.strategy_f:
                gap_pct = (d["open_spot"] - d["prev_close"]) / d["prev_close"]
                regime = _regime_classifier.classify(d["day"].recent_closes, d["vix"])
                if gap_pct < 0.0025:
                    print(f" SKIPPED [F] gap {gap_pct:.3%} < 0.250%")
                    continue
                if regime != Regime.BULL:
                    print(f" SKIPPED [F] regime={regime.value}")
                    continue
                if d["vix"] >= d["vix_prev_close"]:
                    print(
                        f" SKIPPED [F] VIX not gap-down "
                        f"({d['vix']:.1f} >= prev {d['vix_prev_close']:.1f})"
                    )
                    continue
                direction = "CALL"

            if not args.gap_filter and not args.strategy_f:
                gap_regime_filter = GapRegimeFilter(
                    bull_call_bias=args.bull_call_bias,
                    min_gap_pct=args.min_gap_pct,
                )
                regime = _regime_classifier.classify(d["day"].recent_closes, d["vix"])
                override, skip_reason = gap_regime_filter.apply(
                    d["open_spot"],
                    d["prev_close"],
                    regime,
                )
                if skip_reason:
                    print(f" SKIPPED (gap_regime: {skip_reason})")
                    continue
            if override:
                direction = override

            entry_pst = args.entry_time[0]
            entry_et = _pst_to_et(entry_pst)
            entry_target = dt.datetime(
                date.year,
                date.month,
                date.day,
                entry_et.hour,
                entry_et.minute,
                tzinfo=EASTERN,
            )
            entry_bar = _find_entry_bar_at(
                d["bars"],
                entry_target,
                max_lag_seconds=None if args.allow_late_entry_fallback else 120,
            )
            if entry_bar is None:
                print(f" SKIPPED (no entry bar within 120s of {entry_et:%H:%M} ET)")
                continue
            entry_spot = entry_bar.close

            entry_quotes = nearest_snapshot(d["chains"], entry_bar.ts) or []
            selection = select_entry_candidate(
                quotes=entry_quotes,
                spot=entry_spot,
                direction=direction,
                vix=d["vix"],
                config=live_config,
                asset=args.asset,
                wing_widths=wing_widths if args.wing_provided else None,
            )
            chosen = selection.candidate

            if not chosen:
                print(" SKIPPED (no qualifying butterfly)")
                continue

            print(f" {chosen.wing_width}W {direction} center={chosen.center_strike:.0f}  "
                  f"R/R={chosen.reward_risk:.1f}  cost=${chosen.cost:.2f}")

            monitoring = await load_monitoring_chains(
                conn, date, args.asset,
                [chosen.lower_strike, chosen.center_strike, chosen.upper_strike],
                [chosen.direction],
            )
            full_chains = merge_chains(d["chains"], monitoring)

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
                max_cost_per_width=max_cost_per_width,
                max_loss_from_cost=live_config.profit_management.max_loss_from_cost,
                use_absolute_loss_stop=args.use_abs_stop,
                drawdown_schedule=dd_schedule,
                profit_management_strategy=profit_strategy,
                profitprotector=live_config.profit_management.profitprotector,
            )

            restore = _patch_chain_cache(full_chains, date)
            result = engine.simulate_day_from_entry(
                d["day"],
                params,
                entry_candidate=chosen,
                entry_price=chosen.cost + args.slippage,
                entry_time=entry_bar.ts,
            )
            restore()

            synth_result = None
            if args.compare_synthetic:
                restore_synth = _force_synthetic_for_date(date)
                synth_result = engine.simulate_day(d["day"], params)
                restore_synth()

            same_entry_result = None
            if args.compare_synthetic_same_entry and result.traded:
                restore_se = _force_synthetic_for_date(date)
                same_entry_result = engine.simulate_day_from_entry(
                    d["day"], params,
                    entry_candidate=chosen,
                    entry_price=result.entry_price,
                    entry_time=result.entry_time,
                )
                restore_se()

            # Drop heavy chain/bar data before storing — only keep scalars needed for output
            d_slim = {k: d[k] for k in ("date", "vix", "entry_spot", "prev_close")}
            day_rows.append(
                {
                    "data": d_slim,
                    "chosen": chosen,
                    "result": result,
                    "synth_result": synth_result,
                    "same_entry_result": same_entry_result,
                }
            )

    finally:
        await conn.close()

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
    print("  Exit reasons: "
          + "  ".join(f"{k}={v}" for k, v in sorted(exit_counts.items())))
    print(f"{'='*90}")

    _print_pnl_histogram(pnls_ct)

    if args.html_report:
        _write_single_html_report(
            path=args.html_report,
            asset=args.asset,
            direction=direction,
            day_rows=day_rows,
            exit_counts=exit_counts,
            pnls_ct=pnls_ct,
        )
        print(f"\n  HTML report written to: {args.html_report}\n")

    if args.thinkback:
        print_thinkback_checklist(day_rows, args.asset)

    if args.compare_synthetic:
        _print_comparison_table(day_rows)

    if args.compare_synthetic_same_entry:
        _print_same_entry_comparison_table(day_rows)


# ---------------------------------------------------------------------------
# Sweep mode
# ---------------------------------------------------------------------------

async def run_sweep(args: argparse.Namespace) -> None:
    live_config = load_asset_config(args.asset)
    max_cost_per_width = live_config.strategy.max_cost_per_width
    wing_values = args.wing if args.wing_provided else [None]

    # Build combo grid
    param_grid = list(itertools.product(
        wing_values,
        args.direction,
        args.rr_min,
        args.morning_dd,
        args.late_morning_dd,
        args.afternoon_dd,
        args.dd_schedule,
        args.profit_strategy,
        args.method,
        args.entry_time,
    ))
    total_combos = len(param_grid)

    entry_strs = [f"{t.hour:02d}:{t.minute:02d}" for t in args.entry_time]
    print(f"\n{'='*72}")
    print(f"  PARAMETER SWEEP  |  {args.asset}  |  {total_combos} combos")
    print(f"  Live config: {ASSET_CONFIG_PATHS[args.asset]}")
    width_label = _live_width_label(
        wing_provided=args.wing_provided,
        method=args.method[0],
        config=live_config,
        wing_widths=args.wing,
    )
    print(f"  Wings: {width_label}  Directions: {args.direction}  rr_min: {args.rr_min}")
    print(f"  Methods: {args.method}  Entry times (PST): {entry_strs}")
    print(f"  morning_dd: {args.morning_dd}  late_morning_dd: {args.late_morning_dd}")
    print(
        f"  afternoon_dd: {args.afternoon_dd}  "
        f"abs_stop: {'ON' if args.use_abs_stop else 'OFF'}  "
        f"slippage: {args.slippage}"
    )
    print(f"  dd_schedules: {[_dd_schedule_label(s) for s in args.dd_schedule]}")
    print(f"  profit_strategies: {args.profit_strategy}")
    print(f"{'='*72}\n")

    conn = await asyncpg.connect(resolve_db_dsn())
    try:
        dates = await discover_dates(conn, args.asset, args.start, args.end)

        if not dates:
            print("ERROR: No full trading days found in DB for the specified range.")
            return

        print(f"  {len(dates)} trading day(s): {dates[0]} → {dates[-1]}")
        print(f"  Running {total_combos} combos (loading one day at a time)...\n")

        engine = SimulationEngine()
        combo_day_results: list[list[tuple[dt.date, object]]] = [[] for _ in param_grid]
        usable_dates: list[dt.date] = []

        for date in dates:
            d = await load_date_data(conn, date, args.asset)

            if d is None:
                print(f"    {date} SKIPPED (no data)")
                continue
            if args.vix_max and d["vix"] > args.vix_max:
                print(f"    {date} SKIPPED (VIX {d['vix']:.1f} > {args.vix_max})")
                continue
            print(f"    {date}  VIX={d['vix']:.1f}  spot={d['entry_spot']:.0f}")
            usable_dates.append(date)

            # Phase 1: run all combo selections using entry-window chains
            per_combo: list[tuple] = []
            needed_strikes: set[float] = set()
            needed_types: set[str] = set()

            for (
                wing,
                direction,
                rr_min,
                morning_dd,
                late_morning_dd,
                afternoon_dd,
                dd_schedule,
                profit_strategy,
                method,
                entry_pst,
            ) in param_grid:
                entry_et = _pst_to_et(entry_pst)
                entry_target = dt.datetime(date.year, date.month, date.day,
                                           entry_et.hour, entry_et.minute, tzinfo=EASTERN)
                entry_bar_combo = _find_entry_bar_at(
                    d["bars"],
                    entry_target,
                    max_lag_seconds=None if args.allow_late_entry_fallback else 120,
                )
                if entry_bar_combo is None:
                    per_combo.append((None, None, None, None))
                    continue

                entry_quotes = nearest_snapshot(d["chains"], entry_bar_combo.ts) or []
                entry_spot = entry_bar_combo.close
                resolved_direction = (
                    ("CALL" if d["open_spot"] >= d["prev_close"] else "PUT")
                    if direction == "auto"
                    else direction
                )

                if args.gap_filter is not None:
                    gap_pct = (d["open_spot"] - d["prev_close"]) / d["prev_close"]
                    if gap_pct < args.gap_filter:
                        per_combo.append((None, None, None, None))
                        continue
                    resolved_direction = "CALL"

                if args.strategy_f:
                    gap_pct = (d["open_spot"] - d["prev_close"]) / d["prev_close"]
                    regime = _regime_classifier.classify(d["day"].recent_closes, d["vix"])
                    if (gap_pct < 0.0025
                            or regime != Regime.BULL
                            or d["vix"] >= d["vix_prev_close"]):
                        per_combo.append((None, None, None, None))
                        continue
                    resolved_direction = "CALL"

                if not args.gap_filter and not args.strategy_f:
                    gap_regime_filter = GapRegimeFilter(
                        bull_call_bias=args.bull_call_bias,
                        min_gap_pct=args.min_gap_pct,
                    )
                    regime = _regime_classifier.classify(d["day"].recent_closes, d["vix"])
                    override, skip_reason = gap_regime_filter.apply(
                        d["open_spot"],
                        d["prev_close"],
                        regime,
                    )
                    if skip_reason:
                        per_combo.append((None, None, None, None))
                        continue
                    if override:
                        resolved_direction = override

                selection = select_entry_candidate(
                    quotes=entry_quotes,
                    spot=entry_spot,
                    direction=resolved_direction,
                    vix=d["vix"],
                    config=live_config,
                    asset=args.asset,
                    wing_widths=[wing] if wing is not None else None,
                )
                chosen = selection.candidate
                if chosen is not None:
                    needed_strikes |= {
                        chosen.lower_strike,
                        chosen.center_strike,
                        chosen.upper_strike,
                    }
                    needed_types.add(chosen.direction)
                    et_end_total = entry_et.hour * 60 + entry_et.minute + 10
                    entry_et_end = dt.time(et_end_total // 60, et_end_total % 60)
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
                        max_cost_per_width=max_cost_per_width,
                        max_loss_from_cost=live_config.profit_management.max_loss_from_cost,
                        use_absolute_loss_stop=args.use_abs_stop,
                        entry_start=entry_et,
                        entry_end=entry_et_end,
                        drawdown_schedule=dd_schedule,
                        profit_management_strategy=profit_strategy,
                        profitprotector=live_config.profit_management.profitprotector,
                    )
                else:
                    sim_params = None
                per_combo.append((resolved_direction, chosen, sim_params, entry_bar_combo.ts))

            # Phase 2: load monitoring chains for all needed strikes, patch once
            if needed_strikes:
                monitoring = await load_monitoring_chains(
                    conn, date, args.asset, list(needed_strikes), list(needed_types)
                )
                full_chains = merge_chains(d["chains"], monitoring)
            else:
                full_chains = d["chains"]

            restore = _patch_chain_cache(full_chains, date)
            for ci, (resolved_direction, chosen, sim_params, entry_time) in enumerate(per_combo):
                if chosen is None or sim_params is None or entry_time is None:
                    combo_day_results[ci].append((date, None))
                    continue
                result = engine.simulate_day_from_entry(
                    d["day"],
                    sim_params,
                    entry_candidate=chosen,
                    entry_price=chosen.cost + args.slippage,
                    entry_time=entry_time,
                )
                combo_day_results[ci].append((date, result))
            restore()

    finally:
        await conn.close()

    if not usable_dates:
        print("\nNo usable dates loaded.")
        return

    print(f"\n  Summarizing {total_combos} combos across {len(usable_dates)} dates...\n")

    sweep_results: list[dict] = []
    for i, (
        wing,
        direction,
        rr_min,
        morning_dd,
        late_morning_dd,
        afternoon_dd,
        dd_schedule,
        profit_strategy,
        method,
        entry_pst,
    ) in enumerate(param_grid, 1):
        entry_pst_str = f"{entry_pst.hour:02d}:{entry_pst.minute:02d}"
        dd_schedule_label = _dd_schedule_label(dd_schedule)
        wing_label = "live" if wing is None else wing
        combo_label = dict(
            wing_width=wing_label,
            direction=direction,
            rr_min=rr_min,
            morning_dd=morning_dd,
            late_morning_dd=late_morning_dd,
            afternoon_dd=afternoon_dd,
            dd_schedule=dd_schedule_label,
            profit_strategy=profit_strategy,
            method=method,
            entry_time_pst=entry_pst_str,
        )
        row = _summarize_combo(combo_label, combo_day_results[i - 1])
        sweep_results.append(row)

        if i % 10 == 0 or i == total_combos:
            print(f"  [{i:>{len(str(total_combos))}}/{total_combos}]  "
                  f"{wing_label}W {direction} entry={entry_pst_str}PST "
                  f"method={method} rr={rr_min} "
                  f"profit={profit_strategy} "
                  f"dd={morning_dd}/{late_morning_dd}/{afternoon_dd}  "
                  f"schedule={dd_schedule_label}  "
                  f"→ trades={row['trade_count']}  sharpe={row['sharpe']:.3f}  "
                  f"win={row['win_rate']*100:.0f}%")

    # Sort by Sharpe; push zero-trade combos to bottom
    sweep_results.sort(
        key=lambda r: (r["trade_count"] > 0, r["sharpe"]),
        reverse=True,
    )

    # ── Console table ────────────────────────────────────────────────────────
    top_n = min(args.top, len(sweep_results))
    print(f"\n{'='*127}")
    print(f"  TOP {top_n} COMBOS BY SHARPE  (of {total_combos})")
    print(f"{'='*127}")
    print(
        f"  {'W':>3}  {'Dir':>4}  {'Method':<11}  {'Profit':<16}  "
        f"{'Entry':>5}  {'RR':>5}  {'Morn':>5}  {'LtMrn':>6}  {'Aftn':>5}  "
        f"{'Trd':>4}  {'Win%':>5}  {'TotPnL':>8}  {'AvgPnL':>8}  "
        f"{'Sharpe':>7}  {'PF':>5}  {'MaxDD':>7}  {'MaxCL':>6}"
    )
    print("  " + "-" * 125)

    for row in sweep_results[:top_n]:
        print(f"  {row['wing_width']:>3}  {row['direction']:>4}  "
              f"{row['method']:<11}  "
              f"{row['profit_strategy']:<16}  "
              f"{row['entry_time_pst']:>5}  "
              f"{row['rr_min']:>5.1f}  {row['morning_dd']:>5.2f}  "
              f"{row['late_morning_dd']:>6.2f}  {row['afternoon_dd']:>5.2f}  "
              f"{row['trade_count']:>4}  {row['win_rate']*100:>4.0f}%  "
              f"${row['total_pnl']*100:>+7.2f}  ${row['avg_pnl']*100:>+7.2f}  "
              f"{row['sharpe']:>7.3f}  {row['profit_factor']:>5.3f}  "
              f"${row['max_drawdown']*100:>6.2f}  {row['max_consec_losses']:>6}")

    print(f"{'='*127}\n")

    # ── CSV output ────────────────────────────────────────────────────────────
    ts_str = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    start_str = (args.start or dates[0]).strftime("%Y%m%d")
    end_str = (args.end or dates[-1]).strftime("%Y%m%d")
    results_dir = Path("data/results")
    results_dir.mkdir(exist_ok=True)
    csv_path = args.csv or results_dir / f"sweep_{args.asset}_{start_str}_{end_str}_{ts_str}.csv"

    fieldnames = [
        "wing_width", "direction", "method", "profit_strategy", "entry_time_pst", "rr_min",
        "morning_dd", "late_morning_dd", "afternoon_dd",
        "dd_schedule",
        "trade_count", "win_rate", "total_pnl", "avg_pnl",
        "sharpe", "max_drawdown", "profit_factor", "max_consec_losses",
        "exit_morning_dd", "exit_late_morning_dd", "exit_afternoon_dd",
        "exit_drawdown", "exit_eod", "exit_expired", "exit_abs_stop",
        "exit_profit_floor", "exit_breakeven_floor",
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
    if args.live_pinned_replay:
        await run_live_pinned_replay(args)
    elif args.selection_parity_report:
        await run_selection_parity_report(args)
    elif args.sweep:
        await run_sweep(args)
    else:
        await run_single(args)


if __name__ == "__main__":
    asyncio.run(main())
