from __future__ import annotations

import pytest

from tools.schwab_gateway_v046_readiness_soak import preopen_endpoint_violations


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
