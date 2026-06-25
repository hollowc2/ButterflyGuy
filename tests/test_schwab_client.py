from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.data.schwab_client import SchwabClientWrapper


@pytest.mark.asyncio
async def test_place_order_submits_once_without_retry_wrapper():
    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    schwab._account_hash = "HASH"
    schwab._client = MagicMock()
    response = MagicMock(headers={"Location": "https://api/orders/ORD1"})
    response.raise_for_status = MagicMock()
    schwab.client.place_order = AsyncMock(return_value=response)
    schwab._retry = AsyncMock()

    order_id = await schwab.place_order({"orderType": "LIMIT"})

    assert order_id == "ORD1"
    schwab.client.place_order.assert_awaited_once()
    schwab._retry.assert_not_called()


@pytest.mark.asyncio
async def test_place_order_missing_location_does_not_retry():
    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    schwab._account_hash = "HASH"
    schwab._client = MagicMock()
    response = MagicMock(headers={})
    response.raise_for_status = MagicMock()
    schwab.client.place_order = AsyncMock(return_value=response)
    schwab._retry = AsyncMock()

    with pytest.raises(RuntimeError, match="missing Location"):
        await schwab.place_order({"orderType": "LIMIT"})

    schwab.client.place_order.assert_awaited_once()
    schwab._retry.assert_not_called()
