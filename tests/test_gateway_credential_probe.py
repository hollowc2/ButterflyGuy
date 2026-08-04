from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from butterfly_guy.schwab_gateway.config import GatewayCredentialProbeSettings
from butterfly_guy.schwab_gateway.credential_probe import (
    GatewayCredentialProbeError,
    GatewayCredentialProbeResult,
    run_gateway_credential_probe,
)
from butterfly_guy.scripts import probe_schwab_gateway_credentials as probe_command

NOW = 2_000_000_000
FAKE_API_KEY = "fake-api-key"
FAKE_APP_SECRET = "fake-app-secret"


def token_document() -> dict:
    return {
        "creation_timestamp": NOW - 60,
        "token": {
            "access_token": "access-secret",
            "refresh_token": "refresh-secret",
        },
    }


def write_token(path: Path) -> None:
    path.write_text(json.dumps(token_document()), encoding="utf-8")
    path.chmod(0o600)


def settings(path: Path) -> GatewayCredentialProbeSettings:
    return GatewayCredentialProbeSettings(
        SCHWAB_API_KEY=FAKE_API_KEY,
        SCHWAB_SECRET_KEY=FAKE_APP_SECRET,
        SCHWAB_TOKEN_PATH=path,
    )


class FakeResponse:
    def __init__(self, *, malformed: bool = False) -> None:
        self._malformed = malformed

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        if self._malformed:
            return {"unexpected": {}}
        return {"AAPL": {"quote": {"mark": 100.0}}}


class FakeClient:
    Quote = SimpleNamespace(
        Fields=SimpleNamespace(QUOTE="QUOTE", EXTENDED="EXTENDED")
    )

    def __init__(self, *, malformed: bool = False) -> None:
        self.calls: list[tuple[list[str], list[str]]] = []
        self.session = MagicMock()
        self._malformed = malformed

    def get_quotes(self, symbols, *, fields):
        self.calls.append((symbols, fields))
        return FakeResponse(malformed=self._malformed)


class FakeFactory:
    def __init__(self, client: FakeClient) -> None:
        self.client = client
        self.calls: list[dict] = []

    def __call__(
        self,
        api_key,
        app_secret,
        token_read_func,
        token_write_func,
        asyncio=False,
        enforce_enums=True,
    ) -> FakeClient:
        del token_write_func
        loaded = token_read_func()
        assert loaded == token_document()
        self.calls.append(
            {
                "api_key": api_key,
                "app_secret": app_secret,
                "asyncio": asyncio,
                "enforce_enums": enforce_enums,
            }
        )
        return self.client


def test_probe_performs_only_one_bounded_quote_read(tmp_path: Path) -> None:
    token_path = tmp_path / "synthetic-token.json"
    write_token(token_path)
    client = FakeClient()
    factory = FakeFactory(client)

    result = run_gateway_credential_probe(settings(token_path), factory)

    assert result.status == "ok"
    assert result.token_state == "ready"
    assert result.quote_count == 1
    assert factory.calls == [
        {
            "api_key": FAKE_API_KEY,
            "app_secret": FAKE_APP_SECRET,
            "asyncio": False,
            "enforce_enums": True,
        }
    ]
    assert client.calls == [(["AAPL"], ["QUOTE", "EXTENDED"])]
    client.session.close.assert_called_once_with()


def test_probe_normalizes_malformed_response_without_exposing_data(tmp_path: Path) -> None:
    token_path = tmp_path / "synthetic-token.json"
    write_token(token_path)

    with pytest.raises(GatewayCredentialProbeError) as exc:
        run_gateway_credential_probe(settings(token_path), FakeFactory(FakeClient(malformed=True)))

    assert str(exc.value) == "Schwab gateway credential probe failed"
    assert "unexpected" not in str(exc.value)


def test_probe_settings_require_absolute_path_and_redact_inputs(tmp_path: Path) -> None:
    token_path = tmp_path / "synthetic-token.json"
    value = settings(token_path)
    assert FAKE_API_KEY not in repr(value)
    assert FAKE_APP_SECRET not in repr(value)
    assert str(token_path) not in repr(value)

    with pytest.raises(ValidationError, match="must be absolute"):
        GatewayCredentialProbeSettings(
            SCHWAB_API_KEY=FAKE_API_KEY,
            SCHWAB_SECRET_KEY=FAKE_APP_SECRET,
            SCHWAB_TOKEN_PATH="relative-token.json",
        )


def test_probe_command_refuses_to_load_settings_without_all_confirmations() -> None:
    with pytest.raises(SystemExit):
        probe_command.main([])


def test_probe_command_bounds_configuration_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setenv("SCHWAB_API_KEY", "sensitive-api-key")
    monkeypatch.setenv("SCHWAB_SECRET_KEY", "sensitive-app-secret")
    monkeypatch.setenv("SCHWAB_TOKEN_PATH", "sensitive/relative-token-path")

    with pytest.raises(SystemExit) as exc:
        probe_command.main(
            [
                "--authorize-real-credential-read",
                "--confirm-single-token-writer",
                "--confirm-no-deployment",
            ]
        )

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert captured.out == ""
    assert captured.err == "Schwab gateway credential proof failed\n"
    assert "sensitive" not in captured.err
    assert "token-path" not in captured.err


def test_probe_command_emits_only_bounded_success_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    fake_settings = object()
    fake_factory = object()
    fake_schwab = ModuleType("schwab")
    fake_auth = ModuleType("schwab.auth")
    fake_auth.client_from_access_functions = fake_factory
    fake_schwab.auth = fake_auth
    setup_logging = MagicMock()
    run_probe = MagicMock(
        return_value=GatewayCredentialProbeResult(
            status="ok",
            token_state="ready",
            quote_count=1,
        )
    )
    monkeypatch.setattr(probe_command, "GatewayCredentialProbeSettings", lambda: fake_settings)
    monkeypatch.setattr(probe_command, "setup_logging", setup_logging)
    monkeypatch.setattr(probe_command, "run_gateway_credential_probe", run_probe)
    monkeypatch.setitem(sys.modules, "schwab", fake_schwab)
    monkeypatch.setitem(sys.modules, "schwab.auth", fake_auth)

    probe_command.main(
        [
            "--authorize-real-credential-read",
            "--confirm-single-token-writer",
            "--confirm-no-deployment",
        ]
    )

    captured = capsys.readouterr()
    assert captured.out == '{"quote_count":1,"status":"ok","token_state":"ready"}\n'
    assert captured.err == ""
    setup_logging.assert_called_once_with("CRITICAL", json_output=True)
    run_probe.assert_called_once_with(fake_settings, fake_factory)
