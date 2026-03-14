"""Main orchestrator: runs collector + trading + position monitor concurrently."""
# TODO(regime-classifier): For regime-adaptive live trading, source recent_closes
# from Schwab's get_price_history endpoint (frequencyType=daily, frequency=1,
# periodType=month) covering at least lookback_days + 5 prior trading days.
# Construct a RegimeDispatch with tuned thresholds from run_classifier_sweep.py
# and call engine.simulate_day_adaptive() instead of simulate_day() in the entry loop.
# Note: revisit BULL regime direction (CALL vs PUT) before deploying live.

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.metrics import start_metrics_server
from butterfly_guy.core.time_utils import is_market_open, now_eastern
from butterfly_guy.data.collector import OptionChainCollector
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import (
    CandidateQueries,
    ChainQueries,
    DecisionQueries,
    RiskQueries,
    SpotQueries,
    TradeQueries,
)
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.position_service import PositionService
from butterfly_guy.services.trade_service import TradeService
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

log = get_logger("run_live")


async def entry_loop(trade_service: TradeService, position_service: PositionService) -> None:
    """Periodically attempt entries during the entry window."""
    active_trade = None
    monitor_task: asyncio.Task | None = None

    while True:
        if not is_market_open():
            await asyncio.sleep(30)
            continue

        # Check if monitor task has finished — reset active_trade so we can re-enter
        if monitor_task is not None and monitor_task.done():
            exc = monitor_task.exception()
            if exc:
                log.error("monitor_task_error", error=str(exc))
            active_trade = None
            monitor_task = None

        # If no active position, try entry
        if active_trade is None:
            try:
                result = await trade_service.attempt_entry()
                if result:
                    active_trade, candidate = result
                    log.info("entry_loop_got_trade", trade_id=active_trade.trade_id)
                    monitor_task = asyncio.create_task(
                        position_service.monitor_loop(active_trade, candidate),
                        name=f"monitor_{active_trade.trade_id}",
                    )
            except Exception as e:
                log.error("entry_loop_error", error=str(e))

        await asyncio.sleep(15)


async def daily_reset_loop(risk_queries: RiskQueries) -> None:
    """Reset daily risk state at market open."""
    while True:
        now = now_eastern()
        # Sleep until next day
        next_midnight = (now + dt.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_secs = (next_midnight - now).total_seconds()
        await asyncio.sleep(sleep_secs)
        today = dt.date.today()
        await risk_queries.get_or_create(today)
        log.info("daily_risk_reset", date=str(today))


async def main() -> None:
    config = load_config()
    setup_logging(config.monitoring.log_level, json_output=True)

    log.info("live_trading_starting")
    start_metrics_server(config.monitoring.metrics_port)

    # Init DB
    db = DatabasePool(config.database.dsn)
    await db.initialize()
    await run_migrations(db)

    # Init Schwab
    schwab = SchwabClientWrapper(config.schwab)
    await schwab.initialize()

    # Build query objects
    chain_q = ChainQueries(db)
    spot_q = SpotQueries(db)
    trade_q = TradeQueries(db)
    risk_q = RiskQueries(db)
    decision_q = DecisionQueries(db)
    candidate_q = CandidateQueries(db)

    # Build service objects
    risk_engine = RiskEngine(config.risk, risk_q)
    order_builder = ButterflyOrderBuilder()
    order_manager = OrderManager(config.execution, schwab, order_builder)

    trade_service = TradeService(
        config=config,
        schwab=schwab,
        risk_engine=risk_engine,
        order_manager=order_manager,
        builder=ButterflyBuilder(config.strategy),
        selector=ButterflySelector(config.strategy),
        direction_filter=DirectionFilter(),
        chain_queries=chain_q,
        trade_queries=trade_q,
        candidate_queries=candidate_q,
        decision_queries=decision_q,
    )

    position_service = PositionService(
        config=config,
        schwab=schwab,
        order_manager=order_manager,
        risk_engine=risk_engine,
        trade_queries=trade_q,
        decision_queries=decision_q,
    )

    collector = OptionChainCollector(
        config=config,
        schwab=schwab,
        chain_queries=chain_q,
        spot_queries=spot_q,
    )

    # Discord notifier (optional)
    from dotenv import dotenv_values
    env = dotenv_values(".env")
    webhook = env.get("DISCORD_WEBHOOK_URL", "")
    notifier = DiscordNotifier(webhook) if webhook else None

    if notifier:
        await notifier._post("🚀 Butterfly Guy starting up!")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(collector.run_loop(), name="collector")
            tg.create_task(
                entry_loop(trade_service, position_service), name="entry_loop"
            )
            tg.create_task(daily_reset_loop(risk_q), name="daily_reset")
    except* Exception as eg:
        for exc in eg.exceptions:
            log.error("task_group_error", error=str(exc))
            if notifier:
                await notifier.notify_error(str(exc), context="TaskGroup")
    finally:
        await schwab.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
