from __future__ import annotations

import copy
import datetime as dt

import httpx
import pytest

from tools.schwab_gateway_session_soak import (
    _request_with_retry,
    assert_production_identity,
    cache_consistency_result,
    canonical_market_data,
    health_violations,
    partition_opening_warmup_violations,
    validate_chain,
    validate_history,
    validate_spot,
)

SESSION_DATE = dt.date(2026, 8, 31)


def _contract(option_type: str, symbol: str, strike: float) -> dict:
    return {
        "symbol": symbol,
        "option_type": option_type,
        "expiration": SESSION_DATE.isoformat(),
        "strike": strike,
        "bid": 1.0,
        "ask": 1.2,
        "mark": 1.1,
        "bid_size": 2,
        "ask_size": 3,
        "total_volume": 4,
        "open_interest": 5,
        "event_timestamp": "2026-08-31T13:31:00Z",
        "stale": False,
        "data_quality_flags": [],
    }


def _chain(*contracts: dict, flags: list[str] | None = None) -> dict:
    calls = sum(contract["option_type"] == "CALL" for contract in contracts)
    puts = sum(contract["option_type"] == "PUT" for contract in contracts)
    return {
        "option_chain": {
            "symbol": "$NDX",
            "expiration": SESSION_DATE.isoformat(),
            "underlying_price": 6450.5,
            "call_contract_count": calls,
            "put_contract_count": puts,
            "strike_count": len({contract["strike"] for contract in contracts}),
            "contracts": list(contracts),
            "event_timestamp": "2026-08-31T13:31:00Z",
            "gateway_received_at": "2026-08-31T13:31:01Z",
            "stale": False,
            "age_seconds": 1.0,
            "data_quality_flags": flags or [],
        }
    }


def test_validate_spot_requires_fresh_positive_matching_observation() -> None:
    body = {
        "spot": {
            "symbol": "$SPX",
            "price": 6500.0,
            "event_timestamp": "2026-08-31T13:31:00Z",
            "gateway_received_at": "2026-08-31T13:31:01Z",
            "stale": False,
            "age_seconds": 1.0,
            "data_quality_flags": [],
        }
    }

    assert validate_spot(body, "$SPX")["errors"] == []
    body["spot"]["age_seconds"] = 31.0
    assert validate_spot(body, "$SPX")["errors"] == ["too_old_for_consumer"]


def test_validate_chain_accepts_audible_crossed_market_normalization() -> None:
    call = _contract("CALL", "NDX CALL", 6450.0)
    call["data_quality_flags"] = ["crossed_market_normalized"]
    body = _chain(
        call,
        _contract("PUT", "NDX PUT", 6450.0),
        flags=["crossed_markets_normalized"],
    )

    result = validate_chain(body, "$NDX", SESSION_DATE)

    assert result["errors"] == []
    assert result["normalized_crosses"] == 1
    assert (result["calls"], result["puts"], result["contracts"]) == (1, 1, 2)


def test_validate_chain_rejects_silent_or_invalid_normalization() -> None:
    call = _contract("CALL", "NDX CALL", 6450.0)
    call["bid"] = 126.2
    call["ask"] = 126.0
    call["mark"] = 126.1
    call["data_quality_flags"] = ["crossed_market_normalized"]
    body = _chain(call, _contract("PUT", "NDX PUT", 6450.0))

    errors = validate_chain(body, "$NDX", SESSION_DATE)["errors"]

    assert "invalid_bid_ask_mark" in errors
    assert "normalization_not_audible_at_chain_level" in errors


def test_validate_history_accepts_bounded_empty_extended_contract() -> None:
    body = {
        "session_history": {
            "symbol": "$XSP",
            "date": SESSION_DATE.isoformat(),
            "session": "extended",
            "candles": [],
            "event_timestamp": None,
            "gateway_received_at": "2026-08-31T20:10:00Z",
            "stale": True,
            "age_seconds": None,
            "data_quality_flags": ["no_bars_returned", "stale"],
        }
    }

    result = validate_history(
        body,
        "$XSP",
        surface="session_history",
        allow_empty_extended=True,
    )

    assert result["errors"] == []
    assert result["bar_count"] == 0


def test_canonical_market_data_removes_only_reevaluated_envelope_fields() -> None:
    left = {
        "option_chain": {
            "age_seconds": 1.0,
            "gateway_received_at": "first",
            "stale": False,
            "data_quality_flags": ["crossed_markets_normalized"],
            "contracts": [
                {
                    "symbol": "A",
                    "age_seconds": 0.5,
                    "stale": False,
                    "data_quality_flags": ["crossed_market_normalized"],
                    "bid": 1.0,
                }
            ],
        }
    }
    right = {
        "option_chain": {
            "age_seconds": 1.2,
            "gateway_received_at": "second",
            "stale": True,
            "data_quality_flags": [
                "crossed_markets_normalized",
                "stale_contracts_present",
                "stale",
            ],
            "contracts": [
                {
                    "symbol": "A",
                    "age_seconds": 0.7,
                    "stale": True,
                    "data_quality_flags": ["crossed_market_normalized", "stale"],
                    "bid": 1.0,
                }
            ],
        }
    }

    assert canonical_market_data(left) == canonical_market_data(right)
    right["option_chain"]["contracts"][0]["bid"] = 1.1
    assert canonical_market_data(left) != canonical_market_data(right)


def test_cache_consistency_records_ignored_freshness_paths() -> None:
    first = {
        "option_chain": {
            "event_timestamp": "2026-09-02T16:13:30Z",
            "age_seconds": 89.5,
            "stale": False,
            "data_quality_flags": [],
            "contracts": [
                {
                    "symbol": "SPXW A",
                    "event_timestamp": "2026-09-02T16:13:30Z",
                    "age_seconds": 89.5,
                    "stale": False,
                    "data_quality_flags": [],
                    "bid": 1.0,
                }
            ],
        }
    }
    cached = {
        "option_chain": {
            "event_timestamp": "2026-09-02T16:13:30Z",
            "age_seconds": 91.5,
            "stale": False,
            "data_quality_flags": ["stale_contracts_present"],
            "contracts": [
                {
                    "symbol": "SPXW A",
                    "event_timestamp": "2026-09-02T16:13:30Z",
                    "age_seconds": 91.5,
                    "stale": True,
                    "data_quality_flags": ["stale"],
                    "bid": 1.0,
                }
            ],
        }
    }

    result = cache_consistency_result(first, cached)

    assert result == {
        "evaluated": True,
        "semantic_equal": True,
        "ignored_freshness_difference_count": 5,
        "ignored_freshness_difference_paths": [
            "$.option_chain.age_seconds",
            "$.option_chain.contracts[0].age_seconds",
            "$.option_chain.contracts[0].data_quality_flags",
            "$.option_chain.contracts[0].stale",
            "$.option_chain.data_quality_flags",
        ],
    }


def test_cache_consistency_keeps_market_and_nonfreshness_quality_changes_gating() -> None:
    first = {
        "option_chain": {
            "event_timestamp": "2026-09-02T16:13:30Z",
            "contracts": [
                {
                    "symbol": "SPXW A",
                    "bid": 1.0,
                    "data_quality_flags": [],
                }
            ],
        }
    }
    cached = {
        "option_chain": {
            "event_timestamp": "2026-09-02T16:13:31Z",
            "contracts": [
                {
                    "symbol": "SPXW A",
                    "bid": 1.1,
                    "data_quality_flags": ["crossed_market_normalized"],
                }
            ],
        }
    }

    result = cache_consistency_result(first, cached)

    assert result["semantic_equal"] is False
    assert result["ignored_freshness_difference_count"] == 0


def test_cache_canonicalization_does_not_weaken_independent_freshness_gate() -> None:
    first = _chain(
        _contract("CALL", "NDX CALL", 6450.0),
        _contract("PUT", "NDX PUT", 6450.0),
    )
    cached = copy.deepcopy(first)
    chain = cached["option_chain"]
    chain["age_seconds"] = 31.0
    chain["stale"] = True
    chain["data_quality_flags"] = ["stale"]
    for contract in chain["contracts"]:
        contract["stale"] = True
        contract["data_quality_flags"] = ["stale"]

    assert cache_consistency_result(first, cached)["semantic_equal"] is True
    assert validate_chain(cached, "$NDX", SESSION_DATE)["errors"] == [
        "aggregate_stale",
        "too_old_for_consumer",
    ]


def test_production_identity_assertion_detects_only_frozen_target_drift() -> None:
    expected = {
        "container_id": "container",
        "image_id": "image",
        "revision": "revision",
        "started_at": "started",
    }
    observed = {
        **expected,
        "restart_count": 0,
        "status": "running",
        "health": "healthy",
        "gateway_processes": 1,
    }

    assert assert_production_identity(observed, expected) == []
    observed["image_id"] = "changed"
    assert assert_production_identity(observed, expected) == [
        "production_image_id_changed"
    ]


def test_health_violations_requires_ready_token_without_exposing_details() -> None:
    healthy = {
        "health": {"status": 200, "body": {"status": "healthy"}},
        "ready": {"status": 200, "body": {"token_state": "ready"}},
    }
    assert health_violations(healthy, prefix="baseline") == []

    unhealthy = {
        "health": {"status": 503, "body": {"status": "unhealthy"}},
        "ready": {"status": 503, "body": {"token_state": "expired"}},
    }
    assert health_violations(unhealthy, prefix="final") == [
        "final_health_non_200",
        "final_ready_non_200",
        "final_token_not_ready",
    ]


@pytest.mark.asyncio
async def test_request_retry_recovers_timeout_and_preserves_both_attempts(
    tmp_path,
) -> None:
    responses = iter(
        [
            httpx.Response(504, json={"detail": "upstream timeout"}),
            httpx.Response(200, json={"spot": {"symbol": "$SPX"}}),
        ]
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://gateway", transport=transport
    ) as client:
        result = await _request_with_retry(
            client,
            tmp_path,
            "spot_spx",
            "/v1/spot",
            {"symbol": "$SPX"},
            retry_backoff_seconds=0,
        )

    assert result["name"] == "spot_spx"
    assert result["status"] == 200
    assert result["recovered_transient"] is True
    assert [attempt["status"] for attempt in result["attempts"]] == [504, 200]
    assert (tmp_path / "spot_spx.json").exists()
    assert (tmp_path / "spot_spx_retry_2.json").exists()


@pytest.mark.asyncio
async def test_request_retry_does_not_retry_authorization_failure(tmp_path) -> None:
    request_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(403, json={"detail": "forbidden"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://gateway", transport=transport
    ) as client:
        result = await _request_with_retry(
            client,
            tmp_path,
            "spot_spx",
            "/v1/spot",
            {"symbol": "$SPX"},
            retry_backoff_seconds=0,
        )

    assert request_count == 1
    assert result["classification"] == "authentication_or_authorization_failure"
    assert result["recovered_transient"] is False
    assert len(result["attempts"]) == 1


def test_cache_consistency_requires_two_successful_bodies() -> None:
    missing = cache_consistency_result(None, {"option_chain": {"contracts": []}})
    assert missing == {
        "evaluated": False,
        "semantic_equal": None,
        "reason": "missing_successful_pair",
        "ignored_freshness_difference_count": 0,
        "ignored_freshness_difference_paths": [],
    }

    left = {
        "option_chain": {
            "contracts": [{"symbol": "A", "bid": 1.0, "age_seconds": 1.0}],
            "gateway_received_at": "first",
        }
    }
    right = {
        "option_chain": {
            "contracts": [{"symbol": "A", "bid": 1.0, "age_seconds": 1.2}],
            "gateway_received_at": "second",
        }
    }
    assert cache_consistency_result(left, right) == {
        "evaluated": True,
        "semantic_equal": True,
        "ignored_freshness_difference_count": 2,
        "ignored_freshness_difference_paths": [
            "$.option_chain.contracts[0].age_seconds",
            "$.option_chain.gateway_received_at",
        ],
    }


def test_opening_warmup_keeps_data_age_observable_but_not_gating() -> None:
    violations = [
        "spot_spx:stale",
        "chain_ndx_first:aggregate_stale",
        "session_ndx_regular:no_bars",
        "chain_xsp_first_non_200_or_invalid_json",
        "cache_semantic_mismatch:$XSP",
    ]

    gating, observations = partition_opening_warmup_violations(
        violations,
        checkpoint_index=0,
        warmup_checkpoints=1,
    )

    assert observations == [
        "chain_ndx_first:aggregate_stale",
        "session_ndx_regular:no_bars",
        "spot_spx:stale",
    ]
    assert gating == [
        "cache_semantic_mismatch:$XSP",
        "chain_xsp_first_non_200_or_invalid_json",
    ]


def test_opening_warmup_does_not_weaken_later_checkpoints() -> None:
    violations = ["spot_spx:stale", "session_ndx_regular:no_bars"]

    gating, observations = partition_opening_warmup_violations(
        violations,
        checkpoint_index=1,
        warmup_checkpoints=1,
    )

    assert gating == sorted(violations)
    assert observations == []
