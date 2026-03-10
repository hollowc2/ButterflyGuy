"""Entry point: run the option chain collector."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.core.metrics import start_metrics_server
from butterfly_guy.data.collector import OptionChainCollector
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import ChainQueries, SpotQueries


async def main() -> None:
    config = load_config()
    setup_logging(config.monitoring.log_level, json_output=False)

    from butterfly_guy.core.logging import get_logger
    log = get_logger("run_collector")

    log.info("collector_starting", underlying=config.strategy.underlying)

    # Start Prometheus metrics
    start_metrics_server(config.monitoring.metrics_port)

    # Init DB
    db = DatabasePool(config.database.dsn)
    await db.initialize()
    await run_migrations(db)

    # Init Schwab
    schwab = SchwabClientWrapper(config.schwab)
    await schwab.initialize()

    # Build collector
    collector = OptionChainCollector(
        config=config,
        schwab=schwab,
        chain_queries=ChainQueries(db),
        spot_queries=SpotQueries(db),
    )

    try:
        await collector.run_loop()
    finally:
        await schwab.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
