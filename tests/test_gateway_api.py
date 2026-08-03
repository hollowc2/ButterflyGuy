from __future__ import annotations

import asyncio
import datetime as dt

import httpx
import pytest
from aiohttp.test_utils import TestServer

from butterfly_guy.gateway_client.client import (
    GatewayAuthorizationError,
    GatewayMarketDataClient,
    GatewayUnavailableError,
)
from butterfly_guy.gateway_client.models import QuoteV1
from butterfly_guy.schwab_gateway.api import create_app
from butterfly_guy.schwab_gateway.auth import (
    InternalKeyAuthenticator,
    InternalPrincipal,
    hash_api_key,
)


class FakeQuoteUpstream:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    async def get_quotes(self, symbols: tuple[str, ...]) -> tuple[QuoteV1, ...]:
        self.calls.append(symbols)
        now = dt.datetime.now(dt.timezone.utc)
        return tuple(
            QuoteV1(
                symbol=symbol,
                event_timestamp=now,
                gateway_received_at=now,
                source="fake_schwab",
                bid=100.0,
                ask=100.2,
                mark=100.1,
                stale=False,
                age_seconds=0,
            )
            for symbol in symbols
        )


def authenticator(*, capability: str = "market_data:read") -> InternalKeyAuthenticator:
    return InternalKeyAuthenticator(
        (
            InternalPrincipal(
                client_id="butterfly-guy",
                key_sha256=hash_api_key("valid-key"),
                capabilities=frozenset({capability}),
            ),
        )
    )


@pytest.mark.asyncio
async def test_client_to_http_gateway_to_fake_upstream_contract() -> None:
    upstream = FakeQuoteUpstream()
    server = TestServer(create_app(upstream, authenticator()))
    await server.start_server()
    try:
        client = GatewayMarketDataClient(str(server.make_url("/")), "valid-key")
        response = await client.get_quotes(["AAPL", "MSFT"])
        await client.close()
    finally:
        await server.close()

    assert response.schema_version == "1.0"
    assert [quote.symbol for quote in response.quotes] == ["AAPL", "MSFT"]
    assert response.quotes[0].bid == 100.0
    assert upstream.calls == [("AAPL", "MSFT")]


@pytest.mark.asyncio
async def test_gateway_authentication_authorization_and_health_contracts() -> None:
    server = TestServer(create_app(FakeQuoteUpstream(), authenticator(capability="history:read")))
    await server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(server.make_url("/"))) as http:
            health = await http.get("/health")
            missing = await http.get("/v1/quotes", params={"symbols": "AAPL"})
            invalid = await http.get(
                "/v1/quotes",
                params={"symbols": "AAPL"},
                headers={"X-Internal-API-Key": "invalid"},
            )
            client = GatewayMarketDataClient(
                str(server.make_url("/")),
                "valid-key",
                client=http,
            )
            with pytest.raises(GatewayAuthorizationError):
                await client.get_quotes(["AAPL"])
    finally:
        await server.close()

    assert health.status_code == 200
    assert health.json()["service"] == "schwab-gateway"
    assert "key" not in health.text.lower()
    assert missing.status_code == 401
    assert invalid.status_code == 401


@pytest.mark.asyncio
async def test_gateway_validates_symbols_and_exposes_no_order_routes() -> None:
    app = create_app(FakeQuoteUpstream(), authenticator())
    server = TestServer(app)
    await server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(server.make_url("/"))) as http:
            response = await http.get(
                "/v1/quotes",
                params={"symbols": "AAPL,bad symbol"},
                headers={"X-Internal-API-Key": "valid-key"},
            )
            missing_order = await http.post(
                "/v1/orders",
                headers={"X-Internal-API-Key": "valid-key"},
            )
            metrics = await http.get("/metrics")
    finally:
        await server.close()

    route_shapes = {(route.method, route.resource.canonical) for route in app.router.routes()}
    assert response.status_code == 400
    assert missing_order.status_code == 404
    assert (
        'gateway_client_requests_total{operation="unknown",status="404"} 1.0'
        in metrics.text
    )
    assert all("order" not in path for _method, path in route_shapes)
    assert all(method != "POST" for method, _path in route_shapes)


@pytest.mark.asyncio
async def test_gateway_surfaces_upstream_timeout() -> None:
    class SlowUpstream:
        async def get_quotes(self, _symbols):
            await asyncio.sleep(0.05)
            return ()

    server = TestServer(
        create_app(SlowUpstream(), authenticator(), upstream_timeout_seconds=0.001)
    )
    await server.start_server()
    try:
        client = GatewayMarketDataClient(str(server.make_url("/")), "valid-key")
        with pytest.raises(GatewayUnavailableError):
            await client.get_quotes(["AAPL"])
        await client.close()
    finally:
        await server.close()
