import io
import json
import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from butterfly_guy.schwab_gateway.token_manager import (
    AtomicFileTokenStore,
    TokenLockTimeoutError,
)


@pytest.fixture(autouse=True)
def lock_events(monkeypatch):
    """Record lock acquire/release without touching a real lock file."""
    events = []

    @contextmanager
    def fake_locked(self, timeout_seconds):
        events.append(("acquire", str(self.path), timeout_seconds))
        try:
            yield MagicMock()
        finally:
            events.append(("release", str(self.path), timeout_seconds))

    monkeypatch.setattr(AtomicFileTokenStore, "locked", fake_locked)
    return events


@pytest.mark.parametrize(
    "seconds_remaining,resolved,expected",
    [
        (-1, False, "TOKEN ALERT: sent; refresh token expired"),
        (4 * 3600, False, "TOKEN ALERT: sent; refresh token expires in 4.0h"),
        # WARN_BEFORE is 24h and the comparison is inclusive, so 24h alerts and 25h
        # does not. The old 8h window opened on the morning the token died; the whole
        # point of widening it is that the Friday before is already alerting.
        (20 * 3600, False, "TOKEN ALERT: sent; refresh token expires in 20.0h"),
        (24 * 3600, False, "TOKEN ALERT: sent; refresh token expires in 24.0h"),
        (25 * 3600, True, "TOKEN ALERT: resolved; refresh token is healthy"),
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


@pytest.mark.parametrize(
    "process_env,dotenv_value,expected,root_relative",
    [
        (None, None, "tokens.json", True),
        (None, "secrets/tokens.json", "secrets/tokens.json", True),
        ("/srv/tokens.json", "secrets/tokens.json", "/srv/tokens.json", False),
    ],
)
def test_token_keepalive_honours_schwab_token_path(
    monkeypatch, process_env, dotenv_value, expected, root_relative
):
    """SCHWAB_TOKEN_PATH overrides the default, process env winning over .env."""
    now = 2_000_000_000
    token = json.dumps({"creation_timestamp": now})
    original_open = open

    def fake_open(path, *args, **kwargs):
        if Path(path).name == "tokens.json":
            return io.StringIO(token)
        return original_open(path, *args, **kwargs)

    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None
    client_from_token_file = MagicMock(
        return_value=MagicMock(get_quote=MagicMock(return_value=response))
    )
    dotenv = {"SCHWAB_API_KEY": "key", "SCHWAB_SECRET_KEY": "secret"}
    if dotenv_value is not None:
        dotenv["SCHWAB_TOKEN_PATH"] = dotenv_value

    monkeypatch.delenv("SCHWAB_TOKEN_PATH", raising=False)
    if process_env is not None:
        monkeypatch.setenv("SCHWAB_TOKEN_PATH", process_env)
    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr("time.time", lambda: now)
    monkeypatch.setattr("dotenv.dotenv_values", lambda _path: dotenv)
    monkeypatch.setattr("schwab.auth.client_from_token_file", client_from_token_file)
    monkeypatch.setitem(
        sys.modules,
        "notify",
        types.SimpleNamespace(
            send=lambda _message: True,
            send_alertmanager=lambda *_args, **_kwargs: True,
        ),
    )
    monkeypatch.setattr(sys, "argv", ["schwab_token_keepalive.py"])

    runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    root = Path("tools/schwab_token_keepalive.py").parent.parent
    used = client_from_token_file.call_args.kwargs["token_path"]
    assert used == (str(root / expected) if root_relative else expected)


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


def _run_with_stub_token(monkeypatch, now=2_000_000_000):
    """Wire up the module-level environment the keepalive script reads on import."""
    token = json.dumps({"creation_timestamp": now})
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
    monkeypatch.setitem(
        sys.modules,
        "notify",
        types.SimpleNamespace(
            send=lambda _message: True,
            send_alertmanager=lambda *_args, **_kwargs: True,
        ),
    )
    monkeypatch.setattr(sys, "argv", ["schwab_token_keepalive.py"])


def test_token_keepalive_refreshes_inside_the_token_lock(
    monkeypatch, lock_events
):
    """The refresh and the quote both happen while the gateway's lock is held.

    Schwab rotates the refresh token on every refresh, so a refresh that runs outside
    the lock can spend a credential the gateway has already replaced.
    """
    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None

    def refresh(**_kwargs):
        lock_events.append(("refresh", None, None))
        return MagicMock(get_quote=MagicMock(return_value=response))

    _run_with_stub_token(monkeypatch)
    monkeypatch.setattr("schwab.auth.client_from_token_file", refresh)

    runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    stages = [event[0] for event in lock_events]
    assert stages == ["acquire", "refresh", "release"]
    assert lock_events[0][1].endswith("tokens.json")
    assert lock_events[0][2] == 30.0


def test_token_keepalive_exits_when_the_token_lock_is_held(monkeypatch, capsys):
    """A busy lock fails loudly rather than writing alongside the other writer."""
    client_from_token_file = MagicMock()

    @contextmanager
    def busy_lock(self, timeout_seconds):
        raise TokenLockTimeoutError("timed out waiting for the token lock")
        yield  # pragma: no cover - unreachable, keeps this a generator

    _run_with_stub_token(monkeypatch)
    monkeypatch.setattr("schwab.auth.client_from_token_file", client_from_token_file)
    monkeypatch.setattr(AtomicFileTokenStore, "locked", busy_lock)

    with pytest.raises(SystemExit) as exc:
        runpy.run_path("tools/schwab_token_keepalive.py", run_name="__main__")

    assert exc.value.code == 1
    assert "ERROR: token lock held by another writer" in capsys.readouterr().out
    client_from_token_file.assert_not_called()
