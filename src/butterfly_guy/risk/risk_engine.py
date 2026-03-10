"""Risk management engine — enforces daily limits and trading rules."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.config import RiskSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import is_market_open, is_trading_day
from butterfly_guy.db.queries import RiskQueries

log = get_logger(__name__)


class RiskEngine:
    """Enforces risk constraints before allowing trades."""

    def __init__(self, settings: RiskSettings, risk_queries: RiskQueries) -> None:
        self.settings = settings
        self.risk_queries = risk_queries

    async def can_trade(self, trade_date: dt.date | None = None) -> tuple[bool, str]:
        """
        Check all risk conditions. Returns (allowed, reason).
        """
        today = trade_date or dt.date.today()

        if not is_trading_day(today):
            return False, "not_trading_day"

        if not is_market_open():
            return False, "market_closed"

        state = await self.risk_queries.get_or_create(today)

        if state["halted"]:
            return False, "trading_halted"

        if state["trade_count"] >= self.settings.max_trades_per_day:
            return False, f"max_trades_reached ({state['trade_count']})"

        if state["realized_pnl"] <= -self.settings.max_daily_loss:
            log.warning("max_daily_loss_hit", pnl=state["realized_pnl"])
            await self.risk_queries.set_halted(today)
            return False, f"max_daily_loss ({state['realized_pnl']})"

        return True, "ok"

    async def record_trade(self, trade_date: dt.date | None = None) -> None:
        """Record that a trade was executed."""
        today = trade_date or dt.date.today()
        await self.risk_queries.get_or_create(today)
        await self.risk_queries.increment_trade_count(today)

    async def record_pnl(self, pnl: float, trade_date: dt.date | None = None) -> None:
        """Record realized PnL."""
        today = trade_date or dt.date.today()
        await self.risk_queries.update_pnl(today, pnl)

        # Check if we just hit max loss
        state = await self.risk_queries.get_or_create(today)
        if state["realized_pnl"] <= -self.settings.max_daily_loss:
            await self.risk_queries.set_halted(today)
            log.warning("max_daily_loss_triggered", pnl=state["realized_pnl"])
