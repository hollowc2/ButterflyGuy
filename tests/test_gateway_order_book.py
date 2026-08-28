"""ButterflyGuy's fail-closed SchwabGateway order-book consumer contract."""

from __future__ import annotations

import json

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from butterfly_guy.data.gateway_order_book import (
    GatewayOrderBookClient,
    OrderBookContractError,
    OrderBookUnavailableError,
)


def _snapshot(*, symbol: str = "AAPL", venue: str = "NASDAQ") -> dict:
    return {
        "schema_version": "1.0",
        "symbol": symbol,
        "venue": venue,
        "service": f"{venue}_BOOK",
        "connection_id": 1,
        "continuity_epoch": 1,
        "sequence": None,
        "event_timestamp": "2026-08-27T17:00:00Z",
        "gateway_received_at": "2026-08-27T17:00:00.100000Z",
        "source": "schwab_streaming",
        "is_consolidated": False,
        "bids": [
            {
                "price": 100.0,
                "total_size": 5,
                "participant_count": 1,
                "participants": [{"exchange": "Q", "size": 5, "sequence": None}],
            }
        ],
        "asks": [
            {
                "price": 100.1,
                "total_size": 8,
                "participant_count": 0,
                "participants": [],
            }
        ],
        "data_quality_flags": ["sequence_unavailable"],
    }


def _recent_payload() -> dict:
    return {
        "schema_version": "1.0",
        "symbol": "AAPL",
        "venue": "NASDAQ",
        "is_consolidated": False,
        "snapshots": [_snapshot()],
        "generated_at": "2026-08-27T17:00:00.200000Z",
        "stale": False,
        "age_seconds": 0.1,
    }


@pytest.mark.asyncio
async def test_recent_authenticates_and_validates_fresh_contract() -> None:
    seen: dict[str, str] = {}

    async def recent(request: web.Request) -> web.Response:
        seen.update(request.query)
        seen["api_key"] = request.headers["X-Internal-API-Key"]
        return web.json_response(_recent_payload())

    app = web.Application()
    app.router.add_get("/v1/order-book/recent", recent)
    async with TestServer(app) as server:
        async with GatewayOrderBookClient(str(server.make_url("/")), "secret") as client:
            response = await client.recent("aapl", venue="nasdaq", limit=1)

    assert response.symbol == "AAPL"
    assert response.stale is False
    assert response.snapshots[0].bids[0].price == 100.0
    assert seen == {
        "symbol": "AAPL",
        "venue": "NASDAQ",
        "limit": "1",
        "api_key": "secret",
    }


@pytest.mark.asyncio
async def test_recent_fails_closed_when_gateway_reports_stale_feed() -> None:
    async def unavailable(_request: web.Request) -> web.Response:
        return web.json_response({"error": {"code": "order_book_unavailable"}}, status=503)

    app = web.Application()
    app.router.add_get("/v1/order-book/recent", unavailable)
    async with TestServer(app) as server:
        async with GatewayOrderBookClient(str(server.make_url("/")), "secret") as client:
            with pytest.raises(OrderBookUnavailableError):
                await client.recent("AAPL", venue="NASDAQ")


@pytest.mark.asyncio
async def test_recent_rejects_mismatched_snapshot() -> None:
    payload = _recent_payload()
    payload["snapshots"] = [_snapshot(symbol="MSFT")]

    async def recent(_request: web.Request) -> web.Response:
        return web.json_response(payload)

    app = web.Application()
    app.router.add_get("/v1/order-book/recent", recent)
    async with TestServer(app) as server:
        async with GatewayOrderBookClient(str(server.make_url("/")), "secret") as client:
            with pytest.raises(OrderBookContractError, match="mismatched"):
                await client.recent("AAPL", venue="NASDAQ")


@pytest.mark.asyncio
async def test_stream_authenticates_and_yields_only_requested_contracts() -> None:
    seen: dict[str, str] = {}

    async def stream(request: web.Request) -> web.WebSocketResponse:
        seen.update(request.query)
        seen["api_key"] = request.headers["X-Internal-API-Key"]
        socket = web.WebSocketResponse()
        await socket.prepare(request)
        await socket.send_str(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "type": "order_book_snapshot",
                    "snapshot": _snapshot(),
                }
            )
        )
        await socket.close()
        return socket

    app = web.Application()
    app.router.add_get("/v1/order-book/stream", stream)
    async with TestServer(app) as server:
        async with GatewayOrderBookClient(str(server.make_url("/")), "secret") as client:
            snapshots = [snapshot async for snapshot in client.stream(["aapl"], venue="nasdaq")]

    assert len(snapshots) == 1
    assert snapshots[0].asks[0].price == 100.1
    assert seen == {"symbols": "AAPL", "venue": "NASDAQ", "api_key": "secret"}


@pytest.mark.asyncio
async def test_stream_rejects_an_unrequested_symbol() -> None:
    async def stream(request: web.Request) -> web.WebSocketResponse:
        socket = web.WebSocketResponse()
        await socket.prepare(request)
        await socket.send_json(
            {
                "schema_version": "1.0",
                "type": "order_book_snapshot",
                "snapshot": _snapshot(symbol="MSFT"),
            }
        )
        return socket

    app = web.Application()
    app.router.add_get("/v1/order-book/stream", stream)
    async with TestServer(app) as server:
        async with GatewayOrderBookClient(str(server.make_url("/")), "secret") as client:
            with pytest.raises(OrderBookContractError, match="unrequested"):
                _ = [
                    snapshot
                    async for snapshot in client.stream(["AAPL"], venue="NASDAQ")
                ]


def test_client_rejects_unsafe_or_ambiguous_inputs() -> None:
    with pytest.raises(ValueError, match="API key"):
        GatewayOrderBookClient("http://gateway", "")
