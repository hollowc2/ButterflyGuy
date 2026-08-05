"""Capture and verify redacted Docker configuration fingerprints for credential proof."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import importlib
import io
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tarfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

SCHEMA_VERSION = 1
OPERATOR_STATE_VERSION = 1
COMPOSE_CONFIG_HASH_LABEL = "com.docker.compose.config-hash"
STAGING_TMPFS_TARGET = "/app/.schwab-credential-proof-runtime"
STAGING_ARCHIVE_TARGET = f"{STAGING_TMPFS_TARGET}/reviewed.tar"
STAGING_SOURCE_TARGET = f"{STAGING_TMPFS_TARGET}/source"
MAX_CAPTURE_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 256 * 1024
MAX_RESULT_BYTES = 512
DEFAULT_COMMAND_TIMEOUT_SECONDS = 15
PROOF_TIMEOUT_SECONDS = 45
RESTORE_BUDGET_SECONDS = 120
APPROVAL_TIMEOUT_SECONDS = 120
HARD_RESTORE_SECONDS = 300
FRESH_ERROR_WINDOW_SECONDS = 30
_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")
_GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
_IMAGE_ID_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_PID_PATTERN = re.compile(r"[1-9][0-9]{0,9}")
_CONTAINER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
_UNIT_PATTERN = re.compile(r"butterfly-credential-proof-[0-9a-f]{12}-(?:hard|approval)")
_MATERIAL_FIELDS = (
    "cmd",
    "entrypoint",
    "working_dir",
    "user",
    "healthcheck",
    "env",
    "binds",
    "mounts",
    "ports",
    "network_mode",
    "networks",
    "readonly_rootfs",
    "restart_policy",
    "tmpfs",
    "cap_drop",
    "security_opt",
)
_FIELD_HASHES = frozenset((*_MATERIAL_FIELDS, "image"))
_SNAPSHOT_FIELDS = frozenset(
    {
        "schema_version",
        "configuration_fingerprint",
        "compose_config_hash",
        "field_hashes",
        "staging_tmpfs_present",
    }
)

_SERVICE_SPECS = {
    "spx": {
        "container": "butterfly_spx_app",
        "compose_service": "app_spx",
        "health_port": 8000,
        "process_marker": "butterfly_guy.scripts.run_live",
    },
    "ndx": {
        "container": "butterfly_ndx_app",
        "compose_service": "app_ndx",
        "health_port": 8001,
        "process_marker": "butterfly_guy.scripts.run_live",
    },
    "xsp": {
        "container": "butterfly_xsp_app",
        "compose_service": "app_xsp",
        "health_port": 8003,
        "process_marker": "butterfly_guy.scripts.run_live",
    },
    "candidate": {
        "container": "butterfly_spx_candidate_feed",
        "compose_service": "spx_candidate_feed",
        "health_port": None,
        "process_marker": "butterfly_guy.scripts.run_candidate_feed",
    },
}
_TRADING_SERVICES = ("spx", "ndx", "xsp")
_ALL_SERVICES = (*_TRADING_SERVICES, "candidate")
_HOST_CLIENT_MARKERS = (
    "auth_init.py",
    "backfill_equity_candles.py",
    "download_schwab_cache.py",
    "record_equity_market_data.py",
    "refresh_equity_universes.py",
    "report_broker_order_statuses.py",
    "run_collector.py",
    "run_morning_scan.py",
    "send_daily_report_card.py",
)
_KEEPALIVE_MARKER = "schwab_token_keepalive.py"
_CI_WORKER_MARKERS = ("Runner.Worker", "Agent.Worker")
_PROOF_MARKER = "probe_schwab_gateway_credentials.py"
_ERROR_MARKERS = ("error", "exception", "traceback", "critical", "failed")
_ARCHIVE_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "infra/docker-compose.yml",
    "infra/docker-compose.credential-proof-staging.yml",
    "src/butterfly_guy/__init__.py",
    "src/butterfly_guy/core/__init__.py",
    "src/butterfly_guy/core/logging.py",
    "src/butterfly_guy/schwab_gateway/__init__.py",
    "src/butterfly_guy/schwab_gateway/config.py",
    "src/butterfly_guy/schwab_gateway/credential_probe.py",
    "src/butterfly_guy/schwab_gateway/token_adapter.py",
    "src/butterfly_guy/schwab_gateway/token_manager.py",
    "src/butterfly_guy/scripts/__init__.py",
    "src/butterfly_guy/scripts/credential_proof_fingerprint.py",
    "src/butterfly_guy/scripts/probe_schwab_gateway_credentials.py",
)
_CHECK_NAMES = (
    "accepted_fingerprints",
    "field_hashes",
    "images",
    "compose_hashes",
    "health",
    "process_uniqueness",
    "candidate_ownership",
    "keepalive",
    "host_clients",
    "ci_workers",
    "compose_semantics",
    "compose_dry_run",
    "archive_provenance",
    "archive_sha256",
    "reviewed_compose_files",
    "native_smoke",
    "refusal_gate",
    "watchdog",
    "single_writer",
    "proof",
    "restoration_fingerprints",
    "restoration_health",
    "restoration_uniqueness",
    "restoration_ownership",
    "restoration_keepalive",
    "restoration_errors",
)
_CHECK_VALUES = frozenset({"pending", "pass", "fail", "invalid"})
_FAILURE_CHECK = {
    "archive_invalid": "archive_provenance",
    "archive_mismatch": "archive_sha256",
    "baseline_mismatch": "accepted_fingerprints",
    "candidate_ownership_invalid": "candidate_ownership",
    "ci_worker_active": "ci_workers",
    "compose_dry_run_invalid": "compose_dry_run",
    "compose_semantics_invalid": "compose_semantics",
    "credential_output_invalid": "proof",
    "credential_proof_failed": "proof",
    "health_invalid": "health",
    "host_client_active": "host_clients",
    "keepalive_active": "keepalive",
    "native_smoke_failed": "native_smoke",
    "process_uniqueness_invalid": "process_uniqueness",
    "provenance_invalid": "archive_provenance",
    "single_writer_invalid": "single_writer",
    "staging_invalid": "field_hashes",
    "watchdog_invalid": "watchdog",
}
_RESULT_CODES = frozenset(
    {
        "approval_1_ready",
        "approval_2_required",
        "approval_2_timeout",
        "archive_created",
        "archive_invalid",
        "archive_mismatch",
        "baseline_mismatch",
        "candidate_ownership_invalid",
        "ci_worker_active",
        "compose_dry_run_invalid",
        "compose_semantics_invalid",
        "credential_output_invalid",
        "credential_proof_failed",
        "credential_proof_passed",
        "credential_refused",
        "docker_inspect_invalid",
        "docker_top_invalid",
        "evidence_invalid",
        "fingerprint_failed",
        "health_invalid",
        "host_client_active",
        "internal_failure",
        "invalid_arguments",
        "keepalive_active",
        "native_smoke_failed",
        "native_smoke_passed",
        "operator_state_invalid",
        "process_uniqueness_invalid",
        "provenance_invalid",
        "restoration_failed_paused",
        "restoration_passed",
        "snapshot_captured",
        "snapshot_verified",
        "single_writer_invalid",
        "signal_invalid",
        "signal_passed",
        "staging_invalid",
        "subprocess_failed",
        "subprocess_output_invalid",
        "subprocess_timeout",
        "watchdog_invalid",
        "watchdog_armed",
        "watchdog_cancelled",
        "watchdog_ready",
        "refusal_gate_passed",
    }
)


class OperatorFailure(RuntimeError):  # noqa: N818 - fixed operator result, not public API
    """A fixed, non-sensitive operator failure."""

    def __init__(self, code: str):
        if code not in _RESULT_CODES:
            code = "internal_failure"
        super().__init__(code)
        self.code = code


class SafeArgumentParser(argparse.ArgumentParser):
    """Argparse variant that never echoes arguments, paths, or parser internals."""

    def error(self, message: str) -> None:
        del message
        _emit("error", "invalid_arguments")
        raise SystemExit(2)


@dataclass(frozen=True)
class CapturedProcess:
    returncode: int
    stdout: str
    stderr: str


def _emit(status_value: str, code: str, **fields: object) -> None:
    if status_value not in {"ok", "error"} or code not in _RESULT_CODES:
        status_value = "error"
        code = "internal_failure"
        fields = {}
    payload = {"code": code, **fields, "status": status_value}
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode()) > MAX_RESULT_BYTES:
        encoded = '{"code":"internal_failure","status":"error"}'
    print(encoded)


def _run(
    command: Sequence[str],
    *,
    timeout: int = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    input_bytes: bytes | None = None,
) -> CapturedProcess:
    try:
        result = subprocess.run(
            list(command),
            input=input_bytes,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise OperatorFailure("subprocess_timeout") from None
    except Exception:
        raise OperatorFailure("subprocess_failed") from None
    stdout_bytes = result.stdout or b""
    stderr_bytes = result.stderr or b""
    if len(stdout_bytes) > MAX_CAPTURE_BYTES or len(stderr_bytes) > MAX_CAPTURE_BYTES:
        raise OperatorFailure("subprocess_output_invalid")
    try:
        stdout = stdout_bytes.decode("utf-8", errors="strict")
        stderr = stderr_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise OperatorFailure("subprocess_output_invalid") from None
    return CapturedProcess(result.returncode, stdout, stderr)


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _sorted_options(value: object) -> str:
    if not isinstance(value, str) or not value:
        return "" if value is None else str(value)
    return ",".join(sorted(part for part in value.split(",") if part))


def _canonical_mount(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("invalid Docker inspect")
    return {
        "Type": value.get("Type"),
        "Source": value.get("Source"),
        "Destination": value.get("Destination"),
        "Mode": _sorted_options(value.get("Mode")),
        "RW": value.get("RW"),
        "Propagation": value.get("Propagation"),
    }


def _canonical_ports(value: object) -> dict[str, list[dict[str, object]]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("invalid Docker inspect")
    result: dict[str, list[dict[str, object]]] = {}
    for port, bindings in value.items():
        if not isinstance(port, str) or not isinstance(bindings, list):
            raise ValueError("invalid Docker inspect")
        normalized: list[dict[str, object]] = []
        for binding in bindings:
            if not isinstance(binding, dict):
                raise ValueError("invalid Docker inspect")
            normalized.append(
                {
                    "HostIp": binding.get("HostIp"),
                    "HostPort": binding.get("HostPort"),
                }
            )
        result[port] = sorted(normalized, key=_canonical_sort_key)
    return result


def _canonical_sort_key(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _configuration_material(
    value: dict[str, Any], *, remove_staging_tmpfs: bool = False
) -> dict[str, object]:
    config = value.get("Config") or {}
    host = value.get("HostConfig") or {}
    network_settings = value.get("NetworkSettings") or {}
    if not all(isinstance(item, dict) for item in (config, host, network_settings)):
        raise ValueError("invalid Docker inspect")

    raw_mounts = value.get("Mounts") or []
    raw_networks = network_settings.get("Networks") or {}
    raw_tmpfs = host.get("Tmpfs") or {}
    if not isinstance(raw_mounts, list) or not isinstance(raw_networks, dict):
        raise ValueError("invalid Docker inspect")
    if not isinstance(raw_tmpfs, dict):
        raise ValueError("invalid Docker inspect")

    mounts = [_canonical_mount(mount) for mount in raw_mounts]
    tmpfs = {str(target): _sorted_options(options) for target, options in raw_tmpfs.items()}
    if remove_staging_tmpfs:
        mounts = [
            mount
            for mount in mounts
            if mount.get("Destination") != STAGING_TMPFS_TARGET
        ]
        tmpfs.pop(STAGING_TMPFS_TARGET, None)

    binds = host.get("Binds") or []
    env = config.get("Env") or []
    cap_drop = host.get("CapDrop") or []
    security_opt = host.get("SecurityOpt") or []
    if not all(isinstance(item, list) for item in (binds, env, cap_drop, security_opt)):
        raise ValueError("invalid Docker inspect")

    return {
        "cmd": config.get("Cmd"),
        "entrypoint": config.get("Entrypoint"),
        "working_dir": config.get("WorkingDir"),
        "user": config.get("User"),
        "healthcheck": config.get("Healthcheck"),
        "env": sorted(env),
        "binds": sorted(binds),
        "mounts": sorted(mounts, key=_canonical_sort_key),
        "ports": _canonical_ports(host.get("PortBindings")),
        "network_mode": host.get("NetworkMode"),
        "networks": sorted(raw_networks),
        "readonly_rootfs": host.get("ReadonlyRootfs"),
        "restart_policy": host.get("RestartPolicy"),
        "tmpfs": tmpfs,
        "cap_drop": sorted(cap_drop),
        "security_opt": sorted(security_opt),
    }


def _compose_config_hash(value: dict[str, Any]) -> str:
    config = value.get("Config") or {}
    labels = config.get("Labels") or {}
    if not isinstance(config, dict) or not isinstance(labels, dict):
        raise ValueError("invalid Docker inspect")
    compose_hash = labels.get(COMPOSE_CONFIG_HASH_LABEL)
    if not isinstance(compose_hash, str) or _HASH_PATTERN.fullmatch(compose_hash) is None:
        raise ValueError("invalid Docker inspect")
    return compose_hash


def _staging_tmpfs_present(value: dict[str, Any]) -> bool:
    host = value.get("HostConfig") or {}
    tmpfs = host.get("Tmpfs") or {}
    mounts = value.get("Mounts") or []
    if not isinstance(host, dict) or not isinstance(tmpfs, dict) or not isinstance(mounts, list):
        raise ValueError("invalid Docker inspect")
    return STAGING_TMPFS_TARGET in tmpfs or any(
        isinstance(mount, dict) and mount.get("Destination") == STAGING_TMPFS_TARGET
        for mount in mounts
    )


def build_record(
    value: dict[str, Any], *, remove_staging_tmpfs: bool = False
) -> dict[str, object]:
    """Build a bounded record containing hashes and booleans, never raw configuration values."""
    if not isinstance(value, dict):
        raise ValueError("invalid Docker inspect")
    material = _configuration_material(value, remove_staging_tmpfs=remove_staging_tmpfs)
    image_material = {
        "runtime_id": value.get("Image"),
        "configured_reference": (value.get("Config") or {}).get("Image"),
    }
    if not all(isinstance(item, str) and item for item in image_material.values()):
        raise ValueError("invalid Docker inspect")
    field_hashes = {field: _digest(material[field]) for field in _MATERIAL_FIELDS}
    field_hashes["image"] = _digest(image_material)
    return {
        "schema_version": SCHEMA_VERSION,
        "configuration_fingerprint": _digest(material),
        "compose_config_hash": _compose_config_hash(value),
        "field_hashes": field_hashes,
        "staging_tmpfs_present": (
            False if remove_staging_tmpfs else _staging_tmpfs_present(value)
        ),
    }


def _valid_record(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != _SNAPSHOT_FIELDS:
        return False
    hashes = value.get("field_hashes")
    return bool(
        value.get("schema_version") == SCHEMA_VERSION
        and isinstance(value.get("staging_tmpfs_present"), bool)
        and isinstance(hashes, dict)
        and set(hashes) == _FIELD_HASHES
        and all(isinstance(item, str) and _HASH_PATTERN.fullmatch(item) for item in hashes.values())
        and isinstance(value.get("configuration_fingerprint"), str)
        and _HASH_PATTERN.fullmatch(value["configuration_fingerprint"])
        and isinstance(value.get("compose_config_hash"), str)
        and _HASH_PATTERN.fullmatch(value["compose_config_hash"])
    )


def records_match_exactly(baseline: dict[str, object], current: dict[str, object]) -> bool:
    return _valid_record(baseline) and _valid_record(current) and baseline == current


def _approved_staging_tmpfs(value: dict[str, Any]) -> bool:
    host = value.get("HostConfig") or {}
    tmpfs = host.get("Tmpfs") or {}
    mounts = value.get("Mounts") or []
    if not isinstance(host, dict) or not isinstance(tmpfs, dict) or not isinstance(mounts, list):
        return False
    options = set(str(tmpfs.get(STAGING_TMPFS_TARGET, "")).split(","))
    required = {"rw", "exec", "nosuid", "nodev", "mode=1777"}
    sizes = options.intersection({"size=256m", "size=268435456"})
    if not required.issubset(options) or len(sizes) != 1 or options != required | sizes:
        return False
    target_mounts = [
        mount
        for mount in mounts
        if isinstance(mount, dict) and mount.get("Destination") == STAGING_TMPFS_TARGET
    ]
    return len(target_mounts) <= 1 and all(
        mount.get("Type") == "tmpfs" and mount.get("RW") is True
        for mount in target_mounts
    )


def staging_matches_baseline(
    staged_inspect: dict[str, Any], baseline: dict[str, object]
) -> bool:
    if (
        not _valid_record(baseline)
        or baseline["staging_tmpfs_present"] is not False
        or not _approved_staging_tmpfs(staged_inspect)
    ):
        return False
    current = build_record(staged_inspect, remove_staging_tmpfs=True)
    return bool(
        current["configuration_fingerprint"] == baseline["configuration_fingerprint"]
        and current["field_hashes"] == baseline["field_hashes"]
        and current["compose_config_hash"] != baseline["compose_config_hash"]
        and current["staging_tmpfs_present"] is False
    )


def inspect_container(name: str) -> dict[str, Any]:
    if _CONTAINER_PATTERN.fullmatch(name) is None:
        raise OperatorFailure("docker_inspect_invalid")
    result = _run(["docker", "inspect", "--type", "container", name], timeout=10)
    if result.returncode != 0 or result.stderr:
        raise OperatorFailure("docker_inspect_invalid")
    try:
        parsed = json.loads(result.stdout)
    except (TypeError, ValueError):
        raise OperatorFailure("docker_inspect_invalid") from None
    if not isinstance(parsed, list) or len(parsed) != 1 or not isinstance(parsed[0], dict):
        raise OperatorFailure("docker_inspect_invalid")
    return parsed[0]


def write_snapshot(path: Path, record: dict[str, object]) -> None:
    if not _valid_record(record):
        raise ValueError("invalid snapshot")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        payload = json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n"
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def read_snapshot(path: Path) -> dict[str, object]:
    file_stat = path.lstat()
    if not stat.S_ISREG(file_stat.st_mode) or stat.S_IMODE(file_stat.st_mode) != 0o600:
        raise ValueError("invalid snapshot")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, encoding="utf-8") as handle:
            descriptor = -1
            value = json.load(handle)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if not _valid_record(value):
        raise ValueError("invalid snapshot")
    return value


_STATE_FIELDS = frozenset(
    {
        "schema_version",
        "approved_sha",
        "archive_sha256",
        "session_id",
        "phase",
        "failure_code",
        "approval_1",
        "checks",
        "baseline",
        "cron",
        "watchdog",
        "quiescence",
        "proof",
        "restoration",
    }
)
_STATE_PHASES = frozenset(
    {
        "new",
        "approval_1_ready",
        "approval_1_running",
        "approval_2_pending",
        "approval_2_running",
        "restoring",
        "restored",
        "failed",
    }
)
_WATCHDOG_VALUES = frozenset({"pending", "armed", "cancelled", "fired", "fail"})


def _new_state(approved_sha: str) -> dict[str, Any]:
    if _GIT_SHA_PATTERN.fullmatch(approved_sha) is None:
        raise OperatorFailure("invalid_arguments")
    session_id = hashlib.sha256(
        f"{approved_sha}:{os.getpid()}:{time.time_ns()}".encode()
    ).hexdigest()[:12]
    return {
        "schema_version": OPERATOR_STATE_VERSION,
        "approved_sha": approved_sha,
        "archive_sha256": None,
        "session_id": session_id,
        "phase": "new",
        "failure_code": None,
        "approval_1": {
            "reference_sha256": None,
            "window_start": None,
            "window_end": None,
        },
        "checks": {name: "pending" for name in _CHECK_NAMES},
        "baseline": {
            name: {"container_id": None, "image_id": None, "record": None}
            for name in _ALL_SERVICES
        },
        "cron": {
            "sha256": None,
            "keepalive_entries": None,
            "present": None,
            "disabled": False,
            "restored": False,
        },
        "watchdog": {
            "hard": "pending",
            "approval": "pending",
            "hard_deadline": None,
            "approval_deadline": None,
        },
        "quiescence": {"started": None, "spx_pid": None},
        "proof": {
            "approval_reference_sha256": None,
            "attempted": False,
            "attempt_count": 0,
            "started": None,
            "ended": None,
            "result": "pending",
            "quote_count": None,
            "token_state": None,
            "reason_code": None,
            "retry_count": 0,
            "information_exposure": "pending",
        },
        "restoration": {
            "result": "pending",
            "completed": None,
            "error_counts": {name: None for name in _TRADING_SERVICES},
        },
    }


def _valid_state(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != _STATE_FIELDS:
        return False
    if value.get("schema_version") != OPERATOR_STATE_VERSION:
        return False
    if not isinstance(value.get("approved_sha"), str) or _GIT_SHA_PATTERN.fullmatch(
        value["approved_sha"]
    ) is None:
        return False
    archive_sha256 = value.get("archive_sha256")
    if archive_sha256 is not None and (
        not isinstance(archive_sha256, str) or _HASH_PATTERN.fullmatch(archive_sha256) is None
    ):
        return False
    session_id = value.get("session_id")
    if not isinstance(session_id, str) or re.fullmatch(r"[0-9a-f]{12}", session_id) is None:
        return False
    if value.get("phase") not in _STATE_PHASES:
        return False
    failure_code = value.get("failure_code")
    if failure_code is not None and failure_code not in _RESULT_CODES:
        return False
    approval_1 = value.get("approval_1")
    if not isinstance(approval_1, dict) or set(approval_1) != {
        "reference_sha256",
        "window_start",
        "window_end",
    }:
        return False
    reference_hash = approval_1["reference_sha256"]
    if reference_hash is not None and (
        not isinstance(reference_hash, str) or _HASH_PATTERN.fullmatch(reference_hash) is None
    ):
        return False
    for boundary in (approval_1["window_start"], approval_1["window_end"]):
        if boundary is not None and (not isinstance(boundary, int) or boundary <= 0):
            return False
    if (
        approval_1["window_start"] is not None
        and approval_1["window_end"] is not None
        and approval_1["window_start"] >= approval_1["window_end"]
    ):
        return False
    checks = value.get("checks")
    if (
        not isinstance(checks, dict)
        or set(checks) != set(_CHECK_NAMES)
        or any(item not in _CHECK_VALUES for item in checks.values())
    ):
        return False
    baseline = value.get("baseline")
    if not isinstance(baseline, dict) or set(baseline) != set(_ALL_SERVICES):
        return False
    for entry in baseline.values():
        if not isinstance(entry, dict) or set(entry) != {"container_id", "image_id", "record"}:
            return False
        container_id = entry["container_id"]
        image_id = entry["image_id"]
        record = entry["record"]
        if container_id is not None and (
            not isinstance(container_id, str)
            or re.fullmatch(r"[0-9a-f]{64}", container_id) is None
        ):
            return False
        if image_id is not None and (
            not isinstance(image_id, str) or _IMAGE_ID_PATTERN.fullmatch(image_id) is None
        ):
            return False
        if record is not None and not _valid_record(record):
            return False
    cron = value.get("cron")
    if not isinstance(cron, dict) or set(cron) != {
        "sha256",
        "keepalive_entries",
        "present",
        "disabled",
        "restored",
    }:
        return False
    if cron["sha256"] is not None and (
        not isinstance(cron["sha256"], str) or _HASH_PATTERN.fullmatch(cron["sha256"]) is None
    ):
        return False
    if cron["keepalive_entries"] is not None and (
        not isinstance(cron["keepalive_entries"], int) or cron["keepalive_entries"] < 0
    ):
        return False
    if cron["present"] is not None and not isinstance(cron["present"], bool):
        return False
    if not isinstance(cron["disabled"], bool) or not isinstance(cron["restored"], bool):
        return False
    watchdog = value.get("watchdog")
    if not isinstance(watchdog, dict) or set(watchdog) != {
        "hard",
        "approval",
        "hard_deadline",
        "approval_deadline",
    }:
        return False
    if watchdog["hard"] not in _WATCHDOG_VALUES or watchdog["approval"] not in _WATCHDOG_VALUES:
        return False
    for deadline in (watchdog["hard_deadline"], watchdog["approval_deadline"]):
        if deadline is not None and (not isinstance(deadline, int) or deadline <= 0):
            return False
    quiescence = value.get("quiescence")
    if not isinstance(quiescence, dict) or set(quiescence) != {"started", "spx_pid"}:
        return False
    if quiescence["started"] is not None and (
        not isinstance(quiescence["started"], int) or quiescence["started"] <= 0
    ):
        return False
    if quiescence["spx_pid"] is not None and (
        not isinstance(quiescence["spx_pid"], int) or quiescence["spx_pid"] <= 0
    ):
        return False
    proof = value.get("proof")
    if not isinstance(proof, dict) or set(proof) != {
        "approval_reference_sha256",
        "attempted",
        "attempt_count",
        "started",
        "ended",
        "result",
        "quote_count",
        "token_state",
        "reason_code",
        "retry_count",
        "information_exposure",
    }:
        return False
    approval_hash = proof["approval_reference_sha256"]
    if approval_hash is not None and (
        not isinstance(approval_hash, str) or _HASH_PATTERN.fullmatch(approval_hash) is None
    ):
        return False
    if not isinstance(proof["attempted"], bool) or proof["attempt_count"] not in {0, 1}:
        return False
    if proof["attempt_count"] != int(proof["attempted"]):
        return False
    for timestamp in (proof["started"], proof["ended"]):
        if timestamp is not None and (not isinstance(timestamp, int) or timestamp <= 0):
            return False
    if proof["result"] not in {"pending", "pass", "fail", "invalid"}:
        return False
    if proof["quote_count"] not in {None, 1} or proof["token_state"] not in {None, "ready"}:
        return False
    if proof["reason_code"] is not None and proof["reason_code"] not in _RESULT_CODES:
        return False
    if proof["retry_count"] != 0 or proof["information_exposure"] not in {
        "pending",
        "pass",
        "fail",
        "invalid",
    }:
        return False
    if proof["started"] is not None and proof["ended"] is not None:
        if proof["started"] > proof["ended"]:
            return False
    if proof["result"] == "pass" and not (
        proof["attempted"]
        and proof["quote_count"] == 1
        and proof["token_state"] == "ready"
        and proof["reason_code"] == "credential_proof_passed"
        and proof["information_exposure"] == "pass"
    ):
        return False
    restoration = value.get("restoration")
    if not isinstance(restoration, dict) or set(restoration) != {
        "result",
        "completed",
        "error_counts",
    }:
        return False
    if restoration["result"] not in {"pending", "pass", "fail"}:
        return False
    if restoration["completed"] is not None and (
        not isinstance(restoration["completed"], int) or restoration["completed"] <= 0
    ):
        return False
    error_counts = restoration["error_counts"]
    return bool(
        isinstance(error_counts, dict)
        and set(error_counts) == set(_TRADING_SERVICES)
        and all(
            item is None or (isinstance(item, int) and item >= 0)
            for item in error_counts.values()
        )
    )


def _private_open_flags(*, write: bool, exclusive: bool = False) -> int:
    flags = os.O_WRONLY if write else os.O_RDONLY
    if write:
        flags |= os.O_CREAT
    if exclusive:
        flags |= os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _write_private_bytes(path: Path, payload: bytes, *, exclusive: bool = True) -> None:
    descriptor = os.open(path, _private_open_flags(write=True, exclusive=exclusive), 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _read_private_bytes(path: Path, *, max_bytes: int = MAX_CAPTURE_BYTES) -> bytes:
    file_stat = path.lstat()
    if not stat.S_ISREG(file_stat.st_mode) or stat.S_IMODE(file_stat.st_mode) != 0o600:
        raise OperatorFailure("evidence_invalid")
    if file_stat.st_size > max_bytes:
        raise OperatorFailure("evidence_invalid")
    descriptor = os.open(path, _private_open_flags(write=False))
    try:
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            payload = handle.read(max_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(payload) > max_bytes:
        raise OperatorFailure("evidence_invalid")
    return payload


def _write_state_new(path: Path, value: dict[str, Any]) -> None:
    if not _valid_state(value):
        raise OperatorFailure("operator_state_invalid")
    payload = (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()
    _write_private_bytes(path, payload)


def _replace_state(path: Path, value: dict[str, Any]) -> None:
    if not _valid_state(value):
        raise OperatorFailure("operator_state_invalid")
    current = path.lstat()
    if not stat.S_ISREG(current.st_mode) or stat.S_IMODE(current.st_mode) != 0o600:
        raise OperatorFailure("operator_state_invalid")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()
    try:
        _write_private_bytes(temporary, payload)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _read_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read_private_bytes(path).decode("utf-8", errors="strict"))
    except (OperatorFailure, UnicodeDecodeError, ValueError):
        raise OperatorFailure("operator_state_invalid") from None
    if not _valid_state(value):
        raise OperatorFailure("operator_state_invalid")
    return value


@contextlib.contextmanager
def _state_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_name(f".{path.name}.lock")
    descriptor = os.open(lock_path, _private_open_flags(write=True), 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _set_failure(
    state_path: Path,
    state: dict[str, Any],
    code: str,
    *,
    check: str | None = None,
    invalidate_pending: bool = False,
) -> None:
    if check is None:
        check = _FAILURE_CHECK.get(code)
    if check in state["checks"]:
        state["checks"][check] = "fail"
    if invalidate_pending:
        for name, result in state["checks"].items():
            if result == "pending" and not name.startswith("restoration_"):
                state["checks"][name] = "invalid"
    state["failure_code"] = code if code in _RESULT_CODES else "internal_failure"
    state["phase"] = "failed"
    _replace_state(state_path, state)


def _container_identity(inspected: dict[str, Any]) -> tuple[str, str]:
    container_id = inspected.get("Id")
    image_id = inspected.get("Image")
    if (
        not isinstance(container_id, str)
        or re.fullmatch(r"[0-9a-f]{64}", container_id) is None
        or not isinstance(image_id, str)
        or _IMAGE_ID_PATTERN.fullmatch(image_id) is None
    ):
        raise OperatorFailure("docker_inspect_invalid")
    return container_id, image_id


def _container_running(inspected: dict[str, Any], *, paused: bool = False) -> bool:
    state = inspected.get("State")
    return bool(
        isinstance(state, dict)
        and state.get("Status") == "running"
        and state.get("Running") is True
        and state.get("Paused") is paused
    )


def _health_ok(service: str) -> bool:
    spec = _SERVICE_SPECS[service]
    port = spec["health_port"]
    if not isinstance(port, int):
        return True
    result = _run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--max-time",
            "5",
            f"http://127.0.0.1:{port}/health",
        ],
        timeout=8,
    )
    if result.returncode != 0 or result.stderr:
        return False
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError):
        return False
    if not isinstance(payload, dict) or set(payload) != {
        "status",
        "service",
        "timestamp",
        "uptime_seconds",
    }:
        return False
    return bool(
        payload.get("status") == "ok"
        and isinstance(payload.get("service"), str)
        and len(payload["service"]) <= 16
        and isinstance(payload.get("timestamp"), str)
        and len(payload["timestamp"]) <= 32
        and isinstance(payload.get("uptime_seconds"), (int, float))
    )


def _docker_top_rows(container: str) -> list[tuple[int, str]]:
    result = _run(["docker", "top", container, "-eo", "pid,args"], timeout=10)
    if result.returncode != 0 or result.stderr:
        raise OperatorFailure("docker_top_invalid")
    lines = result.stdout.splitlines()
    if not lines or lines[0].split() != ["PID", "COMMAND"]:
        raise OperatorFailure("docker_top_invalid")
    rows: list[tuple[int, str]] = []
    for line in lines[1:]:
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or _PID_PATTERN.fullmatch(parts[0]) is None or not parts[1]:
            raise OperatorFailure("docker_top_invalid")
        rows.append((int(parts[0]), parts[1]))
    return rows


def _unique_service_pid(service: str, *, allow_proof: bool = False) -> int:
    spec = _SERVICE_SPECS[service]
    rows = _docker_top_rows(str(spec["container"]))
    marker = str(spec["process_marker"])
    application = [row for row in rows if marker in row[1]]
    proof = [row for row in rows if _PROOF_MARKER in row[1]]
    if len(application) != 1 or (proof and not allow_proof):
        raise OperatorFailure("process_uniqueness_invalid")
    if any(marker not in command and _PROOF_MARKER not in command for _, command in rows):
        raise OperatorFailure("process_uniqueness_invalid")
    return application[0][0]


def _candidate_read_only(inspected: dict[str, Any]) -> bool:
    mounts = inspected.get("Mounts")
    if not isinstance(mounts, list):
        return False
    token_mounts = [
        mount
        for mount in mounts
        if isinstance(mount, dict) and mount.get("Destination") == "/app/tokens.json"
    ]
    return bool(
        len(token_mounts) == 1
        and token_mounts[0].get("Type") == "bind"
        and token_mounts[0].get("RW") is False
        and token_mounts[0].get("Mode") == "ro"
    )


def _matching_host_processes(marker: str) -> list[int]:
    result = _run(["pgrep", "-af", marker], timeout=5)
    if result.returncode == 1 and not result.stdout and not result.stderr:
        return []
    if result.returncode != 0 or result.stderr:
        raise OperatorFailure("subprocess_failed")
    pids: list[int] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or _PID_PATTERN.fullmatch(parts[0]) is None or marker not in parts[1]:
            raise OperatorFailure("subprocess_output_invalid")
        pids.append(int(parts[0]))
    return pids


def _require_no_host_writers() -> None:
    if _matching_host_processes(_KEEPALIVE_MARKER):
        raise OperatorFailure("keepalive_active")
    if any(_matching_host_processes(marker) for marker in _HOST_CLIENT_MARKERS):
        raise OperatorFailure("host_client_active")
    if any(_matching_host_processes(marker) for marker in _CI_WORKER_MARKERS):
        raise OperatorFailure("ci_worker_active")


def _require_no_unowned_runtime_processes(allowed_pids: Sequence[int]) -> None:
    allowed = set(allowed_pids)
    for marker in {
        str(_SERVICE_SPECS["spx"]["process_marker"]),
        str(_SERVICE_SPECS["candidate"]["process_marker"]),
    }:
        if any(pid not in allowed for pid in _matching_host_processes(marker)):
            raise OperatorFailure("host_client_active")


def _normalize_compose(value: object, parent_key: str = "") -> object:
    if isinstance(value, dict):
        return {
            key: _normalize_compose(item, key)
            for key, item in sorted(value.items(), key=lambda pair: pair[0])
        }
    if isinstance(value, list):
        normalized = [_normalize_compose(item, parent_key) for item in value]
        if parent_key in {
            "cap_drop",
            "depends_on",
            "networks",
            "security_opt",
            "tmpfs",
            "volumes",
        }:
            return sorted(normalized, key=_canonical_sort_key)
        return normalized
    return value


def _compose_json(files: Sequence[Path]) -> dict[str, Any]:
    command = ["docker", "compose"]
    for path in files:
        command.extend(["-f", str(path)])
    command.extend(["config", "--format", "json", "--no-interpolate"])
    result = _run(command, timeout=20)
    if result.returncode != 0 or result.stderr:
        raise OperatorFailure("compose_semantics_invalid")
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError):
        raise OperatorFailure("compose_semantics_invalid") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("services"), dict):
        raise OperatorFailure("compose_semantics_invalid")
    return payload


def _approved_tmpfs_entry(value: object) -> bool:
    if not isinstance(value, str):
        return False
    target, separator, raw_options = value.partition(":")
    if target != STAGING_TMPFS_TARGET or not separator:
        return False
    options = set(raw_options.split(","))
    required = {"rw", "exec", "nosuid", "nodev", "mode=1777"}
    sizes = options.intersection({"size=256m", "size=268435456"})
    return bool(len(sizes) == 1 and options == required | sizes)


def _validate_compose_semantics(base_path: Path, staging_path: Path) -> None:
    base = _compose_json([base_path])
    combined = _compose_json([base_path, staging_path])
    base_services = base.get("services")
    combined_services = combined.get("services")
    if (
        not isinstance(base_services, dict)
        or not isinstance(combined_services, dict)
        or set(base_services) != set(combined_services)
        or "app_spx" not in combined_services
    ):
        raise OperatorFailure("compose_semantics_invalid")
    staged_service = combined_services["app_spx"]
    if not isinstance(staged_service, dict):
        raise OperatorFailure("compose_semantics_invalid")
    tmpfs = staged_service.get("tmpfs")
    if not isinstance(tmpfs, list):
        raise OperatorFailure("compose_semantics_invalid")
    additions = [item for item in tmpfs if _approved_tmpfs_entry(item)]
    if len(additions) != 1:
        raise OperatorFailure("compose_semantics_invalid")
    staged_service["tmpfs"] = [item for item in tmpfs if not _approved_tmpfs_entry(item)]
    if _normalize_compose(base) != _normalize_compose(combined):
        raise OperatorFailure("compose_semantics_invalid")


def _validate_compose_dry_run(base_path: Path, staging_path: Path) -> None:
    command = [
        "docker",
        "compose",
        "-f",
        str(base_path),
        "-f",
        str(staging_path),
        "--dry-run",
        "up",
        "-d",
        "--no-deps",
        "--no-build",
        "--pull",
        "never",
        "--force-recreate",
        "app_spx",
    ]
    result = _run(command, timeout=30)
    if result.returncode != 0:
        raise OperatorFailure("compose_dry_run_invalid")
    _validate_compose_action_output(result, "compose_dry_run_invalid")
    combined = f"{result.stdout}\n{result.stderr}"
    lowered = combined.lower()
    forbidden = (" pull", "pulling", " build", "building", " volume ", " network ")
    if any(marker in lowered for marker in forbidden):
        raise OperatorFailure("compose_dry_run_invalid")
    container_lines = [line for line in combined.splitlines() if "container" in line.lower()]
    if not container_lines or any(
        "butterfly_spx_app" not in line for line in container_lines
    ):
        raise OperatorFailure("compose_dry_run_invalid")
    for service in ("app_ndx", "app_xsp", "spx_candidate_feed"):
        if service in combined:
            raise OperatorFailure("compose_dry_run_invalid")


def _validate_compose_action_output(result: CapturedProcess, failure_code: str) -> None:
    combined = f"{result.stdout}\n{result.stderr}"
    container_lines = 0
    for raw_line in combined.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw_line).strip()
        if not line:
            continue
        lowered = line.casefold()
        if "container" in lowered:
            container_lines += 1
            allowed_actions = (
                "create",
                "created",
                "recreate",
                "recreated",
                "remove",
                "removed",
                "start",
                "started",
                "stop",
                "stopped",
            )
            if "butterfly_spx_app" not in line or not any(
                action in lowered for action in allowed_actions
            ):
                raise OperatorFailure(failure_code)
        elif "running" not in lowered or not line.startswith("["):
            raise OperatorFailure(failure_code)
    if container_lines == 0:
        raise OperatorFailure(failure_code)


def _compose_service_hash(base_path: Path) -> str:
    result = _run(
        ["docker", "compose", "-f", str(base_path), "config", "--hash", "app_spx"],
        timeout=20,
    )
    parts = result.stdout.strip().split()
    if (
        result.returncode != 0
        or result.stderr
        or len(parts) != 2
        or parts[0] != "app_spx"
        or _HASH_PATTERN.fullmatch(parts[1]) is None
    ):
        raise OperatorFailure("compose_semantics_invalid")
    return parts[1]


def _require_base_image(base_path: Path, expected_image_id: str) -> None:
    images = _run(
        ["docker", "compose", "-f", str(base_path), "config", "--images", "app_spx"],
        timeout=20,
    )
    references = images.stdout.splitlines()
    if (
        images.returncode != 0
        or images.stderr
        or len(references) != 1
        or not references[0]
        or len(references[0]) > 256
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:-]{0,255}", references[0]) is None
    ):
        raise OperatorFailure("compose_semantics_invalid")
    inspected = _run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", references[0]],
        timeout=10,
    )
    if (
        inspected.returncode != 0
        or inspected.stderr
        or inspected.stdout.strip() != expected_image_id
    ):
        raise OperatorFailure("compose_semantics_invalid")


def _sha256_file(path: Path, *, max_bytes: int = 8 * 1024 * 1024) -> str:
    file_stat = path.lstat()
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size > max_bytes:
        raise OperatorFailure("archive_invalid")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_archive(path: Path, approved_sha: str, expected_sha256: str | None) -> str:
    if _GIT_SHA_PATTERN.fullmatch(approved_sha) is None:
        raise OperatorFailure("provenance_invalid")
    archive_sha256 = _sha256_file(path)
    if expected_sha256 is not None and archive_sha256 != expected_sha256:
        raise OperatorFailure("archive_mismatch")
    payload = path.read_bytes()
    commit_result = _run(["git", "get-tar-commit-id"], input_bytes=payload, timeout=10)
    if (
        commit_result.returncode != 0
        or commit_result.stderr
        or commit_result.stdout.strip() != approved_sha
    ):
        raise OperatorFailure("provenance_invalid")
    try:
        with tarfile.open(path, mode="r:") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError):
        raise OperatorFailure("archive_invalid") from None
    names = []
    for member in members:
        name = member.name.rstrip("/")
        if member.isdir():
            continue
        if not member.isfile() or name.startswith("/") or ".." in Path(name).parts:
            raise OperatorFailure("archive_invalid")
        names.append(name)
    if set(names) != set(_ARCHIVE_PATHS) or len(names) != len(_ARCHIVE_PATHS):
        raise OperatorFailure("archive_invalid")
    return archive_sha256


def _create_archive(path: Path, approved_sha: str) -> str:
    if _GIT_SHA_PATTERN.fullmatch(approved_sha) is None or path.exists():
        raise OperatorFailure("archive_invalid")
    previous_umask = os.umask(0o077)
    try:
        try:
            result = _run(
                [
                    "git",
                    "archive",
                    "--format=tar",
                    f"--output={path}",
                    approved_sha,
                    "--",
                    *_ARCHIVE_PATHS,
                ],
                timeout=30,
            )
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
            raise
    finally:
        os.umask(previous_umask)
    if result.returncode != 0 or result.stdout or result.stderr:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        raise OperatorFailure("archive_invalid")
    path.chmod(0o600)
    return _validate_archive(path, approved_sha, None)


def _capture_crontab(path: Path) -> tuple[str, int, bool]:
    result = _run(["crontab", "-l"], timeout=10)
    if result.returncode == 1 and not result.stdout:
        payload = b""
        present = False
    elif result.returncode == 0 and not result.stderr:
        payload = result.stdout.encode()
        present = True
    else:
        raise OperatorFailure("subprocess_failed")
    _write_private_bytes(path, payload)
    entries = sum(
        1
        for line in result.stdout.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and _KEEPALIVE_MARKER in line
    )
    return hashlib.sha256(payload).hexdigest(), entries, present


def _disable_keepalive_cron(
    snapshot_path: Path, expected_sha256: str, *, originally_present: bool
) -> None:
    payload = _read_private_bytes(snapshot_path)
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise OperatorFailure("evidence_invalid")
    try:
        text_value = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise OperatorFailure("evidence_invalid") from None
    retained = [
        line
        for line in text_value.splitlines(keepends=True)
        if _KEEPALIVE_MARKER not in line
    ]
    if not originally_present:
        return
    result = _run(["crontab", "-"], input_bytes="".join(retained).encode(), timeout=10)
    if result.returncode != 0 or result.stdout or result.stderr:
        raise OperatorFailure("subprocess_failed")


def _restore_crontab(
    snapshot_path: Path, expected_sha256: str, *, originally_present: bool
) -> None:
    payload = _read_private_bytes(snapshot_path)
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise OperatorFailure("evidence_invalid")
    if originally_present:
        result = _run(["crontab", "-"], input_bytes=payload, timeout=10)
        if result.returncode != 0 or result.stdout or result.stderr:
            raise OperatorFailure("subprocess_failed")
    else:
        result = _run(["crontab", "-r"], timeout=10)
        if result.returncode not in {0, 1} or result.stdout:
            raise OperatorFailure("subprocess_failed")
    verification = _run(["crontab", "-l"], timeout=10)
    if not originally_present:
        if verification.returncode != 1 or verification.stdout:
            raise OperatorFailure("subprocess_failed")
        return
    restored = verification.stdout.encode()
    if (
        verification.returncode != 0
        or verification.stderr
        or hashlib.sha256(restored).hexdigest() != expected_sha256
    ):
        raise OperatorFailure("subprocess_failed")


def _rollback_override_payload(image_id: str) -> bytes:
    if _IMAGE_ID_PATTERN.fullmatch(image_id) is None:
        raise OperatorFailure("evidence_invalid")
    return f"services:\n  app_spx:\n    image: {image_id}\n".encode()


def _watchdog_unit(state: dict[str, Any], kind: str) -> str:
    unit = f"butterfly-credential-proof-{state['session_id']}-{kind}"
    if _UNIT_PATTERN.fullmatch(unit) is None:
        raise OperatorFailure("watchdog_invalid")
    return unit


def _restore_argv(args: argparse.Namespace, *, watchdog_fired: bool = True) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "restore",
        "--state",
        str(args.state.resolve()),
        "--base-compose",
        str(args.base_compose.resolve()),
        "--rollback-override",
        str(args.rollback_override.resolve()),
        "--cron-snapshot",
        str(args.cron_snapshot.resolve()),
    ]
    if getattr(args, "archive", None) is not None:
        command.extend(["--archive", str(args.archive.resolve())])
    if watchdog_fired:
        command.append("--watchdog-fired")
    return command


def _arm_watchdog(state: dict[str, Any], kind: str, delay: int, restore_argv: list[str]) -> None:
    unit = _watchdog_unit(state, kind)
    result = _run(
        [
            "sudo",
            "-n",
            "systemd-run",
            "--collect",
            f"--uid={os.getuid()}",
            f"--gid={os.getgid()}",
            f"--working-directory={Path.cwd().resolve()}",
            f"--unit={unit}",
            f"--on-active={delay}s",
            "--timer-property=AccuracySec=1s",
            "--",
            *restore_argv,
        ],
        timeout=15,
    )
    output = f"{result.stdout}\n{result.stderr}"
    if (
        result.returncode != 0
        or f"{unit}.timer" not in output
        or f"{unit}.service" not in output
        or any(unit not in line for line in output.splitlines() if line.strip())
    ):
        raise OperatorFailure("watchdog_invalid")


def _watchdog_active(state: dict[str, Any], kind: str) -> bool:
    unit = f"{_watchdog_unit(state, kind)}.timer"
    result = _run(["sudo", "-n", "systemctl", "is-active", unit], timeout=10)
    return bool(result.returncode == 0 and result.stdout.strip() == "active" and not result.stderr)


def _watchdog_service_active(state: dict[str, Any], kind: str) -> bool:
    unit = f"{_watchdog_unit(state, kind)}.service"
    result = _run(["sudo", "-n", "systemctl", "is-active", unit], timeout=10)
    return bool(result.returncode == 0 and result.stdout.strip() == "active" and not result.stderr)


def _cancel_watchdog(state: dict[str, Any], kind: str) -> None:
    unit = _watchdog_unit(state, kind)
    result = _run(
        ["sudo", "-n", "systemctl", "stop", f"{unit}.timer"],
        timeout=10,
    )
    if result.returncode == 0 and (result.stdout or result.stderr):
        raise OperatorFailure("watchdog_invalid")
    if result.returncode not in {0, 5}:
        raise OperatorFailure("watchdog_invalid")


def _internal_native_smoke() -> None:
    try:
        scipy_special = importlib.import_module("scipy.special")
        if scipy_special.ndtr(0.0) != 0.5:
            raise OperatorFailure("native_smoke_failed")
        importlib.import_module("schwab.auth")
        importlib.import_module("butterfly_guy.schwab_gateway.credential_probe")
    except Exception:
        raise OperatorFailure("native_smoke_failed") from None


def _internal_refusal_gate() -> None:
    try:
        probe_module = importlib.import_module(
            "butterfly_guy.scripts.probe_schwab_gateway_credentials"
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                probe_module.main([])
            except SystemExit as exc:
                refusal_code = exc.code
            else:
                refusal_code = 0
        refusal = stderr.getvalue()
        if (
            refusal_code != 2
            or stdout.getvalue()
            or "credential proof requires explicit" not in refusal
            or len(refusal.encode()) > 2048
        ):
            raise OperatorFailure("credential_refused")
    except OperatorFailure:
        raise
    except Exception:
        raise OperatorFailure("credential_refused") from None


def _internal_signal(action: str) -> None:
    signal_number = {"stop": signal.SIGSTOP, "continue": signal.SIGCONT}.get(action)
    if signal_number is None:
        raise OperatorFailure("signal_invalid")
    try:
        os.kill(1, signal_number)
    except Exception:
        raise OperatorFailure("signal_invalid") from None


def _internal_signal_status(expected: str) -> None:
    if expected not in {"stopped", "running"}:
        raise OperatorFailure("signal_invalid")
    try:
        status_text = Path("/proc/1/status").read_text(encoding="utf-8")
    except Exception:
        raise OperatorFailure("signal_invalid") from None
    state_lines = [line for line in status_text.splitlines() if line.startswith("State:")]
    if len(state_lines) != 1:
        raise OperatorFailure("signal_invalid")
    stopped = "T (stopped)" in state_lines[0] or "t (tracing stop)" in state_lines[0]
    if stopped != (expected == "stopped"):
        raise OperatorFailure("signal_invalid")


def _inspect_all() -> dict[str, dict[str, Any]]:
    return {
        name: inspect_container(str(_SERVICE_SPECS[name]["container"]))
        for name in _ALL_SERVICES
    }


def _require_runtime_baseline(
    state: dict[str, Any],
    inspections: dict[str, dict[str, Any]],
    *,
    require_unpaused: bool = True,
) -> None:
    for name in _ALL_SERVICES:
        inspected = inspections[name]
        if not _container_running(inspected, paused=False if require_unpaused else False):
            raise OperatorFailure("baseline_mismatch")
        baseline = state["baseline"][name]
        current = build_record(inspected)
        if not records_match_exactly(baseline["record"], current):
            raise OperatorFailure("baseline_mismatch")
        _, image_id = _container_identity(inspected)
        if image_id != baseline["image_id"]:
            raise OperatorFailure("baseline_mismatch")


def _run_health_checks() -> None:
    if any(not _health_ok(name) for name in _TRADING_SERVICES):
        raise OperatorFailure("health_invalid")


def _run_uniqueness_checks(*, allow_stopped: bool = False) -> dict[str, int]:
    pids: dict[str, int] = {}
    for name in _ALL_SERVICES:
        if allow_stopped and name in {"ndx", "xsp"}:
            continue
        pids[name] = _unique_service_pid(name)
    return pids


def _require_candidate_ownership(inspected: dict[str, Any]) -> None:
    if not _candidate_read_only(inspected):
        raise OperatorFailure("candidate_ownership_invalid")


def _archive_member_sha256(path: Path, member_name: str) -> str:
    try:
        with tarfile.open(path, mode="r:") as archive:
            member = archive.getmember(member_name)
            handle = archive.extractfile(member)
            if handle is None:
                raise OperatorFailure("archive_invalid")
            payload = handle.read(MAX_SOURCE_BYTES + 1)
    except (KeyError, OSError, tarfile.TarError):
        raise OperatorFailure("archive_invalid") from None
    if len(payload) > MAX_SOURCE_BYTES:
        raise OperatorFailure("archive_invalid")
    return hashlib.sha256(payload).hexdigest()


def _require_reviewed_file(path: Path, archive: Path, member_name: str) -> None:
    if _sha256_file(path, max_bytes=MAX_SOURCE_BYTES) != _archive_member_sha256(
        archive, member_name
    ):
        raise OperatorFailure("provenance_invalid")


def _discover_accepted_snapshots(directory: Path) -> dict[str, dict[str, object]]:
    try:
        directory_stat = directory.lstat()
    except OSError:
        raise OperatorFailure("evidence_invalid") from None
    if not stat.S_ISDIR(directory_stat.st_mode) or directory.is_symlink():
        raise OperatorFailure("evidence_invalid")
    found: dict[str, list[dict[str, object]]] = {name: [] for name in _TRADING_SERVICES}
    visited = 0
    try:
        for root, directories, filenames in os.walk(directory, followlinks=False):
            directories[:] = [
                name for name in directories if not (Path(root) / name).is_symlink()
            ]
            for filename in filenames:
                visited += 1
                if visited > 256:
                    raise OperatorFailure("evidence_invalid")
                path = Path(root) / filename
                relative = str(path.relative_to(directory)).casefold()
                if not any(marker in relative for marker in ("accepted", "resume", "supplement")):
                    continue
                matched = [
                    name
                    for name in _TRADING_SERVICES
                    if re.search(rf"(?:^|[^a-z0-9]){name}(?:[^a-z0-9]|$)", relative)
                ]
                if len(matched) != 1:
                    continue
                try:
                    record = read_snapshot(path)
                except (OSError, ValueError):
                    continue
                found[matched[0]].append(record)
    except OperatorFailure:
        raise
    except OSError:
        raise OperatorFailure("evidence_invalid") from None
    if any(len(records) != 1 for records in found.values()):
        raise OperatorFailure("evidence_invalid")
    return {name: records[0] for name, records in found.items()}


def _accepted_snapshots(args: argparse.Namespace) -> dict[str, dict[str, object]]:
    explicit = (args.accepted_spx, args.accepted_ndx, args.accepted_xsp)
    if args.accepted_directory is not None:
        if any(path is not None for path in explicit):
            raise OperatorFailure("invalid_arguments")
        return _discover_accepted_snapshots(args.accepted_directory)
    if any(path is None for path in explicit):
        raise OperatorFailure("invalid_arguments")
    try:
        return {
            "spx": read_snapshot(args.accepted_spx),
            "ndx": read_snapshot(args.accepted_ndx),
            "xsp": read_snapshot(args.accepted_xsp),
        }
    except (OSError, ValueError):
        raise OperatorFailure("evidence_invalid") from None


def _approved_window(reference: str, start_utc: str, end_utc: str) -> tuple[int, int, str]:
    if not reference or len(reference) > 256:
        raise OperatorFailure("invalid_arguments")
    timestamp_pattern = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z"
    if re.fullmatch(timestamp_pattern, start_utc) is None or re.fullmatch(
        timestamp_pattern, end_utc
    ) is None:
        raise OperatorFailure("invalid_arguments")
    try:
        start = int(datetime.strptime(start_utc, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        ).timestamp())
        end = int(datetime.strptime(end_utc, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        ).timestamp())
    except ValueError:
        raise OperatorFailure("invalid_arguments") from None
    now = int(time.time())
    if start >= end or end - start > 2 * 60 * 60 or now < start or now > end:
        raise OperatorFailure("invalid_arguments")
    return start, end, hashlib.sha256(reference.encode()).hexdigest()


def _prepare(args: argparse.Namespace) -> None:
    state = _new_state(args.approved_sha)
    window_start, window_end, approval_hash = _approved_window(
        args.approval_reference,
        args.window_start_utc,
        args.window_end_utc,
    )
    state["approval_1"] = {
        "reference_sha256": approval_hash,
        "window_start": window_start,
        "window_end": window_end,
    }
    _write_state_new(args.state, state)
    try:
        archive_sha256 = _validate_archive(
            args.archive, args.approved_sha, args.expected_archive_sha256
        )
        state["archive_sha256"] = archive_sha256
        operator_sha = _archive_member_sha256(
            args.archive, "src/butterfly_guy/scripts/credential_proof_fingerprint.py"
        )
        if _sha256_file(Path(__file__).resolve(), max_bytes=MAX_SOURCE_BYTES) != operator_sha:
            raise OperatorFailure("provenance_invalid")
        state["checks"]["archive_provenance"] = "pass"
        state["checks"]["archive_sha256"] = "pass"
        _require_reviewed_file(
            args.base_compose, args.archive, "infra/docker-compose.yml"
        )
        _require_reviewed_file(
            args.staging_override,
            args.archive,
            "infra/docker-compose.credential-proof-staging.yml",
        )
        state["checks"]["reviewed_compose_files"] = "pass"

        inspections = _inspect_all()
        accepted = _accepted_snapshots(args)
        for name in _ALL_SERVICES:
            inspected = inspections[name]
            if not _container_running(inspected):
                raise OperatorFailure("baseline_mismatch")
            container_id, image_id = _container_identity(inspected)
            record = build_record(inspected)
            if record["staging_tmpfs_present"] is not False:
                raise OperatorFailure("baseline_mismatch")
            if name in accepted and not records_match_exactly(accepted[name], record):
                raise OperatorFailure("baseline_mismatch")
            state["baseline"][name] = {
                "container_id": container_id,
                "image_id": image_id,
                "record": record,
            }
        for check in ("accepted_fingerprints", "field_hashes", "images", "compose_hashes"):
            state["checks"][check] = "pass"

        _run_health_checks()
        state["checks"]["health"] = "pass"
        service_pids = _run_uniqueness_checks()
        state["checks"]["process_uniqueness"] = "pass"
        _require_candidate_ownership(inspections["candidate"])
        state["checks"]["candidate_ownership"] = "pass"
        _require_no_host_writers()
        _require_no_unowned_runtime_processes(list(service_pids.values()))
        state["checks"]["keepalive"] = "pass"
        state["checks"]["host_clients"] = "pass"
        state["checks"]["ci_workers"] = "pass"

        _validate_compose_semantics(args.base_compose, args.staging_override)
        if (
            _compose_service_hash(args.base_compose)
            != state["baseline"]["spx"]["record"]["compose_config_hash"]
        ):
            raise OperatorFailure("compose_semantics_invalid")
        _require_base_image(args.base_compose, state["baseline"]["spx"]["image_id"])
        state["checks"]["compose_semantics"] = "pass"
        _validate_compose_dry_run(args.base_compose, args.staging_override)
        state["checks"]["compose_dry_run"] = "pass"

        cron_sha256, keepalive_entries, cron_present = _capture_crontab(args.cron_snapshot)
        state["cron"]["sha256"] = cron_sha256
        state["cron"]["keepalive_entries"] = keepalive_entries
        state["cron"]["present"] = cron_present
        _write_private_bytes(
            args.rollback_override,
            _rollback_override_payload(state["baseline"]["spx"]["image_id"]),
        )
        state["phase"] = "approval_1_ready"
        state["failure_code"] = None
        _replace_state(args.state, state)
        _emit("ok", "approval_1_ready", archive_sha256=archive_sha256)
    except ValueError:
        _set_failure(
            args.state,
            state,
            "evidence_invalid",
            invalidate_pending=True,
        )
        raise OperatorFailure("evidence_invalid") from None
    except OperatorFailure as exc:
        _set_failure(args.state, state, exc.code, invalidate_pending=True)
        raise
    except Exception:
        with contextlib.suppress(Exception):
            _set_failure(args.state, state, "internal_failure", invalidate_pending=True)
        raise OperatorFailure("internal_failure") from None


def _run_exact_json(
    command: Sequence[str], expected: dict[str, object], *, timeout: int = 15
) -> None:
    result = _run(command, timeout=timeout)
    if result.returncode != 0 or result.stderr:
        raise OperatorFailure("subprocess_failed")
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError):
        raise OperatorFailure("subprocess_output_invalid") from None
    expected_output = json.dumps(expected, separators=(",", ":"), sort_keys=True) + "\n"
    if payload != expected or result.stdout != expected_output:
        raise OperatorFailure("subprocess_output_invalid")


def _staged_operator_command(*arguments: str) -> list[str]:
    return [
        "docker",
        "exec",
        "-e",
        f"PYTHONPATH={STAGING_SOURCE_TARGET}/src",
        "butterfly_spx_app",
        "python",
        f"{STAGING_SOURCE_TARGET}/src/butterfly_guy/scripts/credential_proof_fingerprint.py",
        *arguments,
    ]


def _stage_archive(archive_path: Path, expected_sha256: str) -> None:
    commands = (
        ["docker", "exec", "butterfly_spx_app", "mkdir", "-p", STAGING_SOURCE_TARGET],
        ["docker", "cp", str(archive_path), f"butterfly_spx_app:{STAGING_ARCHIVE_TARGET}"],
        [
            "docker",
            "exec",
            "butterfly_spx_app",
            "tar",
            "-xf",
            STAGING_ARCHIVE_TARGET,
            "-C",
            STAGING_SOURCE_TARGET,
        ],
    )
    for command in commands:
        result = _run(command, timeout=30)
        if result.returncode != 0 or result.stdout or result.stderr:
            raise OperatorFailure("staging_invalid")
    digest_result = _run(
        ["docker", "exec", "butterfly_spx_app", "sha256sum", STAGING_ARCHIVE_TARGET],
        timeout=10,
    )
    parts = digest_result.stdout.strip().split()
    if (
        digest_result.returncode != 0
        or digest_result.stderr
        or len(parts) != 2
        or parts[0] != expected_sha256
        or parts[1] != STAGING_ARCHIVE_TARGET
    ):
        raise OperatorFailure("staging_invalid")


def _recreate_staged(base_path: Path, staging_path: Path) -> None:
    result = _run(
        [
            "docker",
            "compose",
            "-f",
            str(base_path),
            "-f",
            str(staging_path),
            "up",
            "-d",
            "--no-deps",
            "--no-build",
            "--pull",
            "never",
            "--force-recreate",
            "app_spx",
        ],
        timeout=60,
    )
    if result.returncode != 0:
        raise OperatorFailure("staging_invalid")
    _validate_compose_action_output(result, "staging_invalid")


def _container_is_stopped(service: str) -> bool:
    inspected = inspect_container(str(_SERVICE_SPECS[service]["container"]))
    state = inspected.get("State")
    return bool(isinstance(state, dict) and state.get("Running") is False)


def _approval_1_execute(args: argparse.Namespace) -> None:
    state = _read_state(args.state)
    if (
        state["phase"] != "approval_1_ready"
        or state["approved_sha"] != args.approved_sha
        or state["archive_sha256"] != args.expected_archive_sha256
        or not isinstance(state["approval_1"]["window_start"], int)
        or not isinstance(state["approval_1"]["window_end"], int)
        or not state["approval_1"]["window_start"]
        <= int(time.time())
        <= state["approval_1"]["window_end"]
    ):
        raise OperatorFailure("operator_state_invalid")
    state["phase"] = "approval_1_running"
    _replace_state(args.state, state)
    mutated = False
    try:
        _validate_archive(args.archive, state["approved_sha"], args.expected_archive_sha256)
        _validate_compose_semantics(args.base_compose, args.staging_override)
        _validate_compose_dry_run(args.base_compose, args.staging_override)
        inspections = _inspect_all()
        _require_runtime_baseline(state, inspections)
        _run_health_checks()
        service_pids = _run_uniqueness_checks()
        _require_candidate_ownership(inspections["candidate"])
        _require_no_host_writers()
        _require_no_unowned_runtime_processes(list(service_pids.values()))

        mutated = True
        _recreate_staged(args.base_compose, args.staging_override)
        staged = inspect_container("butterfly_spx_app")
        if (
            not _container_running(staged)
            or _container_identity(staged)[1] != state["baseline"]["spx"]["image_id"]
            or not staging_matches_baseline(staged, state["baseline"]["spx"]["record"])
        ):
            raise OperatorFailure("staging_invalid")
        _stage_archive(args.archive, args.expected_archive_sha256)

        _run_exact_json(
            _staged_operator_command("internal-native-smoke"),
            {"code": "native_smoke_passed", "status": "ok"},
            timeout=30,
        )
        state["checks"]["native_smoke"] = "pass"
        _run_exact_json(
            _staged_operator_command("internal-refusal-gate"),
            {"code": "refusal_gate_passed", "status": "ok"},
            timeout=20,
        )
        state["checks"]["refusal_gate"] = "pass"
        _replace_state(args.state, state)

        now = int(time.time())
        restore_argv = _restore_argv(args)
        _arm_watchdog(state, "hard", HARD_RESTORE_SECONDS, restore_argv)
        if not _watchdog_active(state, "hard"):
            raise OperatorFailure("watchdog_invalid")
        state["watchdog"]["hard"] = "armed"
        state["watchdog"]["hard_deadline"] = now + HARD_RESTORE_SECONDS
        state["checks"]["watchdog"] = "pass"
        _replace_state(args.state, state)

        cron_sha = state["cron"]["sha256"]
        if not isinstance(cron_sha, str):
            raise OperatorFailure("evidence_invalid")
        cron_present = state["cron"]["present"]
        if not isinstance(cron_present, bool):
            raise OperatorFailure("evidence_invalid")
        _disable_keepalive_cron(
            args.cron_snapshot,
            cron_sha,
            originally_present=cron_present,
        )
        state["cron"]["disabled"] = True
        _replace_state(args.state, state)

        for service in ("ndx", "xsp"):
            result = _run(
                ["docker", "stop", "--time", "20", str(_SERVICE_SPECS[service]["container"])],
                timeout=30,
            )
            expected_stop = f"{_SERVICE_SPECS[service]['container']}\n"
            if result.returncode != 0 or result.stdout != expected_stop or result.stderr:
                raise OperatorFailure("single_writer_invalid")
        _run_exact_json(
            _staged_operator_command("internal-signal", "--action", "stop"),
            {"code": "signal_passed", "status": "ok"},
        )
        if not all(_container_is_stopped(service) for service in ("ndx", "xsp")):
            raise OperatorFailure("single_writer_invalid")
        _run_exact_json(
            _staged_operator_command("internal-signal-status", "--expect", "stopped"),
            {"code": "signal_passed", "status": "ok"},
        )
        spx_pid = _unique_service_pid("spx")
        candidate = inspect_container("butterfly_spx_candidate_feed")
        candidate_pid = _unique_service_pid("candidate")
        _require_candidate_ownership(candidate)
        _require_no_host_writers()
        _require_no_unowned_runtime_processes([spx_pid, candidate_pid])
        if _matching_host_processes(_PROOF_MARKER):
            raise OperatorFailure("single_writer_invalid")

        quiescence_started = int(time.time())
        _arm_watchdog(state, "approval", APPROVAL_TIMEOUT_SECONDS, restore_argv)
        if not _watchdog_active(state, "approval"):
            raise OperatorFailure("watchdog_invalid")
        state["watchdog"]["approval"] = "armed"
        state["watchdog"]["approval_deadline"] = (
            quiescence_started + APPROVAL_TIMEOUT_SECONDS
        )
        state["checks"]["single_writer"] = "pass"
        state["quiescence"]["started"] = quiescence_started
        state["quiescence"]["spx_pid"] = spx_pid
        state["phase"] = "approval_2_pending"
        _replace_state(args.state, state)
        _emit("ok", "approval_2_required", timeout_seconds=APPROVAL_TIMEOUT_SECONDS)
    except OperatorFailure as exc:
        with contextlib.suppress(Exception):
            _set_failure(args.state, state, exc.code, invalidate_pending=True)
        if mutated:
            _restore_operation(args, failure_code=exc.code)
        raise
    except Exception:
        with contextlib.suppress(Exception):
            _set_failure(args.state, state, "internal_failure", invalidate_pending=True)
        if mutated:
            _restore_operation(args, failure_code="internal_failure")
        raise OperatorFailure("internal_failure") from None


def _validate_rollback_override(
    base_path: Path, rollback_path: Path, expected_image_id: str
) -> None:
    del base_path
    if _read_private_bytes(rollback_path) != _rollback_override_payload(expected_image_id):
        raise OperatorFailure("evidence_invalid")


def _recreate_baseline(base_path: Path, rollback_path: Path) -> None:
    del rollback_path
    result = _run(
        [
            "docker",
            "compose",
            "-f",
            str(base_path),
            "up",
            "-d",
            "--no-deps",
            "--no-build",
            "--pull",
            "never",
            "--force-recreate",
            "app_spx",
        ],
        timeout=60,
    )
    if result.returncode != 0:
        raise OperatorFailure("subprocess_failed")
    _validate_compose_action_output(result, "subprocess_output_invalid")


def _emergency_restore_spx(
    base_path: Path, rollback_path: Path, expected_image_id: str
) -> None:
    try:
        if _read_private_bytes(rollback_path) != _rollback_override_payload(expected_image_id):
            return
        result = _run(
            [
                "docker",
                "compose",
                "-f",
                str(base_path),
                "-f",
                str(rollback_path),
                "up",
                "-d",
                "--no-deps",
                "--no-build",
                "--pull",
                "never",
                "--force-recreate",
                "app_spx",
            ],
            timeout=60,
        )
        if result.returncode != 0:
            return
        _validate_compose_action_output(result, "subprocess_output_invalid")
        inspected = inspect_container("butterfly_spx_app")
        current = build_record(inspected)
        if (
            _container_identity(inspected)[1] != expected_image_id
            or current["staging_tmpfs_present"] is not False
        ):
            return
    except Exception:
        return


def _start_container(service: str) -> None:
    result = _run(["docker", "start", str(_SERVICE_SPECS[service]["container"])], timeout=30)
    expected = f"{_SERVICE_SPECS[service]['container']}\n"
    if result.returncode != 0 or result.stdout != expected or result.stderr:
        raise OperatorFailure("subprocess_failed")


def _wait_for_health() -> None:
    deadline = time.monotonic() + 30
    while True:
        if all(_health_ok(name) for name in _TRADING_SERVICES):
            return
        if time.monotonic() >= deadline:
            raise OperatorFailure("health_invalid")
        time.sleep(2)


def _fresh_error_counts(since_epoch: int) -> dict[str, int]:
    time.sleep(FRESH_ERROR_WINDOW_SECONDS)
    counts: dict[str, int] = {}
    for name in _TRADING_SERVICES:
        result = _run(
            [
                "docker",
                "logs",
                "--since",
                str(since_epoch),
                str(_SERVICE_SPECS[name]["container"]),
            ],
            timeout=15,
        )
        if result.returncode != 0:
            raise OperatorFailure("subprocess_failed")
        lines = f"{result.stdout}\n{result.stderr}".splitlines()
        counts[name] = sum(
            1 for line in lines if any(marker in line.casefold() for marker in _ERROR_MARKERS)
        )
    return counts


def _pause_fail_closed() -> None:
    for name in _TRADING_SERVICES:
        try:
            inspected = inspect_container(str(_SERVICE_SPECS[name]["container"]))
            state = inspected.get("State")
            if (
                isinstance(state, dict)
                and state.get("Running") is True
                and state.get("Paused") is False
            ):
                _run(["docker", "pause", str(_SERVICE_SPECS[name]["container"])], timeout=15)
        except Exception:
            continue


def _cleanup_temporary_inputs(args: argparse.Namespace) -> None:
    for attribute in ("archive", "rollback_override", "cron_snapshot"):
        path = getattr(args, attribute, None)
        if isinstance(path, Path):
            with contextlib.suppress(FileNotFoundError):
                path.unlink()


def _best_effort_restore_cron(args: argparse.Namespace, state: dict[str, Any]) -> None:
    cron_sha = state["cron"]["sha256"]
    cron_present = state["cron"]["present"]
    if not isinstance(cron_sha, str) or not isinstance(cron_present, bool):
        return
    try:
        _restore_crontab(
            args.cron_snapshot,
            cron_sha,
            originally_present=cron_present,
        )
    except Exception:
        return
    state["cron"]["disabled"] = False
    state["cron"]["restored"] = True


def _restore_operation(
    args: argparse.Namespace,
    *,
    failure_code: str | None = None,
    emit_result: bool = False,
) -> bool:
    with _state_lock(args.state):
        state = _read_state(args.state)
        if state["phase"] == "restored" and state["restoration"]["result"] == "pass":
            if emit_result:
                _emit("ok", "restoration_passed")
            return True
        state["phase"] = "restoring"
        if failure_code in _RESULT_CODES:
            state["failure_code"] = failure_code
        if getattr(args, "watchdog_fired", False):
            if state["watchdog"]["approval"] == "armed":
                state["watchdog"]["approval"] = "fired"
                state["failure_code"] = "approval_2_timeout"
            elif state["watchdog"]["hard"] == "armed":
                state["watchdog"]["hard"] = "fired"
                state["failure_code"] = "watchdog_invalid"
        _replace_state(args.state, state)

        expected_image: str | None = None
        try:
            expected_image = state["baseline"]["spx"]["image_id"]
            if not isinstance(expected_image, str):
                raise OperatorFailure("operator_state_invalid")
            _validate_rollback_override(args.base_compose, args.rollback_override, expected_image)
            _require_base_image(args.base_compose, expected_image)
            if (
                _compose_service_hash(args.base_compose)
                != state["baseline"]["spx"]["record"]["compose_config_hash"]
            ):
                raise OperatorFailure("compose_semantics_invalid")

            restoration_started = int(time.time())
            _recreate_baseline(args.base_compose, args.rollback_override)
            for service in ("ndx", "xsp"):
                inspected = inspect_container(str(_SERVICE_SPECS[service]["container"]))
                state_value = inspected.get("State")
                if not isinstance(state_value, dict):
                    raise OperatorFailure("docker_inspect_invalid")
                if state_value.get("Running") is not True:
                    _start_container(service)

            cron_sha = state["cron"]["sha256"]
            if not isinstance(cron_sha, str):
                raise OperatorFailure("evidence_invalid")
            cron_present = state["cron"]["present"]
            if not isinstance(cron_present, bool):
                raise OperatorFailure("evidence_invalid")
            _restore_crontab(
                args.cron_snapshot,
                cron_sha,
                originally_present=cron_present,
            )
            state["cron"]["disabled"] = False
            state["cron"]["restored"] = True

            _wait_for_health()
            inspections = _inspect_all()
            _require_runtime_baseline(state, inspections)
            state["checks"]["restoration_fingerprints"] = "pass"
            state["checks"]["restoration_health"] = "pass"
            service_pids = _run_uniqueness_checks()
            state["checks"]["restoration_uniqueness"] = "pass"
            _require_candidate_ownership(inspections["candidate"])
            state["checks"]["restoration_ownership"] = "pass"
            _require_no_host_writers()
            _require_no_unowned_runtime_processes(list(service_pids.values()))
            state["checks"]["restoration_keepalive"] = "pass"
            counts = _fresh_error_counts(restoration_started)
            state["restoration"]["error_counts"] = counts
            if any(counts.values()):
                raise OperatorFailure("subprocess_output_invalid")
            state["checks"]["restoration_errors"] = "pass"

            for kind in ("approval", "hard"):
                if state["watchdog"][kind] in {"armed", "fired"}:
                    _cancel_watchdog(state, kind)
                state["watchdog"][kind] = "cancelled"
            if state["proof"]["result"] == "pending":
                state["proof"]["result"] = "invalid"
                state["proof"]["reason_code"] = state["failure_code"]
                state["proof"]["information_exposure"] = "invalid"
                if state["checks"]["proof"] == "pending":
                    state["checks"]["proof"] = "invalid"
            state["restoration"]["result"] = "pass"
            state["restoration"]["completed"] = int(time.time())
            state["phase"] = "restored"
            _replace_state(args.state, state)
            _cleanup_temporary_inputs(args)
            if emit_result:
                _emit("ok", "restoration_passed")
            return True
        except Exception:
            if isinstance(expected_image, str):
                _emergency_restore_spx(
                    args.base_compose,
                    args.rollback_override,
                    expected_image,
                )
            _best_effort_restore_cron(args, state)
            _pause_fail_closed()
            for kind in ("approval", "hard"):
                if state["watchdog"][kind] in {"armed", "fired"}:
                    try:
                        _cancel_watchdog(state, kind)
                    except Exception:
                        state["watchdog"][kind] = "fail"
                    else:
                        state["watchdog"][kind] = "cancelled"
            state["restoration"]["result"] = "fail"
            state["restoration"]["completed"] = int(time.time())
            for name in (
                "restoration_fingerprints",
                "restoration_health",
                "restoration_uniqueness",
                "restoration_ownership",
                "restoration_keepalive",
                "restoration_errors",
            ):
                if state["checks"][name] == "pending":
                    state["checks"][name] = "invalid"
            state["phase"] = "failed"
            state["failure_code"] = "restoration_failed_paused"
            with contextlib.suppress(Exception):
                _replace_state(args.state, state)
            if emit_result:
                _emit("error", "restoration_failed_paused")
            raise OperatorFailure("restoration_failed_paused") from None


def _watchdog_status(args: argparse.Namespace) -> None:
    state = _read_state(args.state)
    if state["watchdog"]["hard"] != "armed" or not _watchdog_active(state, "hard"):
        raise OperatorFailure("watchdog_invalid")
    if args.require_approval_timer and (
        state["watchdog"]["approval"] != "armed" or not _watchdog_active(state, "approval")
    ):
        raise OperatorFailure("watchdog_invalid")
    _emit("ok", "watchdog_ready")


def _watchdog_arm_command(args: argparse.Namespace) -> None:
    with _state_lock(args.state):
        state = _read_state(args.state)
        if state["phase"] != "approval_1_running" or state["watchdog"][args.kind] != "pending":
            raise OperatorFailure("watchdog_invalid")
        if args.kind == "approval" and not _watchdog_active(state, "hard"):
            raise OperatorFailure("watchdog_invalid")
        delay = HARD_RESTORE_SECONDS if args.kind == "hard" else APPROVAL_TIMEOUT_SECONDS
        _arm_watchdog(state, args.kind, delay, _restore_argv(args))
        if not _watchdog_active(state, args.kind):
            raise OperatorFailure("watchdog_invalid")
        state["watchdog"][args.kind] = "armed"
        state["watchdog"][f"{args.kind}_deadline"] = int(time.time()) + delay
        _replace_state(args.state, state)
    _emit("ok", "watchdog_armed")


def _watchdog_cancel_command(args: argparse.Namespace) -> None:
    with _state_lock(args.state):
        state = _read_state(args.state)
        allowed = (args.kind == "approval" and state["phase"] == "approval_2_running") or (
            args.kind == "hard" and state["phase"] == "restored"
        )
        if not allowed or state["watchdog"][args.kind] not in {"armed", "fired"}:
            raise OperatorFailure("watchdog_invalid")
        _cancel_watchdog(state, args.kind)
        state["watchdog"][args.kind] = "cancelled"
        _replace_state(args.state, state)
    _emit("ok", "watchdog_cancelled")


def _approval_2_execute(args: argparse.Namespace) -> None:
    proof_code = "credential_proof_failed"
    try:
        with _state_lock(args.state):
            state = _read_state(args.state)
            now = int(time.time())
            deadline = state["watchdog"]["approval_deadline"]
            hard_deadline = state["watchdog"]["hard_deadline"]
            window_end = state["approval_1"]["window_end"]
            if (
                state["phase"] != "approval_2_pending"
                or state["proof"]["attempted"]
                or not isinstance(state["archive_sha256"], str)
                or not isinstance(deadline, int)
                or not isinstance(hard_deadline, int)
                or not isinstance(window_end, int)
                or now > deadline
                or now > window_end
                or now + PROOF_TIMEOUT_SECONDS + RESTORE_BUDGET_SECONDS > hard_deadline
                or not args.approval_reference
                or len(args.approval_reference) > 256
            ):
                raise OperatorFailure("approval_2_timeout")
            if not _watchdog_active(state, "hard") or not _watchdog_active(state, "approval"):
                raise OperatorFailure("watchdog_invalid")
            _cancel_watchdog(state, "approval")
            if _watchdog_service_active(state, "approval"):
                raise OperatorFailure("approval_2_timeout")
            state["watchdog"]["approval"] = "cancelled"
            state["proof"]["approval_reference_sha256"] = hashlib.sha256(
                args.approval_reference.encode()
            ).hexdigest()
            state["proof"]["attempted"] = True
            state["proof"]["attempt_count"] = 1
            state["proof"]["started"] = now
            state["phase"] = "approval_2_running"
            _replace_state(args.state, state)
    except OperatorFailure as exc:
        with contextlib.suppress(Exception):
            current = _read_state(args.state)
            if current["phase"] in {"approval_2_pending", "approval_2_running"}:
                _restore_operation(args, failure_code=exc.code)
        raise

    try:
        if not _watchdog_active(state, "hard"):
            raise OperatorFailure("watchdog_invalid")
        if not all(_container_is_stopped(service) for service in ("ndx", "xsp")):
            raise OperatorFailure("single_writer_invalid")
        _run_exact_json(
            _staged_operator_command("internal-signal-status", "--expect", "stopped"),
            {"code": "signal_passed", "status": "ok"},
        )
        spx_pid = _unique_service_pid("spx")
        candidate = inspect_container("butterfly_spx_candidate_feed")
        candidate_pid = _unique_service_pid("candidate")
        _require_candidate_ownership(candidate)
        _require_no_host_writers()
        _require_no_unowned_runtime_processes([spx_pid, candidate_pid])
        if _matching_host_processes(_PROOF_MARKER):
            raise OperatorFailure("single_writer_invalid")

        proof_command = [
            "docker",
            "exec",
            "-e",
            f"PYTHONPATH={STAGING_SOURCE_TARGET}/src",
            "butterfly_spx_app",
            "python",
            f"{STAGING_SOURCE_TARGET}/src/butterfly_guy/scripts/probe_schwab_gateway_credentials.py",
            "--authorize-real-credential-read",
            "--confirm-single-token-writer",
            "--confirm-no-deployment",
        ]
        result = _run(proof_command, timeout=PROOF_TIMEOUT_SECONDS)
        expected_output = '{"quote_count":1,"status":"ok","token_state":"ready"}\n'
        if result.returncode != 0:
            raise OperatorFailure("credential_proof_failed")
        if result.stderr or result.stdout != expected_output:
            raise OperatorFailure("credential_output_invalid")
        with _state_lock(args.state):
            state = _read_state(args.state)
            state["proof"]["result"] = "pass"
            state["proof"]["ended"] = int(time.time())
            state["proof"]["quote_count"] = 1
            state["proof"]["token_state"] = "ready"
            state["proof"]["reason_code"] = "credential_proof_passed"
            state["proof"]["information_exposure"] = "pass"
            state["checks"]["proof"] = "pass"
            _replace_state(args.state, state)
        proof_code = "credential_proof_passed"
    except OperatorFailure as exc:
        proof_code = exc.code if exc.code in {
            "credential_proof_failed",
            "credential_output_invalid",
            "single_writer_invalid",
            "subprocess_timeout",
            "watchdog_invalid",
        } else "credential_proof_failed"
        with _state_lock(args.state):
            state = _read_state(args.state)
            state["proof"]["result"] = "fail"
            state["proof"]["ended"] = int(time.time())
            state["proof"]["reason_code"] = proof_code
            state["proof"]["information_exposure"] = "pass"
            state["checks"]["proof"] = "fail"
            state["failure_code"] = proof_code
            _replace_state(args.state, state)
    except Exception:
        proof_code = "internal_failure"
        with _state_lock(args.state):
            state = _read_state(args.state)
            state["proof"]["result"] = "fail"
            state["proof"]["ended"] = int(time.time())
            state["proof"]["reason_code"] = proof_code
            state["proof"]["information_exposure"] = "pass"
            state["checks"]["proof"] = "fail"
            state["failure_code"] = proof_code
            _replace_state(args.state, state)
    restoration_ok = _restore_operation(args, failure_code=None)
    if restoration_ok and proof_code == "credential_proof_passed":
        _emit("ok", "credential_proof_passed", quote_count=1, retry_count=0)
        return
    raise OperatorFailure(proof_code)


def _parser() -> argparse.ArgumentParser:
    parser = SafeArgumentParser(description=__doc__, add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture", add_help=False)
    capture.add_argument("--container", required=True)
    capture.add_argument("--snapshot", required=True, type=Path)

    verify = subparsers.add_parser("verify", add_help=False)
    verify.add_argument("--container", required=True)
    verify.add_argument("--baseline", required=True, type=Path)
    verify.add_argument("--expect", choices=("exact", "staging-only"), required=True)
    verify.add_argument("--snapshot", type=Path)

    archive = subparsers.add_parser("archive-create", add_help=False)
    archive.add_argument("--approved-sha", required=True)
    archive.add_argument("--archive", required=True, type=Path)

    prepare = subparsers.add_parser("prepare", add_help=False)
    prepare.add_argument("--state", required=True, type=Path)
    prepare.add_argument("--approved-sha", required=True)
    prepare.add_argument("--approval-reference", required=True)
    prepare.add_argument("--window-start-utc", required=True)
    prepare.add_argument("--window-end-utc", required=True)
    prepare.add_argument("--accepted-directory", type=Path)
    prepare.add_argument("--accepted-spx", type=Path)
    prepare.add_argument("--accepted-ndx", type=Path)
    prepare.add_argument("--accepted-xsp", type=Path)
    prepare.add_argument("--base-compose", required=True, type=Path)
    prepare.add_argument("--staging-override", required=True, type=Path)
    prepare.add_argument("--archive", required=True, type=Path)
    prepare.add_argument("--expected-archive-sha256", required=True)
    prepare.add_argument("--rollback-override", required=True, type=Path)
    prepare.add_argument("--cron-snapshot", required=True, type=Path)

    approval_1 = subparsers.add_parser("approval1-execute", add_help=False)
    approval_1.add_argument("--state", required=True, type=Path)
    approval_1.add_argument("--approved-sha", required=True)
    approval_1.add_argument("--base-compose", required=True, type=Path)
    approval_1.add_argument("--staging-override", required=True, type=Path)
    approval_1.add_argument("--archive", required=True, type=Path)
    approval_1.add_argument("--expected-archive-sha256", required=True)
    approval_1.add_argument("--rollback-override", required=True, type=Path)
    approval_1.add_argument("--cron-snapshot", required=True, type=Path)

    watchdog = subparsers.add_parser("watchdog-status", add_help=False)
    watchdog.add_argument("--state", required=True, type=Path)
    watchdog.add_argument("--require-approval-timer", action="store_true")

    watchdog_arm = subparsers.add_parser("watchdog-arm", add_help=False)
    watchdog_arm.add_argument("--state", required=True, type=Path)
    watchdog_arm.add_argument("--kind", choices=("hard", "approval"), required=True)
    watchdog_arm.add_argument("--base-compose", required=True, type=Path)
    watchdog_arm.add_argument("--rollback-override", required=True, type=Path)
    watchdog_arm.add_argument("--cron-snapshot", required=True, type=Path)
    watchdog_arm.add_argument("--archive", type=Path)

    watchdog_cancel = subparsers.add_parser("watchdog-cancel", add_help=False)
    watchdog_cancel.add_argument("--state", required=True, type=Path)
    watchdog_cancel.add_argument("--kind", choices=("hard", "approval"), required=True)

    approval_2 = subparsers.add_parser("approval2-execute", add_help=False)
    approval_2.add_argument("--state", required=True, type=Path)
    approval_2.add_argument("--approval-reference", required=True)
    approval_2.add_argument("--base-compose", required=True, type=Path)
    approval_2.add_argument("--rollback-override", required=True, type=Path)
    approval_2.add_argument("--cron-snapshot", required=True, type=Path)
    approval_2.add_argument("--archive", type=Path)

    restore = subparsers.add_parser("restore", add_help=False)
    restore.add_argument("--state", required=True, type=Path)
    restore.add_argument("--base-compose", required=True, type=Path)
    restore.add_argument("--rollback-override", required=True, type=Path)
    restore.add_argument("--cron-snapshot", required=True, type=Path)
    restore.add_argument("--archive", type=Path)
    restore.add_argument("--watchdog-fired", action="store_true")

    subparsers.add_parser("internal-native-smoke", add_help=False)
    subparsers.add_parser("internal-refusal-gate", add_help=False)
    internal_signal = subparsers.add_parser("internal-signal", add_help=False)
    internal_signal.add_argument("--action", choices=("stop", "continue"), required=True)
    signal_status = subparsers.add_parser("internal-signal-status", add_help=False)
    signal_status.add_argument("--expect", choices=("stopped", "running"), required=True)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "archive-create":
            archive_sha256 = _create_archive(args.archive, args.approved_sha)
            _emit("ok", "archive_created", archive_sha256=archive_sha256)
            return
        if args.command == "prepare":
            _prepare(args)
            return
        if args.command == "approval1-execute":
            _approval_1_execute(args)
            return
        if args.command == "watchdog-status":
            _watchdog_status(args)
            return
        if args.command == "watchdog-arm":
            _watchdog_arm_command(args)
            return
        if args.command == "watchdog-cancel":
            _watchdog_cancel_command(args)
            return
        if args.command == "approval2-execute":
            _approval_2_execute(args)
            return
        if args.command == "restore":
            _restore_operation(args, emit_result=True)
            return
        if args.command == "internal-native-smoke":
            _internal_native_smoke()
            _emit("ok", "native_smoke_passed")
            return
        if args.command == "internal-refusal-gate":
            _internal_refusal_gate()
            _emit("ok", "refusal_gate_passed")
            return
        if args.command == "internal-signal":
            _internal_signal(args.action)
            _emit("ok", "signal_passed")
            return
        if args.command == "internal-signal-status":
            _internal_signal_status(args.expect)
            _emit("ok", "signal_passed")
            return

        inspected = inspect_container(args.container)
        current = build_record(inspected)
        if args.command == "capture":
            if current["staging_tmpfs_present"] is not False:
                raise OperatorFailure("fingerprint_failed")
            write_snapshot(args.snapshot, current)
            _emit("ok", "snapshot_captured")
            return

        baseline = read_snapshot(args.baseline)
        if args.snapshot is not None:
            write_snapshot(args.snapshot, current)
        if args.expect == "exact":
            verified = records_match_exactly(baseline, current)
        else:
            verified = staging_matches_baseline(inspected, baseline)
        if not verified:
            raise OperatorFailure("fingerprint_failed")
        _emit("ok", "snapshot_verified", expectation=args.expect)
    except OperatorFailure as exc:
        _emit("error", exc.code)
        raise SystemExit(1) from None
    except Exception:
        _emit("error", "internal_failure")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
