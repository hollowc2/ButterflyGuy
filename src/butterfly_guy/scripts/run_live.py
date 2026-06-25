"""Main orchestrator: runs collector + trading + position monitor concurrently."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
from typing import Any

from dotenv import dotenv_values

from butterfly_guy.core.config import AppConfig, load_config
from butterfly_guy.core.logging import get_logger, setup_logging
from butterfly_guy.core.metrics import (
    butterfly_candidates_found,
    daily_pnl,
    daily_trade_count,
    start_metrics_server,
    trades_active,
)
from butterfly_guy.core.time_utils import (
    is_market_open,
    is_trading_day,
    market_close_time,
    now_eastern,
)
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
    MonitoringLegQueries,
    OrderIntentQueries,
    RiskQueries,
    SpotQueries,
    TentQueries,
    TradeQueries,
)
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder
from butterfly_guy.execution.order_manager import (
    CANCEL_PENDING_STATUSES,
    PARTIAL_FILL_STATUSES,
    WORKING_ORDER_STATUSES,
    OrderManager,
    PartialFillError,
)
from butterfly_guy.reports.live_performance import trade_pnl_dollars
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.services.notifier import DiscordNotifier, TelegramNotifier
from butterfly_guy.services.position_service import PositionService
from butterfly_guy.services.trade_service import TradeService
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter
from butterfly_guy.strategy.gap_regime_filter import GapRegimeFilter
from butterfly_guy.strategy.regime_classifier import RegimeClassifier

log = get_logger("run_live")

LIVE_UNDERLYING = "SPX"


def _matches_underlying(symbol: str, underlying: str) -> bool:
    normalized = symbol.upper().lstrip("$")
    return normalized.startswith(underlying.upper())


def _broker_option_position_symbols(
    account_snapshot: dict[str, Any], underlying: str
) -> set[str]:
    acct = account_snapshot.get("securitiesAccount", account_snapshot)
    symbols: set[str] = set()
    for pos in acct.get("positions") or []:
        instrument = pos.get("instrument") or {}
        if instrument.get("assetType") != "OPTION":
            continue
        qty = float(pos.get("longQuantity") or 0) + float(pos.get("shortQuantity") or 0)
        if qty == 0:
            continue
        symbol = str(instrument.get("symbol") or "")
        underlier = str(instrument.get("underlyingSymbol") or "")
        if _matches_underlying(symbol, underlying) or _matches_underlying(underlier, underlying):
            symbols.add(symbol)
    return symbols


def _order_symbols(order: dict[str, Any]) -> set[str]:
    symbols: set[str] = set()
    for leg in order.get("orderLegCollection") or []:
        instrument = leg.get("instrument") or {}
        symbol = instrument.get("symbol")
        if symbol:
            symbols.add(str(symbol))
    for child in order.get("childOrderStrategies") or []:
        symbols.update(_order_symbols(child))
    return symbols


def _open_trade_symbols(open_rows: list[dict]) -> set[str]:
    symbols: set[str] = set()
    for row in open_rows:
        for key in ("lower_symbol", "center_symbol", "upper_symbol"):
            if row.get(key):
                symbols.add(str(row[key]))
    return symbols


def _order_id(order: dict[str, Any]) -> str:
    return str(order.get("orderId") or order.get("order_id") or "")


def _intent_order_ids(intents: list[dict[str, Any]]) -> set[str]:
    return {
        str(intent["broker_order_id"])
        for intent in intents
        if intent.get("broker_order_id")
    }


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return {}


def _snapshot_symbols(snapshot: dict[str, Any]) -> set[str]:
    return {
        str(snapshot[key])
        for key in ("lower_symbol", "center_symbol", "upper_symbol")
        if snapshot.get(key)
    }


def _parse_broker_time(value: Any) -> dt.datetime | None:
    if isinstance(value, dt.datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def _explicit_fill_details(order: dict[str, Any]) -> tuple[float, dt.datetime] | None:
    if order.get("status") != "FILLED":
        return None
    activities = order.get("orderActivityCollection") or [{}]
    executions = activities[0].get("executionLegs") or [{}]
    price = (
        order.get("filledPrice")
        or order.get("averageFillPrice")
        or order.get("averagePrice")
    )
    fill_time = _parse_broker_time(
        order.get("closeTime")
        or order.get("enteredTime")
        or executions[0].get("time")
    )
    if price is None or fill_time is None:
        return None
    return float(price), fill_time


async def _repair_filled_entry_intent(
    intent: dict[str, Any],
    broker_symbols: set[str],
    trade_queries: TradeQueries,
) -> dict[str, Any]:
    payload = _json_dict(intent.get("raw_broker_payload"))
    fill = _explicit_fill_details(payload)
    snapshot = _json_dict(intent.get("candidate_snapshot"))
    if fill is None:
        raise RuntimeError("filled entry intent missing explicit fill price/time")
    if _snapshot_symbols(snapshot) != broker_symbols:
        raise RuntimeError("filled entry intent legs do not match broker positions")

    fill_price, fill_time = fill
    trade_id = await trade_queries.insert_trade(
        {
            "underlying": intent["underlying"],
            "trade_date": intent["trade_date"],
            "direction": snapshot["direction"],
            "wing_width": snapshot["wing_width"],
            "center_strike": snapshot["center_strike"],
            "lower_strike": snapshot["lower_strike"],
            "upper_strike": snapshot["upper_strike"],
            "entry_price": fill_price,
            "entry_time": fill_time,
            "lower_symbol": snapshot.get("lower_symbol"),
            "center_symbol": snapshot.get("center_symbol"),
            "upper_symbol": snapshot.get("upper_symbol"),
            "quantity": intent.get("quantity") or 1,
            "metadata": {"broker_reconciled_entry_intent_id": intent["id"]},
        }
    )
    return {**intent, "trade_id": trade_id}


async def _repair_filled_exit_intent(
    intent: dict[str, Any],
    open_trade: dict[str, Any],
    trade_queries: TradeQueries,
) -> None:
    payload = _json_dict(intent.get("raw_broker_payload"))
    fill = _explicit_fill_details(payload)
    if fill is None:
        raise RuntimeError("filled exit intent missing explicit fill price/time")
    fill_price, fill_time = fill
    entry_price = float(open_trade["entry_price"])
    pnl = fill_price - entry_price
    snapshot = _json_dict(intent.get("candidate_snapshot"))
    await trade_queries.close_trade(
        int(open_trade["id"]),
        fill_price,
        fill_time,
        str(snapshot.get("exit_reason") or "broker_reconciled_exit"),
        pnl,
        float(open_trade.get("peak_value") or entry_price),
        metadata={"broker_reconciled_exit_intent_id": intent["id"]},
    )


class BrokerStateGate:
    def __init__(self) -> None:
        self.reason: str | None = None

    @property
    def unsafe(self) -> bool:
        return self.reason is not None

    def set_unsafe(self, reason: str) -> None:
        self.reason = reason

    def clear(self) -> None:
        self.reason = None


async def _assert_broker_state_matches_db(
    schwab: SchwabClientWrapper,
    underlying: str,
    open_rows: list[dict],
    intent_queries: OrderIntentQueries | None = None,
    trade_queries: TradeQueries | None = None,
) -> None:
    account_snapshot = await schwab.get_account_snapshot()
    broker_symbols = _broker_option_position_symbols(account_snapshot, underlying)
    expected_symbols = _open_trade_symbols(open_rows)
    intents = (
        await intent_queries.intents_for_day(underlying, dt.date.today())
        if intent_queries is not None
        else []
    )
    known_order_ids = _intent_order_ids(intents)

    todays_orders = await schwab.get_todays_orders()
    if intent_queries is not None:
        intent_by_order_id = {
            str(intent["broker_order_id"]): intent
            for intent in intents
            if intent.get("broker_order_id")
        }
        for order in todays_orders:
            intent = intent_by_order_id.get(_order_id(order))
            if intent is not None and order.get("status"):
                intent["status"] = str(order["status"])
                intent["raw_broker_payload"] = order
                await intent_queries.update_broker_status(
                    int(intent["id"]), str(order["status"]), order
                )

    working_orders = [
        order for order in todays_orders
        if order.get("status") in WORKING_ORDER_STATUSES | CANCEL_PENDING_STATUSES
        and any(_matches_underlying(sym, underlying) for sym in _order_symbols(order))
        and _order_id(order) not in known_order_ids
    ]
    if working_orders:
        raise RuntimeError(
            f"Broker has {len(working_orders)} unknown working {underlying} order(s); "
            "refusing live startup"
        )

    unsafe_known = [
        order for order in todays_orders
        if _order_id(order) in known_order_ids
        and order.get("status") in PARTIAL_FILL_STATUSES | CANCEL_PENDING_STATUSES
    ]
    if unsafe_known:
        raise RuntimeError(
            f"Broker has {len(unsafe_known)} partial/cancel-pending bot-owned "
            f"{underlying} order(s); manual reconciliation required"
        )

    if broker_symbols and not open_rows:
        filled_entries = [
            intent for intent in intents
            if intent.get("side") == "ENTRY"
            and intent.get("status") == "FILLED"
            and not intent.get("trade_id")
        ]
        if trade_queries is not None and len(filled_entries) == 1:
            repaired = await _repair_filled_entry_intent(
                filled_entries[0],
                broker_symbols,
                trade_queries,
            )
            if intent_queries is not None:
                await intent_queries.link_trade(int(repaired["id"]), int(repaired["trade_id"]))
            log.warning(
                "broker_filled_entry_repaired",
                intent_id=repaired["id"],
                trade_id=repaired["trade_id"],
            )
            return
        raise RuntimeError(
            f"Broker has {len(broker_symbols)} {underlying} option position(s) "
            "but DB has no OPEN trade"
        )
    if open_rows and not broker_symbols:
        filled_exits = [
            intent for intent in intents
            if intent.get("side") == "EXIT"
            and intent.get("status") == "FILLED"
            and intent.get("trade_id") in {row.get("id") for row in open_rows}
        ]
        if trade_queries is not None and len(open_rows) == 1 and len(filled_exits) == 1:
            await _repair_filled_exit_intent(filled_exits[0], open_rows[0], trade_queries)
            log.warning(
                "broker_filled_exit_repaired",
                intent_id=filled_exits[0]["id"],
                trade_id=open_rows[0]["id"],
            )
            return
        raise RuntimeError(
            f"DB has {len(open_rows)} OPEN {underlying} trade(s) but broker is flat"
        )
    if expected_symbols and not expected_symbols.issubset(broker_symbols):
        missing = sorted(expected_symbols - broker_symbols)
        raise RuntimeError(
            f"Broker positions missing DB OPEN leg symbol(s): {', '.join(missing)}"
        )


async def broker_reconciler_loop(
    schwab: SchwabClientWrapper,
    underlying: str,
    trade_queries: TradeQueries,
    intent_queries: OrderIntentQueries,
    gate: BrokerStateGate,
    interval_seconds: int = 15,
) -> None:
    while True:
        try:
            open_rows = await trade_queries.get_open_trades(underlying)
            await _assert_broker_state_matches_db(
                schwab,
                underlying,
                open_rows,
                intent_queries,
                trade_queries,
            )
            if gate.unsafe:
                log.info("broker_state_gate_cleared")
            gate.clear()
        except Exception as e:
            gate.set_unsafe(str(e))
            log.error("broker_state_unsafe", error=str(e))
        await asyncio.sleep(interval_seconds)


def _assert_live_config_supported(config: AppConfig) -> None:
    if config.execution.paper_trading:
        return
    if not config.execution.allow_live_trading:
        raise RuntimeError(
            "Live trading requires execution.allow_live_trading=true or ALLOW_LIVE_TRADING=true"
        )
    if config.strategy.underlying != LIVE_UNDERLYING:
        raise RuntimeError(
            f"Live trading is {LIVE_UNDERLYING}-only; "
            f"{config.strategy.underlying} must stay paper/research until explicitly approved"
        )


async def entry_loop(
    trade_service: TradeService,
    position_service: PositionService,
    recovered_trade: TradeRecord | None = None,
    recovered_candidate: ButterflyCandidate | None = None,
    recovered_peak: float | None = None,
    broker_gate: BrokerStateGate | None = None,
) -> None:
    """Periodically attempt entries during the entry window."""
    active_trade: TradeRecord | None = recovered_trade
    monitor_task: asyncio.Task | None = None

    if recovered_trade is not None and recovered_candidate is not None:
        log.info("resuming_monitor_for_recovered_trade", trade_id=recovered_trade.trade_id)
        monitor_task = asyncio.create_task(
            position_service.monitor_loop(
                recovered_trade,
                recovered_candidate,
                recovered_peak=recovered_peak,
            ),
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
                if isinstance(exc, PartialFillError):
                    log.error("entry_loop_stopped_unknown_broker_state")
                    return
            active_trade = None
            monitor_task = None

        # If no active position, try entry
        if active_trade is None:
            if broker_gate is not None and broker_gate.unsafe:
                log.error("entry_blocked_broker_state_unsafe", reason=broker_gate.reason)
                await asyncio.sleep(15)
                continue
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
                if isinstance(e, PartialFillError):
                    log.error("entry_loop_stopped_unknown_broker_state")
                    return

        await asyncio.sleep(15)


EOD_CHART_DELAY_MINUTES = 5


async def eod_chart_loop(position_service: PositionService) -> None:
    """Send deferred full-session EOD charts after the cash close."""
    while True:
        await asyncio.sleep(60)
        if position_service.notifier is None:
            continue

        now = now_eastern()
        if not is_trading_day(now.date()):
            continue

        close = market_close_time(now.date())
        eod_at = dt.datetime.combine(now.date(), close, tzinfo=now.tzinfo) + dt.timedelta(
            minutes=EOD_CHART_DELAY_MINUTES
        )
        eod_ready = now >= eod_at
        if not eod_ready:
            continue

        sent = await position_service.send_pending_eod_charts(now.date())
        if sent:
            log.info("eod_chart_batch_complete", sent=sent, trade_date=str(now.date()))


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
        daily_trade_count.labels(underlying=underlying).set(0)
        trades_active.labels(underlying=underlying).set(0)
        daily_pnl.labels(underlying=underlying).set(0)
        log.info("daily_risk_reset", date=str(today))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml", help="Path to config YAML file")
    args = parser.parse_args()
    config = load_config(args.config)
    setup_logging(config.monitoring.log_level, json_output=True)

    _assert_live_config_supported(config)

    log.info(
        "live_trading_starting",
        underlying=config.strategy.underlying,
        config_path=args.config,
        strike_selection_method=config.entry.strike_selection_method,
        wing_widths=config.strategy.wing_widths,
        vix_width_buckets=[
            {"vix_max": bucket.vix_max, "widths": bucket.widths}
            for bucket in (config.strategy.vix_width_buckets or [])
        ],
        rr_min=config.strategy.rr_min,
        rr_max=config.strategy.rr_max,
        rr_target=config.strategy.rr_target,
        center_tolerance=config.entry.center_tolerance,
    )
    start_metrics_server(config.monitoring.metrics_port, underlying=config.strategy.underlying)

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
    intent_q = OrderIntentQueries(db)
    monitoring_leg_q = MonitoringLegQueries(db)
    candidate_q = CandidateQueries(db)
    daily_bar_q = DailyBarQueries(db)
    tent_q = TentQueries(db)

    # Discord trade notifications for SPX only (paper and live).
    # NDX/XSP stay on logs/metrics; risk warnings use Telegram.
    webhook = os.environ.get("DISCORD_WEBHOOK_URL") or dotenv_values(".env").get(
        "DISCORD_WEBHOOK_URL",
        "",
    )
    risk_notifier = TelegramNotifier()
    notifier = (
        DiscordNotifier(webhook)
        if webhook and config.strategy.underlying == "SPX"
        else None
    )

    # Classify today's market regime (must precede TradeService construction)
    regime_classifier = RegimeClassifier()
    lookback = regime_classifier.lookback_days
    recent_spx = await daily_bar_q.get_recent_closes(
        config.strategy.underlying, days=lookback + 5
    )
    vix_closes = await daily_bar_q.get_recent_closes("$VIX", days=1)
    vix_level = vix_closes[0] if vix_closes else 0.0
    regime = regime_classifier.classify(recent_spx, vix_level)
    log.info(
        "regime_classified",
        regime=regime.value,
        spx_bars=len(recent_spx),
        vix=vix_level,
    )

    gap_regime_filter = GapRegimeFilter(
        bull_call_bias=config.entry.bull_call_bias,
        min_gap_pct=config.entry.min_gap_pct,
    )

    # Build service objects
    risk_engine = RiskEngine(
        config.risk,
        risk_q,
        config.strategy.underlying,
        notifier=risk_notifier,
    )
    order_builder = ButterflyOrderBuilder()
    order_manager = OrderManager(
        config.execution,
        schwab,
        order_builder,
        config.strategy.underlying,
        intent_queries=intent_q,
    )

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
        notifier=notifier,
        regime=regime,
        gap_regime_filter=gap_regime_filter,
    )

    position_service = PositionService(
        config=config,
        schwab=schwab,
        order_manager=order_manager,
        risk_engine=risk_engine,
        trade_queries=trade_q,
        decision_queries=decision_q,
        chain_queries=chain_q,
        monitoring_leg_queries=monitoring_leg_q,
        tent_queries=tent_q,
        notifier=notifier,
    )

    collector = OptionChainCollector(
        config=config,
        schwab=schwab,
        chain_queries=chain_q,
        spot_queries=spot_q,
        daily_bar_queries=daily_bar_q,
    )

    if notifier:
        await notifier.notify_startup()

    # Recover any open trade and initialize daily metrics from DB
    underlying = config.strategy.underlying
    recovered_trade: TradeRecord | None = None
    recovered_candidate: ButterflyCandidate | None = None

    trades_active.labels(underlying=underlying).set(0)

    recovered_peak: float | None = None

    open_rows = await trade_q.get_open_trades(underlying)
    if not config.execution.paper_trading:
        await _assert_broker_state_matches_db(
            schwab, underlying, open_rows, intent_q, trade_q
        )
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
        # Restore persisted peak so drawdown thresholds are correct after restart
        raw_peak = row.get("peak_value")
        recovered_peak = float(raw_peak) if raw_peak is not None else None
        trades_active.labels(underlying=underlying).set(len(open_rows))
        log.info(
            "recovered_open_trade",
            trade_id=recovered_trade.trade_id,
            underlying=underlying,
            recovered_peak=recovered_peak,
        )

    # Initialize daily counters from DB so metrics survive restarts
    today = dt.date.today()
    today_trades = await trade_q.get_trades_for_date(today, underlying)
    daily_trade_count.labels(underlying=underlying).set(len(today_trades))
    await risk_engine.sync_trade_count(len(today_trades), today)
    realized_pnl = sum(
        trade_pnl_dollars(t["pnl"], int(t.get("quantity") or 1))
        for t in today_trades
        if t.get("pnl") is not None
    )

    # Sync risk state PnL — if an open trade was recovered, include its entry cost as
    # worst-case committed exposure so the daily loss budget is correctly consumed.
    if recovered_trade is not None:
        open_trade_entry = trade_pnl_dollars(
            recovered_trade.entry_price, recovered_trade.quantity
        )
        worst_case_pnl = realized_pnl - open_trade_entry
        await risk_engine.sync_realized_pnl(worst_case_pnl, today)
        log.info(
            "startup_pnl_sync_with_open_trade",
            realized_pnl=realized_pnl,
            open_trade_entry=open_trade_entry,
            worst_case_pnl=worst_case_pnl,
        )
    else:
        await risk_engine.sync_realized_pnl(realized_pnl, today)

    daily_pnl.labels(underlying=underlying).set(realized_pnl)
    broker_gate = BrokerStateGate()

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
                entry_loop(
                    trade_service,
                    position_service,
                    recovered_trade,
                    recovered_candidate,
                    recovered_peak,
                    broker_gate,
                ),
                name="entry_loop",
            )
            if not config.execution.paper_trading:
                tg.create_task(
                    broker_reconciler_loop(
                        schwab,
                        underlying,
                        trade_q,
                        intent_q,
                        broker_gate,
                    ),
                    name="broker_reconciler",
                )
            tg.create_task(daily_reset_loop(risk_q, config.strategy.underlying), name="daily_reset")
            if notifier:
                tg.create_task(eod_chart_loop(position_service), name="eod_charts")
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
