from __future__ import annotations

import copy
import json
import stat
from pathlib import Path

import pytest

from butterfly_guy.scripts import credential_proof_fingerprint as fingerprint

COMPOSE_HASH = "a" * 64
IMAGE_ID = f"sha256:{'b' * 64}"
STAGING_TARGET = "/app/.schwab-credential-proof-runtime"
SENSITIVE_VALUES = (
    "sensitive-environment-value",
    "/sensitive/host/token/path",
    "sensitive-container-state",
    "sensitive-runtime-exception",
)


def docker_inspect() -> dict:
    return {
        "Id": "volatile-container-id",
        "Created": "volatile-created-time",
        "Image": IMAGE_ID,
        "Config": {
            "Image": "butterfly-guy:reviewed",
            "Cmd": ["python", "-m", "butterfly_guy.scripts.run_live"],
            "Entrypoint": ["/entrypoint"],
            "WorkingDir": "/app",
            "User": "1001:1001",
            "Healthcheck": {"Test": ["CMD", "healthcheck"]},
            "Env": [
                "ZED=last",
                "SCHWAB_SECRET=sensitive-environment-value",
                "ALPHA=first",
            ],
            "Labels": {
                "com.docker.compose.config-hash": COMPOSE_HASH,
                "unrelated-sensitive-label": "sensitive-label-value",
            },
        },
        "HostConfig": {
            "Binds": [
                "/sensitive/host/token/path:/app/tokens.json:rw",
                "/host/config:/app/config.yaml:ro",
            ],
            "PortBindings": {
                "8000/tcp": [
                    {"HostIp": "::1", "HostPort": "8000"},
                    {"HostIp": "127.0.0.1", "HostPort": "8000"},
                ]
            },
            "NetworkMode": "monitoring_net",
            "ReadonlyRootfs": True,
            "RestartPolicy": {"Name": "unless-stopped", "MaximumRetryCount": 0},
            "Tmpfs": {"/tmp": "rw,nosuid,nodev"},
            "CapDrop": ["NET_RAW", "ALL"],
            "SecurityOpt": ["label=disable", "no-new-privileges"],
        },
        "Mounts": [
            {
                "Type": "bind",
                "Source": "/sensitive/host/token/path",
                "Destination": "/app/tokens.json",
                "Mode": "rw",
                "RW": True,
                "Propagation": "rprivate",
            },
            {
                "Type": "bind",
                "Source": "/host/config",
                "Destination": "/app/config.yaml",
                "Mode": "ro",
                "RW": False,
                "Propagation": "rprivate",
            },
        ],
        "NetworkSettings": {
            "Networks": {
                "monitoring_net": {"EndpointID": "volatile-endpoint-id"},
                "audit_net": {"EndpointID": "another-volatile-endpoint-id"},
            }
        },
        "State": {"Status": "running", "Error": "sensitive-container-state"},
    }


def write_record(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")
    path.chmod(0o600)


def test_canonical_fingerprint_is_independent_of_semantically_unordered_fields() -> None:
    original = docker_inspect()
    permuted = copy.deepcopy(original)
    permuted["Config"]["Env"].reverse()
    permuted["HostConfig"]["Binds"].reverse()
    permuted["HostConfig"]["PortBindings"]["8000/tcp"].reverse()
    permuted["HostConfig"]["CapDrop"].reverse()
    permuted["HostConfig"]["SecurityOpt"].reverse()
    permuted["HostConfig"]["Tmpfs"]["/tmp"] = "nodev,rw,nosuid"
    permuted["Mounts"].reverse()
    permuted["NetworkSettings"]["Networks"] = {
        key: permuted["NetworkSettings"]["Networks"][key]
        for key in reversed(permuted["NetworkSettings"]["Networks"])
    }

    assert fingerprint.build_record(original) == fingerprint.build_record(permuted)


@pytest.mark.parametrize(
    ("field", "mutate"),
    [
        ("env", lambda value: value["Config"]["Env"].append("REAL_CHANGE=yes")),
        ("mounts", lambda value: value["Mounts"][0].update({"RW": False})),
        (
            "restart_policy",
            lambda value: value["HostConfig"].update(
                {"RestartPolicy": {"Name": "no", "MaximumRetryCount": 0}}
            ),
        ),
        (
            "networks",
            lambda value: value["NetworkSettings"]["Networks"].update({"new_net": {}}),
        ),
        ("image", lambda value: value.update({"Image": f"sha256:{'c' * 64}"})),
    ],
)
def test_field_hashes_detect_real_configuration_changes(field: str, mutate) -> None:
    baseline = docker_inspect()
    changed = copy.deepcopy(baseline)
    mutate(changed)

    baseline_record = fingerprint.build_record(baseline)
    changed_record = fingerprint.build_record(changed)

    assert changed_record["field_hashes"][field] != baseline_record["field_hashes"][field]
    assert not fingerprint.records_match_exactly(baseline_record, changed_record)


def test_staging_verification_removes_only_the_exact_approved_tmpfs() -> None:
    baseline = fingerprint.build_record(docker_inspect())
    staged_inspect = docker_inspect()
    staged_inspect["Config"]["Labels"]["com.docker.compose.config-hash"] = "d" * 64
    staged_inspect["HostConfig"]["Tmpfs"][STAGING_TARGET] = (
        "size=268435456,nodev,nosuid,exec,rw,mode=1777"
    )
    staged_inspect["Mounts"].append(
        {
            "Type": "tmpfs",
            "Source": "",
            "Destination": STAGING_TARGET,
            "Mode": "rw,nosuid,nodev,exec,size=268435456,mode=1777",
            "RW": True,
            "Propagation": "",
        }
    )

    assert fingerprint.staging_matches_baseline(staged_inspect, baseline)

    staged_inspect["Config"]["Env"].append("UNAPPROVED_CHANGE=yes")
    assert not fingerprint.staging_matches_baseline(staged_inspect, baseline)


def test_cli_writes_mode_0600_bounded_redacted_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot = tmp_path / "baseline.json"
    monkeypatch.setattr(fingerprint, "inspect_container", lambda _name: docker_inspect())

    fingerprint.main(
        ["capture", "--container", "butterfly_spx_app", "--snapshot", str(snapshot)]
    )

    captured = capsys.readouterr()
    stored = snapshot.read_text(encoding="utf-8")
    assert captured.out == '{"code":"snapshot_captured","status":"ok"}\n'
    assert captured.err == ""
    assert len(captured.out) <= 64
    assert stat.S_IMODE(snapshot.stat().st_mode) == 0o600
    assert set(json.loads(stored)) == {
        "compose_config_hash",
        "configuration_fingerprint",
        "field_hashes",
        "schema_version",
        "staging_tmpfs_present",
    }
    for sensitive in SENSITIVE_VALUES:
        assert sensitive not in captured.out
        assert sensitive not in stored
    assert "volatile-container-id" not in stored
    assert "volatile-created-time" not in stored


def test_cli_bounds_docker_failure_without_raw_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_inspect(_name: str) -> dict:
        raise RuntimeError("sensitive-runtime-exception")

    monkeypatch.setattr(fingerprint, "inspect_container", fail_inspect)

    with pytest.raises(SystemExit) as exc:
        fingerprint.main(
            [
                "capture",
                "--container",
                "butterfly_spx_app",
                "--snapshot",
                str(tmp_path / "baseline.json"),
            ]
        )

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert captured.out == '{"code":"internal_failure","status":"error"}\n'
    assert captured.err == ""
    assert "sensitive-runtime-exception" not in captured.out


def test_cli_exact_and_staging_verification_are_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_path = tmp_path / "baseline.json"
    write_record(baseline_path, fingerprint.build_record(docker_inspect()))
    monkeypatch.setattr(fingerprint, "inspect_container", lambda _name: docker_inspect())

    fingerprint.main(
        [
            "verify",
            "--container",
            "butterfly_spx_app",
            "--baseline",
            str(baseline_path),
            "--expect",
            "exact",
        ]
    )

    captured = capsys.readouterr()
    assert captured.out == (
        '{"code":"snapshot_verified","expectation":"exact","status":"ok"}\n'
    )
    assert captured.err == ""
    assert len(captured.out) <= 80


def test_snapshot_reader_rejects_extra_unhashed_fields(tmp_path: Path) -> None:
    record = fingerprint.build_record(docker_inspect())
    record["raw_environment"] = SENSITIVE_VALUES[0]
    path = tmp_path / "unsafe.json"
    write_record(path, record)

    with pytest.raises(ValueError, match="invalid snapshot"):
        fingerprint.read_snapshot(path)
