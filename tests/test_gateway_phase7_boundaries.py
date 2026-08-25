"""Phase 7 boundaries after extracting the Schwab gateway from ButterflyGuy."""

from __future__ import annotations

import ast
import inspect
import tomllib
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import yaml
from schwab_gateway_sdk.client import GatewayMarketDataClient
from schwab_gateway_sdk.config import GatewayClientSettings

from butterfly_guy.data.providers import DirectSchwabMarketDataProvider
from butterfly_guy.gateway_client.shadow import ShadowComparingMarketDataProvider
from butterfly_guy.scripts.run_live import _build_collector_market_data

ROOT = Path(__file__).resolve().parents[1]
STANDALONE_COMMIT = "2d1da47b37ba48e3603f8d52a2fe73a55924aaf0"


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_embedded_gateway_surfaces_are_absent() -> None:
    removed_paths = (
        "src/butterfly_guy/scripts/run_schwab_gateway.py",
        "src/butterfly_guy/scripts/probe_schwab_gateway_credentials.py",
        "src/butterfly_guy/scripts/issue_gateway_keys.py",
        "src/butterfly_guy/scripts/credential_proof_fingerprint.py",
        "configs/schwab_gateway_keys.example.json",
        "infra/docker-compose.credential-proof-staging.yml",
        "infra/docker-compose.gateway.yml",
        "infra/schwab-gateway-alerts.yml",
        "infra/schwab-gateway-keys.example.json",
    )

    present = [path for path in removed_paths if (ROOT / path).exists()]
    embedded_root = ROOT / "src/butterfly_guy/schwab_gateway"
    if embedded_root.exists():
        present.append(str(embedded_root.relative_to(ROOT)))
    compatibility_root = ROOT / "src/butterfly_guy/gateway_client"
    unexpected_compatibility = {
        path.name for path in compatibility_root.glob("*.py")
    } - {"__init__.py", "shadow.py"}
    present.extend(
        f"src/butterfly_guy/gateway_client/{name}"
        for name in sorted(unexpected_compatibility)
    )
    assert present == [], f"embedded gateway surfaces still present: {present}"


def test_production_code_has_no_embedded_gateway_imports() -> None:
    violations: list[str] = []
    for path in (ROOT / "src/butterfly_guy").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = (node.module or "",)
            elif isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            else:
                names = ()
            imports_embedded = any(
                name.startswith("butterfly_guy.schwab_gateway") for name in names
            )
            dynamically_imports_embedded = (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and "butterfly_guy.schwab_gateway" in node.value
            )
            if imports_embedded or dynamically_imports_embedded:
                violations.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert violations == []


def test_standalone_packages_remain_pinned_and_consumers_import_them_directly() -> None:
    project = tomllib.loads(_source("pyproject.toml"))
    sources = project["tool"]["uv"]["sources"]
    for distribution, subdirectory in (
        ("schwab-gateway-sdk", "packages/sdk"),
        ("schwab-token-store", "packages/token-store"),
    ):
        assert sources[distribution] == {
            "git": "https://github.com/hollowc2/SchwabGateway.git",
            "tag": "v0.1.0",
            "subdirectory": subdirectory,
        }

    locked = tomllib.loads(_source("uv.lock"))
    packages = {package["name"]: package for package in locked["package"]}
    for distribution in ("schwab-gateway-sdk", "schwab-token-store"):
        package = packages[distribution]
        assert package["version"] == "0.1.0"
        assert package["source"]["git"].endswith(f"#{STANDALONE_COMMIT}")

    assert "from schwab_gateway_sdk." in _source(
        "src/butterfly_guy/gateway_client/shadow.py"
    )
    assert "from schwab_gateway_sdk." in _source(
        "src/butterfly_guy/scripts/run_live.py"
    )
    for consumer in (
        "src/butterfly_guy/data/schwab_client.py",
        "src/butterfly_guy/candidate_fleet/schwab_market_data.py",
        "tools/schwab_token_keepalive.py",
    ):
        assert "from schwab_token_store import" in _source(consumer), consumer


def test_sdk_exposes_only_read_only_market_data_routes() -> None:
    tree = ast.parse(inspect.getsource(GatewayMarketDataClient))
    routes = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("/v1/")
    }

    assert routes == {"/v1/quotes", "/v1/spot", "/v1/chain"}
    assert not any(
        sensitive in route
        for route in routes
        for sensitive in ("account", "order", "position", "transaction")
    )


def test_compose_keeps_each_strategy_default_direct_with_staged_gateway_opt_in() -> None:
    compose = yaml.safe_load(_source("infra/docker-compose.yml"))
    services = compose["services"]
    for service_name, suffix in (
        ("app_xsp", "XSP"),
        ("app_spx", "SPX"),
        ("app_ndx", "NDX"),
    ):
        environment = services[service_name]["environment"]
        assert environment["SCHWAB_ACCESS_MODE"] == (
            f"${{SCHWAB_ACCESS_MODE_{suffix}:-direct}}"
        )
        assert environment["SCHWAB_GATEWAY_URL"] == (
            "${SCHWAB_GATEWAY_URL:-http://schwab-gateway:8011}"
        )
        assert environment["SCHWAB_GATEWAY_API_KEY"] == (
            "${SCHWAB_GATEWAY_API_KEY:-}"
        )
        assert environment["SCHWAB_GATEWAY_SHADOW_READS"] == (
            f"${{SCHWAB_GATEWAY_SHADOW_READS_{suffix}:-false}}"
        )


def test_default_settings_construct_no_gateway_client(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway_constructor = Mock()
    monkeypatch.setattr(
        "butterfly_guy.scripts.run_live.GatewayMarketDataClient",
        gateway_constructor,
    )

    provider, shadow, gateway = _build_collector_market_data(
        Mock(), GatewayClientSettings()
    )

    assert isinstance(provider, DirectSchwabMarketDataProvider)
    assert shadow is None
    assert gateway is None
    gateway_constructor.assert_not_called()


@pytest.mark.asyncio
async def test_shadow_failure_is_observed_without_changing_the_direct_result() -> None:
    direct = Mock(get_spot_price=AsyncMock(return_value=6123.45))
    gateway = Mock(get_spot=AsyncMock(side_effect=RuntimeError("gateway unavailable")))
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_spot_price("$XSP") == 6123.45
    await provider.wait_for_shadow_reads()

    direct.get_spot_price.assert_awaited_once_with("$XSP")
    gateway.get_spot.assert_awaited_once_with("$XSP")
    counts = provider.recorder.counts()
    assert len(counts) == 1
    (discrepancy,) = counts
    assert (discrepancy.operation, discrepancy.code, counts[discrepancy]) == (
        "spot",
        "gateway_unexpected_error",
        1,
    )
