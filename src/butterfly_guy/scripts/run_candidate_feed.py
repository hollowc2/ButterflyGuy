"""Run the demand-aware shared SPX candidate market-data feed."""

from __future__ import annotations

import argparse
import asyncio
import os

from aiohttp import web

from butterfly_guy.candidate_fleet.feed import (
    AtomicSnapshotStore,
    CandidateFeed,
    LeaseRegistry,
    SnapshotArchive,
    create_app,
)
from butterfly_guy.candidate_fleet.schwab_market_data import ReadOnlySchwabMarketDataClient
from butterfly_guy.core.config import DatabaseSettings, SchwabSettings
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.db.connection import DatabasePool


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    setup_logging(os.getenv("LOG_LEVEL", "INFO"), json_output=True)

    schwab = ReadOnlySchwabMarketDataClient(
        SchwabSettings(
            api_key=os.environ["SCHWAB_API_KEY"],
            secret_key=os.environ["SCHWAB_SECRET_KEY"],
            token_path=os.getenv("SCHWAB_TOKEN_PATH", "tokens.json"),
        )
    )
    database = DatabaseSettings(
        host=os.getenv("DATABASE_HOST", "timescaledb"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        name=os.getenv("DATABASE_NAME", "butterfly_guy_candidate_market"),
        user=os.getenv("DATABASE_USER", "butterfly"),
        password=os.getenv("DATABASE_PASSWORD", ""),
    )
    db = DatabasePool(database.dsn, min_size=1, max_size=4)
    await db.initialize()
    archive = SnapshotArchive(db)
    await archive.initialize()
    await schwab.initialize()
    feed = CandidateFeed(
        schwab,
        AtomicSnapshotStore(),
        LeaseRegistry(ttl_seconds=30),
        archive,
    )
    await feed.collect_once()
    runner = web.AppRunner(create_app(feed))
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", args.port)
    await site.start()
    collector = asyncio.create_task(feed.run(), name="candidate_feed_collector")
    try:
        await asyncio.Event().wait()
    finally:
        collector.cancel()
        await runner.cleanup()
        await schwab.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
