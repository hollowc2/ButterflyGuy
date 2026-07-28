import datetime as dt

import httpx
import pytest

from butterfly_guy.candidate_fleet.models import (
    MarketSnapshot,
    SessionClose,
    SessionCloseUnavailableError,
    SnapshotIdentity,
    SnapshotWaitTimeoutError,
)
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


def make_session_close(
    session_date: dt.date = dt.date(2026, 7, 23),
) -> SessionClose:
    return SessionClose(
        session_date=session_date,
        close=6305.25,
        bar_timestamp=dt.datetime(2026, 7, 23, 19, 59, tzinfo=dt.timezone.utc),
        observed_at=dt.datetime(2026, 7, 23, 20, 1, tzinfo=dt.timezone.utc),
        source="schwab_spx_intraday_1m_regular_session_close",
        feed_instance="feed-contract",
    )


@pytest.mark.asyncio
async def test_http_and_schwab_provider_contracts_normalize_equally() -> None:
    expected = make_snapshot()
    expected_close = make_session_close()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/snapshot":
            return httpx.Response(200, json=expected.to_dict())
        if request.url.path == "/v1/legs":
            return httpx.Response(200, json=expected.leg_quotes(("L", "C", "U")).to_dict())
        if request.url.path == "/v1/sessions/2026-07-23/close":
            return httpx.Response(200, json=expected_close.to_dict())
        return httpx.Response(204)

    client = httpx.AsyncClient(
        base_url="http://candidate-feed",
        transport=httpx.MockTransport(handler),
    )
    http_provider = HttpMarketDataProvider("http://candidate-feed", client=client)
    direct_provider = SchwabMarketDataProvider(
        lambda: _return(expected),
        session_close_loader=lambda _day: _return_close(expected_close),
    )

    assert await http_provider.snapshot() == await direct_provider.snapshot()
    assert await http_provider.legs(("L", "C", "U")) == await direct_provider.legs(
        ("L", "C", "U")
    )
    assert await http_provider.session_close(
        expected_close.session_date
    ) == await direct_provider.session_close(expected_close.session_date)
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


@pytest.mark.asyncio
async def test_http_provider_surfaces_no_newer_snapshot_without_server_retries() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            503,
            json={"error": "no newer snapshot is available"},
        )

    client = httpx.AsyncClient(
        base_url="http://candidate-feed",
        transport=httpx.MockTransport(handler),
    )
    provider = HttpMarketDataProvider("http://candidate-feed", client=client)

    with pytest.raises(SnapshotWaitTimeoutError, match="no newer snapshot"):
        await provider.legs(("L", "C", "U"), wait_seconds=3)
    assert calls == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_http_provider_fails_closed_on_mismatched_session_close() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=make_session_close().to_dict())

    client = httpx.AsyncClient(
        base_url="http://candidate-feed",
        transport=httpx.MockTransport(handler),
    )
    provider = HttpMarketDataProvider("http://candidate-feed", client=client)

    with pytest.raises(SessionCloseUnavailableError, match="different session date"):
        await provider.session_close(dt.date(2026, 7, 24))
    await client.aclose()


async def _return(snapshot: MarketSnapshot) -> MarketSnapshot:
    return snapshot


async def _return_close(session_close: SessionClose) -> SessionClose:
    return session_close
