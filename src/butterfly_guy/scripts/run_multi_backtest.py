"""Multi-config, multi-day DB backtest.

Runs four parameter configurations across all available full trading days
in the database and prints a consolidated comparison table.

Configs:
  A  Defaults          morning=50% late=40% afternoon=30% abs_stop=ON
  B  No abs stop       morning=50% late=40% afternoon=30% abs_stop=OFF
  C  Wider DD          morning=75% late=65% afternoon=50% abs_stop=OFF
  D  Hold to expiry    no exits — butterfly runs until close

Usage:
    python -m butterfly_guy.scripts.run_multi_backtest
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
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import (
    VIX_SIGMA_BY_WIDTH,
    ButterflyBuilder,
    vix_expected_move,
    vix_target_center,
)
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.core.config import StrategySettings

setup_logging(log_level="WARNING", json_output=False)
log = get_logger("run_multi_backtest")

EASTERN = ZoneInfo("America/New_York")
DB_DSN = "postgresql://butterfly:butterfly_dev@localhost:5432/butterfly_guy"

WING_WIDTHS = [10, 20, 30]
DIRECTION = "PUT"

# --------------------------------------------------------------------------- #
#  Four configurations to compare                                              #
# --------------------------------------------------------------------------- #
CONFIGS = {
    "A-defaults": dict(
        direction_override=DIRECTION,
        rr_min=8.0,
        morning_drawdown=0.50,
        late_morning_drawdown=0.40,
        afternoon_drawdown=0.30,
        slippage=0.05,
        use_vix_center=True,
        use_absolute_loss_stop=True,
    ),
    "B-no-abs-stop": dict(
        direction_override=DIRECTION,
        rr_min=8.0,
        morning_drawdown=0.50,
        late_morning_drawdown=0.40,
        afternoon_drawdown=0.30,
        slippage=0.05,
        use_vix_center=True,
        use_absolute_loss_stop=False,
    ),
    "C-wider-dd": dict(
        direction_override=DIRECTION,
        rr_min=8.0,
        morning_drawdown=0.75,
        late_morning_drawdown=0.65,
        afternoon_drawdown=0.50,
        slippage=0.05,
        use_vix_center=True,
        use_absolute_loss_stop=False,
    ),
    "D-hold-expiry": dict(
        direction_override=DIRECTION,
        rr_min=8.0,
        morning_drawdown=0.50,
        late_morning_drawdown=0.40,
        afternoon_drawdown=0.30,
        slippage=0.05,
        use_vix_center=True,
        use_absolute_loss_stop=False,
        hold_to_expiry=True,
    ),
}
# --------------------------------------------------------------------------- #


async def get_all_dates(conn: asyncpg.Connection) -> list[dt.date]:
    """Return all dates that have a full trading day of SPX chain data (>= 50 snapshots)."""
    rows = await conn.fetch(
        """
        SELECT snapshot_time::date AS trade_date, COUNT(DISTINCT snapshot_time) AS snap_count
        FROM option_chain_snapshots
        WHERE underlying = 'SPX'
          AND expiration = snapshot_time::date
        GROUP BY trade_date
        HAVING COUNT(DISTINCT snapshot_time) >= 50
        ORDER BY trade_date
        """
    )
    return [r["trade_date"] for r in rows]


async def load_chains_from_db(
    conn: asyncpg.Connection, date: dt.date
) -> dict[dt.datetime, list[OptionQuote]]:
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


async def load_bars_from_db(conn: asyncpg.Connection, date: dt.date) -> list[MinuteBar]:
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


async def get_prev_close(conn: asyncpg.Connection, date: dt.date) -> float:
    row = await conn.fetchval(
        "SELECT price FROM spot_prices WHERE underlying = 'SPX' AND ts::date < $1 ORDER BY ts DESC LIMIT 1",
        date,
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
    end = date + dt.timedelta(days=1)
    hist = yf.Ticker("^VIX").history(start=date, end=end, interval="1d")
    if not hist.empty:
        return float(hist["Close"].iloc[0])
    return 18.0


def select_live_width(
    quotes: list[OptionQuote],
    spot: float,
    direction: str,
    vix: float,
    wing_widths: list[int],
    rr_min: float,
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


async def run_day(
    conn: asyncpg.Connection,
    date: dt.date,
    engine: SimulationEngine,
) -> dict[str, object] | None:
    """Load data and run all configs for one date. Returns None if data insufficient."""
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
    chosen = select_live_width(
        quotes=entry_quotes,
        spot=entry_spot,
        direction=DIRECTION,
        vix=vix,
        wing_widths=WING_WIDTHS,
        rr_min=8.0,
    )
    if not chosen:
        return None

    day = DayData(date=date, bars=bars, vix=vix, prev_close=prev_close)

    # Patch chain cache
    import butterfly_guy.backtest.chain_cache as _cc
    _cc._DB_CHAINS = chains  # type: ignore[attr-defined]
    _original_load = _cc.load_chain_day

    def _patched_load(d, cache_dir=None):
        if d == date:
            return _cc._DB_CHAINS  # type: ignore[attr-defined]
        return _original_load(d, cache_dir) if cache_dir else _original_load(d)

    _cc.load_chain_day = _patched_load  # type: ignore[assignment]

    results = {}
    for config_name, param_dict in CONFIGS.items():
        params = SimulationParams(wing_width=chosen.wing_width, **param_dict)
        results[config_name] = engine.simulate_day(day, params)

    _cc.load_chain_day = _original_load  # type: ignore[assignment]

    return {
        "date": date,
        "vix": vix,
        "entry_spot": entry_spot,
        "wing_width": chosen.wing_width,
        "center_strike": chosen.center_strike,
        "results": results,
    }


async def main() -> None:
    print(f"\n{'='*100}")
    print(f"  MULTI-CONFIG DB BACKTEST  |  {DIRECTION} butterflies  |  widths: {WING_WIDTHS}")
    print(f"{'='*100}")
    print(f"  A  Defaults       : morning=50% late=40% afternoon=30%  abs_stop=ON")
    print(f"  B  No abs stop    : morning=50% late=40% afternoon=30%  abs_stop=OFF")
    print(f"  C  Wider DD       : morning=75% late=65% afternoon=50%  abs_stop=OFF")
    print(f"  D  Hold to expiry : no exits — run to close")
    print(f"{'='*100}\n")

    conn = await asyncpg.connect(DB_DSN)
    try:
        dates = await get_all_dates(conn)
    finally:
        await conn.close()

    if not dates:
        print("ERROR: No full trading days found in DB.")
        return

    print(f"  Found {len(dates)} full trading day(s): {dates[0]} → {dates[-1]}\n")

    engine = SimulationEngine()
    day_data: list[dict] = []

    for date in dates:
        print(f"  Processing {date}...", end="", flush=True)
        conn = await asyncpg.connect(DB_DSN)
        try:
            data = await run_day(conn, date, engine)
        finally:
            await conn.close()

        if data is None:
            print(" SKIPPED (no data or no entry)")
            continue
        day_data.append(data)
        print(f" done  (VIX={data['vix']:.1f}  SPX={data['entry_spot']:.0f}  "
              f"{data['wing_width']}W center={data['center_strike']:.0f})")

    if not day_data:
        print("\nNo tradeable days found.")
        return

    config_names = list(CONFIGS.keys())

    # ─── Per-day detail table ────────────────────────────────────────────────
    print(f"\n{'='*110}")
    print(f"  PER-DAY RESULTS")
    print(f"{'='*110}")
    header = f"  {'Date':>10}  {'VIX':>5}  {'W':>2}  {'Ctr':>5}"
    for cn in config_names:
        label = cn.split("-")[0]  # A, B, C, D
        header += f"  {label+':Exit':>18}  {label+':PnL/ct':>9}"
    print(header)
    print("  " + "-" * 108)

    totals: dict[str, list[float]] = {cn: [] for cn in config_names}
    no_trade_counts: dict[str, int] = {cn: 0 for cn in config_names}

    for d in day_data:
        row = f"  {d['date']!s:>10}  {d['vix']:>5.1f}  {d['wing_width']:>2}  {d['center_strike']:>5.0f}"
        for cn in config_names:
            r = d["results"][cn]
            if not r.traded:
                row += f"  {'NO TRADE':>18}  {'':>9}"
                no_trade_counts[cn] += 1
            else:
                pnl_ct = r.pnl * 100
                reason = r.exit_reason[:16]
                row += f"  {reason:>18}  ${pnl_ct:>+7.2f}"
                totals[cn].append(pnl_ct)
        print(row)

    # ─── Summary table ───────────────────────────────────────────────────────
    print(f"\n{'='*110}")
    print(f"  SUMMARY  ({len(day_data)} days)")
    print(f"{'='*110}")
    print(f"  {'Config':<20}  {'Trades':>6}  {'Winners':>7}  {'Win%':>5}  "
          f"{'Total PnL/ct':>13}  {'Avg PnL/ct':>11}  {'Best':>8}  {'Worst':>8}")
    print("  " + "-" * 95)

    for cn in config_names:
        pnls = totals[cn]
        n_traded = len(pnls)
        n_days = len(day_data)
        winners = [p for p in pnls if p > 0]
        win_pct = len(winners) / n_traded * 100 if n_traded else 0
        total = sum(pnls)
        avg = total / n_traded if n_traded else 0
        best = max(pnls) if pnls else 0
        worst = min(pnls) if pnls else 0
        print(f"  {cn:<20}  {n_traded:>6}  {len(winners):>7}  {win_pct:>4.0f}%  "
              f"  ${total:>+10.2f}  ${avg:>+9.2f}  ${best:>+6.2f}  ${worst:>+6.2f}")

    print(f"{'='*110}\n")


if __name__ == "__main__":
    asyncio.run(main())
