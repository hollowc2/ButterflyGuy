"""Create, seed and gate the live SPX database that runs beside paper.

Runs in the release image with no token mount; it never talks to Schwab. The paper
database (butterfly_guy) is only ever opened read-only. See
docs/operations/concurrent-paper-live-spx-design.md §4, §5, §9, §10.

    python -m butterfly_guy.scripts.spx_live_db bootstrap --db butterfly_guy_spx_live \
        --copy-live-trade 415
    python -m butterfly_guy.scripts.spx_live_db seed-daily-bars --db butterfly_guy_spx_live
    python -m butterfly_guy.scripts.spx_live_db check --db butterfly_guy_spx_live
    python -m butterfly_guy.scripts.spx_live_db compare --date 2026-11-20 --out-dir /tmp/x
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import asyncpg

from butterfly_guy.core.config import DatabaseSettings, load_config
from butterfly_guy.core.instance_role import PAPER_DATABASE_NAME
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import MIGRATIONS_DIR, run_migrations
from butterfly_guy.reports import spx_paired

LIVE_DB_PREFIX = "butterfly_guy_spx_live"
# Live trade and intent ids start here, so an id names its database on sight.
LIVE_ID_START = 100_000
DAILY_BAR_SYMBOLS = ("SPX", "$VIX")
DAILY_BAR_SEED_DAYS = 400
TERMINAL_INTENT_STATUSES = ("FILLED", "CANCELED", "REJECTED", "EXPIRED")

# The same 7-day compression butterfly_guy carries (added there by hand, not by migrations).
COMPRESSION = {
    "option_chain_snapshots": ("underlying, expiration, option_type", "snapshot_time DESC"),
    "spot_prices": ("underlying", "ts DESC"),
    "tent_boundaries": ("underlying", "ts DESC"),
    "butterfly_candidates": ("underlying, direction", "scan_time DESC"),
}
COMPRESS_AFTER = "7 days"


class LiveDbError(RuntimeError):
    """A refusal; nothing unsafe was written."""


def target_name(name: str) -> str:
    """Only live/rehearsal databases may be written; never the paper database."""
    if name == PAPER_DATABASE_NAME or not name.startswith(LIVE_DB_PREFIX):
        raise LiveDbError(f"refusing to write {name!r}: not a {LIVE_DB_PREFIX}* database")
    return name


def dsn_for(base: DatabaseSettings, name: str) -> str:
    return base.model_copy(update={"name": name}).dsn


async def connect_read_only(base: DatabaseSettings, name: str) -> asyncpg.Connection:
    conn = await asyncpg.connect(dsn_for(base, name))
    await conn.execute("SET default_transaction_read_only = on")
    return conn


async def ensure_database(base: DatabaseSettings, name: str) -> bool:
    """Create the database if missing. Returns True when it was created."""
    admin = await asyncpg.connect(dsn_for(base, "postgres"))
    try:
        if await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", name):
            return False
        await admin.execute(f'CREATE DATABASE "{name}"')
        return True
    finally:
        await admin.close()


async def ensure_compression(conn: asyncpg.Connection) -> list[str]:
    added = []
    for table, (segment_by, order_by) in COMPRESSION.items():
        enabled = await conn.fetchval(
            "SELECT compression_enabled FROM timescaledb_information.hypertables "
            "WHERE hypertable_name = $1",
            table,
        )
        if not enabled:
            await conn.execute(
                f"ALTER TABLE {table} SET (timescaledb.compress, "
                f"timescaledb.compress_segmentby = '{segment_by}', "
                f"timescaledb.compress_orderby = '{order_by}')"
            )
        await conn.execute(
            f"SELECT add_compression_policy('{table}', INTERVAL '{COMPRESS_AFTER}', "
            "if_not_exists => TRUE)"
        )
        added.append(table)
    return added


async def ensure_id_start(conn: asyncpg.Connection) -> None:
    for table in ("butterfly_trades", "broker_order_intents"):
        sequence = await conn.fetchval("SELECT pg_get_serial_sequence($1, 'id')", table)
        last = await conn.fetchval(f"SELECT last_value FROM {sequence}")
        if last < LIVE_ID_START - 1:
            await conn.execute("SELECT setval($1, $2)", sequence, LIVE_ID_START - 1)


async def seed_daily_bars(source: asyncpg.Connection, target: asyncpg.Connection) -> int:
    """Copy closed daily bars newer than the target's latest, per symbol."""
    copied = 0
    for symbol in DAILY_BAR_SYMBOLS:
        latest = await target.fetchval(
            "SELECT max(date) FROM daily_bars WHERE underlying = $1", symbol
        )
        rows = await source.fetch(
            """
            SELECT date, underlying, open, high, low, close, volume FROM daily_bars
            WHERE underlying = $1
              AND date > COALESCE($2::date, CURRENT_DATE - $3::int)
            ORDER BY date
            """,
            symbol,
            latest,
            DAILY_BAR_SEED_DAYS,
        )
        await target.executemany(
            """
            INSERT INTO daily_bars (date, underlying, open, high, low, close, volume)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (date, underlying) DO NOTHING
            """,
            [tuple(row) for row in rows],
        )
        copied += len(rows)
    return copied


async def _copy_rows(
    target: asyncpg.Connection, table: str, rows: list[asyncpg.Record]
) -> int:
    if not rows:
        return 0
    columns = list(rows[0].keys())
    await target.copy_records_to_table(
        table, records=[tuple(row) for row in rows], columns=columns
    )
    return len(rows)


async def live_trade(
    source: asyncpg.Connection, trade_id: int
) -> tuple[asyncpg.Record, list[asyncpg.Record]]:
    """Return a CLOSED, broker-placed live trade and its intents, or refuse."""
    trade = await source.fetchrow("SELECT * FROM butterfly_trades WHERE id = $1", trade_id)
    if trade is None:
        raise LiveDbError(f"trade {trade_id} not found")
    if trade["status"] != "CLOSED":
        raise LiveDbError(f"trade {trade_id} is {trade['status']}, not CLOSED")
    if "paper_fill_model" in json.loads(trade["metadata"] or "{}"):
        raise LiveDbError(f"trade {trade_id} is a paper trade")
    intents = await source.fetch(
        "SELECT * FROM broker_order_intents WHERE trade_id = $1 ORDER BY id", trade_id
    )
    if not any(intent["broker_order_id"] for intent in intents):
        raise LiveDbError(f"trade {trade_id} has no broker order: not a live trade")
    return trade, intents


async def copy_live_trade(
    source: asyncpg.Connection, target: asyncpg.Connection, trade_id: int
) -> dict[str, int]:
    """Copy one CLOSED, broker-placed live trade and its evidence. Idempotent."""
    trade, intents = await live_trade(source, trade_id)
    if await target.fetchval("SELECT 1 FROM butterfly_trades WHERE id = $1", trade_id):
        return {}

    window = (
        trade["entry_time"],
        trade["exit_time"] or trade["entry_time"],
    )
    counts: dict[str, int] = {}
    async with target.transaction():
        counts["butterfly_trades"] = await _copy_rows(target, "butterfly_trades", [trade])
        counts["broker_order_intents"] = await _copy_rows(
            target, "broker_order_intents", intents
        )
        for table in ("monitoring_leg_quotes", "post_exit_leg_quotes"):
            rows = await source.fetch(
                f"SELECT * FROM {table} WHERE trade_id = $1 ORDER BY ts", trade_id
            )
            counts[table] = await _copy_rows(target, table, rows)
        decisions = await source.fetch(
            """
            SELECT ts, event_type, data, underlying FROM decision_log
            WHERE underlying = $1
              AND ts BETWEEN $2::timestamptz - INTERVAL '1 hour'
                         AND $3::timestamptz + INTERVAL '1 hour'
            ORDER BY ts, id
            """,
            trade["underlying"],
            *window,
        )
        counts["decision_log"] = await _copy_rows(target, "decision_log", decisions)
    return counts


def migration_head() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_text().encode()).hexdigest()
        for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    }


async def check(conn: asyncpg.Connection, *, allow_paper_trades: bool = False) -> dict[str, Any]:
    """Gate for activation and close-out: schema at head, flat, and no paper rows.

    allow_paper_trades is for the rehearsal database only, whose trades are all paper.
    """
    has_ledger = await conn.fetchval("SELECT to_regclass('public.schema_migrations') IS NOT NULL")
    applied = (
        {r["version"]: r["checksum"] for r in await conn.fetch(
            "SELECT version, checksum FROM schema_migrations"
        )}
        if has_ledger
        else {}
    )
    result: dict[str, Any] = {"schema_at_head": applied == migration_head()}
    if not result["schema_at_head"]:
        result["ok"] = False
        return result
    result["open_spx_trades"] = await conn.fetchval(
        "SELECT count(*) FROM butterfly_trades WHERE underlying = 'SPX' AND status = 'OPEN'"
    )
    result["nonterminal_spx_intents"] = await conn.fetchval(
        "SELECT count(*) FROM broker_order_intents "
        "WHERE underlying = 'SPX' AND NOT (status = ANY($1::text[]))",
        list(TERMINAL_INTENT_STATUSES),
    )
    result["paper_trades"] = await conn.fetchval(
        "SELECT count(*) FROM butterfly_trades WHERE metadata ? 'paper_fill_model'"
    )
    result["ok"] = not (
        result["open_spx_trades"]
        or result["nonterminal_spx_intents"]
        or (result["paper_trades"] and not allow_paper_trades)
    )
    return result


async def bootstrap(
    base: DatabaseSettings, name: str, source_name: str, copy_trades: list[int]
) -> dict[str, Any]:
    # Refuse a bad trade id before creating or writing anything.
    source = await connect_read_only(base, source_name)
    try:
        for trade_id in copy_trades:
            await live_trade(source, trade_id)
    finally:
        await source.close()

    created = await ensure_database(base, name)
    db = DatabasePool(dsn_for(base, name), min_size=1, max_size=2)
    await db.initialize()
    try:
        await run_migrations(db)
    finally:
        await db.close()

    report: dict[str, Any] = {"database": name, "created": created}
    target = await asyncpg.connect(dsn_for(base, name))
    source = await connect_read_only(base, source_name)
    try:
        report["compressed_tables"] = await ensure_compression(target)
        report["daily_bars_copied"] = await seed_daily_bars(source, target)
        report["copied_trades"] = {
            trade_id: await copy_live_trade(source, target, trade_id)
            for trade_id in copy_trades
        }
        await ensure_id_start(target)
        report["check"] = await check(target)
    finally:
        await source.close()
        await target.close()
    return report


async def compare(
    base: DatabaseSettings,
    session: dt.date,
    paper_name: str,
    live_name: str,
    rate_limited: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Paired paper-vs-live report for one session; both databases read-only."""
    paper = await connect_read_only(base, paper_name)
    live = await connect_read_only(base, live_name)
    try:
        paper_trades, paper_blocks = await spx_paired.fetch_side(paper, session)
        live_trades, live_blocks = await spx_paired.fetch_side(live, session)
    finally:
        await paper.close()
        await live.close()
    return spx_paired.pair_report(
        session, paper_trades, live_trades, paper_blocks, live_blocks, rate_limited
    )


async def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", default="configs/config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("bootstrap", "seed-daily-bars", "check"):
        p = sub.add_parser(command)
        p.add_argument("--db", required=True)
        if command != "check":
            p.add_argument("--source-db", default=PAPER_DATABASE_NAME)
        if command == "bootstrap":
            p.add_argument("--copy-live-trade", type=int, action="append", default=[])
        if command == "check":
            p.add_argument("--allow-paper-trades", action="store_true")
    p = sub.add_parser("compare")
    p.add_argument("--date", required=True, type=dt.date.fromisoformat)
    p.add_argument("--paper-db", default=PAPER_DATABASE_NAME)
    p.add_argument("--live-db", default=LIVE_DB_PREFIX)
    p.add_argument("--out-dir", type=Path)
    # Schwab 429 counts from each container's logs; the databases do not record them.
    p.add_argument("--paper-rate-limited", type=int)
    p.add_argument("--live-rate-limited", type=int)
    args = parser.parse_args(argv)

    base = load_config(args.config).database
    if args.command == "compare":
        counts = {"paper": args.paper_rate_limited, "live": args.live_rate_limited}
        rate_limited = None if None in counts.values() else counts
        report = await compare(base, args.date, args.paper_db, args.live_db, rate_limited)
        markdown = spx_paired.render_markdown(report)
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            stem = f"spx-paired-{args.date.isoformat()}"
            (args.out_dir / f"{stem}.md").write_text(markdown)
            (args.out_dir / f"{stem}.json").write_text(
                json.dumps(report, default=str, indent=2, sort_keys=True)
            )
        print(markdown, end="")
        return 0

    try:
        name = target_name(args.db)
        if args.command == "bootstrap":
            result: dict[str, Any] = await bootstrap(
                base, name, args.source_db, args.copy_live_trade
            )
            ok = result["check"]["ok"]
        elif args.command == "seed-daily-bars":
            target = await asyncpg.connect(dsn_for(base, name))
            source = await connect_read_only(base, args.source_db)
            try:
                result = {"daily_bars_copied": await seed_daily_bars(source, target)}
            finally:
                await source.close()
                await target.close()
            ok = True
        else:
            conn = await connect_read_only(base, name)
            try:
                result = await check(conn, allow_paper_trades=args.allow_paper_trades)
            finally:
                await conn.close()
            ok = result["ok"]
    except LiveDbError as e:
        print(json.dumps({"ok": False, "refused": str(e)}))
        return 2
    print(json.dumps(result, default=str, sort_keys=True))
    return 0 if ok else 1


def main() -> None:
    sys.exit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
