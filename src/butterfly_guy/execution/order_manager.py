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
from butterfly_guy.db.queries import OrderIntentQueries
from butterfly_guy.execution.order_builder import ButterflyOrderBuilder

log = get_logger(__name__)

WORKING_ORDER_STATUSES = {"WORKING", "QUEUED", "PENDING_ACTIVATION", "ACCEPTED"}
PARTIAL_FILL_STATUSES = {"PARTIAL", "PARTIAL_FILL", "PARTIALLY_FILLED"}
CANCEL_PENDING_STATUSES = {"CANCEL_PENDING", "PENDING_CANCEL", "CANCEL_REQUESTED"}
TERMINAL_ORDER_STATUSES = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}


class PartialFillError(RuntimeError):
    """Broker reported a partial fill; operator reconciliation is required."""


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
        intent_queries: OrderIntentQueries | None = None,
    ) -> None:
        self.settings = settings
        self.schwab = schwab
        self.builder = builder
        self.underlying = underlying
        self.intent_queries = intent_queries

    def _candidate_snapshot(self, candidate: ButterflyCandidate) -> dict[str, object]:
        return {
            "direction": candidate.direction,
            "wing_width": candidate.wing_width,
            "center_strike": candidate.center_strike,
            "lower_strike": candidate.lower_strike,
            "upper_strike": candidate.upper_strike,
            "cost": candidate.cost,
            "ask": candidate.ask,
            "lower_symbol": candidate.lower_symbol,
            "center_symbol": candidate.center_symbol,
            "upper_symbol": candidate.upper_symbol,
        }

    async def _fetch_live_spread(self, candidate: ButterflyCandidate) -> LiveSpread | None:
        """Fetch current butterfly bid/mark/ask from live chain, or None on failure."""
        try:
            chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(self.underlying, self.underlying)
            expiration = (
                candidate.lower_quote.expiration
                if candidate.lower_quote is not None
                else get_0dte_expiration()
            )
            chain_data = await self.schwab.get_option_chain(chain_symbol, expiration)

            target_strikes = {
                candidate.lower_strike,
                candidate.center_strike,
                candidate.upper_strike,
            }
            bids: dict[float, float] = {}
            marks: dict[float, float] = {}
            asks: dict[float, float] = {}
            ois: dict[float, int] = {}

            for strike, _, opt in iter_chain_options(
                chain_data, expiration, direction=candidate.direction
            ):
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
        legs = 4
        return legs * quantity * self.settings.paper_commission_per_contract / 100

    def _paper_exit_fill_price(self, fill_ref: float, quantity: int) -> float:
        return round(
            max(
                0.05,
                fill_ref
                - self.settings.paper_fill_buffer
                - self.settings.paper_slippage_per_spread
                - self._commission(quantity),
            ),
            2,
        )

    def _paper_forced_fill_ref(
        self, bid_floor: float | None, current_value: float
    ) -> float:
        """Ignore collapsed post-close bids that no longer reflect mark at signal."""
        if bid_floor is None:
            return current_value
        if current_value > 0 and bid_floor < current_value * 0.5:
            return current_value
        return bid_floor

    async def _entry_blocked_by_working_orders(
        self, exclude_intent_id: int | None = None
    ) -> bool:
        try:
            todays_orders = await self.schwab.get_todays_orders()
        except Exception as e:
            log.warning("open_orders_check_failed", error=str(e))
            return True

        known_order_ids: set[str] = set()
        if self.intent_queries is not None:
            try:
                known_order_ids = await self.intent_queries.active_broker_order_ids(
                    self.underlying,
                    dt.date.today(),
                    exclude_intent_id=exclude_intent_id,
                )
            except Exception as e:
                log.warning("open_order_intent_check_failed", error=str(e))
                return True

        working = [
            o for o in todays_orders
            if o.get("status") in WORKING_ORDER_STATUSES | CANCEL_PENDING_STATUSES
            and str(o.get("orderId") or "") not in known_order_ids
        ]
        if not working:
            return False

        log.error(
            "entry_blocked_open_orders_exist",
            count=len(working),
            order_ids=[o.get("orderId") for o in working],
        )
        return True

    async def execute_single_attempt(
        self,
        candidate: ButterflyCandidate,
        limit_price: float,
        quantity: int = 1,
        intent_id: int | None = None,
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
            fill_threshold = spread.ask + self.settings.paper_fill_buffer
            log.debug(
                "paper_entry_spread",
                bid=spread.bid,
                mark=spread.mark,
                ask=spread.ask,
                limit=limit_price,
                fill_threshold=fill_threshold,
            )
            if limit_price >= fill_threshold:
                fill_price = round(
                    spread.ask
                    + self.settings.paper_slippage_per_spread
                    + self._commission(quantity),
                    2,
                )
                log.info("paper_entry_filled", limit=limit_price, fill_price=fill_price)
                return {
                    "order_id": "PAPER",
                    "fill_price": fill_price,
                    "fill_time": now_utc(),
                }
            log.debug(
                "paper_entry_not_filled",
                limit=limit_price,
                ask=spread.ask,
                fill_threshold=fill_threshold,
            )
            return None

        if await self._entry_blocked_by_working_orders(exclude_intent_id=intent_id):
            return None

        order_spec = self.builder.build_butterfly_open(candidate, limit_price, quantity)
        if intent_id is None and self.intent_queries is not None:
            intent_id = await self.intent_queries.create_intent(
                underlying=self.underlying,
                trade_date=(
                    candidate.lower_quote.expiration
                    if candidate.lower_quote is not None
                    else get_0dte_expiration()
                ),
                side="ENTRY",
                limit_price=limit_price,
                quantity=quantity,
                order_spec=order_spec,
                candidate_snapshot=self._candidate_snapshot(candidate),
            )
        orders_placed.labels(underlying=self.underlying, order_type="entry").inc()
        start_time = now_utc()

        try:
            order_id = await self.schwab.place_order(order_spec)
            if intent_id is not None and self.intent_queries is not None:
                await self.intent_queries.mark_broker_order_id(intent_id, order_id)
            fill = await self._wait_for_fill(
                order_id,
                self.settings.retry_interval_seconds,
                intent_id=intent_id,
            )

            if fill:
                elapsed = (now_utc() - start_time).total_seconds()
                order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                orders_filled.labels(underlying=self.underlying, order_type="entry").inc()
                log.info("entry_filled", order_id=order_id, price=limit_price)
                return {
                    "order_id": order_id,
                    "fill_price": limit_price,
                    "fill_time": now_utc(),
                    "intent_id": intent_id,
                }

            if intent_id is not None and self.intent_queries is not None:
                await self.intent_queries.update_broker_status(
                    intent_id, "CANCEL_REQUESTED"
                )
            await self.schwab.cancel_order(order_id)
            log.info("entry_unfilled_cancelled", price=limit_price)
            post_fill = await self._check_post_cancel_fill(
                order_id, limit_price, intent_id=intent_id
            )
            if post_fill:
                return post_fill

        except PartialFillError:
            raise
        except Exception as e:
            if intent_id is not None and self.intent_queries is not None:
                await self.intent_queries.mark_unknown(intent_id, str(e))
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
                            fill_price = round(
                                limit_price
                                + self.settings.paper_slippage_per_spread
                                + self._commission(quantity),
                                2,
                            )
                            log.info(
                                "paper_entry_filled",
                                price=limit_price,
                                fill_price=fill_price,
                                step=i,
                            )
                            return {
                                "order_id": "PAPER",
                                "fill_price": fill_price,
                                "fill_time": now_utc(),
                            }

                    await asyncio.sleep(retry_interval)

                log.debug(
                    "paper_entry_ladder_exhausted_repricing",
                    candidate_center=candidate.center_strike,
                )

        if await self._entry_blocked_by_working_orders():
            return None

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

                except PartialFillError:
                    raise
                except Exception as e:
                    log.error("entry_step_failed", step=i, error=str(e))

            log.info("entry_ladder_exhausted_repricing", candidate_center=candidate.center_strike)

    async def execute_exit(
        self,
        candidate: ButterflyCandidate,
        current_value: float,
        quantity: int = 1,
        exit_reason: str | None = None,
        trade_id: int | None = None,
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
            if exit_reason == "end_of_day":
                fill_price = self._paper_exit_fill_price(current_value, quantity)
                log.info(
                    "paper_exit_eod_immediate_fill",
                    fill_price=fill_price,
                    mark=current_value,
                )
                return {
                    "order_id": "PAPER",
                    "fill_price": fill_price,
                    "fill_time": now_utc(),
                    "forced": False,
                    "eod_immediate": True,
                    "ladder_steps": [],
                }

            deadline = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=timeout)
            bid_floor: float | None = None
            step_trace: list[dict[str, float | int | bool | None]] = []

            while True:
                if dt.datetime.now(dt.timezone.utc) >= deadline:
                    fill_ref = self._paper_forced_fill_ref(bid_floor, current_value)
                    fill_price = self._paper_exit_fill_price(fill_ref, quantity)
                    log.warning(
                        "paper_exit_forced_fill",
                        fill_price=fill_price,
                        fill_ref=fill_ref,
                        bid_floor=bid_floor,
                        mark_at_signal=current_value,
                    )
                    return {
                        "order_id": "PAPER",
                        "fill_price": fill_price,
                        "fill_time": now_utc(),
                        "forced": True,
                        "ladder_steps": step_trace,
                    }

                for i in range(max_steps):
                    spread = await self._fetch_live_spread(candidate)
                    if spread is not None:
                        bid_floor = spread.bid if bid_floor is None else min(bid_floor, spread.bid)

                    if dt.datetime.now(dt.timezone.utc) >= deadline:
                        fill_ref = self._paper_forced_fill_ref(bid_floor, current_value)
                        fill_price = self._paper_exit_fill_price(fill_ref, quantity)
                        log.warning(
                            "paper_exit_forced_fill",
                            fill_price=fill_price,
                            fill_ref=fill_ref,
                            bid_floor=bid_floor,
                            mark_at_signal=current_value,
                        )
                        return {
                            "order_id": "PAPER",
                            "fill_price": fill_price,
                            "fill_time": now_utc(),
                            "forced": True,
                            "ladder_steps": step_trace,
                        }

                    mid_price = bid_floor if bid_floor is not None else current_value
                    limit_price = round(max(0.05, mid_price + (max_steps - 1 - i) * step), 2)
                    log.debug("paper_exit_step", step=i, price=limit_price,
                              bid=spread.bid if spread is not None else None,
                              mark=spread.mark if spread is not None else None)
                    step_trace.append({
                        "step": i,
                        "limit": limit_price,
                        "bid": spread.bid if spread is not None else None,
                        "mark": spread.mark if spread is not None else None,
                        "ask": spread.ask if spread is not None else None,
                        "filled": False,
                    })

                    if spread is not None:
                        fill_threshold = spread.bid - self.settings.paper_fill_buffer
                        if limit_price <= fill_threshold:
                            fill_price = self._paper_exit_fill_price(limit_price, quantity)
                            log.info(
                                "paper_exit_filled",
                                price=limit_price,
                                fill_price=fill_price,
                                step=i,
                            )
                            step_trace[-1]["filled"] = True
                            return {
                                "order_id": "PAPER",
                                "fill_price": fill_price,
                                "fill_time": now_utc(),
                                "spread_bid": spread.bid,
                                "spread_mark": spread.mark,
                                "spread_ask": spread.ask,
                                "ladder_steps": step_trace,
                            }

                    await asyncio.sleep(retry_interval)

                log.debug("paper_exit_ladder_exhausted_repricing")

        deadline = now_utc() + dt.timedelta(seconds=timeout)
        bid_floor: float | None = None
        step_trace: list[dict[str, float | int | bool | None]] = []

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
                step_trace.append({
                    "step": i,
                    "limit": limit_price,
                    "bid": spread.bid if spread is not None else None,
                    "mark": spread.mark if spread is not None else None,
                    "ask": spread.ask if spread is not None else None,
                    "filled": False,
                })

                order_spec = self.builder.build_butterfly_close(candidate, limit_price, quantity)
                intent_id: int | None = None
                if self.intent_queries is not None:
                    snapshot = self._candidate_snapshot(candidate)
                    snapshot["exit_reason"] = exit_reason
                    intent_id = await self.intent_queries.create_intent(
                        underlying=self.underlying,
                        trade_date=(
                            candidate.lower_quote.expiration
                            if candidate.lower_quote is not None
                            else get_0dte_expiration()
                        ),
                        trade_id=trade_id,
                        side="EXIT",
                        limit_price=limit_price,
                        quantity=quantity,
                        order_spec=order_spec,
                        candidate_snapshot=snapshot,
                    )
                orders_placed.labels(underlying=self.underlying, order_type="exit").inc()
                start_time = now_utc()

                try:
                    order_id = await self.schwab.place_order(order_spec)
                    if intent_id is not None and self.intent_queries is not None:
                        await self.intent_queries.mark_broker_order_id(intent_id, order_id)
                    fill = await self._wait_for_fill(
                        order_id, retry_interval, intent_id=intent_id
                    )

                    if fill:
                        elapsed = (now_utc() - start_time).total_seconds()
                        order_fill_duration.labels(underlying=self.underlying).observe(elapsed)
                        orders_filled.labels(underlying=self.underlying, order_type="exit").inc()
                        log.info("exit_filled", order_id=order_id, price=limit_price, step=i)
                        return {
                            "order_id": order_id,
                            "fill_price": limit_price,
                            "fill_time": now_utc(),
                            "intent_id": intent_id,
                            "spread_bid": spread.bid if spread is not None else None,
                            "spread_mark": spread.mark if spread is not None else None,
                            "spread_ask": spread.ask if spread is not None else None,
                            "ladder_steps": [
                                *step_trace[:-1],
                                {**step_trace[-1], "filled": True},
                            ] if step_trace else [{
                                "step": i,
                                "limit": limit_price,
                                "bid": None,
                                "mark": None,
                                "ask": None,
                                "filled": True,
                            }],
                        }

                    if intent_id is not None and self.intent_queries is not None:
                        await self.intent_queries.update_broker_status(
                            intent_id, "CANCEL_REQUESTED"
                        )
                    await self.schwab.cancel_order(order_id)
                    post_fill = await self._check_post_cancel_fill(
                        order_id, limit_price, order_type="exit", intent_id=intent_id
                    )
                    if post_fill:
                        return {
                            **post_fill,
                            "spread_bid": spread.bid if spread is not None else None,
                            "spread_mark": spread.mark if spread is not None else None,
                            "spread_ask": spread.ask if spread is not None else None,
                            "ladder_steps": [
                                *step_trace[:-1],
                                {**step_trace[-1], "filled": True},
                            ],
                        }

                except PartialFillError:
                    raise
                except Exception as e:
                    if intent_id is not None and self.intent_queries is not None:
                        await self.intent_queries.mark_unknown(intent_id, str(e))
                    log.error("exit_step_failed", step=i, error=str(e))

            log.warning("exit_ladder_exhausted")

    async def _check_post_cancel_fill(
        self,
        order_id: str,
        limit_price: float,
        order_type: str = "entry",
        intent_id: int | None = None,
    ) -> dict | None:
        """After a cancel, confirm the order didn't sneak through as filled."""
        try:
            status = await self.schwab.get_order_status(order_id)
            order_status = status.get("status")
            if intent_id is not None and self.intent_queries is not None and order_status:
                await self.intent_queries.update_broker_status(intent_id, order_status, status)
            if order_status == "FILLED":
                log.warning(
                    "post_cancel_fill_detected",
                    order_id=order_id,
                    price=limit_price,
                    order_type=order_type,
                )
                orders_filled.labels(underlying=self.underlying, order_type=order_type).inc()
                return {
                    "order_id": order_id,
                    "fill_price": limit_price,
                    "fill_time": now_utc(),
                    "post_cancel": True,
                    "intent_id": intent_id,
                }
            if order_status in PARTIAL_FILL_STATUSES | CANCEL_PENDING_STATUSES:
                raise PartialFillError(
                    f"Order {order_id} is partially filled after cancel; reconcile broker state"
                )
        except Exception as e:
            if isinstance(e, PartialFillError):
                raise
            log.warning("post_cancel_check_failed", error=str(e))
        return None

    async def _wait_for_fill(
        self, order_id: str, timeout: int, intent_id: int | None = None
    ) -> bool:
        """Poll order status until filled or timeout."""
        elapsed = 0
        poll_interval = 2

        while elapsed < timeout:
            try:
                status = await self.schwab.get_order_status(order_id)
                order_status = status.get("status", "")
                if intent_id is not None and self.intent_queries is not None:
                    await self.intent_queries.update_broker_status(
                        intent_id, order_status, status
                    )

                if order_status == "FILLED":
                    return True
                if order_status in PARTIAL_FILL_STATUSES | CANCEL_PENDING_STATUSES:
                    raise PartialFillError(
                        f"Order {order_id} is partially filled; reconcile broker state"
                    )
                if order_status in TERMINAL_ORDER_STATUSES - {"FILLED"}:
                    log.warning("order_terminal_status", status=order_status, order_id=order_id)
                    return False

            except Exception as e:
                if isinstance(e, PartialFillError):
                    raise
                log.warning("order_poll_error", error=str(e))

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return False
