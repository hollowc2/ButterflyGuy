"""Capture and verify redacted Docker configuration fingerprints for credential proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
COMPOSE_CONFIG_HASH_LABEL = "com.docker.compose.config-hash"
STAGING_TMPFS_TARGET = "/app/.schwab-credential-proof-runtime"
_HASH_PATTERN = re.compile(r"[0-9a-f]{64}")
_CONTAINER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
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
        raise ValueError("invalid container")
    result = subprocess.run(
        ["docker", "inspect", "--type", "container", name],
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if result.returncode != 0:
        raise ValueError("Docker inspect failed")
    parsed = json.loads(result.stdout)
    if not isinstance(parsed, list) or len(parsed) != 1 or not isinstance(parsed[0], dict):
        raise ValueError("invalid Docker inspect")
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture")
    capture.add_argument("--container", required=True)
    capture.add_argument("--snapshot", required=True, type=Path)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--container", required=True)
    verify.add_argument("--baseline", required=True, type=Path)
    verify.add_argument("--expect", choices=("exact", "staging-only"), required=True)
    verify.add_argument("--snapshot", type=Path)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        inspected = inspect_container(args.container)
        current = build_record(inspected)
        if args.command == "capture":
            if current["staging_tmpfs_present"] is not False:
                raise ValueError("staging mount present")
            write_snapshot(args.snapshot, current)
            print('{"status":"captured"}')
            return

        baseline = read_snapshot(args.baseline)
        if args.snapshot is not None:
            write_snapshot(args.snapshot, current)
        if args.expect == "exact":
            verified = records_match_exactly(baseline, current)
        else:
            verified = staging_matches_baseline(inspected, baseline)
        if not verified:
            raise ValueError("fingerprint mismatch")
        print(json.dumps({"expectation": args.expect, "status": "verified"}, separators=(",", ":")))
    except Exception:
        parser.exit(status=1, message="Credential proof fingerprint failed\n")


if __name__ == "__main__":
    main()
