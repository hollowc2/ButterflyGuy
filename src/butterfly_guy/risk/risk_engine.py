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

    def __init__(self, settings: RiskSettings, risk_queries: RiskQueries, underlying: str = "SPX") -> None:
        self.settings = settings
        self.risk_queries = risk_queries
        self.underlying = underlying

    async def can_trade(
        self,
        trade_date: dt.date | None = None,
        account_value: float | None = None,
        buying_power: float | None = None,
        quantity: int = 1,
    ) -> tuple[bool, str]:
        """
        Check all risk conditions. Returns (allowed, reason).

        account_value and buying_power are optional — pass them from a pre-fetched
        Schwab balance call. If None, those checks are skipped.
        """
        today = trade_date or dt.date.today()

        if not is_trading_day(today):
            return False, "not_trading_day"

        if not is_market_open():
            return False, "market_closed"

        state = await self.risk_queries.get_or_create(today, self.underlying)

        if state["halted"]:
            return False, "trading_halted"

        if state["trade_count"] >= self.settings.max_trades_per_day:
            return False, f"max_trades_reached ({state['trade_count']})"

        if quantity < 1:
            return False, f"invalid_quantity ({quantity})"

        if quantity > self.settings.max_position_size:
            return False, f"max_position_size ({quantity}>{self.settings.max_position_size})"

        if state["realized_pnl"] <= -self.settings.max_daily_loss:
            log.warning("max_daily_loss_hit", pnl=state["realized_pnl"])
            await self.risk_queries.set_halted(today, self.underlying)
            return False, f"max_daily_loss ({state['realized_pnl']})"

        # Account floor — PDT compliance
        if account_value is not None:
            if account_value < self.settings.min_account_value:
                log.warning(
                    "account_below_minimum",
                    account_value=account_value,
                    minimum=self.settings.min_account_value,
                )
                await self.risk_queries.set_halted(today, self.underlying)
                return False, f"account_below_minimum ({account_value:.2f})"

        # Buying power guard
        if buying_power is not None:
            if buying_power < self.settings.min_buying_power:
                log.warning(
                    "insufficient_buying_power",
                    buying_power=buying_power,
                    minimum=self.settings.min_buying_power,
                )
                return False, f"insufficient_buying_power ({buying_power:.2f})"

        # Weekly loss circuit breaker
        weekly_pnl = await self.risk_queries.get_weekly_pnl(self.underlying)
        if weekly_pnl <= -self.settings.max_weekly_loss:
            log.warning("max_weekly_loss_hit", weekly_pnl=weekly_pnl)
            await self.risk_queries.set_halted(today, self.underlying)
            return False, f"max_weekly_loss ({weekly_pnl:.4f})"

        # Consecutive loss circuit breaker
        if self.settings.max_consecutive_losses > 0:
            recent_pnls = await self.risk_queries.get_recent_closed_pnls(
                self.underlying, self.settings.max_consecutive_losses
            )
            if (
                len(recent_pnls) >= self.settings.max_consecutive_losses
                and all(p < 0 for p in recent_pnls)
            ):
                log.warning("consecutive_loss_limit_hit", losses=recent_pnls, count=len(recent_pnls))
                await self.risk_queries.set_halted(today, self.underlying)
                return False, f"consecutive_losses ({len(recent_pnls)})"

        return True, "ok"

    async def record_trade(self, trade_date: dt.date | None = None) -> None:
        """Record that a trade was executed."""
        today = trade_date or dt.date.today()
        await self.risk_queries.get_or_create(today, self.underlying)
        await self.risk_queries.increment_trade_count(today, self.underlying)

    async def record_pnl(self, pnl: float, trade_date: dt.date | None = None) -> None:
        """Record realized PnL."""
        today = trade_date or dt.date.today()
        await self.risk_queries.update_pnl(today, pnl, self.underlying)

        # Check if we just hit max loss
        state = await self.risk_queries.get_or_create(today, self.underlying)
        if state["realized_pnl"] <= -self.settings.max_daily_loss:
            await self.risk_queries.set_halted(today, self.underlying)
            log.warning("max_daily_loss_triggered", pnl=state["realized_pnl"])

    async def sync_realized_pnl(self, pnl: float, trade_date: dt.date | None = None) -> None:
        """
        Overwrite realized_pnl in risk state (SET, not ADD).
        Used at startup to restore correct state, including worst-case open trade exposure.
        """
        today = trade_date or dt.date.today()
        await self.risk_queries.get_or_create(today, self.underlying)
        await self.risk_queries.db.pool.execute(
            "UPDATE daily_risk_state SET realized_pnl = $1 WHERE trade_date = $2 AND underlying = $3",
            pnl, today, self.underlying,
        )
        log.info("synced_realized_pnl", pnl=pnl, underlying=self.underlying)

    async def sync_trade_count(self, count: int, trade_date: dt.date | None = None) -> None:
        """
        Manually sync the trade count in the risk state table.
        Used at startup to ensure persistence matches reality.
        """
        today = trade_date or dt.date.today()
        state = await self.risk_queries.get_or_create(today, self.underlying)
        if state["trade_count"] != count:
            log.info("syncing_risk_trade_count", old=state["trade_count"], new=count, underlying=self.underlying)
            await self.risk_queries.db.pool.execute(
                "UPDATE daily_risk_state SET trade_count = $1 WHERE trade_date = $2 AND underlying = $3",
                count, today, self.underlying
            )
