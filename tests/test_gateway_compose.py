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
    # Always-on: it survives a crash and a reboot. Safe only because both token
    # writers now take the same lock (tools/schwab_token_keepalive.py).
    assert service["restart"] == "unless-stopped"

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


def test_only_the_live_gateway_joins_the_shared_monitoring_network() -> None:
    """Reachability is the live service's alone, and the network is never created here.

    A 127.0.0.1 publish is loopback-only, so no container can reach the gateway
    through it; monitoring_net is what gives Prometheus and the C3 consumers a route.
    It must be declared external -- this project must attach to the existing network,
    never define one that unrelated stacks already depend on.
    """
    compose = yaml.safe_load(Path("infra/docker-compose.gateway.yml").read_text())

    assert compose["networks"] == {"monitoring_net": {"external": True}}
    assert compose["services"]["schwab_gateway_live"]["networks"] == ["monitoring_net"]
    # The demo service stays on the project default network, unreachable from it.
    assert "networks" not in compose["services"]["schwab_gateway_foundation"]


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
    #
    # Re-pinned in Window E: the four token binds move from the document to the token
    # *directory*, and each service's SCHWAB_TOKEN_PATH moves to the host-absolute path
    # inside it. The gateway persists the token with os.replace, which swaps in a new
    # inode, and the three live trading containers had silently detached from every
    # write it made. Still no gateway service, profile, or port in this file.
    assert hashlib.sha256(default_compose).hexdigest() == (
        "5e7804fee1802c4d835e570b0b868697827049e50f44070009f578710491a341"
    )


def test_default_compose_token_binds_require_the_shared_token_directory() -> None:
    """All four trading services bind the token document from one required variable.

    A bind whose source path does not exist does not fail -- Docker creates an empty
    directory -- so the variable carries no default and every service must use it.
    """
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())
    directory = "${SCHWAB_GATEWAY_TOKEN_DIR:?set the host token directory}"

    # The variable carries its own ":?" default-guard, so the bind cannot be split on ":".
    binds = {
        name: [v for v in service["volumes"] if v.startswith(f"{directory}:")]
        for name, service in compose["services"].items()
    }
    assert binds == {
        "app_spx": [f"{directory}:{directory}"],
        "app_spx_candidate": [f"{directory}:{directory}:ro"],
        "app_ndx": [f"{directory}:{directory}"],
        "app_xsp": [f"{directory}:{directory}"],
    }

    # Every service must set SCHWAB_TOKEN_PATH from the same required variable as its
    # bind, never inherit it from ../.env.
    assert all(
        service["environment"]["SCHWAB_TOKEN_PATH"] == f"{directory}/tokens.json"
        for service in compose["services"].values()
    )


def test_default_compose_binds_the_token_directory_never_the_document() -> None:
    """The gateway replaces the token document atomically, swapping in a new inode.

    A document-level bind mount pins the inode Docker resolved at container start, so
    every later gateway write -- including the re-authorized refresh token -- becomes
    invisible to the container. Only a directory bind follows the replacement.
    """
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())

    for name, service in compose["services"].items():
        for volume in service["volumes"]:
            assert "tokens.json" not in volume, (
                f"{name} binds the token document; bind the directory instead"
            )


def test_live_configs_leave_token_path_to_the_environment() -> None:
    """A token_path in YAML silently beats the deployment's SCHWAB_TOKEN_PATH.

    config.py applies the environment variable with setdefault, so a value here wins.
    These three configs each pinned the relative "tokens.json", which only resolved
    because the old bind mount placed a document at /app alongside the working
    directory. Once the bind became a directory the containers crash-looped on a
    relative path that no longer existed.
    """
    for name in ("config.yaml", "config_ndx.yaml", "config_xsp.yaml"):
        config = yaml.safe_load(Path("configs", name).read_text(encoding="utf-8"))
        assert "token_path" not in config["schwab"], (
            f"configs/{name} pins token_path; leave it to SCHWAB_TOKEN_PATH"
        )
