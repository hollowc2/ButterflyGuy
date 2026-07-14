from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.data.schwab_client import SchwabClientWrapper


@pytest.mark.asyncio
async def test_initialize_does_not_log_account_identifiers(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.return_value = [{"accountNumber": "123", "hashValue": "SECRET_HASH"}]
    client = MagicMock(get_account_numbers=AsyncMock(return_value=response))
    client_factory = MagicMock(return_value=client)
    log_info = MagicMock()
    monkeypatch.setattr("schwab.auth.client_from_token_file", client_factory)
    monkeypatch.setattr("butterfly_guy.data.schwab_client.log.info", log_info)

    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    await schwab.initialize()

    log_info.assert_called_once_with("schwab_client_initialized")


@pytest.mark.asyncio
async def test_initialize_fails_closed_when_authentication_fails(monkeypatch):
    response = MagicMock(status_code=401)
    client = MagicMock(get_account_numbers=AsyncMock(return_value=response))
    monkeypatch.setattr(
        "schwab.auth.client_from_token_file", MagicMock(return_value=client)
    )

    with pytest.raises(RuntimeError, match="Failed to get account numbers: 401"):
        await SchwabClientWrapper(SchwabSettings(account_id="redacted")).initialize()


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
