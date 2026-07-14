import io
import json
import runpy
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "seconds_remaining,expected",
    [(-1, "has EXPIRED"), (4 * 3600, "expires in 4.0 hours")],
)
def test_token_keepalive_alerts_for_expired_and_expiring_tokens(
    monkeypatch, seconds_remaining, expected
):
    now = 2_000_000_000
    token = json.dumps(
        {"creation_timestamp": now - 7 * 24 * 3600 + seconds_remaining}
    )
    messages = []
    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None
    client = MagicMock(get_quote=MagicMock(return_value=response))
    original_open = open

    def fake_open(path, *args, **kwargs):
        if Path(path).name == "tokens.json":
            return io.StringIO(token)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr("time.time", lambda: now)
    monkeypatch.setattr(
        "dotenv.dotenv_values",
        lambda _path: {"SCHWAB_API_KEY": "key", "SCHWAB_SECRET_KEY": "secret"},
    )
    monkeypatch.setattr(
        "schwab.auth.client_from_token_file", MagicMock(return_value=client)
    )
    monkeypatch.setitem(
        sys.modules,
        "notify",
        types.SimpleNamespace(send=lambda message: messages.append(message) or True),
    )
    monkeypatch.setattr(sys, "argv", ["schwab_token_keepalive.py"])

    runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    assert any(expected in message for message in messages)
    client.get_quote.assert_called_once_with("$SPX")
