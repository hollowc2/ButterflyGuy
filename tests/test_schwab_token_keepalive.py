import io
import json
import runpy
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize(
    "seconds_remaining,resolved,expected",
    [
        (-1, False, "TOKEN ALERT: sent; refresh token expired"),
        (4 * 3600, False, "TOKEN ALERT: sent; refresh token expires in 4.0h"),
        (24 * 3600, True, "TOKEN ALERT: resolved; refresh token is healthy"),
    ],
)
def test_token_keepalive_reports_alertmanager_state(
    monkeypatch, capsys, seconds_remaining, resolved, expected
):
    now = 2_000_000_000
    token = json.dumps(
        {"creation_timestamp": now - 7 * 24 * 3600 + seconds_remaining}
    )
    alerts = []
    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None
    client = MagicMock(get_quote=MagicMock(return_value=response))
    original_open = open

    def fake_open(path, *args, **kwargs):
        if Path(path).name == "tokens.json":
            return io.StringIO(token)
        return original_open(path, *args, **kwargs)

    def send_alertmanager(url, condition, underlying, **kwargs):
        alerts.append((url, condition, underlying, kwargs))
        return True

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
        types.SimpleNamespace(
            send=lambda _message: True,
            send_alertmanager=send_alertmanager,
        ),
    )
    monkeypatch.setattr(sys, "argv", ["schwab_token_keepalive.py"])

    runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    assert alerts == [
        (
            "http://127.0.0.1:9093",
            "token_expiry",
            "ALL",
            {"resolved": True} if resolved else {},
        )
    ]
    assert expected in capsys.readouterr().out
    client.get_quote.assert_called_once_with("$SPX")


def test_token_keepalive_reports_alertmanager_failure(monkeypatch, capsys):
    now = 2_000_000_000
    token = json.dumps({"creation_timestamp": now - 7 * 24 * 3600 - 1})
    original_open = open

    def fake_open(path, *args, **kwargs):
        if Path(path).name == "tokens.json":
            return io.StringIO(token)
        return original_open(path, *args, **kwargs)

    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None
    client = MagicMock(get_quote=MagicMock(return_value=response))
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
        types.SimpleNamespace(
            send=lambda _message: True,
            send_alertmanager=lambda *_args, **_kwargs: False,
        ),
    )
    monkeypatch.setattr(sys, "argv", ["schwab_token_keepalive.py"])

    with pytest.raises(SystemExit) as exc:
        runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    assert exc.value.code == 1
    assert "TOKEN ALERT: failed" in capsys.readouterr().out
    client.get_quote.assert_called_once_with("$SPX")
