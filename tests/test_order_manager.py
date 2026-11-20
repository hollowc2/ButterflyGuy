"""Tests for OrderManager live mark repricing."""

from __future__ import annotations

import datetime as dt
import json
import statistics
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncpg.exceptions import UniqueViolationError
from pydantic import ValidationError

from butterfly_guy.core.config import ExecutionSettings
from butterfly_guy.core.exit_pricing import (
    EXIT_PRICING_RULES,
    exit_limit,
    static_quote_estimate,
)
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.data.schwab_client import OrderRejectedError
from butterfly_guy.execution.order_manager import (
    AmbiguousOrderError,
    BrokerFillError,
    EntryOrderReplacedError,
    IntentPersistenceError,
    LiveSpread,
    OperatorExitTakeoverError,
    OrderManager,
    PartialFillError,
    TerminalOrderError,
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
    schwab.get_option_chain = AsyncMock(
        side_effect=lambda _symbol, expiration: make_chain_data(
            expiration,
            5900,
            5950,
            6000,
            1.1,
            1.5,
            2.4,
        )
    )
    # A resting order works until the bot cancels it, then reads CANCELED like Schwab's.
    cancelled: set[str] = set()
    schwab.place_order = AsyncMock(side_effect=lambda _spec: (cancelled.clear(), "ORD1")[1])
    schwab.cancel_order = AsyncMock(side_effect=cancelled.add)
    schwab.get_order_status = AsyncMock(
        side_effect=lambda order_id: {
            "status": "CANCELED" if order_id in cancelled else "WORKING"
        }
    )
    schwab.get_todays_orders = AsyncMock(return_value=[])
    schwab.get_account_snapshot = AsyncMock(
        return_value={"securitiesAccount": {"positions": []}}
    )

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
async def test_fetch_live_spread_uses_separate_market_data_provider():
    settings = make_settings()
    om, schwab = make_order_manager(settings)
    market_data = AsyncMock()
    om.market_data = market_data
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    expiration = candidate.lower_quote.expiration
    market_data.get_option_chain.return_value = make_chain_data(
        expiration,
        5900,
        5950,
        6000,
        1.1,
        1.5,
        2.4,
    )

    assert await om._fetch_live_spread(candidate) is not None
    market_data.get_option_chain.assert_awaited_once()
    schwab.get_option_chain.assert_not_awaited()


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

    result = await om.execute_single_attempt(candidate, limit_price=2.50)

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
async def test_single_attempt_rejects_broker_fill_above_submitted_limit():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    schwab.get_order_status = AsyncMock(return_value=filled_order())

    with pytest.raises(BrokerFillError, match="exceeds submitted limit"):
        await om.execute_single_attempt(
            make_candidate(5900, 5950, 6000, 2.50),
            limit_price=0.40,
        )

    schwab.place_order.assert_awaited_once()


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
@pytest.mark.parametrize(
    "db_error,expected_error",
    [
        (UniqueViolationError("private DB detail"), AmbiguousOrderError),
        (ConnectionError("db unavailable"), ConnectionError),
    ],
)
async def test_exit_intent_conflict_halts_but_connection_failure_remains_retryable(
    db_error, expected_error,
):
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.side_effect = db_error

    with pytest.raises(expected_error) as caught:
        await om.execute_exit(
            make_candidate(5900, 5950, 6000, 2.50), current_value=3.00, trade_id=7
        )

    if isinstance(db_error, UniqueViolationError):
        assert str(caught.value) == "an active exit intent already exists for this trade"
        assert caught.value.__cause__ is db_error
    else:
        assert caught.value is db_error
    om.intent_queries.create_intent.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_not_awaited()
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_entry_intent_conflict_logs_distinct_event_and_preserves_exception():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    db_error = UniqueViolationError("private DB detail")
    om.intent_queries.create_intent.side_effect = db_error

    with patch("butterfly_guy.execution.order_manager.log") as logger, \
         pytest.raises(UniqueViolationError) as caught:
        await om.execute_single_attempt(
            make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
        )

    assert caught.value is db_error
    logger.error.assert_called_once_with("entry_blocked_active_intent", underlying="SPX")
    om.intent_queries.mark_unknown.assert_not_awaited()
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
async def test_single_attempt_4xx_submit_is_rejected_not_ambiguous():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    schwab.place_order = AsyncMock(side_effect=OrderRejectedError(400, "bad price"))

    with pytest.raises(TerminalOrderError, match="REJECTED"):
        await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 2.50), 2.50)

    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_not_called()
    om.intent_queries.update_broker_status.assert_awaited_once_with(
        42, "REJECTED", {"http_status": 400, "error": "bad price"}
    )
    om.intent_queries.mark_unknown.assert_not_called()


@pytest.mark.asyncio
async def test_exit_ladder_stops_after_4xx_submit_rejection():
    om, schwab = make_order_manager(
        make_settings(paper_trading=False, price_ladder_steps=2)
    )
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    schwab.place_order.side_effect = OrderRejectedError(400, "bad price")

    with patch.object(
        om, "_fetch_live_spread", new=AsyncMock(return_value=None)
    ), pytest.raises(TerminalOrderError, match="REJECTED"):
        await om.execute_exit(
            make_candidate(5900, 5950, 6000, 2.50), current_value=3.00, trade_id=7
        )

    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_not_called()


async def _rejected_submit(om, side):
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    if side == "entry":
        return await om.execute_single_attempt(candidate, 2.50)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)):
        return await om.execute_exit(candidate, current_value=3.00, trade_id=7)


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
async def test_recorded_rejection_stops_the_ladder_as_terminal(side):
    om, schwab = make_order_manager(make_settings(price_ladder_steps=2))
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    schwab.place_order = AsyncMock(side_effect=OrderRejectedError(400, "bad price"))

    with pytest.raises(TerminalOrderError, match="REJECTED"):
        await _rejected_submit(om, side)

    om.intent_queries.update_broker_status.assert_awaited_once_with(
        42, "REJECTED", {"http_status": 400, "error": "bad price"}
    )
    schwab.place_order.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
@pytest.mark.parametrize("db_error", [RuntimeError("db down"), ConnectionError("reset")])
async def test_unrecorded_rejection_halts_as_unsafe_intent_state(side, db_error):
    # Schwab refused it, but the intent still says SUBMITTING and holds its index.
    om, schwab = make_order_manager(make_settings(price_ladder_steps=2))
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    om.intent_queries.update_broker_status.side_effect = db_error
    om.intent_queries.mark_unknown.side_effect = RuntimeError("must not be called")
    rejection = OrderRejectedError(403, "forbidden for account 1234-5678")
    schwab.place_order = AsyncMock(side_effect=rejection)

    with pytest.raises(IntentPersistenceError) as caught:
        await _rejected_submit(om, side)

    error = caught.value
    assert not isinstance(error, (TerminalOrderError, AmbiguousOrderError))
    assert error.__cause__ is db_error and error.__cause__.__context__ is rejection
    assert "rejected at submit (HTTP 403)" in str(error) and "1234" not in str(error)
    om.intent_queries.create_intent.assert_awaited_once()
    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
async def test_single_attempt_raises_ambiguous_when_mark_unknown_also_fails():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    om.intent_queries.mark_broker_order_id.side_effect = RuntimeError("db down")
    om.intent_queries.mark_unknown.side_effect = RuntimeError("db still down")

    with pytest.raises(AmbiguousOrderError, match="outcome is unknown"):
        await om.execute_single_attempt(
            make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
        )

    schwab.place_order.assert_awaited_once()
    om.intent_queries.mark_unknown.assert_awaited_once_with(42, "db down")


@pytest.mark.asyncio
async def test_exit_raises_ambiguous_when_mark_unknown_also_fails():
    om, schwab = make_order_manager(
        make_settings(paper_trading=False, price_ladder_steps=2)
    )
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    om.intent_queries.mark_broker_order_id.side_effect = RuntimeError("db down")
    om.intent_queries.mark_unknown.side_effect = RuntimeError("db still down")

    with patch.object(
        om, "_fetch_live_spread", new=AsyncMock(return_value=None)
    ), pytest.raises(AmbiguousOrderError, match="outcome is unknown"):
        await om.execute_exit(
            make_candidate(5900, 5950, 6000, 2.50),
            current_value=3.00,
            trade_id=7,
        )

    schwab.place_order.assert_awaited_once()


# A status read that keeps failing is ambiguous once the settle budget is spent.
ZERO_SETTLE_BUDGET = patch(
    "butterfly_guy.execution.order_manager.POST_CANCEL_SETTLE_SECONDS", 0.0
)


@pytest.mark.asyncio
async def test_post_cancel_raises_ambiguous_when_mark_unknown_also_fails():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    om.intent_queries.mark_unknown.side_effect = RuntimeError("db down")
    schwab.get_order_status.side_effect = RuntimeError("status unavailable")

    with ZERO_SETTLE_BUDGET, pytest.raises(AmbiguousOrderError, match="post-cancel"):
        await om._check_post_cancel_fill("ORD1", 1, intent_id=42)


PENDING_CANCEL = {"status": "PENDING_CANCEL"}
NO_SLEEP = patch("butterfly_guy.execution.order_manager.asyncio.sleep", new=AsyncMock())


@pytest.mark.asyncio
async def test_post_cancel_waits_out_pending_cancel():
    # Live 2026-11-19: the read 0.3 s after the DELETE said PENDING_CANCEL; Schwab closed
    # the order as CANCELED, 0 filled, a second later. That is not a partial fill.
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(
        side_effect=[PENDING_CANCEL, PENDING_CANCEL, {"status": "CANCELED"}]
    )

    with NO_SLEEP:
        assert await om._check_post_cancel_fill("ORD1", 1, order_type="exit") is None

    assert schwab.get_order_status.await_count == 3


@pytest.mark.asyncio
async def test_post_cancel_waits_out_working_then_reports_the_fill():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(side_effect=[{"status": "WORKING"}, filled_order()])

    with NO_SLEEP:
        result = await om._check_post_cancel_fill("ORD1", 1, order_type="exit")

    assert result["post_cancel"] is True
    assert result["fill_price"] == pytest.approx(0.41)


@pytest.mark.asyncio
async def test_post_cancel_that_never_settles_stops_the_bot():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value=PENDING_CANCEL)

    with NO_SLEEP, patch(
        "butterfly_guy.execution.order_manager.POST_CANCEL_SETTLE_SECONDS", 0.0
    ), pytest.raises(PartialFillError, match="still PENDING_CANCEL"):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")


@pytest.mark.asyncio
async def test_post_cancel_partial_fill_stops_the_bot_without_waiting():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value={"status": "PARTIALLY_FILLED"})

    with NO_SLEEP, pytest.raises(PartialFillError, match="partially filled"):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")

    schwab.get_order_status.assert_awaited_once()


@pytest.mark.asyncio
async def test_exit_ladder_moves_on_after_a_pending_cancel_settles():
    settings = make_settings(price_ladder_steps=2, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.20, mark=3.40, ask=3.60)
    schwab.get_order_status = AsyncMock(
        side_effect=[PENDING_CANCEL, {"status": "CANCELED"}, filled_order()]
    )

    with NO_SLEEP, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert schwab.place_order.await_count == 2
    assert result["post_cancel"] is True


@pytest.mark.asyncio
async def test_single_attempt_refuses_live_entry_when_broker_holds_positions():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                {
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260321P05950000",
                        "underlyingSymbol": "$SPX",
                    },
                    "longQuantity": 0,
                    "shortQuantity": 2,
                }
            ]
        }
    }

    with pytest.raises(AmbiguousOrderError, match="option position"):
        await om.execute_single_attempt(
            make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
        )

    om.intent_queries.create_intent.assert_not_awaited()
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_single_attempt_blocks_live_entry_when_position_check_fails():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    schwab.get_account_snapshot.side_effect = RuntimeError("account unavailable")

    result = await om.execute_single_attempt(
        make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
    )

    assert result is None
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_single_attempt_ignores_other_underlying_positions():
    settings = make_settings(paper_trading=False, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                {
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "NDXP  260321P20000000",
                        "underlyingSymbol": "$NDX",
                    },
                    "longQuantity": 1,
                    "shortQuantity": 0,
                }
            ]
        }
    }
    schwab.get_order_status = AsyncMock(return_value=filled_order())

    result = await om.execute_single_attempt(
        make_candidate(5900, 5950, 6000, 2.50), limit_price=2.50
    )

    assert result is not None
    schwab.place_order.assert_awaited_once()


@pytest.mark.asyncio
async def test_wait_for_fill_counts_request_latency_against_timeout():
    om, schwab = make_order_manager(make_settings())
    clock = [0.0]

    async def slow_status(_order_id):
        clock[0] += 6.0
        return {"status": "WORKING"}

    async def fake_sleep(seconds):
        clock[0] += seconds

    schwab.get_order_status = AsyncMock(side_effect=slow_status)
    with patch(
        "butterfly_guy.execution.order_manager.monotonic", new=lambda: clock[0]
    ), patch("butterfly_guy.execution.order_manager.asyncio.sleep", new=fake_sleep):
        result = await om._wait_for_fill("ORD1", 10)

    assert result is False
    # 0s: poll (+6s) and sleep (+2s); 8s: poll (+6s) and sleep (+2s); 16s: deadline.
    assert schwab.get_order_status.await_count == 2


@pytest.mark.asyncio
async def test_post_cancel_status_failure_is_ambiguous():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status.side_effect = RuntimeError("status unavailable")

    with ZERO_SETTLE_BUDGET, pytest.raises(AmbiguousOrderError, match="post-cancel"):
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
    # Step 0: bid anchor + (max_steps-1)*step = 3.20 + 3*0.05 = 3.35
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
    # Step 0: bid anchor + (4-1)*0.05 = 3.35  (best price first)
    # Step 1: bid anchor + (4-2)*0.05 = 3.30  (step down)
    assert calls[0][0][1] == pytest.approx(live_bid + 3 * 0.05)
    assert calls[1][0][1] == pytest.approx(live_bid + 2 * 0.05)


@pytest.mark.parametrize(
    ("underlying", "expected"),
    [("SPX", [3.40, 3.35]), ("XSP", [3.36, 3.31])],
)
@pytest.mark.asyncio
async def test_exit_limits_round_up_to_the_underlyings_increment(underlying, expected):
    settings = make_settings(price_ladder_steps=4)
    om, _ = make_order_manager(settings, underlying=underlying)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    live_spread = LiveSpread(bid=3.21, mark=3.40, ask=3.60)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=live_spread)), \
         patch.object(
             om, "_wait_for_fill", new=AsyncMock(side_effect=[False, broker_fill()])
         ):
        await om.execute_exit(candidate, current_value=2.50, quantity=1)

    limits = [c[0][1] for c in om.builder.build_butterfly_close.call_args_list]
    assert limits == pytest.approx(expected)


async def _exit_limits_for_bids(bids: list[float]) -> list[float]:
    settings = make_settings(price_ladder_steps=4)
    om, _ = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spreads = [LiveSpread(bid=b, mark=b + 0.20, ask=b + 0.40) for b in bids]
    fills = [False] * (len(bids) - 1) + [broker_fill()]
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(side_effect=spreads)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=fills)):
        await om.execute_exit(candidate, current_value=2.50, quantity=1)
    return [c[0][1] for c in om.builder.build_butterfly_close.call_args_list]


@pytest.mark.asyncio
async def test_exit_single_bad_bid_does_not_pin_later_steps():
    # A lone 1.00 tick used to anchor every later step near 1.00.
    limits = await _exit_limits_for_bids([3.20, 1.00, 3.20, 3.20])
    assert limits == pytest.approx([3.35, 2.20, 3.25, 3.20])


@pytest.mark.asyncio
async def test_exit_sustained_bid_decline_still_lowers_the_ladder():
    limits = await _exit_limits_for_bids([3.20, 2.90, 2.60, 2.30])
    assert limits == pytest.approx([3.35, 3.15, 2.95, 2.60])


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
async def test_paper_single_attempt_blocks_fill_above_submitted_limit():
    settings = make_settings(
        paper_trading=True,
        paper_commission_per_contract=0.65,
    )
    om, schwab = make_order_manager(settings, underlying="XSP")
    candidate = make_candidate(5900, 5950, 6000, 0.34)
    spread = LiveSpread(bid=0.20, mark=0.73, ask=0.81)

    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        result = await om.execute_single_attempt(candidate, limit_price=0.40)

    assert result is None
    schwab.place_order.assert_not_awaited()


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


# ---------------------------------------------------------------------------
# execute_exit pricing rules (core/exit_pricing.py)
# ---------------------------------------------------------------------------

async def _exit_limits_for_rule(rule: str, spreads: list[LiveSpread]) -> list[float]:
    settings = make_settings(price_ladder_step=0.10, price_ladder_steps=4, exit_pricing=rule)
    om, _ = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    fills = [False] * (len(spreads) - 1) + [broker_fill()]
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(side_effect=spreads)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=fills)):
        await om.execute_exit(candidate, current_value=2.50, quantity=1)
    return [c[0][1] for c in om.builder.build_butterfly_close.call_args_list]


_PATH = [  # 415-like wide spread, a bad tick, then a restart of the 4-step cycle
    LiveSpread(bid=1.00, mark=1.85, ask=2.70),
    LiveSpread(bid=0.80, mark=1.80, ask=2.80),
    LiveSpread(bid=0.10, mark=0.60, ask=1.10),
    LiveSpread(bid=1.30, mark=1.70, ask=2.10),
    LiveSpread(bid=1.20, mark=1.60, ask=2.00),
    LiveSpread(bid=1.25, mark=1.55, ask=1.85),
]


@pytest.mark.parametrize("rule", EXIT_PRICING_RULES)
@pytest.mark.asyncio
async def test_exit_submits_exactly_the_shared_rule_limits(rule):
    """Live/research parity: execute_exit prices every step with exit_limit."""
    limits = await _exit_limits_for_rule(rule, _PATH)
    bids, mids, expected = [], [], []
    for n, s in enumerate(_PATH):
        bids = (bids + [s.bid])[-3:]
        mids = (mids + [(s.bid + s.ask) / 2])[-3:]
        expected.append(exit_limit(
            rule, n, statistics.median(bids), statistics.median(mids),
            ladder_step=0.10, ladder_steps=4, underlying="SPX",
        ))
    assert limits == pytest.approx(expected)


@pytest.mark.asyncio
async def test_default_exit_pricing_is_the_original_bid_ladder_with_restart():
    assert ExecutionSettings().exit_pricing == "bid_ladder"
    limits = await _exit_limits_for_rule("bid_ladder", _PATH)
    # median bid + (3 - i mod 4) x 0.10, rounded up to $0.05
    assert limits == pytest.approx([1.30, 1.10, 0.90, 0.80, 1.50, 1.45])


@pytest.mark.asyncio
async def test_mid_walk_starts_at_mid_and_holds_at_the_bid():
    limits = await _exit_limits_for_rule("mid_walk", _PATH)
    assert limits[0] == pytest.approx(1.85)
    assert limits[3:] == pytest.approx([0.80, 1.20, 1.25])  # bid anchor, no restart


@pytest.mark.asyncio
async def test_mid_walk_falls_back_to_the_signal_mark_without_quotes():
    settings = make_settings(price_ladder_step=0.10, exit_pricing="mid_walk")
    om, _ = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        await om.execute_exit(candidate, current_value=3.72, quantity=1)
    assert om.builder.build_butterfly_close.call_args[0][1] == pytest.approx(3.75)


def test_exit_pricing_setting_matches_the_rules_and_rejects_unknown_values():
    allowed = ExecutionSettings.model_fields["exit_pricing"].annotation.__args__
    assert tuple(allowed) == EXIT_PRICING_RULES
    with pytest.raises(ValidationError):
        ExecutionSettings(exit_pricing="mid")


@pytest.mark.asyncio
async def test_paper_exit_records_the_live_rule_estimate_without_changing_the_fill():
    settings = make_settings(
        paper_trading=True, price_ladder_step=0.10, paper_commission_per_contract=1.15,
        exit_pricing="mid_walk",
    )
    om, _ = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=1.00, mark=1.85, ask=2.70)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        result = await om.execute_exit(candidate, current_value=1.65, quantity=1)

    diag = result["execution_diagnostics"]
    assert result["fill_price"] == pytest.approx(1.65 - 0.046, abs=0.005)
    assert diag["live_exit_rule"] == "mid_walk"
    assert diag["live_rule_first_limit"] == 1.85
    assert diag["live_rule_exit_estimate"] == round(
        static_quote_estimate("mid_walk", 1.00, 1.85, ladder_step=0.10, ladder_steps=4,
                              underlying="SPX") - 0.046, 2)


@pytest.mark.asyncio
async def test_paper_exit_live_rule_fields_are_empty_without_a_quote():
    settings = make_settings(paper_trading=True)
    om, _ = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)):
        result = await om.execute_exit(candidate, current_value=3.30, quantity=1)
    diag = result["execution_diagnostics"]
    assert diag["live_exit_rule"] == "bid_ladder"
    assert diag["live_rule_exit_estimate"] is None


# ---------------------------------------------------------------------------
# Post-cancel settle: 2026-11-19 halt audit (reports/execution_audits/
# spx-live-halt-audit-20261119). Payload shapes are Schwab's from live exit 100001.
# ---------------------------------------------------------------------------

def live_1119_canceled_exit() -> dict:
    """Schwab's final read of live exit 100001: CANCELED, 0 filled, plus an
    EXECUTION activity of executionType CANCELED at price 0 (not a fill)."""
    return json.loads(
        (Path(__file__).parent / "fixtures/live_20261119_exit_cancel_redacted.json").read_text()
    )


def live_1119_status(status: str, **fields) -> dict:
    order = live_1119_canceled_exit()
    order.pop("orderActivityCollection")
    order.pop("closeTime")
    order.update(status=status, remainingQuantity=1.0, cancelable=True, **fields)
    return order


def fake_clock():
    """A monotonic clock that only advances when the code sleeps."""
    clock = [0.0]

    async def sleep(seconds):
        clock[0] += seconds

    return clock, patch(
        "butterfly_guy.execution.order_manager.monotonic", new=lambda: clock[0]
    ), patch("butterfly_guy.execution.order_manager.asyncio.sleep", new=sleep)


@pytest.mark.asyncio
async def test_post_cancel_1119_payloads_settle_as_unfilled():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status = AsyncMock(
        side_effect=[live_1119_status("PENDING_CANCEL"), live_1119_canceled_exit()]
    )

    with NO_SLEEP:
        assert await om._check_post_cancel_fill("ORD1", 1, "exit", intent_id=100001) is None

    final = om.intent_queries.update_broker_status.await_args_list[-1].args
    assert final[:2] == (100001, "CANCELED")


@pytest.mark.asyncio
async def test_post_cancel_pending_for_the_whole_budget_halts_before_a_late_cancel():
    om, schwab = make_order_manager(make_settings())
    reads = [live_1119_status("PENDING_CANCEL")] * 8 + [live_1119_status("WORKING")] * 8
    schwab.get_order_status = AsyncMock(side_effect=[*reads, live_1119_canceled_exit()])
    clock, mono, sleep = fake_clock()

    with mono, sleep, pytest.raises(PartialFillError, match="still WORKING 15s after cancel"):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")

    assert clock[0] == pytest.approx(15.0)
    assert schwab.get_order_status.await_count == 16  # the CANCELED at 16 s is never read


@pytest.mark.asyncio
async def test_post_cancel_canceled_with_a_filled_quantity_is_a_partial_fill():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(
        return_value={**live_1119_canceled_exit(), "filledQuantity": 1.0}
    )

    with NO_SLEEP, pytest.raises(PartialFillError, match="filled quantity"):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")


@pytest.mark.asyncio
async def test_post_cancel_filled_child_under_a_canceled_parent_is_a_partial_fill():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value={
        "status": "CANCELED",
        "filledQuantity": 0.0,
        "childOrderStrategies": [{"status": "FILLED", "orderId": "C1"}],
    })

    with NO_SLEEP, pytest.raises(PartialFillError):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", ["PENDING_REPLACE", "AWAITING_MANUAL_REVIEW", "NEW", "UNKNOWN", "SOMETHING_NEW"]
)
async def test_post_cancel_waits_on_any_non_final_status(status):
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(
        side_effect=[live_1119_status(status), live_1119_canceled_exit()]
    )

    with NO_SLEEP:
        assert await om._check_post_cancel_fill("ORD1", 1, order_type="exit") is None

    assert schwab.get_order_status.await_count == 2


@pytest.mark.asyncio
async def test_post_cancel_never_final_status_halts():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value=live_1119_status("PENDING_REPLACE"))
    _, mono, sleep = fake_clock()

    with mono, sleep, pytest.raises(PartialFillError, match="still PENDING_REPLACE"):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["REJECTED", "EXPIRED"])
async def test_post_cancel_terminal_failure_stops_the_ladder(status):
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value=live_1119_status(status))

    with NO_SLEEP, pytest.raises(TerminalOrderError):
        await om._check_post_cancel_fill("ORD1", 1, order_type="exit")


@pytest.mark.asyncio
@pytest.mark.parametrize("order_type", ["entry", "exit"])
async def test_post_cancel_replaced_hands_over_exits_and_stops_entries(order_type):
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value=live_1119_status("REPLACED"))

    with NO_SLEEP:
        if order_type == "exit":
            with pytest.raises(OperatorExitTakeoverError, match="operator replaced"):
                await om._check_post_cancel_fill("ORD1", 1, order_type=order_type)
        else:
            with pytest.raises(EntryOrderReplacedError, match="operator replaced"):
                await om._check_post_cancel_fill("ORD1", 1, order_type=order_type)


@pytest.mark.asyncio
async def test_exit_post_cancel_replaced_stops_before_another_intent_or_order():
    om, schwab = make_order_manager(make_settings(price_ladder_steps=2))
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    candidate.lower_symbol = "SPXW  260321P05900000"
    candidate.center_symbol = "SPXW  260321P05950000"
    candidate.upper_symbol = "SPXW  260321P06000000"
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": [
        {
            "instrument": {"assetType": "OPTION", "symbol": symbol},
            "longQuantity": max(quantity, 0), "shortQuantity": max(-quantity, 0),
        }
        for symbol, quantity in (
            (candidate.lower_symbol, 1), (candidate.center_symbol, -2),
            (candidate.upper_symbol, 1),
        )
    ]}}
    # No working replacement is listed: the REPLACED status itself must stop us.
    schwab.get_todays_orders.return_value = []
    payload = live_1119_status("REPLACED")
    schwab.get_order_status = AsyncMock(return_value=payload)

    with patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=[False, broker_fill()])), \
         pytest.raises(OperatorExitTakeoverError, match="operator replaced"):
        await om.execute_exit(candidate, current_value=3.00, trade_id=7)

    om.intent_queries.create_intent.assert_awaited_once()
    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_awaited_once_with("ORD1")
    om.intent_queries.update_broker_status.assert_any_await(42, "REPLACED", payload)
    om.intent_queries.mark_unknown.assert_not_awaited()


MALFORMED_STATUS_READS = {
    "empty": {},
    "null": {"status": None},
    "blank": {"status": ""},
    "whitespace": {"status": "  "},
    "parent-missing-child-final": {
        "childOrderStrategies": [{"orderId": "C1", "status": "CANCELED"}],
    },
    "parent-final-child-missing": {
        "status": "CANCELED", "childOrderStrategies": [{"orderId": "C1"}],
    },
}


@pytest.mark.asyncio
@pytest.mark.parametrize("read", MALFORMED_STATUS_READS.values(), ids=MALFORMED_STATUS_READS)
async def test_post_cancel_read_without_a_status_is_never_settled(read):
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status = AsyncMock(return_value=read)
    clock, mono, sleep = fake_clock()

    with mono, sleep, pytest.raises(PartialFillError, match="15s after cancel; reconcile"):
        await om._check_post_cancel_fill("ORD1", 1, "exit", intent_id=42)

    assert clock[0] == pytest.approx(15.0)
    om.intent_queries.update_broker_status.assert_not_awaited()  # nothing authoritative
    om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("final", ["canceled", "filled"])
async def test_post_cancel_recovers_from_one_read_without_a_status(final):
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    last = live_1119_canceled_exit() if final == "canceled" else filled_order()
    schwab.get_order_status = AsyncMock(side_effect=[{}, last])
    _, mono, sleep = fake_clock()

    with mono, sleep:
        result = await om._check_post_cancel_fill("ORD1", 1, "exit", intent_id=42)

    assert schwab.get_order_status.await_count == 2
    assert (result is None) == (final == "canceled")
    om.intent_queries.update_broker_status.assert_awaited_once_with(42, last["status"], last)


@pytest.mark.asyncio
@pytest.mark.parametrize("with_intents", [True, False], ids=["intents", "no-intent-store"])
async def test_exit_without_post_cancel_status_sends_no_second_order(with_intents):
    # Without an intent store no unique index stands in the way: the status rule must.
    om, schwab = make_order_manager(make_settings(price_ladder_steps=2))
    if with_intents:
        om.intent_queries = AsyncMock()
        om.intent_queries.create_intent.return_value = 42
    schwab.place_order = AsyncMock(side_effect=["ORD1", RuntimeError("a second order")])
    schwab.get_order_status = AsyncMock(return_value={})
    _, mono, sleep = fake_clock()

    with mono, sleep, patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)), \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=None)), \
         pytest.raises(PartialFillError, match="missing its status 15s after cancel"):
        await om.execute_exit(make_candidate(5900, 5950, 6000, 2.50), 3.00, trade_id=7)

    schwab.place_order.assert_awaited_once()
    if with_intents:
        om.intent_queries.create_intent.assert_awaited_once()
        om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
async def test_entry_without_post_cancel_status_stops_instead_of_moving_on():
    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value={"status": None})
    _, mono, sleep = fake_clock()

    with mono, sleep, patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)), \
         pytest.raises(PartialFillError, match="missing its status"):
        await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 2.50), 2.50)

    schwab.place_order.assert_awaited_once()


def _working_replacement() -> dict:
    """The operator's order that replaced the bot's: a new id, still working."""
    return {**live_1119_status("WORKING"), "orderId": "OPERATOR-2"}


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement_listed", [False, True], ids=["none-listed", "working"])
async def test_entry_poll_replaced_stops_without_cancel_or_another_order(replacement_listed):
    # An operator edit of the resting entry: stop now, not at the fill timeout, and
    # leave both the REPLACED original and any replacement alone.
    om, schwab = make_order_manager(make_settings(retry_interval_seconds=20))
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    # Listed only after the bot submitted: the pre-submit working-order check saw none.
    listed = [_working_replacement()] if replacement_listed else []
    schwab.get_todays_orders = AsyncMock(side_effect=[[], *[listed] * 5])
    payload = live_1119_status("REPLACED")
    reads = iter([live_1119_status("WORKING")])
    schwab.get_order_status = AsyncMock(side_effect=lambda _order_id: next(reads, payload))
    clock, mono, sleep = fake_clock()

    with mono, sleep, pytest.raises(EntryOrderReplacedError, match="operator replaced"):
        await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 2.50), 2.50)

    assert clock[0] == pytest.approx(2.0)  # one poll interval, not the 20 s fill wait
    om.intent_queries.create_intent.assert_awaited_once()
    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_not_called()
    assert om.intent_queries.update_broker_status.await_args_list[-1].args == (
        42, "REPLACED", payload
    )
    om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement_listed", [False, True], ids=["none-listed", "working"])
async def test_entry_post_cancel_replaced_stops_before_another_order(replacement_listed):
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent.return_value = 42
    # Listed only after the bot submitted: the pre-submit working-order check saw none.
    listed = [_working_replacement()] if replacement_listed else []
    schwab.get_todays_orders = AsyncMock(side_effect=[[], *[listed] * 5])
    payload = live_1119_status("REPLACED")
    schwab.get_order_status = AsyncMock(return_value=payload)

    with NO_SLEEP, patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)), \
         pytest.raises(EntryOrderReplacedError, match="operator replaced"):
        await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 2.50), 2.50)

    schwab.place_order.assert_awaited_once()
    schwab.cancel_order.assert_awaited_once_with("ORD1")  # the bot's own, never the operator's
    assert om.intent_queries.update_broker_status.await_args_list[-1].args == (
        42, "REPLACED", payload
    )
    om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["CANCELED", "REJECTED", "EXPIRED"])
async def test_entry_poll_final_statuses_keep_their_handling(status):
    om, schwab = make_order_manager(make_settings(retry_interval_seconds=20))
    schwab.get_order_status = AsyncMock(return_value=live_1119_status(status))
    _, mono, sleep = fake_clock()

    with mono, sleep:
        if status == "CANCELED":
            assert await om._wait_for_fill("ORD1", 20) is False
        else:
            with pytest.raises(TerminalOrderError, match=status):
                await om._wait_for_fill("ORD1", 20)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        "API call failed after 3 retries: HTTP 429 rate limited on get_order",
        "API call failed after 3 retries: Server error '502 Bad Gateway'",
        "API call failed after 3 retries: ReadTimeout",
        "API call failed after 3 retries: [Errno 104] Connection reset by peer",
        "API call failed with non-retryable HTTP 401: Unauthorized",
    ],
)
async def test_post_cancel_one_failed_status_read_does_not_halt(error):
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status = AsyncMock(
        side_effect=[RuntimeError(error), live_1119_canceled_exit()]
    )

    with NO_SLEEP:
        assert await om._check_post_cancel_fill("ORD1", 1, "exit", intent_id=7) is None

    om.intent_queries.mark_unknown.assert_not_awaited()


@pytest.mark.asyncio
async def test_post_cancel_status_reads_failing_for_the_whole_budget_are_ambiguous():
    om, schwab = make_order_manager(make_settings())
    om.intent_queries = AsyncMock()
    schwab.get_order_status = AsyncMock(side_effect=RuntimeError("status unavailable"))
    _, mono, sleep = fake_clock()

    with mono, sleep, pytest.raises(AmbiguousOrderError, match="post-cancel"):
        await om._check_post_cancel_fill("ORD1", 1, "exit", intent_id=7)

    om.intent_queries.mark_unknown.assert_awaited_once_with(7, "status unavailable")


@pytest.mark.asyncio
async def test_exit_cancel_that_lost_the_race_books_the_fill_and_sends_no_more_steps():
    settings = make_settings(price_ladder_steps=4, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.20, mark=3.40, ask=3.60)
    schwab.get_order_status = AsyncMock(side_effect=[PENDING_CANCEL, filled_order()])

    with NO_SLEEP, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert result["post_cancel"] is True
    schwab.place_order.assert_awaited_once()


@pytest.mark.asyncio
async def test_exit_cancel_refused_because_the_order_filled_books_the_fill():
    # Schwab refuses to DELETE a filled order; that refusal is not an unknown outcome.
    settings = make_settings(price_ladder_steps=4, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.20, mark=3.40, ask=3.60)
    schwab.cancel_order = AsyncMock(side_effect=RuntimeError(
        "API call failed with non-retryable HTTP 400: order is not cancelable"
    ))
    schwab.get_order_status = AsyncMock(return_value=filled_order())

    with NO_SLEEP, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)):
        result = await om.execute_exit(candidate, current_value=2.50, quantity=1)

    assert result["post_cancel"] is True
    schwab.place_order.assert_awaited_once()


@pytest.mark.asyncio
async def test_exit_cancel_refused_with_the_order_still_working_halts_without_a_new_step():
    settings = make_settings(price_ladder_steps=4, retry_interval_seconds=0)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=3.20, mark=3.40, ask=3.60)
    schwab.cancel_order = AsyncMock(side_effect=RuntimeError("API call failed after 3 retries"))
    schwab.get_order_status = AsyncMock(return_value=live_1119_status("WORKING"))
    _, mono, sleep = fake_clock()

    with mono, sleep, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=False)), \
         pytest.raises(PartialFillError, match="still WORKING"):
        await om.execute_exit(candidate, current_value=2.50, quantity=1)

    schwab.place_order.assert_awaited_once()


def _broker_event_log(om, schwab, cancel_reads: list[list[dict]], final: dict):
    """Record place/cancel/status calls; each cancel settles through its own reads."""
    events: list[tuple[str, str]] = []
    orders = iter(f"ORD{n}" for n in range(1, 100))
    pending: dict[str, list[dict]] = {}
    reads = iter(cancel_reads)

    async def place(_spec):
        order_id = next(orders)
        events.append(("place", order_id))
        return order_id

    async def cancel(order_id):
        events.append(("cancel", order_id))
        pending[order_id] = list(next(reads))

    async def status(order_id):
        queue = pending.get(order_id)
        read = queue.pop(0) if queue else final
        events.append(("status:" + read["status"], order_id))
        return read

    schwab.place_order = AsyncMock(side_effect=place)
    schwab.cancel_order = AsyncMock(side_effect=cancel)
    schwab.get_order_status = AsyncMock(side_effect=status)
    return events


def _assert_one_order_at_a_time(events):
    """Every new order follows a final read of the one before it: no double exit."""
    live: str | None = None
    for event, order_id in events:
        if event == "place":
            assert live is None, f"{order_id} placed while {live} was not final: {events}"
            live = order_id
        elif event in {"status:CANCELED", "status:FILLED"} and order_id == live:
            live = None


@pytest.mark.asyncio
async def test_mid_walk_full_exit_with_pending_cancel_on_every_cancel():
    # Day-2 config: mid_walk, 4 steps, 0.10, 20 s. Every cancel reads PENDING_CANCEL
    # twice before CANCELED; the fifth order (held at the bid) fills.
    settings = make_settings(
        exit_pricing="mid_walk", price_ladder_steps=4, price_ladder_step=0.10,
        retry_interval_seconds=20,
    )
    om, schwab = make_order_manager(settings)
    om.intent_queries = AsyncMock()
    om.intent_queries.create_intent = AsyncMock(side_effect=range(1, 100))
    candidate = make_candidate(5900, 5950, 6000, 3.75)
    spread = LiveSpread(bid=1.85, mark=1.97, ask=2.10)  # live 100001's quote at signal
    cancel_reads = [[PENDING_CANCEL, PENDING_CANCEL, {"status": "CANCELED"}]] * 4
    events = _broker_event_log(om, schwab, cancel_reads, final={"status": "CANCELED"})
    fills = [False, False, False, False, broker_fill()]

    with NO_SLEEP, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=fills)):
        result = await om.execute_exit(candidate, current_value=1.97, quantity=1)

    assert result is not None and result["ladder_steps"][-1]["filled"] is True
    limits = [c[0][1] for c in om.builder.build_butterfly_close.call_args_list]
    assert limits == pytest.approx([2.00, 1.95, 1.90, 1.85, 1.85])  # mid -> bid, hold
    assert [e for e, _ in events].count("cancel") == 4
    _assert_one_order_at_a_time(events)
    statuses = [c.args[1] for c in om.intent_queries.update_broker_status.await_args_list]
    assert statuses.count("CANCELED") == 4 and "PENDING_CANCEL" in statuses


@pytest.mark.asyncio
async def test_bid_ladder_never_overlaps_orders_across_a_restart_cycle():
    settings = make_settings(price_ladder_steps=4, price_ladder_step=0.10)
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 3.75)
    spread = LiveSpread(bid=1.85, mark=1.97, ask=2.10)
    cancel_reads = [[PENDING_CANCEL, {"status": "WORKING"}, {"status": "CANCELED"}]] * 6
    events = _broker_event_log(om, schwab, cancel_reads, final={"status": "CANCELED"})
    fills = [False] * 6 + [broker_fill()]

    with NO_SLEEP, \
         patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(side_effect=fills)):
        await om.execute_exit(candidate, current_value=1.97, quantity=1)

    limits = [c[0][1] for c in om.builder.build_butterfly_close.call_args_list]
    assert limits == pytest.approx([2.15, 2.05, 1.95, 1.85, 2.15, 2.05, 1.95])
    _assert_one_order_at_a_time(events)


@pytest.mark.asyncio
async def test_live_test_exit_refetches_a_stale_quote_instead_of_halting():
    # One stale leg (> live_test_quote_max_age_seconds) or a 429 burst returns None.
    settings = make_settings(price_ladder_steps=1, live_test_date=dt.date(2026, 11, 20))
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    spread = LiveSpread(bid=1.85, mark=1.97, ask=2.10)
    fetch = AsyncMock(side_effect=[None, None, None, spread])
    _, mono, sleep = fake_clock()

    with mono, sleep, patch.object(om, "_fetch_live_spread", new=fetch), \
         patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await om.execute_exit(candidate, current_value=1.97, quantity=1)

    assert result is not None
    schwab.place_order.assert_awaited_once()
    assert om.builder.build_butterfly_close.call_args[0][1] == pytest.approx(1.85)


@pytest.mark.asyncio
async def test_live_test_exit_halts_without_an_order_when_quotes_stay_stale():
    settings = make_settings(live_test_date=dt.date(2026, 11, 20))
    om, schwab = make_order_manager(settings)
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    fetch = AsyncMock(return_value=None)
    clock, mono, sleep = fake_clock()

    with mono, sleep, patch.object(om, "_fetch_live_spread", new=fetch), \
         pytest.raises(BrokerFillError, match="fresh leg quotes"):
        await om.execute_exit(candidate, current_value=1.97, quantity=1)

    assert clock[0] == pytest.approx(20.0)
    schwab.place_order.assert_not_awaited()
