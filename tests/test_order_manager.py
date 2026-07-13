"""Tests for OrderManager live mark repricing."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import ExecutionSettings
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.execution.order_manager import (
    AmbiguousOrderError,
    BrokerFillError,
    LiveSpread,
    OrderManager,
    PartialFillError,
    parse_broker_fill,
)

# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def make_settings(**overrides) -> ExecutionSettings:
    defaults = dict(
        price_ladder_step=0.05,
        price_ladder_steps=4,
        retry_interval_seconds=0,
        order_timeout_seconds=300,
        paper_trading=False,
        paper_fill_buffer=0.0,
        paper_slippage_per_spread=0.0,
        paper_commission_per_contract=0.0,
        paper_min_oi_per_leg=0,
    )
    defaults.update(overrides)
    return ExecutionSettings(**defaults)


def make_quote(strike: float, expiration: dt.date) -> OptionQuote:
    return OptionQuote(
        symbol=f"SPXW_{strike}",
        underlying="SPX",
        expiration=expiration,
        strike=strike,
        option_type="PUT",
        bid=1.0,
        ask=1.2,
        mark=1.1,
    )


def make_candidate(
    lower: float,
    center: float,
    upper: float,
    cost: float,
    direction: str = "PUT",
) -> ButterflyCandidate:
    exp = dt.date(2026, 3, 21)
    return ButterflyCandidate(
        direction=direction,
        wing_width=50,
        center_strike=float(center),
        lower_strike=float(lower),
        upper_strike=float(upper),
        cost=cost,
        max_profit=10.0,
        reward_risk=5.0,
        lower_be=float(lower) + 5,
        upper_be=float(upper) - 5,
        distance_from_spot=0.5,
        spot_price=float(center),
        lower_quote=make_quote(float(lower), exp),
        center_quote=make_quote(float(center), exp),
        upper_quote=make_quote(float(upper), exp),
    )


def make_order_manager(settings: ExecutionSettings, underlying: str = "SPX"):
    schwab = MagicMock()
    schwab.get_option_chain = AsyncMock()
    schwab.place_order = AsyncMock(return_value="ORD1")
    schwab.cancel_order = AsyncMock()
    schwab.get_order_status = AsyncMock(return_value={"status": "WORKING"})
    schwab.get_todays_orders = AsyncMock(return_value=[])

    builder = MagicMock()
    builder.build_butterfly_open = MagicMock(return_value={})
    builder.build_butterfly_close = MagicMock(return_value={})

    om = OrderManager(settings, schwab, builder, underlying)
    return om, schwab


def filled_order() -> dict:
    return json.loads(
        (Path(__file__).parent / "fixtures/trade_177_entry_fill_redacted.json").read_text()
    )


def broker_fill():
    return parse_broker_fill(filled_order(), 1, "ORD1")


def test_captured_trade_177_fill_uses_execution_net_not_limit() -> None:
    fill = parse_broker_fill(filled_order(), 1, "REDACTED")

    assert fill.net_fill_price == pytest.approx(0.41)
    assert fill.execution_time == dt.datetime(
        2026, 7, 13, 14, 0, 16, tzinfo=dt.timezone.utc
    )
    assert fill.remaining_quantity == 0


def test_fill_parser_combines_multiple_activities_and_nested_executions() -> None:
    payload = filled_order()
    payload["quantity"] = payload["filledQuantity"] = 2
    payload["orderLegCollection"][0]["quantity"] = 2
    payload["orderLegCollection"][1]["quantity"] = 4
    payload["orderLegCollection"][2]["quantity"] = 2
    activity = payload.pop("orderActivityCollection")[0]
    payload["childOrderStrategies"] = [
        {
            "orderLegCollection": payload["orderLegCollection"],
            "orderActivityCollection": [activity],
        },
        {
            "orderLegCollection": payload["orderLegCollection"],
            "orderActivityCollection": [activity],
        },
    ]

    assert parse_broker_fill(payload, 2).net_fill_price == pytest.approx(0.41)


@pytest.mark.parametrize(
    "mutation, message",
    [
        (
            lambda payload: payload["orderActivityCollection"][0]["executionLegs"][0].pop(
                "time"
            ),
            "time",
        ),
        (
            lambda payload: payload["orderActivityCollection"][0]["executionLegs"][0].pop(
                "price"
            ),
            "execution evidence",
        ),
        (lambda payload: payload.pop("orderActivityCollection"), "executions"),
        (lambda payload: payload.update(filledQuantity=0), "quantity"),
        (lambda payload: payload.update(remainingQuantity=1), "quantity"),
        (lambda payload: payload["orderLegCollection"][1].update(quantity=1), "ratio"),
    ],
)
def test_fill_parser_fails_closed_on_incomplete_or_inconsistent_evidence(
    mutation, message: str
) -> None:
    payload = filled_order()
    mutation(payload)

    with pytest.raises(BrokerFillError, match=message):
        parse_broker_fill(payload, 1)


def make_chain_data(
    expiration: dt.date,
    lower: float,
    center: float,
    upper: float,
    lower_mark: float,
    center_mark: float,
    upper_mark: float,
    direction: str = "PUT",
) -> dict:
    map_key = "callExpDateMap" if direction == "CALL" else "putExpDateMap"
    exp_key = f"{expiration}:0"
    return {
        map_key: {
            exp_key: {
                str(lower): [
                    {"mark": lower_mark, "bid": lower_mark - 0.1, "ask": lower_mark + 0.1}
                ],
                str(center): [
                    {
                        "mark": center_mark,
                        "bid": center_mark - 0.1,
                        "ask": center_mark + 0.1,
                    }
                ],
                str(upper): [
                    {"mark": upper_mark, "bid": upper_mark - 0.1, "ask": upper_mark + 0.1}
                ],
            }
        }
    }


def make_chain_data_with_spread(
    expiration: dt.date,
    lower: float,
    center: float,
    upper: float,
    lower_bid: float,
    lower_mark: float,
    lower_ask: float,
    center_bid: float,
    center_mark: float,
    center_ask: float,
    upper_bid: float,
    upper_mark: float,
    upper_ask: float,
    direction: str = "PUT",
) -> dict:
    map_key = "callExpDateMap" if direction == "CALL" else "putExpDateMap"
    exp_key = f"{expiration}:0"
    return {
        map_key: {
            exp_key: {
                str(lower): [{"bid": lower_bid, "mark": lower_mark, "ask": lower_ask}],
                str(center): [{"bid": center_bid, "mark": center_mark, "ask": center_ask}],
                str(upper): [{"bid": upper_bid, "mark": upper_mark, "ask": upper_ask}],
            }
        }
    }


# ---------------------------------------------------------------------------
# _fetch_live_spread
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_live_spread_returns_correct_bid_mark_ask():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # lower_bid=1.0, lower_mark=1.1, lower_ask=1.2
    # center_bid=1.4, center_mark=1.5, center_ask=1.6
    # upper_bid=2.3, upper_mark=2.4, upper_ask=2.5
    # spread_bid = 1.0 + 2.3 - 2*1.6 = -0.9
    # spread_mark = 1.1 + 2.4 - 2*1.5 = 0.5
    # spread_ask = 1.2 + 2.5 - 2*1.4 = 0.9
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_spread(
            exp, 5900, 5950, 6000,
            1.0, 1.1, 1.2,
            1.4, 1.5, 1.6,
            2.3, 2.4, 2.5,
        )
    )

    result = await om._fetch_live_spread(candidate)

    assert result is not None
    assert result.mark == pytest.approx(0.5)
    assert result.bid == pytest.approx(1.0 + 2.3 - 2 * 1.6)
    assert result.ask == pytest.approx(1.2 + 2.5 - 2 * 1.4)


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_exception():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    schwab.get_option_chain = AsyncMock(side_effect=RuntimeError("network error"))

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_live_entry_blocks_when_open_orders_check_fails():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_todays_orders = AsyncMock(side_effect=RuntimeError("orders unavailable"))

    result = await om.execute_entry(candidate, quantity=1)

    assert result is None
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_single_attempt_blocks_when_working_order_exists():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_todays_orders = AsyncMock(
        return_value=[{"status": "WORKING", "orderId": "OPEN1"}]
    )

    result = await om.execute_single_attempt(candidate, limit_price=2.50)

    assert result is None
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_single_attempt_blocks_when_child_order_is_working():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_todays_orders = AsyncMock(
        return_value=[
            {
                "status": "CANCELED",
                "childOrderStrategies": [{"status": "WORKING", "orderId": "OPEN1"}],
            }
        ]
    )

    result = await om.execute_single_attempt(candidate, limit_price=2.50)

    assert result is None
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("unsafe_status", ["PARTIALLY_FILLED", "CANCEL_PENDING"])
async def test_single_attempt_raises_on_partial_or_cancel_pending_status(unsafe_status):
    settings = make_settings(paper_trading=False, retry_interval_seconds=2)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_order_status = AsyncMock(return_value={"status": unsafe_status})

    with pytest.raises(PartialFillError):
        await om.execute_single_attempt(candidate, limit_price=2.50)

    schwab.cancel_order.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("unsafe_status", ["PARTIALLY_FILLED", "CANCEL_PENDING"])
async def test_single_attempt_raises_on_partial_or_cancel_pending_child_status(
    unsafe_status,
):
    settings = make_settings(paper_trading=False, retry_interval_seconds=2)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_order_status = AsyncMock(
        return_value={
            "status": "WORKING",
            "childOrderStrategies": [{"status": unsafe_status}],
        }
    )

    with pytest.raises(PartialFillError):
        await om.execute_single_attempt(candidate, limit_price=2.50)

    schwab.cancel_order.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal_status", ["REJECTED", "EXPIRED"])
async def test_single_attempt_aborts_terminal_failure_without_cancel(
    terminal_status: str,
):
    settings = make_settings(paper_trading=False, retry_interval_seconds=2)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    payload = {"status": terminal_status, "orderId": "ORD1"}
    schwab.get_order_status = AsyncMock(return_value=payload)

    with patch("butterfly_guy.execution.order_manager.asyncio.sleep", new=AsyncMock()), \
         pytest.raises(RuntimeError, match=terminal_status):
        await om.execute_single_attempt(candidate, limit_price=2.50)

    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_not_called()
    om.intent_queries.update_broker_status.assert_awaited_once_with(
        42, terminal_status, payload
    )
    om.intent_queries.mark_unknown.assert_not_called()


@pytest.mark.asyncio
async def test_single_attempt_aborts_rejected_child_even_if_parent_is_filled():
    settings = make_settings(paper_trading=False, retry_interval_seconds=2)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    payload = {
        "status": "FILLED",
        "orderId": "ORD1",
        "childOrderStrategies": [{"status": "REJECTED"}],
    }
    schwab.get_order_status = AsyncMock(return_value=payload)

    with pytest.raises(RuntimeError, match="REJECTED"):
        await om.execute_single_attempt(candidate, limit_price=2.50)

    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_not_called()
    om.intent_queries.update_broker_status.assert_awaited_once_with(
        42, "REJECTED", payload
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("terminal_status", ["REJECTED", "EXPIRED"])
async def test_exit_ladder_aborts_terminal_failure_without_cancel_or_resubmit(
    terminal_status: str,
):
    settings = make_settings(
        paper_trading=False,
        retry_interval_seconds=2,
        price_ladder_steps=2,
    )
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    payload = {"status": terminal_status, "orderId": "ORD1"}
    schwab.get_order_status = AsyncMock(return_value=payload)

    base = dt.datetime(2026, 7, 13, 14, 0, tzinfo=dt.timezone.utc)
    now_calls = 0

    def fake_now() -> dt.datetime:
        nonlocal now_calls
        now_calls += 1
        return base if now_calls <= 4 else base + dt.timedelta(seconds=301)

    with patch(
        "butterfly_guy.execution.order_manager.now_utc", side_effect=fake_now
    ), patch(
        "butterfly_guy.execution.order_manager.asyncio.sleep", new=AsyncMock()
    ), patch.object(
        om, "_fetch_live_spread", new=AsyncMock(return_value=None)
    ), pytest.raises(RuntimeError, match=terminal_status):
        await om.execute_exit(candidate, current_value=3.00, quantity=1, trade_id=7)

    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_not_called()
    om.intent_queries.update_broker_status.assert_awaited_once_with(
        42, terminal_status, payload
    )
    om.intent_queries.mark_unknown.assert_not_called()


@pytest.mark.asyncio
async def test_exit_ladder_stops_after_ambiguous_submit():
    om, schwab = make_order_manager(
        make_settings(paper_trading=False, price_ladder_steps=2)
    )
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    schwab.place_order.side_effect = RuntimeError("missing Location")

    with patch.object(
        om, "_fetch_live_spread", new=AsyncMock(return_value=None)
    ), pytest.raises(AmbiguousOrderError, match="outcome is unknown"):
        await om.execute_exit(
            make_candidate(5900, 5950, 6000, 2.50),
            current_value=3.00,
            trade_id=7,
        )

    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_awaited_once_with(42, "missing Location")


@pytest.mark.asyncio
async def test_single_attempt_creates_intent_before_live_submit_and_saves_order_id():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    schwab.get_order_status = AsyncMock(return_value=filled_order())

    result = await om.execute_single_attempt(candidate, limit_price=2.50)

    assert result["intent_id"] == 42
    om.intent_queries.create_intent.assert_awaited_once()
    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_broker_order_id.assert_awaited_once_with(42, "ORD1")


@pytest.mark.asyncio
async def test_single_attempt_ambiguous_submit_leaves_unsafe_intent_without_retry():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    schwab.place_order = AsyncMock(side_effect=RuntimeError("missing Location"))
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with pytest.raises(AmbiguousOrderError, match="outcome is unknown"):
        await om.execute_single_attempt(candidate, limit_price=2.50)

    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_awaited_once_with(42, "missing Location")


@pytest.mark.asyncio
async def test_post_cancel_status_failure_is_ambiguous():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status.side_effect = RuntimeError("status unavailable")

    with pytest.raises(AmbiguousOrderError, match="post-cancel"):
        await om._check_post_cancel_fill("ORD1", 1, intent_id=42)

    om.intent_queries.mark_unknown.assert_awaited_once_with(42, "status unavailable")


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_missing_strikes():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(return_value={
        "putExpDateMap": {
            f"{exp}:0": {
                "5900.0": [{"bid": 0.9, "mark": 1.0, "ask": 1.1}],
                "5950.0": [{"bid": 1.4, "mark": 1.5, "ask": 1.6}],
            }
        }
    })

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_live_spread_returns_none_on_nonpositive_mark():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # mark = 1.0 + 1.0 - 2*2.0 = -2.0
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_spread(
            exp, 5900, 5950, 6000,
            0.9, 1.0, 1.1,
            1.9, 2.0, 2.1,
            0.9, 1.0, 1.1,
        )
    )

    result = await om._fetch_live_spread(candidate)

    assert result is None


# ---------------------------------------------------------------------------
# Paper trading — entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_fills_when_at_ask():
    # spread.mark = 2.30, ask = 2.40; limit steps up 0.05 each step
    # step 0 = 2.30 (< 2.40), step 1 = 2.35 (< 2.40), step 2 = 2.40 (>= 2.40) → fills
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    assert result["order_id"] == "PAPER"
    assert result["fill_price"] == pytest.approx(2.40)  # fills when limit reaches ask


@pytest.mark.asyncio
async def test_paper_entry_no_fill_when_below_ask():
    # spread.ask = 10.0; limit 2.30→2.35→2.40→2.45 across 4 steps — never fills
    # Escape infinite outer loop via CancelledError after all 4 steps sleep
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.00, mark=2.30, ask=10.0)

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 4:
            raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_entry(candidate, quantity=1)
        except asyncio.CancelledError:
            result = None

    assert result is None
    assert sleep_count == 4  # all 4 ladder steps slept without filling


@pytest.mark.asyncio
async def test_paper_entry_sleeps_between_steps():
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        retry_interval_seconds=5,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    # ask=2.40, mark=2.30 → limit at step 2 = 2.30+2*0.05 = 2.40 >= ask → fills at step 2
    spread = LiveSpread(bid=2.00, mark=2.30, ask=2.40)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_entry(candidate, quantity=1)

    # Steps 0 and 1 sleep, step 2 fills (no sleep after fill)
    assert result is not None
    assert sleep_mock.call_count == 2
    sleep_mock.assert_called_with(5)


@pytest.mark.asyncio
async def test_paper_entry_falls_back_on_fetch_failure():
    # fetch returns None → mid_price stays at candidate.cost; spread is None → no fill check
    # Escape via CancelledError after first sleep
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    async def mock_sleep(_):
        raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_entry(candidate, quantity=1)
        except asyncio.CancelledError:
            result = None

    # No fill possible when spread is None
    assert result is None


@pytest.mark.asyncio
async def test_paper_entry_respects_timeout():
    settings = make_settings(paper_trading=True, order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is None


@pytest.mark.asyncio
async def test_paper_entry_does_not_mutate_candidate_cost():
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    original_cost = candidate.cost
    spread = LiveSpread(bid=2.00, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        await om.execute_entry(candidate, quantity=1)

    assert candidate.cost == original_cost


# ---------------------------------------------------------------------------
# Paper trading — exit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_exit_fills_when_at_bid():
    # spread.bid = 3.50; bid_floor = 3.50
    # step 0: 3.50+3*0.05=3.65 > 3.50, step 1: 3.60 > 3.50, step 2: 3.55 > 3.50
    # step 3: 3.50+0*0.05=3.50 <= 3.50 → fills at 3.50 after 3 sleeps
    settings = make_settings(paper_trading=True, price_ladder_steps=4, price_ladder_step=0.05)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=3.60)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert result["order_id"] == "PAPER"
    assert result["fill_price"] == pytest.approx(3.50)
    assert sleep_mock.call_count == 3


@pytest.mark.asyncio
async def test_paper_exit_fills_at_bid_when_bid_far_below_mark():
    # spread.bid = 2.00, mark = 3.30; bid_floor = 2.00
    # step 0: 2.00+3*0.05=2.15 > 2.00, step 1: 2.10 > 2.00, step 2: 2.05 > 2.00
    # step 3: 2.00+0*0.05=2.00 <= 2.00 → fills at 2.00 after 3 sleeps
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.00, mark=3.30, ask=3.60)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_exit(candidate, current_value=3.30, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(2.00)
    assert sleep_mock.call_count == 3


@pytest.mark.asyncio
async def test_paper_exit_sleeps_between_steps():
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        retry_interval_seconds=5,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    # bid=3.05; bid_floor=3.05; step0=3.20, step1=3.15, step2=3.10, step3=3.05
    # step 3: 3.05 <= 3.05 → fills after 3 sleeps
    spread = LiveSpread(bid=3.05, mark=3.00, ask=3.60)

    sleep_mock = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=sleep_mock):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    # Steps 0, 1, 2 sleep (not filled), step 3 fills (no sleep)
    assert sleep_mock.call_count == 3
    sleep_mock.assert_called_with(5)


@pytest.mark.asyncio
async def test_paper_exit_returns_ladder_trace():
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.05, mark=3.00, ask=3.60)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert "ladder_steps" in result
    assert len(result["ladder_steps"]) == 4
    assert result["ladder_steps"][-1]["filled"] is True


@pytest.mark.asyncio
async def test_paper_exit_respects_timeout():
    """When the exit ladder times out, it should force-fill at bid (not return None)."""
    settings = make_settings(paper_trading=True, order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.75, quantity=1)

    # Force-fill fallback returns a dict with forced=True, not None
    assert result is not None
    assert result.get("forced") is True
    assert result["fill_price"] >= 0.05


# ---------------------------------------------------------------------------
# execute_entry live mark repricing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_entry_uses_live_mark_not_candidate_cost():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 2.75

    spread = LiveSpread(bid=2.60, mark=live_mark, ask=2.90)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_open.call_args[0][1]
    assert limit_price_used == live_mark


@pytest.mark.asyncio
async def test_entry_steps_up_from_live_mark():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_mark = 2.75

    spread = LiveSpread(bid=2.60, mark=live_mark, ask=2.90)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(
             om, "_wait_for_fill", new=AsyncMock(side_effect=[False, broker_fill()])
         ):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    calls = om.builder.build_butterfly_open.call_args_list
    assert len(calls) == 2
    assert calls[0][0][1] == pytest.approx(live_mark)
    assert calls[1][0][1] == pytest.approx(live_mark + 0.05)


@pytest.mark.asyncio
async def test_entry_falls_back_to_candidate_cost_when_fetch_fails():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_open.call_args[0][1]
    assert limit_price_used == candidate.cost


@pytest.mark.asyncio
async def test_entry_reprice_called_per_step():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    fetch_mock = AsyncMock(return_value=LiveSpread(bid=2.60, mark=2.75, ask=2.90))
    # Fill on the last step so we traverse all 4 steps
    wait_mock = AsyncMock(side_effect=[False, False, False, broker_fill()])

    with patch.object(om, "_fetch_live_spread", new=fetch_mock), \
         patch.object(om, "_wait_for_fill", new=wait_mock):
        await om.execute_entry(candidate, quantity=1)

    assert fetch_mock.call_count == 4


@pytest.mark.asyncio
async def test_entry_returns_none_on_timeout():
    settings = make_settings(order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    result = await om.execute_entry(candidate, quantity=1)

    assert result is None


@pytest.mark.asyncio
async def test_entry_does_not_mutate_candidate_cost():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    original_cost = candidate.cost
    live_mark = 2.75

    spread = LiveSpread(bid=2.60, mark=live_mark, ask=2.90)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        await om.execute_entry(candidate, quantity=1)

    assert candidate.cost == original_cost


# ---------------------------------------------------------------------------
# execute_exit live mark repricing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exit_uses_live_bid_not_current_value():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_bid = 3.20
    current_value = 2.50

    live_spread = LiveSpread(bid=live_bid, mark=3.40, ask=3.60)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=live_spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await om.execute_exit(candidate, current_value=current_value, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_close.call_args[0][1]
    # Step 0: bid_floor + (max_steps-1)*step = 3.20 + 3*0.05 = 3.35
    assert limit_price_used == pytest.approx(live_bid + 3 * 0.05)


@pytest.mark.asyncio
async def test_exit_falls_back_to_current_value_when_fetch_fails():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    current_value = 3.75

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await om.execute_exit(candidate, current_value=current_value, quantity=1)

    assert result is not None
    limit_price_used = om.builder.build_butterfly_close.call_args[0][1]
    # fetch failed → mid_price = current_value; step 0 = current_value + (4-1)*0.05
    assert limit_price_used == pytest.approx(current_value + 3 * 0.05)


@pytest.mark.asyncio
async def test_exit_steps_down_from_live_bid():
    settings = make_settings(price_ladder_steps=4)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_bid = 3.20

    live_spread = LiveSpread(bid=live_bid, mark=3.40, ask=3.60)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=live_spread)), \
         patch.object(
             om, "_wait_for_fill", new=AsyncMock(side_effect=[False, broker_fill()])
         ):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert result is not None
    calls = om.builder.build_butterfly_close.call_args_list
    assert len(calls) == 2
    # Step 0: bid_floor + (4-1)*0.05 = 3.35  (best price first)
    # Step 1: bid_floor + (4-2)*0.05 = 3.30  (step down)
    assert calls[0][0][1] == pytest.approx(live_bid + 3 * 0.05)
    assert calls[1][0][1] == pytest.approx(live_bid + 2 * 0.05)


@pytest.mark.asyncio
async def test_exit_detects_post_cancel_fill():
    settings = make_settings(price_ladder_steps=1, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.20, mark=3.40, ask=3.60)
    schwab.get_order_status = AsyncMock(return_value=filled_order())

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert result is not None
    assert result["post_cancel"] is True
    assert result["fill_price"] == pytest.approx(0.41)
    assert result["ladder_steps"][-1]["filled"] is True
    schwab.cancel_order.assert_called_once_with("ORD1")


@pytest.mark.asyncio
async def test_exit_returns_none_on_timeout():
    settings = make_settings(order_timeout_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    result = await om.execute_exit(candidate, current_value=3.75, quantity=1)

    assert result is None


# ---------------------------------------------------------------------------
# Paper realism: fill buffer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_fill_buffer_prevents_early_fill():
    # mark=2.30, ask=2.40, fill_buffer=0.10 → need limit >= 2.50
    # Steps: 2.30, 2.35, 2.40, 2.45 — none reach 2.50 → no fill in 4 steps
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_fill_buffer=0.10,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 4:
            raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_entry(candidate, quantity=1)
        except asyncio.CancelledError:
            result = None

    assert result is None
    assert sleep_count == 4


@pytest.mark.asyncio
async def test_paper_entry_fill_buffer_requires_extra_width():
    # mark=2.30, ask=2.40, fill_buffer=0.10 → fill at step 4 (2.30+4*0.05=2.50 >= 2.40+0.10)
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=5,
        price_ladder_step=0.05,
        paper_fill_buffer=0.10,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    assert result["order_id"] == "PAPER"
    # limit_price at step 4 = 2.30 + 4*0.05 = 2.50; fill_price = 2.50 (no slippage/commission)
    assert result["fill_price"] == pytest.approx(2.50)


@pytest.mark.asyncio
async def test_paper_exit_fill_buffer_prevents_early_fill():
    # bid=3.50, fill_buffer=0.10 → need limit <= 3.40
    # Steps from 3.50+(3)*0.05=3.65 down: 3.65, 3.60, 3.55, 3.50 — none <= 3.40
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_fill_buffer=0.10,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=3.60)

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 4:
            raise asyncio.CancelledError()

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=mock_sleep):
        try:
            result = await om.execute_exit(candidate, current_value=3.00, quantity=1)
        except asyncio.CancelledError:
            result = None

    assert result is None
    assert sleep_count == 4


# ---------------------------------------------------------------------------
# Paper realism: slippage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_slippage_added_to_fill_price():
    # mark=2.30, ask=2.40 → fills at step 2 (limit=2.40); slippage=0.10 → fill_price=2.50
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_slippage_per_spread=0.10,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(2.50)  # 2.40 + 0.10 slippage


@pytest.mark.asyncio
async def test_paper_exit_slippage_subtracted_from_fill_price():
    # bid=3.50; step 3: limit=3.50+0*0.05=3.50 <= 3.50; slippage=0.10 → fill_price=3.40
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_slippage_per_spread=0.10,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=3.60)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(3.40)  # 3.50 - 0.10 slippage


# ---------------------------------------------------------------------------
# Paper realism: commission
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_commission_added_to_fill_price():
    # mark=2.30, ask=2.40 → limit=2.40 at step 2; commission=4*1*1.00/100=0.04 → fill_price=2.44
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_commission_per_contract=1.00,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(2.44)  # 2.40 + 0.04 commission


@pytest.mark.asyncio
async def test_paper_exit_commission_subtracted_from_fill_price():
    # bid=3.50; step 3: limit=3.50; commission=4*1*1.00/100=0.04 → fill_price=3.46
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_commission_per_contract=1.00,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=3.60)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(3.46)  # 3.50 - 0.04 commission


# ---------------------------------------------------------------------------
# Paper realism: forced exit applies buffer + slippage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_forced_exit_applies_buffer_and_slippage():
    # Forced fill triggers when all ladder steps exhaust and deadline expires.
    # Mock dt.datetime.now to control the timeout: enters loop once, then expires.
    # bid=3.50, ask=10.0 (never fills), fill_buffer=0.05, slippage=0.10 →
    # force_price = 3.50 - 0.05 - 0.10 = 3.35
    settings = make_settings(
        paper_trading=True,
        order_timeout_seconds=300,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        paper_fill_buffer=0.05,
        paper_slippage_per_spread=0.10,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.50, mark=3.00, ask=10.0)  # ask too high: fill never triggers

    base = dt.datetime(2026, 3, 23, 12, 0, 0, tzinfo=dt.timezone.utc)
    now_call = 0

    def mock_now(tz=None):
        nonlocal now_call
        now_call += 1
        # Call 1: deadline setup; call 2: while-check enters loop
        # Call 3+: inner deadline check + while-check + fill_time → expired
        return base if now_call <= 2 else base + dt.timedelta(seconds=400)

    mock_dt = MagicMock()
    mock_dt.datetime.now.side_effect = mock_now
    mock_dt.timedelta = dt.timedelta
    mock_dt.timezone = dt.timezone
    mock_dt.date = dt.date

    with patch("butterfly_guy.execution.order_manager.dt", mock_dt), \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=3.00, quantity=1)

    assert result is not None
    assert result.get("forced") is True
    assert result["fill_price"] == pytest.approx(3.35)


@pytest.mark.asyncio
async def test_paper_exit_eod_fills_immediately_at_mark():
    settings = make_settings(paper_trading=True)
    om, _schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    fetch = AsyncMock()
    with patch.object(om, "_fetch_live_spread", new=fetch):
        result = await om.execute_exit(
            candidate,
            current_value=16.63,
            quantity=1,
            exit_reason="end_of_day",
        )

    assert result is not None
    assert result.get("eod_immediate") is True
    assert result.get("forced") is False
    assert result["fill_price"] == pytest.approx(16.63)
    fetch.assert_not_called()


@pytest.mark.asyncio
async def test_paper_forced_fill_uses_mark_when_market_closed():
    settings = make_settings(paper_trading=True, order_timeout_seconds=0)
    om, _schwab = make_order_manager(settings)
    candidate = make_candidate(7250, 7290, 7330, 3.98)
    garbage_spread = LiveSpread(bid=0.05, mark=0.05, ask=0.10)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=garbage_spread)), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_exit(candidate, current_value=16.63, quantity=1)

    assert result is not None
    assert result.get("forced") is True
    assert result["fill_price"] == pytest.approx(16.63)


# ---------------------------------------------------------------------------
# Paper realism: open interest gate
# ---------------------------------------------------------------------------

def make_chain_data_with_oi(
    expiration: dt.date,
    lower: float,
    center: float,
    upper: float,
    lower_oi: int,
    center_oi: int,
    upper_oi: int,
    direction: str = "PUT",
) -> dict:
    map_key = "callExpDateMap" if direction == "CALL" else "putExpDateMap"
    exp_key = f"{expiration}:0"
    return {
        map_key: {
            exp_key: {
                str(lower): [{"bid": 1.0, "mark": 1.1, "ask": 1.2, "openInterest": lower_oi}],
                str(center): [{"bid": 1.4, "mark": 1.5, "ask": 1.6, "openInterest": center_oi}],
                str(upper): [{"bid": 2.3, "mark": 2.4, "ask": 2.5, "openInterest": upper_oi}],
            }
        }
    }


@pytest.mark.asyncio
async def test_paper_spread_oi_gate_returns_none_when_oi_insufficient():
    settings = make_settings(paper_trading=True, paper_min_oi_per_leg=50)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    # center has OI=10 < 50 → gate fires
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_oi(exp, 5900, 5950, 6000, 100, 10, 100)
    )

    result = await om._fetch_live_spread(candidate)

    assert result is None


@pytest.mark.asyncio
async def test_paper_spread_oi_gate_passes_when_all_oi_sufficient():
    settings = make_settings(paper_trading=True, paper_min_oi_per_leg=50)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_oi(exp, 5900, 5950, 6000, 100, 200, 150)
    )

    result = await om._fetch_live_spread(candidate)

    assert result is not None


@pytest.mark.asyncio
async def test_paper_spread_oi_gate_disabled_when_zero():
    # paper_min_oi_per_leg=0 means disabled; even OI=0 should not block
    settings = make_settings(paper_trading=True, paper_min_oi_per_leg=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_oi(exp, 5900, 5950, 6000, 0, 0, 0)
    )

    result = await om._fetch_live_spread(candidate)

    assert result is not None


@pytest.mark.asyncio
async def test_paper_spread_oi_gate_skipped_in_live_mode():
    # paper_trading=False → OI gate should not fire even if OI is low
    settings = make_settings(paper_trading=False, paper_min_oi_per_leg=50)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)

    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_oi(exp, 5900, 5950, 6000, 1, 1, 1)
    )

    result = await om._fetch_live_spread(candidate)

    assert result is not None


# ---------------------------------------------------------------------------
# Paper realism: no ratchet — uses current mark each step
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_entry_uses_current_mark_not_ratchet():
    # First step sees mark=3.00 (high), second step sees mark=2.30 (lower).
    # Without ratchet, second step should anchor to 2.30, not stay at 3.00.
    # ask=2.40 at step 2 of second outer-loop pass → limit=2.30+2*0.05=2.40 fills.
    settings = make_settings(
        paper_trading=True,
        price_ladder_steps=4,
        price_ladder_step=0.05,
        order_timeout_seconds=300,
    )
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    high_spread = LiveSpread(bid=2.90, mark=3.00, ask=10.0)   # first pass: ask too high to fill
    low_spread = LiveSpread(bid=2.20, mark=2.30, ask=2.40)    # second pass: fills at step 2

    call_count = 0

    async def fetch_side_effect(_):
        nonlocal call_count
        call_count += 1
        return high_spread if call_count <= 4 else low_spread

    with patch.object(om, "_fetch_live_spread", new=fetch_side_effect), \
         patch("asyncio.sleep", new=AsyncMock()):
        result = await om.execute_entry(candidate, quantity=1)

    assert result is not None
    # fill_price should be based on mark=2.30, not ratcheted 3.00
    assert result["fill_price"] == pytest.approx(2.40)


# ---------------------------------------------------------------------------
# execute_single_attempt (TradeService entry path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paper_single_attempt_fills_at_ask_not_mark():
    settings = make_settings(paper_trading=True, paper_slippage_per_spread=0.05)
    om, _schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 3.30)

    wide_spread = LiveSpread(bid=2.50, mark=3.30, ask=9.80)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=wide_spread)):
        result = await om.execute_single_attempt(candidate, limit_price=9.80)

    assert result is not None
    assert result["fill_price"] == pytest.approx(9.85)  # ask + slippage


@pytest.mark.asyncio
async def test_paper_single_attempt_no_fill_when_limit_below_ask():
    settings = make_settings(paper_trading=True)
    om, _schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 3.30)

    wide_spread = LiveSpread(bid=2.50, mark=3.30, ask=9.80)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=wide_spread)):
        result = await om.execute_single_attempt(candidate, limit_price=5.00)

    assert result is None
