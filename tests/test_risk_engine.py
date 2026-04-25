"""Tests for the risk engine."""

import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.core.config import RiskSettings
from butterfly_guy.risk.risk_engine import RiskEngine


def make_risk_engine(
    trade_count=0, realized_pnl=0.0, halted=False
) -> tuple[RiskEngine, MagicMock]:
    settings = RiskSettings(max_daily_loss=500.0, max_trades_per_day=2)
    risk_queries = MagicMock()
    risk_queries.get_or_create = AsyncMock(
        return_value={
            "trade_count": trade_count,
            "realized_pnl": realized_pnl,
            "halted": halted,
        }
    )
    risk_queries.increment_trade_count = AsyncMock()
    risk_queries.update_pnl = AsyncMock()
    risk_queries.set_halted = AsyncMock()
    risk_queries.get_weekly_pnl = AsyncMock(return_value=0.0)
    risk_queries.get_recent_closed_pnls = AsyncMock(return_value=[])
    engine = RiskEngine(settings, risk_queries)
    return engine, risk_queries


@pytest.mark.asyncio
async def test_can_trade_market_closed():
    """Should block trading when market is closed."""
    engine, _ = make_risk_engine()
    # Force market-closed scenario by using a Sunday date
    sunday = dt.date(2026, 3, 8)
    allowed, reason = await engine.can_trade(trade_date=sunday)
    assert not allowed
    assert "trading_day" in reason


@pytest.mark.asyncio
async def test_can_trade_max_trades():
    engine, _ = make_risk_engine(trade_count=2)
    # Use a Monday but override market check
    from unittest.mock import patch
    with patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True):
        allowed, reason = await engine.can_trade()
    assert not allowed
    assert "max_trades" in reason


@pytest.mark.asyncio
async def test_can_trade_max_loss():
    engine, _ = make_risk_engine(realized_pnl=-600.0)
    from unittest.mock import patch
    with patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True):
        allowed, reason = await engine.can_trade()
    assert not allowed
    assert "max_daily_loss" in reason


@pytest.mark.asyncio
async def test_can_trade_halted():
    engine, _ = make_risk_engine(halted=True)
    from unittest.mock import patch
    with patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True):
        allowed, reason = await engine.can_trade()
    assert not allowed
    assert reason == "trading_halted"


@pytest.mark.asyncio
async def test_can_trade_ok():
    engine, _ = make_risk_engine(trade_count=0, realized_pnl=0.0)
    from unittest.mock import patch
    with patch("butterfly_guy.risk.risk_engine.is_market_open", return_value=True), \
         patch("butterfly_guy.risk.risk_engine.is_trading_day", return_value=True):
        allowed, reason = await engine.can_trade()
    assert allowed
    assert reason == "ok"


@pytest.mark.asyncio
async def test_record_trade_increments():
    engine, queries = make_risk_engine()
    await engine.record_trade(dt.date.today())
    queries.increment_trade_count.assert_called_once()


@pytest.mark.asyncio
async def test_record_pnl_halts_on_max_loss():
    engine, queries = make_risk_engine(realized_pnl=-450.0)
    # After recording -100 pnl, total = -550 → should halt
    queries.get_or_create = AsyncMock(
        return_value={"trade_count": 1, "realized_pnl": -550.0, "halted": False}
    )
    await engine.record_pnl(-100.0, dt.date.today())
    queries.set_halted.assert_called_once()
