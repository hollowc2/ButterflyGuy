from __future__ import annotations

import httpx
import pytest

from tools import schwab_gateway_v046_readiness_soak as soak
from tools.schwab_gateway_v046_readiness_soak import (
    http_json,
    preopen_endpoint_violations,
)


def _endpoints(*, status: int, reason: str) -> dict:
    return {
        "butterfly_spx_app": {
            "/ready": {"status": status, "body": {"reason": reason}}
        }
    }


def test_preopen_allows_documented_after_hours_strategy_readiness() -> None:
    violations = ["butterfly_spx_app:ready_non_200"]

    assert (
        preopen_endpoint_violations(
            _endpoints(
                status=503,
                reason="gateway_market_data_unavailable",
            ),
            violations,
        )
        == []
    )


def test_preopen_accepts_retried_market_data_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            503,
            json={
                "status": "not_ready",
                "reason": "gateway_market_data_unavailable",
                "sensitive_detail": "must-not-be-recorded",
            },
        )

    monkeypatch.setattr(soak.time, "sleep", lambda _seconds: None)
    with httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    ) as client:
        ready = http_json(client, "/ready")

    assert attempts == 3
    assert ready["status"] == 503
    assert ready["body"] == {
        "status": "not_ready",
        "reason": "gateway_market_data_unavailable",
    }
    endpoints = {"butterfly_spx_app": {"/ready": ready}}
    violations = ["butterfly_spx_app:ready_non_200"]

    assert preopen_endpoint_violations(endpoints, violations) == []


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (500, "gateway_market_data_unavailable"),
        (503, "gateway_market_data_warming"),
        (503, "unexpected_failure"),
    ],
)
def test_preopen_rejects_every_other_readiness_failure(
    status: int, reason: str
) -> None:
    violation = "butterfly_spx_app:ready_non_200"

    assert preopen_endpoint_violations(
        _endpoints(status=status, reason=reason), [violation]
    ) == [violation]


def test_preopen_never_suppresses_other_endpoint_failures() -> None:
    violation = "butterfly_spx_app:health_non_200"

    assert preopen_endpoint_violations(
        _endpoints(status=503, reason="gateway_market_data_unavailable"),
        [violation],
    ) == [violation]
