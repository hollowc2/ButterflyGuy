from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from butterfly_guy.candidate_fleet.schwab_market_data import (
    ReadOnlySchwabMarketDataClient,
)
from butterfly_guy.core.config import SchwabSettings


@pytest.mark.asyncio
async def test_token_refresh_is_retained_in_memory_without_writing_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    token_path = tmp_path / "tokens.json"
    original_token = {
        "creation_timestamp": 1,
        "token": {"access_token": "original"},
    }
    token_path.write_text(json.dumps(original_token), encoding="utf-8")
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
        SchwabSettings(
            api_key="api-key",
            secret_key="secret-key",
            token_path=str(token_path),
        )
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
