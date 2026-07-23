import datetime as dt

import httpx
import pytest

from butterfly_guy.candidate_fleet.models import MarketSnapshot, SnapshotIdentity
from butterfly_guy.candidate_fleet.provider import (
    HttpMarketDataProvider,
    SchwabMarketDataProvider,
)
from butterfly_guy.data.schemas import OptionQuote


def make_snapshot() -> MarketSnapshot:
    expiration = dt.date.today()
    return MarketSnapshot(
        identity=SnapshotIdentity("feed-contract", 7),
        captured_at=dt.datetime.now(dt.timezone.utc),
        expiration=expiration,
        spot=6300,
        vix=20,
        session_open=6290,
        previous_close=6280,
        quotes=(
            OptionQuote(
                symbol="L",
                underlying="SPX",
                expiration=expiration,
                strike=6280,
                option_type="CALL",
                bid=3,
                ask=3.2,
                mark=3.1,
            ),
            OptionQuote(
                symbol="C",
                underlying="SPX",
                expiration=expiration,
                strike=6300,
                option_type="CALL",
                bid=1,
                ask=1.2,
                mark=1.1,
            ),
            OptionQuote(
                symbol="U",
                underlying="SPX",
                expiration=expiration,
                strike=6320,
                option_type="CALL",
                bid=0.1,
                ask=0.2,
                mark=0.15,
            ),
        ),
    )


@pytest.mark.asyncio
async def test_http_and_schwab_provider_contracts_normalize_equally() -> None:
    expected = make_snapshot()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/snapshot":
            return httpx.Response(200, json=expected.to_dict())
        if request.url.path == "/v1/legs":
            return httpx.Response(200, json=expected.leg_quotes(("L", "C", "U")).to_dict())
        return httpx.Response(204)

    client = httpx.AsyncClient(
        base_url="http://candidate-feed",
        transport=httpx.MockTransport(handler),
    )
    http_provider = HttpMarketDataProvider("http://candidate-feed", client=client)
    direct_provider = SchwabMarketDataProvider(lambda: _return(expected))

    assert await http_provider.snapshot() == await direct_provider.snapshot()
    assert await http_provider.legs(("L", "C", "U")) == await direct_provider.legs(
        ("L", "C", "U")
    )
    await client.aclose()


@pytest.mark.asyncio
async def test_http_provider_retries_server_failures() -> None:
    expected = make_snapshot()
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=expected.to_dict())

    client = httpx.AsyncClient(
        base_url="http://candidate-feed",
        transport=httpx.MockTransport(handler),
    )
    provider = HttpMarketDataProvider("http://candidate-feed", client=client)

    assert (await provider.snapshot()).sequence == 7
    assert calls == 3
    await client.aclose()


async def _return(snapshot: MarketSnapshot) -> MarketSnapshot:
    return snapshot
