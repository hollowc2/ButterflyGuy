"""Latch new entries in daily_risk_state; never submit or cancel broker orders."""

from __future__ import annotations

import argparse
import asyncio

from butterfly_guy.core.config import load_config
from butterfly_guy.core.time_utils import session_date
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.queries import RiskQueries


async def halt(config_path: str, reason: str) -> None:
    if not reason.strip():
        raise ValueError("A nonempty incident reason is required")
    config = load_config(config_path)
    db = DatabasePool(config.database.dsn)
    try:
        await db.initialize()
        await RiskQueries(db).halt_entries(
            session_date(), config.strategy.underlying, reason.strip()
        )
        print("Entry halt committed. Take manual broker control, then stop the container.")
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--reason", required=True, help="Non-secret incident reference/reason")
    args = parser.parse_args()
    asyncio.run(halt(args.config, args.reason))


if __name__ == "__main__":
    main()
