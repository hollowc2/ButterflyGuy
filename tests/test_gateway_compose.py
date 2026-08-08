import hashlib
import json
import re
from pathlib import Path

import yaml

from butterfly_guy.schwab_gateway.auth import (
    EXPECTED_PRIORITY_BY_CLIENT,
    KNOWN_CAPABILITIES,
    KNOWN_CLIENT_IDS,
)


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


def test_gateway_live_service_is_isolated_and_read_only() -> None:
    compose = yaml.safe_load(Path("infra/docker-compose.gateway.yml").read_text())
    service = compose["services"]["schwab_gateway_live"]

    # Its own non-default profile, distinct container name, distinct port.
    assert service["profiles"] == ["gateway-live"]
    assert service["container_name"] == "butterfly_schwab_gateway_live"
    assert service["ports"] == ["127.0.0.1:8011:8011"]
    assert service["restart"] == "no"

    # The same hardening the demo service carries.
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert service["user"] == "${SCHWAB_GATEWAY_UID:-1001}:${SCHWAB_GATEWAY_GID:-1001}"

    # Live serving is explicit at the command line, never implicit.
    assert service["command"][-3:] == [
        "--serve-live",
        "--authorize-real-credential-read",
        "--confirm-single-token-writer",
    ]
    assert service["environment"]["SCHWAB_GATEWAY_ORDER_WRITES_ENABLED"] == "false"


def test_gateway_live_service_mounts_the_token_directory_not_the_document() -> None:
    """A document-only bind under read_only: true cannot support atomic replacement.

    AtomicTokenManager creates its lock and its atomic replacement as siblings of the
    token file and os.replace cannot cross filesystems, so the directory must be the
    writable mount. This is the defect that stopped the in-container credential proof.
    """
    compose = yaml.safe_load(Path("infra/docker-compose.gateway.yml").read_text())
    service = compose["services"]["schwab_gateway_live"]

    token_mounts = [v for v in service["volumes"] if "TOKEN_DIR" in v]
    assert len(token_mounts) == 1

    # The directory is mounted at its own host path, writable, with no default value --
    # a missing token directory must fail loudly rather than mount a guess.
    directory = "${SCHWAB_GATEWAY_TOKEN_DIR:?set the host token directory}"
    assert ":?" in directory
    assert token_mounts[0] == f"{directory}:{directory}:rw"
    assert not directory.endswith("tokens.json")

    # The document path is derived from that same directory.
    assert service["environment"]["SCHWAB_TOKEN_PATH"] == f"{directory}/tokens.json"


def test_gateway_keys_example_matches_the_authenticator_schema() -> None:
    """The template must parse under the real loader's schema rules."""
    payload = json.loads(Path("infra/schwab-gateway-keys.example.json").read_text())

    assert set(payload) == {"version", "clients"}
    assert payload["version"] == 1
    assert {client["id"] for client in payload["clients"]} == KNOWN_CLIENT_IDS
    for client in payload["clients"]:
        assert set(client) == {"id", "key_sha256", "capabilities", "priority_class"}
        assert set(client["capabilities"]) <= KNOWN_CAPABILITIES
        assert client["priority_class"] == EXPECTED_PRIORITY_BY_CLIENT[client["id"]].value
        # A placeholder, never a real digest.
        assert not re.fullmatch(r"[0-9a-f]{64}", client["key_sha256"])


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

    # Originally recorded from origin/main 6179f2e as
    # 87a41005a7f6c8c0b2aac860b6f301d52b422d8a3e873c1415b6f7ed747975b5, before the
    # isolated package was added. Re-pinned at 5055991 ("Stop the legacy SPX candidate
    # container from auto-restarting"): it changes app_spx_candidate's restart policy
    # from unless-stopped to "no" and adds a comment, and introduces no gateway service,
    # profile, mount, or environment entry. Re-pinned again for B3, which repoints the
    # four token binds at SCHWAB_GATEWAY_TOKEN_DIR -- a shared variable, not a gateway
    # service, profile, or port, and pins each service's in-container SCHWAB_TOKEN_PATH.
    # The gateway still contributes no service here.
    assert hashlib.sha256(default_compose).hexdigest() == (
        "5957840e7fb0a7d15d6c1a85c627cb260d2a7d9e53d713945542fab1872f141d"
    )


def test_default_compose_token_binds_require_the_shared_token_directory() -> None:
    """All four trading services bind the token document from one required variable.

    A bind whose source path does not exist does not fail -- Docker creates an empty
    directory -- so the variable carries no default and every service must use it.
    """
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())
    directory = "${SCHWAB_GATEWAY_TOKEN_DIR:?set the host token directory}"

    binds = {
        name: [v for v in service["volumes"] if v.endswith("/app/tokens.json")
               or v.endswith("/app/tokens.json:ro")]
        for name, service in compose["services"].items()
    }
    assert binds == {
        "app_spx": [f"{directory}/tokens.json:/app/tokens.json"],
        "app_spx_candidate": [f"{directory}/tokens.json:/app/tokens.json:ro"],
        "app_ndx": [f"{directory}/tokens.json:/app/tokens.json"],
        "app_xsp": [f"{directory}/tokens.json:/app/tokens.json"],
    }

    # The host token path in ../.env names a host directory the container does not
    # have; every service must override it with its own mount target.
    assert all(
        service["environment"]["SCHWAB_TOKEN_PATH"] == "/app/tokens.json"
        for service in compose["services"].values()
    )
