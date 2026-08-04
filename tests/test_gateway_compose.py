import hashlib
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


def test_credential_proof_staging_override_is_isolated_and_mount_only() -> None:
    path = Path("infra/docker-compose.credential-proof-staging.yml")
    override = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert path.name not in {"compose.override.yml", "docker-compose.override.yml"}
    assert set(override) == {"services"}
    assert set(override["services"]) == {"app_spx"}
    assert set(override["services"]["app_spx"]) == {"tmpfs"}
    assert override["services"]["app_spx"]["tmpfs"] == [
        "/app/.schwab-credential-proof-runtime:"
        "rw,exec,nosuid,nodev,size=256m,mode=1777"
    ]


def test_staging_package_does_not_change_default_compose() -> None:
    default_compose = Path("infra/docker-compose.yml").read_bytes()

    # Recorded from origin/main 6179f2e before the isolated package was added.
    assert hashlib.sha256(default_compose).hexdigest() == (
        "87a41005a7f6c8c0b2aac860b6f301d52b422d8a3e873c1415b6f7ed747975b5"
    )
