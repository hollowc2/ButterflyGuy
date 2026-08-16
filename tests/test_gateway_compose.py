"""Deployment boundaries retained after the standalone gateway extraction."""

from pathlib import Path

import yaml


def test_only_xsp_receives_the_default_off_gateway_shadow_canary() -> None:
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())
    services = compose["services"]
    xsp_environment = services["app_xsp"]["environment"]

    assert xsp_environment["SCHWAB_ACCESS_MODE"] == "direct"
    assert xsp_environment["SCHWAB_GATEWAY_URL"] == (
        "${SCHWAB_GATEWAY_URL:-http://schwab-gateway:8011}"
    )
    assert xsp_environment["SCHWAB_GATEWAY_API_KEY"] == (
        "${SCHWAB_GATEWAY_API_KEY:-}"
    )
    assert xsp_environment["SCHWAB_GATEWAY_SHADOW_READS"] == (
        "${SCHWAB_GATEWAY_SHADOW_READS_XSP:-false}"
    )

    for service_name in ("app_spx", "app_spx_candidate", "app_ndx"):
        environment = services[service_name]["environment"]
        assert "SCHWAB_ACCESS_MODE" not in environment
        assert "SCHWAB_GATEWAY_URL" not in environment
        assert "SCHWAB_GATEWAY_API_KEY" not in environment
        assert "SCHWAB_GATEWAY_SHADOW_READS" not in environment


def test_default_compose_token_binds_require_the_shared_token_directory() -> None:
    """All four trading services bind the token document from one required variable."""
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())
    directory = "${SCHWAB_GATEWAY_TOKEN_DIR:?set the host token directory}"

    binds = {
        name: [value for value in service["volumes"] if value.startswith(f"{directory}:")]
        for name, service in compose["services"].items()
    }
    assert binds == {
        "app_spx": [f"{directory}:{directory}"],
        "app_spx_candidate": [f"{directory}:{directory}:ro"],
        "app_ndx": [f"{directory}:{directory}"],
        "app_xsp": [f"{directory}:{directory}"],
    }
    assert all(
        service["environment"]["SCHWAB_TOKEN_PATH"] == f"{directory}/tokens.json"
        for service in compose["services"].values()
    )


def test_environment_example_names_the_required_compose_token_directory() -> None:
    example = Path(".env.example").read_text(encoding="utf-8")

    assert "SCHWAB_GATEWAY_TOKEN_DIR=/absolute/path/to/schwab-token-directory" in example
    assert "SCHWAB_GATEWAY_SHADOW_READS_XSP=false" in example


def test_default_compose_binds_the_token_directory_never_the_document() -> None:
    """Directory binds follow atomic token replacement to its new inode."""
    compose = yaml.safe_load(Path("infra/docker-compose.yml").read_text())

    for name, service in compose["services"].items():
        for volume in service["volumes"]:
            assert "tokens.json" not in volume, (
                f"{name} binds the token document; bind the directory instead"
            )


def test_live_configs_leave_token_path_to_the_environment() -> None:
    """A YAML token_path would override the deployment's shared token path."""
    for name in ("config.yaml", "config_ndx.yaml", "config_xsp.yaml"):
        config = yaml.safe_load(Path("configs", name).read_text(encoding="utf-8"))
        assert "token_path" not in config["schwab"], (
            f"configs/{name} pins token_path; leave it to SCHWAB_TOKEN_PATH"
        )
