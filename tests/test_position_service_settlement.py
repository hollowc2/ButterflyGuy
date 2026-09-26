"""Tests for cash-settlement spot selection."""

import asyncio
import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import ProfitManagementSettings, TimeRegime
from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.data.schemas import TradeRecord
from butterfly_guy.execution import order_manager as order_manager_module
from butterfly_guy.position.position_manager import PositionState
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.services.position_service import (
    BrokerCashSettlement,
    PositionService,
    SettlementEvidenceError,
    _settlement_pending_alert_time,
    broker_cash_settlement_from_transactions,
    final_regular_session_close_from_candles,
)


def _candle(ts: dt.datetime, close: float) -> dict:
    return {
        "datetime": int(ts.astimezone(dt.timezone.utc).timestamp() * 1000),
        "close": close,
    }


def test_final_regular_session_close_uses_latest_regular_bar() -> None:
    session_date = dt.date(2026, 6, 16)
    candles = [
        _candle(dt.datetime(2026, 6, 16, 15, 58, tzinfo=EASTERN), 7514.46),
        _candle(dt.datetime(2026, 6, 16, 15, 59, tzinfo=EASTERN), 7511.57),
        _candle(dt.datetime(2026, 6, 16, 16, 1, tzinfo=EASTERN), 7508.68),
    ]

    result = final_regular_session_close_from_candles(candles, session_date)

    assert result is not None
    ts, close = result
    assert ts == dt.datetime(2026, 6, 16, 15, 59, tzinfo=EASTERN)
    assert close == 7511.57


def test_final_regular_session_close_accepts_bar_timestamped_at_close() -> None:
    session_date = dt.date(2026, 6, 16)
    candles = [
        _candle(dt.datetime(2026, 6, 16, 15, 59, tzinfo=EASTERN), 7516.38),
        _candle(dt.datetime(2026, 6, 16, 16, 0, tzinfo=EASTERN), 7511.57),
    ]

    result = final_regular_session_close_from_candles(candles, session_date)

    assert result is not None
    ts, close = result
    assert ts == dt.datetime(2026, 6, 16, 16, 0, tzinfo=EASTERN)
    assert close == 7511.57


def test_final_regular_session_close_returns_none_without_session_bar() -> None:
    session_date = dt.date(2026, 6, 16)
    candles = [
        _candle(dt.datetime(2026, 6, 16, 16, 1, tzinfo=EASTERN), 7508.68),
        _candle(dt.datetime(2026, 6, 15, 15, 59, tzinfo=EASTERN), 7554.29),
    ]

    assert final_regular_session_close_from_candles(candles, session_date) is None


@pytest.mark.asyncio
async def test_settlement_spot_uses_separate_market_data_provider() -> None:
    day = dt.date(2026, 6, 16)
    service = PositionService.__new__(PositionService)
    service.schwab = AsyncMock()
    service.market_data = AsyncMock()
    service.market_data.get_intraday_bars_for_day.return_value = [
        _candle(dt.datetime(2026, 6, 16, 16, 0, tzinfo=EASTERN), 7511.57)
    ]

    spot, source, timestamp = await service._settlement_spot_price("SPX", day)

    assert spot == 7511.57
    assert source == "market_data_final_regular_session_1m_close"
    assert timestamp == dt.datetime(2026, 6, 16, 16, 0, tzinfo=EASTERN)
    service.market_data.get_intraday_bars_for_day.assert_awaited_once_with(
        "$SPX",
        day,
        include_extended_hours=False,
    )
    service.schwab.get_intraday_bars_for_day.assert_not_awaited()


@pytest.mark.asyncio
async def test_settlement_spot_uses_prior_exact_session_after_midnight() -> None:
    session_day = dt.date(2026, 6, 16)
    service = PositionService.__new__(PositionService)
    service.schwab = AsyncMock()
    service.market_data = AsyncMock()
    service.market_data.get_intraday_bars_for_day.return_value = [
        _candle(dt.datetime(2026, 6, 16, 15, 59, tzinfo=EASTERN), 7511.57),
        _candle(dt.datetime(2026, 6, 17, 9, 30, tzinfo=EASTERN), 7525.0),
    ]

    spot, source, timestamp = await service._settlement_spot_price(
        "SPX",
        session_day,
    )

    assert spot == 7511.57
    assert source == "market_data_final_regular_session_1m_close"
    assert timestamp == dt.datetime(2026, 6, 16, 15, 59, tzinfo=EASTERN)
    service.market_data.get_intraday_bars_for_day.assert_awaited_once_with(
        "$SPX",
        session_day,
        include_extended_hours=False,
    )
    service.market_data.get_spot_price.assert_not_awaited()


@pytest.mark.asyncio
async def test_repeated_position_market_data_failures_mark_not_ready_and_keep_open() -> None:
    set_readiness(None)
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "XSP"
    service.market_data = AsyncMock()
    service.market_data.get_option_chain.side_effect = (
        RuntimeError("gateway unavailable"),
        RuntimeError("gateway unavailable"),
        RuntimeError("gateway unavailable"),
        asyncio.CancelledError(),
    )
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.notifier = None
    service.position_manager = MagicMock()
    service.state_machine = MagicMock()
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=AsyncMock())
    service.trade_queries = MagicMock()
    service._last_persisted_peak = 1.0
    service._last_profit_state = None
    day = dt.date(2026, 8, 24)
    trade = TradeRecord(trade_id=7, trade_date=day, entry_price=1.0)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date", return_value=day
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    ready, reason = readiness_snapshot()
    assert ready is False
    assert reason == "market_data_unavailable"
    service.position_manager.update_position_value.assert_not_called()
    service.trade_queries.close_trade.assert_not_called()
    assert any(
        call.args[0] == "position_market_data_unavailable"
        for call in service.decision_queries.log_event.await_args_list
    )
    set_readiness(None)


@pytest.mark.asyncio
async def test_validated_position_market_data_recovery_clears_readiness() -> None:
    set_readiness("market_data_unavailable")
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "XSP"
    service.market_data = AsyncMock()
    service.market_data.get_option_chain.side_effect = (
        RuntimeError("gateway unavailable"),
        {"putExpDateMap": {}},
        asyncio.CancelledError(),
    )
    service._extract_quotes = MagicMock(return_value={})
    position_state = MagicMock(peak_update_rejected=False, peak_value=1.0)
    service.position_manager = MagicMock(
        update_position_value=MagicMock(return_value=position_state)
    )
    service.state_machine = MagicMock()
    service.state_machine.evaluate.return_value = None
    service.state_machine.state.name = "INITIAL"
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.notifier = None
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=AsyncMock())
    service.trade_queries = MagicMock(update_peak_value=AsyncMock())
    service._last_persisted_peak = 1.0
    service._last_profit_state = None
    day = dt.date(2026, 8, 24)
    trade = TradeRecord(trade_id=7, trade_date=day, entry_price=1.0)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date", return_value=day
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    assert readiness_snapshot() == (True, None)
    assert any(
        call.args[0] == "position_market_data_recovered"
        for call in service.decision_queries.log_event.await_args_list
    )


@pytest.mark.asyncio
async def test_missing_held_leg_does_not_clear_market_data_readiness() -> None:
    set_readiness("market_data_unavailable")
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "XSP"
    service.market_data = AsyncMock()
    service.market_data.get_option_chain.side_effect = (
        {"putExpDateMap": {}},
        asyncio.CancelledError(),
    )
    service._extract_quotes = MagicMock(return_value={"LOWER": MagicMock()})
    service.position_manager = MagicMock()
    service.position_manager.update_position_value.side_effect = ValueError(
        "missing held leg quotes"
    )
    service.state_machine = MagicMock()
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.notifier = None
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=AsyncMock())
    service.trade_queries = MagicMock()
    day = dt.date(2026, 8, 24)
    trade = TradeRecord(trade_id=8, trade_date=day, entry_price=1.0)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date", return_value=day
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    assert readiness_snapshot() == (False, "market_data_unavailable")
    assert not any(
        call.args[0] == "position_market_data_recovered"
        for call in service.decision_queries.log_event.await_args_list
    )
    set_readiness(None)


@pytest.mark.asyncio
async def test_record_exit_metrics_converts_contract_pnl_to_dollars() -> None:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "SPX"
    service.risk_engine = MagicMock()
    service.risk_engine.record_pnl = AsyncMock()

    trade_date = dt.date(2026, 7, 13)
    await service._record_exit_metrics(
        -1.25,
        TradeRecord(trade_date=trade_date, direction="CALL", quantity=2),
    )

    service.risk_engine.record_pnl.assert_awaited_once_with(-250.0, trade_date)


def test_broker_cash_settlement_uses_actual_cash_and_fees() -> None:
    trade = TradeRecord(
        trade_id=177,
        trade_date=dt.date(2026, 7, 13),
        direction="PUT",
        lower_strike=747.0,
        center_strike=751.0,
        upper_strike=755.0,
        lower_symbol="XSP   260713P00747000",
        center_symbol="XSP   260713P00751000",
        upper_symbol="XSP   260713P00755000",
    )
    transactions = [
        {
            "type": "TRADE",
            "time": "2026-07-13T14:00:16+0000",
            "netAmount": net,
            "transferItems": [
                {
                    "amount": amount,
                    "positionEffect": "OPENING",
                    "price": price,
                    "instrument": {"symbol": symbol, "assetType": "OPTION"},
                }
            ],
        }
        for symbol, amount, price, net in (
            (trade.lower_symbol, 1.0, 0.05, -5.66),
            (trade.center_symbol, -2.0, 0.14, 26.67),
            (trade.upper_symbol, 1.0, 0.64, -64.66),
        )
    ] + [
        {
            "type": transaction_type,
            "time": time,
            "netAmount": net,
            "transferItems": [
                {
                    "amount": amount,
                    "positionEffect": "CLOSING",
                    "price": price,
                    "instrument": {"symbol": symbol, "assetType": "OPTION"},
                }
            ],
        }
        for symbol, amount, price, net, transaction_type, time in (
            (
                trade.lower_symbol,
                -1.0,
                0.0,
                0.0,
                "RECEIVE_AND_DELIVER",
                "2026-07-14T06:56:03+0000",
            ),
            (
                trade.center_symbol,
                2.0,
                0.0,
                0.0,
                "RECEIVE_AND_DELIVER",
                "2026-07-14T06:56:01+0000",
            ),
            (
                trade.upper_symbol,
                -1.0,
                3.47,
                347.0,
                "TRADE",
                "2026-07-14T06:53:45+0000",
            ),
        )
    ]

    settlement = broker_cash_settlement_from_transactions(transactions, trade)

    assert settlement is not None
    assert settlement.settlement_value == pytest.approx(3.47)
    assert settlement.settlement_spot == pytest.approx(751.53)
    assert settlement.entry_net_amount == pytest.approx(-43.65)
    assert settlement.settlement_net_amount == pytest.approx(347.0)
    assert settlement.net_pnl_dollars == pytest.approx(303.35)
    assert settlement.processing_time == dt.datetime(
        2026, 7, 14, 6, 56, 3, tzinfo=dt.timezone.utc
    )


@pytest.mark.asyncio
async def test_live_cash_settlement_closes_from_broker_transactions() -> None:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.execution.paper_trading = False
    service.config.strategy.underlying = "XSP"
    service.trade_queries = MagicMock(close_trade=AsyncMock(return_value=True))
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.notifier = None
    service.position_manager = MagicMock()
    service.state_machine = MagicMock()
    service._last_persisted_peak = 1.88
    service._wait_for_broker_cash_settlement = AsyncMock(
        return_value=BrokerCashSettlement(
            settlement_value=3.47,
            settlement_spot=751.53,
            processing_time=dt.datetime(2026, 7, 14, 6, 56, 3, tzinfo=dt.timezone.utc),
            entry_net_amount=-43.65,
            settlement_net_amount=347.0,
            net_pnl_dollars=303.35,
            evidence={"status": "SETTLED"},
        )
    )
    service._record_exit_metrics = AsyncMock()
    trade = TradeRecord(
        trade_id=177,
        trade_date=dt.date(2026, 7, 13),
        direction="PUT",
        quantity=1,
        entry_price=0.41,
        peak_value=1.88,
    )

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=False
    ):
        await service.monitor_loop(trade, MagicMock())

    args = service.trade_queries.close_trade.await_args.args
    assert args[1] == pytest.approx(3.47)
    assert args[2] == dt.datetime(2026, 7, 13, 16, 0, tzinfo=EASTERN)
    assert args[3] == "cash_settled"
    assert args[4] == pytest.approx(3.0335)
    metadata = service.trade_queries.close_trade.await_args.kwargs["metadata"]
    assert metadata["settlement_source"] == "schwab_expiration_transactions"
    assert metadata["gross_pnl_dollars"] == pytest.approx(306.0)
    assert metadata["net_pnl_dollars"] == pytest.approx(303.35)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        order_manager_module.AmbiguousOrderError("exit outcome unknown"),
        order_manager_module.TerminalOrderError("REJECTED", "ORD1"),
        order_manager_module.BrokerFillError("missing execution evidence"),
    ],
)
async def test_monitor_stops_after_unsafe_broker_result(error: RuntimeError) -> None:
    set_readiness(None)
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "XSP"
    service.schwab = AsyncMock()
    service.schwab.get_option_chain.return_value = {}
    service.order_manager = AsyncMock()
    service.order_manager.execute_exit.side_effect = error
    service.trade_queries = MagicMock()
    service.trade_queries.merge_metadata = AsyncMock()
    service.decision_queries = MagicMock()
    service.decision_queries.log_event = AsyncMock()
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock()
    service.tent_queries.insert = AsyncMock()
    service.notifier = None
    service.position_manager = MagicMock()
    pos_state = MagicMock()
    pos_state.peak_update_rejected = False
    pos_state.peak_value = 1.0
    pos_state.current_value = 0.5
    pos_state.drawdown_from_peak = 0.5
    pos_state.time_regime = "morning"
    pos_state.entry_price = 1.0
    service.position_manager.update_position_value.return_value = pos_state
    service.state_machine = MagicMock()
    service.state_machine.state.name = "LOSS"
    service.state_machine.evaluate.return_value = MagicMock(
        reason="drawdown_morning", urgency="normal"
    )
    service._extract_quotes = MagicMock(return_value=[])
    service._exit_mark_parity_report = AsyncMock(return_value={})

    trade = TradeRecord(
        trade_id=7,
        trade_date=dt.date(2026, 7, 13),
        direction="PUT",
        quantity=1,
        entry_price=1.0,
    )

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date",
        return_value=trade.trade_date,
    ), patch("butterfly_guy.services.position_service.get_0dte_expiration"), patch(
        "butterfly_guy.services.position_service.asyncio.sleep",
        new=AsyncMock(side_effect=AssertionError("exit submission restarted")),
    ), pytest.raises(type(error), match=str(error)):
        await service.monitor_loop(trade, MagicMock())

    service.order_manager.execute_exit.assert_awaited_once()
    assert readiness_snapshot() == (False, "broker_order_state_unsafe")
    set_readiness(None)


@pytest.mark.asyncio
async def test_monitor_never_resubmits_after_fill_when_risk_update_fails() -> None:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "SPX"
    service.schwab = AsyncMock()
    service.schwab.get_option_chain.return_value = {}
    service.order_manager = AsyncMock()
    service.order_manager.execute_exit.return_value = {
        "fill_price": 1.25,
        "fill_time": dt.datetime.now(dt.timezone.utc),
        "broker_fill_evidence": {"status": "FILLED"},
        "paper_fill_model": "mark_v1",
        "execution_diagnostics": {"estimated_execution_drag": 0.20},
    }
    service.trade_queries = MagicMock(
        close_trade=AsyncMock(return_value=True),
        merge_metadata=AsyncMock(),
        update_peak_value=AsyncMock(),
    )
    service.decision_queries = MagicMock(log_event=AsyncMock())
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=AsyncMock())
    service.notifier = None
    service.position_manager = MagicMock()
    pos_state = MagicMock(
        peak_update_rejected=False,
        peak_value=1.5,
        current_value=1.25,
        drawdown_from_peak=0.25,
        time_regime="morning",
        entry_price=1.0,
        peak_bid=1.4,
        bid_to_mark_ratio=0.9,
    )
    service.position_manager.update_position_value.return_value = pos_state
    service.state_machine = MagicMock()
    service.state_machine.state.name = "TARGET"
    service.state_machine.evaluate.return_value = MagicMock(
        reason="target", urgency="normal"
    )
    service._extract_quotes = MagicMock(return_value=[])
    service._exit_mark_parity_report = AsyncMock(return_value={})
    service._record_exit_metrics = AsyncMock(side_effect=RuntimeError("risk unavailable"))
    trade = TradeRecord(
        trade_id=7,
        trade_date=dt.date(2026, 7, 13),
        direction="PUT",
        quantity=1,
        entry_price=1.0,
    )

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date",
        return_value=trade.trade_date,
    ), patch("butterfly_guy.services.position_service.get_0dte_expiration"):
        await service.monitor_loop(trade, MagicMock())

    service.order_manager.execute_exit.assert_awaited_once()
    service.trade_queries.close_trade.assert_awaited_once()
    metadata = service.trade_queries.close_trade.await_args.kwargs["metadata"]
    assert metadata["exit_secondary_work_pending"] is True
    assert metadata["paper_fill_model"] == "mark_v1"
    assert metadata["exit_execution_diagnostics"] == {
        "estimated_execution_drag": 0.20
    }
    assert not any(
        call.args == (7, {"exit_secondary_work_pending": False})
        for call in service.trade_queries.merge_metadata.await_args_list
    )


@pytest.mark.asyncio
async def test_settlement_failure_keeps_trade_open() -> None:
    set_readiness(None)
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "SPX"
    service.schwab = AsyncMock()
    service.schwab.get_option_chain.side_effect = RuntimeError("chain unavailable")
    service.trade_queries = MagicMock(close_trade=AsyncMock())
    service.position_manager = MagicMock()
    service.state_machine = MagicMock()
    service._settlement_spot_price = AsyncMock(side_effect=RuntimeError("bars unavailable"))
    service._last_persisted_peak = 0.0
    trade = TradeRecord(trade_id=9, trade_date=dt.date(2026, 7, 13), entry_price=1.0)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=False
    ), pytest.raises(SettlementEvidenceError, match="open trade 9"):
        await service.monitor_loop(trade, MagicMock())

    service.trade_queries.close_trade.assert_not_awaited()
    assert readiness_snapshot() == (False, "settlement_evidence_unavailable")
    set_readiness(None)


def _telemetry_service(db_error: Exception | None) -> PositionService:
    """Service whose non-critical DB telemetry all fails with *db_error*."""
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "SPX"
    service.market_data = AsyncMock()
    service.market_data.get_option_chain.return_value = {}
    service.order_manager = AsyncMock()
    service.order_manager.execute_exit.return_value = None

    def failing() -> AsyncMock:
        return AsyncMock(side_effect=db_error)

    service.trade_queries = MagicMock(
        update_peak_value=failing(), merge_metadata=failing(), close_trade=AsyncMock()
    )
    service.decision_queries = MagicMock(log_event=failing())
    service.chain_queries = MagicMock(get_nearest_snapshot_chain=failing())
    service.monitoring_leg_queries = None
    service.tent_queries = MagicMock(insert=failing())
    service.notifier = None
    service.position_manager = MagicMock()
    service._extract_quotes = MagicMock(return_value={})
    return service


def _pos_state(current: float, peak: float, entry: float = 1.0) -> PositionState:
    return PositionState(
        entry_price=entry,
        current_value=current,
        peak_value=peak,
        pnl=current - entry,
        drawdown_from_peak=(peak - current) / peak if peak else 0.0,
        time_regime="morning",
        minutes_to_close=300.0,
        minutes_since_open=30.0,
    )


def _monitor_patches(trade: TradeRecord, sleep: AsyncMock):
    return (
        patch("butterfly_guy.services.position_service.is_market_open", return_value=True),
        patch(
            "butterfly_guy.services.position_service.session_date",
            return_value=trade.trade_date,
        ),
        patch(
            "butterfly_guy.services.position_service.get_0dte_expiration",
            return_value=trade.trade_date,
        ),
        patch("butterfly_guy.services.position_service.asyncio.sleep", new=sleep),
        patch(
            "butterfly_guy.services.position_service.notify_telegram",
            new=AsyncMock(return_value=True),
        ),
    )


@pytest.mark.asyncio
async def test_telemetry_db_failure_still_reaches_broker_exit() -> None:
    set_readiness(None)
    service = _telemetry_service(RuntimeError("db unavailable"))
    service.position_manager.update_position_value.return_value = _pos_state(1.5, 2.0)
    service.state_machine = MagicMock()
    service.state_machine.state.name = "LOSS"
    service.state_machine.evaluate.return_value = MagicMock(
        reason="drawdown_morning", urgency="normal"
    )
    trade = TradeRecord(trade_id=7, trade_date=dt.date(2026, 7, 14), entry_price=1.0)

    p = _monitor_patches(trade, AsyncMock(side_effect=asyncio.CancelledError))
    with p[0], p[1], p[2], p[3], p[4], pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    service.order_manager.execute_exit.assert_awaited_once()
    assert service.order_manager.execute_exit.await_args.kwargs["exit_reason"] == (
        "drawdown_morning"
    )
    # The peak still advances in memory even though the DB write failed.
    assert service._last_persisted_peak == 2.0
    service.trade_queries.update_peak_value.assert_awaited_once_with(7, 2.0)
    assert service._telemetry_failures["update_peak_value"] == 1
    set_readiness(None)


@pytest.mark.asyncio
async def test_failed_peak_write_is_retried_and_repeated_failures_alert_once() -> None:
    set_readiness(None)
    service = _telemetry_service(RuntimeError("db unavailable"))
    service.position_manager.update_position_value.return_value = _pos_state(1.5, 2.0)
    service.state_machine = MagicMock()
    service.state_machine.state.name = "LOSS"
    service.state_machine.evaluate.return_value = None
    trade = TradeRecord(trade_id=7, trade_date=dt.date(2026, 7, 14), entry_price=1.0)
    polls = 0

    async def sleep(_seconds: float) -> None:
        nonlocal polls
        polls += 1
        if polls == 8:
            raise asyncio.CancelledError

    p = _monitor_patches(trade, AsyncMock(side_effect=sleep))
    with p[0], p[1], p[2], p[3], p[4] as telegram, pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    assert service.state_machine.evaluate.call_count == 8
    assert service.trade_queries.update_peak_value.await_count == 8
    alerts = [c for c in telegram.call_args_list if "WARNING" in c.args[0]]
    # Both update_peak_value and tent_insert cross the threshold once each.
    assert len(alerts) == 2
    assert readiness_snapshot() == (False, "position_telemetry_unavailable")
    set_readiness(None)


@pytest.mark.asyncio
async def test_telemetry_recovery_clears_readiness() -> None:
    set_readiness(None)
    service = _telemetry_service(None)
    service.tent_queries.insert = AsyncMock(
        side_effect=[RuntimeError("db unavailable")] * 5 + [None, None]
    )
    service.position_manager.update_position_value.return_value = _pos_state(1.5, 1.0)
    service.state_machine = MagicMock()
    service.state_machine.state.name = "LOSS"
    service.state_machine.evaluate.return_value = None
    trade = TradeRecord(trade_id=7, trade_date=dt.date(2026, 7, 14), entry_price=1.0)
    polls = 0

    async def sleep(_seconds: float) -> None:
        nonlocal polls
        polls += 1
        if polls == 5:
            assert readiness_snapshot() == (False, "position_telemetry_unavailable")
        if polls == 6:
            assert readiness_snapshot() == (True, None)
            raise asyncio.CancelledError

    p = _monitor_patches(trade, AsyncMock(side_effect=sleep))
    with p[0], p[1], p[2], p[3], p[4] as telegram, pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock())

    messages = [c.args[0] for c in telegram.call_args_list]
    assert sum("WARNING" in m for m in messages) == 1
    assert sum(m.startswith("OK:") for m in messages) == 1
    set_readiness(None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("recovered_peak", "expect_exit"),
    [(3.0, True), (None, False)],
)
async def test_restart_with_recovered_peak_keeps_drawdown_exit(
    recovered_peak: float | None, expect_exit: bool
) -> None:
    """Entry 1.00, peak 3.00, current 0.90: a restart must still exit on drawdown."""
    service = _telemetry_service(None)
    service.position_manager.update_position_value.return_value = _pos_state(0.90, 3.0)
    service.state_machine = ProfitStateMachine(
        ProfitManagementSettings(
            regimes={
                name: TimeRegime(
                    start_minutes_after_open=start,
                    end_minutes_after_open=end,
                    drawdown_threshold=0.50,
                )
                for name, start, end in (
                    ("morning", 0, 120),
                    ("late_morning", 120, 240),
                    ("afternoon", 240, 390),
                )
            }
        )
    )
    service.state_machine._ever_in_profit = True  # must be reset by monitor_loop
    trade = TradeRecord(trade_id=7, trade_date=dt.date(2026, 7, 14), entry_price=1.0)

    p = _monitor_patches(trade, AsyncMock(side_effect=asyncio.CancelledError))
    with p[0], p[1], p[2], p[3], p[4], pytest.raises(asyncio.CancelledError):
        await service.monitor_loop(trade, MagicMock(), recovered_peak=recovered_peak)

    if expect_exit:
        service.order_manager.execute_exit.assert_awaited_once()
        reason = service.order_manager.execute_exit.await_args.kwargs["exit_reason"]
        assert reason.startswith("drawdown")
    else:
        service.order_manager.execute_exit.assert_not_awaited()


def test_settlement_pending_alert_time_is_next_session_open() -> None:
    # Friday -> Monday, and 2026-09-04 is the Friday before Labor Day.
    assert _settlement_pending_alert_time(dt.date(2026, 7, 17)) == dt.datetime(
        2026, 7, 20, 9, 30, tzinfo=EASTERN
    )
    assert _settlement_pending_alert_time(dt.date(2026, 9, 4)) == dt.datetime(
        2026, 9, 8, 9, 30, tzinfo=EASTERN
    )


@pytest.mark.asyncio
async def test_overdue_broker_settlement_alerts_once_and_keeps_waiting() -> None:
    service = PositionService.__new__(PositionService)
    service.schwab = AsyncMock()
    service.schwab.get_transactions_for_day.return_value = []
    service.notifier = MagicMock(_post=AsyncMock())
    trade = TradeRecord(trade_id=9, trade_date=dt.date(2026, 7, 13), entry_price=1.0)
    settled = BrokerCashSettlement(
        settlement_value=1.0,
        settlement_spot=None,
        processing_time=dt.datetime(2026, 7, 14, tzinfo=dt.timezone.utc),
        entry_net_amount=-100.0,
        settlement_net_amount=100.0,
        net_pnl_dollars=0.0,
        evidence={},
    )
    clock = iter(
        [
            dt.datetime(2026, 7, 13, 20, 0, tzinfo=EASTERN),
            dt.datetime(2026, 7, 14, 9, 30, tzinfo=EASTERN),
            dt.datetime(2026, 7, 14, 9, 35, tzinfo=EASTERN),
        ]
    )

    with patch(
        "butterfly_guy.services.position_service.session_date",
        return_value=dt.date(2026, 7, 14),
    ), patch(
        "butterfly_guy.services.position_service.now_eastern",
        side_effect=lambda: next(clock),
    ), patch(
        "butterfly_guy.services.position_service.broker_cash_settlement_from_transactions",
        side_effect=[None, None, None, settled],
    ), patch(
        "butterfly_guy.services.position_service.asyncio.sleep", new=AsyncMock()
    ), patch(
        "butterfly_guy.services.position_service.notify_telegram", new=AsyncMock(return_value=True)
    ) as telegram:
        result = await service._wait_for_broker_cash_settlement(trade)

    assert result is settled
    service.notifier._post.assert_awaited_once()
    messages = [c.args[0] for c in telegram.call_args_list]
    assert len(messages) == 2
    assert messages[0].startswith("WARNING") and "trade 9" in messages[0]
    assert messages[1].startswith("OK:")


@pytest.mark.asyncio
async def test_paper_chain_fallback_refuses_past_dated_trade() -> None:
    set_readiness(None)
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.execution.paper_trading = True
    service.config.strategy.underlying = "SPX"
    service.market_data = AsyncMock()
    service.trade_queries = MagicMock(close_trade=AsyncMock())
    service.position_manager = MagicMock()
    service.state_machine = MagicMock()
    service._settlement_spot_price = AsyncMock(side_effect=RuntimeError("bars unavailable"))
    service._last_persisted_peak = 0.0
    trade = TradeRecord(trade_id=9, trade_date=dt.date(2026, 7, 13), entry_price=1.0)

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=False
    ), patch(
        "butterfly_guy.services.position_service.get_0dte_expiration",
        return_value=dt.date(2026, 7, 14),
    ), pytest.raises(SettlementEvidenceError, match="open trade 9"):
        await service.monitor_loop(trade, MagicMock())

    service.market_data.get_option_chain.assert_not_awaited()
    service.trade_queries.close_trade.assert_not_awaited()
    assert readiness_snapshot() == (False, "settlement_evidence_unavailable")
    set_readiness(None)


@pytest.mark.asyncio
async def test_cash_settlement_db_failure_stops_after_one_close_attempt() -> None:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.execution.paper_trading = False
    service.config.strategy.underlying = "XSP"
    service.trade_queries = MagicMock(
        close_trade=AsyncMock(side_effect=RuntimeError("db unavailable"))
    )
    service.position_manager = MagicMock()
    service.state_machine = MagicMock()
    service._last_persisted_peak = 1.0
    service._wait_for_broker_cash_settlement = AsyncMock(
        return_value=BrokerCashSettlement(
            settlement_value=3.47,
            settlement_spot=751.53,
            processing_time=dt.datetime(2026, 7, 14, 6, 56, tzinfo=dt.timezone.utc),
            entry_net_amount=-43.65,
            settlement_net_amount=347.0,
            net_pnl_dollars=303.35,
            evidence={"status": "SETTLED"},
        )
    )
    trade = TradeRecord(
        trade_id=177,
        trade_date=dt.date(2026, 7, 13),
        entry_price=0.41,
        quantity=1,
    )

    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=False
    ), pytest.raises(RuntimeError, match="db unavailable"):
        await service.monitor_loop(trade, MagicMock())

    service.trade_queries.close_trade.assert_awaited_once()
