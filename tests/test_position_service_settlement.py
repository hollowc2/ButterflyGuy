"""Tests for cash-settlement spot selection."""

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.data.schemas import TradeRecord
from butterfly_guy.execution import order_manager as order_manager_module
from butterfly_guy.services.position_service import (
    PositionService,
    SettlementEvidenceError,
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
async def test_record_exit_metrics_converts_contract_pnl_to_dollars() -> None:
    service = PositionService.__new__(PositionService)
    service.config = MagicMock()
    service.config.strategy.underlying = "SPX"
    service.risk_engine = MagicMock()
    service.risk_engine.record_pnl = AsyncMock()

    await service._record_exit_metrics(-1.25, TradeRecord(direction="CALL", quantity=2))

    service.risk_engine.record_pnl.assert_awaited_once_with(-250.0)


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
    ), patch("butterfly_guy.services.position_service.get_0dte_expiration"):
        await service.monitor_loop(trade, MagicMock())

    service.order_manager.execute_exit.assert_awaited_once()
    service.trade_queries.close_trade.assert_awaited_once()
    metadata = service.trade_queries.close_trade.await_args.kwargs["metadata"]
    assert metadata["exit_secondary_work_pending"] is True
    assert not any(
        call.args == (7, {"exit_secondary_work_pending": False})
        for call in service.trade_queries.merge_metadata.await_args_list
    )


@pytest.mark.asyncio
async def test_settlement_failure_keeps_trade_open() -> None:
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
