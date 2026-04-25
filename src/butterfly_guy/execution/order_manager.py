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
from butterfly_guy.core.time_utils import get_0dte_expiration, now_utc
from butterfly_guy.data.chain_utils import iter_chain_options
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
            expiration = (
                candidate.lower_quote.expiration
                if candidate.lower_quote is not None
                else get_0dte_expiration()
            )
            chain_data = await self.schwab.get_option_chain(chain_symbol, expiration)

            target_strikes = {candidate.lower_strike, candidate.center_strike, candidate.upper_strike}
            bids: dict[float, float] = {}
            marks: dict[float, float] = {}
            asks: dict[float, float] = {}
            ois: dict[float, int] = {}

            for strike, _, opt in iter_chain_options(chain_data, expiration, direction=candidate.direction):
                if strike in target_strikes:
                    bids[strike] = opt.get("bid", 0)
                    marks[strike] = opt.get("mark", 0)
                    asks[strike] = opt.get("ask", 0)
                    ois[strike] = opt.get("openInterest", 0)

            if len(marks) < 3:
                log.warning("live_spread_incomplete", found=len(marks), expected=3)
                return None

            lo, ce, up = candidate.lower_strike, candidate.center_strike, candidate.upper_strike
            if self.settings.paper_trading and self.settings.paper_min_oi_per_leg > 0:
                if any(ois.get(s, 0) < self.settings.paper_min_oi_per_leg for s in [lo, ce, up]):
                    log.warning("paper_spread_insufficient_oi", ois=ois)
                    return None
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

    def _commission(self, quantity: int) -> float:
        """Paper trading commission: 4 legs × quantity × rate."""
        _LEGS = 4
        return _LEGS * quantity * self.settings.paper_commission_per_contract / 100

    async def execute_single_attempt(
        self, candidate: ButterflyCandidate, limit_price: float, quantity: int = 1
    ) -> dict | None:
        """
        Place one butterfly order at limit_price. Wait for fill; cancel if unfilled.
        Returns fill dict on success, None otherwise.
        The retry loop and re-scanning live in TradeService — this is a single shot.

        Paper trading: checks live spread; fills if limit_price >= spread.ask + buffer.
        Live trading: places order, waits retry_interval_seconds, cancels if unfilled.
        """
        log.info("entry_attempt", price=limit_price, center=candidate.center_strike,
                 width=candidate.wing_width, paper=self.settings.paper_trading)

        if self.settings.paper_trading:
            spread = await self._fetch_live_spread(candidate)
            if spread is None:
                log.warning("paper_entry_no_spread", center=candidate.center_strike)
                return None
            log.debug("paper_entry_spread", bid=spread.bid, mark=spread.mark,
                      ask=spread.ask, limit=limit_price)
            if limit_price >= spread.mark:
                fill_price = round(spread.mark + self.settings.paper_slippage_per_spread + self._commission(quantity), 2)
                log.info("paper_entry_filled", limit=limit_price, fill_price=fill_price)
                return {
                    "order_id": "PAPER",
                    "fill_price": fill_price,
                    "fill_time": now_utc(),
                }
            log.debug("paper_entry_not_filled", limit=limit_price, mark=spread.mark)
            return None

        order_spec = self.builder.build_butterfly_open(candidate, limit_price, quantity)
        orders_placed.labels(underlying=self.underlying, order_type="entry").inc()
        start_time = now_utc()

        try:
            order_id = await self.schwab.place_order(order_spec)
            fill = await self._wait_for_fill(order_id, self.settings.retry_interval_seconds)

            if fill:
                elapsed = (now_utc() - start_time).total_seconds()
                order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                orders_filled.labels(underlying=self.underlying, order_type="entry").inc()
                log.info("entry_filled", order_id=order_id, price=limit_price)
                return {
                    "order_id": order_id,
                    "fill_price": limit_price,
                    "fill_time": now_utc(),
                }

            await self.schwab.cancel_order(order_id)
            log.info("entry_unfilled_cancelled", price=limit_price)
            post_fill = await self._check_post_cancel_fill(order_id, limit_price)
            if post_fill:
                return post_fill

        except Exception as e:
            log.error("entry_attempt_failed", error=str(e))

        return None

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
            deadline = now_utc() + dt.timedelta(seconds=timeout)

            while True:
                if now_utc() >= deadline:
                    log.warning("paper_entry_timeout", candidate_center=candidate.center_strike)
                    return None

                for i in range(max_steps):
                    if now_utc() >= deadline:
                        log.warning("paper_entry_timeout", candidate_center=candidate.center_strike)
                        return None

                    spread = await self._fetch_live_spread(candidate)
                    mid_price = spread.mark if spread is not None else candidate.cost

                    limit_price = round(mid_price + i * step, 2)
                    log.debug(
                        "paper_entry_step",
                        step=i,
                        price=limit_price,
                        bid=spread.bid if spread is not None else None,
                        mark=spread.mark if spread is not None else None,
                        ask=spread.ask if spread is not None else None,
                    )

                    if spread is not None:
                        fill_threshold = spread.ask + self.settings.paper_fill_buffer
                        if limit_price >= fill_threshold:
                            fill_price = round(limit_price + self.settings.paper_slippage_per_spread + self._commission(quantity), 2)
                            log.info("paper_entry_filled", price=limit_price, fill_price=fill_price, step=i)
                            return {
                                "order_id": "PAPER",
                                "fill_price": fill_price,
                                "fill_time": now_utc(),
                            }

                    await asyncio.sleep(retry_interval)

                log.debug("paper_entry_ladder_exhausted_repricing", candidate_center=candidate.center_strike)

        # Guard: abort if any working entry orders already exist today (prevents duplicates
        # from network-drop retries where Schwab accepted an order but we never got the ID).
        try:
            todays_orders = await self.schwab.get_todays_orders()
            working = [
                o for o in todays_orders
                if o.get("status") in ("WORKING", "QUEUED", "PENDING_ACTIVATION", "ACCEPTED")
            ]
            if working:
                log.error(
                    "entry_blocked_open_orders_exist",
                    count=len(working),
                    order_ids=[o.get("orderId") for o in working],
                )
                return None
        except Exception as e:
            log.warning("open_orders_check_failed", error=str(e))
            # Degrade gracefully — DB-level max_trades_per_day remains the backstop

        deadline = now_utc() + dt.timedelta(seconds=timeout)
        mid_price = candidate.cost

        while True:
            if now_utc() >= deadline:
                log.warning("entry_timeout", candidate_center=candidate.center_strike)
                return None

            for i in range(max_steps):
                if now_utc() >= deadline:
                    log.warning("entry_timeout", candidate_center=candidate.center_strike)
                    return None

                live_spread = await self._fetch_live_spread(candidate)
                if live_spread is not None:
                    mid_price = live_spread.mark

                limit_price = round(mid_price + i * step, 2)
                log.debug("entry_ladder_step", step=i, price=limit_price, mid_price=mid_price)

                order_spec = self.builder.build_butterfly_open(candidate, limit_price, quantity)
                orders_placed.labels(underlying=self.underlying, order_type="entry").inc()
                start_time = now_utc()

                try:
                    order_id = await self.schwab.place_order(order_spec)
                    fill = await self._wait_for_fill(order_id, retry_interval)

                    if fill:
                        elapsed = (now_utc() - start_time).total_seconds()
                        order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                        orders_filled.labels(underlying=self.underlying, order_type="entry").inc()
                        log.info("entry_filled", order_id=order_id, price=limit_price, step=i)
                        return {
                            "order_id": order_id,
                            "fill_price": limit_price,
                            "fill_time": now_utc(),
                        }

                    await self.schwab.cancel_order(order_id)
                    log.debug("entry_step_cancelled", step=i, price=limit_price)
                    post_fill = await self._check_post_cancel_fill(order_id, limit_price)
                    if post_fill:
                        return post_fill

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
            bid_floor: float | None = None

            while True:
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    fill_ref = bid_floor if bid_floor is not None else current_value
                    fill_price = round(max(0.05, fill_ref - self.settings.paper_fill_buffer - self.settings.paper_slippage_per_spread - self._commission(quantity)), 2)
                    log.warning("paper_exit_forced_fill", fill_price=fill_price)
                    return {
                        "order_id": "PAPER",
                        "fill_price": fill_price,
                        "fill_time": now_utc(),
                        "forced": True,
                    }

                for i in range(max_steps):
                    spread = await self._fetch_live_spread(candidate)
                    if spread is not None:
                        bid_floor = spread.bid if bid_floor is None else min(bid_floor, spread.bid)

                    if dt.datetime.now(dt.timezone.utc) >= deadline:
                        fill_ref = bid_floor if bid_floor is not None else current_value
                        fill_price = round(max(0.05, fill_ref - self.settings.paper_fill_buffer - self.settings.paper_slippage_per_spread - self._commission(quantity)), 2)
                        log.warning("paper_exit_forced_fill", fill_price=fill_price)
                        return {
                            "order_id": "PAPER",
                            "fill_price": fill_price,
                            "fill_time": now_utc(),
                            "forced": True,
                        }

                    mid_price = bid_floor if bid_floor is not None else current_value
                    limit_price = round(max(0.05, mid_price + (max_steps - 1 - i) * step), 2)
                    log.debug("paper_exit_step", step=i, price=limit_price,
                              bid=spread.bid if spread is not None else None,
                              mark=spread.mark if spread is not None else None)

                    if spread is not None:
                        fill_threshold = spread.bid - self.settings.paper_fill_buffer
                        if limit_price <= fill_threshold:
                            fill_price = round(max(0.05, limit_price - self.settings.paper_slippage_per_spread - self._commission(quantity)), 2)
                            log.info("paper_exit_filled", price=limit_price, fill_price=fill_price, step=i)
                            return {
                                "order_id": "PAPER",
                                "fill_price": fill_price,
                                "fill_time": now_utc(),
                                "spread_bid": spread.bid,
                                "spread_mark": spread.mark,
                                "spread_ask": spread.ask,
                            }

                    await asyncio.sleep(retry_interval)

                log.debug("paper_exit_ladder_exhausted_repricing")

        deadline = now_utc() + dt.timedelta(seconds=timeout)
        bid_floor: float | None = None

        while True:
            if now_utc() >= deadline:
                log.warning("exit_timeout")
                return None

            for i in range(max_steps):
                if now_utc() >= deadline:
                    log.warning("exit_timeout")
                    return None

                spread = await self._fetch_live_spread(candidate)
                if spread is not None:
                    bid_floor = spread.bid if bid_floor is None else min(bid_floor, spread.bid)
                mid_price = bid_floor if bid_floor is not None else current_value

                limit_price = round(max(0.05, mid_price + (max_steps - 1 - i) * step), 2)
                log.debug("exit_ladder_step", step=i, price=limit_price, mid_price=mid_price)

                order_spec = self.builder.build_butterfly_close(candidate, limit_price, quantity)
                orders_placed.labels(underlying=self.underlying, order_type="exit").inc()
                start_time = now_utc()

                try:
                    order_id = await self.schwab.place_order(order_spec)
                    fill = await self._wait_for_fill(order_id, retry_interval)

                    if fill:
                        elapsed = (now_utc() - start_time).total_seconds()
                        order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                        orders_filled.labels(underlying=self.underlying, order_type="exit").inc()
                        log.info("exit_filled", order_id=order_id, price=limit_price, step=i)
                        return {
                            "order_id": order_id,
                            "fill_price": limit_price,
                            "fill_time": now_utc(),
                            "spread_bid": spread.bid if spread is not None else None,
                            "spread_mark": spread.mark if spread is not None else None,
                            "spread_ask": spread.ask if spread is not None else None,
                        }

                    await self.schwab.cancel_order(order_id)

                except Exception as e:
                    log.error("exit_step_failed", step=i, error=str(e))

            log.warning("exit_ladder_exhausted")

    async def _check_post_cancel_fill(self, order_id: str, limit_price: float) -> dict | None:
        """After a cancel, confirm the order didn't sneak through as filled."""
        try:
            status = await self.schwab.get_order_status(order_id)
            if status.get("status") == "FILLED":
                log.warning("post_cancel_fill_detected", order_id=order_id, price=limit_price)
                orders_filled.labels(underlying=self.underlying, order_type="entry").inc()
                return {
                    "order_id": order_id,
                    "fill_price": limit_price,
                    "fill_time": now_utc(),
                    "post_cancel": True,
                }
        except Exception as e:
            log.warning("post_cancel_check_failed", error=str(e))
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
