"""The shadow comparator must never change what the collector sees, on any path."""

from __future__ import annotations

import asyncio
import datetime as dt

import httpx
import pytest
from aiohttp.test_utils import TestServer
from pydantic import ValidationError

from butterfly_guy.core.metrics import (
    gateway_shadow_comparisons,
    gateway_shadow_discrepancies,
)
from butterfly_guy.gateway_client import shadow as shadow_module
from butterfly_guy.gateway_client.client import (
    GatewayAuthenticationError,
    GatewayAuthorizationError,
    GatewayCapacityError,
    GatewayMarketDataClient,
    GatewayResponseError,
    GatewayTimeoutError,
    GatewayUnavailableError,
)
from butterfly_guy.gateway_client.config import GatewayClientSettings
from butterfly_guy.gateway_client.models import ChainMetadataResponseV1, SpotResponseV1
from butterfly_guy.gateway_client.shadow import (
    CHAIN_COUNT_FIELDS,
    CLASSIFICATION_BY_CODE,
    SHADOW_CLASSIFICATIONS,
    ShadowComparingMarketDataProvider,
)
from butterfly_guy.schwab_gateway.api import create_app
from butterfly_guy.schwab_gateway.auth import (
    InternalKeyAuthenticator,
    InternalPrincipal,
    PriorityClass,
    hash_api_key,
)
from butterfly_guy.schwab_gateway.token_manager import (
    TokenManagerHealth,
    TokenManagerState,
)
from butterfly_guy.schwab_gateway.upstream import (
    DirectSchwabChainMetadataUpstream,
    DirectSchwabSpotUpstream,
)

EXPIRATION = dt.date(2026, 8, 6)
DIRECT_SPOT = 5000.25
CHAIN_PAYLOAD = {
    "underlyingPrice": DIRECT_SPOT,
    "underlying": {"quoteTime": 1785000000000},
    "callExpDateMap": {
        "2026-08-06:0": {"5000.0": [{"bid": 1.0}], "5010.0": [{"bid": 0.5}]}
    },
    "putExpDateMap": {"2026-08-06:0": {"5000.0": [{"bid": 1.1}]}},
}


class DirectProvider:
    """The only source of returned values. Records every delegated call."""

    def __init__(self, spot: float = DIRECT_SPOT, chain: dict | None = None) -> None:
        self.spot = spot
        self.chain = CHAIN_PAYLOAD if chain is None else chain
        self.calls: list[str] = []

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        self.calls.append("get_spot_price")
        return self.spot

    async def get_option_chain(self, symbol: str, expiration: dt.date) -> dict:
        self.calls.append("get_option_chain")
        return self.chain

    async def get_intraday_bars(self, symbol: str = "$SPX", days_back: int = 1) -> list[dict]:
        self.calls.append("get_intraday_bars")
        return [{"close": 1.0}]

    async def get_intraday_bars_for_day(
        self, symbol: str, day: dt.date, *, include_extended_hours: bool = True
    ) -> list[dict]:
        self.calls.append("get_intraday_bars_for_day")
        return [{"close": 2.0}]

    async def get_daily_bars(self, symbol: str, days_back: int = 10) -> list[dict]:
        self.calls.append("get_daily_bars")
        return [{"close": 3.0}]


class RecordingGateway:
    """Stands in for GatewayMarketDataClient with a scripted spot/chain reply."""

    def __init__(self, spot_result=None, chain_result=None) -> None:
        self.spot_result = spot_result
        self.chain_result = chain_result
        self.calls: list[str] = []

    async def get_spot(self, symbol: str):
        self.calls.append("get_spot")
        if isinstance(self.spot_result, Exception):
            raise self.spot_result
        return self.spot_result

    async def get_chain_metadata(self, symbol: str, expiration: dt.date):
        self.calls.append("get_chain_metadata")
        if isinstance(self.chain_result, Exception):
            raise self.chain_result
        return self.chain_result


def spot_response(
    price: float | None,
    *,
    stale: bool = False,
    age_seconds: float | None = 0.5,
) -> SpotResponseV1:
    return SpotResponseV1.model_validate(
        {
            "spot": {
                "symbol": "$SPX",
                "price": price,
                "gateway_received_at": dt.datetime.now(dt.timezone.utc),
                "source": "fake",
                "stale": stale,
                "age_seconds": age_seconds,
            }
        }
    )


def chain_response(
    *,
    underlying_price: float | None = DIRECT_SPOT,
    call_count: int = 2,
    put_count: int = 1,
    strike_count: int = 2,
    stale: bool = False,
    age_seconds: float | None = 1.0,
) -> ChainMetadataResponseV1:
    return ChainMetadataResponseV1.model_validate(
        {
            "chain": {
                "symbol": "SPX",
                "expiration": EXPIRATION,
                "underlying_price": underlying_price,
                "call_contract_count": call_count,
                "put_contract_count": put_count,
                "strike_count": strike_count,
                "gateway_received_at": dt.datetime.now(dt.timezone.utc),
                "source": "fake",
                "stale": stale,
                "age_seconds": age_seconds,
            }
        }
    )


# --- the flag is the whole gate --------------------------------------------------------


@pytest.mark.asyncio
async def test_default_flag_never_contacts_the_gateway() -> None:
    direct = DirectProvider()
    gateway = RecordingGateway(spot_result=spot_response(1.0), chain_result=chain_response())
    provider = ShadowComparingMarketDataProvider(direct, gateway)

    assert provider.shadow_enabled is False
    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD

    assert gateway.calls == []
    assert provider.recorder.total() == 0


def test_shadow_reads_setting_defaults_to_false_and_requires_connection_settings() -> None:
    assert GatewayClientSettings().shadow_reads is False
    assert GatewayClientSettings(SCHWAB_GATEWAY_SHADOW_READS="false").shadow_reads is False

    with pytest.raises(ValidationError, match="shadow reads require"):
        GatewayClientSettings(SCHWAB_GATEWAY_SHADOW_READS="true")

    enabled = GatewayClientSettings(
        SCHWAB_GATEWAY_SHADOW_READS="true",
        SCHWAB_GATEWAY_URL="http://127.0.0.1:8010",
        SCHWAB_GATEWAY_API_KEY="test-secret",
    )
    assert enabled.shadow_reads is True
    assert enabled.access_mode == "direct"
    assert "test-secret" not in repr(enabled)


@pytest.mark.asyncio
async def test_shadow_stays_disabled_when_no_gateway_client_is_supplied() -> None:
    direct = DirectProvider()
    provider = ShadowComparingMarketDataProvider(direct, None, shadow_reads=True)

    assert provider.shadow_enabled is False
    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert provider.recorder.total() == 0


# --- the direct result is returned unchanged, always -----------------------------------


@pytest.mark.asyncio
async def test_direct_result_is_unchanged_when_the_gateway_agrees() -> None:
    direct = DirectProvider()
    gateway = RecordingGateway(
        spot_result=spot_response(DIRECT_SPOT), chain_result=chain_response()
    )
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD
    await provider.wait_for_shadow_reads()

    assert gateway.calls == ["get_spot", "get_chain_metadata"]
    assert provider.recorder.total() == 0


@pytest.mark.asyncio
async def test_direct_result_is_unchanged_when_the_gateway_disagrees() -> None:
    direct = DirectProvider()
    gateway = RecordingGateway(
        spot_result=spot_response(1.0),
        chain_result=chain_response(call_count=999, underlying_price=1.0),
    )
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD
    await provider.wait_for_shadow_reads()
    assert provider.recorder.total() == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        GatewayTimeoutError("timed out"),
        GatewayUnavailableError("unavailable"),
        GatewayCapacityError("capacity"),
        GatewayAuthenticationError("auth"),
        GatewayAuthorizationError("authz"),
        GatewayResponseError("contract"),
        RuntimeError("an unclassified failure at /private/token/path"),
    ],
)
async def test_direct_result_is_unchanged_when_the_gateway_errors(error: Exception) -> None:
    direct = DirectProvider()
    gateway = RecordingGateway(spot_result=error, chain_result=error)
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD
    await provider.wait_for_shadow_reads()
    assert provider.recorder.total() == 2


@pytest.mark.asyncio
async def test_direct_result_is_unchanged_when_the_gateway_times_out_in_real_time() -> None:
    class HangingGateway:
        async def get_spot(self, symbol: str):
            await asyncio.sleep(0.01)
            raise GatewayTimeoutError("gateway market data request timed out")

        async def get_chain_metadata(self, symbol: str, expiration: dt.date):
            await asyncio.sleep(0.01)
            raise GatewayTimeoutError("gateway market data request timed out")

    direct = DirectProvider()
    provider = ShadowComparingMarketDataProvider(direct, HangingGateway(), shadow_reads=True)

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD
    await provider.wait_for_shadow_reads()
    assert {d.classification for d in provider.recorder.counts()} == {"timing"}


@pytest.mark.asyncio
async def test_non_shadowed_reads_are_pure_delegation() -> None:
    direct = DirectProvider()
    gateway = RecordingGateway(spot_result=spot_response(1.0))
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_intraday_bars("$SPX", 2) == [{"close": 1.0}]
    assert await provider.get_intraday_bars_for_day("$SPX", EXPIRATION) == [{"close": 2.0}]
    assert await provider.get_daily_bars("$SPX", 5) == [{"close": 3.0}]

    assert gateway.calls == []
    assert direct.calls == [
        "get_intraday_bars",
        "get_intraday_bars_for_day",
        "get_daily_bars",
    ]


# --- classification --------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "code", "classification"),
    [
        (GatewayTimeoutError("x"), "gateway_timeout", "timing"),
        (GatewayUnavailableError("x"), "gateway_unavailable", "upstream"),
        (GatewayCapacityError("x"), "gateway_capacity_exceeded", "upstream"),
        (GatewayAuthenticationError("x"), "gateway_authentication_failed", "upstream"),
        (GatewayAuthorizationError("x"), "gateway_authorization_failed", "upstream"),
        (GatewayResponseError("x"), "gateway_contract_invalid", "parsing"),
        (RuntimeError("x"), "gateway_unexpected_error", "upstream"),
    ],
)
async def test_gateway_errors_are_classified_by_fixed_code(
    error: Exception, code: str, classification: str
) -> None:
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), RecordingGateway(spot_result=error), shadow_reads=True
    )
    await provider.get_spot_price("$SPX")
    await provider.wait_for_shadow_reads()

    (discrepancy,) = provider.recorder.counts()
    assert discrepancy.operation == "spot"
    assert discrepancy.code == code
    assert discrepancy.classification == classification
    assert discrepancy.fields == ()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stale", "age_seconds", "code", "classification"),
    [
        (False, 0.5, "gateway_value_mismatch", "parsing"),
        (True, 600.0, "gateway_stale_value", "cache"),
        (True, None, "gateway_unknown_age", "timing"),
    ],
)
async def test_value_differences_are_classified_by_provable_freshness(
    stale: bool, age_seconds: float | None, code: str, classification: str
) -> None:
    gateway = RecordingGateway(
        spot_result=spot_response(1.0, stale=stale, age_seconds=age_seconds),
        chain_result=chain_response(call_count=99, stale=stale, age_seconds=age_seconds),
    )
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), gateway, shadow_reads=True
    )

    await provider.get_spot_price("$SPX")
    await provider.get_option_chain("SPX", EXPIRATION)
    await provider.wait_for_shadow_reads()

    observed = sorted(provider.recorder.counts(), key=lambda d: d.operation)
    assert [d.operation for d in observed] == ["chain", "spot"]
    assert {d.code for d in observed} == {code}
    assert {d.classification for d in observed} == {classification}
    assert observed[0].fields == ("call_contract_count",)
    assert observed[1].fields == ("price",)


@pytest.mark.asyncio
async def test_every_declared_classification_is_one_of_the_four_migration_categories() -> None:
    assert set(CLASSIFICATION_BY_CODE.values()) == set(SHADOW_CLASSIFICATIONS)
    assert set(SHADOW_CLASSIFICATIONS) == {"timing", "cache", "parsing", "upstream"}


@pytest.mark.asyncio
async def test_a_direct_payload_that_cannot_be_summarized_is_a_parsing_discrepancy() -> None:
    """``extract_chain_metadata`` now tolerates a payload with no expiration maps (it
    matches both live parsers on that shape), so ``{"status": "FAILED"}`` no longer
    counts as unsummarizable -- it agrees with the gateway's chain_response() as a
    plain field mismatch instead. The one shape ``extract_chain_metadata`` still
    refuses is a payload that is not a dict at all, so that is what this test uses to
    exercise the "direct_payload_invalid" classification."""
    direct = DirectProvider(chain="not-a-chain-payload")
    gateway = RecordingGateway(chain_result=chain_response())
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_option_chain("SPX", EXPIRATION) == "not-a-chain-payload"
    await provider.wait_for_shadow_reads()

    (discrepancy,) = provider.recorder.counts()
    assert discrepancy.code == "direct_payload_invalid"
    assert discrepancy.classification == "parsing"


@pytest.mark.asyncio
async def test_a_null_gateway_price_is_reported_as_a_field_level_difference() -> None:
    gateway = RecordingGateway(spot_result=spot_response(None))
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), gateway, shadow_reads=True
    )
    await provider.get_spot_price("$SPX")
    await provider.wait_for_shadow_reads()

    (discrepancy,) = provider.recorder.counts()
    assert discrepancy.fields == ("price",)


@pytest.mark.asyncio
async def test_prices_within_tolerance_are_not_a_discrepancy() -> None:
    gateway = RecordingGateway(spot_result=spot_response(DIRECT_SPOT + 0.005))
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), gateway, shadow_reads=True, price_tolerance=0.01
    )
    await provider.get_spot_price("$SPX")
    await provider.wait_for_shadow_reads()

    assert provider.recorder.total() == 0


# --- bounded diagnostics ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_unbounded_detail_reaches_the_logs(monkeypatch) -> None:
    """Assert on what is handed to the logger, independent of any configured sink."""
    emitted: list[tuple[str, dict]] = []

    class RecordingLogger:
        def warning(self, event: str, **kwargs) -> None:
            emitted.append((event, kwargs))

    monkeypatch.setattr(shadow_module, "log", RecordingLogger())

    secret = "/private/token/path?key=access-secret"
    gateway = RecordingGateway(
        spot_result=RuntimeError(secret),
        chain_result=chain_response(call_count=41, underlying_price=9.0),
    )
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), gateway, shadow_reads=True
    )

    await provider.get_spot_price("$SPX")
    await provider.get_option_chain("SPX", EXPIRATION)
    await provider.wait_for_shadow_reads()

    assert [event for event, _ in emitted] == [
        "gateway_shadow_discrepancy",
        "gateway_shadow_discrepancy",
    ]
    for _event, kwargs in emitted:
        assert set(kwargs) == {"operation", "code", "classification", "fields"}
        assert kwargs["code"] in CLASSIFICATION_BY_CODE
        assert kwargs["classification"] in SHADOW_CLASSIFICATIONS
        assert kwargs["operation"] in {"spot", "chain"}
        assert set(kwargs["fields"]) <= {"price", *CHAIN_COUNT_FIELDS, "underlying_price"}

    text = repr(emitted)
    assert secret not in text
    assert "access-secret" not in text
    assert "/private" not in text
    assert str(DIRECT_SPOT) not in text
    assert "5000" not in text
    assert "41" not in text

    for discrepancy in provider.recorder.counts():
        assert discrepancy.code in CLASSIFICATION_BY_CODE
        assert discrepancy.classification in SHADOW_CLASSIFICATIONS
        assert discrepancy.operation in {"spot", "chain"}
        assert all(isinstance(name, str) for name in discrepancy.fields)


@pytest.mark.asyncio
async def test_repeated_discrepancies_collapse_onto_a_fixed_key_space() -> None:
    gateway = RecordingGateway(spot_result=GatewayUnavailableError("x"))
    provider = ShadowComparingMarketDataProvider(
        DirectProvider(), gateway, shadow_reads=True
    )
    for _ in range(25):
        await provider.get_spot_price("$SPX")
    await provider.wait_for_shadow_reads()

    counts = provider.recorder.counts()
    assert len(counts) == 1
    assert provider.recorder.total() == 25


# --- the shadow read never sits on the caller's critical path --------------------------


@pytest.mark.asyncio
async def test_get_spot_price_returns_before_a_slow_gateway_responds() -> None:
    class SlowGateway:
        def __init__(self) -> None:
            self.started = asyncio.Event()
            self.finished = False

        async def get_spot(self, symbol: str):
            self.started.set()
            await asyncio.sleep(1.0)
            self.finished = True
            return spot_response(DIRECT_SPOT)

    direct = DirectProvider()
    gateway = SlowGateway()
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    loop = asyncio.get_running_loop()
    start = loop.time()
    price = await provider.get_spot_price("$SPX")
    elapsed = loop.time() - start

    assert price == DIRECT_SPOT
    # The gateway call was in flight when we returned, but we didn't wait on it.
    assert gateway.started.is_set()
    assert gateway.finished is False
    assert elapsed < 0.2  # well under the gateway's 1.0s delay

    # The comparison still completes eventually, off the critical path.
    await provider.wait_for_shadow_reads()
    assert gateway.finished is True
    assert provider.recorder.total() == 0


@pytest.mark.asyncio
async def test_get_option_chain_returns_before_a_slow_gateway_responds() -> None:
    class SlowGateway:
        def __init__(self) -> None:
            self.finished = False

        async def get_chain_metadata(self, symbol: str, expiration: dt.date):
            await asyncio.sleep(1.0)
            self.finished = True
            return chain_response()

    direct = DirectProvider()
    gateway = SlowGateway()
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    loop = asyncio.get_running_loop()
    start = loop.time()
    chain = await provider.get_option_chain("SPX", EXPIRATION)
    elapsed = loop.time() - start

    assert chain is CHAIN_PAYLOAD
    assert gateway.finished is False
    assert elapsed < 0.2  # well under the gateway's 1.0s delay

    await provider.wait_for_shadow_reads()
    assert gateway.finished is True
    assert provider.recorder.total() == 0


# --- end to end against the real in-process gateway ------------------------------------


@pytest.mark.asyncio
async def test_shadow_comparison_against_the_real_in_process_gateway_agrees() -> None:
    direct = DirectProvider()

    authenticator = InternalKeyAuthenticator(
        (
            InternalPrincipal(
                client_id="butterfly-guy",
                key_sha256=hash_api_key("valid-key"),
                capabilities=frozenset({"market_data:read"}),
                priority_class=PriorityClass.PROTECTED,
            ),
        )
    )

    class Ready:
        def health(self) -> TokenManagerHealth:
            return TokenManagerHealth(
                state=TokenManagerState.READY,
                reason="fake",
                updated_at=dt.datetime.now(dt.timezone.utc),
            )

    class Upstreams:
        async def get_quotes(self, symbols: tuple[str, ...]) -> tuple:
            return ()

    server = TestServer(
        create_app(
            Upstreams(),
            authenticator,
            token_readiness_provider=Ready(),
            spot_upstream=DirectSchwabSpotUpstream(direct),
            chain_upstream=DirectSchwabChainMetadataUpstream(direct),
        )
    )
    await server.start_server()
    try:
        async with httpx.AsyncClient(base_url=str(server.make_url("/"))) as http:
            gateway = GatewayMarketDataClient(
                str(server.make_url("/")), "valid-key", client=http
            )
            provider = ShadowComparingMarketDataProvider(
                direct, gateway, shadow_reads=True
            )
            spot = await provider.get_spot_price("$SPX")
            chain = await provider.get_option_chain("SPX", EXPIRATION)
            await provider.wait_for_shadow_reads()
    finally:
        await server.close()

    assert spot == DIRECT_SPOT
    assert chain is CHAIN_PAYLOAD
    assert provider.recorder.total() == 0


def _comparisons(operation: str, result: str) -> float:
    """Current value of one comparison counter; the child is created at zero if absent."""
    return gateway_shadow_comparisons.labels(
        operation=operation, result=result
    )._value.get()


def _discrepancies(operation: str, code: str, classification: str) -> float:
    return gateway_shadow_discrepancies.labels(
        operation=operation, code=code, classification=classification
    )._value.get()


class FailingDirectProvider(DirectProvider):
    """A direct provider whose reads raise, to exercise the direct_unavailable path."""

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        raise RuntimeError("direct spot unavailable")

    async def get_option_chain(self, symbol: str, expiration: dt.date) -> dict:
        raise RuntimeError("direct chain unavailable")


@pytest.mark.asyncio
async def test_agreements_are_counted_and_not_only_failures() -> None:
    """An agreement must be observable; otherwise the ratio has no denominator."""
    before_spot = _comparisons("spot", "agree")
    before_chain = _comparisons("chain", "agree")
    direct = DirectProvider()
    gateway = RecordingGateway(
        spot_result=spot_response(DIRECT_SPOT), chain_result=chain_response()
    )
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    await provider.get_spot_price("$SPX")
    await provider.get_option_chain("SPX", EXPIRATION)
    await provider.wait_for_shadow_reads()

    assert _comparisons("spot", "agree") == before_spot + 1
    assert _comparisons("chain", "agree") == before_chain + 1
    assert provider.recorder.total() == 0


@pytest.mark.asyncio
async def test_a_discrepancy_counts_once_as_a_comparison_and_once_by_code() -> None:
    before_comparisons = _comparisons("spot", "discrepancy")
    before_coded = _discrepancies("spot", "gateway_value_mismatch", "parsing")
    direct = DirectProvider()
    gateway = RecordingGateway(spot_result=spot_response(1.0))
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    await provider.wait_for_shadow_reads()

    assert _comparisons("spot", "discrepancy") == before_comparisons + 1
    assert _discrepancies("spot", "gateway_value_mismatch", "parsing") == before_coded + 1


@pytest.mark.asyncio
async def test_a_gateway_error_is_counted_under_its_own_code() -> None:
    before = _discrepancies("chain", "gateway_timeout", "timing")
    direct = DirectProvider()
    gateway = RecordingGateway(chain_result=GatewayTimeoutError("slow"))
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    assert await provider.get_option_chain("SPX", EXPIRATION) is CHAIN_PAYLOAD
    await provider.wait_for_shadow_reads()

    assert _discrepancies("chain", "gateway_timeout", "timing") == before + 1


@pytest.mark.asyncio
async def test_a_failing_direct_read_is_counted_separately_from_a_discrepancy() -> None:
    """A comparison that could not run is not evidence against the gateway."""
    before_unavailable = _comparisons("spot", "direct_unavailable")
    before_discrepancy = _comparisons("spot", "discrepancy")
    direct = FailingDirectProvider()
    gateway = RecordingGateway(spot_result=spot_response(DIRECT_SPOT))
    provider = ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)

    with pytest.raises(RuntimeError):
        await provider.get_spot_price("$SPX")
    await provider.wait_for_shadow_reads()

    assert _comparisons("spot", "direct_unavailable") == before_unavailable + 1
    assert _comparisons("spot", "discrepancy") == before_discrepancy
    assert provider.recorder.total() == 0


@pytest.mark.asyncio
async def test_a_disabled_shadow_records_no_metrics_at_all() -> None:
    """The default flag must leave the counters untouched, not merely unlogged."""
    before = {
        result: _comparisons("spot", result)
        for result in ("agree", "discrepancy", "direct_unavailable")
    }
    direct = DirectProvider()
    provider = ShadowComparingMarketDataProvider(direct, RecordingGateway())

    assert await provider.get_spot_price("$SPX") == DIRECT_SPOT
    await provider.wait_for_shadow_reads()

    assert {
        result: _comparisons("spot", result) for result in before
    } == before


def test_discrepancy_metric_labels_cover_every_declared_code() -> None:
    """Every code the module can emit is a legal label set, with no payload fields."""
    for code, classification in CLASSIFICATION_BY_CODE.items():
        assert classification in SHADOW_CLASSIFICATIONS
        for operation in ("spot", "chain"):
            gateway_shadow_discrepancies.labels(
                operation=operation, code=code, classification=classification
            )
    assert set(gateway_shadow_discrepancies._labelnames) == {
        "operation",
        "code",
        "classification",
    }
