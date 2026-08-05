from __future__ import annotations

import copy
import hashlib
import io
import json
import stat
import subprocess
import tarfile
import time
from argparse import Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from butterfly_guy.scripts import credential_proof_fingerprint as operator
from tests.test_credential_proof_fingerprint import COMPOSE_HASH, IMAGE_ID, docker_inspect

SENSITIVE = "secret-bearing-subprocess-output"
APPROVED_SHA = "c" * 40
ARCHIVE_SHA = "d" * 64


def result(returncode: int = 0, stdout: str = "", stderr: str = "") -> operator.CapturedProcess:
    return operator.CapturedProcess(returncode, stdout, stderr)


def runtime_inspect(*, image_id: str = IMAGE_ID) -> dict:
    value = docker_inspect()
    value["Id"] = "e" * 64
    value["Image"] = image_id
    value["State"] = {"Status": "running", "Running": True, "Paused": False}
    return value


def populated_state(phase: str = "approval_2_pending") -> dict:
    value = operator._new_state(APPROVED_SHA)
    value["archive_sha256"] = ARCHIVE_SHA
    now = int(time.time())
    value["approval_1"] = {
        "reference_sha256": hashlib.sha256(b"approval-1").hexdigest(),
        "window_start": now - 60,
        "window_end": now + 3600,
    }
    record = operator.build_record(runtime_inspect())
    for name in operator._ALL_SERVICES:
        value["baseline"][name] = {
            "container_id": "e" * 64,
            "image_id": IMAGE_ID,
            "record": copy.deepcopy(record),
        }
    value["phase"] = phase
    value["cron"]["sha256"] = hashlib.sha256(b"").hexdigest()
    value["cron"]["keepalive_entries"] = 0
    value["cron"]["present"] = True
    return value


def write_state(path: Path, value: dict) -> None:
    operator._write_state_new(path, value)


def approval_args(tmp_path: Path) -> Namespace:
    return Namespace(
        state=tmp_path / "state.json",
        approval_reference="approved-in-chat",
        base_compose=tmp_path / "compose.yml",
        rollback_override=tmp_path / "rollback.yml",
        cron_snapshot=tmp_path / "cron.txt",
        archive=tmp_path / "reviewed.tar",
        watchdog_fired=False,
    )


def patch_approval_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator, "_watchdog_active", lambda *_args: True)
    monkeypatch.setattr(operator, "_watchdog_service_active", lambda *_args: False)
    monkeypatch.setattr(operator, "_cancel_watchdog", lambda *_args: None)
    monkeypatch.setattr(operator, "_container_is_stopped", lambda *_args: True)
    monkeypatch.setattr(operator, "_run_exact_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(operator, "_unique_service_pid", lambda *_args, **_kwargs: 101)
    monkeypatch.setattr(operator, "inspect_container", lambda *_args: {})
    monkeypatch.setattr(operator, "_require_candidate_ownership", lambda *_args: None)
    monkeypatch.setattr(operator, "_require_no_host_writers", lambda: None)
    monkeypatch.setattr(operator, "_require_no_unowned_runtime_processes", lambda *_args: None)
    monkeypatch.setattr(operator, "_matching_host_processes", lambda *_args: [])


def test_subprocess_timeout_maps_to_fixed_code(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired([SENSITIVE], 1, output=SENSITIVE.encode())

    monkeypatch.setattr(operator.subprocess, "run", timeout)

    with pytest.raises(operator.OperatorFailure) as exc:
        operator._run(["safe-command"])

    assert exc.value.code == "subprocess_timeout"
    assert SENSITIVE not in str(exc.value)


def test_subprocess_rejects_oversized_and_non_utf8_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.CompletedProcess([], 0, b"x" * (operator.MAX_CAPTURE_BYTES + 1), b"")
    monkeypatch.setattr(operator.subprocess, "run", lambda *_args, **_kwargs: completed)
    with pytest.raises(operator.OperatorFailure, match="subprocess_output_invalid"):
        operator._run(["safe-command"])

    completed = subprocess.CompletedProcess([], 0, b"\xff", b"")
    monkeypatch.setattr(operator.subprocess, "run", lambda *_args, **_kwargs: completed)
    with pytest.raises(operator.OperatorFailure, match="subprocess_output_invalid"):
        operator._run(["safe-command"])


def test_secret_bearing_docker_failure_never_escapes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(1, SENSITIVE, SENSITIVE),
    )

    with pytest.raises(SystemExit):
        operator.main(
            [
                "capture",
                "--container",
                "butterfly_spx_app",
                "--snapshot",
                str(tmp_path / "snapshot.json"),
            ]
        )

    captured = capsys.readouterr()
    assert captured.out == '{"code":"docker_inspect_invalid","status":"error"}\n'
    assert captured.err == ""
    assert SENSITIVE not in captured.out


@pytest.mark.parametrize("header", ["UID PID COMMAND", "PID CMD", "", SENSITIVE])
def test_docker_top_rejects_unsupported_formats(
    header: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stdout=f"{header}\n"))
    with pytest.raises(operator.OperatorFailure, match="docker_top_invalid"):
        operator._docker_top_rows("butterfly_spx_app")


def test_process_uniqueness_rejects_extra_process(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        "PID COMMAND\n"
        "101 python -m butterfly_guy.scripts.run_live\n"
        "102 python unexpected-helper.py\n"
    )
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stdout=output))
    with pytest.raises(operator.OperatorFailure, match="process_uniqueness_invalid"):
        operator._unique_service_pid("spx")


def test_candidate_ownership_requires_one_read_only_token_mount() -> None:
    inspected = runtime_inspect()
    assert not operator._candidate_read_only(inspected)

    inspected["Mounts"][0].update({"Mode": "ro", "RW": False})
    assert operator._candidate_read_only(inspected)

    inspected["Mounts"].append(copy.deepcopy(inspected["Mounts"][0]))
    assert not operator._candidate_read_only(inspected)


def test_health_parser_rejects_malformed_and_secret_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stdout="not-json"))
    assert not operator._health_ok("spx")

    payload = {
        "status": "ok",
        "service": "SPX",
        "timestamp": "2026-08-05T01:02:03",
        "uptime_seconds": 10,
        "secret": SENSITIVE,
    }
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(stdout=json.dumps(payload)),
    )
    assert not operator._health_ok("spx")


def compose_pair() -> tuple[dict, dict]:
    base = {
        "name": "butterfly",
        "services": {
            "app_spx": {
                "command": ["python", "-m", "butterfly_guy.scripts.run_live"],
                "tmpfs": ["/tmp"],
                "cap_drop": ["ALL", "NET_RAW"],
            },
            "app_ndx": {"profiles": ["ndx"]},
        },
    }
    combined = copy.deepcopy(base)
    combined["services"] = {
        "app_ndx": combined["services"]["app_ndx"],
        "app_spx": combined["services"]["app_spx"],
    }
    combined["services"]["app_spx"]["tmpfs"] = [
        "/app/.schwab-credential-proof-runtime:mode=1777,size=256m,nodev,nosuid,exec,rw",
        "/tmp",
    ]
    combined["services"]["app_spx"]["cap_drop"].reverse()
    return base, combined


def test_compose_semantics_accepts_order_permutations(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base, combined = compose_pair()
    responses = iter((base, combined))
    monkeypatch.setattr(operator, "_compose_json", lambda *_args: next(responses))
    operator._validate_compose_semantics(tmp_path / "base", tmp_path / "staging")


def test_compose_semantics_rejects_unexpected_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base, combined = compose_pair()
    combined["services"]["unexpected_writer"] = {"image": "unsafe"}
    responses = iter((base, combined))
    monkeypatch.setattr(operator, "_compose_json", lambda *_args: next(responses))
    with pytest.raises(operator.OperatorFailure, match="compose_semantics_invalid"):
        operator._validate_compose_semantics(tmp_path / "base", tmp_path / "staging")


def test_compose_dry_run_rejects_unexpected_container(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = "DRY-RUN MODE - Container butterfly_spx_app Recreate\nContainer secret_writer Start\n"
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stdout=output))
    with pytest.raises(operator.OperatorFailure, match="compose_dry_run_invalid"):
        operator._validate_compose_dry_run(tmp_path / "base", tmp_path / "staging")


def test_compose_dry_run_accepts_only_target_recreation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = (
        "[+] Running 1/1\n"
        "DRY-RUN MODE - Container butterfly_spx_app Recreated\n"
        "DRY-RUN MODE - Container butterfly_spx_app Started\n"
    )
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stderr=output))
    operator._validate_compose_dry_run(tmp_path / "base", tmp_path / "staging")


def test_compose_action_rejects_secret_bearing_success_output() -> None:
    with pytest.raises(operator.OperatorFailure, match="staging_invalid"):
        operator._validate_compose_action_output(
            result(stderr=f"Container butterfly_spx_app Started\n{SENSITIVE}\n"),
            "staging_invalid",
        )


def write_archive(path: Path) -> None:
    with tarfile.open(path, "w") as archive:
        for name in operator._ARCHIVE_PATHS:
            payload = name.encode()
            member = tarfile.TarInfo(name)
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    path.chmod(0o600)


def test_archive_provenance_and_hash_are_exact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "reviewed.tar"
    write_archive(archive)
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(stdout=f"{APPROVED_SHA}\n"),
    )
    assert operator._validate_archive(archive, APPROVED_SHA, expected) == expected

    with pytest.raises(operator.OperatorFailure, match="archive_mismatch"):
        operator._validate_archive(archive, APPROVED_SHA, ARCHIVE_SHA)


def test_archive_rejects_wrong_embedded_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "reviewed.tar"
    write_archive(archive)
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(stdout=f"{'f' * 40}\n"),
    )
    with pytest.raises(operator.OperatorFailure, match="provenance_invalid"):
        operator._validate_archive(archive, APPROVED_SHA, None)


def test_reviewed_compose_file_must_match_exact_archive_member(tmp_path: Path) -> None:
    archive = tmp_path / "reviewed.tar"
    write_archive(archive)
    member_name = "infra/docker-compose.yml"
    compose = tmp_path / "compose.yml"
    compose.write_bytes(member_name.encode())

    operator._require_reviewed_file(compose, archive, member_name)

    compose.write_text("services: {}\n", encoding="utf-8")
    with pytest.raises(operator.OperatorFailure, match="provenance_invalid"):
        operator._require_reviewed_file(compose, archive, member_name)


def test_container_archive_staging_verifies_every_command_and_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = 0

    def fake_run(command, **_kwargs):
        nonlocal calls
        calls += 1
        if command[:3] == ["docker", "exec", "butterfly_spx_app"] and "sha256sum" in command:
            return result(stdout=f"{ARCHIVE_SHA}  {operator.STAGING_ARCHIVE_TARGET}\n")
        return result()

    monkeypatch.setattr(operator, "_run", fake_run)
    operator._stage_archive(tmp_path / "reviewed.tar", ARCHIVE_SHA)
    assert calls == 4


def test_container_archive_staging_rejects_success_with_unexpected_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(stdout=SENSITIVE),
    )
    with pytest.raises(operator.OperatorFailure, match="staging_invalid"):
        operator._stage_archive(tmp_path / "reviewed.tar", ARCHIVE_SHA)


def test_missing_compose_label_and_wrong_image_fail_closed() -> None:
    missing_label = runtime_inspect()
    missing_label["Config"]["Labels"] = {}
    with pytest.raises(ValueError, match="invalid Docker inspect"):
        operator.build_record(missing_label)

    state = populated_state("approval_1_ready")
    inspections = {
        name: runtime_inspect(image_id=f"sha256:{'9' * 64}")
        for name in operator._ALL_SERVICES
    }
    with pytest.raises(operator.OperatorFailure, match="baseline_mismatch"):
        operator._require_runtime_baseline(state, inspections)


def test_state_is_mode_0600_and_rejects_partial_evidence(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    state = populated_state("approval_1_ready")
    write_state(path, state)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert operator._read_state(path) == state

    partial = json.loads(path.read_text(encoding="utf-8"))
    partial["checks"].pop("health")
    path.write_text(json.dumps(partial), encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(operator.OperatorFailure, match="operator_state_invalid"):
        operator._read_state(path)


def test_failure_explicitly_invalidates_incomplete_fields(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    state = populated_state("new")
    state["checks"]["archive_provenance"] = "pass"
    write_state(path, state)

    operator._set_failure(
        path,
        state,
        "baseline_mismatch",
        check="accepted_fingerprints",
        invalidate_pending=True,
    )

    stored = operator._read_state(path)
    assert stored["checks"]["accepted_fingerprints"] == "fail"
    assert stored["checks"]["health"] == "invalid"
    assert stored["checks"]["restoration_health"] == "pending"


def test_crontab_capture_disable_and_restore_are_hash_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cron = "0 * * * * python tools/schwab_token_keepalive.py\n5 * * * * safe-job\n"
    calls: list[tuple[list[str], bytes | None]] = []

    def fake_run(command, **kwargs):
        calls.append((list(command), kwargs.get("input_bytes")))
        if command == ["crontab", "-l"]:
            return result(stdout=cron)
        return result()

    monkeypatch.setattr(operator, "_run", fake_run)
    snapshot = tmp_path / "cron.txt"
    digest, entries, present = operator._capture_crontab(snapshot)
    assert entries == 1
    assert present
    assert stat.S_IMODE(snapshot.stat().st_mode) == 0o600

    operator._disable_keepalive_cron(snapshot, digest, originally_present=True)
    assert calls[-1][1] == b"5 * * * * safe-job\n"
    operator._restore_crontab(snapshot, digest, originally_present=True)
    assert calls[-2][1] == cron.encode()


def test_watchdog_arm_failure_is_bounded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(1, SENSITIVE, SENSITIVE),
    )
    state = populated_state("approval_1_running")
    with pytest.raises(operator.OperatorFailure, match="watchdog_invalid"):
        operator._arm_watchdog(state, "hard", 300, ["safe-restore"])


def test_watchdog_arm_is_system_level_and_output_is_exactly_validated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = populated_state("approval_1_running")
    unit = operator._watchdog_unit(state, "hard")
    commands: list[list[str]] = []

    def fake_run(command, **_kwargs):
        commands.append(list(command))
        return result(
            stdout=(
                f"Running timer as unit: {unit}.timer. "
                f"Will run service as unit: {unit}.service.\n"
            )
        )

    monkeypatch.setattr(operator, "_run", fake_run)
    operator._arm_watchdog(state, "hard", 300, ["safe-restore"])
    assert commands[0][:4] == ["sudo", "-n", "systemd-run", "--collect"]
    assert any(part.startswith("--uid=") for part in commands[0])
    assert any(part.startswith("--gid=") for part in commands[0])


@pytest.mark.parametrize(
    ("active_marker", "code"),
    [
        (operator._KEEPALIVE_MARKER, "keepalive_active"),
        (operator._HOST_CLIENT_MARKERS[0], "host_client_active"),
        (operator._CI_WORKER_MARKERS[0], "ci_worker_active"),
    ],
)
def test_keepalive_host_client_and_ci_worker_checks_are_distinct(
    active_marker: str,
    code: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        operator,
        "_matching_host_processes",
        lambda marker: [101] if marker == active_marker else [],
    )
    with pytest.raises(operator.OperatorFailure, match=code):
        operator._require_no_host_writers()


def test_unowned_direct_runtime_process_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operator, "_matching_host_processes", lambda *_args: [101, 999])
    with pytest.raises(operator.OperatorFailure, match="host_client_active"):
        operator._require_no_unowned_runtime_processes([101])


def test_watchdog_status_requires_verified_active_units(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    state = populated_state("approval_2_pending")
    state["watchdog"]["hard"] = "armed"
    state["watchdog"]["approval"] = "armed"
    state_path = tmp_path / "state.json"
    write_state(state_path, state)
    monkeypatch.setattr(operator, "_watchdog_active", lambda *_args: False)
    with pytest.raises(operator.OperatorFailure, match="watchdog_invalid"):
        operator._watchdog_status(
            Namespace(state=state_path, require_approval_timer=True)
        )


def test_watchdog_cancel_requires_safe_phase_and_records_cancellation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = populated_state("restored")
    state["watchdog"]["hard"] = "armed"
    state_path = tmp_path / "state.json"
    write_state(state_path, state)
    monkeypatch.setattr(operator, "_cancel_watchdog", lambda *_args: None)

    operator._watchdog_cancel_command(Namespace(state=state_path, kind="hard"))

    assert operator._read_state(state_path)["watchdog"]["hard"] == "cancelled"
    assert capsys.readouterr().out == '{"code":"watchdog_cancelled","status":"ok"}\n'


def test_approval_2_runs_credential_command_exactly_once_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = approval_args(tmp_path)
    state = populated_state()
    state["watchdog"].update(
        {
            "hard": "armed",
            "approval": "armed",
            "hard_deadline": int(time.time()) + 300,
            "approval_deadline": int(time.time()) + 120,
        }
    )
    write_state(args.state, state)
    patch_approval_checks(monkeypatch)
    invocations = 0

    def fake_run(command, **_kwargs):
        nonlocal invocations
        assert operator._PROOF_MARKER in " ".join(command)
        invocations += 1
        return result(stdout='{"quote_count":1,"status":"ok","token_state":"ready"}\n')

    monkeypatch.setattr(operator, "_run", fake_run)
    monkeypatch.setattr(operator, "_restore_operation", lambda *_args, **_kwargs: True)

    operator._approval_2_execute(args)
    assert invocations == 1
    proof = operator._read_state(args.state)["proof"]
    assert proof["attempt_count"] == 1
    assert proof["quote_count"] == 1
    assert proof["token_state"] == "ready"
    assert proof["retry_count"] == 0
    assert proof["information_exposure"] == "pass"
    capsys.readouterr()

    with pytest.raises(operator.OperatorFailure, match="approval_2_timeout"):
        operator._approval_2_execute(args)
    assert invocations == 1


def test_malformed_secret_credential_output_is_not_persisted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = approval_args(tmp_path)
    state = populated_state()
    state["watchdog"].update(
        {
            "hard": "armed",
            "approval": "armed",
            "hard_deadline": int(time.time()) + 300,
            "approval_deadline": int(time.time()) + 120,
        }
    )
    write_state(args.state, state)
    patch_approval_checks(monkeypatch)
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: result(stdout=SENSITIVE))
    monkeypatch.setattr(operator, "_restore_operation", lambda *_args, **_kwargs: True)

    with pytest.raises(operator.OperatorFailure, match="credential_output_invalid"):
        operator._approval_2_execute(args)

    stored = args.state.read_text(encoding="utf-8")
    assert SENSITIVE not in stored
    proof = operator._read_state(args.state)["proof"]
    assert proof["attempt_count"] == 1
    assert proof["reason_code"] == "credential_output_invalid"
    assert proof["information_exposure"] == "pass"


def test_approval_timer_race_restores_without_invoking_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = approval_args(tmp_path)
    state = populated_state()
    state["watchdog"].update(
        {
            "hard": "armed",
            "approval": "armed",
            "hard_deadline": int(time.time()) + 300,
            "approval_deadline": int(time.time()) + 120,
        }
    )
    write_state(args.state, state)
    patch_approval_checks(monkeypatch)
    monkeypatch.setattr(operator, "_watchdog_service_active", lambda *_args: True)
    proof_calls: list[bool] = []
    monkeypatch.setattr(operator, "_run", lambda *_args, **_kwargs: proof_calls.append(True))
    restored: list[str | None] = []
    monkeypatch.setattr(
        operator,
        "_restore_operation",
        lambda *_args, **kwargs: restored.append(kwargs.get("failure_code")) or True,
    )

    with pytest.raises(operator.OperatorFailure, match="approval_2_timeout"):
        operator._approval_2_execute(args)

    assert proof_calls == []
    assert restored == ["approval_2_timeout"]


def patch_restoration_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator, "_validate_rollback_override", lambda *_args: None)
    monkeypatch.setattr(operator, "_require_base_image", lambda *_args: None)
    monkeypatch.setattr(operator, "_compose_service_hash", lambda *_args: COMPOSE_HASH)
    monkeypatch.setattr(operator, "_recreate_baseline", lambda *_args: None)
    monkeypatch.setattr(operator, "inspect_container", lambda *_args: runtime_inspect())
    monkeypatch.setattr(operator, "_start_container", lambda *_args: None)
    monkeypatch.setattr(operator, "_restore_crontab", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(operator, "_wait_for_health", lambda: None)
    monkeypatch.setattr(
        operator,
        "_inspect_all",
        lambda: {name: runtime_inspect() for name in operator._ALL_SERVICES},
    )
    monkeypatch.setattr(operator, "_require_runtime_baseline", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(operator, "_run_uniqueness_checks", lambda **_kwargs: {})
    monkeypatch.setattr(operator, "_require_candidate_ownership", lambda *_args: None)
    monkeypatch.setattr(operator, "_require_no_host_writers", lambda: None)
    monkeypatch.setattr(operator, "_require_no_unowned_runtime_processes", lambda *_args: None)
    monkeypatch.setattr(
        operator,
        "_fresh_error_counts",
        lambda *_args: {name: 0 for name in operator._TRADING_SERVICES},
    )
    monkeypatch.setattr(operator, "_cancel_watchdog", lambda *_args: None)
    monkeypatch.setattr(operator, "_cleanup_temporary_inputs", lambda *_args: None)
    monkeypatch.setattr(operator, "_emergency_restore_spx", lambda *_args: None)


def test_restoration_mismatch_pauses_trading_services(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = approval_args(tmp_path)
    state = populated_state("approval_2_running")
    write_state(args.state, state)
    patch_restoration_success(monkeypatch)
    monkeypatch.setattr(
        operator,
        "_require_runtime_baseline",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            operator.OperatorFailure("baseline_mismatch")
        ),
    )
    paused = []
    monkeypatch.setattr(operator, "_pause_fail_closed", lambda: paused.append(True))

    with pytest.raises(operator.OperatorFailure, match="restoration_failed_paused"):
        operator._restore_operation(args)

    assert paused == [True]
    stored = operator._read_state(args.state)
    assert stored["restoration"]["result"] == "fail"
    assert stored["failure_code"] == "restoration_failed_paused"


def test_emergency_restoration_removes_staging_with_recorded_image_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rollback = tmp_path / "rollback.yml"
    operator._write_private_bytes(rollback, operator._rollback_override_payload(IMAGE_ID))
    commands: list[list[str]] = []

    def fake_run(command, **_kwargs):
        commands.append(list(command))
        return result(stderr="Container butterfly_spx_app Recreated\n")

    monkeypatch.setattr(operator, "_run", fake_run)
    monkeypatch.setattr(operator, "inspect_container", lambda *_args: runtime_inspect())
    operator._emergency_restore_spx(tmp_path / "compose.yml", rollback, IMAGE_ID)
    assert str(rollback) in commands[0]
    assert "--no-build" in commands[0]
    assert "--pull" in commands[0]


def test_successful_restoration_proves_every_postcondition(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = approval_args(tmp_path)
    state = populated_state("approval_2_running")
    state["watchdog"]["hard"] = "armed"
    state["watchdog"]["approval"] = "cancelled"
    write_state(args.state, state)
    patch_restoration_success(monkeypatch)

    assert operator._restore_operation(args)
    stored = operator._read_state(args.state)
    assert stored["phase"] == "restored"
    assert stored["restoration"]["result"] == "pass"
    assert all(
        stored["checks"][name] == "pass"
        for name in (
            "restoration_fingerprints",
            "restoration_health",
            "restoration_uniqueness",
            "restoration_ownership",
            "restoration_keepalive",
            "restoration_errors",
        )
    )


def test_fresh_error_parser_counts_without_echoing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(operator.time, "sleep", lambda *_args: None)
    monkeypatch.setattr(
        operator,
        "_run",
        lambda *_args, **_kwargs: result(stdout=f"INFO ok\nERROR {SENSITIVE}\n"),
    )
    assert operator._fresh_error_counts(1) == {"spx": 1, "ndx": 1, "xsp": 1}


def prepare_args(tmp_path: Path) -> Namespace:
    now = datetime.now(timezone.utc)
    return Namespace(
        state=tmp_path / "state.json",
        approved_sha=APPROVED_SHA,
        approval_reference="approved-in-chat",
        window_start_utc=(now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        window_end_utc=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        accepted_directory=None,
        accepted_spx=tmp_path / "accepted-spx.json",
        accepted_ndx=tmp_path / "accepted-ndx.json",
        accepted_xsp=tmp_path / "accepted-xsp.json",
        base_compose=tmp_path / "compose.yml",
        staging_override=tmp_path / "staging.yml",
        archive=tmp_path / "reviewed.tar",
        expected_archive_sha256=ARCHIVE_SHA,
        rollback_override=tmp_path / "rollback.yml",
        cron_snapshot=tmp_path / "cron.txt",
        watchdog_fired=False,
    )


def patch_prepare_success(
    monkeypatch: pytest.MonkeyPatch, args: Namespace
) -> dict[str, dict]:
    inspections = {name: runtime_inspect() for name in operator._ALL_SERVICES}
    inspections["candidate"]["Mounts"][0].update({"Mode": "ro", "RW": False})
    record = operator.build_record(runtime_inspect())
    for path in (args.accepted_spx, args.accepted_ndx, args.accepted_xsp):
        path.write_text(json.dumps(record), encoding="utf-8")
        path.chmod(0o600)
    monkeypatch.setattr(operator, "_validate_archive", lambda *_args: ARCHIVE_SHA)
    current_hash = operator._sha256_file(Path(operator.__file__).resolve())
    monkeypatch.setattr(operator, "_archive_member_sha256", lambda *_args: current_hash)
    monkeypatch.setattr(operator, "_require_reviewed_file", lambda *_args: None)
    monkeypatch.setattr(operator, "_inspect_all", lambda: inspections)
    monkeypatch.setattr(operator, "_run_health_checks", lambda: None)
    monkeypatch.setattr(
        operator,
        "_run_uniqueness_checks",
        lambda **_kwargs: {name: index + 100 for index, name in enumerate(operator._ALL_SERVICES)},
    )
    monkeypatch.setattr(operator, "_require_no_host_writers", lambda: None)
    monkeypatch.setattr(operator, "_require_no_unowned_runtime_processes", lambda *_args: None)
    monkeypatch.setattr(operator, "_validate_compose_semantics", lambda *_args: None)
    monkeypatch.setattr(operator, "_compose_service_hash", lambda *_args: COMPOSE_HASH)
    monkeypatch.setattr(operator, "_require_base_image", lambda *_args: None)
    monkeypatch.setattr(operator, "_validate_compose_dry_run", lambda *_args: None)

    def capture_cron(path: Path):
        operator._write_private_bytes(path, b"")
        return hashlib.sha256(b"").hexdigest(), 0, True

    monkeypatch.setattr(operator, "_capture_crontab", capture_cron)
    return inspections


def test_prepare_captures_fresh_accepted_baseline_and_rollback_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = prepare_args(tmp_path)
    patch_prepare_success(monkeypatch, args)

    operator._prepare(args)

    captured = json.loads(capsys.readouterr().out)
    assert captured == {
        "archive_sha256": ARCHIVE_SHA,
        "code": "approval_1_ready",
        "status": "ok",
    }
    state = operator._read_state(args.state)
    assert state["phase"] == "approval_1_ready"
    assert state["archive_sha256"] == ARCHIVE_SHA
    assert all(state["baseline"][name]["record"] for name in operator._ALL_SERVICES)
    assert stat.S_IMODE(args.state.stat().st_mode) == 0o600
    assert stat.S_IMODE(args.cron_snapshot.stat().st_mode) == 0o600
    assert stat.S_IMODE(args.rollback_override.stat().st_mode) == 0o600


def test_prepare_refuses_contact_outside_exact_approval_window(tmp_path: Path) -> None:
    args = prepare_args(tmp_path)
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    args.window_start_utc = past.strftime("%Y-%m-%dT%H:%M:%SZ")
    args.window_end_utc = (past + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    with pytest.raises(operator.OperatorFailure, match="invalid_arguments"):
        operator._prepare(args)

    assert not args.state.exists()


def test_accepted_snapshot_discovery_uses_only_unique_mode_0600_accepted_records(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    record = operator.build_record(runtime_inspect())
    for name in operator._TRADING_SERVICES:
        path = evidence / f"accepted-resume-{name}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        path.chmod(0o600)
    unrelated = evidence / "third-window-baseline-spx.json"
    unrelated.write_text(json.dumps(record), encoding="utf-8")
    unrelated.chmod(0o600)

    assert operator._discover_accepted_snapshots(evidence) == {
        name: record for name in operator._TRADING_SERVICES
    }

    duplicate = evidence / "accepted-supplement-spx.json"
    duplicate.write_text(json.dumps(record), encoding="utf-8")
    duplicate.chmod(0o600)
    with pytest.raises(operator.OperatorFailure, match="evidence_invalid"):
        operator._discover_accepted_snapshots(evidence)


def test_accepted_snapshot_discovery_extracts_bounded_composite_supplement(
    tmp_path: Path,
) -> None:
    evidence_root = tmp_path / "deployment"
    evidence_root.mkdir()
    nested = evidence_root / "retained"
    nested.mkdir()
    record = operator.build_record(runtime_inspect())
    supplement = nested / "accepted-resume-supplement.json"
    supplement.write_text(
        json.dumps(
            {
                "reviewer_disposition": "accepted",
                "accepted_fingerprints": {
                    name: record for name in operator._TRADING_SERVICES
                },
            }
        ),
        encoding="utf-8",
    )
    supplement.chmod(0o600)
    for index in range(300):
        (evidence_root / f"unrelated-{index}.txt").write_text("ignored", encoding="utf-8")
    third = evidence_root / "third-window-baseline-spx.json"
    third.write_text(json.dumps(record), encoding="utf-8")
    third.chmod(0o600)

    assert operator._discover_accepted_snapshots(evidence_root) == {
        name: record for name in operator._TRADING_SERVICES
    }


def test_accepted_snapshot_discovery_rejects_duplicate_composite_records(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    record = operator.build_record(runtime_inspect())
    for index in range(2):
        supplement = evidence / f"accepted-supplement-{index}.json"
        supplement.write_text(
            json.dumps({name: record for name in operator._TRADING_SERVICES}),
            encoding="utf-8",
        )
        supplement.chmod(0o600)

    with pytest.raises(operator.OperatorFailure, match="evidence_invalid"):
        operator._discover_accepted_snapshots(evidence)


def test_evidence_status_emits_only_bounded_fixed_failure_diagnostics(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    candidate = evidence / f"accepted-{SENSITIVE}.json"
    candidate.write_text("{}", encoding="utf-8")
    candidate.chmod(0o600)

    with pytest.raises(SystemExit, match="1"):
        operator.main(["evidence-status", "--accepted-directory", str(evidence)])

    output = capsys.readouterr().out
    assert json.loads(output) == {
        "candidate_count": 1,
        "code": "evidence_invalid",
        "reason": "schema_invalid",
        "status": "error",
        "valid_record_count": 0,
    }
    assert SENSITIVE not in output


def test_evidence_status_reports_ready_without_paths_or_content(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    record = operator.build_record(runtime_inspect())
    for name in operator._TRADING_SERVICES:
        path = evidence / f"accepted-{name}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        path.chmod(0o600)

    operator.main(["evidence-status", "--accepted-directory", str(evidence)])

    assert json.loads(capsys.readouterr().out) == {
        "code": "evidence_ready",
        "service_count": 3,
        "status": "ok",
        "valid_record_count": 3,
    }


def write_reviewed_legacy_evidence(root: Path) -> dict[str, object]:
    record = operator.build_record(runtime_inspect())
    decision = root / "credential-proof-operator-decision.json"
    decision.write_text(
        json.dumps(
            {
                "operator_decision": "accept current verified configuration as new baseline",
                "accepted_fingerprints": {
                    name: record["configuration_fingerprint"]
                    for name in operator._TRADING_SERVICES
                },
            }
        ),
        encoding="utf-8",
    )
    decision.chmod(0o600)
    for name in operator._TRADING_SERVICES:
        snapshot = root / f"credential-proof-baseline-{name}.json"
        snapshot.write_text(json.dumps(record), encoding="utf-8")
        snapshot.chmod(0o600)
    return record


def test_reviewed_legacy_discovery_links_explicit_acceptance_to_exact_records(
    tmp_path: Path,
) -> None:
    record = write_reviewed_legacy_evidence(tmp_path)

    snapshots, candidate_count, acceptance_count = (
        operator._discover_reviewed_legacy_snapshots([tmp_path])
    )

    assert snapshots == {name: record for name in operator._TRADING_SERVICES}
    assert candidate_count == 4
    assert acceptance_count == 1


def test_reviewed_legacy_discovery_rejects_unaccepted_third_baselines(
    tmp_path: Path,
) -> None:
    record = operator.build_record(runtime_inspect())
    for name in operator._TRADING_SERVICES:
        snapshot = tmp_path / f"credential-proof-third-baseline-{name}.json"
        snapshot.write_text(json.dumps(record), encoding="utf-8")
        snapshot.chmod(0o600)

    with pytest.raises(operator.EvidenceFailure, match="evidence_invalid") as failure:
        operator._discover_reviewed_legacy_snapshots([tmp_path])

    assert failure.value.reason == "no_acceptance"


def test_reviewed_legacy_discovery_rejects_rejected_or_ambiguous_evidence(
    tmp_path: Path,
) -> None:
    record = write_reviewed_legacy_evidence(tmp_path)
    decision = tmp_path / "credential-proof-operator-decision.json"
    decision.write_text(
        json.dumps(
            {
                "accepted_fingerprint_comparison": "invalid",
                "accepted_fingerprints": {
                    name: record["configuration_fingerprint"]
                    for name in operator._TRADING_SERVICES
                },
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(operator.EvidenceFailure) as rejected:
        operator._discover_reviewed_legacy_snapshots([tmp_path])
    assert rejected.value.reason == "no_acceptance"

    decision.unlink()
    write_reviewed_legacy_evidence(tmp_path)
    duplicate = tmp_path / "credential-proof-baseline-copy-spx.json"
    duplicate.write_text(json.dumps(record), encoding="utf-8")
    duplicate.chmod(0o600)
    with pytest.raises(operator.EvidenceFailure) as ambiguous:
        operator._discover_reviewed_legacy_snapshots([tmp_path])
    assert ambiguous.value.reason == "duplicate_service"


def test_legacy_evidence_status_is_bounded_and_never_reads_token_named_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    token = tmp_path / "credential-proof-token-baseline.json"
    token.write_text(SENSITIVE, encoding="utf-8")
    token.chmod(0o600)
    original = operator._read_evidence_value
    read_paths: list[Path] = []

    def tracked(path: Path):
        read_paths.append(path)
        return original(path)

    monkeypatch.setattr(operator, "_read_evidence_value", tracked)
    with pytest.raises(SystemExit, match="1"):
        operator.main(
            ["legacy-evidence-status", "--evidence-root", str(tmp_path)]
        )

    output = capsys.readouterr().out
    assert json.loads(output) == {
        "candidate_count": 0,
        "code": "evidence_invalid",
        "reason": "no_candidates",
        "status": "error",
        "valid_record_count": 0,
    }
    assert read_paths == []
    assert SENSITIVE not in output


def test_legacy_evidence_status_reports_only_bounded_counts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_reviewed_legacy_evidence(tmp_path)

    operator.main(["legacy-evidence-status", "--evidence-root", str(tmp_path)])

    assert json.loads(capsys.readouterr().out) == {
        "acceptance_count": 1,
        "candidate_count": 4,
        "code": "legacy_evidence_ready",
        "service_count": 3,
        "status": "ok",
        "valid_record_count": 3,
    }


def legacy_capture_args(tmp_path: Path, evidence_root: Path) -> list[str]:
    now = datetime.now(timezone.utc)
    return [
        "legacy-evidence-capture",
        "--evidence-root",
        str(evidence_root),
        "--evidence-output",
        str((tmp_path / "bounded-evidence.json").resolve()),
        "--approved-sha",
        APPROVED_SHA,
        "--approval-reference",
        "approved-in-chat",
        "--window-start-utc",
        (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--window-end-utc",
        (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--archive",
        str(tmp_path / "reviewed.tar"),
        "--expected-archive-sha256",
        ARCHIVE_SHA,
    ]


def patch_legacy_capture_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator, "_validate_archive", lambda *_args: ARCHIVE_SHA)
    current_hash = operator._sha256_file(Path(operator.__file__).resolve())
    monkeypatch.setattr(operator, "_archive_member_sha256", lambda *_args: current_hash)


def test_legacy_evidence_capture_persists_bounded_failure_before_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_legacy_capture_provenance(monkeypatch)
    record = operator.build_record(runtime_inspect())
    for name in operator._TRADING_SERVICES:
        path = tmp_path / f"credential-proof-third-baseline-{name}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        path.chmod(0o600)

    with pytest.raises(SystemExit, match="1"):
        operator.main(legacy_capture_args(tmp_path, tmp_path))

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "candidate_count": 3,
        "code": "evidence_invalid",
        "reason": "no_acceptance",
        "status": "error",
        "valid_record_count": 0,
    }
    evidence_path = tmp_path / "bounded-evidence.json"
    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert stat.S_IMODE(evidence_path.stat().st_mode) == 0o600
    assert stored["locator_result"] == output
    assert stored["approved_sha"] == APPROVED_SHA
    assert stored["archive_sha256"] == ARCHIVE_SHA
    assert stored["approval_reference_sha256"] == hashlib.sha256(
        b"approved-in-chat"
    ).hexdigest()
    assert stored["evidence_type"] == "legacy_baseline_locator"
    assert stored["retry_count"] == 0
    assert stored["service_mutation"] is False
    assert stored["credential_read"] is False
    assert stored["token_read"] is False
    assert stored["schwab_request"] is False
    assert str(tmp_path) not in evidence_path.read_text(encoding="utf-8")
    assert SENSITIVE not in evidence_path.read_text(encoding="utf-8")


def test_legacy_evidence_capture_persists_ready_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_legacy_capture_provenance(monkeypatch)
    write_reviewed_legacy_evidence(tmp_path)

    operator.main(legacy_capture_args(tmp_path, tmp_path))

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "acceptance_count": 1,
        "candidate_count": 4,
        "code": "legacy_evidence_ready",
        "service_count": 3,
        "status": "ok",
        "valid_record_count": 3,
    }
    stored = json.loads((tmp_path / "bounded-evidence.json").read_text(encoding="utf-8"))
    assert stored["locator_result"] == output


def test_legacy_evidence_capture_never_overwrites_existing_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_legacy_capture_provenance(monkeypatch)
    write_reviewed_legacy_evidence(tmp_path)
    evidence_path = tmp_path / "bounded-evidence.json"
    evidence_path.write_text(SENSITIVE, encoding="utf-8")
    evidence_path.chmod(0o600)

    with pytest.raises(SystemExit, match="1"):
        operator.main(legacy_capture_args(tmp_path, tmp_path))

    assert evidence_path.read_text(encoding="utf-8") == SENSITIVE
    assert capsys.readouterr().out == (
        '{"code":"evidence_invalid","status":"error"}\n'
    )


def baseline_candidate_args(tmp_path: Path) -> list[str]:
    now = datetime.now(timezone.utc)
    return [
        "baseline-candidate-capture",
        "--evidence-output",
        str((tmp_path / "baseline-candidate.json").resolve()),
        "--approved-sha",
        APPROVED_SHA,
        "--approval-reference",
        "approved-baseline-capture",
        "--window-start-utc",
        (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--window-end-utc",
        (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--archive",
        str(tmp_path / "reviewed.tar"),
        "--expected-archive-sha256",
        ARCHIVE_SHA,
        "--base-compose",
        str(tmp_path / "compose.yml"),
        "--spx-config",
        str(tmp_path / "config.yaml"),
        "--ndx-config",
        str(tmp_path / "config_ndx.yaml"),
        "--xsp-config",
        str(tmp_path / "config_xsp.yaml"),
    ]


def patch_baseline_candidate_success(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_legacy_capture_provenance(monkeypatch)
    inspections = {name: runtime_inspect() for name in operator._ALL_SERVICES}
    inspections["candidate"]["Mounts"][0].update({"Mode": "ro", "RW": False})
    monkeypatch.setattr(operator, "_require_reviewed_file", lambda *_args: None)
    monkeypatch.setattr(operator, "_reviewed_paper_configs", lambda *_args: True)
    monkeypatch.setattr(operator, "_inspect_all", lambda: inspections)
    monkeypatch.setattr(operator, "_matching_host_processes", lambda *_args: [])
    monkeypatch.setattr(operator, "_run_health_checks", lambda: None)
    monkeypatch.setattr(
        operator,
        "_run_uniqueness_checks",
        lambda: {name: index + 100 for index, name in enumerate(operator._ALL_SERVICES)},
    )
    monkeypatch.setattr(operator, "_require_no_host_writers", lambda: None)
    monkeypatch.setattr(operator, "_require_no_unowned_runtime_processes", lambda *_args: None)
    monkeypatch.setattr(operator, "_compose_service_hash", lambda *_args: COMPOSE_HASH)
    monkeypatch.setattr(operator, "_require_base_image", lambda *_args: None)


def test_baseline_candidate_capture_persists_exact_hash_only_candidate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)

    operator.main(baseline_candidate_args(tmp_path))

    output = json.loads(capsys.readouterr().out)
    assert output["code"] == "baseline_candidate_ready"
    assert output["status"] == "ok"
    assert output["service_count"] == 3
    assert operator._HASH_PATTERN.fullmatch(output["candidate_set_sha256"])
    evidence_path = tmp_path / "baseline-candidate.json"
    stored_text = evidence_path.read_text(encoding="utf-8")
    stored = json.loads(stored_text)
    assert stat.S_IMODE(evidence_path.stat().st_mode) == 0o600
    assert stored["result"] == output
    assert stored["candidate"]["candidate_set_sha256"] == output[
        "candidate_set_sha256"
    ]
    assert set(stored["candidate"]["records"]) == set(operator._TRADING_SERVICES)
    assert set(stored["candidate"]["images"]) == set(operator._TRADING_SERVICES)
    assert all(value == "pass" for value in stored["checks"].values())
    assert stored["service_mutation"] is False
    assert stored["credential_read"] is False
    assert stored["token_read"] is False
    assert stored["schwab_request"] is False
    assert SENSITIVE not in stored_text
    assert "/sensitive/host/token/path" not in stored_text

    operator.main(
        ["baseline-candidate-status", "--evidence", str(evidence_path.resolve())]
    )
    assert json.loads(capsys.readouterr().out) == output


def test_baseline_candidate_capture_persists_bounded_failed_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)

    def fail_health() -> None:
        raise operator.OperatorFailure("health_invalid")

    monkeypatch.setattr(operator, "_run_health_checks", fail_health)

    with pytest.raises(SystemExit, match="1"):
        operator.main(baseline_candidate_args(tmp_path))

    output = capsys.readouterr().out
    assert output == '{"code":"health_invalid","status":"error"}\n'
    stored = json.loads((tmp_path / "baseline-candidate.json").read_text())
    assert stored["candidate"] is None
    assert stored["checks"]["health"] == "fail"
    assert stored["result"] == {"code": "health_invalid", "status": "error"}
    assert SENSITIVE not in output

    with pytest.raises(SystemExit, match="1"):
        operator.main(
            [
                "baseline-candidate-status",
                "--evidence",
                str((tmp_path / "baseline-candidate.json").resolve()),
            ]
        )
    assert json.loads(capsys.readouterr().out) == {
        "code": "health_invalid",
        "failed_check": "health",
        "status": "error",
    }


def test_baseline_candidate_capture_limits_compose_and_image_equality_to_trading_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)
    compose_services: list[str] = []
    image_services: list[str] = []

    def compose_hash(_path: Path, service: str) -> str:
        compose_services.append(service)
        return COMPOSE_HASH

    def require_image(_path: Path, _image_id: str, service: str) -> None:
        image_services.append(service)

    monkeypatch.setattr(operator, "_compose_service_hash", compose_hash)
    monkeypatch.setattr(operator, "_require_base_image", require_image)

    operator.main(baseline_candidate_args(tmp_path))

    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert compose_services == list(operator._TRADING_SERVICES)
    assert image_services == list(operator._TRADING_SERVICES)


def test_baseline_candidate_capture_reports_only_fixed_trading_compose_mismatches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)
    monkeypatch.setattr(
        operator,
        "_compose_service_hash",
        lambda _path, service: "f" * 64 if service == "ndx" else COMPOSE_HASH,
    )

    with pytest.raises(SystemExit, match="1"):
        operator.main(baseline_candidate_args(tmp_path))

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "code": "compose_semantics_invalid",
        "mismatched_services": ["ndx"],
        "status": "error",
    }
    evidence_path = tmp_path / "baseline-candidate.json"
    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert stored["candidate"] is None
    assert stored["checks"]["compose_hashes"] == "fail"

    with pytest.raises(SystemExit, match="1"):
        operator.main(
            ["baseline-candidate-status", "--evidence", str(evidence_path.resolve())]
        )
    assert json.loads(capsys.readouterr().out) == {
        "code": "compose_semantics_invalid",
        "failed_check": "compose_hashes",
        "mismatched_services": ["ndx"],
        "status": "error",
    }


def test_baseline_candidate_capture_distinguishes_invalid_compose_hash_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)

    def compose_hash(_path: Path, service: str) -> str:
        if service == "ndx":
            raise operator.OperatorFailure("compose_semantics_invalid")
        return "f" * 64 if service == "xsp" else COMPOSE_HASH

    monkeypatch.setattr(operator, "_compose_service_hash", compose_hash)

    with pytest.raises(SystemExit, match="1"):
        operator.main(baseline_candidate_args(tmp_path))

    output = json.loads(capsys.readouterr().out)
    assert output == {
        "code": "compose_semantics_invalid",
        "invalid_services": ["ndx"],
        "mismatched_services": ["xsp"],
        "status": "error",
    }
    assert SENSITIVE not in json.dumps(output)
    evidence_path = tmp_path / "baseline-candidate.json"
    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert stored["candidate"] is None
    assert stored["checks"]["compose_hashes"] == "fail"

    with pytest.raises(SystemExit, match="1"):
        operator.main(
            ["baseline-candidate-status", "--evidence", str(evidence_path.resolve())]
        )
    assert json.loads(capsys.readouterr().out) == {
        "code": "compose_semantics_invalid",
        "failed_check": "compose_hashes",
        "invalid_services": ["ndx"],
        "mismatched_services": ["xsp"],
        "status": "error",
    }


def test_baseline_candidate_status_rejects_overlapping_compose_service_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)
    monkeypatch.setattr(
        operator,
        "_compose_service_hash",
        lambda _path, service: "f" * 64 if service == "ndx" else COMPOSE_HASH,
    )
    with pytest.raises(SystemExit, match="1"):
        operator.main(baseline_candidate_args(tmp_path))
    capsys.readouterr()

    evidence_path = tmp_path / "baseline-candidate.json"
    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
    stored["result"]["invalid_services"] = ["ndx"]
    evidence_path.write_text(json.dumps(stored), encoding="utf-8")
    evidence_path.chmod(0o600)

    with pytest.raises(SystemExit, match="1"):
        operator.main(
            ["baseline-candidate-status", "--evidence", str(evidence_path.resolve())]
        )
    assert capsys.readouterr().out == '{"code":"evidence_invalid","status":"error"}\n'


def test_baseline_candidate_status_rejects_extra_fields_without_disclosure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_baseline_candidate_success(monkeypatch)
    operator.main(baseline_candidate_args(tmp_path))
    capsys.readouterr()
    evidence_path = tmp_path / "baseline-candidate.json"
    stored = json.loads(evidence_path.read_text(encoding="utf-8"))
    stored["raw_environment"] = SENSITIVE
    evidence_path.write_text(json.dumps(stored), encoding="utf-8")
    evidence_path.chmod(0o600)

    with pytest.raises(SystemExit, match="1"):
        operator.main(
            ["baseline-candidate-status", "--evidence", str(evidence_path.resolve())]
        )

    output = capsys.readouterr().out
    assert output == '{"code":"evidence_invalid","status":"error"}\n'
    assert SENSITIVE not in output


def test_runtime_direct_access_rejects_gateway_or_duplicate_environment() -> None:
    inspected = runtime_inspect()
    assert operator._runtime_direct_access(inspected)

    inspected["Config"]["Env"].append("SCHWAB_ACCESS_MODE=gateway")
    assert not operator._runtime_direct_access(inspected)

    inspected = runtime_inspect()
    inspected["Config"]["Env"].extend(["DUPLICATE=one", "DUPLICATE=two"])
    assert not operator._runtime_direct_access(inspected)


def test_reviewed_paper_configs_require_one_true_value_per_service(
    tmp_path: Path,
) -> None:
    valid: list[Path] = []
    for name in operator._TRADING_SERVICES:
        path = tmp_path / f"{name}.yaml"
        path.write_text("execution:\n  paper_trading: true\n", encoding="utf-8")
        valid.append(path)
    assert operator._reviewed_paper_configs(valid)

    valid[1].write_text("execution:\n  paper_trading: false\n", encoding="utf-8")
    assert not operator._reviewed_paper_configs(valid)


def test_prepare_selects_only_explicit_reviewed_legacy_roots(tmp_path: Path) -> None:
    record = write_reviewed_legacy_evidence(tmp_path)
    args = prepare_args(tmp_path)
    args.accepted_spx = None
    args.accepted_ndx = None
    args.accepted_xsp = None
    args.reviewed_evidence_root = [tmp_path]

    assert operator._accepted_snapshots(args) == {
        name: record for name in operator._TRADING_SERVICES
    }


def test_accepted_snapshot_discovery_rejects_insecure_or_partial_records(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    record = operator.build_record(runtime_inspect())
    for name in ("spx", "ndx"):
        path = evidence / f"accepted-{name}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        path.chmod(0o600)
    insecure = evidence / "accepted-xsp.json"
    insecure.write_text(json.dumps(record), encoding="utf-8")
    insecure.chmod(0o644)

    with pytest.raises(operator.OperatorFailure, match="evidence_invalid"):
        operator._discover_accepted_snapshots(evidence)


def test_prepare_failure_retains_only_invalidated_bounded_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = prepare_args(tmp_path)
    patch_prepare_success(monkeypatch, args)
    monkeypatch.setattr(
        operator,
        "_run_health_checks",
        lambda: (_ for _ in ()).throw(operator.OperatorFailure("health_invalid")),
    )

    with pytest.raises(operator.OperatorFailure, match="health_invalid"):
        operator._prepare(args)

    state = operator._read_state(args.state)
    assert state["phase"] == "failed"
    assert state["failure_code"] == "health_invalid"
    assert state["checks"]["accepted_fingerprints"] == "pass"
    assert state["checks"]["health"] == "fail"
    assert SENSITIVE not in args.state.read_text(encoding="utf-8")


def patch_approval_1_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(operator, "_validate_archive", lambda *_args: ARCHIVE_SHA)
    monkeypatch.setattr(operator, "_validate_compose_semantics", lambda *_args: None)
    monkeypatch.setattr(operator, "_validate_compose_dry_run", lambda *_args: None)
    monkeypatch.setattr(
        operator,
        "_inspect_all",
        lambda: {name: runtime_inspect() for name in operator._ALL_SERVICES},
    )
    monkeypatch.setattr(operator, "_require_runtime_baseline", lambda *_args: None)
    monkeypatch.setattr(operator, "_run_health_checks", lambda: None)
    monkeypatch.setattr(
        operator,
        "_run_uniqueness_checks",
        lambda **_kwargs: {name: index + 100 for index, name in enumerate(operator._ALL_SERVICES)},
    )
    monkeypatch.setattr(operator, "_require_candidate_ownership", lambda *_args: None)
    monkeypatch.setattr(operator, "_require_no_host_writers", lambda: None)
    monkeypatch.setattr(operator, "_require_no_unowned_runtime_processes", lambda *_args: None)
    monkeypatch.setattr(operator, "_recreate_staged", lambda *_args: None)
    monkeypatch.setattr(operator, "inspect_container", lambda *_args: runtime_inspect())
    monkeypatch.setattr(operator, "staging_matches_baseline", lambda *_args: True)
    monkeypatch.setattr(operator, "_stage_archive", lambda *_args: None)
    monkeypatch.setattr(operator, "_run_exact_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(operator, "_arm_watchdog", lambda *_args: None)
    monkeypatch.setattr(operator, "_watchdog_active", lambda *_args: True)
    monkeypatch.setattr(operator, "_disable_keepalive_cron", lambda *_args, **_kwargs: None)
    def fake_run(command, **_kwargs):
        if command[:2] == ["docker", "stop"]:
            return result(stdout=f"{command[-1]}\n")
        return result()

    monkeypatch.setattr(operator, "_run", fake_run)
    monkeypatch.setattr(operator, "_container_is_stopped", lambda *_args: True)
    monkeypatch.setattr(operator, "_unique_service_pid", lambda *_args, **_kwargs: 101)
    monkeypatch.setattr(operator, "_matching_host_processes", lambda *_args: [])


def test_approval_1_success_arms_both_watchdogs_and_starts_two_minute_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = prepare_args(tmp_path)
    state = populated_state("approval_1_ready")
    write_state(args.state, state)
    patch_approval_1_success(monkeypatch)

    operator._approval_1_execute(args)

    assert json.loads(capsys.readouterr().out) == {
        "code": "approval_2_required",
        "status": "ok",
        "timeout_seconds": 120,
    }
    stored = operator._read_state(args.state)
    assert stored["phase"] == "approval_2_pending"
    assert stored["watchdog"]["hard"] == "armed"
    assert stored["watchdog"]["approval"] == "armed"
    assert stored["checks"]["native_smoke"] == "pass"
    assert stored["checks"]["refusal_gate"] == "pass"
    assert stored["checks"]["single_writer"] == "pass"


def test_post_recreation_watchdog_failure_invokes_immediate_restoration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = prepare_args(tmp_path)
    write_state(args.state, populated_state("approval_1_ready"))
    patch_approval_1_success(monkeypatch)
    monkeypatch.setattr(
        operator,
        "_arm_watchdog",
        lambda *_args: (_ for _ in ()).throw(operator.OperatorFailure("watchdog_invalid")),
    )
    restored: list[str | None] = []
    monkeypatch.setattr(
        operator,
        "_restore_operation",
        lambda *_args, **kwargs: restored.append(kwargs.get("failure_code")) or True,
    )

    with pytest.raises(operator.OperatorFailure, match="watchdog_invalid"):
        operator._approval_1_execute(args)

    assert restored == ["watchdog_invalid"]


def test_pre_recreation_failure_does_not_mutate_or_restore(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = prepare_args(tmp_path)
    write_state(args.state, populated_state("approval_1_ready"))
    patch_approval_1_success(monkeypatch)
    monkeypatch.setattr(
        operator,
        "_validate_compose_dry_run",
        lambda *_args: (_ for _ in ()).throw(
            operator.OperatorFailure("compose_dry_run_invalid")
        ),
    )
    restored: list[bool] = []
    monkeypatch.setattr(
        operator,
        "_restore_operation",
        lambda *_args, **_kwargs: restored.append(True),
    )

    with pytest.raises(operator.OperatorFailure, match="compose_dry_run_invalid"):
        operator._approval_1_execute(args)

    assert restored == []


def test_invalid_cli_arguments_have_one_small_fixed_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        operator.main(["prepare", "--state", SENSITIVE])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert captured.out == '{"code":"invalid_arguments","status":"error"}\n'
    assert captured.err == ""
    assert SENSITIVE not in captured.out
