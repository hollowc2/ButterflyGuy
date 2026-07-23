"""Run one isolated paper-only evaluator against the shared SPX feed."""

from __future__ import annotations

import argparse
import asyncio
import os

import yaml

from butterfly_guy.candidate_fleet.evaluator import (
    CandidateAuditContext,
    CandidateEvaluator,
    assert_candidate_safety,
    config_sha256,
)
from butterfly_guy.candidate_fleet.provider import HttpMarketDataProvider
from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import setup_logging
from butterfly_guy.core.metrics import set_readiness, start_metrics_server
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import (
    CandidateQueries,
    DecisionQueries,
    MonitoringLegQueries,
    RiskQueries,
    TentQueries,
    TradeQueries,
)


def load_candidate_config(path: str) -> AppConfig:
    with open(path) as config_file:
        payload = yaml.safe_load(config_file) or {}
    payload["schwab"] = {}
    return AppConfig(**payload)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    candidate_id = os.environ["CANDIDATE_ID"]
    config = load_candidate_config(args.config)
    assert_candidate_safety(config)
    setup_logging(config.monitoring.log_level, json_output=True)
    start_metrics_server(config.monitoring.metrics_port, underlying=candidate_id)

    db = DatabasePool(config.database.dsn, min_size=1, max_size=4)
    await db.initialize()
    await run_migrations(db)
    provider = HttpMarketDataProvider(os.environ["CANDIDATE_FEED_URL"])
    evaluator = CandidateEvaluator(
        candidate_id=candidate_id,
        config=config,
        provider=provider,
        audit=CandidateAuditContext(
            candidate_id=candidate_id,
            config_hash=config_sha256(args.config),
            git_sha=os.getenv("DEPLOYED_GIT_SHA", "unknown"),
        ),
        trade_queries=TradeQueries(db),
        risk_queries=RiskQueries(db),
        candidate_queries=CandidateQueries(db),
        decision_queries=DecisionQueries(db),
        monitoring_leg_queries=MonitoringLegQueries(db),
        tent_queries=TentQueries(db),
        review_trade_count=int(os.getenv("CANDIDATE_REVIEW_TRADE_COUNT", "1")),
    )
    set_readiness(None)
    try:
        await evaluator.run()
    finally:
        set_readiness("shutting_down")
        await provider.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
