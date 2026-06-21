"""Print stored entry/exit ladder traces for a trade or trade date."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import subprocess
from urllib.parse import urlsplit, urlunsplit

import asyncpg

from butterfly_guy.core.config import load_config


def resolve_db_dsn() -> str:
    return load_config().database.dsn


def _docker_postgres_password(container_name: str = "butterfly_timescaledb") -> str | None:
    """Best-effort fallback to the running TimescaleDB container password."""
    try:
        proc = subprocess.run(
            ["docker", "exec", container_name, "env"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None

    for line in proc.stdout.splitlines():
        if line.startswith("POSTGRES_PASSWORD="):
            return line.split("=", 1)[1]
    return None


def _replace_dsn_password(dsn: str, password: str) -> str:
    parts = urlsplit(dsn)
    if "@" not in parts.netloc:
        return dsn
    creds, host = parts.netloc.rsplit("@", 1)
    if ":" in creds:
        user, _ = creds.split(":", 1)
    else:
        user = creds
    return urlunsplit(
        (parts.scheme, f"{user}:{password}@{host}", parts.path, parts.query, parts.fragment)
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Report stored ladder traces for paper/live trades",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("trade_date", type=dt.date.fromisoformat, help="Trade date YYYY-MM-DD")
    p.add_argument("--underlying", default="SPX", choices=["SPX", "NDX", "XSP"], help="Underlying")
    p.add_argument("--trade-id", type=int, default=None, help="Optional specific trade id")
    return p.parse_args()


def _pretty(value: object) -> str:
    return json.dumps(value, indent=2, default=str, sort_keys=True)


def _coerce_json(value: object) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


async def _load_trade_rows(
    conn: asyncpg.Connection,
    trade_date: dt.date,
    underlying: str,
    trade_id: int | None,
) -> list[asyncpg.Record]:
    if trade_id is not None:
        return await conn.fetch(
            """
            SELECT *
            FROM butterfly_trades
            WHERE id = $1 AND trade_date = $2 AND underlying = $3
            ORDER BY entry_time
            """,
            trade_id,
            trade_date,
            underlying,
        )
    return await conn.fetch(
        """
        SELECT *
        FROM butterfly_trades
        WHERE trade_date = $1 AND underlying = $2
        ORDER BY entry_time
        """,
        trade_date,
        underlying,
    )


async def _load_trace_event(
    conn: asyncpg.Connection,
    trade_id: int,
    event_type: str,
    underlying: str,
) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT data
        FROM decision_log
        WHERE event_type = $1
          AND underlying = $2
          AND data->>'trade_id' = $3
        ORDER BY ts DESC
        LIMIT 1
        """,
        event_type,
        underlying,
        str(trade_id),
    )
    if row is None:
        return None
    return _coerce_json(row["data"])


def _print_trace_block(title: str, payload: object | None) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if payload is None:
        print("(missing)")
        return
    print(_pretty(payload))


async def main() -> None:
    args = parse_args()
    dsn = resolve_db_dsn()
    try:
        conn = await asyncpg.connect(dsn)
    except asyncpg.InvalidPasswordError:
        fallback_password = _docker_postgres_password()
        if not fallback_password:
            raise
        dsn = _replace_dsn_password(dsn, fallback_password)
        conn = await asyncpg.connect(dsn)
    try:
        rows = await _load_trade_rows(conn, args.trade_date, args.underlying, args.trade_id)
        if not rows:
            print(
                f"No trades found for {args.underlying} on {args.trade_date}"
                + (f" with id {args.trade_id}" if args.trade_id is not None else "")
            )
            return

        print(f"Found {len(rows)} trade(s) for {args.underlying} on {args.trade_date}")

        for row in rows:
            trade = dict(row)
            metadata = _coerce_json(trade.get("metadata")) or {}
            if not isinstance(metadata, dict):
                metadata = {}
            trade_id = trade["id"]
            print("\n" + "=" * 88)
            print(
                f"Trade {trade_id} | {trade['underlying']} {trade['direction']} "
                f"{trade['wing_width']}W center={trade['center_strike']} "
                f"entry={trade['entry_price']} exit={trade.get('exit_price')} "
                f"pnl={trade.get('pnl')} reason={trade.get('exit_reason')}"
            )
            print("=" * 88)
            _print_trace_block("ENTRY TRACE (trade row metadata)", metadata.get("entry_attempts"))
            entry_event = await _load_trace_event(
                conn, trade_id, "entry_ladder_trace", args.underlying
            )
            _print_trace_block("ENTRY TRACE (decision log)", entry_event)
            _print_trace_block("EXIT TRACE (trade row metadata)", metadata.get("exit_ladder_steps"))
            exit_event = await _load_trace_event(
                conn, trade_id, "exit_ladder_trace", args.underlying
            )
            _print_trace_block("EXIT TRACE (decision log)", exit_event)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
