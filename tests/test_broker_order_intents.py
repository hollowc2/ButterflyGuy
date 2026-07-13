from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from butterfly_guy.scripts.run_live import (
    BrokerStateGate,
    _assert_broker_state_matches_db,
    _repair_filled_entry_intent,
)


def broker_fill_payload(*, order_type: str = "NET_DEBIT") -> dict:
    opening = order_type == "NET_DEBIT"
    return {
        "status": "FILLED",
        "orderType": order_type,
        "quantity": 1,
        "filledQuantity": 1,
        "remainingQuantity": 0,
        "orderLegCollection": [
            {
                "legId": 1,
                "instruction": "BUY_TO_OPEN" if opening else "SELL_TO_CLOSE",
                "quantity": 1,
            },
            {
                "legId": 2,
                "instruction": "SELL_TO_OPEN" if opening else "BUY_TO_CLOSE",
                "quantity": 2,
            },
            {
                "legId": 3,
                "instruction": "BUY_TO_OPEN" if opening else "SELL_TO_CLOSE",
                "quantity": 1,
            },
        ],
        "orderActivityCollection": [{
            "executionLegs": [
                {"legId": 1, "price": 0.05, "quantity": 1, "time": "2026-06-25T14:31:00Z"},
                {"legId": 2, "price": 0.14, "quantity": 2, "time": "2026-06-25T14:31:00Z"},
                {"legId": 3, "price": 0.64, "quantity": 1, "time": "2026-06-25T14:31:00Z"},
            ]
        }],
    }


@pytest.mark.asyncio
async def test_startup_allows_bot_owned_working_order():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "status": "WORKING",
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    await _assert_broker_state_matches_db(schwab, "SPX", [], intents)

    intents.update_broker_status.assert_awaited_once()


@pytest.mark.asyncio
async def test_startup_matches_bot_intent_to_nested_order_id():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    child = {
        "orderId": "BOT1",
        "status": "WORKING",
        "orderLegCollection": [
            {"instrument": {"symbol": "SPXW  260625C06000000"}}
        ],
    }
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "WRAPPER1",
            "status": "WORKING",
            "childOrderStrategies": [child],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    await _assert_broker_state_matches_db(schwab, "SPX", [], intents)

    intents.update_broker_status.assert_awaited_once_with(1, "WORKING", child)


@pytest.mark.asyncio
async def test_startup_rejects_unknown_working_order():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "OTHER1",
            "status": "WORKING",
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = []

    with pytest.raises(RuntimeError, match="unknown working SPX order"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
async def test_startup_rejects_unknown_nested_working_order():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "WRAPPER1",
            "status": "CANCELED",
            "childOrderStrategies": [
                {
                    "orderId": "OTHER1",
                    "status": "WORKING",
                    "orderLegCollection": [
                        {"instrument": {"symbol": "SPXW  260625C06000000"}}
                    ],
                }
            ],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = []

    with pytest.raises(RuntimeError, match="unknown working SPX order"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
@pytest.mark.parametrize("unsafe_status", ["PARTIALLY_FILLED", "CANCEL_PENDING"])
async def test_startup_rejects_bot_owned_partial_or_cancel_pending_order(unsafe_status):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "status": unsafe_status,
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    with pytest.raises(RuntimeError, match="manual reconciliation"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
@pytest.mark.parametrize("unsafe_status", ["PARTIALLY_FILLED", "CANCEL_PENDING"])
async def test_startup_rejects_bot_owned_partial_or_cancel_pending_child_order(
    unsafe_status,
):
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "status": "WORKING",
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
            "childOrderStrategies": [{"status": unsafe_status}],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    with pytest.raises(RuntimeError, match="manual reconciliation"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
async def test_startup_rejects_unmapped_child_status():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "status": "WORKING",
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
            "childOrderStrategies": [{"status": "NEW_BROKER_STATE"}],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    with pytest.raises(RuntimeError, match="unmapped SPX order status"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
async def test_startup_rejects_missing_order_status():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "orderLegCollection": [
                {"instrument": {"symbol": "SPXW  260625C06000000"}}
            ],
        }
    ]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {"id": 1, "broker_order_id": "BOT1", "status": "SUBMITTED"}
    ]

    with pytest.raises(RuntimeError, match="missing SPX order status"):
        await _assert_broker_state_matches_db(schwab, "SPX", [], intents)


@pytest.mark.asyncio
async def test_filled_entry_intent_repairs_open_trade_only_with_matching_legs_and_fill():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {
        "securitiesAccount": {
            "positions": [
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06000000",
                    },
                },
                {
                    "shortQuantity": 2,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06050000",
                    },
                },
                {
                    "longQuantity": 1,
                    "instrument": {
                        "assetType": "OPTION",
                        "symbol": "SPXW  260625C06100000",
                    },
                },
            ]
        }
    }
    order = {**broker_fill_payload(), "orderId": "BOT1"}
    schwab.get_todays_orders.return_value = [order]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {
            "id": 1,
            "underlying": "SPX",
            "trade_date": "2026-06-25",
            "side": "ENTRY",
            "status": "SUBMITTED",
            "broker_order_id": "BOT1",
            "trade_id": None,
            "quantity": 1,
            "candidate_snapshot": {
                "direction": "CALL",
                "wing_width": 50,
                "center_strike": 6050.0,
                "lower_strike": 6000.0,
                "upper_strike": 6100.0,
                "lower_symbol": "SPXW  260625C06000000",
                "center_symbol": "SPXW  260625C06050000",
                "upper_symbol": "SPXW  260625C06100000",
            },
        }
    ]
    trades = AsyncMock()
    trades.insert_trade.return_value = 99

    await _assert_broker_state_matches_db(schwab, "SPX", [], intents, trades)

    trades.insert_trade.assert_awaited_once()
    intents.link_trade.assert_awaited_once_with(1, 99)


@pytest.mark.asyncio
async def test_filled_entry_intent_rejects_wrong_broker_ratio():
    intent = {
        "quantity": 1,
        "raw_broker_payload": broker_fill_payload(),
        "candidate_snapshot": {
            "lower_symbol": "SPXW  260625C06000000",
            "center_symbol": "SPXW  260625C06050000",
            "upper_symbol": "SPXW  260625C06100000",
        },
    }
    trades = AsyncMock()

    with pytest.raises(RuntimeError, match="legs/quantities"):
        await _repair_filled_entry_intent(
            intent,
            {
                "SPXW  260625C06000000": 1,
                "SPXW  260625C06050000": -1,
                "SPXW  260625C06100000": 1,
            },
            trades,
        )

    trades.insert_trade.assert_not_awaited()


@pytest.mark.asyncio
async def test_filled_entry_intent_rejects_zero_quantity():
    intent = {
        "quantity": 0,
        "raw_broker_payload": broker_fill_payload(),
        "candidate_snapshot": {
            "lower_symbol": "SPXW  260625C06000000",
            "center_symbol": "SPXW  260625C06050000",
            "upper_symbol": "SPXW  260625C06100000",
        },
    }
    trades = AsyncMock()

    with pytest.raises(RuntimeError, match="invalid leg symbols or quantity"):
        await _repair_filled_entry_intent(
            intent,
            {
                "SPXW  260625C06000000": 1,
                "SPXW  260625C06050000": -2,
                "SPXW  260625C06100000": 1,
            },
            trades,
        )

    trades.insert_trade.assert_not_awaited()


@pytest.mark.asyncio
async def test_filled_exit_intent_repairs_open_trade_only_when_broker_flat():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    order = {**broker_fill_payload(order_type="NET_CREDIT"), "orderId": "BOT2"}
    schwab.get_todays_orders.return_value = [order]
    intents = AsyncMock()
    intents.intents_for_day.return_value = [
        {
            "id": 2,
            "underlying": "SPX",
            "trade_date": "2026-06-25",
            "side": "EXIT",
            "status": "SUBMITTED",
            "broker_order_id": "BOT2",
            "trade_id": 99,
            "candidate_snapshot": {"exit_reason": "profit_take"},
        }
    ]
    trades = AsyncMock()
    trades.close_trade.return_value = True

    await _assert_broker_state_matches_db(
        schwab,
        "SPX",
        [
            {
                "id": 99,
                "entry_price": 2.00,
                "peak_value": 3.75,
                "lower_symbol": "SPXW  260625C06000000",
                "center_symbol": "SPXW  260625C06050000",
                "upper_symbol": "SPXW  260625C06100000",
                "quantity": 1,
            }
        ],
        intents,
        trades,
    )

    trades.close_trade.assert_awaited_once()
    assert trades.close_trade.await_args.args[0] == 99
    assert trades.close_trade.await_args.args[1] == 0.41


def test_broker_state_gate_records_unsafe_reason():
    gate = BrokerStateGate()

    gate.set_unsafe("unknown broker order")

    assert gate.unsafe
    assert gate.reason == "unknown broker order"
    gate.clear()
    assert not gate.unsafe
