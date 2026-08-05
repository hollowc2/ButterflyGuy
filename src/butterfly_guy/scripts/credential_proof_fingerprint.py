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
LEGACY_EVIDENCE_RECORD_VERSION = 1
COMPOSE_CONFIG_HASH_LABEL = "com.docker.compose.config-hash"
STAGING_TMPFS_TARGET = "/app/.schwab-credential-proof-runtime"
STAGING_ARCHIVE_TARGET = f"{STAGING_TMPFS_TARGET}/reviewed.tar"
STAGING_SOURCE_TARGET = f"{STAGING_TMPFS_TARGET}/source"
RUNTIME_STAGING_TMPFS_TARGET = "/tmp/.schwab-credential-proof-runtime"
MAX_CAPTURE_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 256 * 1024
MAX_RESULT_BYTES = 512
MAX_EVIDENCE_DIRECTORIES = 128
MAX_EVIDENCE_FILES = 4096
MAX_EVIDENCE_CANDIDATES = 256
MAX_EVIDENCE_JSON_NODES = 512
MAX_EVIDENCE_DEPTH = 3
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
_RUNTIME_CONFIG_DESTINATIONS = {
    "spx": "/app/configs/config.yaml",
    "ndx": "/app/configs/config_ndx.yaml",
    "xsp": "/app/configs/config_xsp.yaml",
}
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
_EVIDENCE_MARKERS = ("accepted", "resume", "supplement")
_LEGACY_EVIDENCE_MARKERS = (
    "credential-proof",
    "credential_proof",
    "fingerprint",
    "baseline",
)
_LEGACY_EVIDENCE_DIRECTORY_MARKERS = (
    "evidence",
    "credential",
    "fingerprint",
    "baseline",
)
_FORBIDDEN_EVIDENCE_NAME_PATTERN = re.compile(
    r"(?:^|[^a-z0-9])(?:tokens?|secrets?|keys?)(?:[^a-z0-9]|$)"
)
_EVIDENCE_PRUNED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        "data",
        "graphify-out",
        "logs",
        "node_modules",
        "user_data",
    }
)
_ARCHIVE_PATHS = (
    "configs/config.yaml",
    "configs/config_ndx.yaml",
    "configs/config_xsp.yaml",
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
_BASELINE_CANDIDATE_CHECKS = (
    "candidate_ownership",
    "compose_hashes",
    "direct_access",
    "health",
    "images",
    "no_staging",
    "no_writers",
    "paper_mode",
    "process_uniqueness",
    "reviewed_sources",
    "running_unpaused",
)
_RUNTIME_BASELINE_CHECKS = (
    "candidate_ownership",
    "direct_access",
    "health",
    "images",
    "no_staging",
    "no_writers",
    "paper_mode",
    "process_uniqueness",
    "reviewed_sources",
    "running_unpaused",
    "runtime_config_mounts",
)
_COMPOSE_OBSERVATION_FIELDS = (
    "invalid_services",
    "matched_services",
    "mismatched_services",
)
_CONFIG_MOUNT_OBSERVATION_FIELDS = (
    "config_content_match_services",
    "config_exact_services",
    "config_invalid_services",
    "config_readonly_services",
    "config_writable_services",
)
_EVIDENCE_REASON_CODES = frozenset(
    {
        "directory_invalid",
        "duplicate_service",
        "missing_service",
        "no_acceptance",
        "no_candidates",
        "schema_invalid",
        "traversal_limit",
    }
)
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
    "staging_copy_invalid": "field_hashes",
    "staging_digest_invalid": "field_hashes",
    "staging_extract_invalid": "field_hashes",
    "staging_invalid": "field_hashes",
    "staging_target_invalid": "field_hashes",
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
        "baseline_candidate_ready",
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
        "evidence_ready",
        "fingerprint_failed",
        "health_invalid",
        "host_client_active",
        "internal_failure",
        "invalid_arguments",
        "keepalive_active",
        "legacy_evidence_ready",
        "native_smoke_failed",
        "native_smoke_passed",
        "operator_state_invalid",
        "process_uniqueness_invalid",
        "provenance_invalid",
        "restoration_failed_paused",
        "restoration_passed",
        "snapshot_captured",
        "snapshot_verified",
        "runtime_baseline_candidate_ready",
        "single_writer_invalid",
        "signal_invalid",
        "signal_passed",
        "staging_copy_invalid",
        "staging_digest_invalid",
        "staging_extract_invalid",
        "staging_invalid",
        "staging_target_invalid",
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


class EvidenceFailure(OperatorFailure):  # noqa: N818 - fixed bounded diagnostic
    """Accepted-evidence failure with only fixed codes and bounded integer counts."""

    def __init__(
        self,
        reason: str,
        *,
        candidate_count: int = 0,
        valid_record_count: int = 0,
    ):
        super().__init__("evidence_invalid")
        self.reason = reason if reason in _EVIDENCE_REASON_CODES else "schema_invalid"
        self.candidate_count = max(0, min(candidate_count, MAX_EVIDENCE_CANDIDATES))
        self.valid_record_count = max(0, min(valid_record_count, MAX_EVIDENCE_JSON_NODES))


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
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or stat.S_IMODE(file_stat.st_mode) != 0o600
        or file_stat.st_size > MAX_SOURCE_BYTES
    ):
        raise ValueError("invalid snapshot")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, encoding="utf-8", errors="strict") as handle:
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
        "runtime_baseline",
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
        "runtime_baseline": {
            "candidate_set_sha256": None,
            "compose_observation": None,
            "config_content_sha256": None,
            "config_mount_observation": None,
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
    if not (
        isinstance(error_counts, dict)
        and set(error_counts) == set(_TRADING_SERVICES)
        and all(
            item is None or (isinstance(item, int) and item >= 0)
            for item in error_counts.values()
        )
    ):
        return False
    runtime_baseline = value.get("runtime_baseline")
    if not isinstance(runtime_baseline, dict) or set(runtime_baseline) != {
        "candidate_set_sha256",
        "compose_observation",
        "config_content_sha256",
        "config_mount_observation",
    }:
        return False
    candidate_set_sha256 = runtime_baseline["candidate_set_sha256"]
    compose_observation = runtime_baseline["compose_observation"]
    config_content_sha256 = runtime_baseline["config_content_sha256"]
    config_mount_observation = runtime_baseline["config_mount_observation"]
    if candidate_set_sha256 is None:
        return (
            compose_observation is None
            and config_content_sha256 is None
            and config_mount_observation is None
        )
    candidate_material = {
        "compose_observation": compose_observation,
        "config_mount_observation": config_mount_observation,
        "images": {
            name: baseline[name]["image_id"] for name in _TRADING_SERVICES
        },
        "records": {
            name: baseline[name]["record"] for name in _TRADING_SERVICES
        },
    }
    return bool(
        isinstance(candidate_set_sha256, str)
        and _HASH_PATTERN.fullmatch(candidate_set_sha256)
        and _valid_compose_observation(compose_observation)
        and isinstance(config_content_sha256, dict)
        and set(config_content_sha256) == set(_TRADING_SERVICES)
        and all(
            isinstance(item, str) and _HASH_PATTERN.fullmatch(item)
            for item in config_content_sha256.values()
        )
        and _valid_config_mount_observation(config_mount_observation)
        and candidate_set_sha256 == _digest(candidate_material)
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


def _compose_service_hash(base_path: Path, service: str = "spx") -> str:
    if service not in _ALL_SERVICES:
        raise OperatorFailure("compose_semantics_invalid")
    compose_service = str(_SERVICE_SPECS[service]["compose_service"])
    result = _run(
        [
            "docker",
            "compose",
            "-f",
            str(base_path),
            "config",
            "--hash",
            compose_service,
        ],
        timeout=20,
    )
    parts = result.stdout.strip().split()
    if (
        result.returncode != 0
        or result.stderr
        or len(parts) != 2
        or parts[0] != compose_service
        or _HASH_PATTERN.fullmatch(parts[1]) is None
    ):
        raise OperatorFailure("compose_semantics_invalid")
    return parts[1]


def _require_base_image(
    base_path: Path, expected_image_id: str, service: str = "spx"
) -> None:
    if service not in _ALL_SERVICES:
        raise OperatorFailure("compose_semantics_invalid")
    compose_service = str(_SERVICE_SPECS[service]["compose_service"])
    images = _run(
        [
            "docker",
            "compose",
            "-f",
            str(base_path),
            "config",
            "--images",
            compose_service,
        ],
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


def _service_name(value: str) -> str | None:
    matched = [
        name
        for name in _TRADING_SERVICES
        if re.search(rf"(?:^|[^a-z0-9]){name}(?:[^a-z0-9]|$)", value.casefold())
    ]
    return matched[0] if len(matched) == 1 else None


def _records_in_evidence(value: object) -> list[tuple[str, dict[str, object]]]:
    found: list[tuple[str, dict[str, object]]] = []
    stack: list[tuple[object, str | None]] = [(value, None)]
    visited = 0
    while stack:
        current, service_hint = stack.pop()
        visited += 1
        if visited > MAX_EVIDENCE_JSON_NODES:
            raise ValueError("invalid evidence")
        if _valid_record(current):
            if service_hint is not None:
                found.append((service_hint, current))
            continue
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    raise ValueError("invalid evidence")
                key_service = _service_name(key)
                next_hint = key_service if key_service is not None else service_hint
                stack.append((item, next_hint))
        elif isinstance(current, list):
            stack.extend((item, service_hint) for item in current)
    return found


def _read_evidence_value(path: Path) -> object | None:
    file_stat = path.lstat()
    if (
        not stat.S_ISREG(file_stat.st_mode)
        or stat.S_IMODE(file_stat.st_mode) != 0o600
        or file_stat.st_uid != os.getuid()
        or file_stat.st_size > MAX_SOURCE_BYTES
    ):
        return None
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        with os.fdopen(descriptor, encoding="utf-8", errors="strict") as handle:
            descriptor = -1
            value = json.load(handle)
    except (UnicodeDecodeError, ValueError):
        return None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return value


def _evidence_records(
    value: object, relative_name: str
) -> list[tuple[str, dict[str, object]]]:
    if _valid_record(value):
        service = _service_name(relative_name)
        return [] if service is None else [(service, value)]
    try:
        return _records_in_evidence(value)
    except ValueError:
        return []


def _read_evidence_records(path: Path, relative_name: str) -> list[tuple[str, dict[str, object]]]:
    try:
        value = _read_evidence_value(path)
    except OSError:
        return []
    return [] if value is None else _evidence_records(value, relative_name)


def _has_explicit_acceptance(value: object) -> bool:
    stack: list[tuple[str, object]] = [("", value)]
    visited = 0
    while stack:
        context, current = stack.pop()
        visited += 1
        if visited > MAX_EVIDENCE_JSON_NODES:
            return False
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    return False
                normalized_key = key.casefold().replace("-", "_")
                if "accepted" in normalized_key and (
                    "fingerprint" in normalized_key or "baseline" in normalized_key
                ):
                    if isinstance(item, (dict, list)) or item is True:
                        return True
                    if isinstance(item, str) and item.casefold() in {"accepted", "pass", "yes"}:
                        return True
                stack.append((normalized_key, item))
        elif isinstance(current, list):
            stack.extend((context, item) for item in current)
        elif isinstance(current, str):
            normalized = " ".join(current.casefold().replace("_", " ").split())
            if context in {"reviewer_disposition", "disposition"} and normalized == "accepted":
                return True
            if "baseline" in normalized and (
                "accepted" in normalized or normalized.startswith("accept ")
            ):
                return True
    return False


def _has_explicit_rejection(value: object) -> bool:
    stack: list[tuple[str, object]] = [("", value)]
    visited = 0
    rejected_values = {"fail", "inconclusive", "invalid", "no", "rejected"}
    while stack:
        context, current = stack.pop()
        visited += 1
        if visited > MAX_EVIDENCE_JSON_NODES:
            return True
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    return True
                stack.append((key.casefold().replace("-", "_"), item))
        elif isinstance(current, list):
            stack.extend((context, item) for item in current)
        elif isinstance(current, str):
            normalized = " ".join(current.casefold().replace("_", " ").split())
            if context in {"reviewer_disposition", "disposition"} and normalized in {
                "inconclusive",
                "rejected",
            }:
                return True
            if "accepted" in context and normalized in rejected_values:
                return True
        elif current is False and "accepted" in context:
            return True
    return False


def _accepted_fingerprint_hashes(value: object) -> dict[str, set[str]]:
    found = {name: set() for name in _TRADING_SERVICES}
    stack: list[tuple[object, str | None, bool]] = [(value, None, False)]
    visited = 0
    while stack:
        current, service_hint, fingerprint_context = stack.pop()
        visited += 1
        if visited > MAX_EVIDENCE_JSON_NODES:
            return {name: set() for name in _TRADING_SERVICES}
        if isinstance(current, dict):
            for key, item in current.items():
                if not isinstance(key, str):
                    return {name: set() for name in _TRADING_SERVICES}
                key_service = _service_name(key)
                stack.append(
                    (
                        item,
                        key_service if key_service is not None else service_hint,
                        fingerprint_context or "fingerprint" in key.casefold(),
                    )
                )
        elif isinstance(current, list):
            stack.extend(
                (item, service_hint, fingerprint_context) for item in current
            )
        elif (
            isinstance(current, str)
            and service_hint is not None
            and fingerprint_context
            and _HASH_PATTERN.fullmatch(current)
        ):
            found[service_hint].add(current)
    return found


def _legacy_candidate(relative_name: str) -> bool:
    lowered = relative_name.casefold()
    return bool(
        lowered.endswith(".json")
        and any(marker in lowered for marker in _LEGACY_EVIDENCE_MARKERS)
        and _FORBIDDEN_EVIDENCE_NAME_PATTERN.search(lowered) is None
    )


def _discover_reviewed_legacy_snapshots(
    directories: Sequence[Path],
) -> tuple[dict[str, dict[str, object]], int, int]:
    if not directories or len(directories) > 4:
        raise EvidenceFailure("directory_invalid")
    candidates: list[tuple[object, str]] = []
    visited_directories = 0
    visited_files = 0
    for directory in directories:
        try:
            directory_stat = directory.lstat()
        except OSError:
            raise EvidenceFailure("directory_invalid") from None
        if not stat.S_ISDIR(directory_stat.st_mode) or directory.is_symlink():
            raise EvidenceFailure("directory_invalid")
        try:
            for root, child_directories, filenames in os.walk(
                directory, followlinks=False
            ):
                visited_directories += 1
                if visited_directories > MAX_EVIDENCE_DIRECTORIES:
                    raise EvidenceFailure(
                        "traversal_limit", candidate_count=len(candidates)
                    )
                child_directories[:] = [
                    name
                    for name in child_directories
                    if name not in _EVIDENCE_PRUNED_DIRECTORIES
                    and not (Path(root) / name).is_symlink()
                    and any(
                        marker in name.casefold()
                        for marker in _LEGACY_EVIDENCE_DIRECTORY_MARKERS
                    )
                ]
                if len(Path(root).relative_to(directory).parts) >= MAX_EVIDENCE_DEPTH:
                    child_directories[:] = []
                for filename in filenames:
                    visited_files += 1
                    if visited_files > MAX_EVIDENCE_FILES:
                        raise EvidenceFailure(
                            "traversal_limit", candidate_count=len(candidates)
                        )
                    path = Path(root) / filename
                    relative = str(path.relative_to(directory))
                    if not _legacy_candidate(relative):
                        continue
                    if len(candidates) >= MAX_EVIDENCE_CANDIDATES:
                        raise EvidenceFailure(
                            "traversal_limit", candidate_count=len(candidates)
                        )
                    value = _read_evidence_value(path)
                    if value is not None:
                        candidates.append((value, relative))
        except EvidenceFailure:
            raise
        except OSError:
            raise EvidenceFailure(
                "directory_invalid", candidate_count=len(candidates)
            ) from None
    if not candidates:
        raise EvidenceFailure("no_candidates")

    accepted_values = [
        value
        for value, _ in candidates
        if _has_explicit_acceptance(value) and not _has_explicit_rejection(value)
    ]
    if not accepted_values:
        raise EvidenceFailure("no_acceptance", candidate_count=len(candidates))
    accepted_hashes = {name: set() for name in _TRADING_SERVICES}
    for value in accepted_values:
        hashes = _accepted_fingerprint_hashes(value)
        for name in _TRADING_SERVICES:
            accepted_hashes[name].update(hashes[name])

    direct = {name: [] for name in _TRADING_SERVICES}
    linked = {name: [] for name in _TRADING_SERVICES}
    accepted_ids = {id(value) for value in accepted_values}
    valid_record_count = 0
    for value, relative in candidates:
        records = _evidence_records(value, relative)
        valid_record_count += len(records)
        for service, record in records:
            if id(value) in accepted_ids:
                direct[service].append(record)
            elif record["configuration_fingerprint"] in accepted_hashes[service]:
                linked[service].append(record)
    if valid_record_count == 0:
        raise EvidenceFailure("schema_invalid", candidate_count=len(candidates))
    selected = {
        name: direct[name] if direct[name] else linked[name] for name in _TRADING_SERVICES
    }
    selected_count = sum(len(records) for records in selected.values())
    if any(len(records) > 1 for records in selected.values()):
        raise EvidenceFailure(
            "duplicate_service",
            candidate_count=len(candidates),
            valid_record_count=selected_count,
        )
    if any(len(records) == 0 for records in selected.values()):
        raise EvidenceFailure(
            "missing_service",
            candidate_count=len(candidates),
            valid_record_count=selected_count,
        )
    return (
        {name: selected[name][0] for name in _TRADING_SERVICES},
        len(candidates),
        len(accepted_values),
    )


def _discover_accepted_snapshots(directory: Path) -> dict[str, dict[str, object]]:
    try:
        directory_stat = directory.lstat()
    except OSError:
        raise EvidenceFailure("directory_invalid") from None
    if not stat.S_ISDIR(directory_stat.st_mode) or directory.is_symlink():
        raise EvidenceFailure("directory_invalid")
    found: dict[str, list[dict[str, object]]] = {name: [] for name in _TRADING_SERVICES}
    visited_directories = 0
    visited_files = 0
    candidate_files = 0
    try:
        for root, directories, filenames in os.walk(directory, followlinks=False):
            visited_directories += 1
            if visited_directories > MAX_EVIDENCE_DIRECTORIES:
                raise EvidenceFailure(
                    "traversal_limit",
                    candidate_count=candidate_files,
                    valid_record_count=sum(len(records) for records in found.values()),
                )
            directories[:] = [
                name
                for name in directories
                if name not in _EVIDENCE_PRUNED_DIRECTORIES
                and not (Path(root) / name).is_symlink()
            ]
            if len(Path(root).relative_to(directory).parts) >= MAX_EVIDENCE_DEPTH:
                directories[:] = []
            for filename in filenames:
                visited_files += 1
                if visited_files > MAX_EVIDENCE_FILES:
                    raise EvidenceFailure(
                        "traversal_limit",
                        candidate_count=candidate_files,
                        valid_record_count=sum(len(records) for records in found.values()),
                    )
                path = Path(root) / filename
                relative = str(path.relative_to(directory)).casefold()
                if not relative.endswith(".json") or not any(
                    marker in relative for marker in _EVIDENCE_MARKERS
                ):
                    continue
                candidate_files += 1
                if candidate_files > MAX_EVIDENCE_CANDIDATES:
                    raise EvidenceFailure(
                        "traversal_limit",
                        candidate_count=candidate_files,
                        valid_record_count=sum(len(records) for records in found.values()),
                    )
                for service, record in _read_evidence_records(path, relative):
                    found[service].append(record)
    except EvidenceFailure:
        raise
    except OSError:
        raise EvidenceFailure(
            "directory_invalid",
            candidate_count=candidate_files,
            valid_record_count=sum(len(records) for records in found.values()),
        ) from None
    valid_record_count = sum(len(records) for records in found.values())
    if candidate_files == 0:
        raise EvidenceFailure("no_candidates")
    if valid_record_count == 0:
        raise EvidenceFailure("schema_invalid", candidate_count=candidate_files)
    if any(len(records) > 1 for records in found.values()):
        raise EvidenceFailure(
            "duplicate_service",
            candidate_count=candidate_files,
            valid_record_count=valid_record_count,
        )
    if any(len(records) == 0 for records in found.values()):
        raise EvidenceFailure(
            "missing_service",
            candidate_count=candidate_files,
            valid_record_count=valid_record_count,
        )
    return {name: records[0] for name, records in found.items()}


def _accepted_snapshots(args: argparse.Namespace) -> dict[str, dict[str, object]]:
    explicit = (args.accepted_spx, args.accepted_ndx, args.accepted_xsp)
    reviewed_roots = getattr(args, "reviewed_evidence_root", None)
    if reviewed_roots:
        if args.accepted_directory is not None or any(path is not None for path in explicit):
            raise OperatorFailure("invalid_arguments")
        return _discover_reviewed_legacy_snapshots(reviewed_roots)[0]
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


def _runtime_config_paths(args: argparse.Namespace) -> dict[str, Path]:
    paths = {
        "spx": getattr(args, "spx_config", None),
        "ndx": getattr(args, "ndx_config", None),
        "xsp": getattr(args, "xsp_config", None),
    }
    if any(not isinstance(path, Path) for path in paths.values()):
        raise OperatorFailure("invalid_arguments")
    return paths  # type: ignore[return-value]


def _runtime_prepare_candidate(args: argparse.Namespace) -> dict[str, object] | None:
    evidence = getattr(args, "accepted_runtime_baseline", None)
    digest = getattr(args, "accepted_runtime_digest", None)
    legacy_inputs = (
        getattr(args, "accepted_directory", None),
        getattr(args, "accepted_spx", None),
        getattr(args, "accepted_ndx", None),
        getattr(args, "accepted_xsp", None),
        getattr(args, "reviewed_evidence_root", None),
    )
    if evidence is None and digest is None:
        return None
    if (
        not isinstance(evidence, Path)
        or not isinstance(digest, str)
        or any(item for item in legacy_inputs)
    ):
        raise OperatorFailure("invalid_arguments")
    _runtime_config_paths(args)
    return _accepted_runtime_baseline(evidence, digest)


def _runtime_mode(state: dict[str, Any]) -> bool:
    return state["runtime_baseline"]["candidate_set_sha256"] is not None


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


def _write_bounded_evidence_record(path: Path, value: dict[str, object]) -> None:
    if not path.is_absolute() or path.exists():
        raise OperatorFailure("evidence_invalid")
    payload = (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()
    if len(payload) > MAX_SOURCE_BYTES:
        raise OperatorFailure("evidence_invalid")
    try:
        _write_private_bytes(path, payload)
    except OSError:
        raise OperatorFailure("evidence_invalid") from None


def _legacy_evidence_capture(
    args: argparse.Namespace,
) -> tuple[bool, dict[str, object]]:
    window_start, window_end, approval_hash = _approved_window(
        args.approval_reference,
        args.window_start_utc,
        args.window_end_utc,
    )
    archive_sha256 = _validate_archive(
        args.archive,
        args.approved_sha,
        args.expected_archive_sha256,
    )
    operator_sha = _archive_member_sha256(
        args.archive, "src/butterfly_guy/scripts/credential_proof_fingerprint.py"
    )
    if _sha256_file(Path(__file__).resolve(), max_bytes=MAX_SOURCE_BYTES) != operator_sha:
        raise OperatorFailure("provenance_invalid")

    started = int(time.time())
    succeeded = False
    try:
        snapshots, candidate_count, acceptance_count = (
            _discover_reviewed_legacy_snapshots(args.evidence_root)
        )
        result: dict[str, object] = {
            "acceptance_count": acceptance_count,
            "candidate_count": candidate_count,
            "code": "legacy_evidence_ready",
            "service_count": len(snapshots),
            "status": "ok",
            "valid_record_count": len(snapshots),
        }
        succeeded = True
    except EvidenceFailure as exc:
        result = {
            "candidate_count": exc.candidate_count,
            "code": exc.code,
            "reason": exc.reason,
            "status": "error",
            "valid_record_count": exc.valid_record_count,
        }

    record: dict[str, object] = {
        "approval_reference_sha256": approval_hash,
        "approved_sha": args.approved_sha,
        "archive_sha256": archive_sha256,
        "credential_read": False,
        "ended_utc": int(time.time()),
        "evidence_type": "legacy_baseline_locator",
        "locator_result": result,
        "retry_count": 0,
        "schema_version": LEGACY_EVIDENCE_RECORD_VERSION,
        "service_mutation": False,
        "schwab_request": False,
        "started_utc": started,
        "token_read": False,
        "window_end_utc": window_end,
        "window_start_utc": window_start,
    }
    _write_bounded_evidence_record(args.evidence_output, record)
    return succeeded, result


def _reviewed_paper_configs(paths: Sequence[Path]) -> bool:
    if len(paths) != len(_TRADING_SERVICES):
        return False
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            return False
        paper_values = re.findall(
            r"(?m)^\s*paper_trading:\s*(true|false)\s*(?:#.*)?$", text
        )
        live_values = re.findall(
            r"(?m)^\s*allow_live_trading:\s*(true|false)\s*(?:#.*)?$", text
        )
        if paper_values != ["true"] or any(value != "false" for value in live_values):
            return False
    return True


def _runtime_direct_access(inspected: dict[str, Any]) -> bool:
    config = inspected.get("Config")
    if not isinstance(config, dict) or not isinstance(config.get("Env"), list):
        return False
    values: dict[str, str] = {}
    for item in config["Env"]:
        if not isinstance(item, str) or "=" not in item:
            return False
        key, value = item.split("=", 1)
        if not key or key in values:
            return False
        values[key] = value
    return bool(
        values.get("SCHWAB_ACCESS_MODE", "direct") == "direct"
        and "SCHWAB_GATEWAY_URL" not in values
        and "SCHWAB_GATEWAY_API_KEY" not in values
    )


def _runtime_config_mount_status(
    inspected: dict[str, Any], config_path: Path, service: str
) -> tuple[str, str | None]:
    if service not in _TRADING_SERVICES:
        return "invalid", None
    mounts = inspected.get("Mounts")
    if not isinstance(mounts, list):
        return "invalid", None
    try:
        reviewed_source = config_path.resolve(strict=True)
    except OSError:
        return "invalid", None
    matching_mounts = [
        mount
        for mount in mounts
        if isinstance(mount, dict)
        and mount.get("Destination") == _RUNTIME_CONFIG_DESTINATIONS[service]
    ]
    if len(matching_mounts) != 1:
        return "invalid", None
    mount = matching_mounts[0]
    mode = mount.get("Mode")
    source = mount.get("Source")
    if not (
        mount.get("Type") == "bind"
        and isinstance(source, str)
        and source.startswith("/")
        and len(source) <= 4096
        and "\x00" not in source
        and isinstance(mode, str)
        and isinstance(mount.get("RW"), bool)
    ):
        return "invalid", None
    mode_options = mode.split(",") if mode else []
    if mount["RW"] is False and "ro" in mode_options:
        permission = "readonly"
    elif mount["RW"] is True and (not mode_options or "rw" in mode_options):
        permission = "writable"
    else:
        return "invalid", None
    source_path = Path(source)
    if source_path.name != config_path.name or source_path.parent.name != "configs":
        return "invalid", permission
    try:
        resolved_source = source_path.resolve(strict=True)
        if resolved_source == reviewed_source:
            return "exact", permission
        if _sha256_file(source_path) == _sha256_file(reviewed_source):
            return "content_match", permission
    except (OSError, OperatorFailure, ValueError):
        return "invalid", permission
    return "invalid", permission


def _config_mount_observation(
    inspections: dict[str, dict[str, Any]], config_paths: dict[str, Path]
) -> dict[str, list[str]]:
    observation = {field: [] for field in _CONFIG_MOUNT_OBSERVATION_FIELDS}
    status_fields = {
        "content_match": "config_content_match_services",
        "exact": "config_exact_services",
        "invalid": "config_invalid_services",
    }
    permission_fields = {
        "readonly": "config_readonly_services",
        "writable": "config_writable_services",
    }
    for name in _TRADING_SERVICES:
        status, permission = _runtime_config_mount_status(
            inspections[name], config_paths[name], name
        )
        observation[status_fields.get(status, "config_invalid_services")].append(name)
        if permission in permission_fields:
            observation[permission_fields[permission]].append(name)
    return observation


def _runtime_config_content_hashes(
    inspections: dict[str, dict[str, Any]],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in _TRADING_SERVICES:
        mounts = inspections[name].get("Mounts")
        if not isinstance(mounts, list):
            raise OperatorFailure("baseline_mismatch")
        matching = [
            mount
            for mount in mounts
            if isinstance(mount, dict)
            and mount.get("Destination") == _RUNTIME_CONFIG_DESTINATIONS[name]
        ]
        if len(matching) != 1:
            raise OperatorFailure("baseline_mismatch")
        source = matching[0].get("Source")
        if not (
            matching[0].get("Type") == "bind"
            and isinstance(source, str)
            and source.startswith("/")
            and len(source) <= 4096
            and "\x00" not in source
        ):
            raise OperatorFailure("baseline_mismatch")
        try:
            hashes[name] = _sha256_file(Path(source), max_bytes=MAX_SOURCE_BYTES)
        except (OSError, OperatorFailure, ValueError):
            raise OperatorFailure("baseline_mismatch") from None
    return hashes


def _valid_config_mount_observation(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(_CONFIG_MOUNT_OBSERVATION_FIELDS):
        return False
    for field in _CONFIG_MOUNT_OBSERVATION_FIELDS:
        services = value[field]
        if (
            not isinstance(services, list)
            or any(name not in _TRADING_SERVICES for name in services)
            or services != [name for name in _TRADING_SERVICES if name in services]
        ):
            return False
    content_observed = [
        name
        for field in (
            "config_content_match_services",
            "config_exact_services",
            "config_invalid_services",
        )
        for name in value[field]
    ]
    permission_observed = [
        name
        for field in ("config_readonly_services", "config_writable_services")
        for name in value[field]
    ]
    return bool(
        len(content_observed) == len(set(content_observed))
        and set(content_observed) == set(_TRADING_SERVICES)
        and len(permission_observed) == len(set(permission_observed))
        and set(permission_observed) == set(_TRADING_SERVICES)
    )


def _compose_observation(
    base_compose: Path, records: dict[str, dict[str, object]]
) -> dict[str, list[str]]:
    invalid_services: list[str] = []
    matched_services: list[str] = []
    mismatched_services: list[str] = []
    for name in _TRADING_SERVICES:
        try:
            expected_hash = _compose_service_hash(base_compose, name)
        except OperatorFailure:
            invalid_services.append(name)
            continue
        if expected_hash == records[name]["compose_config_hash"]:
            matched_services.append(name)
        else:
            mismatched_services.append(name)
    return {
        "invalid_services": invalid_services,
        "matched_services": matched_services,
        "mismatched_services": mismatched_services,
    }


def _valid_compose_observation(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(_COMPOSE_OBSERVATION_FIELDS):
        return False
    observed: list[str] = []
    for field in _COMPOSE_OBSERVATION_FIELDS:
        services = value[field]
        if (
            not isinstance(services, list)
            or any(name not in _TRADING_SERVICES for name in services)
            or services != [name for name in _TRADING_SERVICES if name in services]
        ):
            return False
        observed.extend(services)
    return len(observed) == len(set(observed)) and set(observed) == set(_TRADING_SERVICES)


def _baseline_candidate_capture(
    args: argparse.Namespace,
) -> tuple[bool, dict[str, object]]:
    window_start, window_end, approval_hash = _approved_window(
        args.approval_reference,
        args.window_start_utc,
        args.window_end_utc,
    )
    archive_sha256 = _validate_archive(
        args.archive,
        args.approved_sha,
        args.expected_archive_sha256,
    )
    operator_sha = _archive_member_sha256(
        args.archive, "src/butterfly_guy/scripts/credential_proof_fingerprint.py"
    )
    if _sha256_file(Path(__file__).resolve(), max_bytes=MAX_SOURCE_BYTES) != operator_sha:
        raise OperatorFailure("provenance_invalid")

    checks = {name: "pending" for name in _BASELINE_CANDIDATE_CHECKS}
    started = int(time.time())
    current_check = "reviewed_sources"
    candidate: dict[str, object] | None = None
    failure_fields: dict[str, object] = {}
    succeeded = False
    try:
        _require_reviewed_file(args.base_compose, args.archive, "infra/docker-compose.yml")
        config_members = {
            "spx": "configs/config.yaml",
            "ndx": "configs/config_ndx.yaml",
            "xsp": "configs/config_xsp.yaml",
        }
        config_paths = {
            "spx": args.spx_config,
            "ndx": args.ndx_config,
            "xsp": args.xsp_config,
        }
        for service, member in config_members.items():
            _require_reviewed_file(config_paths[service], args.archive, member)
        checks[current_check] = "pass"

        current_check = "paper_mode"
        if not _reviewed_paper_configs(list(config_paths.values())):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        inspections = _inspect_all()
        current_check = "running_unpaused"
        if any(not _container_running(inspections[name]) for name in _ALL_SERVICES):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        current_check = "no_staging"
        records = {name: build_record(inspections[name]) for name in _ALL_SERVICES}
        if any(record["staging_tmpfs_present"] is not False for record in records.values()):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        current_check = "direct_access"
        if any(not _runtime_direct_access(inspections[name]) for name in _TRADING_SERVICES):
            raise OperatorFailure("baseline_mismatch")
        if _matching_host_processes("run_schwab_gateway.py"):
            raise OperatorFailure("host_client_active")
        checks[current_check] = "pass"

        current_check = "health"
        _run_health_checks()
        checks[current_check] = "pass"

        current_check = "process_uniqueness"
        service_pids = _run_uniqueness_checks()
        checks[current_check] = "pass"

        current_check = "candidate_ownership"
        _require_candidate_ownership(inspections["candidate"])
        checks[current_check] = "pass"

        current_check = "no_writers"
        _require_no_host_writers()
        _require_no_unowned_runtime_processes(list(service_pids.values()))
        checks[current_check] = "pass"

        images: dict[str, str] = {}
        current_check = "compose_hashes"
        compose = _compose_observation(args.base_compose, records)
        compose_invalid = compose["invalid_services"]
        compose_mismatches = compose["mismatched_services"]
        if compose_invalid:
            failure_fields["invalid_services"] = compose_invalid
        if compose_mismatches:
            failure_fields["mismatched_services"] = compose_mismatches
        if compose_invalid or compose_mismatches:
            raise OperatorFailure("compose_semantics_invalid")
        checks[current_check] = "pass"

        current_check = "images"
        for name in _TRADING_SERVICES:
            _, image_id = _container_identity(inspections[name])
            _require_base_image(args.base_compose, image_id, name)
            images[name] = image_id
        checks[current_check] = "pass"

        accepted_records = {name: records[name] for name in _TRADING_SERVICES}
        accepted_images = {name: images[name] for name in _TRADING_SERVICES}
        candidate_set_sha256 = _digest(
            {"images": accepted_images, "records": accepted_records}
        )
        candidate = {
            "candidate_set_sha256": candidate_set_sha256,
            "images": accepted_images,
            "records": accepted_records,
        }
        result: dict[str, object] = {
            "candidate_set_sha256": candidate_set_sha256,
            "code": "baseline_candidate_ready",
            "service_count": len(accepted_records),
            "status": "ok",
        }
        succeeded = True
    except OperatorFailure as exc:
        checks[current_check] = "fail"
        result = {"code": exc.code, **failure_fields, "status": "error"}
    except (OSError, ValueError):
        checks[current_check] = "fail"
        result = {"code": "evidence_invalid", "status": "error"}

    evidence: dict[str, object] = {
        "approval_reference_sha256": approval_hash,
        "approved_sha": args.approved_sha,
        "archive_sha256": archive_sha256,
        "candidate": candidate,
        "checks": checks,
        "credential_read": False,
        "ended_utc": int(time.time()),
        "evidence_type": "baseline_candidate",
        "result": result,
        "retry_count": 0,
        "schema_version": LEGACY_EVIDENCE_RECORD_VERSION,
        "service_mutation": False,
        "schwab_request": False,
        "started_utc": started,
        "token_read": False,
        "window_end_utc": window_end,
        "window_start_utc": window_start,
    }
    _write_bounded_evidence_record(args.evidence_output, evidence)
    return succeeded, result


def _baseline_candidate_status(path: Path) -> tuple[str, str, dict[str, object]]:
    try:
        value = json.loads(_read_private_bytes(path).decode("utf-8", errors="strict"))
    except (OperatorFailure, UnicodeError, ValueError):
        raise OperatorFailure("evidence_invalid") from None
    expected_fields = {
        "approval_reference_sha256",
        "approved_sha",
        "archive_sha256",
        "candidate",
        "checks",
        "credential_read",
        "ended_utc",
        "evidence_type",
        "result",
        "retry_count",
        "schema_version",
        "service_mutation",
        "schwab_request",
        "started_utc",
        "token_read",
        "window_end_utc",
        "window_start_utc",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise OperatorFailure("evidence_invalid")
    if not (
        value["schema_version"] == LEGACY_EVIDENCE_RECORD_VERSION
        and value["evidence_type"] == "baseline_candidate"
        and isinstance(value["approved_sha"], str)
        and _GIT_SHA_PATTERN.fullmatch(value["approved_sha"])
        and isinstance(value["archive_sha256"], str)
        and _HASH_PATTERN.fullmatch(value["archive_sha256"])
        and isinstance(value["approval_reference_sha256"], str)
        and _HASH_PATTERN.fullmatch(value["approval_reference_sha256"])
        and value["retry_count"] == 0
        and value["service_mutation"] is False
        and value["credential_read"] is False
        and value["token_read"] is False
        and value["schwab_request"] is False
        and all(
            isinstance(value[name], int) and value[name] > 0
            for name in ("started_utc", "ended_utc", "window_start_utc", "window_end_utc")
        )
        and value["started_utc"] <= value["ended_utc"]
        and value["window_start_utc"] <= value["started_utc"] <= value["window_end_utc"]
    ):
        raise OperatorFailure("evidence_invalid")
    checks = value["checks"]
    result = value["result"]
    if (
        not isinstance(checks, dict)
        or set(checks) != set(_BASELINE_CANDIDATE_CHECKS)
        or any(item not in {"pending", "pass", "fail"} for item in checks.values())
        or not isinstance(result, dict)
    ):
        raise OperatorFailure("evidence_invalid")

    candidate = value["candidate"]
    if candidate is None:
        failed = [name for name, result_value in checks.items() if result_value == "fail"]
        result_fields = set(result)
        allowed_result_fields = {"code", "status"}
        if failed == ["compose_hashes"]:
            allowed_result_fields.update({"invalid_services", "mismatched_services"})
        invalid_services = result.get("invalid_services")
        mismatches = result.get("mismatched_services")
        if (
            len(failed) != 1
            or not {"code", "status"}.issubset(result_fields)
            or not result_fields.issubset(allowed_result_fields)
            or result.get("status") != "error"
            or result.get("code") not in _RESULT_CODES
            or (
                "invalid_services" in result
                and (
                    not isinstance(invalid_services, list)
                    or not invalid_services
                    or any(name not in _TRADING_SERVICES for name in invalid_services)
                    or len(invalid_services) != len(set(invalid_services))
                )
            )
            or (
                "mismatched_services" in result
                and (
                    not isinstance(mismatches, list)
                    or not mismatches
                    or any(name not in _TRADING_SERVICES for name in mismatches)
                    or len(mismatches) != len(set(mismatches))
                )
            )
            or (
                isinstance(invalid_services, list)
                and isinstance(mismatches, list)
                and not set(invalid_services).isdisjoint(mismatches)
            )
        ):
            raise OperatorFailure("evidence_invalid")
        fields: dict[str, object] = {"failed_check": failed[0]}
        if "invalid_services" in result:
            fields["invalid_services"] = invalid_services
        if "mismatched_services" in result:
            fields["mismatched_services"] = mismatches
        return "error", str(result["code"]), fields

    if not isinstance(candidate, dict) or set(candidate) != {
        "candidate_set_sha256",
        "images",
        "records",
    }:
        raise OperatorFailure("evidence_invalid")
    images = candidate["images"]
    records = candidate["records"]
    candidate_hash = candidate["candidate_set_sha256"]
    if not (
        isinstance(images, dict)
        and set(images) == set(_TRADING_SERVICES)
        and all(
            isinstance(item, str) and _IMAGE_ID_PATTERN.fullmatch(item)
            for item in images.values()
        )
        and isinstance(records, dict)
        and set(records) == set(_TRADING_SERVICES)
        and all(_valid_record(item) for item in records.values())
        and isinstance(candidate_hash, str)
        and _HASH_PATTERN.fullmatch(candidate_hash)
        and candidate_hash == _digest({"images": images, "records": records})
        and all(item == "pass" for item in checks.values())
        and result
        == {
            "candidate_set_sha256": candidate_hash,
            "code": "baseline_candidate_ready",
            "service_count": len(_TRADING_SERVICES),
            "status": "ok",
        }
    ):
        raise OperatorFailure("evidence_invalid")
    return "ok", "baseline_candidate_ready", {
        "candidate_set_sha256": candidate_hash,
        "service_count": len(_TRADING_SERVICES),
    }


def _runtime_baseline_capture(
    args: argparse.Namespace,
) -> tuple[bool, dict[str, object]]:
    window_start, window_end, approval_hash = _approved_window(
        args.approval_reference,
        args.window_start_utc,
        args.window_end_utc,
    )
    archive_sha256 = _validate_archive(
        args.archive,
        args.approved_sha,
        args.expected_archive_sha256,
    )
    operator_sha = _archive_member_sha256(
        args.archive, "src/butterfly_guy/scripts/credential_proof_fingerprint.py"
    )
    if _sha256_file(Path(__file__).resolve(), max_bytes=MAX_SOURCE_BYTES) != operator_sha:
        raise OperatorFailure("provenance_invalid")

    checks = {name: "pending" for name in _RUNTIME_BASELINE_CHECKS}
    started = int(time.time())
    current_check = "reviewed_sources"
    candidate: dict[str, object] | None = None
    failure_fields: dict[str, object] = {}
    succeeded = False
    try:
        _require_reviewed_file(args.base_compose, args.archive, "infra/docker-compose.yml")
        config_members = {
            "spx": "configs/config.yaml",
            "ndx": "configs/config_ndx.yaml",
            "xsp": "configs/config_xsp.yaml",
        }
        config_paths = {
            "spx": args.spx_config,
            "ndx": args.ndx_config,
            "xsp": args.xsp_config,
        }
        for service, member in config_members.items():
            _require_reviewed_file(config_paths[service], args.archive, member)
        checks[current_check] = "pass"

        current_check = "paper_mode"
        if not _reviewed_paper_configs(list(config_paths.values())):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        inspections = _inspect_all()
        current_check = "running_unpaused"
        if any(not _container_running(inspections[name]) for name in _ALL_SERVICES):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        current_check = "no_staging"
        records = {name: build_record(inspections[name]) for name in _ALL_SERVICES}
        if any(record["staging_tmpfs_present"] is not False for record in records.values()):
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        current_check = "runtime_config_mounts"
        config_mounts = _config_mount_observation(inspections, config_paths)
        if config_mounts["config_invalid_services"]:
            failure_fields["invalid_config_services"] = config_mounts[
                "config_invalid_services"
            ]
            raise OperatorFailure("baseline_mismatch")
        checks[current_check] = "pass"

        current_check = "direct_access"
        if any(not _runtime_direct_access(inspections[name]) for name in _TRADING_SERVICES):
            raise OperatorFailure("baseline_mismatch")
        if _matching_host_processes("run_schwab_gateway.py"):
            raise OperatorFailure("host_client_active")
        checks[current_check] = "pass"

        current_check = "health"
        _run_health_checks()
        checks[current_check] = "pass"

        current_check = "process_uniqueness"
        service_pids = _run_uniqueness_checks()
        checks[current_check] = "pass"

        current_check = "candidate_ownership"
        _require_candidate_ownership(inspections["candidate"])
        checks[current_check] = "pass"

        current_check = "no_writers"
        _require_no_host_writers()
        _require_no_unowned_runtime_processes(list(service_pids.values()))
        checks[current_check] = "pass"

        current_check = "images"
        images = {
            name: _container_identity(inspections[name])[1]
            for name in _TRADING_SERVICES
        }
        checks[current_check] = "pass"

        compose = _compose_observation(args.base_compose, records)
        accepted_records = {name: records[name] for name in _TRADING_SERVICES}
        candidate_material = {
            "compose_observation": compose,
            "config_mount_observation": config_mounts,
            "images": images,
            "records": accepted_records,
        }
        candidate_set_sha256 = _digest(candidate_material)
        candidate = {
            "candidate_set_sha256": candidate_set_sha256,
            **candidate_material,
        }
        result: dict[str, object] = {
            "candidate_set_sha256": candidate_set_sha256,
            **compose,
            **config_mounts,
            "code": "runtime_baseline_candidate_ready",
            "service_count": len(accepted_records),
            "status": "ok",
        }
        succeeded = True
    except OperatorFailure as exc:
        checks[current_check] = "fail"
        result = {"code": exc.code, **failure_fields, "status": "error"}
    except (OSError, ValueError):
        checks[current_check] = "fail"
        result = {"code": "evidence_invalid", "status": "error"}

    evidence: dict[str, object] = {
        "approval_reference_sha256": approval_hash,
        "approved_sha": args.approved_sha,
        "archive_sha256": archive_sha256,
        "candidate": candidate,
        "checks": checks,
        "credential_read": False,
        "ended_utc": int(time.time()),
        "evidence_type": "runtime_baseline_candidate",
        "result": result,
        "retry_count": 0,
        "schema_version": LEGACY_EVIDENCE_RECORD_VERSION,
        "service_mutation": False,
        "schwab_request": False,
        "started_utc": started,
        "token_read": False,
        "window_end_utc": window_end,
        "window_start_utc": window_start,
    }
    _write_bounded_evidence_record(args.evidence_output, evidence)
    return succeeded, result


def _read_runtime_baseline_value(path: Path) -> dict[str, object]:
    try:
        value = json.loads(_read_private_bytes(path).decode("utf-8", errors="strict"))
    except (OperatorFailure, UnicodeError, ValueError):
        raise OperatorFailure("evidence_invalid") from None
    if not isinstance(value, dict):
        raise OperatorFailure("evidence_invalid")
    return value


def _runtime_baseline_status_value(
    value: dict[str, object],
) -> tuple[str, str, dict[str, object]]:
    expected_fields = {
        "approval_reference_sha256",
        "approved_sha",
        "archive_sha256",
        "candidate",
        "checks",
        "credential_read",
        "ended_utc",
        "evidence_type",
        "result",
        "retry_count",
        "schema_version",
        "service_mutation",
        "schwab_request",
        "started_utc",
        "token_read",
        "window_end_utc",
        "window_start_utc",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise OperatorFailure("evidence_invalid")
    if not (
        value["schema_version"] == LEGACY_EVIDENCE_RECORD_VERSION
        and value["evidence_type"] == "runtime_baseline_candidate"
        and isinstance(value["approved_sha"], str)
        and _GIT_SHA_PATTERN.fullmatch(value["approved_sha"])
        and isinstance(value["archive_sha256"], str)
        and _HASH_PATTERN.fullmatch(value["archive_sha256"])
        and isinstance(value["approval_reference_sha256"], str)
        and _HASH_PATTERN.fullmatch(value["approval_reference_sha256"])
        and value["retry_count"] == 0
        and value["service_mutation"] is False
        and value["credential_read"] is False
        and value["token_read"] is False
        and value["schwab_request"] is False
        and all(
            isinstance(value[name], int) and value[name] > 0
            for name in ("started_utc", "ended_utc", "window_start_utc", "window_end_utc")
        )
        and value["started_utc"] <= value["ended_utc"]
        and value["window_start_utc"] <= value["started_utc"] <= value["window_end_utc"]
    ):
        raise OperatorFailure("evidence_invalid")
    checks = value["checks"]
    result = value["result"]
    if (
        not isinstance(checks, dict)
        or set(checks) != set(_RUNTIME_BASELINE_CHECKS)
        or any(item not in {"pending", "pass", "fail"} for item in checks.values())
        or not isinstance(result, dict)
    ):
        raise OperatorFailure("evidence_invalid")

    candidate = value["candidate"]
    if candidate is None:
        failed = [name for name, result_value in checks.items() if result_value == "fail"]
        allowed_result_fields = {"code", "status"}
        if failed == ["runtime_config_mounts"]:
            allowed_result_fields.add("invalid_config_services")
        invalid_config_services = result.get("invalid_config_services")
        if (
            len(failed) != 1
            or not {"code", "status"}.issubset(result)
            or not set(result).issubset(allowed_result_fields)
            or result.get("status") != "error"
            or result.get("code") not in _RESULT_CODES
            or (
                "invalid_config_services" in result
                and (
                    not isinstance(invalid_config_services, list)
                    or not invalid_config_services
                    or any(
                        name not in _TRADING_SERVICES
                        for name in invalid_config_services
                    )
                    or invalid_config_services
                    != [
                        name
                        for name in _TRADING_SERVICES
                        if name in invalid_config_services
                    ]
                )
            )
        ):
            raise OperatorFailure("evidence_invalid")
        fields: dict[str, object] = {"failed_check": failed[0]}
        if "invalid_config_services" in result:
            fields["invalid_config_services"] = invalid_config_services
        return "error", str(result["code"]), fields

    if not isinstance(candidate, dict) or set(candidate) != {
        "candidate_set_sha256",
        "compose_observation",
        "config_mount_observation",
        "images",
        "records",
    }:
        raise OperatorFailure("evidence_invalid")
    compose = candidate["compose_observation"]
    config_mounts = candidate["config_mount_observation"]
    images = candidate["images"]
    records = candidate["records"]
    candidate_hash = candidate["candidate_set_sha256"]
    candidate_material = {
        "compose_observation": compose,
        "config_mount_observation": config_mounts,
        "images": images,
        "records": records,
    }
    if not (
        _valid_compose_observation(compose)
        and _valid_config_mount_observation(config_mounts)
        and not config_mounts["config_invalid_services"]
    ):
        raise OperatorFailure("evidence_invalid")
    expected_result = {
        "candidate_set_sha256": candidate_hash,
        **compose,
        **config_mounts,
        "code": "runtime_baseline_candidate_ready",
        "service_count": len(_TRADING_SERVICES),
        "status": "ok",
    }
    if not (
        isinstance(images, dict)
        and set(images) == set(_TRADING_SERVICES)
        and all(
            isinstance(item, str) and _IMAGE_ID_PATTERN.fullmatch(item)
            for item in images.values()
        )
        and isinstance(records, dict)
        and set(records) == set(_TRADING_SERVICES)
        and all(_valid_record(item) for item in records.values())
        and isinstance(candidate_hash, str)
        and _HASH_PATTERN.fullmatch(candidate_hash)
        and candidate_hash == _digest(candidate_material)
        and all(item == "pass" for item in checks.values())
        and result == expected_result
    ):
        raise OperatorFailure("evidence_invalid")
    return "ok", "runtime_baseline_candidate_ready", {
        "candidate_set_sha256": candidate_hash,
        **compose,
        **config_mounts,
        "service_count": len(_TRADING_SERVICES),
    }


def _runtime_baseline_status(path: Path) -> tuple[str, str, dict[str, object]]:
    return _runtime_baseline_status_value(_read_runtime_baseline_value(path))


def _accepted_runtime_baseline(
    path: Path, accepted_digest: str
) -> dict[str, object]:
    if _HASH_PATTERN.fullmatch(accepted_digest) is None:
        raise OperatorFailure("invalid_arguments")
    value = _read_runtime_baseline_value(path)
    status_value, _, fields = _runtime_baseline_status_value(value)
    if (
        status_value != "ok"
        or fields.get("candidate_set_sha256") != accepted_digest
        or not isinstance(value.get("candidate"), dict)
    ):
        raise OperatorFailure("baseline_mismatch")
    return value["candidate"]


def _require_runtime_acceptance(
    args: argparse.Namespace,
    candidate: dict[str, object],
    inspections: dict[str, dict[str, Any]],
    records: dict[str, dict[str, object]],
) -> None:
    config_paths = _runtime_config_paths(args)
    config_members = {
        "spx": "configs/config.yaml",
        "ndx": "configs/config_ndx.yaml",
        "xsp": "configs/config_xsp.yaml",
    }
    for name, member in config_members.items():
        _require_reviewed_file(config_paths[name], args.archive, member)
    if not _reviewed_paper_configs(list(config_paths.values())):
        raise OperatorFailure("baseline_mismatch")
    accepted_records = candidate.get("records")
    accepted_images = candidate.get("images")
    compose_observation = candidate.get("compose_observation")
    config_mount_observation = candidate.get("config_mount_observation")
    if not (
        isinstance(accepted_records, dict)
        and isinstance(accepted_images, dict)
        and all(
            records[name] == accepted_records.get(name)
            and _container_identity(inspections[name])[1] == accepted_images.get(name)
            for name in _TRADING_SERVICES
        )
        and _config_mount_observation(inspections, config_paths)
        == config_mount_observation
        and _compose_observation(args.base_compose, records) == compose_observation
        and all(_runtime_direct_access(inspections[name]) for name in _TRADING_SERVICES)
        and not _matching_host_processes("run_schwab_gateway.py")
    ):
        raise OperatorFailure("baseline_mismatch")


def _require_runtime_acceptance_state(
    args: argparse.Namespace,
    state: dict[str, Any],
    inspections: dict[str, dict[str, Any]],
) -> None:
    records = {name: build_record(inspections[name]) for name in _ALL_SERVICES}
    candidate = {
        "candidate_set_sha256": state["runtime_baseline"]["candidate_set_sha256"],
        "compose_observation": state["runtime_baseline"]["compose_observation"],
        "config_mount_observation": state["runtime_baseline"][
            "config_mount_observation"
        ],
        "images": {
            name: state["baseline"][name]["image_id"] for name in _TRADING_SERVICES
        },
        "records": {
            name: state["baseline"][name]["record"] for name in _TRADING_SERVICES
        },
    }
    _require_runtime_acceptance(args, candidate, inspections, records)
    if (
        _runtime_config_content_hashes(inspections)
        != state["runtime_baseline"]["config_content_sha256"]
    ):
        raise OperatorFailure("baseline_mismatch")


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
        runtime_candidate = _runtime_prepare_candidate(args)
        accepted = (
            runtime_candidate["records"]
            if runtime_candidate is not None
            else _accepted_snapshots(args)
        )
        if not isinstance(accepted, dict):
            raise OperatorFailure("evidence_invalid")
        records: dict[str, dict[str, object]] = {}
        for name in _ALL_SERVICES:
            inspected = inspections[name]
            if not _container_running(inspected):
                raise OperatorFailure("baseline_mismatch")
            container_id, image_id = _container_identity(inspected)
            record = build_record(inspected)
            records[name] = record
            if record["staging_tmpfs_present"] is not False:
                raise OperatorFailure("baseline_mismatch")
            if name in accepted and not records_match_exactly(accepted[name], record):
                raise OperatorFailure("baseline_mismatch")
            state["baseline"][name] = {
                "container_id": container_id,
                "image_id": image_id,
                "record": record,
            }
        if runtime_candidate is not None:
            _require_runtime_acceptance(args, runtime_candidate, inspections, records)
            state["runtime_baseline"] = {
                "candidate_set_sha256": runtime_candidate["candidate_set_sha256"],
                "compose_observation": runtime_candidate["compose_observation"],
                "config_content_sha256": _runtime_config_content_hashes(inspections),
                "config_mount_observation": runtime_candidate[
                    "config_mount_observation"
                ],
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
        if runtime_candidate is None:
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


def _staging_targets(state: dict[str, Any]) -> tuple[str, str, str]:
    root = RUNTIME_STAGING_TMPFS_TARGET if _runtime_mode(state) else STAGING_TMPFS_TARGET
    return root, f"{root}/reviewed.tar", f"{root}/source"


def _staged_operator_command(state: dict[str, Any], *arguments: str) -> list[str]:
    _, _, source_target = _staging_targets(state)
    return [
        "docker",
        "exec",
        "-e",
        f"PYTHONPATH={source_target}/src",
        "butterfly_spx_app",
        "python",
        f"{source_target}/src/butterfly_guy/scripts/credential_proof_fingerprint.py",
        *arguments,
    ]


def _stage_archive(
    archive_path: Path,
    expected_sha256: str,
    *,
    root_target: str = STAGING_TMPFS_TARGET,
) -> None:
    archive_target = f"{root_target}/reviewed.tar"
    source_target = f"{root_target}/source"
    commands = (
        (
            ["docker", "exec", "butterfly_spx_app", "mkdir", "-p", source_target],
            "staging_target_invalid",
        ),
        (
            [
                "docker",
                "cp",
                "--quiet",
                str(archive_path),
                f"butterfly_spx_app:{archive_target}",
            ],
            "staging_copy_invalid",
        ),
        (
            [
                "docker",
                "exec",
                "butterfly_spx_app",
                "tar",
                "-xf",
                archive_target,
                "-C",
                source_target,
            ],
            "staging_extract_invalid",
        ),
    )
    for command, failure_code in commands:
        result = _run(command, timeout=30)
        if result.returncode != 0 or result.stdout or result.stderr:
            raise OperatorFailure(failure_code)
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
        or parts[1] != archive_target
    ):
        raise OperatorFailure("staging_digest_invalid")


def _prepare_runtime_staging() -> None:
    absent = _run(
        ["docker", "exec", "butterfly_spx_app", "test", "!", "-e", RUNTIME_STAGING_TMPFS_TARGET],
        timeout=10,
    )
    if absent.returncode != 0 or absent.stdout or absent.stderr:
        raise OperatorFailure("staging_target_invalid")
    created = _run(
        [
            "docker",
            "exec",
            "butterfly_spx_app",
            "mkdir",
            "-m",
            "700",
            RUNTIME_STAGING_TMPFS_TARGET,
        ],
        timeout=10,
    )
    if created.returncode != 0 or created.stdout or created.stderr:
        raise OperatorFailure("staging_target_invalid")


def _cleanup_runtime_staging() -> None:
    result = _run(
        ["docker", "exec", "butterfly_spx_app", "rm", "-rf", RUNTIME_STAGING_TMPFS_TARGET],
        timeout=15,
    )
    if result.returncode != 0 or result.stdout or result.stderr:
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
        if _runtime_mode(state):
            _require_runtime_acceptance_state(args, state, inspections)
        _run_health_checks()
        service_pids = _run_uniqueness_checks()
        _require_candidate_ownership(inspections["candidate"])
        _require_no_host_writers()
        _require_no_unowned_runtime_processes(list(service_pids.values()))

        mutated = True
        if _runtime_mode(state):
            _prepare_runtime_staging()
            _stage_archive(
                args.archive,
                args.expected_archive_sha256,
                root_target=RUNTIME_STAGING_TMPFS_TARGET,
            )
            _require_runtime_baseline(state, _inspect_all())
        else:
            _recreate_staged(args.base_compose, args.staging_override)
            staged = inspect_container("butterfly_spx_app")
            if (
                not _container_running(staged)
                or _container_identity(staged)[1]
                != state["baseline"]["spx"]["image_id"]
                or not staging_matches_baseline(
                    staged, state["baseline"]["spx"]["record"]
                )
            ):
                raise OperatorFailure("staging_invalid")
            _stage_archive(args.archive, args.expected_archive_sha256)

        _run_exact_json(
            _staged_operator_command(state, "internal-native-smoke"),
            {"code": "native_smoke_passed", "status": "ok"},
            timeout=30,
        )
        state["checks"]["native_smoke"] = "pass"
        _run_exact_json(
            _staged_operator_command(state, "internal-refusal-gate"),
            {"code": "refusal_gate_passed", "status": "ok"},
            timeout=20,
        )
        state["checks"]["refusal_gate"] = "pass"
        if _runtime_mode(state):
            post_smoke_inspections = _inspect_all()
            _require_runtime_baseline(state, post_smoke_inspections)
            _require_runtime_acceptance_state(args, state, post_smoke_inspections)
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
            _staged_operator_command(state, "internal-signal", "--action", "stop"),
            {"code": "signal_passed", "status": "ok"},
        )
        if not all(_container_is_stopped(service) for service in ("ndx", "xsp")):
            raise OperatorFailure("single_writer_invalid")
        _run_exact_json(
            _staged_operator_command(
                state, "internal-signal-status", "--expect", "stopped"
            ),
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


def _resume_spx() -> None:
    result = _run(
        ["docker", "kill", "--signal", "CONT", str(_SERVICE_SPECS["spx"]["container"])],
        timeout=15,
    )
    expected = f"{_SERVICE_SPECS['spx']['container']}\n"
    if result.returncode != 0 or result.stdout != expected or result.stderr:
        raise OperatorFailure("signal_invalid")


def _best_effort_runtime_restore() -> None:
    with contextlib.suppress(Exception):
        _resume_spx()
    for service in ("ndx", "xsp"):
        with contextlib.suppress(Exception):
            inspected = inspect_container(str(_SERVICE_SPECS[service]["container"]))
            state_value = inspected.get("State")
            if isinstance(state_value, dict) and state_value.get("Running") is not True:
                _start_container(service)
    with contextlib.suppress(Exception):
        _cleanup_runtime_staging()


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
            restoration_started = int(time.time())
            if _runtime_mode(state):
                _resume_spx()
            else:
                _validate_rollback_override(
                    args.base_compose, args.rollback_override, expected_image
                )
                _require_base_image(args.base_compose, expected_image)
                if (
                    _compose_service_hash(args.base_compose)
                    != state["baseline"]["spx"]["record"]["compose_config_hash"]
                ):
                    raise OperatorFailure("compose_semantics_invalid")
                _recreate_baseline(args.base_compose, args.rollback_override)
            for service in ("ndx", "xsp"):
                inspected = inspect_container(str(_SERVICE_SPECS[service]["container"]))
                state_value = inspected.get("State")
                if not isinstance(state_value, dict):
                    raise OperatorFailure("docker_inspect_invalid")
                if state_value.get("Running") is not True:
                    _start_container(service)
            if _runtime_mode(state):
                _cleanup_runtime_staging()

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
            if _runtime_mode(state) and (
                _runtime_config_content_hashes(inspections)
                != state["runtime_baseline"]["config_content_sha256"]
            ):
                raise OperatorFailure("baseline_mismatch")
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
            if _runtime_mode(state):
                _best_effort_runtime_restore()
            elif isinstance(expected_image, str):
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
            _staged_operator_command(
                state, "internal-signal-status", "--expect", "stopped"
            ),
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

        _, _, source_target = _staging_targets(state)
        proof_command = [
            "docker",
            "exec",
            "-e",
            f"PYTHONPATH={source_target}/src",
            "butterfly_spx_app",
            "python",
            f"{source_target}/src/butterfly_guy/scripts/probe_schwab_gateway_credentials.py",
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

    evidence_status = subparsers.add_parser("evidence-status", add_help=False)
    evidence_status.add_argument("--accepted-directory", required=True, type=Path)

    legacy_evidence_status = subparsers.add_parser(
        "legacy-evidence-status", add_help=False
    )
    legacy_evidence_status.add_argument(
        "--evidence-root", required=True, action="append", type=Path
    )

    legacy_evidence_capture = subparsers.add_parser(
        "legacy-evidence-capture", add_help=False
    )
    legacy_evidence_capture.add_argument(
        "--evidence-root", required=True, action="append", type=Path
    )
    legacy_evidence_capture.add_argument("--evidence-output", required=True, type=Path)
    legacy_evidence_capture.add_argument("--approved-sha", required=True)
    legacy_evidence_capture.add_argument("--approval-reference", required=True)
    legacy_evidence_capture.add_argument("--window-start-utc", required=True)
    legacy_evidence_capture.add_argument("--window-end-utc", required=True)
    legacy_evidence_capture.add_argument("--archive", required=True, type=Path)
    legacy_evidence_capture.add_argument("--expected-archive-sha256", required=True)

    baseline_candidate_capture = subparsers.add_parser(
        "baseline-candidate-capture", add_help=False
    )
    baseline_candidate_capture.add_argument("--evidence-output", required=True, type=Path)
    baseline_candidate_capture.add_argument("--approved-sha", required=True)
    baseline_candidate_capture.add_argument("--approval-reference", required=True)
    baseline_candidate_capture.add_argument("--window-start-utc", required=True)
    baseline_candidate_capture.add_argument("--window-end-utc", required=True)
    baseline_candidate_capture.add_argument("--archive", required=True, type=Path)
    baseline_candidate_capture.add_argument(
        "--expected-archive-sha256", required=True
    )
    baseline_candidate_capture.add_argument("--base-compose", required=True, type=Path)
    baseline_candidate_capture.add_argument("--spx-config", required=True, type=Path)
    baseline_candidate_capture.add_argument("--ndx-config", required=True, type=Path)
    baseline_candidate_capture.add_argument("--xsp-config", required=True, type=Path)

    baseline_candidate_status = subparsers.add_parser(
        "baseline-candidate-status", add_help=False
    )
    baseline_candidate_status.add_argument("--evidence", required=True, type=Path)

    runtime_baseline_capture = subparsers.add_parser(
        "runtime-baseline-capture", add_help=False
    )
    runtime_baseline_capture.add_argument("--evidence-output", required=True, type=Path)
    runtime_baseline_capture.add_argument("--approved-sha", required=True)
    runtime_baseline_capture.add_argument("--approval-reference", required=True)
    runtime_baseline_capture.add_argument("--window-start-utc", required=True)
    runtime_baseline_capture.add_argument("--window-end-utc", required=True)
    runtime_baseline_capture.add_argument("--archive", required=True, type=Path)
    runtime_baseline_capture.add_argument(
        "--expected-archive-sha256", required=True
    )
    runtime_baseline_capture.add_argument("--base-compose", required=True, type=Path)
    runtime_baseline_capture.add_argument("--spx-config", required=True, type=Path)
    runtime_baseline_capture.add_argument("--ndx-config", required=True, type=Path)
    runtime_baseline_capture.add_argument("--xsp-config", required=True, type=Path)

    runtime_baseline_status = subparsers.add_parser(
        "runtime-baseline-status", add_help=False
    )
    runtime_baseline_status.add_argument("--evidence", required=True, type=Path)

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
    prepare.add_argument("--reviewed-evidence-root", action="append", type=Path)
    prepare.add_argument("--accepted-runtime-baseline", type=Path)
    prepare.add_argument("--accepted-runtime-digest")
    prepare.add_argument("--spx-config", type=Path)
    prepare.add_argument("--ndx-config", type=Path)
    prepare.add_argument("--xsp-config", type=Path)
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
    approval_1.add_argument("--spx-config", type=Path)
    approval_1.add_argument("--ndx-config", type=Path)
    approval_1.add_argument("--xsp-config", type=Path)

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
        if args.command == "evidence-status":
            snapshots = _discover_accepted_snapshots(args.accepted_directory)
            _emit(
                "ok",
                "evidence_ready",
                service_count=len(snapshots),
                valid_record_count=len(snapshots),
            )
            return
        if args.command == "legacy-evidence-status":
            snapshots, candidate_count, acceptance_count = (
                _discover_reviewed_legacy_snapshots(args.evidence_root)
            )
            _emit(
                "ok",
                "legacy_evidence_ready",
                acceptance_count=acceptance_count,
                candidate_count=candidate_count,
                service_count=len(snapshots),
                valid_record_count=len(snapshots),
            )
            return
        if args.command == "legacy-evidence-capture":
            succeeded, result = _legacy_evidence_capture(args)
            status_value = str(result.pop("status"))
            code = str(result.pop("code"))
            _emit(status_value, code, **result)
            if not succeeded:
                raise SystemExit(1)
            return
        if args.command == "baseline-candidate-capture":
            succeeded, result = _baseline_candidate_capture(args)
            status_value = str(result.pop("status"))
            code = str(result.pop("code"))
            _emit(status_value, code, **result)
            if not succeeded:
                raise SystemExit(1)
            return
        if args.command == "baseline-candidate-status":
            status_value, code, fields = _baseline_candidate_status(args.evidence)
            _emit(status_value, code, **fields)
            if status_value == "error":
                raise SystemExit(1)
            return
        if args.command == "runtime-baseline-capture":
            succeeded, result = _runtime_baseline_capture(args)
            status_value = str(result.pop("status"))
            code = str(result.pop("code"))
            _emit(status_value, code, **result)
            if not succeeded:
                raise SystemExit(1)
            return
        if args.command == "runtime-baseline-status":
            status_value, code, fields = _runtime_baseline_status(args.evidence)
            _emit(status_value, code, **fields)
            if status_value == "error":
                raise SystemExit(1)
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
    except EvidenceFailure as exc:
        if args.command in {
            "evidence-status",
            "legacy-evidence-status",
            "legacy-evidence-capture",
            "baseline-candidate-capture",
            "baseline-candidate-status",
            "runtime-baseline-capture",
            "runtime-baseline-status",
        }:
            _emit(
                "error",
                exc.code,
                candidate_count=exc.candidate_count,
                reason=exc.reason,
                valid_record_count=exc.valid_record_count,
            )
        else:
            _emit("error", exc.code)
        raise SystemExit(1) from None
    except OperatorFailure as exc:
        _emit("error", exc.code)
        raise SystemExit(1) from None
    except Exception:
        _emit("error", "internal_failure")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
