#!/usr/bin/env python3
"""Read-only Schwab Gateway v0.4.6 and ButterflyGuy readiness soak.

The monitor has no Docker lifecycle, order, token-write, configuration-write, or
database-write capability. It stores only aggregate market-data validation and
redacted operational evidence; authenticated Schwab response bodies are never
written to disk.
"""

from __future__ import annotations

import argparse
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

try:
    from schwab_gateway_session_soak_20260909_validator import (
        METRIC_RE,
        _read_scoped_key,
        validate_chain,
        validate_history,
        validate_spot,
    )
except ImportError:  # local repository execution/tests
    from tools.schwab_gateway_session_soak import (
        METRIC_RE,
        _read_scoped_key,
        validate_chain,
        validate_history,
        validate_spot,
    )

UTC = dt.timezone.utc
PACIFIC = ZoneInfo("America/Los_Angeles")
SYMBOLS = ("$SPX", "$NDX", "$XSP")
GATEWAY = "schwab_gateway_live"
STRATEGIES = {
    "$SPX": ("butterfly_spx_app", 8000),
    "$NDX": ("butterfly_ndx_app", 8001),
    "$XSP": ("butterfly_xsp_app", 8003),
}
EXPECTED = {
    GATEWAY: {
        "image_id": "sha256:8870ad371e36b3aacaa73fc20c4fa20400bf62e4080aed6f0fb9ddd9a9147410",
        "revision": "ce4c5e1ef1432747a5f0915f93bae9640a9190b5",
    },
    **{
        container: {
            "image_id": "sha256:1f7b1a513e72e82b1f93a9bf838466f11d196178840e27df838cc765f35b55a9",
            "revision": "be171aef6f2291b3ba953f3d5d35824be5f8e556",
        }
        for container, _port in STRATEGIES.values()
    },
}
PAPER_FLAGS = {
    "EXECUTION__PAPER_TRADING": "true",
    "EXECUTION__ALLOW_LIVE_TRADING": "false",
    "ALLOW_LIVE_TRADING": "false",
    "SCHWAB_ACCESS_MODE": "gateway",
}
GATEWAY_FLAGS = {"SCHWAB_GATEWAY_ORDER_WRITES_ENABLED": "false"}
TOKEN_PATH = "/opt/butterflyguy-tokens/tokens.json"
LOG_PATTERNS = {
    "negative_intrinsic_rejection": re.compile(
        r"gateway option contract intrinsic_value must be nonnegative", re.I
    ),
    "task_group_failure": re.compile(r"task.?group", re.I),
    "fatal_critical": re.compile(r"\b(?:fatal|critical)\b", re.I),
    "traceback": re.compile(r"traceback", re.I),
    "timeout": re.compile(r"timeout", re.I),
    "http_429": re.compile(r"(?:HTTP/\d(?:\.\d)?\s+429|status(?:_code)?[=: ]+429)", re.I),
    "http_5xx": re.compile(r"(?:HTTP/\d(?:\.\d)?\s+5\d\d|status(?:_code)?[=: ]+5\d\d)", re.I),
}
GATING_LOG_PATTERNS = {
    "negative_intrinsic_rejection",
    "task_group_failure",
    "fatal_critical",
    "traceback",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_new(path: pathlib.Path, value: Any) -> str:
    payload = value if isinstance(value, bytes) else (
        json.dumps(value, sort_keys=True, indent=2) + "\n"
    ).encode()
    with path.open("xb") as handle:
        handle.write(payload)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return sha256(path)


def append_jsonl(path: pathlib.Path, value: Any) -> None:
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run(args: list[str], *, timeout: float = 60.0, check: bool = True) -> str:
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]} {args[1] if len(args) > 1 else ''}")
    return result.stdout


def docker_inspect(container: str) -> dict[str, Any]:
    raw = json.loads(run(["docker", "inspect", container]))[0]
    state = raw["State"]
    health = state.get("Health") or {}
    labels = raw["Config"].get("Labels") or {}
    safe_env: dict[str, str | None] = {}
    wanted = GATEWAY_FLAGS if container == GATEWAY else PAPER_FLAGS
    env = {}
    for entry in raw["Config"].get("Env") or []:
        name, separator, value = entry.partition("=")
        if separator and name in wanted:
            env[name] = value
    safe_env.update({key: env.get(key) for key in wanted})
    token_mounts = [
        {
            "source": mount["Source"],
            "destination": mount["Destination"],
            "mode": mount.get("Mode"),
            "rw": mount.get("RW"),
        }
        for mount in raw.get("Mounts") or []
        if "token" in mount["Source"].lower()
        or "token" in mount["Destination"].lower()
    ]
    top = run(["docker", "top", container, "-eo", "pid,comm,args"])
    process_lines = [line for line in top.splitlines()[1:] if line.strip()]
    return {
        "container_id": raw["Id"],
        "image_id": raw["Image"],
        "revision": labels.get("org.opencontainers.image.revision", "<no value>"),
        "started_at": state["StartedAt"],
        "restart_count": raw["RestartCount"],
        "status": state["Status"],
        "docker_health": health.get("Status", "none"),
        "failing_streak": health.get("FailingStreak", 0),
        "healthcheck": raw["Config"].get("Healthcheck"),
        "read_only_rootfs": raw["HostConfig"].get("ReadonlyRootfs"),
        "cap_drop": raw["HostConfig"].get("CapDrop") or [],
        "security_opt": raw["HostConfig"].get("SecurityOpt") or [],
        "process_count": len(process_lines),
        "safe_flags": safe_env,
        "token_mounts": token_mounts,
    }


def identity_violations(
    observed: dict[str, Any],
    expected_release: dict[str, str],
    frozen: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    for field in ("image_id", "revision"):
        if observed.get(field) != expected_release[field]:
            errors.append(f"{field}_unexpected")
    if frozen:
        for field in ("container_id", "image_id", "revision", "started_at"):
            if observed.get(field) != frozen.get(field):
                errors.append(f"{field}_drift")
    if observed.get("restart_count") != 0:
        errors.append("restart_count_nonzero")
    if observed.get("status") != "running":
        errors.append("not_running")
    if observed.get("process_count") != 1:
        errors.append("process_count_not_one")
    if observed.get("read_only_rootfs") is not True:
        errors.append("rootfs_not_read_only")
    if "ALL" not in observed.get("cap_drop", []):
        errors.append("capabilities_not_all_dropped")
    if "no-new-privileges:true" not in observed.get("security_opt", []):
        errors.append("no_new_privileges_missing")
    if observed["safe_flags"] != (
        GATEWAY_FLAGS if expected_release == EXPECTED[GATEWAY] else PAPER_FLAGS
    ):
        errors.append("safety_flags_mismatch")
    if observed["docker_health"] not in {"healthy", "none"}:
        errors.append("docker_unhealthy")
    return errors


def token_observation(containers: list[str]) -> tuple[dict[str, Any], list[str]]:
    source_paths: set[str] = set()
    destination_paths: set[str] = set()
    rows: dict[str, Any] = {}
    host_stat = os.stat(TOKEN_PATH)
    host_meta = {
        "path": TOKEN_PATH,
        "inode": host_stat.st_ino,
        "mode": stat.S_IMODE(host_stat.st_mode),
        "uid": host_stat.st_uid,
        "gid": host_stat.st_gid,
    }
    violations: list[str] = []
    for container in containers:
        observed = docker_inspect(container)
        mounts = observed["token_mounts"]
        matching = [mount for mount in mounts if mount["destination"] == os.path.dirname(TOKEN_PATH)]
        if len(matching) != 1:
            violations.append(f"{container}:token_mount_count")
        else:
            source_paths.add(matching[0]["source"])
            destination_paths.add(matching[0]["destination"])
        metadata = run(
            ["docker", "exec", container, "stat", "-Lc", "%i:%a:%u:%g", TOKEN_PATH]
        ).strip()
        rows[container] = {"mounts": mounts, "metadata": metadata}
        if metadata != f"{host_meta['inode']}:{host_meta['mode']:o}:{host_meta['uid']}:{host_meta['gid']}":
            violations.append(f"{container}:token_metadata_disagreement")
    if len(source_paths) != 1 or len(destination_paths) != 1:
        violations.append("token_mount_path_disagreement")
    return {"host": host_meta, "containers": rows}, violations


def candidate_observation() -> tuple[list[dict[str, str]], list[str]]:
    rows = run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.State}}\t{{.Status}}"])
    candidates: list[dict[str, str]] = []
    running: list[str] = []
    for row in rows.splitlines():
        name, state, status_text = row.split("\t", 2)
        if "candidate" not in name.lower():
            continue
        candidates.append({"name": name, "state": state, "status": status_text})
        if state == "running":
            running.append(name)
    return candidates, [f"candidate_running:{name}" for name in sorted(running)]


def http_json(client: httpx.Client, path: str) -> dict[str, Any]:
    started = time.perf_counter()
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        try:
            response = client.get(path)
            attempts.append({"attempt": attempt, "status": response.status_code})
            body = response.json() if response.content else None
            if isinstance(body, dict):
                body = {
                    key: body[key]
                    for key in (
                        "status", "reason", "token_state", "service", "timestamp"
                    )
                    if key in body
                }
            if response.status_code == 200 or response.status_code < 500:
                return {
                    "status": response.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "body": body,
                    "attempts": attempts,
                }
        except Exception as exc:
            attempts.append(
                {"attempt": attempt, "status": None, "error": type(exc).__name__}
            )
        if attempt < 3:
            time.sleep(0.5 * (2 ** (attempt - 1)))
    return {
        "status": attempts[-1]["status"],
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "attempts": attempts,
    }


def endpoint_snapshot() -> tuple[dict[str, Any], list[str]]:
    endpoints: dict[str, Any] = {}
    violations: list[str] = []
    targets = {GATEWAY: 8011, **{container: port for container, port in STRATEGIES.values()}}
    for container, port in targets.items():
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=15.0) as client:
            endpoints[container] = {
                route: http_json(client, route) for route in ("/health", "/ready")
            }
            if container == GATEWAY:
                response = client.get("/metrics")
                endpoints[container]["/metrics"] = {
                    "status": response.status_code,
                    "latency_ms": round(response.elapsed.total_seconds() * 1000, 3),
                }
        for route in ("/health", "/ready"):
            if endpoints[container][route]["status"] != 200:
                violations.append(f"{container}:{route.lstrip('/')}_non_200")
        if container == GATEWAY:
            ready_body = endpoints[container]["/ready"].get("body") or {}
            if ready_body.get("token_state") != "ready":
                violations.append("gateway_token_not_ready")
            if endpoints[container]["/metrics"]["status"] != 200:
                violations.append("gateway_metrics_non_200")
    return endpoints, violations


def preopen_endpoint_violations(
    endpoints: dict[str, Any], violations: list[str]
) -> list[str]:
    """Allow only the documented post-close strategy readiness state."""
    allowed: set[str] = set()
    for container, _port in STRATEGIES.values():
        ready = endpoints.get(container, {}).get("/ready", {})
        if (
            ready.get("status") == 503
            and (ready.get("body") or {}).get("reason")
            == "gateway_market_data_unavailable"
        ):
            allowed.add(f"{container}:ready_non_200")
    return [violation for violation in violations if violation not in allowed]


def parse_prometheus(text: str, allow: re.Pattern[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for line in text.splitlines():
        if line.startswith("#") or not allow.match(line):
            continue
        name, separator, raw_value = line.rpartition(" ")
        if not separator:
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        if math.isfinite(value):
            values[name] = value
    return dict(sorted(values.items()))


def metrics_snapshot() -> tuple[dict[str, Any], list[str]]:
    result: dict[str, Any] = {}
    violations: list[str] = []
    response = httpx.get("http://127.0.0.1:8011/metrics", timeout=15.0)
    result[GATEWAY] = {
        "status": response.status_code,
        "values": parse_prometheus(response.text, METRIC_RE),
    }
    if response.status_code != 200:
        violations.append("gateway_metrics_non_200")
    strategy_pattern = re.compile(r"^(?:butterfly_chain_snapshots_total|process_start_time_seconds)(?=[{ ]|$)")
    for symbol, (container, port) in STRATEGIES.items():
        response = httpx.get(f"http://127.0.0.1:{port}/metrics", timeout=15.0)
        values = parse_prometheus(response.text, strategy_pattern)
        result[container] = {"symbol": symbol, "status": response.status_code, "values": values}
        if response.status_code != 200:
            violations.append(f"{container}:metrics_non_200")
    return result, violations


def normalization_counter(metrics: dict[str, Any]) -> float | None:
    name = "gateway_option_chain_negative_intrinsic_value_normalizations_total"
    values = metrics.get(GATEWAY, {}).get("values", {})
    matching = [value for key, value in values.items() if key == name or key.startswith(name + "{")]
    return sum(matching) if matching else None


def snapshot_counter(metrics: dict[str, Any], container: str) -> float | None:
    values = metrics.get(container, {}).get("values", {})
    matching = [
        value
        for key, value in values.items()
        if key == "butterfly_chain_snapshots_total"
        or key.startswith("butterfly_chain_snapshots_total{")
    ]
    return sum(matching) if matching else None


def host_snapshot() -> dict[str, Any]:
    meminfo: dict[str, int] = {}
    for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}:
            meminfo[key] = int(value.strip().split()[0]) * 1024
    disk = os.statvfs("/opt")
    stats = run(
        [
            "docker", "stats", "--no-stream", "--format",
            "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.PIDs}}",
            GATEWAY, *[container for container, _port in STRATEGIES.values()],
        ],
        timeout=30,
    )
    return {
        "load_average": list(os.getloadavg()),
        "memory_bytes": meminfo,
        "disk": {
            "path": "/opt",
            "available_bytes": disk.f_bavail * disk.f_frsize,
            "total_bytes": disk.f_blocks * disk.f_frsize,
        },
        "docker_stats": [line.split("|", 3) for line in stats.splitlines() if line],
    }


def host_violations(observation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    memory = observation["memory_bytes"]
    if memory.get("MemAvailable", 0) < 1024**3:
        errors.append("host_memory_headroom_below_1gib")
    if observation["disk"]["available_bytes"] < 5 * 1024**3:
        errors.append("host_disk_headroom_below_5gib")
    cpu_count = os.cpu_count() or 1
    if observation["load_average"][0] > cpu_count * 2:
        errors.append("host_load_exceeds_two_per_cpu")
    return errors


def required_unit_observation() -> tuple[dict[str, str], list[str]]:
    states: dict[str, str] = {}
    errors: list[str] = []
    for unit in ("docker", "containerd", "piavpn"):
        state = run(["systemctl", "is-active", unit], check=False).strip()
        states[unit] = state
        if state != "active":
            errors.append(f"unit_not_active:{unit}")
    return states, errors


def log_summary(since: dt.datetime) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for container in [GATEWAY, *[name for name, _port in STRATEGIES.values()]]:
        completed = subprocess.run(
            ["docker", "logs", "--since", since.isoformat(), container],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        text = completed.stdout + "\n" + completed.stderr
        counts = {name: len(pattern.findall(text)) for name, pattern in LOG_PATTERNS.items()}
        if container != GATEWAY:
            counts["spot_success"] = len(re.findall(r"/v1/spot\?.*HTTP/1\.1 200", text))
            counts["chain_success"] = len(re.findall(r"/v1/option-chain\?.*HTTP/1\.1 200", text))
            counts["minute_history_success"] = len(
                re.findall(r"/v1/history\?.*frequency=minute.*HTTP/1\.1 200", text)
            )
        result[container] = counts
    return result


def log_violations(summary: dict[str, Any]) -> list[str]:
    return [
        f"{container}:log:{pattern}"
        for container, counts in summary.items()
        for pattern in GATING_LOG_PATTERNS
        if counts.get(pattern, 0)
    ]


def bounded_request(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        started = time.perf_counter()
        try:
            response = client.get(path, params=params)
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            attempts.append({"attempt": attempt, "status": response.status_code, "latency_ms": elapsed})
            if response.status_code == 200:
                body = response.json()
                return {"attempts": attempts, "status": 200, "bytes": len(response.content)}, body if isinstance(body, dict) else None
            if response.status_code not in {429, 502, 503, 504}:
                break
        except Exception as exc:
            attempts.append(
                {
                    "attempt": attempt,
                    "status": None,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "error": type(exc).__name__,
                }
            )
        if attempt < 3:
            time.sleep(0.5 * (2 ** (attempt - 1)))
    return {"attempts": attempts, "status": attempts[-1]["status"], "bytes": 0}, None


def formula_mismatches(validation: dict[str, Any]) -> int:
    return sum(
        side.get("mismatch", 0)
        for side in validation.get("formula_consistency", {}).values()
    )


def diagnostic_probe(
    client: httpx.Client,
    session_date: dt.date,
    *,
    preflight: bool = False,
    allow_opening_freshness: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    result: dict[str, Any] = {}
    violations: list[str] = []
    for symbol in SYMBOLS:
        symbol_result: dict[str, Any] = {}
        if not preflight:
            request, body = bounded_request(client, "/v1/spot", {"symbol": symbol})
            symbol_result["spot_request"] = request
            if body is None:
                violations.append(f"{symbol}:spot_request_failed")
            else:
                validation = validate_spot(body, symbol)
                symbol_result["spot"] = validation
                spot_errors = list(validation["errors"])
                if allow_opening_freshness:
                    spot_errors = [
                        error
                        for error in spot_errors
                        if error not in {"stale", "too_old_for_consumer"}
                    ]
                violations.extend(f"{symbol}:spot:{error}" for error in spot_errors)

        request, body = bounded_request(
            client,
            "/v1/option-chain",
            {"symbol": symbol, "expiration": session_date.isoformat()},
        )
        symbol_result["chain_request"] = request
        if body is None:
            violations.append(f"{symbol}:chain_request_failed")
        else:
            validation = validate_chain(body, symbol, session_date)
            symbol_result["chain"] = validation
            chain_errors = list(validation["errors"])
            if preflight or allow_opening_freshness:
                chain_errors = [
                    error
                    for error in chain_errors
                    if error not in {"aggregate_stale", "too_old_for_consumer"}
                ]
            mismatches = formula_mismatches(validation)
            if mismatches:
                retry_request, retry_body = bounded_request(
                    client,
                    "/v1/option-chain",
                    {"symbol": symbol, "expiration": session_date.isoformat()},
                )
                symbol_result["formula_reprobe_request"] = retry_request
                if retry_body is None:
                    chain_errors.append("formula_reprobe_failed")
                else:
                    retry_validation = validate_chain(retry_body, symbol, session_date)
                    symbol_result["formula_reprobe"] = retry_validation
                    if formula_mismatches(retry_validation):
                        chain_errors.append("persistent_intrinsic_formula_mismatch")
            violations.extend(f"{symbol}:chain:{error}" for error in sorted(set(chain_errors)))

        if not preflight:
            request, body = bounded_request(
                client,
                "/v1/history",
                {"symbol": symbol, "frequency": "minute", "days_back": "1"},
            )
            symbol_result["history_request"] = request
            if body is None:
                violations.append(f"{symbol}:history_request_failed")
            else:
                validation = validate_history(body, symbol, surface="history")
                symbol_result["minute_history"] = validation
                history_errors = list(validation["errors"])
                if allow_opening_freshness:
                    history_errors = [
                        error
                        for error in history_errors
                        if error not in {"stale", "too_old_for_consumer"}
                    ]
                violations.extend(
                    f"{symbol}:history:{error}" for error in history_errors
                )
        result[symbol] = symbol_result
    return result, sorted(set(violations))


def flatness(tool: pathlib.Path, repo: pathlib.Path, session_date: dt.date) -> dict[str, Any]:
    completed = subprocess.run(
        [
            str(repo / ".venv/bin/python"),
            str(tool),
            "--config", "configs/config.yaml",
            "--date", session_date.isoformat(),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    try:
        observation = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        observation = {"flat": False, "error": "redacted_flatness_output_unavailable"}
    observation["returncode"] = completed.returncode
    return observation


def readiness_flap_events(
    previous: dict[str, bool],
    endpoints: dict[str, Any],
    now: dt.datetime,
    active: dict[str, dt.datetime],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for container in [GATEWAY, *[name for name, _port in STRATEGIES.values()]]:
        ready = endpoints[container]["/ready"]["status"] == 200
        was_ready = previous.get(container, True)
        if was_ready and not ready:
            active[container] = now
            events.append({"event": "readiness_flap_started", "container": container, "at_utc": now.isoformat()})
        elif not was_ready and ready:
            started = active.pop(container, now)
            events.append(
                {
                    "event": "readiness_flap_recovered",
                    "container": container,
                    "at_utc": now.isoformat(),
                    "duration_seconds": (now - started).total_seconds(),
                }
            )
        previous[container] = ready
    return events


def request_metric_delta(first: dict[str, float], last: dict[str, float]) -> dict[str, float]:
    return {
        key: last[key] - first.get(key, 0.0)
        for key in last
        if key.startswith(("gateway_client_requests_total", "gateway_client_request_latency_seconds_", "gateway_admission_total"))
    }


def summarize_samples(path: pathlib.Path) -> dict[str, Any]:
    endpoint_non_200: Counter[str] = Counter()
    docker_health: Counter[str] = Counter()
    log_counts: Counter[str] = Counter()
    request_statuses: Counter[str] = Counter()
    latencies: list[float] = []
    diagnostic_successes: Counter[str] = Counter()
    findings: dict[str, Counter[str]] = {symbol: Counter() for symbol in SYMBOLS}
    final_identities: dict[str, Any] | None = None
    with path.open() as handle:
        for raw in handle:
            record = json.loads(raw)
            if "index" not in record:
                continue
            final_identities = record["identities"]
            for container, identity in record["identities"].items():
                docker_health[f"{container}:{identity['docker_health']}"] += 1
            for container, routes in record["endpoints"].items():
                for route, observation in routes.items():
                    if observation["status"] != 200:
                        endpoint_non_200[f"{container}:{route}:{observation['status']}"] += 1
            for container, counts in record["log_summary"].items():
                for name, count in counts.items():
                    log_counts[f"{container}:{name}"] += count
            for symbol, diagnostic in (record.get("diagnostic") or {}).items():
                chain = diagnostic.get("chain") or {}
                if chain and not chain.get("errors") and "formula_reprobe" not in diagnostic:
                    diagnostic_successes[symbol] += 1
                elif chain and not chain.get("errors"):
                    reprobe = diagnostic.get("formula_reprobe") or {}
                    if not reprobe.get("errors") and not formula_mismatches(reprobe):
                        diagnostic_successes[symbol] += 1
                for key in (
                    "invalid_markets", "invalid_marks", "invalid_sizes",
                    "wrong_expirations", "duplicate_symbols",
                ):
                    findings[symbol][key] += int(chain.get(key, 0))
                for name, count in chain.get("intrinsic_value_counts", {}).items():
                    findings[symbol][f"intrinsic_{name}"] += int(count)
                for name, count in chain.get("time_value_counts", {}).items():
                    findings[symbol][f"time_value_{name}"] += int(count)
                findings[symbol]["formula_mismatch"] += formula_mismatches(chain)
                for key, value in diagnostic.items():
                    if not key.endswith("_request") or not isinstance(value, dict):
                        continue
                    for attempt in value.get("attempts", []):
                        request_statuses[str(attempt.get("status"))] += 1
                        if isinstance(attempt.get("latency_ms"), (int, float)):
                            latencies.append(float(attempt["latency_ms"]))
    latencies.sort()
    def percentile(fraction: float) -> float | None:
        if not latencies:
            return None
        index = min(len(latencies) - 1, math.ceil(len(latencies) * fraction) - 1)
        return latencies[index]
    return {
        "endpoint_non_200_counts": dict(sorted(endpoint_non_200.items())),
        "docker_health_sample_counts": dict(sorted(docker_health.items())),
        "filtered_log_counts": dict(sorted(log_counts.items())),
        "diagnostic_request_status_counts": dict(sorted(request_statuses.items())),
        "diagnostic_latency_ms": {
            "count": len(latencies),
            "min": latencies[0] if latencies else None,
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "max": latencies[-1] if latencies else None,
        },
        "diagnostic_success_counts": dict(sorted(diagnostic_successes.items())),
        "aggregate_chain_findings": {
            symbol: dict(sorted(counts.items())) for symbol, counts in findings.items()
        },
        "final_identities": final_identities,
    }


def finalize(
    root: pathlib.Path,
    manifest: dict[str, Any],
    launcher: pathlib.Path,
) -> None:
    sample_summary = summarize_samples(root / "samples.jsonl")
    manifest["sample_summary"] = sample_summary
    manifest_path = root / "manifest.json"
    report_path = root / "final_report.json"
    hashes_path = root / "SHA256SUMS"
    write_new(manifest_path, manifest)
    artifact_hashes = {
        "launcher": {"path": str(launcher), "sha256": sha256(launcher)},
        "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "samples": {"path": str(root / "samples.jsonl"), "sha256": sha256(root / "samples.jsonl")},
        "event_log": {"path": str(root / "events.jsonl"), "sha256": sha256(root / "events.jsonl")},
    }
    report = {
        "conclusion": "PASS" if not manifest["violations"] else "FAIL",
        "paper_trading_assessment": "GO" if not manifest["violations"] else "NO-GO",
        "session_date": manifest["session_date"],
        "started_utc": manifest["started_utc"],
        "finished_utc": manifest["finished_utc"],
        "observed_identities": manifest.get("frozen_identities"),
        "final_identities": sample_summary["final_identities"],
        "sample_count": len(manifest["samples"]),
        "missing_intervals": manifest["missing_intervals"],
        "snapshot_success_counts": manifest["snapshot_success_counts"],
        "diagnostic_success_counts": sample_summary["diagnostic_success_counts"],
        "endpoint_non_200_counts": sample_summary["endpoint_non_200_counts"],
        "docker_health_sample_counts": sample_summary["docker_health_sample_counts"],
        "aggregate_chain_findings": sample_summary["aggregate_chain_findings"],
        "filtered_log_counts": sample_summary["filtered_log_counts"],
        "request_status_counts": sample_summary["diagnostic_request_status_counts"],
        "request_latency_ms": sample_summary["diagnostic_latency_ms"],
        "normalization_counter": manifest["normalization_counter"],
        "readiness_flaps": manifest["readiness_flaps"],
        "request_metric_deltas": manifest.get("request_metric_deltas", {}),
        "preflight_flatness": manifest.get("preflight_flatness"),
        "post_close_flatness": manifest.get("post_close_flatness"),
        "violations": manifest["violations"],
        "known_out_of_scope": [
            "historical semantic cache-equivalence mismatches; legacy comparison harness not run"
        ],
        "evidence_permissions": "directories 0700; files 0600",
        "artifact_hashes": artifact_hashes,
    }
    write_new(report_path, report)
    artifact_hashes["final_report"] = {"path": str(report_path), "sha256": sha256(report_path)}
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in artifact_hashes.values()]
    write_new(hashes_path, ("\n".join(lines) + "\n").encode())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-date", type=dt.date.fromisoformat, required=True)
    parser.add_argument("--evidence-dir", type=pathlib.Path, required=True)
    parser.add_argument("--launcher", type=pathlib.Path, required=True)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path("/opt/butterflyguy"))
    parser.add_argument(
        "--flatness-tool",
        type=pathlib.Path,
        default=pathlib.Path("/opt/butterflyguy-gateway-acceptance-tools/gateway_cutover_flatness_audit_20260828.py"),
    )
    parser.add_argument(
        "--api-key-env",
        type=pathlib.Path,
        default=pathlib.Path("/opt/butterflyguy-gateway-consumer.env"),
    )
    parser.add_argument("--sample-seconds", type=int, default=300)
    parser.add_argument("--diagnostic-every", type=int, default=3)
    parser.add_argument("--post-close-minutes", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sample_seconds < 60 or args.diagnostic_every < 1:
        raise SystemExit("unsafe sampling configuration")
    root = args.evidence_dir
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(root, 0o700)
    samples_path = root / "samples.jsonl"
    events_path = root / "events.jsonl"
    append_jsonl(events_path, {"event": "monitor_started", "at_utc": dt.datetime.now(UTC).isoformat(), "pid": os.getpid()})
    append_jsonl(samples_path, {"record": "evidence_stream_initialized", "at_utc": dt.datetime.now(UTC).isoformat()})
    started = dt.datetime.now(UTC)
    open_time = dt.datetime.combine(args.session_date, dt.time(6, 30), tzinfo=PACIFIC)
    end_time = dt.datetime.combine(args.session_date, dt.time(13, args.post_close_minutes), tzinfo=PACIFIC)
    manifest: dict[str, Any] = {
        "purpose": "read-only Schwab Gateway v0.4.6 and ButterflyGuy gateway-readiness soak",
        "session_date": args.session_date.isoformat(),
        "display_timezone": "America/Los_Angeles",
        "started_utc": started.isoformat(),
        "sample_seconds": args.sample_seconds,
        "diagnostic_seconds_per_symbol": args.sample_seconds * args.diagnostic_every,
        "raw_authenticated_payloads_recorded": False,
        "samples": [],
        "violations": [],
        "missing_intervals": [],
        "readiness_flaps": [],
        "snapshot_success_counts": {symbol: 0 for symbol in SYMBOLS},
        "normalization_counter": {"start": None, "end": None, "delta": None},
    }
    frozen: dict[str, Any] = {}
    first_gateway_metrics: dict[str, float] = {}
    last_gateway_metrics: dict[str, float] = {}
    try:
        now = dt.datetime.now(PACIFIC)
        if now.date() != args.session_date or now >= open_time:
            raise RuntimeError("preflight_not_on_session_date_before_open")
        for container in EXPECTED:
            observed = docker_inspect(container)
            errors = identity_violations(observed, EXPECTED[container])
            if errors:
                manifest["violations"].extend(f"preflight:{container}:{error}" for error in errors)
            frozen[container] = observed
        manifest["frozen_identities"] = frozen
        tokens, token_errors = token_observation(list(EXPECTED))
        manifest["token_mount_agreement"] = tokens
        manifest["violations"].extend(f"preflight:{error}" for error in token_errors)
        candidates, candidate_errors = candidate_observation()
        manifest["preflight_candidates"] = candidates
        manifest["violations"].extend(f"preflight:{error}" for error in candidate_errors)
        endpoints, endpoint_errors = endpoint_snapshot()
        manifest["preflight_endpoints"] = endpoints
        manifest["violations"].extend(
            f"preflight:{error}"
            for error in preopen_endpoint_violations(endpoints, endpoint_errors)
        )
        preflight_metrics, metric_errors = metrics_snapshot()
        manifest["preflight_metrics"] = preflight_metrics
        manifest["violations"].extend(f"preflight:{error}" for error in metric_errors)
        counter = normalization_counter(preflight_metrics)
        manifest["normalization_counter"]["start"] = counter
        preflight_logs = log_summary(min(dt.datetime.fromisoformat(frozen[GATEWAY]["started_at"]), started))
        manifest["preflight_log_summary"] = preflight_logs
        manifest["violations"].extend(f"preflight:{error}" for error in log_violations(preflight_logs))
        manifest["preflight_units"], unit_errors = required_unit_observation()
        manifest["violations"].extend(f"preflight:{error}" for error in unit_errors)
        manifest["preflight_host"] = host_snapshot()
        manifest["violations"].extend(
            f"preflight:{error}" for error in host_violations(manifest["preflight_host"])
        )
        manifest["preflight_flatness"] = flatness(args.flatness_tool, args.repo, args.session_date)
        if not manifest["preflight_flatness"].get("flat"):
            manifest["violations"].append("preflight:flatness_failed")
        key = _read_scoped_key(args.api_key_env)
        with httpx.Client(
            base_url="http://127.0.0.1:8011",
            headers={"X-Internal-API-Key": key},
            timeout=20.0,
        ) as client:
            probe, probe_errors = diagnostic_probe(
                client, args.session_date, preflight=True
            )
            manifest["preflight_probe"] = probe
            manifest["violations"].extend(f"preflight:{error}" for error in probe_errors)
        append_jsonl(events_path, {"event": "preflight_complete", "at_utc": dt.datetime.now(UTC).isoformat(), "violations": sorted(set(manifest["violations"]))})
        if manifest["violations"]:
            raise RuntimeError("preflight_failed")

        while dt.datetime.now(UTC) < open_time.astimezone(UTC):
            time.sleep(min(30.0, (open_time.astimezone(UTC) - dt.datetime.now(UTC)).total_seconds()))

        previous_ready: dict[str, bool] = {}
        active_flaps: dict[str, dt.datetime] = {}
        previous_counter = counter
        previous_snapshots: dict[str, float | None] = {}
        previous_sample_at: dt.datetime | None = None
        log_since = started
        index = 0
        with httpx.Client(
            base_url="http://127.0.0.1:8011",
            headers={"X-Internal-API-Key": key},
            timeout=20.0,
        ) as client:
            target = open_time.astimezone(UTC)
            while target <= end_time.astimezone(UTC):
                while dt.datetime.now(UTC) < target:
                    time.sleep(min(30.0, (target - dt.datetime.now(UTC)).total_seconds()))
                sample_started = dt.datetime.now(UTC)
                violations: list[str] = []
                identities: dict[str, Any] = {}
                for container in EXPECTED:
                    observed = docker_inspect(container)
                    identities[container] = observed
                    violations.extend(
                        f"{container}:{error}"
                        for error in identity_violations(observed, EXPECTED[container], frozen[container])
                    )
                candidates, candidate_errors = candidate_observation()
                violations.extend(candidate_errors)
                endpoints, endpoint_errors = endpoint_snapshot()
                deferred_strategy_ready = {
                    f"{container}:ready_non_200"
                    for container, _port in STRATEGIES.values()
                }
                violations.extend(
                    error
                    for error in endpoint_errors
                    if error not in deferred_strategy_ready
                )
                metrics, metric_errors = metrics_snapshot()
                violations.extend(metric_errors)
                current_counter = normalization_counter(metrics)
                if previous_counter is not None and (current_counter is None or current_counter < previous_counter):
                    violations.append("normalization_counter_decreased_or_missing")
                previous_counter = current_counter
                current_snapshots: dict[str, float | None] = {}
                regular_session = sample_started < dt.datetime.combine(args.session_date, dt.time(13, 0), tzinfo=PACIFIC).astimezone(UTC)
                for symbol, (container, _port) in STRATEGIES.items():
                    value = snapshot_counter(metrics, container)
                    current_snapshots[symbol] = value
                    prior = previous_snapshots.get(symbol)
                    if value is not None and (prior is None or value > prior):
                        manifest["snapshot_success_counts"][symbol] += 1
                    elif regular_session and prior is not None:
                        violations.append(f"{symbol}:collector_snapshot_not_advanced")
                previous_snapshots = current_snapshots
                logs = log_summary(log_since)
                log_since = sample_started
                violations.extend(log_violations(logs))
                flap_events = readiness_flap_events(previous_ready, endpoints, sample_started, active_flaps)
                for event in flap_events:
                    append_jsonl(events_path, event)
                    if event["event"] == "readiness_flap_recovered":
                        manifest["readiness_flaps"].append(event)
                if any(
                    not ready and (sample_started - active_flaps.get(container, sample_started)).total_seconds() >= args.sample_seconds
                    for container, ready in previous_ready.items()
                ):
                    violations.append("strategy_or_gateway_unready_beyond_recovery_interval")
                diagnostic = None
                if index % args.diagnostic_every == 0:
                    diagnostic, diagnostic_errors = diagnostic_probe(
                        client,
                        args.session_date,
                        allow_opening_freshness=index == 0,
                    )
                    violations.extend(diagnostic_errors)
                if previous_sample_at is not None:
                    elapsed = (sample_started - previous_sample_at).total_seconds()
                    if elapsed > args.sample_seconds * 1.5:
                        manifest["missing_intervals"].append({"after_index": index - 1, "elapsed_seconds": elapsed})
                previous_sample_at = sample_started
                host = host_snapshot()
                violations.extend(host_violations(host))
                sample = {
                    "index": index,
                    "scheduled_utc": target.isoformat(),
                    "started_utc": sample_started.isoformat(),
                    "finished_utc": dt.datetime.now(UTC).isoformat(),
                    "identities": identities,
                    "candidates": candidates,
                    "endpoints": endpoints,
                    "metrics": metrics,
                    "host": host,
                    "collector_snapshot_counters": current_snapshots,
                    "log_summary": logs,
                    "diagnostic": diagnostic,
                    "violations": sorted(set(violations)),
                }
                append_jsonl(samples_path, sample)
                manifest["samples"].append({
                    "index": index,
                    "started_utc": sample["started_utc"],
                    "diagnostic": diagnostic is not None,
                    "violations": sample["violations"],
                })
                values = metrics[GATEWAY]["values"]
                if not first_gateway_metrics:
                    first_gateway_metrics = values
                last_gateway_metrics = values
                if violations:
                    manifest["violations"].extend(f"sample_{index}:{error}" for error in violations)
                    append_jsonl(events_path, {"event": "abort", "at_utc": dt.datetime.now(UTC).isoformat(), "sample": index, "violations": sorted(set(violations))})
                    break
                index += 1
                target += dt.timedelta(seconds=args.sample_seconds)

        manifest["post_close_flatness"] = flatness(args.flatness_tool, args.repo, args.session_date)
        if not manifest["post_close_flatness"].get("flat"):
            manifest["violations"].append("post_close:flatness_failed")
        _candidates, final_candidate_errors = candidate_observation()
        manifest["violations"].extend(f"post_close:{error}" for error in final_candidate_errors)
        manifest["normalization_counter"]["end"] = previous_counter
        if counter is not None and previous_counter is not None:
            manifest["normalization_counter"]["delta"] = previous_counter - counter
        manifest["request_metric_deltas"] = request_metric_delta(first_gateway_metrics, last_gateway_metrics)
    except Exception as exc:
        manifest["violations"].append(f"monitor:{type(exc).__name__}:{exc}")
        append_jsonl(events_path, {"event": "monitor_exception", "at_utc": dt.datetime.now(UTC).isoformat(), "error": type(exc).__name__})
    manifest["finished_utc"] = dt.datetime.now(UTC).isoformat()
    manifest["violations"] = sorted(set(manifest["violations"]))
    append_jsonl(events_path, {"event": "monitor_finished", "at_utc": manifest["finished_utc"], "conclusion": "PASS" if not manifest["violations"] else "FAIL"})
    finalize(root, manifest, args.launcher)
    return 0 if not manifest["violations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
