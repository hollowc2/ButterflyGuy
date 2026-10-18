"""Exact native-body preservation and optional SDK client injection, all synthetic."""

import copy
import datetime as dt
import json
from unittest.mock import AsyncMock

import httpx
import pytest
from schwab_gateway_sdk.client import GatewayMarketDataClient, GatewayResponseError

from butterfly_guy.research.ndx_evidence import read_json
from butterfly_guy.research.ndx_native_response import (
    MAX_NATIVE_BODY_BYTES,
    NativeCapture,
    preserve_buffered_response,
    validate_capture,
)
from butterfly_guy.research.ndx_postgres_recording import PublishResult, ResearchGatewayHTTPClient
from butterfly_guy.research.ndx_provenance import ROOT
from butterfly_guy.research.ndx_recording import encode, sha

PACKAGE = ROOT / "docs/research/ndx-strategy/postgres-v1"
BODY = (PACKAGE / "native-synthetic.json").read_bytes()
UNIVERSE = read_json(PACKAGE / "universe.json")


def context():
    return dict(snapshot_id="synthetic-snapshot", record_id="synthetic-record",
                request_id="synthetic-request", pass_id="synthetic-pass",
                acquisition_id="synthetic",
                expected_symbols=UNIVERSE["symbols"], session=UNIVERSE["session"],
                evidence_kind="synthetic")


def response(body=BODY, path="/v1/option-chain", status=200):
    return httpx.Response(status, content=body,
                          request=httpx.Request("GET", "https://synthetic.invalid" + path))


def capture():
    return preserve_buffered_response(response(), **context())


def test_exact_body_and_missing_fields_remain_separate():
    saved = capture()
    assert saved.body == BODY and b"10.1000" in saved.body
    doc = validate_capture(saved)
    assert doc["selected"][0]["mark"] == "10.1000"
    assert doc["selected"][0]["multiplier"] is None  # No implicit 100.
    assert doc["selected"][0]["bid_size"] == 0
    assert doc["selected"][0]["flags"] is None  # Chain flags do not label the leg.
    assert doc["selected"][0]["age_seconds"] == "0.0000"
    assert doc["age_reference"] is None
    assert not doc["provider_original_body"] and not doc["replay_eligible"]


@pytest.mark.parametrize("path,status", [("/v1/orders", 200), ("/v1/option-chain", 401)])
def test_non_market_or_error_bodies_never_preserved(path, status):
    with pytest.raises(ValueError, match="successful native option-chain"):
        preserve_buffered_response(response(b"private error", path, status), **context())


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(accountNumber="sensitive"),
    lambda r: r["option_chain"]["contracts"][0].update(authorization="sensitive"),
    lambda r: r["option_chain"].update(expiration="2030-01-03"),
    lambda r: r["option_chain"]["contracts"][0].update(symbol="NDXP  300102P29999000"),
    lambda r: r["option_chain"]["contracts"][0].update(bid=float('nan')),
])
def test_extra_sensitive_fields_identity_and_nonfinite_refuse(mutation):
    raw = json.loads(BODY)
    mutation(raw)
    with pytest.raises(ValueError):
        preserve_buffered_response(response(json.dumps(raw).encode()), **context())


def test_duplicate_keys_budget_and_unbuffered_stream_refuse():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        preserve_buffered_response(response(b'{"schema_version":"1.0","schema_version":"2"}'),
                                   **context())
    with pytest.raises(ValueError, match="16 MiB"):
        preserve_buffered_response(response(b"x" * (MAX_NATIVE_BODY_BYTES + 1)), **context())
    request = httpx.Request("GET", "https://synthetic.invalid/v1/option-chain")
    unbuffered = httpx.Response(200, stream=httpx.ByteStream(BODY), request=request)
    with pytest.raises(ValueError, match="must not consume"):
        preserve_buffered_response(unbuffered, **context())
    assert not unbuffered.is_stream_consumed


def test_capture_derivative_tampering_refuses():
    original = capture()
    doc = copy.deepcopy(original.document)
    doc["selected"][0]["mark"] = "0"
    with pytest.raises(ValueError, match="body/derivative mismatch"):
        validate_capture(NativeCapture(BODY, encode(doc)))
    with pytest.raises(ValueError, match="scope/hash mismatch"):
        validate_capture(NativeCapture(BODY + b" ", original.document_json))


@pytest.mark.asyncio
async def test_sdk_injection_has_one_request_and_preserves_original_bytes():
    requested, captured = [], []
    async def handle(request):
        requested.append(request.url.path)
        return httpx.Response(200, content=BODY)
    async def publish(saved):
        captured.append(saved)
        return PublishResult(True, True, sha(saved.body), None)
    recorder = AsyncMock()
    recorder.publish.side_effect = publish
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(handle), recorder=recorder,
            context_factory=context) as client:
        sdk = GatewayMarketDataClient(
            "https://synthetic.invalid", "synthetic-test-key", client=client)
        result = await sdk.get_option_chain("$NDX", dt.date(2030, 1, 2))
        assert result.option_chain.contracts[0].mark == 10.1
        assert captured[0].body == BODY
        assert captured[0].document["request_start"] is not None
        assert client.recording_failures == 0
    assert requested == ["/v1/option-chain"]


@pytest.mark.asyncio
async def test_recording_failure_leaves_sdk_response_and_counts_drop():
    recorder = AsyncMock()
    recorder.publish.side_effect = RuntimeError("do not retain this context")
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=BODY)),
            recorder=recorder, context_factory=context) as client:
        sdk = GatewayMarketDataClient(
            "https://synthetic.invalid", "synthetic-test-key", client=client)
        result = await sdk.get_option_chain("$NDX", dt.date(2030, 1, 2))
        assert result.option_chain.put_contract_count == 3
        assert client.recording_failures == 1
        assert client.last_recording_result.failure == "observer_recording_failed"


@pytest.mark.asyncio
async def test_disabled_client_and_invalid_native_response_use_sdk_validation():
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=BODY))) as client:
        sdk = GatewayMarketDataClient(
            "https://synthetic.invalid", "synthetic-test-key", client=client)
        await sdk.get_option_chain("$NDX", dt.date(2030, 1, 2))
        assert client.last_recording_result is None and client.recording_failures == 0
    async with ResearchGatewayHTTPClient(base_url="https://synthetic.invalid",
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json={"account":"private"})),
            recorder=AsyncMock(), context_factory=context) as client:
        sdk = GatewayMarketDataClient(
            "https://synthetic.invalid", "synthetic-test-key", client=client)
        with pytest.raises(GatewayResponseError):
            await sdk.get_option_chain("$NDX", dt.date(2030, 1, 2))
        assert client.recording_failures == 1
