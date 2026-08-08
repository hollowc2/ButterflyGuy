from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import stat
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
    monkeypatch.setattr("schwab.auth.client_from_access_functions", client_factory)
    monkeypatch.setattr("butterfly_guy.data.schwab_client.log.info", log_info)

    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    await schwab.initialize()

    log_info.assert_called_once_with("schwab_client_initialized")


@pytest.mark.asyncio
async def test_initialize_fails_closed_when_authentication_fails(monkeypatch):
    response = MagicMock(status_code=401)
    client = MagicMock(get_account_numbers=AsyncMock(return_value=response))
    monkeypatch.setattr(
        "schwab.auth.client_from_access_functions", MagicMock(return_value=client)
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


@pytest.mark.asyncio
async def test_intraday_bars_for_day_requests_extended_hours():
    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    schwab._client = MagicMock()
    schwab.client.PriceHistory.PeriodType.DAY = "day"
    schwab.client.PriceHistory.FrequencyType.MINUTE = "minute"
    schwab.client.PriceHistory.Frequency.EVERY_MINUTE = 1
    response = MagicMock()
    response.json.return_value = {"candles": [{"datetime": 1, "close": 17.10}]}
    schwab._retry = AsyncMock(return_value=response)

    candles = await schwab.get_intraday_bars_for_day(
        "BMNR",
        dt.date(2026, 7, 23),
        include_extended_hours=True,
    )

    assert candles == [{"datetime": 1, "close": 17.10}]
    assert schwab._retry.await_args.kwargs["need_extended_hours_data"] is True


def _token_document(access_token: str) -> dict:
    return {"creation_timestamp": 1786000000, "token": {"access_token": access_token}}


async def _accessors(monkeypatch, token_path):
    """Initialize a wrapper against a real token file, returning its read/write funcs."""
    captured = {}

    def factory(*, token_read_func, token_write_func, **_kwargs):
        captured["read"] = token_read_func
        captured["write"] = token_write_func
        response = MagicMock(status_code=200)
        response.json.return_value = [{"accountNumber": "123", "hashValue": "H"}]
        return MagicMock(get_account_numbers=AsyncMock(return_value=response))

    monkeypatch.setattr("schwab.auth.client_from_access_functions", factory)
    settings = SchwabSettings(account_id="123", token_path=str(token_path))
    await SchwabClientWrapper(settings).initialize()
    return captured


@pytest.mark.asyncio
async def test_token_is_read_through_the_shared_store(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text(json.dumps(_token_document("first")))
    token_path.chmod(0o600)

    captured = await _accessors(monkeypatch, token_path)

    assert captured["read"]() == _token_document("first")


@pytest.mark.asyncio
async def test_token_write_replaces_atomically_and_stays_private(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text(json.dumps(_token_document("first")))
    token_path.chmod(0o600)
    original_inode = token_path.stat().st_ino

    captured = await _accessors(monkeypatch, token_path)
    captured["write"](_token_document("second"))

    # A new inode is the proof of os.replace: schwab-py's default writer truncates in
    # place, which is what could leave a torn document under a concurrent gateway write.
    assert token_path.stat().st_ino != original_inode
    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert json.loads(token_path.read_text()) == _token_document("second")


@pytest.mark.asyncio
async def test_token_write_contends_for_the_shared_lock(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    token_path.write_text(json.dumps(_token_document("first")))
    token_path.chmod(0o600)

    captured = await _accessors(monkeypatch, token_path)
    monkeypatch.setattr("butterfly_guy.data.schwab_client.TOKEN_LOCK_TIMEOUT", 0.1)
    log_error = MagicMock()
    monkeypatch.setattr("butterfly_guy.data.schwab_client.log.error", log_error)

    lock_fd = os.open(tmp_path / ".tokens.json.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        # A blocked persist must not take the trading loop down with it.
        captured["write"](_token_document("second"))
    finally:
        os.close(lock_fd)

    log_error.assert_called_once_with("schwab_token_persist_failed")
    assert json.loads(token_path.read_text()) == _token_document("first")
