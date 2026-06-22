"""Tests for cash-settlement spot selection."""

import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.data.schemas import TradeRecord
from butterfly_guy.services.position_service import (
    PositionService,
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
