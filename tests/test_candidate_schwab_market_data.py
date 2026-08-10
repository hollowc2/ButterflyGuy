from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.candidate_fleet.schwab_market_data import (
    ReadOnlySchwabMarketDataClient,
)
from butterfly_guy.core.config import SchwabSettings
from butterfly_guy.scripts.run_candidate_feed import token_reload_loop


def _write_token(path, *, creation: int | None, access: str) -> dict:
    document = {"token": {"access_token": access}}
    if creation is not None:
        document["creation_timestamp"] = creation
    path.write_text(json.dumps(document), encoding="utf-8")
    path.chmod(0o600)
    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.touch(mode=0o600, exist_ok=True)
    lock_path.chmod(0o600)
    return document


def _settings(token_path) -> SchwabSettings:
    return SchwabSettings(
        api_key="api-key",
        secret_key="secret-key",
        token_path=str(token_path),
    )


def _reload_client(status: int = 200):
    return SimpleNamespace(
        get_quote=AsyncMock(return_value=SimpleNamespace(status_code=status)),
        close_async_session=AsyncMock(),
    )


def _reload_harness(monkeypatch, token_path, clients):
    callbacks: list[tuple[object, object]] = []

    def factory(*, token_read_func, token_write_func, **_kwargs):
        token_read_func()
        callbacks.append((token_read_func, token_write_func))
        return clients[len(callbacks) - 1]

    monkeypatch.setattr(
        "schwab.auth.client_from_access_functions", MagicMock(side_effect=factory)
    )
    return ReadOnlySchwabMarketDataClient(_settings(token_path)), callbacks


@pytest.mark.asyncio
async def test_token_refresh_is_retained_in_memory_without_writing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    original_token = _write_token(token_path, creation=1, access="original")
    callbacks: dict[str, object] = {}

    def client_factory(
        api_key,
        app_secret,
        token_read_func,
        token_write_func,
        *,
        asyncio,
        enforce_enums,
    ):
        callbacks["read"] = token_read_func
        callbacks["write"] = token_write_func
        assert api_key == "api-key"
        assert app_secret == "secret-key"
        assert asyncio is True
        assert enforce_enums is False
        assert token_read_func() == original_token
        return SimpleNamespace()

    monkeypatch.setattr(
        "schwab.auth.client_from_access_functions",
        client_factory,
    )
    legacy_factory = MagicMock(side_effect=AssertionError("file writer must not be used"))
    monkeypatch.setattr("schwab.auth.client_from_token_file", legacy_factory)
    market_data = ReadOnlySchwabMarketDataClient(
        _settings(token_path)
    )

    await market_data.initialize()
    refreshed_token = {
        "creation_timestamp": 1,
        "token": {"access_token": "refreshed"},
    }
    callbacks["write"](refreshed_token)  # type: ignore[operator]

    assert callbacks["read"]() == refreshed_token  # type: ignore[operator]
    assert json.loads(token_path.read_text(encoding="utf-8")) == original_token
    legacy_factory.assert_not_called()


@pytest.mark.asyncio
async def test_reload_is_a_noop_while_creation_timestamp_is_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    _write_token(token_path, creation=1, access="original")
    old = _reload_client()
    market_data, callbacks = _reload_harness(monkeypatch, token_path, [old])
    await market_data.initialize()

    assert await market_data.reload_if_reauthorized() is False
    assert market_data.client is old
    assert len(callbacks) == 1
    old.get_quote.assert_not_awaited()


@pytest.mark.asyncio
async def test_reload_validates_and_swaps_on_reauthorization(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    _write_token(token_path, creation=1, access="original")
    old, new = _reload_client(), _reload_client()
    market_data, callbacks = _reload_harness(monkeypatch, token_path, [old, new])
    await market_data.initialize()
    _write_token(token_path, creation=2, access="reauthorized")

    assert await market_data.reload_if_reauthorized() is True
    assert market_data.client is new
    assert market_data._creation_timestamp == 2
    new.get_quote.assert_awaited_once_with("$SPX")
    old.close_async_session.assert_not_awaited()

    # Each client owns its own memory-only refresh callback. A late refresh from an
    # in-flight old request must not replace the new client's token state.
    old_read, old_write = callbacks[0]
    new_read, _new_write = callbacks[1]
    old_write({"creation_timestamp": 1, "token": {"access_token": "late-old"}})
    assert old_read()["token"]["access_token"] == "late-old"
    assert new_read()["token"]["access_token"] == "reauthorized"


@pytest.mark.asyncio
async def test_failed_reload_keeps_the_working_client_and_marker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    _write_token(token_path, creation=1, access="original")
    old, rejected = _reload_client(), _reload_client(status=401)
    market_data, _callbacks = _reload_harness(monkeypatch, token_path, [old, rejected])
    await market_data.initialize()
    _write_token(token_path, creation=2, access="rejected")

    with pytest.raises(RuntimeError, match="validation returned status 401"):
        await market_data.reload_if_reauthorized()

    assert market_data.client is old
    assert market_data._creation_timestamp == 1
    rejected.close_async_session.assert_awaited_once()
    old.close_async_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_startup_marker_is_adopted_without_rebuilding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    _write_token(token_path, creation=None, access="original")
    old = _reload_client()
    market_data, callbacks = _reload_harness(monkeypatch, token_path, [old])
    await market_data.initialize()
    _write_token(token_path, creation=1, access="same-authorization")

    assert await market_data.reload_if_reauthorized() is False
    assert market_data._creation_timestamp == 1
    assert len(callbacks) == 1


@pytest.mark.asyncio
async def test_close_releases_live_and_retired_clients(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    _write_token(token_path, creation=1, access="original")
    old, new = _reload_client(), _reload_client()
    market_data, _callbacks = _reload_harness(monkeypatch, token_path, [old, new])
    await market_data.initialize()
    _write_token(token_path, creation=2, access="reauthorized")
    await market_data.reload_if_reauthorized()

    await market_data.close()

    old.close_async_session.assert_awaited_once()
    new.close_async_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_reload_loop_logs_failure_and_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcomes = [RuntimeError("bad token"), True]
    calls: list[str] = []

    async def reload_if_reauthorized():
        outcome = outcomes[len(calls)]
        calls.append("called")
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    errors = MagicMock()
    applied = MagicMock()
    monkeypatch.setattr("butterfly_guy.scripts.run_candidate_feed.log.error", errors)
    monkeypatch.setattr("butterfly_guy.scripts.run_candidate_feed.log.info", applied)
    task = asyncio.create_task(
        token_reload_loop(
            SimpleNamespace(reload_if_reauthorized=reload_if_reauthorized), interval=0
        )
    )
    while len(calls) < 2:
        await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)

    errors.assert_called_once_with(
        "candidate_token_reload_failed", reason="RuntimeError"
    )
    applied.assert_called_once_with("candidate_token_reload_applied")
