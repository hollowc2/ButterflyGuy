"""Drawdown parameter sweep across all available full trading days.

Sweeps all valid combinations of (morning, late_morning, afternoon) drawdown
thresholds with abs_stop=OFF. Loads each day's data once, then runs all
parameter combos against it. Prints results sorted by total PnL.

Valid combos: morning >= late_morning >= afternoon (each from a fixed grid).

Usage:
    python -m butterfly_guy.scripts.run_dd_sweep
"""

from __future__ import annotations

import asyncio
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
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.config import StrategySettings
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder, vix_target_center
from butterfly_guy.strategy.butterfly_selector import ButterflySelector

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_dd_sweep")

EASTERN = ZoneInfo("America/New_York")
DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

ASSET = "SPX"
WING_WIDTHS = [10, 20, 30]
DIRECTION = "PUT"

# Grid values for each threshold
DD_VALUES = [0.40, 0.50, 0.60, 0.75, 0.90, 1.0]

# Build all valid (morning, late_morning, afternoon) combos: a >= b >= c
SWEEP_CONFIGS = [
    (a, b, c)
    for a, b, c in itertools.product(DD_VALUES, repeat=3)
    if a >= b >= c
]


async def get_all_dates(conn: asyncpg.Connection, asset: str = ASSET) -> list[dt.date]:
    rows = await conn.fetch(
        """
        SELECT snapshot_time::date AS trade_date, COUNT(DISTINCT snapshot_time) AS snap_count
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = snapshot_time::date
        GROUP BY trade_date
        HAVING COUNT(DISTINCT snapshot_time) >= 50
        ORDER BY trade_date
        """,
        asset,
    )
    return [r["trade_date"] for r in rows]


async def load_chains_from_db(
    conn: asyncpg.Connection, date: dt.date, asset: str = ASSET
) -> dict[dt.datetime, list[OptionQuote]]:
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $2
          AND expiration = $1
          AND snapshot_time::date = $1
        ORDER BY snapshot_time, strike, option_type
        """,
        date, asset,
    )
    chains: dict[dt.datetime, list[OptionQuote]] = defaultdict(list)
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        chains[ts].append(
            OptionQuote(
                symbol=r["symbol"] or f"DB_{r['option_type'][0]}{int(r['strike'])}",
                underlying=asset,
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


async def load_bars_from_db(conn: asyncpg.Connection, date: dt.date, asset: str = ASSET) -> list[MinuteBar]:
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (snapshot_time)
            snapshot_time, spot_price
        FROM option_chain_snapshots
        WHERE underlying = $2
          AND snapshot_time::date = $1
          AND spot_price IS NOT NULL
          AND spot_price > 0
        ORDER BY snapshot_time
        """,
        date, asset,
    )
    bars: list[MinuteBar] = []
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        price = float(r["spot_price"])
        bars.append(MinuteBar(ts=ts, open=price, high=price, low=price, close=price, volume=0))
    return bars


async def get_prev_close(conn: asyncpg.Connection, date: dt.date, asset: str = ASSET) -> float:
    row = await conn.fetchval(
        "SELECT price FROM spot_prices WHERE underlying = $2 AND ts::date < $1 ORDER BY ts DESC LIMIT 1",
        date, asset,
    )
    if row:
        return float(row)
    start = date - dt.timedelta(days=7)
    hist = yf.Ticker("^GSPC").history(start=start, end=date, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[-1])
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


def select_live_width(
    quotes: list[OptionQuote],
    spot: float,
    direction: str,
    vix: float,
    wing_widths: list[int],
    rr_min: float = 8.0,
    rr_target: float = 10.0,
    center_tolerance: float = 15.0,
) -> ButterflyCandidate | None:
    settings = StrategySettings(wing_widths=wing_widths, rr_min=rr_min, spot_range=100)
    builder = ButterflyBuilder(settings)
    selector = ButterflySelector(settings)
    all_candidates = builder.build_candidates(quotes, spot, direction)
    per_width_bests: list[ButterflyCandidate] = []
    for width in wing_widths:
        target_center = vix_target_center(vix=vix, spot=spot, direction=direction, wing_width=width)
        width_candidates = [c for c in all_candidates if c.wing_width == width]
        best = selector.select_best(width_candidates, target_center=target_center, center_tolerance=center_tolerance)
        if best:
            per_width_bests.append(best)
    if not per_width_bests:
        return None
    return min(per_width_bests, key=lambda c: abs(c.reward_risk - rr_target))


def nearest_snapshot(
    chains: dict[dt.datetime, list[OptionQuote]], bar_ts: dt.datetime
) -> list[OptionQuote] | None:
    candidates = [ts for ts in chains if ts <= bar_ts]
    if not candidates:
        return None
    return chains[max(candidates)]


async def load_day(conn: asyncpg.Connection, date: dt.date) -> dict | None:
    """Load all data for a day. Returns None if insufficient."""
    chains = await load_chains_from_db(conn, date)
    bars = await load_bars_from_db(conn, date)
    if not chains or not bars:
        return None

    prev_close = await get_prev_close(conn, date)
    entry_bar = next(
        (b for b in bars if b.ts.astimezone(EASTERN).time() >= dt.time(10, 0)),
        bars[0],
    )
    entry_spot = entry_bar.close
    vix = await get_vix_at(conn, entry_bar.ts)

    entry_quotes = nearest_snapshot(chains, entry_bar.ts) or []
    chosen = select_live_width(quotes=entry_quotes, spot=entry_spot, direction=DIRECTION, vix=vix, wing_widths=WING_WIDTHS)
    if not chosen:
        return None

    return dict(
        date=date,
        vix=vix,
        entry_spot=entry_spot,
        wing_width=chosen.wing_width,
        center_strike=chosen.center_strike,
        chains=chains,
        bars=bars,
        prev_close=prev_close,
    )


async def main() -> None:
    n_combos = len(SWEEP_CONFIGS)
    print(f"\n{'='*80}")
    print(f"  DRAWDOWN PARAMETER SWEEP  |  {DIRECTION} butterflies  |  abs_stop=OFF")
    print(f"  Grid: {[int(v*100) for v in DD_VALUES]}%  →  {n_combos} valid (morning >= late >= afternoon) combos")
    print(f"{'='*80}\n")

    conn = await asyncpg.connect(DB_DSN)
    try:
        dates = await get_all_dates(conn)
    finally:
        await conn.close()

    if not dates:
        print("ERROR: No full trading days found in DB.")
        return

    print(f"  Loading {len(dates)} day(s): {dates[0]} → {dates[-1]}\n")

    engine = SimulationEngine()
    loaded_days: list[dict] = []

    for date in dates:
        conn = await asyncpg.connect(DB_DSN)
        try:
            day_data = await load_day(conn, date)
        finally:
            await conn.close()

        if day_data is None:
            print(f"  {date} — SKIPPED")
            continue
        loaded_days.append(day_data)
        print(f"  {date}  VIX={day_data['vix']:.1f}  SPX={day_data['entry_spot']:.0f}  "
              f"{day_data['wing_width']}W  center={day_data['center_strike']:.0f}")

    if not loaded_days:
        print("\nNo tradeable days.")
        return

    print(f"\n  Running {n_combos} configs × {len(loaded_days)} days = "
          f"{n_combos * len(loaded_days)} simulations...\n")

    # Accumulate results per config: list of pnl_per_contract values
    sweep_results: dict[tuple, list[float]] = {cfg: [] for cfg in SWEEP_CONFIGS}

    import butterfly_guy.backtest.chain_cache as _cc
    _original_load = _cc.load_chain_day

    for day_data in loaded_days:
        date = day_data["date"]
        chains = day_data["chains"]
        wing_width = day_data["wing_width"]

        # Patch chain cache for this day
        _cc._DB_CHAINS = chains  # type: ignore[attr-defined]

        def _patched_load(d, cache_dir=None, _date=date):
            if d == _date:
                return _cc._DB_CHAINS  # type: ignore[attr-defined]
            return _original_load(d, cache_dir) if cache_dir else _original_load(d)

        _cc.load_chain_day = _patched_load  # type: ignore[assignment]

        day = DayData(
            date=date,
            bars=day_data["bars"],
            vix=day_data["vix"],
            prev_close=day_data["prev_close"],
        )

        for (morning, late_morning, afternoon) in SWEEP_CONFIGS:
            params = SimulationParams(
                wing_width=wing_width,
                direction_override=DIRECTION,
                rr_min=8.0,
                morning_drawdown=morning,
                late_morning_drawdown=late_morning,
                afternoon_drawdown=afternoon,
                slippage=0.05,
                use_vix_center=True,
                use_absolute_loss_stop=False,
            )
            result = engine.simulate_day(day, params)
            if result.traded:
                sweep_results[(morning, late_morning, afternoon)].append(result.pnl * 100)

    _cc.load_chain_day = _original_load  # type: ignore[assignment]

    # Build summary rows
    rows = []
    n_days = len(loaded_days)
    for cfg, pnls in sweep_results.items():
        morning, late_morning, afternoon = cfg
        n_traded = len(pnls)
        if n_traded == 0:
            continue
        winners = [p for p in pnls if p > 0]
        total = sum(pnls)
        avg = total / n_traded
        win_pct = len(winners) / n_traded * 100
        best = max(pnls)
        worst = min(pnls)
        rows.append((cfg, n_traded, len(winners), win_pct, total, avg, best, worst))

    # Sort by total PnL descending
    rows.sort(key=lambda r: r[4], reverse=True)

    print(f"\n{'='*95}")
    print(f"  SWEEP RESULTS — sorted by total PnL/ct  ({n_days} days, abs_stop=OFF)")
    print(f"{'='*95}")
    print(f"  {'Morn':>5}  {'Late':>5}  {'Aftn':>5}  {'Trades':>6}  {'Win%':>5}  "
          f"{'Total PnL/ct':>13}  {'Avg PnL/ct':>11}  {'Best':>8}  {'Worst':>8}")
    print("  " + "-" * 83)

    for cfg, n_traded, n_win, win_pct, total, avg, best, worst in rows:
        m, lm, a = cfg
        marker = ""
        if m == 0.75 and lm == 0.65 and a == 0.50:
            marker = "  ← config C"
        elif m == 0.50 and lm == 0.40 and a == 0.30:
            marker = "  ← defaults"
        print(f"  {m*100:>4.0f}%  {lm*100:>4.0f}%  {a*100:>4.0f}%  {n_traded:>6}  {win_pct:>4.0f}%  "
              f"  ${total:>+10.2f}  ${avg:>+9.2f}  ${best:>+6.2f}  ${worst:>+6.2f}{marker}")

    print(f"{'='*95}\n")

    # Top 10
    print(f"  TOP 10 by Total PnL/ct:")
    for i, (cfg, n_traded, n_win, win_pct, total, avg, best, worst) in enumerate(rows[:10], 1):
        m, lm, a = cfg
        print(f"  #{i:>2}  {m*100:.0f}% / {lm*100:.0f}% / {a*100:.0f}%  →  "
              f"total=${total:>+8.2f}  win={win_pct:.0f}%  avg=${avg:>+7.2f}  worst=${worst:>+6.2f}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
