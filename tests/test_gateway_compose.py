from pathlib import Path

import yaml


def test_gateway_compose_matches_secret_owner_and_has_readiness_healthcheck() -> None:
    compose = yaml.safe_load(Path("infra/docker-compose.gateway.yml").read_text())
    service = compose["services"]["schwab_gateway_foundation"]

    assert service["user"] == (
        "${SCHWAB_GATEWAY_UID:-1001}:${SCHWAB_GATEWAY_GID:-1001}"
    )
    assert service["volumes"] == [
        "../secrets/schwab-gateway-keys.json:"
        "/run/secrets/schwab-gateway-keys.json:ro"
    ]
    assert "/ready" in " ".join(service["healthcheck"]["test"])
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
