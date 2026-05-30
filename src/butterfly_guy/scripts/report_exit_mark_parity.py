"""Compare live Schwab exit marks vs DB collector snapshots for a trade.

Usage:
    uv run python src/butterfly_guy/scripts/report_exit_mark_parity.py --trade-id 87
    uv run python src/butterfly_guy/scripts/report_exit_mark_parity.py \\
        --date 2026-05-20 --at 10:13 --strikes 7410,7430,7450 --direction CALL
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg

from butterfly_guy.core.config import load_config
from butterfly_guy.data.schemas import OptionQuote, fly_mark_value

EASTERN = ZoneInfo("America/New_York")


def _quote_from_row(row: asyncpg.Record, underlying: str, expiration: dt.date) -> OptionQuote:
    return OptionQuote(
        symbol=row.get("symbol") or "",
        underlying=underlying,
        expiration=expiration,
        strike=float(row["strike"]),
        option_type=row["option_type"],
        bid=float(row["bid"] or 0),
        ask=float(row["ask"] or 0),
        mark=float(row["mark"] or 0),
        last=float(row.get("last") or 0),
    )


def _fly_from_rows(
    rows: list[asyncpg.Record],
    *,
    underlying: str,
    expiration: dt.date,
    strikes: list[float],
) -> tuple[dict[float, OptionQuote], float | None]:
    by_strike = {
        float(row["strike"]): _quote_from_row(row, underlying, expiration)
        for row in rows
    }
    if not all(strike in by_strike for strike in strikes):
        return by_strike, None
    lower, center, upper = (by_strike[strikes[0]], by_strike[strikes[1]], by_strike[strikes[2]])
    return by_strike, fly_mark_value(lower, center, upper)


async def _nearest_snapshot_time(
    conn: asyncpg.Connection,
    *,
    underlying: str,
    expiration: dt.date,
    at: dt.datetime,
) -> dt.datetime | None:
    return await conn.fetchval(
        """
        SELECT snapshot_time
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time <= $3
        ORDER BY snapshot_time DESC
        LIMIT 1
        """,
        underlying,
        expiration,
        at,
    )


async def _leg_rows_at_snapshot(
    conn: asyncpg.Connection,
    *,
    underlying: str,
    expiration: dt.date,
    snapshot_time: dt.datetime,
    direction: str,
    strikes: list[float],
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT strike, option_type, bid, ask, mark, last, snapshot_time, symbol
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time = $3
          AND option_type = $4
          AND strike = ANY($5::numeric[])
        ORDER BY strike
        """,
        underlying,
        expiration,
        snapshot_time,
        direction,
        strikes,
    )


def _print_leg_table(
    title: str,
    *,
    snapshot_time: dt.datetime | None,
    lag_seconds: float | None,
    by_strike: dict[float, OptionQuote],
    strikes: list[float],
    fly_mark: float | None,
) -> None:
    print(f"\n{title}")
    if snapshot_time is not None:
        et = snapshot_time.astimezone(EASTERN).strftime("%H:%M:%S")
        lag_s = f"{lag_seconds:.0f}s" if lag_seconds is not None else "n/a"
        print(f"  Snapshot ET: {et}  lag: {lag_s}")
    print(f"  {'Strike':>7}  {'Bid':>6}  {'Ask':>6}  {'Mark':>6}")
    for strike in strikes:
        quote = by_strike.get(strike)
        if quote is None:
            print(f"  {strike:>7.0f}  {'—':>6}  {'—':>6}  {'—':>6}")
            continue
        print(
            f"  {strike:>7.0f}  {quote.bid:>6.2f}  {quote.ask:>6.2f}  {quote.mark:>6.2f}"
        )
    if fly_mark is not None:
        print(f"  Fly mark: {fly_mark:.4f}")


async def analyze_trade(conn: asyncpg.Connection, trade_id: int) -> None:
    trade = await conn.fetchrow("SELECT * FROM butterfly_trades WHERE id = $1", trade_id)
    if trade is None:
        print(f"Trade {trade_id} not found.")
        return

    underlying = trade["underlying"]
    expiration = trade["trade_date"]
    direction = trade["direction"]
    strikes = [
        float(trade["lower_strike"]),
        float(trade["center_strike"]),
        float(trade["upper_strike"]),
    ]
    exit_time = trade["exit_time"]
    if exit_time.tzinfo is None:
        exit_time = exit_time.replace(tzinfo=dt.timezone.utc)

    metadata = trade["metadata"]
    if isinstance(metadata, str):
        metadata = json.loads(metadata)

    print(f"Trade {trade_id}  {expiration}  {direction}  "
          f"{int(trade['wing_width'])}W center={float(trade['center_strike']):.0f}")
    print(f"  Entry: ${float(trade['entry_price']):.2f} @ "
          f"{trade['entry_time'].astimezone(EASTERN).strftime('%H:%M:%S')} ET")
    print(f"  Exit:  ${float(trade['exit_price']):.2f} @ "
          f"{exit_time.astimezone(EASTERN).strftime('%H:%M:%S')} ET  "
          f"reason={trade['exit_reason']}")

    live_mark = metadata.get("exit_mark_at_signal")
    if live_mark is not None:
        print(f"  Live exit_mark_at_signal (Schwab poll): {float(live_mark):.4f}")

    ladder = metadata.get("exit_ladder_steps") or []
    if ladder:
        print("  Live exit ladder marks:")
        for step in ladder:
            print(
                f"    step {step.get('step')}: mark={step.get('mark')} "
                f"bid={step.get('bid')} ask={step.get('ask')} filled={step.get('filled')}"
            )

    await _compare_snapshots(
        conn,
        underlying=underlying,
        expiration=expiration,
        direction=direction,
        strikes=strikes,
        at=exit_time,
        live_mark=float(live_mark) if live_mark is not None else None,
    )


async def _compare_snapshots(
    conn: asyncpg.Connection,
    *,
    underlying: str,
    expiration: dt.date,
    direction: str,
    strikes: list[float],
    at: dt.datetime,
    live_mark: float | None,
) -> None:
    if at.tzinfo is None:
        at = at.replace(tzinfo=dt.timezone.utc)

    nearest_ts = await _nearest_snapshot_time(
        conn,
        underlying=underlying,
        expiration=expiration,
        at=at,
    )
    if nearest_ts is None:
        print("\nNo DB snapshot at or before target time.")
        return

    nearest_rows = await _leg_rows_at_snapshot(
        conn,
        underlying=underlying,
        expiration=expiration,
        snapshot_time=nearest_ts,
        direction=direction,
        strikes=strikes,
    )
    nearest_quotes, nearest_fly = _fly_from_rows(
        nearest_rows,
        underlying=underlying,
        expiration=expiration,
        strikes=strikes,
    )
    _print_leg_table(
        "DB nearest_snapshot (what backtest replay uses)",
        snapshot_time=nearest_ts,
        lag_seconds=(at - nearest_ts).total_seconds(),
        by_strike=nearest_quotes,
        strikes=strikes,
        fly_mark=nearest_fly,
    )

    # Exact collector snapshots within ±60s of target (Schwab-cached chains in DB)
    window_rows = await conn.fetch(
        """
        SELECT DISTINCT snapshot_time
        FROM option_chain_snapshots
        WHERE underlying = $1
          AND expiration = $2
          AND snapshot_time BETWEEN $3 AND $4
        ORDER BY snapshot_time
        """,
        underlying,
        expiration,
        at - dt.timedelta(seconds=60),
        at + dt.timedelta(seconds=60),
    )
    if window_rows:
        print("\nCollector snapshots within ±60s (raw Schwab cache in DB):")
        for row in window_rows:
            snap_ts = row["snapshot_time"]
            snap_rows = await _leg_rows_at_snapshot(
                conn,
                underlying=underlying,
                expiration=expiration,
                snapshot_time=snap_ts,
                direction=direction,
                strikes=strikes,
            )
            quotes, fly = _fly_from_rows(
                snap_rows,
                underlying=underlying,
                expiration=expiration,
                strikes=strikes,
            )
            _print_leg_table(
                f"  snapshot",
                snapshot_time=snap_ts,
                lag_seconds=(at - snap_ts).total_seconds(),
                by_strike=quotes,
                strikes=strikes,
                fly_mark=fly,
            )

    if live_mark is not None and nearest_fly is not None:
        delta = live_mark - nearest_fly
        print(
            f"\nLive vs nearest_snapshot fly mark delta: {delta:+.4f} "
            f"(live {live_mark:.4f} vs DB {nearest_fly:.4f})"
        )
        if delta < -0.05:
            print(
                "  Schwab live mark is materially lower than DB collector snapshot — "
                "drawdown exits may fire earlier live than in DB replay."
            )


async def analyze_manual(
    conn: asyncpg.Connection,
    *,
    date: dt.date,
    at_et: dt.time,
    underlying: str,
    direction: str,
    strikes: list[float],
) -> None:
    at = dt.datetime.combine(date, at_et, tzinfo=EASTERN).astimezone(dt.timezone.utc)
    print(f"Manual check  {date}  {at_et.strftime('%H:%M')} ET  {direction}  strikes={strikes}")
    await _compare_snapshots(
        conn,
        underlying=underlying,
        expiration=date,
        direction=direction,
        strikes=strikes,
        at=at,
        live_mark=None,
    )


async def run(args: argparse.Namespace) -> None:
    conn = await asyncpg.connect(load_config().database.dsn)
    try:
        if args.trade_id is not None:
            await analyze_trade(conn, args.trade_id)
            return

        if args.date is None or args.at is None or args.strikes is None:
            print("Provide --trade-id or (--date, --at, --strikes).")
            return

        strikes = [float(s.strip()) for s in args.strikes.split(",")]
        at_et = dt.time.fromisoformat(args.at)
        await analyze_manual(
            conn,
            date=args.date,
            at_et=at_et,
            underlying=args.asset,
            direction=args.direction,
            strikes=strikes,
        )
    finally:
        await conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare live exit marks vs DB chain snapshots")
    parser.add_argument("--trade-id", type=int, default=None)
    parser.add_argument("--date", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--at", help="Time in ET, e.g. 10:13")
    parser.add_argument("--strikes", help="Comma-separated strikes, e.g. 7410,7430,7450")
    parser.add_argument("--direction", default="CALL", choices=["CALL", "PUT"])
    parser.add_argument("--asset", default="SPX")
    return parser.parse_args()


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
