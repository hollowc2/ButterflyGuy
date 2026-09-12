#!/usr/bin/env python3
"""Check ButterflyGuy PAPER gateway readiness without validating gateway wire contracts."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from typing import Any

import httpx

STRATEGIES = {
    "SPX": ("butterfly_spx_app", 8000),
    "NDX": ("butterfly_ndx_app", 8001),
    "XSP": ("butterfly_xsp_app", 8003),
}
EXPECTED_ENV = {
    "EXECUTION__PAPER_TRADING": "true",
    "EXECUTION__ALLOW_LIVE_TRADING": "false",
    "ALLOW_LIVE_TRADING": "false",
    "SCHWAB_ACCESS_MODE": "gateway",
    "SCHWAB_GATEWAY_SHADOW_READS": "false",
}


def _run_read_only(args: list[str]) -> str:
    return subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=30
    ).stdout


def strategy_identity(container: str) -> dict[str, Any]:
    """Return only non-secret identity and safety fields from Docker inspection."""

    raw = json.loads(_run_read_only(["docker", "inspect", container]))[0]
    state = raw["State"]
    environment = {}
    for entry in raw["Config"].get("Env") or []:
        name, separator, value = entry.partition("=")
        if separator and name in EXPECTED_ENV:
            environment[name] = value
    return {
        "container": container,
        "container_id": raw["Id"],
        "image_id": raw["Image"],
        "status": state["Status"],
        "health": (state.get("Health") or {}).get("Status", "none"),
        "restart_count": raw["RestartCount"],
        "environment": environment,
    }


def identity_violations(identity: dict[str, Any]) -> list[str]:
    violations = []
    if identity["status"] != "running":
        violations.append(f"{identity['container']}:not_running")
    if identity["health"] not in {"healthy", "none"}:
        violations.append(f"{identity['container']}:unhealthy")
    for name, expected in EXPECTED_ENV.items():
        if identity["environment"].get(name) != expected:
            violations.append(f"{identity['container']}:{name.lower()}_mismatch")
    return violations


def http_json(client: httpx.Client, path: str) -> dict[str, Any]:
    """Read a local readiness endpoint and retain only its public state fields."""

    response: httpx.Response | None = None
    for attempt in range(3):
        response = client.get(path)
        if response.status_code < 500:
            break
        if attempt < 2:
            time.sleep(0.5)
    assert response is not None
    try:
        body = response.json()
    except ValueError:
        body = {}
    safe_body = {
        key: body[key]
        for key in ("status", "reason")
        if isinstance(body, dict) and key in body
    }
    return {"status": response.status_code, "body": safe_body}


def endpoint_violations(container: str, endpoints: dict[str, Any]) -> list[str]:
    violations = []
    for endpoint in ("/health", "/ready"):
        if endpoints[endpoint]["status"] != 200:
            violations.append(f"{container}:{endpoint.removeprefix('/')}_non_200")
    return violations


def preopen_endpoint_violations(
    endpoints: dict[str, dict[str, Any]], violations: list[str]
) -> list[str]:
    """Allow only the documented after-hours unavailable readiness state."""

    allowed = {
        f"{container}:ready_non_200"
        for container, snapshot in endpoints.items()
        if snapshot.get("/ready", {}).get("status") == 503
        and snapshot["/ready"].get("body", {}).get("reason")
        == "gateway_market_data_unavailable"
    }
    return [violation for violation in violations if violation not in allowed]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preopen",
        action="store_true",
        help="allow the documented after-hours gateway-unavailable readiness state",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    identities: dict[str, Any] = {}
    endpoints: dict[str, Any] = {}
    violations: list[str] = []
    for _symbol, (container, port) in STRATEGIES.items():
        identity = strategy_identity(container)
        identities[container] = identity
        violations.extend(identity_violations(identity))
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:
            snapshot = {
                endpoint: http_json(client, endpoint)
                for endpoint in ("/health", "/ready")
            }
        endpoints[container] = snapshot
        violations.extend(endpoint_violations(container, snapshot))
    if args.preopen:
        violations = preopen_endpoint_violations(endpoints, violations)
    print(
        json.dumps(
            {
                "scope": "butterflyguy_consumer_readiness",
                "identities": identities,
                "endpoints": endpoints,
                "violations": sorted(violations),
                "passed": not violations,
            },
            sort_keys=True,
        )
    )
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
