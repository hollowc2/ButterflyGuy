from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from butterfly_guy.scripts.run_live import (
    BrokerStateGate,
    _assert_broker_state_matches_db,
    _repair_filled_entry_intent,
)


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
async def test_startup_rejects_bot_owned_partial_order():
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = {"securitiesAccount": {"positions": []}}
    schwab.get_todays_orders.return_value = [
        {
            "orderId": "BOT1",
            "status": "PARTIALLY_FILLED",
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
    order = {
        "orderId": "BOT1",
        "status": "FILLED",
        "filledPrice": 2.15,
        "closeTime": "2026-06-25T14:31:00Z",
    }
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
        "raw_broker_payload": {
            "status": "FILLED",
            "filledPrice": 2.15,
            "closeTime": "2026-06-25T14:31:00Z",
        },
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
        "raw_broker_payload": {
            "status": "FILLED",
            "filledPrice": 2.15,
            "closeTime": "2026-06-25T14:31:00Z",
        },
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
    order = {
        "orderId": "BOT2",
        "status": "FILLED",
        "filledPrice": 3.25,
        "closeTime": "2026-06-25T19:45:00Z",
    }
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
    assert trades.close_trade.await_args.args[1] == 3.25


def test_broker_state_gate_records_unsafe_reason():
    gate = BrokerStateGate()

    gate.set_unsafe("unknown broker order")

    assert gate.unsafe
    assert gate.reason == "unknown broker order"
    gate.clear()
    assert not gate.unsafe
