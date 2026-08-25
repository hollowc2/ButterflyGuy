from __future__ import annotations

import asyncio
import datetime as dt
import os
import signal
from unittest.mock import AsyncMock, Mock, call

import pytest
from schwab_gateway_sdk.config import GatewayClientSettings

from butterfly_guy.core.config import (
    AppConfig,
    ExecutionSettings,
    RiskSettings,
    SchwabSettings,
    StrategySettings,
)
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.providers import (
    DirectSchwabMarketDataProvider,
    GatewayAuthoritativeMarketDataProvider,
)
from butterfly_guy.execution.order_manager import (
    AmbiguousOrderError,
    BrokerFillError,
    TerminalOrderError,
)
from butterfly_guy.gateway_client.shadow import ShadowComparingMarketDataProvider
from butterfly_guy.scripts.run_live import (
    BrokerStateGate,
    _assert_broker_state_matches_db,
    _assert_live_config_supported,
    _broker_option_positions,
    _build_collector_market_data,
    _close_runtime_resources,
    _order_symbols,
    _reconcile_broker_state,
    broker_reconciler_loop,
    entry_loop,
    install_shutdown_handler,
    token_reload_loop,
)
from butterfly_guy.services.position_service import SettlementEvidenceError

LOWER = "SPXW  260625C06000000"
CENTER = "SPXW  260625C06050000"
UPPER = "SPXW  260625C06100000"
OPEN_TRADE = {
    "lower_symbol": LOWER,
    "center_symbol": CENTER,
    "upper_symbol": UPPER,
    "quantity": 1,
}


def test_collector_market_data_defaults_to_direct_without_a_gateway_client(
    monkeypatch,
):
    for name in (
        "SCHWAB_ACCESS_MODE",
        "SCHWAB_GATEWAY_URL",
        "SCHWAB_GATEWAY_API_KEY",
        "SCHWAB_GATEWAY_SHADOW_READS",
    ):
        monkeypatch.delenv(name, raising=False)
    gateway_constructor = Mock()
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.GatewayMarketDataClient",
        gateway_constructor,
    )

    provider, shadow, gateway = _build_collector_market_data(Mock())

    assert isinstance(provider, DirectSchwabMarketDataProvider)
    assert shadow is None
    assert gateway is None
    gateway_constructor.assert_not_called()


@pytest.mark.asyncio
async def test_collector_market_data_shadow_is_opt_in_and_direct_authoritative(
    monkeypatch,
):
    schwab = Mock(get_spot_price=AsyncMock(return_value=6123.45))
    gateway = Mock(get_spot=AsyncMock(side_effect=RuntimeError("gateway unavailable")))
    gateway_constructor = Mock(return_value=gateway)
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.GatewayMarketDataClient",
        gateway_constructor,
    )
    settings = GatewayClientSettings(
        SCHWAB_ACCESS_MODE="direct",
        SCHWAB_GATEWAY_SHADOW_READS="true",
        SCHWAB_GATEWAY_URL="http://gateway:8011",
        SCHWAB_GATEWAY_API_KEY="internal-key",
    )

    provider, shadow, configured_gateway = _build_collector_market_data(
        schwab, settings
    )

    assert isinstance(provider, ShadowComparingMarketDataProvider)
    assert shadow is provider
    assert configured_gateway is gateway
    assert await provider.get_spot_price("$XSP") == 6123.45
    await provider.wait_for_shadow_reads()
    schwab.get_spot_price.assert_awaited_once_with("$XSP")
    gateway.get_spot.assert_awaited_once_with("$XSP")


def test_run_live_gateway_mode_is_authoritative_without_shadow(monkeypatch):
    gateway = AsyncMock()
    constructor = Mock(return_value=gateway)
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.GatewayMarketDataClient", constructor
    )
    settings = GatewayClientSettings(
        SCHWAB_ACCESS_MODE="gateway",
        SCHWAB_GATEWAY_URL="http://gateway:8011",
        SCHWAB_GATEWAY_API_KEY="internal-key",
    )

    provider, shadow, configured_gateway = _build_collector_market_data(Mock(), settings)

    assert isinstance(provider, GatewayAuthoritativeMarketDataProvider)
    assert shadow is None
    assert configured_gateway is gateway
    constructor.assert_called_once_with("http://gateway:8011", "internal-key")


@pytest.mark.asyncio
async def test_runtime_cleanup_drains_shadow_before_closing_clients_and_db():
    events: list[str] = []

    shadow = Mock(
        wait_for_shadow_reads=AsyncMock(side_effect=lambda: events.append("shadow"))
    )
    gateway = Mock(close=AsyncMock(side_effect=lambda: events.append("gateway")))
    schwab = Mock(close=AsyncMock(side_effect=lambda: events.append("schwab")))
    db = Mock(close=AsyncMock(side_effect=lambda: events.append("db")))

    await _close_runtime_resources(shadow, gateway, schwab, db)

    assert events == ["shadow", "gateway", "schwab", "db"]


@pytest.mark.asyncio
async def test_runtime_cleanup_closes_every_resource_when_shadow_drain_fails():
    shadow = Mock(
        wait_for_shadow_reads=AsyncMock(side_effect=RuntimeError("drain failed"))
    )
    gateway = Mock(close=AsyncMock())
    schwab = Mock(close=AsyncMock())
    db = Mock(close=AsyncMock())

    with pytest.raises(RuntimeError, match="drain failed"):
        await _close_runtime_resources(shadow, gateway, schwab, db)

    gateway.close.assert_awaited_once_with()
    schwab.close.assert_awaited_once_with()
    db.close.assert_awaited_once_with()


def _synthetic_position(symbol, *, long=0, short=0):
    return {
        "longQuantity": long,
        "shortQuantity": short,
        "instrument": {"assetType": "OPTION", "symbol": symbol},
    }


def _synthetic_butterfly_snapshot(
    *, quantity=1, center_long=0, center_short=None, extra=()
):
    center_short = 2 * quantity if center_short is None else center_short
    return {
        "securitiesAccount": {
            "positions": [
                _synthetic_position(LOWER, long=quantity),
                _synthetic_position(CENTER, long=center_long, short=center_short),
                _synthetic_position(UPPER, long=quantity),
                *extra,
            ]
        }
    }


def test_broker_option_positions_keep_signed_quantity_for_matching_options():
    snapshot = {
        "securitiesAccount": {
            "positions": [
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06000000",
                    },
                },
                {
                    "longQuantity": 1,
                    "instrument": {"assetType": "EQUITY", "symbol": "SPY"},
                },
                {
                    "shortQuantity": 2,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625P05900000",
                    },
                },
            ]
        }
    }

    assert _broker_option_positions(snapshot, "SPX") == {
        "SPXW  260625C06000000": 1,
        "SPXW  260625P05900000": -2,
    }


def test_order_symbols_walks_child_orders():
    order = {
        "orderLegCollection": [
            {"instrument": {"symbol": "SPXW  260625C06000000"}}
        ],
        "childOrderStrategies": [
            {
                "orderLegCollection": [
                    {"instrument": {"symbol": "SPXW  260625C06100000"}}
                ]
            }
        ],
    }

    assert _order_symbols(order) == {
        "SPXW  260625C06000000",
        "SPXW  260625C06100000",
    }


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_broker_position_without_open_trade():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06000000",
                    },
                }
            ]
        }
    }
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="DB has no OPEN trade"):
        await _assert_broker_state_matches_db(schwab, "SPX", [])


@pytest.mark.asyncio
async def test_startup_reconciliation_failure_alerts_without_broker_details():
    schwab = AsyncMock()
    schwab.get_account_snapshot.side_effect = RuntimeError("account identifier redacted")
    critical_notifier = Mock(notify_critical=AsyncMock(return_value=False))

    with pytest.raises(RuntimeError, match="identifier redacted"):
        await _reconcile_broker_state(
            schwab,
            "SPX",
            [],
            None,
            None,
            critical_notifier,
        )

    critical_notifier.notify_critical.assert_awaited_once_with("reconciliation_failure")


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_open_trade_when_broker_flat():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="broker is flat"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [OPEN_TRADE],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_allows_posted_expiration_settlement(monkeypatch):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = []
    schwab.get_transactions_for_day.return_value = [{"settlement": "redacted"}]
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.broker_cash_settlement_from_transactions",
        lambda transactions, trade: Mock() if transactions and trade.trade_id == 177 else None,
    )
    trade = {
        **OPEN_TRADE,
        "id": 177,
        "trade_date": dt.date(2026, 7, 13),
        "direction": "CALL",
        "lower_strike": 6000,
        "center_strike": 6050,
        "upper_strike": 6100,
        "entry_price": 1.0,
    }

    await _assert_broker_state_matches_db(
        schwab,
        "SPX",
        [trade],
        trade_date=dt.date(2026, 7, 14),
    )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_incomplete_db_butterfly():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                _synthetic_position(LOWER, long=1),
                _synthetic_position(UPPER, long=1),
            ]
        }
    }
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="missing leg symbol"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [{"lower_symbol": LOWER, "upper_symbol": UPPER, "quantity": 1}],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_zero_quantity_db_butterfly():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot()
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="invalid leg symbols or quantity"):
        await _assert_broker_state_matches_db(
            schwab,
            "SPX",
            [{**OPEN_TRADE, "quantity": 0}],
        )


@pytest.mark.asyncio
async def test_startup_reconciliation_blocks_extra_broker_leg():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        extra=(_synthetic_position("SPXW  260625C06150000", long=1),)
    )
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="unexpected broker leg symbol"):
        await _assert_broker_state_matches_db(schwab, "SPX", [OPEN_TRADE])


@pytest.mark.asyncio
async def test_startup_reconciliation_allows_exact_signed_butterfly_ratio():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(quantity=2)
    schwab.get_todays_orders.return_value = []

    await _assert_broker_state_matches_db(
        schwab, "SPX", [{**OPEN_TRADE, "quantity": 2}]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("long_quantity", "short_quantity"),
    [(2, 0), (0, 1), (0, 3)],
    ids=["wrong-sign", "partial", "oversized"],
)
async def test_startup_reconciliation_blocks_wrong_center_quantity(
    long_quantity, short_quantity
):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        center_long=long_quantity, center_short=short_quantity
    )
    schwab.get_todays_orders.return_value = []

    with pytest.raises(RuntimeError, match="quantity mismatch"):
        await _assert_broker_state_matches_db(schwab, "SPX", [OPEN_TRADE])


@pytest.mark.asyncio
async def test_runtime_reconciliation_sets_gate_unsafe_for_wrong_ratio(monkeypatch):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = _synthetic_butterfly_snapshot(
        center_short=1
    )
    schwab.get_todays_orders.return_value = []
    trades = AsyncMock()
    trades.get_open_trades.return_value = [OPEN_TRADE]
    intents = AsyncMock()
    intents.intents_for_day.return_value = []
    gate = BrokerStateGate()

    async def stop_after_one_iteration(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(asyncio, "sleep", stop_after_one_iteration)
    with pytest.raises(asyncio.CancelledError):
        await broker_reconciler_loop(schwab, "SPX", trades, intents, gate)

    assert gate.unsafe
    assert "quantity mismatch" in gate.reason


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["broker authentication failed", "database unavailable"])
async def test_runtime_reconciliation_degrades_readiness_on_dependency_failure(
    monkeypatch, failure
):
    schwab = AsyncMock()
    trades = AsyncMock()
    intents = AsyncMock()
    gate = BrokerStateGate()
    if failure.startswith("broker"):
        trades.get_open_trades.return_value = []
        schwab.get_account_snapshot.side_effect = RuntimeError(failure)
    else:
        trades.get_open_trades.side_effect = RuntimeError(failure)

    async def stop_after_one_iteration(_):
        raise asyncio.CancelledError

    set_readiness(None)
    monkeypatch.setattr(asyncio, "sleep", stop_after_one_iteration)
    critical_notifier = Mock(notify_critical=AsyncMock(return_value=False))
    with pytest.raises(asyncio.CancelledError):
        await broker_reconciler_loop(
            schwab,
            "SPX",
            trades,
            intents,
            gate,
            critical_notifier=critical_notifier,
        )

    assert gate.reason == failure
    assert readiness_snapshot() == (False, "broker_reconciliation_unsafe")
    critical_notifier.notify_critical.assert_awaited_once_with("reconciliation_failure")
    set_readiness(None)


@pytest.mark.asyncio
async def test_runtime_reconciliation_resolution_rearms_alert(monkeypatch):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = []
    trades = AsyncMock()
    trades.get_open_trades.side_effect = [RuntimeError("database unavailable"), []]
    intents = AsyncMock()
    intents.intents_for_day.return_value = []
    gate = BrokerStateGate()
    critical_notifier = Mock(
        notify_critical=AsyncMock(),
        resolve_critical=AsyncMock(),
        retry_pending_resolutions=AsyncMock(),
    )
    sleeps = 0

    async def stop_after_recovery(_):
        nonlocal sleeps
        sleeps += 1
        if sleeps == 2:
            raise asyncio.CancelledError

    set_readiness(None)
    monkeypatch.setattr(asyncio, "sleep", stop_after_recovery)
    with pytest.raises(asyncio.CancelledError):
        await broker_reconciler_loop(
            schwab,
            "SPX",
            trades,
            intents,
            gate,
            critical_notifier=critical_notifier,
        )

    critical_notifier.notify_critical.assert_awaited_once_with("reconciliation_failure")
    critical_notifier.resolve_critical.assert_awaited_once_with("reconciliation_failure")
    critical_notifier.retry_pending_resolutions.assert_awaited_once_with()
    assert not gate.unsafe
    assert readiness_snapshot() == (True, None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [TerminalOrderError("REJECTED", "redacted"), AmbiguousOrderError("unknown")],
)
async def test_entry_loop_stops_after_unsafe_order_error(monkeypatch, error):
    trade_service = Mock()
    trade_service.attempt_entry = AsyncMock(side_effect=error)
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)

    critical_notifier = Mock(notify_critical=AsyncMock())
    await entry_loop(trade_service, Mock(), critical_notifier=critical_notifier)

    trade_service.attempt_entry.assert_awaited_once()
    critical_notifier.notify_critical.assert_awaited_once_with("broker_ambiguity")
    assert readiness_snapshot() == (False, "broker_order_state_unsafe")
    set_readiness(None)


@pytest.mark.asyncio
async def test_entry_loop_repeated_errors_degrade_and_recover(
    monkeypatch,
):
    trade_service = Mock(
        config=Mock(strategy=Mock(underlying="SPX")),
        decision_queries=Mock(log_event=AsyncMock()),
    )
    trade_service.attempt_entry = AsyncMock(
        side_effect=[
            RuntimeError("invalid SQL"),
            RuntimeError("invalid SQL"),
            RuntimeError("invalid SQL"),
            RuntimeError("invalid SQL"),
            None,
            RuntimeError("invalid SQL"),
            RuntimeError("invalid SQL"),
            RuntimeError("invalid SQL"),
        ]
    )
    metric = Mock()
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.entry_loop_errors.labels",
        Mock(return_value=metric),
    )
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)

    sleeps = 0

    async def stop_after_two_episodes(_):
        nonlocal sleeps
        sleeps += 1
        if sleeps == 5:
            assert readiness_snapshot() == (True, None)
        if sleeps == 8:
            raise asyncio.CancelledError

    set_readiness(None)
    monkeypatch.setattr(asyncio, "sleep", stop_after_two_episodes)
    with pytest.raises(asyncio.CancelledError):
        await entry_loop(trade_service, Mock())

    assert trade_service.attempt_entry.await_count == 8
    assert metric.inc.call_count == 7
    assert trade_service.decision_queries.log_event.await_count == 7
    assert trade_service.decision_queries.log_event.await_args_list[0] == call(
        "entry_loop_error",
        {"error": "invalid SQL", "consecutive_failures": 1},
        underlying="SPX",
    )
    assert readiness_snapshot() == (False, "entry_loop_repeated_failures")
    set_readiness(None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error,condition",
    [
        (
            BrokerFillError("missing execution evidence"),
            "broker_ambiguity",
        ),
        (
            SettlementEvidenceError("missing settlement evidence"),
            "settlement_failure",
        ),
    ],
)
async def test_entry_loop_alerts_after_monitor_safety_error(
    monkeypatch, error, condition
):
    trade_service = Mock(attempt_entry=AsyncMock())
    position_service = Mock()
    position_service.monitor_loop.return_value = _never_awaited()
    monitor_task = Mock()
    monitor_task.done.return_value = True
    monitor_task.exception.return_value = error

    def create_task(coro, **_kwargs):
        coro.close()
        return monitor_task

    monkeypatch.setattr(asyncio, "create_task", create_task)
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)

    critical_notifier = Mock(notify_critical=AsyncMock())
    await entry_loop(
        trade_service,
        position_service,
        recovered_trade=Mock(trade_id=7),
        recovered_candidate=Mock(),
        critical_notifier=critical_notifier,
    )

    trade_service.attempt_entry.assert_not_awaited()
    critical_notifier.notify_critical.assert_awaited_once_with(condition)
    assert readiness_snapshot() == (False, "broker_order_state_unsafe")
    set_readiness(None)


async def _never_awaited():
    pass


def test_live_config_rejects_non_spx_live_money(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="NDX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
    )

    with pytest.raises(RuntimeError, match="SPX/XSP-canary-only"):
        _assert_live_config_supported(config)


def test_live_config_rejects_xsp_without_canary_confirmation(monkeypatch):
    monkeypatch.delenv("LIVE_XSP_CANARY", raising=False)
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "50")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="XSP"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
        risk=RiskSettings(max_daily_loss=50.0, max_position_size=1),
    )

    with pytest.raises(RuntimeError, match="LIVE_XSP_CANARY=true"):
        _assert_live_config_supported(config)


def test_live_config_allows_confirmed_xsp_canary(monkeypatch):
    monkeypatch.setenv("LIVE_XSP_CANARY", "true")
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "50")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="XSP"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
        risk=RiskSettings(max_daily_loss=50.0, max_position_size=1),
    )

    _assert_live_config_supported(config)


def test_live_config_rejects_spx_live_without_account_confirmation(monkeypatch):
    monkeypatch.delenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("LIVE_ACCOUNT_ALLOCATION", raising=False)
    monkeypatch.delenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", raising=False)
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="SPX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
    )

    with pytest.raises(RuntimeError, match="LIVE_EXPECTED_SCHWAB_ACCOUNT_ID"):
        _assert_live_config_supported(config)


def test_live_config_allows_spx_live_when_explicitly_confirmed(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECTED_SCHWAB_ACCOUNT_ID", "123")
    monkeypatch.setenv("LIVE_ACCOUNT_ALLOCATION", "20000")
    monkeypatch.setenv("LIVE_MAX_ACCOUNT_DAILY_LOSS", "500")
    config = AppConfig(
        schwab=SchwabSettings(account_id="123"),
        strategy=StrategySettings(underlying="SPX"),
        execution=ExecutionSettings(paper_trading=False, allow_live_trading=True),
        risk=RiskSettings(max_daily_loss=500.0),
    )

    _assert_live_config_supported(config)


@pytest.mark.asyncio
async def test_sigterm_cancels_supervised_loops_and_task_group_exits_cleanly():
    """SIGTERM must unwind the TaskGroup without reporting a shutdown as an error.

    The app is PID 1 in its container, so an uncaught SIGTERM is discarded and
    Docker escalates to SIGKILL (exit 137). Cancelling the children lets the
    group exit normally, which is what lets main()'s finally block close the pool.
    """
    running = asyncio.Event()
    cleanup_ran = False

    async def forever() -> None:
        running.set()
        while True:
            await asyncio.sleep(3600)

    try:
        async with asyncio.TaskGroup() as tg:
            supervised = [
                tg.create_task(forever(), name="loop-a"),
                tg.create_task(forever(), name="loop-b"),
            ]
            install_shutdown_handler(supervised)
            await running.wait()
            os.kill(os.getpid(), signal.SIGTERM)
    finally:
        cleanup_ran = True
        asyncio.get_running_loop().remove_signal_handler(signal.SIGTERM)

    # Reaching here at all means the group raised no ExceptionGroup.
    assert cleanup_ran
    assert all(task.cancelled() for task in supervised)


@pytest.mark.asyncio
async def test_shutdown_handler_tolerates_already_finished_tasks():
    async def done_immediately() -> None:
        return None

    task = asyncio.create_task(done_immediately())
    await task

    try:
        install_shutdown_handler([task])
        os.kill(os.getpid(), signal.SIGTERM)
        await asyncio.sleep(0)
    finally:
        asyncio.get_running_loop().remove_signal_handler(signal.SIGTERM)

    assert not task.cancelled()


@pytest.mark.asyncio
async def test_token_reload_loop_survives_a_failed_reload(monkeypatch):
    """A reload failure must not take the trading loop down with it.

    The old client still holds a working access token, so the correct response to a
    bad document is to log and try again -- not to fault the TaskGroup.
    """
    outcomes = [RuntimeError("bad document"), True]
    calls: list[str] = []

    async def reload_if_reauthorized():
        outcome = outcomes[len(calls)]
        calls.append("called")
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    schwab = Mock(reload_if_reauthorized=reload_if_reauthorized)
    token_reload_gate = BrokerStateGate()
    errors = Mock()
    monkeypatch.setattr("butterfly_guy.scripts.run_live.log.error", errors)

    task = asyncio.create_task(token_reload_loop(schwab, token_reload_gate, interval=0))
    while len(calls) < 2:
        await asyncio.sleep(0)
    task.cancel()

    assert len(calls) == 2, "loop stopped after the failure instead of retrying"
    errors.assert_called_once()
    assert errors.call_args.args[0] == "schwab_token_reload_failed"
    assert not token_reload_gate.unsafe


@pytest.mark.asyncio
async def test_failed_token_reload_blocks_new_entries(monkeypatch):
    async def reload_if_reauthorized():
        raise RuntimeError("candidate token rejected")

    token_reload_gate = BrokerStateGate()
    reload_task = asyncio.create_task(
        token_reload_loop(
            Mock(reload_if_reauthorized=reload_if_reauthorized),
            token_reload_gate,
            interval=0,
        )
    )
    while not token_reload_gate.unsafe:
        await asyncio.sleep(0)
    reload_task.cancel()

    trade_service = Mock(attempt_entry=AsyncMock())
    monkeypatch.setattr("butterfly_guy.scripts.run_live.is_market_open", lambda: True)

    async def stop_after_blocked_entry(_):
        raise asyncio.CancelledError

    monkeypatch.setattr(asyncio, "sleep", stop_after_blocked_entry)
    with pytest.raises(asyncio.CancelledError):
        await entry_loop(
            trade_service,
            Mock(),
            token_reload_gate=token_reload_gate,
        )

    trade_service.attempt_entry.assert_not_awaited()
    set_readiness(None)
