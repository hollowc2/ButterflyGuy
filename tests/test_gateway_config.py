from __future__ import annotations

import pytest
from pydantic import ValidationError
from schwab_gateway_sdk.config import GatewayClientSettings


def test_gateway_client_mode_is_opt_in_and_secret_is_hidden() -> None:
    direct = GatewayClientSettings(SCHWAB_ACCESS_MODE="direct")
    gateway = GatewayClientSettings(
        SCHWAB_ACCESS_MODE="gateway",
        SCHWAB_GATEWAY_URL="http://127.0.0.1:8010",
        SCHWAB_GATEWAY_API_KEY="test-secret",
    )

    assert direct.access_mode == "direct"
    assert gateway.access_mode == "gateway"
    assert "test-secret" not in repr(gateway)


def test_gateway_client_mode_requires_url_and_key() -> None:
    with pytest.raises(ValidationError, match="gateway mode requires"):
        GatewayClientSettings(SCHWAB_ACCESS_MODE="gateway")


def test_gateway_client_mode_rejects_shadow_reads() -> None:
    with pytest.raises(ValidationError, match="shadow reads"):
        GatewayClientSettings(
            SCHWAB_ACCESS_MODE="gateway",
            SCHWAB_GATEWAY_SHADOW_READS="true",
            SCHWAB_GATEWAY_URL="http://127.0.0.1:8010",
            SCHWAB_GATEWAY_API_KEY="test-secret",
        )


def test_gateway_client_valid_mode_and_shadow_combinations() -> None:
    direct_no_shadow = GatewayClientSettings(SCHWAB_ACCESS_MODE="direct")
    direct_with_shadow = GatewayClientSettings(
        SCHWAB_ACCESS_MODE="direct",
        SCHWAB_GATEWAY_SHADOW_READS="true",
        SCHWAB_GATEWAY_URL="http://127.0.0.1:8010",
        SCHWAB_GATEWAY_API_KEY="test-secret",
    )
    gateway_no_shadow = GatewayClientSettings(
        SCHWAB_ACCESS_MODE="gateway",
        SCHWAB_GATEWAY_URL="http://127.0.0.1:8010",
        SCHWAB_GATEWAY_API_KEY="test-secret",
    )

    assert direct_no_shadow.access_mode == "direct"
    assert direct_no_shadow.shadow_reads is False
    assert direct_with_shadow.shadow_reads is True
    assert gateway_no_shadow.access_mode == "gateway"
    assert gateway_no_shadow.shadow_reads is False
