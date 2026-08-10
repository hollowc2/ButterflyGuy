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
async def test_token_write_rejects_an_older_reauthorization_lineage(monkeypatch, tmp_path):
    token_path = tmp_path / "tokens.json"
    original = _token_document("original")
    token_path.write_text(json.dumps(original))
    token_path.chmod(0o600)

    captured = await _accessors(monkeypatch, token_path)
    reauthorized = _token_document("reauthorized")
    reauthorized["creation_timestamp"] += 100
    token_path.write_text(json.dumps(reauthorized))
    token_path.chmod(0o600)
    reauthorized_inode = token_path.stat().st_ino
    log_warning = MagicMock()
    monkeypatch.setattr("butterfly_guy.data.schwab_client.log.warning", log_warning)

    # This callback belongs to the client constructed from `original`. Its access
    # token may refresh before the reload loop notices the re-authorized document.
    captured["write"](_token_document("late-old-refresh"))

    assert json.loads(token_path.read_text()) == reauthorized
    assert token_path.stat().st_ino == reauthorized_inode
    log_warning.assert_called_once_with("schwab_token_stale_persist_rejected")


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


def _reload_harness(monkeypatch, *, clients):
    """Wire a wrapper whose _build_client hands out `clients` in order."""
    handed_out = []

    def factory(**_kwargs):
        client = clients[len(handed_out)]
        handed_out.append(client)
        return client

    monkeypatch.setattr("schwab.auth.client_from_access_functions", MagicMock(side_effect=factory))
    schwab = SchwabClientWrapper(SchwabSettings(account_id="123"))
    return schwab, handed_out


def _account_client(hash_value="HASH", status=200):
    response = MagicMock(status_code=status)
    response.json.return_value = [{"accountNumber": "123", "hashValue": hash_value}]
    return MagicMock(
        get_account_numbers=AsyncMock(return_value=response),
        close_async_session=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_reload_is_a_noop_while_creation_timestamp_is_unchanged(monkeypatch):
    """An ordinary hourly refresh rewrites the document but must not rebuild the client."""
    schwab, handed_out = _reload_harness(monkeypatch, clients=[_account_client()])
    monkeypatch.setattr(SchwabClientWrapper, "_read_creation_timestamp", lambda _self: 1000)
    await schwab.initialize()
    first = schwab.client

    assert await schwab.reload_if_reauthorized() is False
    assert schwab.client is first
    assert len(handed_out) == 1


@pytest.mark.asyncio
async def test_reload_swaps_the_client_when_the_token_is_reauthorized(monkeypatch):
    old, new = _account_client("OLD"), _account_client("NEW")
    schwab, _ = _reload_harness(monkeypatch, clients=[old, new])
    stamps = iter([1000, 2000])
    monkeypatch.setattr(SchwabClientWrapper, "_read_creation_timestamp", lambda _self: next(stamps))
    await schwab.initialize()
    assert schwab.client is old

    assert await schwab.reload_if_reauthorized() is True
    assert schwab.client is new
    assert schwab.account_hash == "NEW"
    # The displaced client must NOT be closed: a request may still be in flight on it.
    old.close_async_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_reload_keeps_the_working_client(monkeypatch):
    """A bad document must leave the process on the credential that still works."""
    old, broken = _account_client("OLD"), _account_client(status=401)
    schwab, _ = _reload_harness(monkeypatch, clients=[old, broken])
    stamps = iter([1000, 2000])
    monkeypatch.setattr(SchwabClientWrapper, "_read_creation_timestamp", lambda _self: next(stamps))
    await schwab.initialize()

    with pytest.raises(RuntimeError, match="Failed to get account numbers: 401"):
        await schwab.reload_if_reauthorized()

    assert schwab.client is old
    assert schwab.account_hash == "OLD"
    # The marker must not advance past the document it failed on, or the next check
    # would see no change and the app would stay on the old credential forever.
    assert schwab._creation_timestamp == 1000
    broken.close_async_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_releases_both_the_live_and_retired_sessions(monkeypatch):
    old, new = _account_client("OLD"), _account_client("NEW")
    schwab, _ = _reload_harness(monkeypatch, clients=[old, new])
    stamps = iter([1000, 2000])
    monkeypatch.setattr(SchwabClientWrapper, "_read_creation_timestamp", lambda _self: next(stamps))
    await schwab.initialize()
    await schwab.reload_if_reauthorized()

    await schwab.close()

    old.close_async_session.assert_awaited_once()
    new.close_async_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_unreadable_marker_is_adopted_rather_than_forcing_a_rebuild(monkeypatch):
    """initialize() tolerates an unreadable marker; the first check must not rebuild."""
    schwab, handed_out = _reload_harness(monkeypatch, clients=[_account_client()])
    reads = iter([RuntimeError("unreadable"), 1000, 1000])

    def read(_self):
        value = next(reads)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(SchwabClientWrapper, "_read_creation_timestamp", read)
    await schwab.initialize()
    assert schwab._creation_timestamp is None

    assert await schwab.reload_if_reauthorized() is False
    assert schwab._creation_timestamp == 1000
    assert len(handed_out) == 1
