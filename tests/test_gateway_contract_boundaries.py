from __future__ import annotations

import ast
import datetime as dt
from pathlib import Path

import httpx
import pytest
from aiohttp.test_utils import TestServer

from butterfly_guy.gateway_client.client import GatewayMarketDataClient
from butterfly_guy.gateway_client.models import QuoteV1
from butterfly_guy.schwab_gateway.api import StaticTokenReadinessProvider, create_app
from butterfly_guy.schwab_gateway.auth import (
    InternalKeyAuthenticator,
    InternalPrincipal,
    PriorityClass,
    hash_api_key,
)
from butterfly_guy.schwab_gateway.token_manager import TokenManagerState

KEYS = {
    "butterfly-guy": "synthetic-butterfly-key",
    "equity-scanner": "synthetic-scanner-key",
    "afterhours-lab": "synthetic-lab-key",
}


def principal(
    client_id: str,
    *,
    capabilities: frozenset[str] = frozenset({"market_data:read"}),
) -> InternalPrincipal:
    return InternalPrincipal(
        client_id=client_id,
        key_sha256=hash_api_key(KEYS[client_id]),
        capabilities=capabilities,
        priority_class=(
            PriorityClass.PROTECTED
            if client_id == "butterfly-guy"
            else PriorityClass.BACKGROUND
        ),
    )


class FakeUpstream:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def get_quotes(self, symbols: tuple[str, ...]) -> tuple[QuoteV1, ...]:
        self.calls.append(symbols)
        now = dt.datetime.now(dt.timezone.utc)
        return tuple(
            QuoteV1(
                symbol=symbol,
                gateway_received_at=now,
                source="fake",
                bid=None,
                ask=None,
                stale=False,
                data_quality_flags=("missing_bid", "missing_ask"),
            )
            for symbol in symbols
        )


def ready() -> StaticTokenReadinessProvider:
    return StaticTokenReadinessProvider(TokenManagerState.READY)


@pytest.mark.asyncio
async def test_all_service_identities_can_read_quotes_but_invalid_or_unscoped_keys_fail() -> None:
    upstream = FakeUpstream()
    principals = tuple(principal(client_id) for client_id in KEYS)
    server = TestServer(
        create_app(
            upstream,
            InternalKeyAuthenticator(principals),
            token_readiness_provider=ready(),
        )
    )
    await server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(server.make_url("/"))) as client:
            authorized = [
                await client.get(
                    "/v1/quotes",
                    params={"symbols": "AAPL"},
                    headers={"X-Internal-API-Key": key},
                )
                for key in KEYS.values()
            ]
            invalid = await client.get(
                "/v1/quotes",
                params={"symbols": "AAPL"},
                headers={"X-Internal-API-Key": "invalid-key"},
            )
    finally:
        await server.close()

    assert [response.status_code for response in authorized] == [200, 200, 200]
    assert invalid.status_code == 401
    assert "invalid-key" not in invalid.text

    unscoped = InternalPrincipal(
        client_id="afterhours-lab",
        key_sha256=hash_api_key("unscoped-key"),
        capabilities=frozenset(),
        priority_class=PriorityClass.BACKGROUND,
    )
    denied_server = TestServer(
        create_app(
            upstream,
            InternalKeyAuthenticator((unscoped,)),
            token_readiness_provider=ready(),
        )
    )
    await denied_server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(denied_server.make_url("/"))) as client:
            denied = await client.get(
                "/v1/quotes",
                params={"symbols": "AAPL"},
                headers={"X-Internal-API-Key": "unscoped-key"},
            )
    finally:
        await denied_server.close()

    assert denied.status_code == 403
    assert denied.json()["error"] == {
        "code": "capability_denied",
        "message": "the caller lacks the required capability",
    }


@pytest.mark.asyncio
async def test_quote_reads_require_readiness_for_every_authenticated_caller() -> None:
    upstream = FakeUpstream()
    server = TestServer(
        create_app(upstream, InternalKeyAuthenticator(tuple(principal(name) for name in KEYS)))
    )
    await server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(server.make_url("/"))) as client:
            responses = [
                await client.get(
                    "/v1/quotes",
                    params={"symbols": "AAPL"},
                    headers={"X-Internal-API-Key": key},
                )
                for key in KEYS.values()
            ]
    finally:
        await server.close()

    assert [response.status_code for response in responses] == [503, 503, 503]
    assert all(response.json()["error"]["code"] == "gateway_not_ready" for response in responses)
    assert upstream.calls == []


def test_foundation_route_table_is_exact_and_has_no_sensitive_surface() -> None:
    app = create_app(FakeUpstream(), InternalKeyAuthenticator((principal("butterfly-guy"),)))

    route_shapes = {(route.method, route.resource.canonical) for route in app.router.routes()}
    expected_paths = {"/health", "/ready", "/metrics", "/v1/quotes"}
    assert {path for _method, path in route_shapes} == expected_paths
    assert {method for method, _path in route_shapes} == {"GET", "HEAD"}
    assert not any(
        sensitive in path
        for _method, path in route_shapes
        for sensitive in ("account", "order", "position", "transaction", "stream")
    )


@pytest.mark.asyncio
async def test_client_sends_only_the_internal_key_as_sensitive_authentication() -> None:
    captured: list[httpx.Request] = []
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "schema_version": "1.0",
                "quotes": [
                    {
                        "symbol": "AAPL",
                        "gateway_received_at": now,
                        "source": "fake",
                        "stale": False,
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://gateway.invalid",
        transport=transport,
    ) as http:
        client = GatewayMarketDataClient(
            "http://gateway.invalid",
            "synthetic-internal-key",
            client=http,
        )
        await client.get_quotes(["AAPL"])

    assert len(captured) == 1
    request = captured[0]
    assert request.headers["X-Internal-API-Key"] == "synthetic-internal-key"
    assert "authorization" not in request.headers
    assert not any(
        name in request.headers
        for name in (
            "SCHWAB_API_KEY",
            "SCHWAB_SECRET_KEY",
            "SCHWAB_TOKEN_PATH",
            "Cookie",
        )
    )


def test_strategy_risk_and_execution_layers_do_not_import_gateway_server_internals() -> None:
    roots = [
        Path("src/butterfly_guy/strategy"),
        Path("src/butterfly_guy/risk"),
        Path("src/butterfly_guy/execution"),
        Path("src/butterfly_guy/services"),
        Path("src/butterfly_guy/position"),
    ]
    violations: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                    "butterfly_guy.schwab_gateway"
                ):
                    violations.append(f"{path}:{node.lineno}")
                elif isinstance(node, ast.Import) and any(
                    alias.name.startswith("butterfly_guy.schwab_gateway")
                    for alias in node.names
                ):
                    violations.append(f"{path}:{node.lineno}")

    assert violations == []
