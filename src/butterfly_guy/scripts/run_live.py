"""Main orchestrator: runs collector + trading + position monitor concurrently."""

from __future__ import annotations

import asyncio
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from butterfly_guy.core.config import load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.metrics import butterfly_candidates_found, daily_pnl, daily_trade_count, start_metrics_server, trades_active
from butterfly_guy.core.time_utils import is_market_open, now_eastern
from butterfly_guy.data.collector import OptionChainCollector
from butterfly_guy.data.schemas import ButterflyCandidate, TradeRecord
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.db.migrations.run_migrations import run_migrations
from butterfly_guy.db.queries import (
    CandidateQueries,
    ChainQueries,
    DailyBarQueries,
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
from butterfly_guy.strategy.regime_classifier import RegimeClassifier

log = get_logger("run_live")


async def entry_loop(
    trade_service: TradeService,
    position_service: PositionService,
    recovered_trade: TradeRecord | None = None,
    recovered_candidate: ButterflyCandidate | None = None,
) -> None:
    """Periodically attempt entries during the entry window."""
    active_trade: TradeRecord | None = recovered_trade
    monitor_task: asyncio.Task | None = None

    if recovered_trade is not None and recovered_candidate is not None:
        log.info("resuming_monitor_for_recovered_trade", trade_id=recovered_trade.trade_id)
        monitor_task = asyncio.create_task(
            position_service.monitor_loop(recovered_trade, recovered_candidate),
            name=f"monitor_{recovered_trade.trade_id}",
        )

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


async def daily_reset_loop(risk_queries: RiskQueries, underlying: str) -> None:
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
        await risk_queries.get_or_create(today, underlying)
        log.info("daily_risk_reset", date=str(today))


async def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML file")
    args = parser.parse_args()
    config = load_config(args.config)
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
    daily_bar_q = DailyBarQueries(db)

    # Build service objects
    risk_engine = RiskEngine(config.risk, risk_q, config.strategy.underlying)
    order_builder = ButterflyOrderBuilder()
    order_manager = OrderManager(config.execution, schwab, order_builder, config.strategy.underlying)

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
        daily_bar_queries=daily_bar_q,
    )

    # Classify today's market regime from stored daily bars
    regime_classifier = RegimeClassifier()
    lookback = regime_classifier.lookback_days
    recent_spx = await daily_bar_q.get_recent_closes(
        config.strategy.underlying, days=lookback + 5
    )
    vix_closes = await daily_bar_q.get_recent_closes("$VIX", days=1)
    vix_level = vix_closes[0] if vix_closes else 0.0
    regime = regime_classifier.classify(recent_spx, vix_level)
    log.info("regime_classified", regime=regime.value, spx_bars=len(recent_spx), vix=vix_level)

    # Discord notifier (optional)
    from dotenv import dotenv_values
    env = dotenv_values(".env")
    webhook = env.get("DISCORD_WEBHOOK_URL", "")
    notifier = DiscordNotifier(webhook) if webhook else None

    if notifier:
        await notifier._post("🚀 Butterfly Guy starting up!")

    # Recover any open trade and initialize daily metrics from DB
    underlying = config.strategy.underlying
    recovered_trade: TradeRecord | None = None
    recovered_candidate: ButterflyCandidate | None = None

    trades_active.labels(underlying=underlying).set(0)

    open_rows = await trade_q.get_open_trades(underlying)
    if open_rows:
        row = open_rows[0]
        recovered_trade = TradeRecord(
            trade_id=row["id"],
            trade_date=row["trade_date"],
            direction=row["direction"],
            wing_width=row["wing_width"],
            center_strike=float(row["center_strike"]),
            lower_strike=float(row["lower_strike"]),
            upper_strike=float(row["upper_strike"]),
            entry_price=float(row["entry_price"]),
            entry_time=row["entry_time"],
            lower_symbol=row.get("lower_symbol") or "",
            center_symbol=row.get("center_symbol") or "",
            upper_symbol=row.get("upper_symbol") or "",
            quantity=row.get("quantity") or 1,
            status=row.get("status") or "OPEN",
        )
        recovered_candidate = ButterflyCandidate(
            direction=recovered_trade.direction,
            wing_width=recovered_trade.wing_width,
            center_strike=recovered_trade.center_strike,
            lower_strike=recovered_trade.lower_strike,
            upper_strike=recovered_trade.upper_strike,
            cost=recovered_trade.entry_price,
            max_profit=0.0,
            reward_risk=0.0,
            lower_be=0.0,
            upper_be=0.0,
            distance_from_spot=0.0,
            spot_price=0.0,
            lower_symbol=recovered_trade.lower_symbol,
            center_symbol=recovered_trade.center_symbol,
            upper_symbol=recovered_trade.upper_symbol,
        )
        trades_active.labels(underlying=underlying).set(len(open_rows))
        log.info("recovered_open_trade", trade_id=recovered_trade.trade_id, underlying=underlying)

    # Initialize daily counters from DB so metrics survive restarts
    today = dt.date.today()
    today_trades = await trade_q.get_trades_for_date(today, underlying)
    daily_trade_count.labels(underlying=underlying).set(len(today_trades))
    await risk_engine.sync_trade_count(len(today_trades), today)
    realized_pnl = sum(float(t["pnl"]) for t in today_trades if t.get("pnl") is not None)
    daily_pnl.labels(underlying=underlying).set(realized_pnl)

    # Seed candidates_found from the most recent scan today
    last_scan_count = await db.pool.fetchval(
        """
        SELECT COUNT(*) FROM butterfly_candidates
        WHERE underlying = $1
          AND scan_time = (
              SELECT MAX(scan_time) FROM butterfly_candidates
              WHERE underlying = $1 AND scan_time::date = CURRENT_DATE
          )
        """,
        underlying,
    )
    if last_scan_count:
        butterfly_candidates_found.labels(underlying=underlying).set(last_scan_count)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(collector.run_loop(), name="collector")
            tg.create_task(
                entry_loop(trade_service, position_service, recovered_trade, recovered_candidate),
                name="entry_loop",
            )
            tg.create_task(daily_reset_loop(risk_q, config.strategy.underlying), name="daily_reset")
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
