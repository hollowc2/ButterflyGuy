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
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.db.connection import DatabasePool

log = get_logger(__name__)
TOKEN_RELOAD_INTERVAL = 300.0


async def token_reload_loop(
    schwab: ReadOnlySchwabMarketDataClient,
    *,
    interval: float = TOKEN_RELOAD_INTERVAL,
) -> None:
    """Pick up a re-authorized token while retaining a working client on failure."""
    while True:
        await asyncio.sleep(interval)
        try:
            if await schwab.reload_if_reauthorized():
                log.info("candidate_token_reload_applied")
        except Exception as exc:
            log.error("candidate_token_reload_failed", reason=type(exc).__name__)


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
    runner = web.AppRunner(create_app(feed))
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", args.port)
    await site.start()
    collector = asyncio.create_task(feed.run(), name="candidate_feed_collector")
    token_reloader = asyncio.create_task(
        token_reload_loop(schwab), name="candidate_token_reload"
    )
    try:
        await asyncio.Event().wait()
    finally:
        collector.cancel()
        token_reloader.cancel()
        await asyncio.gather(collector, token_reloader, return_exceptions=True)
        await runner.cleanup()
        await schwab.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
