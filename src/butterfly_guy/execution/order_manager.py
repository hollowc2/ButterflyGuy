"""Order execution with price ladder logic."""

from __future__ import annotations

import asyncio
import datetime as dt
from typing import NamedTuple

from butterfly_guy.core.config import ExecutionSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    order_fill_duration,
    orders_filled,
    orders_placed,
)
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.data.schwab_client import SCHWAB_CHAIN_SYMBOLS, SchwabClientWrapper
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder

log = get_logger(__name__)


class LiveSpread(NamedTuple):
    bid: float   # lower_bid + upper_bid - 2 * center_ask  (market maker buys at this price)
    mark: float  # lower_mark + upper_mark - 2 * center_mark
    ask: float   # lower_ask + upper_ask - 2 * center_bid  (market maker sells at this price)


class OrderManager:
    """Manages order execution with price ladder and fill monitoring."""

    def __init__(
        self,
        settings: ExecutionSettings,
        schwab: SchwabClientWrapper,
        builder: ButterflyOrderBuilder,
        underlying: str = "SPX",
    ) -> None:
        self.settings = settings
        self.schwab = schwab
        self.builder = builder
        self.underlying = underlying

    async def _fetch_live_spread(self, candidate: ButterflyCandidate) -> LiveSpread | None:
        """Fetch current butterfly bid/mark/ask from the live option chain. Returns None on any failure."""
        try:
            chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(self.underlying, self.underlying)
            expiration = candidate.lower_quote.expiration
            chain_data = await self.schwab.get_option_chain(chain_symbol, expiration)

            map_key = "callExpDateMap" if candidate.direction == "CALL" else "putExpDateMap"
            exp_map = chain_data.get(map_key, {})

            bids: dict[float, float] = {}
            marks: dict[float, float] = {}
            asks: dict[float, float] = {}
            target_strikes = {candidate.lower_strike, candidate.center_strike, candidate.upper_strike}

            for exp_key, strikes in exp_map.items():
                if str(expiration) not in exp_key:
                    continue
                for strike_str, options in strikes.items():
                    strike = float(strike_str)
                    if strike in target_strikes and options:
                        opt = options[0]
                        bids[strike] = opt.get("bid", 0)
                        marks[strike] = opt.get("mark", 0)
                        asks[strike] = opt.get("ask", 0)

            if len(marks) < 3:
                log.warning("live_spread_incomplete", found=len(marks), expected=3)
                return None

            lo, ce, up = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
            spread_bid = bids[lo] + bids[up] - 2 * asks[ce]
            spread_mark = marks[lo] + marks[up] - 2 * marks[ce]
            spread_ask = asks[lo] + asks[up] - 2 * bids[ce]

            if spread_mark <= 0:
                log.warning("live_spread_nonpositive", mark=spread_mark)
                return None

            return LiveSpread(bid=spread_bid, mark=spread_mark, ask=spread_ask)

        except Exception as e:
            log.warning("live_spread_fetch_failed", error=str(e))
            return None

    async def _fetch_live_mark(self, candidate: ButterflyCandidate) -> float | None:
        """Fetch current butterfly mark from the live option chain. Returns None on any failure."""
        spread = await self._fetch_live_spread(candidate)
        return spread.mark if spread is not None else None

    async def execute_entry(
        self, candidate: ButterflyCandidate, quantity: int = 1
    ) -> dict | None:
        """
        Execute entry with price ladder: reprice from live mark each step,
        step up by price_ladder_step, retry until filled or order_timeout_seconds expires.
        """
        step = self.settings.price_ladder_step
        max_steps = self.settings.price_ladder_steps
        retry_interval = self.settings.retry_interval_seconds
        timeout = self.settings.order_timeout_seconds

        if self.settings.paper_trading:
            deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
            # price_floor tracks the highest live mark observed so far (ratchet).
            # None means no live price seen yet; fall back to candidate.cost until first fetch.
            price_floor: float | None = None

            while True:
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    log.warning("paper_entry_timeout", candidate_center=candidate.center_strike)
                    return None

                for i in range(max_steps):
                    if dt.datetime.now(dt.timezone.utc) >= deadline:
                        log.warning("paper_entry_timeout", candidate_center=candidate.center_strike)
                        return None

                    spread = await self._fetch_live_spread(candidate)
                    if spread is not None:
                        # Ratchet: first live price replaces candidate.cost; subsequent
                        # prices only update if higher, preventing outer-loop backsliding.
                        price_floor = spread.mark if price_floor is None else max(price_floor, spread.mark)
                    mid_price = price_floor if price_floor is not None else candidate.cost

                    limit_price = round(mid_price + i * step, 2)
                    log.info(
                        "paper_entry_step",
                        step=i,
                        price=limit_price,
                        bid=spread.bid if spread is not None else None,
                        mark=spread.mark if spread is not None else None,
                        ask=spread.ask if spread is not None else None,
                    )

                    if spread is not None and limit_price >= spread.ask:
                        log.info("paper_entry_filled", price=limit_price, step=i)
                        return {
                            "order_id": "PAPER",
                            "fill_price": limit_price,
                            "fill_time": dt.datetime.now(dt.timezone.utc),
                        }

                    await asyncio.sleep(retry_interval)

                log.info("paper_entry_ladder_exhausted_repricing", candidate_center=candidate.center_strike)

        deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
        mid_price = candidate.cost

        while True:
            if dt.datetime.now(dt.timezone.utc) >= deadline:
                log.warning("entry_timeout", candidate_center=candidate.center_strike)
                return None

            for i in range(max_steps):
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    log.warning("entry_timeout", candidate_center=candidate.center_strike)
                    return None

                live = await self._fetch_live_mark(candidate)
                if live is not None:
                    mid_price = live

                limit_price = round(mid_price + i * step, 2)
                log.info("entry_ladder_step", step=i, price=limit_price, mid_price=mid_price)

                order_spec = self.builder.build_butterfly_open(candidate, limit_price, quantity)
                orders_placed.labels(underlying=self.underlying, order_type="entry").inc()
                start_time = dt.datetime.now(dt.timezone.utc)

                try:
                    order_id = await self.schwab.place_order(order_spec)
                    fill = await self._wait_for_fill(order_id, retry_interval)

                    if fill:
                        elapsed = (dt.datetime.now(dt.timezone.utc) - start_time).total_seconds()
                        order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                        orders_filled.labels(underlying=self.underlying, order_type="entry").inc()
                        log.info("entry_filled", order_id=order_id, price=limit_price, step=i)
                        return {
                            "order_id": order_id,
                            "fill_price": limit_price,
                            "fill_time": dt.datetime.now(dt.timezone.utc),
                        }

                    await self.schwab.cancel_order(order_id)
                    log.info("entry_step_cancelled", step=i, price=limit_price)

                except Exception as e:
                    log.error("entry_step_failed", step=i, error=str(e))

            log.info("entry_ladder_exhausted_repricing", candidate_center=candidate.center_strike)

    async def execute_exit(
        self, candidate: ButterflyCandidate, current_value: float, quantity: int = 1
    ) -> dict | None:
        """
        Execute exit with reverse price ladder: reprice from live mark each step,
        step down, retry until filled or order_timeout_seconds expires.
        """
        step = self.settings.price_ladder_step
        max_steps = self.settings.price_ladder_steps
        retry_interval = self.settings.retry_interval_seconds
        timeout = self.settings.order_timeout_seconds

        if self.settings.paper_trading:
            deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
            # price_ceiling tracks the lowest live mark observed so far (ratchet).
            # None means no live price seen yet; fall back to current_value until first fetch.
            price_ceiling: float | None = None

            while True:
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    log.warning("paper_exit_timeout")
                    return None

                for i in range(max_steps):
                    if dt.datetime.now(dt.timezone.utc) >= deadline:
                        log.warning("paper_exit_timeout")
                        return None

                    spread = await self._fetch_live_spread(candidate)
                    if spread is not None:
                        # Ratchet: first live price replaces current_value; subsequent
                        # prices only update if lower, preventing outer-loop backsliding.
                        price_ceiling = spread.mark if price_ceiling is None else min(price_ceiling, spread.mark)
                    mid_price = price_ceiling if price_ceiling is not None else current_value

                    limit_price = round(max(0.05, mid_price + (max_steps - 1 - i) * step), 2)
                    log.info(
                        "paper_exit_step",
                        step=i,
                        price=limit_price,
                        bid=spread.bid if spread is not None else None,
                        mark=spread.mark if spread is not None else None,
                        ask=spread.ask if spread is not None else None,
                    )

                    if spread is not None and limit_price <= spread.bid:
                        log.info("paper_exit_filled", price=limit_price, step=i)
                        return {
                            "order_id": "PAPER",
                            "fill_price": limit_price,
                            "fill_time": dt.datetime.now(dt.timezone.utc),
                        }

                    await asyncio.sleep(retry_interval)

                log.warning("paper_exit_ladder_exhausted_repricing")

        deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
        mid_price = current_value

        while True:
            if dt.datetime.now(dt.timezone.utc) >= deadline:
                log.warning("exit_timeout")
                return None

            for i in range(max_steps):
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    log.warning("exit_timeout")
                    return None

                live = await self._fetch_live_mark(candidate)
                if live is not None:
                    mid_price = live

                limit_price = round(max(0.05, mid_price + (max_steps - 1 - i) * step), 2)
                log.info("exit_ladder_step", step=i, price=limit_price, mid_price=mid_price)

                order_spec = self.builder.build_butterfly_close(candidate, limit_price, quantity)
                orders_placed.labels(underlying=self.underlying, order_type="exit").inc()
                start_time = dt.datetime.now(dt.timezone.utc)

                try:
                    order_id = await self.schwab.place_order(order_spec)
                    fill = await self._wait_for_fill(order_id, retry_interval)

                    if fill:
                        elapsed = (dt.datetime.now(dt.timezone.utc) - start_time).total_seconds()
                        order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                        orders_filled.labels(underlying=self.underlying, order_type="exit").inc()
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
