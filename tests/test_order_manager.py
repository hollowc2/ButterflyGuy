"""Tests for OrderManager live mark repricing."""

from __future__ import annotations

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
async def test_entry_intent_db_failure_prevents_broker_write():
    om, schwab = make_order_manager(
        make_settings(paper_trading=False, retry_interval_seconds=0)
    )
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.side_effect = RuntimeError("db unavailable")

    with pytest.raises(RuntimeError, match="db unavailable"):
        await om.execute_single_attempt(
            make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
        )

    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_intent_db_failure_prevents_broker_write():
    om, schwab = make_order_manager(
        make_settings(paper_trading=False, retry_interval_seconds=0)
    )
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.side_effect = RuntimeError("db unavailable")

    with patch.object(
        om, "_fetch_live_spread", new=AsyncMock(return_value=None)
    ), pytest.raises(RuntimeError, match="db unavailable"):
        await om.execute_exit(
            make_candidate(5900, 5950, 6000, 2.50),
            current_value=3.00,
            trade_id=7,
        )

    schwab.place_order.assert_not_awaited()


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "lower_bid,lower_mark,lower_ask",
    [(-0.1, 1.0, 1.1), (1.2, 1.1, 1.0)],
    ids=["negative", "crossed"],
)
async def test_fetch_live_spread_rejects_invalid_leg_quotes(
    lower_bid, lower_mark, lower_ask
):
    om, schwab = make_order_manager(make_settings())
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    exp = dt.date(2026, 3, 21)
    schwab.get_option_chain = AsyncMock(
        return_value=make_chain_data_with_spread(
            exp, 5900, 5950, 6000,
            lower_bid, lower_mark, lower_ask,
            1.4, 1.5, 1.6,
            2.3, 2.4, 2.5,
        )
    )

    assert await om._fetch_live_spread(candidate) is None


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
# execute_single_attempt (TradeService entry path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("underlying", ["SPX", "NDX", "XSP"])
async def test_paper_single_attempt_fills_at_mark_plus_commission(underlying: str):
    settings = make_settings(
        paper_trading=True,
        paper_slippage_per_spread=0.05,
        paper_commission_per_contract=0.65,
    )
    om, _schwab = make_order_manager(settings, underlying=underlying)
    candidate = make_candidate(5900, 5950, 6000, 3.30)

    wide_spread = LiveSpread(bid=2.50, mark=3.30, ask=9.80)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=wide_spread)):
        result = await om.execute_single_attempt(candidate, limit_price=5.00)

    assert result is not None
    assert result["fill_price"] == pytest.approx(3.33)
    assert result["paper_fill_model"] == "mark_v1"
    assert result["execution_diagnostics"] == {
        "observed_bid": 2.50,
        "observed_mark": 3.30,
        "observed_ask": 9.80,
        "marketable_entry_estimate": 9.88,
        "estimated_execution_drag": 6.55,
        "configured_slippage": 0.05,
        "configured_fill_buffer": 0.0,
    }


@pytest.mark.asyncio
async def test_paper_single_attempt_requires_observed_spread():
    settings = make_settings(paper_trading=True)
    om, _schwab = make_order_manager(settings, underlying="SPX")
    candidate = make_candidate(5900, 5950, 6000, 3.30)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)):
        result = await om.execute_single_attempt(candidate, limit_price=5.00)

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("underlying", ["SPX", "NDX", "XSP"])
async def test_paper_exit_uses_signal_mark_and_slippage_only_in_diagnostics(
    underlying: str,
):
    settings = make_settings(
        paper_trading=True,
        paper_slippage_per_spread=0.10,
        paper_commission_per_contract=0.65,
    )
    om, schwab = make_order_manager(settings, underlying=underlying)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=2.00, mark=3.20, ask=3.60)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        result = await om.execute_exit(candidate, current_value=3.30, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(3.27)
    assert result["paper_fill_model"] == "mark_v1"
    assert result["execution_diagnostics"]["marketable_exit_estimate"] == 1.87
    assert result["execution_diagnostics"]["estimated_execution_drag"] == 1.40
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_paper_exit_falls_back_to_fresh_signal_mark():
    settings = make_settings(
        paper_trading=True,
        paper_commission_per_contract=0.65,
    )
    om, _schwab = make_order_manager(settings, underlying="SPX")
    candidate = make_candidate(5900, 5950, 6000, 2.50)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)):
        result = await om.execute_exit(candidate, current_value=3.30, quantity=1)

    assert result is not None
    assert result["fill_price"] == pytest.approx(3.27)
    assert result["execution_diagnostics"]["observed_mark"] == 3.30
    assert result["execution_diagnostics"]["observed_bid"] is None
