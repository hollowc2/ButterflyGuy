#!/usr/bin/env python3
"""Read-only full-session acceptance harness for the production SchwabGateway.

The harness deliberately owns no Docker lifecycle, broker account, token, database
write, or order capability.  It records the exact production container as an
invariant while treating candidate-gateway and AfterHours containers as mutable
background context.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import stat
import subprocess
import time
from collections import Counter
from typing import Any
from zoneinfo import ZoneInfo

import httpx

EASTERN = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SYMBOLS = ("$SPX", "$NDX", "$XSP")
SPOT_SYMBOLS = (*SYMBOLS, "$VIX")
MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS = 180.0
REQUEST_MAX_ATTEMPTS = 2
REQUEST_RETRY_BACKOFF_SECONDS = 0.25
CONTAINER_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
METRIC_RE = re.compile(
    r"^(gateway_(?:admission_total|client_request_latency_seconds(?:_bucket|_count|_sum)?|"
    r"client_requests_total|option_chain_cache_(?:age_seconds|bytes|entries|events_total)|"
    r"option_chain_inflight|"
    r"option_chain_(?:crossed_market|negative_time_value)_normalizations_total)|"
    r"schwab_gateway_token_(?:refresh_total|state))(?=[{ ]|$)"
)
ALLOWED_GATEWAY_LOG_FIELDS = {
    "timestamp",
    "caller",
    "operation",
    "status",
    "latency_ms",
    "event",
    "level",
    "state",
    "previous_state",
    "reason",
    "result",
}
RETRYABLE_REQUEST_CLASSIFICATIONS = frozenset(
    {
        "likely_three_second_upstream_timeout",
        "admission_rejection",
        "gateway_or_upstream_server_error",
        "client_or_transport_error",
    }
)
OPENING_WARMUP_SURFACES = ("spot_", "chain_", "history_", "session_")
OPENING_WARMUP_ERRORS = frozenset(
    {
        "aggregate_stale",
        "invalid_age",
        "no_bars",
        "stale",
        "too_old_for_consumer",
    }
)
REEVALUATED_FRESHNESS_FIELDS = frozenset(
    {"age_seconds", "gateway_received_at", "stale"}
)
REEVALUATED_FRESHNESS_FLAGS = frozenset({"stale", "stale_contracts_present"})


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_new(path: pathlib.Path, payload: bytes) -> str:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return _sha256(path)


def _write_json_new(path: pathlib.Path, value: Any) -> str:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    return _write_new(path, payload)


def _write_manifest(path: pathlib.Path, value: Any) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    temp = path.with_suffix(".tmp")
    with temp.open("wb") as handle:
        handle.write(payload)
    os.chmod(temp, stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temp, path)


def _run_read_only(args: list[str], *, timeout: float = 30.0) -> str:
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def _read_scoped_key(path: pathlib.Path) -> str:
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "SCHWAB_GATEWAY_API_KEY":
            return value.strip().strip('"').strip("'")
    raise RuntimeError("scoped gateway API key is unavailable")


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _same_symbol(left: Any, right: str) -> bool:
    return str(left or "").strip().upper().lstrip("$") == right.upper().lstrip("$")


def validate_spot(body: dict[str, Any], symbol: str) -> dict[str, Any]:
    spot = body.get("spot")
    errors: list[str] = []
    if not isinstance(spot, dict):
        return {"symbol": symbol, "errors": ["missing_spot_contract"]}
    if not _same_symbol(spot.get("symbol"), symbol):
        errors.append("symbol_mismatch")
    if not _finite(spot.get("price")) or spot["price"] <= 0:
        errors.append("invalid_price")
    if spot.get("stale"):
        errors.append("stale")
    if spot.get("event_timestamp") is None:
        errors.append("missing_event_timestamp")
    age = spot.get("age_seconds")
    if not _finite(age) or age < 0:
        errors.append("invalid_age")
    elif age > 30:
        errors.append("too_old_for_consumer")
    return {
        "symbol": symbol,
        "age_seconds": age,
        "event_timestamp": spot.get("event_timestamp"),
        "gateway_received_at": spot.get("gateway_received_at"),
        "stale": spot.get("stale"),
        "quality_flags": spot.get("data_quality_flags", []),
        "errors": errors,
    }


def validate_chain(
    body: dict[str, Any], symbol: str, expiration: dt.date
) -> dict[str, Any]:
    chain = body.get("option_chain")
    if not isinstance(chain, dict):
        return {"symbol": symbol, "errors": ["missing_option_chain_contract"]}
    contracts = chain.get("contracts")
    if not isinstance(contracts, list):
        return {"symbol": symbol, "errors": ["contracts_not_a_list"]}

    errors: list[str] = []
    counts: Counter[str] = Counter()
    flags: Counter[str] = Counter()
    seen_symbols: set[str] = set()
    strikes: set[float] = set()
    strike_order: dict[str, list[float]] = {"CALL": [], "PUT": []}
    invalid_markets = 0
    invalid_marks = 0
    invalid_sizes = 0
    wrong_expirations = 0
    duplicate_symbols = 0
    normalized_crosses = 0
    stale_contracts = 0
    missing_event_timestamps = 0

    for contract in contracts:
        if not isinstance(contract, dict):
            errors.append("contract_not_an_object")
            continue
        option_type = str(contract.get("option_type", "")).upper()
        if option_type not in strike_order:
            errors.append("invalid_option_type")
            continue
        counts[option_type] += 1
        contract_symbol = str(contract.get("symbol") or "")
        if not contract_symbol or contract_symbol in seen_symbols:
            duplicate_symbols += 1
        seen_symbols.add(contract_symbol)
        if contract.get("expiration") != expiration.isoformat():
            wrong_expirations += 1
        strike = contract.get("strike")
        if not _finite(strike) or strike <= 0:
            errors.append("invalid_strike")
        else:
            strike_value = float(strike)
            strikes.add(strike_value)
            strike_order[option_type].append(strike_value)

        bid, ask, mark = contract.get("bid"), contract.get("ask"), contract.get("mark")
        if not all(_finite(value) and value >= 0 for value in (bid, ask, mark)):
            invalid_markets += 1
        elif bid > ask:
            invalid_markets += 1
        elif mark < bid or mark > ask:
            invalid_marks += 1

        for field in ("bid_size", "ask_size", "total_volume", "open_interest"):
            value = contract.get(field)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                invalid_sizes += 1

        contract_flags = contract.get("data_quality_flags", [])
        if not isinstance(contract_flags, list):
            errors.append("contract_flags_not_a_list")
            contract_flags = []
        flags.update(str(item) for item in contract_flags)
        if "crossed_market_normalized" in contract_flags:
            normalized_crosses += 1
        if contract.get("stale"):
            stale_contracts += 1
        if contract.get("event_timestamp") is None:
            missing_event_timestamps += 1

    declared = {
        "CALL": chain.get("call_contract_count"),
        "PUT": chain.get("put_contract_count"),
    }
    actual = {"CALL": counts["CALL"], "PUT": counts["PUT"]}
    if not _same_symbol(chain.get("symbol"), symbol):
        errors.append("symbol_mismatch")
    if chain.get("expiration") != expiration.isoformat():
        errors.append("chain_expiration_mismatch")
    if chain.get("stale"):
        errors.append("aggregate_stale")
    if chain.get("event_timestamp") is None:
        errors.append("missing_chain_event_timestamp")
    underlying_price = chain.get("underlying_price")
    if not _finite(underlying_price) or underlying_price <= 0:
        errors.append("invalid_underlying_price")
    age = chain.get("age_seconds")
    if not _finite(age) or age < 0:
        errors.append("invalid_age")
    elif age > 30:
        errors.append("too_old_for_consumer")
    if actual != declared:
        errors.append("declared_contract_count_mismatch")
    if not actual["CALL"] or not actual["PUT"]:
        errors.append("missing_chain_side")
    if len(strikes) != chain.get("strike_count"):
        errors.append("declared_strike_count_mismatch")
    if any(values != sorted(values) for values in strike_order.values()):
        errors.append("strike_ordering_invalid")
    if duplicate_symbols:
        errors.append("duplicate_or_missing_symbols")
    if wrong_expirations:
        errors.append("contract_expiration_mismatch")
    if invalid_markets:
        errors.append("invalid_bid_ask_mark")
    if invalid_marks:
        errors.append("mark_outside_market")
    if invalid_sizes:
        errors.append("invalid_size_volume_interest")

    chain_flags = [str(item) for item in chain.get("data_quality_flags", [])]
    if normalized_crosses and "crossed_markets_normalized" not in chain_flags:
        errors.append("normalization_not_audible_at_chain_level")
    if "crossed_markets_normalized" in chain_flags and not normalized_crosses:
        errors.append("normalization_flag_without_contract")

    return {
        "symbol": symbol,
        "age_seconds": age,
        "event_timestamp": chain.get("event_timestamp"),
        "gateway_received_at": chain.get("gateway_received_at"),
        "stale": chain.get("stale"),
        "chain_quality_flags": chain_flags,
        "underlying_price": underlying_price,
        "contracts": len(contracts),
        "calls": actual["CALL"],
        "puts": actual["PUT"],
        "unique_symbols": len(seen_symbols),
        "unique_strikes": len(strikes),
        "normalized_crosses": normalized_crosses,
        "stale_contracts": stale_contracts,
        "missing_event_timestamps": missing_event_timestamps,
        "contract_quality_flags": dict(sorted(flags.items())),
        "invalid_markets": invalid_markets,
        "invalid_marks": invalid_marks,
        "invalid_sizes": invalid_sizes,
        "wrong_expirations": wrong_expirations,
        "duplicate_symbols": duplicate_symbols,
        "errors": sorted(set(errors)),
    }


def validate_history(
    body: dict[str, Any],
    symbol: str,
    *,
    surface: str,
    allow_empty_extended: bool = False,
    session_date: dt.date | None = None,
    expected_session: str | None = None,
) -> dict[str, Any]:
    observation = body.get(surface)
    if not isinstance(observation, dict):
        return {"symbol": symbol, "surface": surface, "errors": ["missing_history"]}
    bars = observation.get("bars", observation.get("candles"))
    if not isinstance(bars, list):
        return {"symbol": symbol, "surface": surface, "errors": ["bars_not_a_list"]}
    errors: list[str] = []
    timestamps: list[str] = []
    invalid_ohlc = 0
    for bar in bars:
        if not isinstance(bar, dict):
            invalid_ohlc += 1
            continue
        timestamp = bar.get("timestamp")
        if timestamp is None:
            invalid_ohlc += 1
        else:
            timestamps.append(str(timestamp))
        open_, high, low, close = (
            bar.get("open"),
            bar.get("high"),
            bar.get("low"),
            bar.get("close"),
        )
        if not all(_finite(value) and value > 0 for value in (open_, high, low, close)):
            invalid_ohlc += 1
        elif low > min(open_, close) or high < max(open_, close) or low > high:
            invalid_ohlc += 1
        volume = bar.get("volume")
        if volume is not None and (not _finite(volume) or volume < 0):
            invalid_ohlc += 1
    if not _same_symbol(observation.get("symbol"), symbol):
        errors.append("symbol_mismatch")
    quality_flags = [str(item) for item in observation.get("data_quality_flags", [])]
    empty_extended = (
        allow_empty_extended
        and observation.get("session") == "extended"
        and not bars
    )
    if empty_extended:
        if "no_bars_returned" not in quality_flags:
            errors.append("empty_extended_missing_no_bars_flag")
        if set(quality_flags) - {"no_bars_returned", "stale"}:
            errors.append("empty_extended_unexpected_quality_flag")
    else:
        if observation.get("stale"):
            errors.append("stale")
        if not bars:
            errors.append("no_bars")
        age = observation.get("age_seconds")
        if not _finite(age) or age < 0:
            errors.append("invalid_age")
        elif age > MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS:
            errors.append("too_old_for_consumer")
    if surface == "history" and observation.get("frequency") != "minute":
        errors.append("frequency_mismatch")
    if surface == "session_history":
        if session_date is not None and observation.get("date") != session_date.isoformat():
            errors.append("date_mismatch")
        if expected_session is not None and observation.get("session") != expected_session:
            errors.append("session_mismatch")
    if timestamps != sorted(timestamps) or len(timestamps) != len(set(timestamps)):
        errors.append("bars_not_strictly_chronological")
    if invalid_ohlc:
        errors.append("invalid_ohlc")
    return {
        "symbol": symbol,
        "surface": surface,
        "session": observation.get("session"),
        "date": observation.get("date"),
        "frequency": observation.get("frequency"),
        "age_seconds": observation.get("age_seconds"),
        "event_timestamp": observation.get("event_timestamp"),
        "gateway_received_at": observation.get("gateway_received_at"),
        "stale": observation.get("stale"),
        "quality_flags": quality_flags,
        "bar_count": len(bars),
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "invalid_ohlc": invalid_ohlc,
        "errors": errors,
    }


def canonical_market_data(value: Any) -> Any:
    """Remove only fields the gateway reevaluates when serving a cached chain.

    Both chain responses are validated independently before this comparison.  This
    canonical form therefore prevents elapsed-time freshness changes from looking like
    market-data mutations without hiding a stale response from the freshness gates.
    """
    if isinstance(value, dict):
        canonical: dict[str, Any] = {}
        for key, item in value.items():
            if key in REEVALUATED_FRESHNESS_FIELDS:
                continue
            if key == "data_quality_flags" and isinstance(item, list):
                canonical[key] = [
                    flag for flag in item if flag not in REEVALUATED_FRESHNESS_FLAGS
                ]
            else:
                canonical[key] = canonical_market_data(item)
        return canonical
    if isinstance(value, list):
        return [canonical_market_data(item) for item in value]
    return value


def ignored_freshness_difference_paths(
    left: Any,
    right: Any,
    *,
    path: str = "$",
) -> list[str]:
    """List differing paths that canonical cache comparison intentionally ignores."""
    differences: list[str] = []
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}"
            left_item = left.get(key)
            right_item = right.get(key)
            if key in REEVALUATED_FRESHNESS_FIELDS:
                if left_item != right_item:
                    differences.append(child_path)
                continue
            if (
                key == "data_quality_flags"
                and isinstance(left_item, list)
                and isinstance(right_item, list)
            ):
                left_canonical = [
                    flag
                    for flag in left_item
                    if flag not in REEVALUATED_FRESHNESS_FLAGS
                ]
                right_canonical = [
                    flag
                    for flag in right_item
                    if flag not in REEVALUATED_FRESHNESS_FLAGS
                ]
                if left_item != right_item and left_canonical == right_canonical:
                    differences.append(child_path)
                continue
            differences.extend(
                ignored_freshness_difference_paths(
                    left_item,
                    right_item,
                    path=child_path,
                )
            )
        return differences
    if isinstance(left, list) and isinstance(right, list):
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=False)):
            differences.extend(
                ignored_freshness_difference_paths(
                    left_item,
                    right_item,
                    path=f"{path}[{index}]",
                )
            )
    return differences


def production_identity(container: str) -> dict[str, Any]:
    if not CONTAINER_NAME_RE.fullmatch(container):
        raise ValueError("invalid container name")
    template = "\t".join(
        (
            "{{.Id}}",
            "{{.Image}}",
            "{{.Created}}",
            "{{.State.StartedAt}}",
            "{{.State.Status}}",
            "{{.RestartCount}}",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}',
            '{{index .Config.Labels "com.docker.compose.project"}}',
            '{{index .Config.Labels "com.docker.compose.service"}}',
        )
    )
    values = _run_read_only(
        ["docker", "inspect", "--format", template, container]
    ).strip().split("\t")
    if len(values) != 9:
        raise RuntimeError("unexpected docker identity response")
    state = json.loads(
        _run_read_only(
            ["docker", "inspect", "--format", "{{json .State}}", container]
        )
    )
    top = _run_read_only(
        ["docker", "top", container, "-eo", "pid,comm,args"]
    ).splitlines()[1:]
    gateway_processes = sum("schwab-gateway" in line for line in top)
    return {
        "container_id": values[0],
        "image_id": values[1],
        "created_at": values[2],
        "started_at": values[3],
        "status": values[4],
        "restart_count": int(values[5]),
        "revision": values[6],
        "compose_project": values[7],
        "compose_service": values[8],
        "health": (state.get("Health") or {}).get("Status", "none"),
        "gateway_processes": gateway_processes,
    }


def background_context() -> dict[str, Any]:
    rows = _run_read_only(
        [
            "docker",
            "ps",
            "--format",
            "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Label \"com.docker.compose.project\"}}",
        ]
    ).splitlines()
    selected = []
    for row in rows:
        name = row.split("\t", 1)[0]
        if name == "schwab_gateway_candidate" or "afterhours" in name.lower():
            selected.append(row.split("\t"))
    return {"containers": selected}


def assert_production_identity(
    observed: dict[str, Any], expected: dict[str, Any]
) -> list[str]:
    errors = []
    for field in ("container_id", "image_id", "revision", "started_at"):
        if observed.get(field) != expected.get(field):
            errors.append(f"production_{field}_changed")
    if observed.get("restart_count") != 0:
        errors.append("production_restart_count_nonzero")
    if observed.get("status") != "running":
        errors.append("production_not_running")
    if observed.get("health") != "healthy":
        errors.append("production_not_healthy")
    if observed.get("gateway_processes") != 1:
        errors.append("production_gateway_process_count_not_one")
    return errors


async def _request(
    client: httpx.AsyncClient,
    directory: pathlib.Path,
    name: str,
    path: str,
    params: dict[str, str],
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = await client.get(path, params=params)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        raw_path = directory / f"{name}.json"
        digest = _write_new(raw_path, response.content)
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.status_code == 200:
            classification = "success"
        elif response.status_code == 504 and 2_500 <= elapsed_ms <= 4_000:
            classification = "likely_three_second_upstream_timeout"
        elif response.status_code == 429:
            classification = "admission_rejection"
        elif response.status_code in {401, 403}:
            classification = "authentication_or_authorization_failure"
        elif response.status_code >= 500:
            classification = "gateway_or_upstream_server_error"
        else:
            classification = "unexpected_http_status"
        return {
            "name": name,
            "path": str(raw_path),
            "sha256": digest,
            "status": response.status_code,
            "latency_ms": elapsed_ms,
            "bytes": len(response.content),
            "body": body,
            "error": None,
            "classification": classification,
        }
    except Exception as exc:
        return {
            "name": name,
            "path": None,
            "sha256": None,
            "status": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "bytes": 0,
            "body": None,
            "error": type(exc).__name__,
            "classification": "client_or_transport_error",
        }


async def _request_with_retry(
    client: httpx.AsyncClient,
    directory: pathlib.Path,
    name: str,
    path: str,
    params: dict[str, str],
    *,
    max_attempts: int = REQUEST_MAX_ATTEMPTS,
    retry_backoff_seconds: float = REQUEST_RETRY_BACKOFF_SECONDS,
) -> dict[str, Any]:
    """Retry bounded transient read failures while preserving every raw attempt."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")
    if retry_backoff_seconds < 0:
        raise ValueError("retry_backoff_seconds must be nonnegative")

    attempts: list[dict[str, Any]] = []
    result: dict[str, Any] | None = None
    for attempt in range(1, max_attempts + 1):
        attempt_name = name if attempt == 1 else f"{name}_retry_{attempt}"
        result = await _request(client, directory, attempt_name, path, params)
        attempts.append({key: value for key, value in result.items() if key != "body"})
        if result["classification"] not in RETRYABLE_REQUEST_CLASSIFICATIONS:
            break
        if attempt < max_attempts:
            await asyncio.sleep(retry_backoff_seconds * (2 ** (attempt - 1)))

    if result is None:  # pragma: no cover - the validated loop always executes
        raise AssertionError("request retry loop exhausted without an attempt")
    result["name"] = name
    result["attempts"] = attempts
    result["recovered_transient"] = (
        len(attempts) > 1 and result["classification"] == "success"
    )
    return result


async def _metrics(client: httpx.AsyncClient, path: pathlib.Path) -> dict[str, Any]:
    started = time.perf_counter()
    response = await client.get("/metrics")
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    lines = [line for line in response.text.splitlines() if METRIC_RE.match(line)]
    payload = ("\n".join(lines) + "\n").encode()
    digest = _write_new(path, payload)
    return {
        "path": str(path),
        "sha256": digest,
        "status": response.status_code,
        "latency_ms": latency_ms,
        "line_count": len(lines),
    }


async def _health(client: httpx.AsyncClient) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in ("/health", "/ready"):
        response = await client.get(path)
        body = response.json() if response.content else None
        if isinstance(body, dict):
            body = {
                key: body.get(key)
                for key in ("schema_version", "status", "service", "timestamp", "token_state", "reason")
                if key in body
            }
        result[path.lstrip("/")] = {"status": response.status_code, "body": body}
    return result


def health_violations(health: dict[str, Any], *, prefix: str) -> list[str]:
    errors: list[str] = []
    if (health.get("health") or {}).get("status") != 200:
        errors.append(f"{prefix}_health_non_200")
    ready = health.get("ready") or {}
    if ready.get("status") != 200:
        errors.append(f"{prefix}_ready_non_200")
    if (ready.get("body") or {}).get("token_state") != "ready":
        errors.append(f"{prefix}_token_not_ready")
    return errors


def cache_consistency_result(
    first: dict[str, Any] | None,
    cached: dict[str, Any] | None,
) -> dict[str, Any]:
    if first is None or cached is None:
        return {
            "evaluated": False,
            "semantic_equal": None,
            "reason": "missing_successful_pair",
            "ignored_freshness_difference_count": 0,
            "ignored_freshness_difference_paths": [],
        }
    freshness_paths = ignored_freshness_difference_paths(first, cached)
    return {
        "evaluated": True,
        "semantic_equal": canonical_market_data(first)
        == canonical_market_data(cached),
        "ignored_freshness_difference_count": len(freshness_paths),
        "ignored_freshness_difference_paths": freshness_paths,
    }


def partition_opening_warmup_violations(
    violations: list[str],
    *,
    checkpoint_index: int,
    warmup_checkpoints: int,
) -> tuple[list[str], list[str]]:
    """Keep expected opening-roll staleness observable without weakening later gates."""
    gating: list[str] = []
    observations: list[str] = []
    for violation in sorted(set(violations)):
        request, separator, error = violation.partition(":")
        is_opening_roll = (
            checkpoint_index < warmup_checkpoints
            and bool(separator)
            and request.startswith(OPENING_WARMUP_SURFACES)
            and error in OPENING_WARMUP_ERRORS
        )
        (observations if is_opening_roll else gating).append(violation)
    return gating, observations


async def run_checkpoint(
    client: httpx.AsyncClient,
    root: pathlib.Path,
    index: int,
    session_date: dt.date,
    expected_identity: dict[str, Any],
    production_container: str,
) -> dict[str, Any]:
    now = dt.datetime.now(UTC)
    directory = root / "raw" / f"{index:03d}_{now.strftime('%Y%m%dT%H%M%SZ')}"
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    observed_before = production_identity(production_container)
    violations = assert_production_identity(observed_before, expected_identity)
    health = await _health(client)
    violations.extend(health_violations(health, prefix="checkpoint"))
    metrics_before = await _metrics(client, directory / "metrics_before.txt")
    if metrics_before["status"] != 200:
        violations.append("metrics_before_non_200")

    groups: list[list[tuple[str, str, dict[str, str]]]] = [
        [
            (f"spot_{symbol.lstrip('$').lower()}", "/v1/spot", {"symbol": symbol})
            for symbol in SYMBOLS
        ],
        [("spot_vix", "/v1/spot", {"symbol": "$VIX"})],
        [
            (
                f"chain_{symbol.lstrip('$').lower()}_first",
                "/v1/option-chain",
                {"symbol": symbol, "expiration": session_date.isoformat()},
            )
            for symbol in SYMBOLS
        ],
        [
            (
                f"chain_{symbol.lstrip('$').lower()}_cached",
                "/v1/option-chain",
                {"symbol": symbol, "expiration": session_date.isoformat()},
            )
            for symbol in SYMBOLS
        ],
        [
            (
                f"history_{symbol.lstrip('$').lower()}_minute",
                "/v1/history",
                {"symbol": symbol, "frequency": "minute", "days_back": "1"},
            )
            for symbol in SYMBOLS
        ],
        [
            (
                f"session_{symbol.lstrip('$').lower()}_regular",
                "/v1/session-history",
                {
                    "symbol": symbol,
                    "date": session_date.isoformat(),
                    "session": "regular",
                },
            )
            for symbol in SYMBOLS
        ],
    ]
    requests: list[dict[str, Any]] = []
    for group in groups:
        requests.extend(
            await asyncio.gather(
                *(
                    _request_with_retry(client, directory, name, path, params)
                    for name, path, params in group
                )
            )
        )
        await asyncio.sleep(0.25)

    validations: dict[str, Any] = {}
    bodies: dict[str, dict[str, Any]] = {}
    summaries: list[dict[str, Any]] = []
    for request in requests:
        body = request.pop("body")
        summaries.append(request)
        if request["status"] != 200 or not isinstance(body, dict):
            violations.append(f"{request['name']}_non_200_or_invalid_json")
            continue
        bodies[request["name"]] = body
        symbol = "$" + request["name"].split("_")[1].upper()
        if request["name"].startswith("spot_"):
            validation = validate_spot(body, symbol)
        elif request["name"].startswith("chain_"):
            validation = validate_chain(body, symbol, session_date)
        elif request["name"].startswith("history_"):
            validation = validate_history(
                body, symbol, surface="history", session_date=session_date
            )
        else:
            validation = validate_history(
                body,
                symbol,
                surface="session_history",
                session_date=session_date,
                expected_session="regular",
            )
        validations[request["name"]] = validation
        violations.extend(
            f"{request['name']}:{error}" for error in validation.get("errors", [])
        )

    cache_consistency: dict[str, Any] = {}
    for symbol in SYMBOLS:
        stem = symbol.lstrip("$").lower()
        first = bodies.get(f"chain_{stem}_first")
        cached = bodies.get(f"chain_{stem}_cached")
        comparison = cache_consistency_result(first, cached)
        cache_consistency[symbol] = comparison
        if comparison["evaluated"] and not comparison["semantic_equal"]:
            violations.append(f"cache_semantic_mismatch:{symbol}")

    metrics_after = await _metrics(client, directory / "metrics_after.txt")
    if metrics_after["status"] != 200:
        violations.append("metrics_after_non_200")
    observed_after = production_identity(production_container)
    violations.extend(assert_production_identity(observed_after, expected_identity))
    result = {
        "index": index,
        "started_utc": now.isoformat(),
        "finished_utc": dt.datetime.now(UTC).isoformat(),
        "production_before": observed_before,
        "production_after": observed_after,
        "background_context": background_context(),
        "health": health,
        "metrics_before": metrics_before,
        "metrics_after": metrics_after,
        "requests": summaries,
        "validations": validations,
        "cache_consistency": cache_consistency,
        "violations": sorted(set(violations)),
    }
    result_path = directory / "checkpoint.json"
    result["checkpoint_sha256"] = _write_json_new(result_path, result)
    return result


async def run_extended_session_check(
    client: httpx.AsyncClient,
    root: pathlib.Path,
    session_date: dt.date,
) -> dict[str, Any]:
    """Validate the bounded empty-extended-session contract after market close."""
    directory = root / "raw" / "post_close_extended"
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    requests = await asyncio.gather(
        *(
            _request_with_retry(
                client,
                directory,
                f"session_{symbol.lstrip('$').lower()}_extended",
                "/v1/session-history",
                {
                    "symbol": symbol,
                    "date": session_date.isoformat(),
                    "session": "extended",
                },
            )
            for symbol in SYMBOLS
        )
    )
    summaries: list[dict[str, Any]] = []
    validations: dict[str, Any] = {}
    violations: list[str] = []
    for request in requests:
        body = request.pop("body")
        summaries.append(request)
        if request["status"] != 200 or not isinstance(body, dict):
            violations.append(f"{request['name']}_non_200_or_invalid_json")
            continue
        symbol = "$" + request["name"].split("_")[1].upper()
        validation = validate_history(
            body,
            symbol,
            surface="session_history",
            allow_empty_extended=True,
            session_date=session_date,
            expected_session="extended",
        )
        validations[request["name"]] = validation
        violations.extend(
            f"{request['name']}:{error}" for error in validation.get("errors", [])
        )
    result = {
        "retrieved_utc": dt.datetime.now(UTC).isoformat(),
        "requests": summaries,
        "validations": validations,
        "violations": sorted(set(violations)),
    }
    result_path = directory / "post_close_extended.json"
    result["evidence_sha256"] = _write_json_new(result_path, result)
    return result


def _filtered_gateway_logs(container: str, since: str, path: pathlib.Path) -> str:
    output = subprocess.run(
        ["docker", "logs", "--since", since, container],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    records = []
    for raw in (output.stdout + "\n" + output.stderr).splitlines():
        try:
            item = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(item, dict):
            continue
        records.append({key: item[key] for key in ALLOWED_GATEWAY_LOG_FIELDS if key in item})
    payload = b"".join(
        (json.dumps(record, sort_keys=True) + "\n").encode() for record in records
    )
    return _write_new(path, payload)


async def _wait_until(target: dt.datetime) -> None:
    while True:
        remaining = (target - dt.datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            return
        await asyncio.sleep(min(remaining, 30.0))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-date", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--evidence-dir", type=pathlib.Path, required=True)
    parser.add_argument(
        "--api-key-env",
        type=pathlib.Path,
        default=pathlib.Path("/opt/butterflyguy-gateway-consumer.env"),
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--production-container", default="schwab_gateway_live")
    parser.add_argument("--expected-container-id", required=True)
    parser.add_argument("--expected-image-id", required=True)
    parser.add_argument("--expected-revision", required=True)
    parser.add_argument("--expected-started-at", required=True)
    parser.add_argument("--sample-seconds", type=int, default=900)
    parser.add_argument("--post-close-minutes", type=int, default=10)
    parser.add_argument("--opening-warmup-checkpoints", type=int, default=1)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    if (
        args.sample_seconds <= 0
        or args.post_close_minutes < 0
        or args.opening_warmup_checkpoints < 0
    ):
        raise SystemExit("sampling and post-close durations must be nonnegative")
    root: pathlib.Path = args.evidence_dir
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(root, 0o700)
    expected = {
        "container_id": args.expected_container_id,
        "image_id": args.expected_image_id,
        "revision": args.expected_revision,
        "started_at": args.expected_started_at,
    }
    started_utc = dt.datetime.now(UTC)
    open_et = dt.datetime.combine(args.session_date, dt.time(9, 30), tzinfo=EASTERN)
    close_et = dt.datetime.combine(args.session_date, dt.time(16, 0), tzinfo=EASTERN)
    if started_utc.astimezone(EASTERN).date() != args.session_date:
        raise SystemExit("harness must start on the requested session date")
    if started_utc > open_et.astimezone(UTC):
        raise SystemExit("harness started after market open; full-session credit is impossible")

    manifest: dict[str, Any] = {
        "purpose": "complete regular-session production SchwabGateway acceptance soak",
        "provider": "SchwabGateway production",
        "endpoint": args.base_url,
        "session_date": args.session_date.isoformat(),
        "display_timezone": "America/Los_Angeles",
        "started_utc": started_utc.isoformat(),
        "expected_production": expected,
        "background_policy": (
            "candidate gateway and AfterHours may change; observations are context only"
        ),
        "sample_seconds": args.sample_seconds,
        "request_retry": {
            "max_attempts": REQUEST_MAX_ATTEMPTS,
            "initial_backoff_seconds": REQUEST_RETRY_BACKOFF_SECONDS,
            "classifications": sorted(RETRYABLE_REQUEST_CLASSIFICATIONS),
            "raw_attempts_preserved": True,
        },
        "opening_warmup_checkpoints": args.opening_warmup_checkpoints,
        "opening_warmup_observations": [],
        "checkpoints": [],
        "violations": [],
        "complete": False,
    }
    _write_manifest(root / "manifest.json", manifest)
    baseline = production_identity(args.production_container)
    baseline_errors = assert_production_identity(baseline, expected)
    if baseline_errors:
        manifest["violations"].extend(baseline_errors)
        _write_manifest(root / "manifest.json", manifest)
        return 1

    api_key = _read_scoped_key(args.api_key_env)
    headers = {"X-Internal-API-Key": api_key}
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(
        base_url=args.base_url.rstrip("/"), headers=headers, timeout=timeout
    ) as client:
        baseline_health = await _health(client)
        baseline_metrics = await _metrics(client, root / "baseline_metrics.txt")
        baseline_violations = health_violations(
            baseline_health, prefix="baseline"
        )
        if baseline_metrics["status"] != 200:
            baseline_violations.append("baseline_metrics_non_200")
        manifest["baseline"] = {
            "retrieved_utc": dt.datetime.now(UTC).isoformat(),
            "production": baseline,
            "background_context": background_context(),
            "health": baseline_health,
            "metrics": baseline_metrics,
            "log_boundary_utc": started_utc.isoformat(),
            "violations": baseline_violations,
        }
        manifest["violations"].extend(baseline_violations)
        _write_manifest(root / "manifest.json", manifest)
        if baseline_violations:
            return 1

        await _wait_until(open_et.astimezone(UTC))
        checkpoint_at = open_et.astimezone(UTC)
        index = 0
        production_drift = False
        while checkpoint_at <= close_et.astimezone(UTC):
            await _wait_until(checkpoint_at)
            checkpoint = await run_checkpoint(
                client,
                root,
                index,
                args.session_date,
                expected,
                args.production_container,
            )
            gating_violations, warmup_observations = (
                partition_opening_warmup_violations(
                    checkpoint["violations"],
                    checkpoint_index=index,
                    warmup_checkpoints=args.opening_warmup_checkpoints,
                )
            )
            manifest["checkpoints"].append(
                {
                    "index": index,
                    "started_utc": checkpoint["started_utc"],
                    "finished_utc": checkpoint["finished_utc"],
                    "checkpoint_sha256": checkpoint["checkpoint_sha256"],
                    "violations": checkpoint["violations"],
                    "gating_violations": gating_violations,
                    "opening_warmup_observations": warmup_observations,
                }
            )
            if warmup_observations:
                manifest["opening_warmup_observations"].append(
                    {
                        "index": index,
                        "started_utc": checkpoint["started_utc"],
                        "observations": warmup_observations,
                    }
                )
            manifest["violations"].extend(gating_violations)
            _write_manifest(root / "manifest.json", manifest)
            if any(error.startswith("production_") for error in gating_violations):
                production_drift = True
                break
            index += 1
            checkpoint_at += dt.timedelta(seconds=args.sample_seconds)

        if not production_drift:
            post_close = close_et + dt.timedelta(minutes=args.post_close_minutes)
            await _wait_until(post_close.astimezone(UTC))
            final_identity = production_identity(args.production_container)
            manifest["violations"].extend(
                assert_production_identity(final_identity, expected)
            )
            manifest["final_production"] = final_identity
            manifest["final_health"] = await _health(client)
            manifest["violations"].extend(
                health_violations(manifest["final_health"], prefix="final")
            )
            manifest["final_metrics"] = await _metrics(
                client, root / "final_metrics.txt"
            )
            if manifest["final_metrics"]["status"] != 200:
                manifest["violations"].append("final_metrics_non_200")
            manifest["post_close_extended"] = await run_extended_session_check(
                client, root, args.session_date
            )
            manifest["violations"].extend(
                manifest["post_close_extended"]["violations"]
            )

    manifest["filtered_log_sha256"] = _filtered_gateway_logs(
        args.production_container,
        started_utc.isoformat().replace("+00:00", "Z"),
        root / "filtered_gateway_logs.jsonl",
    )
    manifest["finished_utc"] = dt.datetime.now(UTC).isoformat()
    manifest["violations"] = sorted(set(manifest["violations"]))
    manifest["complete"] = not production_drift
    _write_manifest(root / "manifest.json", manifest)
    manifest_sha256 = _sha256(root / "manifest.json")
    print(
        json.dumps(
            {
                "evidence_dir": str(root),
                "manifest_sha256": manifest_sha256,
                "checkpoint_count": len(manifest["checkpoints"]),
                "violation_count": len(manifest["violations"]),
            },
            sort_keys=True,
        )
    )
    return 0 if not manifest["violations"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
