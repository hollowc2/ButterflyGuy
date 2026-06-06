"""Generate the public SPX live performance static site from TimescaleDB.

Usage:
    uv run python src/butterfly_guy/scripts/generate_live_performance.py
    uv run python src/butterfly_guy/scripts/generate_live_performance.py \\
        --output /tmp/butterfly-spx/index.html
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg

from butterfly_guy.core.config import load_config
from butterfly_guy.core.time_utils import now_pacific
from butterfly_guy.reports.live_performance import (
    NO_TRADE_EVENTS,
    NoTradeDay,
    TradePoint,
    no_trade_reason,
    render_placeholder_html,
    render_report_html,
    trade_point_from_row,
)

DEFAULT_OUTPUT = Path("/var/www/billybitcoin.cloud/html/butterfly-spx/index.html")


async def fetch_closed_trades(conn: asyncpg.Connection, underlying: str) -> list[TradePoint]:
    rows = await conn.fetch(
        """
        SELECT *
        FROM butterfly_trades
        WHERE underlying = $1 AND status = 'CLOSED'
        ORDER BY trade_date, entry_time
        """,
        underlying,
    )
    return [trade_point_from_row(dict(row)) for row in rows]


async def fetch_no_trade_days(
    conn: asyncpg.Connection,
    underlying: str,
    start_date: dt.date,
    end_date: dt.date,
) -> list[NoTradeDay]:
    risk_rows = await conn.fetch(
        """
        SELECT trade_date, halted
        FROM daily_risk_state
        WHERE underlying = $1
          AND trade_date >= $2
          AND trade_date <= $3
          AND trade_count = 0
        ORDER BY trade_date
        """,
        underlying,
        start_date,
        end_date,
    )
    if not risk_rows:
        return []

    dates = [row["trade_date"] for row in risk_rows]
    event_rows = await conn.fetch(
        """
        SELECT DISTINCT ON (ts::date)
            ts::date AS trade_date,
            event_type,
            data
        FROM decision_log
        WHERE underlying = $1
          AND ts::date = ANY($2::date[])
          AND event_type = ANY($3::text[])
        ORDER BY ts::date, ts ASC
        """,
        underlying,
        dates,
        list(NO_TRADE_EVENTS),
    )
    events_by_date = {row["trade_date"]: row for row in event_rows}

    days: list[NoTradeDay] = []
    for row in risk_rows:
        trade_date = row["trade_date"]
        event = events_by_date.get(trade_date)
        event_data = event["data"] if event else None
        if isinstance(event_data, str):
            event_data = json.loads(event_data)
        status, reason = no_trade_reason(
            halted=bool(row["halted"]),
            event_type=event["event_type"] if event else None,
            event_data=event_data if isinstance(event_data, dict) else None,
        )
        days.append(NoTradeDay(trade_date=trade_date, status=status, reason=reason))
    return days


async def build_report(conn: asyncpg.Connection, underlying: str) -> tuple[list[TradePoint], list[NoTradeDay]]:
    trades = await fetch_closed_trades(conn, underlying)
    if not trades:
        return [], []

    start_date = trades[0].trade_date
    end_date = trades[-1].trade_date
    no_trade_days = await fetch_no_trade_days(conn, underlying, start_date, end_date)
    return trades, no_trade_days


def write_html_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


async def generate(*, underlying: str, output: Path) -> None:
    generated_at = now_pacific()
    conn = await asyncpg.connect(load_config().database.dsn)
    try:
        trades, no_trade_days = await build_report(conn, underlying)
    finally:
        await conn.close()

    if not trades:
        html_doc = render_placeholder_html(underlying=underlying, generated_at=generated_at)
    else:
        html_doc = render_report_html(
            underlying=underlying,
            trades=trades,
            no_trade_days=no_trade_days,
            generated_at=generated_at,
        )

    write_html_atomic(output, html_doc)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Butterfly Guy live performance site")
    parser.add_argument("--underlying", default="SPX")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        asyncio.run(generate(underlying=args.underlying, output=args.output))
    except Exception as exc:
        print(f"generate_live_performance failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
