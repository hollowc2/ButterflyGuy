"""Order execution with price ladder logic."""

from __future__ import annotations

import asyncio
import datetime as dt

from butterfly_guy.core.config import ExecutionSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    order_fill_duration,
    orders_filled,
    orders_placed,
)
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder

log = get_logger(__name__)


class OrderManager:
    """Manages order execution with price ladder and fill monitoring."""

    def __init__(
        self,
        settings: ExecutionSettings,
        schwab: SchwabClientWrapper,
        builder: ButterflyOrderBuilder,
    ) -> None:
        self.settings = settings
        self.schwab = schwab
        self.builder = builder

    async def execute_entry(
        self, candidate: ButterflyCandidate, quantity: int = 1
    ) -> dict | None:
        """
        Execute entry with price ladder: start at mid, step up by price_ladder_step,
        retry every retry_interval_seconds, cancel if not filled after all steps.
        """
        mid_price = candidate.cost
        step = self.settings.price_ladder_step
        max_steps = self.settings.price_ladder_steps
        retry_interval = self.settings.retry_interval_seconds

        for i in range(max_steps):
            limit_price = round(mid_price + i * step, 2)
            log.info("entry_ladder_step", step=i, price=limit_price)

            order_spec = self.builder.build_butterfly_open(candidate, limit_price, quantity)
            orders_placed.labels(order_type="entry").inc()
            start_time = dt.datetime.now(dt.timezone.utc)

            try:
                order_id = await self.schwab.place_order(order_spec)
                fill = await self._wait_for_fill(order_id, retry_interval)

                if fill:
                    elapsed = (dt.datetime.now(dt.timezone.utc) - start_time).total_seconds()
                    order_fill_duration.observe(elapsed)
                    orders_filled.labels(order_type="entry").inc()
                    log.info("entry_filled", order_id=order_id, price=limit_price, step=i)
                    return {
                        "order_id": order_id,
                        "fill_price": limit_price,
                        "fill_time": dt.datetime.now(dt.timezone.utc),
                    }

                # Not filled — cancel and try next step
                await self.schwab.cancel_order(order_id)
                log.info("entry_step_cancelled", step=i, price=limit_price)

            except Exception as e:
                log.error("entry_step_failed", step=i, error=str(e))

        log.warning("entry_ladder_exhausted", candidate_center=candidate.center_strike)
        return None

    async def execute_exit(
        self, candidate: ButterflyCandidate, current_value: float, quantity: int = 1
    ) -> dict | None:
        """
        Execute exit with reverse price ladder: start at mid, step down.
        """
        mid_price = current_value
        step = self.settings.price_ladder_step
        max_steps = self.settings.price_ladder_steps
        retry_interval = self.settings.retry_interval_seconds

        for i in range(max_steps):
            limit_price = round(max(0.05, mid_price - i * step), 2)
            log.info("exit_ladder_step", step=i, price=limit_price)

            order_spec = self.builder.build_butterfly_close(candidate, limit_price, quantity)
            orders_placed.labels(order_type="exit").inc()
            start_time = dt.datetime.now(dt.timezone.utc)

            try:
                order_id = await self.schwab.place_order(order_spec)
                fill = await self._wait_for_fill(order_id, retry_interval)

                if fill:
                    elapsed = (dt.datetime.now(dt.timezone.utc) - start_time).total_seconds()
                    order_fill_duration.observe(elapsed)
                    orders_filled.labels(order_type="exit").inc()
                    log.info("exit_filled", order_id=order_id, price=limit_price, step=i)
                    return {
                        "order_id": order_id,
                        "fill_price": limit_price,
                        "fill_time": dt.datetime.now(dt.timezone.utc),
                    }

                await self.schwab.cancel_order(order_id)

            except Exception as e:
                log.error("exit_step_failed", step=i, error=str(e))

        log.warning("exit_ladder_exhausted")
        return None

    async def _wait_for_fill(self, order_id: str, timeout: int) -> bool:
        """Poll order status until filled or timeout."""
        elapsed = 0
        poll_interval = 2

        while elapsed < timeout:
            try:
                status = await self.schwab.get_order_status(order_id)
                order_status = status.get("status", "")

                if order_status == "FILLED":
                    return True
                if order_status in ("CANCELED", "REJECTED", "EXPIRED"):
                    log.warning("order_terminal_status", status=order_status, order_id=order_id)
                    return False

            except Exception as e:
                log.warning("order_poll_error", error=str(e))

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return False
