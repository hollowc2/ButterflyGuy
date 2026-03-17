"""Backtest using real collected option chain data from TimescaleDB.

Loads all chain snapshots for a given date directly from the database,
reconstructs price bars from spot_price, and runs the simulation engine
with real quotes instead of synthetic ones.

Usage:
    python -m butterfly_guy.scripts.run_db_backtest
"""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
import yfinance as yf

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.data.schemas import OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    VIX_SIGMA_BY_WIDTH,
    vix_expected_move,
    vix_target_center,
)

setup_logging(log_level="INFO", json_output=False)
log = get_logger("run_db_backtest")

EASTERN = ZoneInfo("America/New_York")

DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

# --------------------------------------------------------------------------- #
#  Config — edit these to change the backtest                                 #
# --------------------------------------------------------------------------- #
TARGET_DATE = dt.date(2026, 3, 16)

WING_WIDTHS = [10, 20, 30]
DIRECTION = "CALL"   # forced bullish

BASE_PARAMS = dict(
    direction_override=DIRECTION,
    rr_min=8.0,
    morning_drawdown=0.50,
    late_morning_drawdown=0.40,
    afternoon_drawdown=0.30,
    slippage=0.05,
    use_vix_center=True,  # center anchored to VIX; sigma auto-selected per width
)
# --------------------------------------------------------------------------- #


async def load_chains_from_db(
    conn: asyncpg.Connection,
    date: dt.date,
) -> dict[dt.datetime, list[OptionQuote]]:
    """Load all option chain snapshots for `date` from the DB.

    Returns dict: UTC snapshot_time -> list[OptionQuote]
    """
    rows = await conn.fetch(
        """
        SELECT snapshot_time, strike, option_type, bid, ask, mark, last,
               volume, open_interest, iv, delta, gamma, theta, vega, symbol, spot_price
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND expiration = $1
          AND snapshot_time::date = $1
        ORDER BY snapshot_time, strike, option_type
        """,
        date,
    )

    chains: dict[dt.datetime, list[OptionQuote]] = defaultdict(list)
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        chains[ts].append(
            OptionQuote(
                symbol=r["symbol"] or f"DB_{r['option_type'][0]}{int(r['strike'])}",
                underlying="SPX",
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
) -> list[MinuteBar]:
    """Derive price bars from distinct snapshot spot_prices for `date`."""
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (snapshot_time)
            snapshot_time,
            spot_price
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND snapshot_time::date = $1
          AND spot_price IS NOT NULL
          AND spot_price > 0
        ORDER BY snapshot_time
        """,
        date,
    )

    bars: list[MinuteBar] = []
    for r in rows:
        ts = r["snapshot_time"]
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=dt.timezone.utc)
        price = float(r["spot_price"])
        bars.append(MinuteBar(ts=ts, open=price, high=price, low=price, close=price, volume=0))

    return bars


def get_prev_close(date: dt.date) -> float:
    start = date - dt.timedelta(days=7)
    hist = yf.Ticker("^GSPC").history(start=start, end=date, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[-1])
    return 5500.0


def get_vix(date: dt.date) -> float:
    end = date + dt.timedelta(days=1)
    hist = yf.Ticker("^VIX").history(start=date, end=end, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[0])
    return 18.0


def nearest_snapshot(
    chains: dict[dt.datetime, list[OptionQuote]],
    bar_ts: dt.datetime,
) -> list[OptionQuote] | None:
    candidates = [ts for ts in chains if ts <= bar_ts]
    if not candidates:
        return None
    return chains[max(candidates)]


async def main() -> None:
    print(f"\n{'='*60}")
    print(f"  DB BACKTEST — {TARGET_DATE}  |  30-wide CALL butterfly (bullish)")
    print(f"{'='*60}\n")

    conn = await asyncpg.connect(DB_DSN)
    try:
        print("Loading chain snapshots from DB...")
        chains = await load_chains_from_db(conn, TARGET_DATE)
        bars = await load_bars_from_db(conn, TARGET_DATE)
    finally:
        await conn.close()

    if not chains:
        print("ERROR: No chain data found in DB for this date.")
        return
    if not bars:
        print("ERROR: No spot_price data found for this date.")
        return

    print(f"  Snapshots loaded : {len(chains)}")
    print(f"  Price bars       : {len(bars)}")
    print(f"  Bar time range   : {bars[0].ts.astimezone(EASTERN).strftime('%H:%M')} – "
          f"{bars[-1].ts.astimezone(EASTERN).strftime('%H:%M')} ET")
    spot_prices = [b.close for b in bars]
    print(f"  SPX range        : {min(spot_prices):.2f} – {max(spot_prices):.2f}")

    # Fetch prev_close and VIX from yfinance
    print("\nFetching VIX + prev_close from yfinance...")
    prev_close = await asyncio.to_thread(get_prev_close, TARGET_DATE)
    vix = await asyncio.to_thread(get_vix, TARGET_DATE)
    import math
    entry_spot = bars[0].close  # open bar; actual entry uses 10am bar
    expected_move = vix_expected_move(vix, entry_spot)
    print(f"  Prev close       : {prev_close:.2f}")
    print(f"  VIX              : {vix:.2f}")
    print(f"  Open gap         : {entry_spot - prev_close:+.2f} "
          f"({(entry_spot/prev_close - 1)*100:+.2f}%)")
    print(f"\n  Expected daily 1σ move : ±{expected_move:.0f} pts  (SPX × VIX/100 / √252)")
    print(f"  VIX center targets per width:")
    for w in WING_WIDTHS:
        sigma = VIX_SIGMA_BY_WIDTH.get(w, 0.5)
        tc = vix_target_center(vix, entry_spot, DIRECTION, wing_width=w)
        print(f"    {w}-wide → {sigma}σ → center at {tc:.0f}  ({tc - entry_spot:+.0f} pts OTM)")
    print()

    day = DayData(date=TARGET_DATE, bars=bars, vix=vix, prev_close=prev_close)

    # ---------- Patch chain cache to serve DB data -------------------------- #
    import butterfly_guy.backtest.chain_cache as _cc
    _cc._DB_CHAINS = chains  # type: ignore[attr-defined]
    _original_load = _cc.load_chain_day

    def _patched_load(date, cache_dir=None):
        if date == TARGET_DATE:
            return _cc._DB_CHAINS  # type: ignore[attr-defined]
        return _original_load(date, cache_dir) if cache_dir else _original_load(date)

    _cc.load_chain_day = _patched_load  # type: ignore[assignment]
    # ------------------------------------------------------------------------ #

    engine = SimulationEngine()
    all_results = []

    for width in WING_WIDTHS:
        params = SimulationParams(wing_width=width, **BASE_PARAMS)
        result = engine.simulate_day(day, params)
        all_results.append((width, result))

    # Restore chain cache
    _cc.load_chain_day = _original_load  # type: ignore[assignment]

    # ---------- Summary table ----------------------------------------------- #
    print(f"\n{'='*72}")
    print(f"  RESULTS SUMMARY — {TARGET_DATE}  |  {DIRECTION} butterfly")
    print(f"{'='*72}")
    print(f"  {'Width':>5}  {'Structure':^20}  {'Entry':>6}  {'Peak':>6}  "
          f"{'Exit':>6}  {'Reason':<22}  {'PnL/ct':>8}")
    print(f"  {'-'*5}  {'-'*20}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*22}  {'-'*8}")
    for width, r in all_results:
        if not r.traded:
            print(f"  {width:>5}  {'NO TRADE':^20}")
            continue
        struct = f"{r.center_strike-width:.0f}/{r.center_strike:.0f}/{r.center_strike+width:.0f}"
        pnl_ct = r.pnl * 100
        print(f"  {width:>5}  {struct:^20}  ${r.entry_price:>5.2f}  ${r.peak_value:>5.2f}  "
              f"${r.exit_price:>5.2f}  {r.exit_reason:<22}  ${pnl_ct:>+7.2f}")
    print(f"{'='*72}\n")

    # ---------- VIX center guide --------------------------------------------- #
    print(f"  VIX → center targets across widths (at SPX ~{entry_spot:.0f}, {DIRECTION}):")
    print(f"  {'VIX':>5}  {'Exp.move':>9}  {'10w(0.25σ)':>11}  {'20w(0.50σ)':>11}  {'30w(0.75σ)':>11}")
    print(f"  {'-----':>5}  {'-'*9}  {'-'*11}  {'-'*11}  {'-'*11}")
    for test_vix in [12, 15, 18, 20, 23.5, 25, 30, 35, 45]:
        em = vix_expected_move(test_vix, entry_spot)
        c10 = vix_target_center(test_vix, entry_spot, DIRECTION, wing_width=10)
        c20 = vix_target_center(test_vix, entry_spot, DIRECTION, wing_width=20)
        c30 = vix_target_center(test_vix, entry_spot, DIRECTION, wing_width=30)
        marker = "← today" if abs(test_vix - vix) < 0.6 else ""
        print(f"  {test_vix:>5.1f}  {em:>8.0f}pts"
              f"  {c10:>7.0f}(+{c10-entry_spot:.0f})"
              f"  {c20:>7.0f}(+{c20-entry_spot:.0f})"
              f"  {c30:>7.0f}(+{c30-entry_spot:.0f})  {marker}")
    print()

    # ---------- Detail per width -------------------------------------------- #
    for width, result in all_results:
        print(f"\n{'─'*60}")
        print(f"  {width}-WIDE CALL FLY")
        print(f"{'─'*60}")

        if not result.traded:
            print("  NO TRADE — no qualifying butterfly found in entry window.")
            continue

        entry_et = result.entry_time.astimezone(EASTERN) if result.entry_time else None
        exit_et = result.exit_time.astimezone(EASTERN) if result.exit_time else None

        lower_be = result.center_strike - width + result.entry_price
        upper_be = result.center_strike + width - result.entry_price
        rr = (width - result.entry_price) / result.entry_price

        print(f"  Structure  : {result.center_strike-width:.0f} / {result.center_strike:.0f} / "
              f"{result.center_strike+width:.0f}")
        print(f"  Entry      : {entry_et.strftime('%H:%M:%S') if entry_et else 'N/A'} ET  "
              f"@ ${result.entry_price:.2f}")
        print(f"  Max profit : ${width - result.entry_price:.2f}  (R/R {rr:.1f}x)")
        print(f"  Breakevens : {lower_be:.2f} / {upper_be:.2f}")
        print(f"  Peak value : ${result.peak_value:.2f}")
        print(f"  Exit       : {exit_et.strftime('%H:%M:%S') if exit_et else 'N/A'} ET  "
              f"@ ${result.exit_price:.2f}  [{result.exit_reason}]")
        print(f"  PnL        : ${result.pnl:+.2f} / spread   "
              f"${result.pnl*100:+.2f} / contract")

        # Entry chain around the fly strikes
        entry_quotes = nearest_snapshot(chains, result.entry_time) if result.entry_time else []
        if entry_quotes:
            center = result.center_strike
            relevant = sorted(
                [q for q in entry_quotes
                 if q.option_type == "CALL"
                 and center - width - 5 <= q.strike <= center + width + 5],
                key=lambda q: q.strike,
            )
            print(f"\n  {'Strike':>8}  {'Bid':>6}  {'Ask':>6}  {'Mark':>6}  {'Delta':>6}  Role")
            print(f"  {'-'*8}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*6}  ----")
            for q in relevant:
                role = ""
                if q.strike == center - width:
                    role = "← buy (lower)"
                elif q.strike == center:
                    role = "← sell x2 (center)"
                elif q.strike == center + width:
                    role = "← buy (upper)"
                print(f"  {q.strike:>8.0f}  {q.bid:>6.2f}  {q.ask:>6.2f}  {q.mark:>6.2f}  "
                      f"{q.delta:>6.3f}  {role}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
