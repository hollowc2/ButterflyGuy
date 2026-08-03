from __future__ import annotations

import json

import pytest

from butterfly_guy.schwab_gateway.auth import (
    InternalKeyAuthenticator,
    InternalPrincipal,
    hash_api_key,
)


def test_authenticator_matches_hashed_keys_without_storing_plaintext() -> None:
    principal = InternalPrincipal(
        client_id="after-hours",
        key_sha256=hash_api_key("test-only-secret"),
        capabilities=frozenset({"market_data:read"}),
    )
    authenticator = InternalKeyAuthenticator((principal,))

    assert authenticator.authenticate("test-only-secret") == principal
    assert authenticator.authenticate("wrong") is None
    assert "test-only-secret" not in repr(authenticator)


def test_authenticator_loads_versioned_file(tmp_path) -> None:
    path = tmp_path / "keys.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "clients": [
                    {
                        "id": "butterfly-guy",
                        "key_sha256": hash_api_key("client-key"),
                        "capabilities": ["market_data:read"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    authenticator = InternalKeyAuthenticator.from_file(path)

    assert authenticator.authenticate("client-key").client_id == "butterfly-guy"


def test_authenticator_rejects_writable_key_file(tmp_path) -> None:
    path = tmp_path / "keys.json"
    path.write_text('{"version": 1, "clients": []}', encoding="utf-8")
    path.chmod(0o622)

    with pytest.raises(ValueError, match="must not be group/world writable"):
        InternalKeyAuthenticator.from_file(path)


def test_authenticator_rejects_unknown_key_file_fields(tmp_path) -> None:
    path = tmp_path / "keys.json"
    path.write_text(
        json.dumps({"version": 1, "clients": [], "raw_key": "must-not-be-accepted"}),
        encoding="utf-8",
    )
    path.chmod(0o600)

    with pytest.raises(ValueError, match="invalid gateway keys file schema"):
        InternalKeyAuthenticator.from_file(path)


def test_principal_rejects_order_capability_typo() -> None:
    with pytest.raises(ValueError, match="unknown gateway capabilities"):
        InternalPrincipal(
            client_id="scanner",
            key_sha256=hash_api_key("key"),
            capabilities=frozenset({"order:write"}),
        )
