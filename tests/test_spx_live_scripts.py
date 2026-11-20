"""v2 pilot scripts: start/stop only the live container and never change paper.

A fake `docker` on PATH replays container state from a JSON file and records every call,
so the scripts run end to end with no Docker, Schwab or database.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPTS = Path("deploy/spx-live")
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
CAND = "sha256:" + "c" * 64
PAPER_FINGERPRINT = "paperid sha256:paper 2026-11-17T00:36:51Z 0 true"
LIVE_LIMITS = [
    "BUTTERFLY_INSTANCE_ROLE=live",
    "DATABASE__NAME=butterfly_guy_spx_live",
    "EXECUTION__PAPER_TRADING=false",
    f"EXECUTION__LIVE_TEST_DATE={TODAY}",
    "EXECUTION__LIVE_TEST_MAX_DEBIT=4.0",
    "EXECUTION__RECORD_LIVE_EXECUTION=true",
    "EXECUTION__LIVE_TEST_QUOTE_MAX_AGE_SECONDS=10",
    "RISK__MAX_POSITION_SIZE=1",
    "RISK__MAX_TRADES_PER_DAY=1",
    "LIVE_ACCOUNT_ALLOCATION=20000",
    "LIVE_MAX_ACCOUNT_DAILY_LOSS=500",
    "SCHWAB_ACCESS_MODE=direct",
]

FAKE_DOCKER = r'''
import io, json, os, sys, tarfile, hashlib
state_path = os.environ["FAKE_DOCKER_STATE"]
state = json.load(open(state_path))
args = sys.argv[1:]
with open(os.environ["FAKE_DOCKER_CALLS"], "a") as f:
    f.write(json.dumps(args) + "\n")

def save():
    json.dump(state, open(state_path, "w"))

def token():
    path = os.environ["FAKE_TOKEN"]
    return f"{os.stat(path).st_ino} {hashlib.sha256(open(path, 'rb').read()).hexdigest()}"

cmd = args[0]
if cmd == "ps":
    name = args[args.index("--filter") + 1].split("^", 1)[1].rstrip("$")
    if state["running"].get(name):
        print(name)
elif cmd == "inspect":
    fmt, name = args[2], args[3]
    if "Config.Env" in fmt:
        print("\n".join(state["env"][name]))
    elif "{{.Id}}" in fmt:
        print(state["fingerprint"][name])
    elif fmt == "{{.Image}}":
        print(state["image"][name])
    elif "ExitCode" in fmt:
        print("exit 137 at 2026-11-20T17:02:00Z")
    elif fmt == "{{.RestartCount}}":
        print(state.get("restarts", {}).get(name, 0))
    elif "RestartCount" in fmt:
        print("true 0" if state["running"].get(name) else "false 0")
    elif "Mounts" in fmt:
        print(state["mount"])
elif cmd == "image":
    sys.exit(0 if args[2] in state["images"] else 1)
elif cmd == "exec":
    rest = [a for a in args[1:] if a != "-i"]
    name = rest[0]
    if rest[1:3] == ["sh", "-c"]:
        print(state.get("token_override", {}).get(name) or token())
    elif rest[1:] in (["python", "-"], ["python", "-", "--ignore-expired"]):
        sys.stdin.read()
        sys.exit(state["broker_rc"])
    elif rest[1] == "python":
        sys.stdin.read()
    elif rest[1] == "tar":
        buf = io.BytesIO()
        tarfile.open(fileobj=buf, mode="w").close()
        sys.stdout.buffer.write(buf.getvalue())
elif cmd == "logs":
    print(state["logs"])
elif cmd == "compose":
    if "up" in args:
        state["running"]["butterfly_spx_live_app"] = True
        if state.get("paper_changes_on_up"):
            state["fingerprint"]["butterfly_spx_app"] = "changed"
        save()
    elif "stop" in args:
        state["running"]["butterfly_spx_live_app"] = False
        save()
    elif "run" in args:
        sub = args[args.index("butterfly_guy.scripts.spx_live_db") + 1]
        if sub == "compare":
            print("# paired report")
        sys.exit(state["check_rc"] if sub == "check" else 0)
'''


@pytest.fixture
def session(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(f"#!{sys.executable}\n{FAKE_DOCKER}")
    for name, body in (("curl", "exit 0"), ("sleep", "exit 0")):
        (bin_dir / name).write_text(f"#!/bin/sh\n{body}\n")
    notify = bin_dir / "fake-python"
    notify.write_text(
        f'#!/bin/sh\necho "$2" >> {tmp_path}/notify-attempts.log\n'
        '[ "${FAKE_NOTIFY_FAIL:-0}" != 1 ] || exit 1\n'
        f'echo "$2" >> {tmp_path}/notify.log\n'
    )
    for path in bin_dir.iterdir():
        path.chmod(0o755)

    scripts = tmp_path / "session"
    shutil.copytree(SCRIPTS, scripts)
    rel = tmp_path / "rel"
    (rel / "tools").mkdir(parents=True)
    for tool in ("deploy_broker_flat_check.py", "report_spx_live_test.py"):
        (rel / "tools" / tool).write_text("")
    tokens = tmp_path / "tokens"
    tokens.mkdir()
    (tokens / "tokens.json").write_text("{}")
    infra = tmp_path / "infra"
    infra.mkdir()
    (infra / ".env").write_text(f"SCHWAB_GATEWAY_TOKEN_DIR={tokens}\n")
    data = tmp_path / "data"
    (data / "chains-live").mkdir(parents=True)
    (data / "chains-live-rehearsal").mkdir(parents=True)

    state = {
        "running": {"butterfly_spx_app": True, "butterfly_spx_live_app": False},
        "env": {
            "butterfly_spx_app": ["DATABASE__NAME=butterfly_guy"],
            "butterfly_spx_live_app": LIVE_LIMITS,
        },
        "fingerprint": {"butterfly_spx_app": PAPER_FINGERPRINT},
        "image": {"butterfly_spx_live_app": CAND},
        "images": [CAND],
        "mount": str(data / "chains-live"),
        "logs": '{"event": "live_trading_starting", "level": "info"}',
        "broker_rc": 0,
        "check_rc": 0,
    }

    class Session:
        dir = scripts
        state_path = tmp_path / "state.json"
        calls_path = tmp_path / "calls.log"
        notify_log = tmp_path / "notify.log"

        def __init__(self):
            self.state = state
            self.env_file(REHEARSAL=0)

        def env_file(self, **values):
            settings = {"DATE": TODAY, "REL": rel, "CAND": CAND, **values}
            (scripts / "session.env").write_text(
                "".join(f"{key}={value}\n" for key, value in settings.items())
            )

        def run(self, script, dry_run=False, **extra):
            self.state_path.write_text(json.dumps(self.state))
            env = {
                **os.environ,
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "FAKE_DOCKER_STATE": str(self.state_path),
                "FAKE_DOCKER_CALLS": str(self.calls_path),
                "FAKE_TOKEN": str(tokens / "tokens.json"),
                "ROOT": str(tmp_path),
                "INFRA": str(infra),
                "DATA": str(data),
                "PY": str(notify),
                "WAIT_SECONDS": "0",
                "CONTAINER_UID": str(os.getuid()),
                "DRY_RUN": "1" if dry_run else "0",
                **extra,
            }
            result = subprocess.run(
                ["bash", str(scripts / script)], env=env, capture_output=True, text=True
            )
            self.state = json.loads(self.state_path.read_text())
            log = "".join(p.read_text() for p in scripts.glob("*.log"))
            return result, result.stdout + log

        def calls(self):
            if not self.calls_path.exists():
                return []
            return [json.loads(line) for line in self.calls_path.read_text().splitlines()]

        def notifications(self):
            return self.notify_log.read_text() if self.notify_log.exists() else ""

    return Session()


def assert_paper_never_changed(session):
    """The invariant: docker calls that change state only ever address the live service."""
    for call in session.calls():
        joined = " ".join(call)
        assert call[0] in {"ps", "inspect", "image", "exec", "logs", "compose"}, joined
        if call[0] == "compose":
            assert "-p" not in call and "infra" != call[call.index("--project-directory") + 1]
            files = [call[i + 1] for i, a in enumerate(call) if a == "-f"]
            assert files and all("docker-compose.spx-live" in f for f in files), joined
            assert "app_spx" not in call, joined
            for verb in ("up", "stop"):
                if verb in call:
                    assert call[-1] == "app_spx_live", joined
            assert not {"rm", "restart", "kill", "down"} & set(call), joined
        if call[0] == "exec" and "butterfly_spx_app" in call:
            assert (
                call[-2:] == ["python", "-"]
                or call[-3:] == ["python", "-", "--ignore-expired"]  # read-only flat check
                or call[-2] == "-c"
            ), joined
    assert session.state["fingerprint"]["butterfly_spx_app"] in {PAPER_FINGERPRINT, "changed"}


def test_dry_run_prints_the_exact_compose_command_and_starts_nothing(session):
    result, out = session.run("activate.sh", dry_run=True)

    assert result.returncode == 0, out
    rel = session.dir.parent / "rel"
    assert (
        f"DRY_RUN: env SPX_LIVE_IMAGE={CAND} SPX_LIVE_TEST_DATE={TODAY} docker compose "
        f"--project-directory {session.dir.parent / 'infra'} "
        f"-f {rel}/infra/docker-compose.spx-live.yml up -d --no-build --pull never app_spx_live"
    ) in out
    assert "spx_live_db seed-daily-bars --db butterfly_guy_spx_live" in out
    assert not any("up" in call for call in session.calls() if call[0] == "compose")
    assert not (session.dir / "ACTIVATED").exists()
    assert_paper_never_changed(session)


def test_rehearsal_dry_run_uses_the_rehearsal_override_and_database(session):
    session.env_file(REHEARSAL=1)
    session.state["mount"] = str(session.dir.parent / "data" / "chains-live-rehearsal")

    result, out = session.run("activate.sh", dry_run=True)

    assert result.returncode == 0, out
    assert "-f {}/infra/docker-compose.spx-live-rehearsal.yml up -d".format(
        session.dir.parent / "rel"
    ) in out
    check = next(c for c in session.calls() if "check" in c)
    assert check[-3:] == ["--db", "butterfly_guy_spx_live_rehearsal", "--allow-paper-trades"]


def test_activation_starts_live_and_proves_paper_untouched(session):
    result, out = session.run("activate.sh")

    assert result.returncode == 0, out
    assert "verify fail=none" in out
    assert session.state["running"]["butterfly_spx_live_app"] is True
    assert (session.dir / "ACTIVATED").exists()
    assert (session.dir / "paper.fingerprint").read_text().strip() == PAPER_FINGERPRINT
    assert (session.dir / "VERIFIED").exists()
    assert "RUNNING beside paper" in session.notifications()
    assert "Close-out 13:45 PT" in session.notifications()
    assert_paper_never_changed(session)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"env": {"butterfly_spx_app": ["DATABASE__NAME=butterfly_guy",
                                        "EXECUTION__PAPER_TRADING=false"]}},
         "paper container is not paper"),
        ({"running": {"butterfly_spx_app": True, "butterfly_spx_live_app": True}},
         "live container is already running"),
        ({"running": {"butterfly_spx_app": False, "butterfly_spx_live_app": False}},
         "expected exactly one running paper SPX container"),
        ({"images": []}, "missing"),
        ({"broker_rc": 1}, "broker flat/auth check failed"),
        ({"check_rc": 1}, "gate failed"),
        ({"token_override": {"butterfly_spx_app": "1 deadbeef"}}, "token file differs"),
    ],
)
def test_failed_gate_starts_nothing(session, change, reason):
    session.state.update(change)

    result, out = session.run("activate.sh")

    assert result.returncode == 1
    assert reason in out
    assert not any("up" in call for call in session.calls() if call[0] == "compose")
    assert "NOT started" in session.notifications()
    assert_paper_never_changed(session)


def test_chain_journal_owner_gate(session):
    result, out = session.run("activate.sh", CONTAINER_UID="4242")
    assert result.returncode == 1
    assert "not owned by uid 4242" in out


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"env": {"butterfly_spx_app": ["DATABASE__NAME=butterfly_guy"],
                  "butterfly_spx_live_app": LIVE_LIMITS[:-2]}},
         "live env lacks LIVE_MAX_ACCOUNT_DAILY_LOSS=500"),
        ({"env": {"butterfly_spx_app": ["DATABASE__NAME=butterfly_guy"],
                  "butterfly_spx_live_app": [*LIVE_LIMITS, "EXECUTION__EXIT_PRICING=mid_walk"]}},
         "live env must not set EXECUTION__EXIT_PRICING"),
        ({"mount": "/opt/butterflyguy/data/chains"}, "chain journal mount"),
        ({"logs": 'Traceback (most recent call last)\n"live_trading_starting"'},
         "errors at startup"),
        ({"paper_changes_on_up": True}, "PAPER CONTAINER CHANGED"),
    ],
)
def test_failed_verification_stops_only_the_live_container(session, change, reason):
    session.state.update(change)

    result, out = session.run("activate.sh")

    assert result.returncode == 1, out
    assert reason in out
    assert session.state["running"]["butterfly_spx_live_app"] is False
    assert session.state["running"]["butterfly_spx_app"] is True
    assert any("stop" in call for call in session.calls() if call[0] == "compose")
    assert "Live container stopped; paper untouched" in session.notifications()
    assert (session.dir / "STOPPED").exists()
    assert not (session.dir / "VERIFIED").exists()
    assert_paper_never_changed(session)


def test_closeout_when_flat_exports_reports_and_stops_live(session):
    session.run("activate.sh")

    result, out = session.run("closeout.sh")

    assert result.returncode == 0, out
    evidence = next(session.dir.glob("evidence-*"))
    assert (evidence / "paired-report.md").read_text() == "# paired report\n"
    assert (evidence / "container.log").exists()
    compare = next(c for c in session.calls() if "compare" in c)
    assert compare[-8:] == ["--date", TODAY, "--live-db", "butterfly_guy_spx_live",
                            "--paper-rate-limited", "0", "--live-rate-limited", "0"]
    assert session.state["running"]["butterfly_spx_live_app"] is False
    assert "live container stopped, paper untouched" in session.notifications()
    assert (session.dir / "STOPPED").exists()
    assert_paper_never_changed(session)


def test_closeout_passes_each_containers_429_count_to_the_paired_report(session):
    session.run("activate.sh")
    session.state["logs"] = "\n".join([
        '{"event": "live_trading_starting", "level": "info"}',
        '{"endpoint": "get_option_chain", "wait": 1, "event": "rate_limited"}',
        '{"endpoint": "get_option_chain", "wait": 1, "event": "rate_limited"}',
    ])

    result, out = session.run("closeout.sh")

    assert result.returncode == 0, out
    compare = next(c for c in session.calls() if "compare" in c)
    assert compare[-4:] == ["--paper-rate-limited", "2", "--live-rate-limited", "2"]
    since = [c for c in session.calls() if c[0] == "logs" and "--since" in c]
    assert {c[-1] for c in since} == {"butterfly_spx_app", "butterfly_spx_live_app"}
    assert all(c[c.index("--since") + 1] == f"{TODAY}T00:00:00Z" for c in since)


def test_closeout_when_not_flat_leaves_live_running(session):
    session.run("activate.sh")
    session.state["check_rc"] = 1

    result, out = session.run("closeout.sh")

    assert result.returncode == 0, out
    assert session.state["running"]["butterfly_spx_live_app"] is True
    assert "not flat yet" in session.notifications()
    assert_paper_never_changed(session)


def test_stop_live_refuses_when_not_flat_unless_forced(session):
    session.run("activate.sh")
    session.state["broker_rc"] = 1

    refused, _ = session.run("stop-live.sh")
    assert refused.returncode == 1
    assert session.state["running"]["butterfly_spx_live_app"] is True

    forced, out = session.run("stop-live.sh", FORCE="1")
    assert forced.returncode == 0, out
    assert session.state["running"]["butterfly_spx_live_app"] is False
    assert_paper_never_changed(session)


def test_session_template_aborts_at_the_date_gate(session):
    session.env_file(DATE="YYYY-MM-DD")
    result, out = session.run("activate.sh")
    assert result.returncode == 1
    assert "wrong date" in out
    assert session.calls() == []


def test_notify_posts_only_to_the_live_webhook():
    source = (SCRIPTS / "notify.py").read_text()
    assert 'get("DISCORD_WEBHOOK_URL_SPX_LIVE")' in source
    assert 'get("DISCORD_WEBHOOK_URL")' not in source
    assert textwrap.dedent(source).count("urlopen(") == 1


def test_activation_message_quotes_the_session_closeout_time(session):
    session.env_file(CLOSEOUT_PT="13:15")
    result, out = session.run("activate.sh")
    assert result.returncode == 0, out
    assert "Close-out 13:15 PT" in session.notifications()


def test_health_is_silent_before_activation_is_verified(session):
    result, _ = session.run("health.sh")
    assert result.returncode == 0
    assert session.calls() == []
    assert session.notifications() == ""


def test_health_is_silent_on_a_healthy_session(session):
    session.run("activate.sh")
    before = session.notifications()

    result, out = session.run("health.sh")

    assert result.returncode == 0, out
    assert "health fail=none" in out
    assert session.notifications() == before
    assert_paper_never_changed(session)


def test_health_alerts_once_when_live_dies_holding_a_fly_then_on_recovery(session):
    session.run("activate.sh")
    activation_calls = len(session.calls())
    session.state["running"]["butterfly_spx_live_app"] = False
    session.state["check_rc"] = 1

    first, out = session.run("health.sh")
    assert first.returncode == 1
    alert = session.notifications().splitlines()[-1]
    assert "🚨" in alert and "NOT running (exit 137" in alert
    assert "may hold an OPEN live fly" in alert

    again, _ = session.run("health.sh")
    assert again.returncode == 1
    assert session.notifications().count("🚨") == 1  # no repeat for the same problem

    session.state["running"]["butterfly_spx_live_app"] = True
    session.run("health.sh")
    assert "health recovered" in session.notifications().splitlines()[-1]
    health_calls = session.calls()[activation_calls:]
    assert not any(c[0] == "compose" and {"up", "stop"} & set(c) for c in health_calls)
    assert_paper_never_changed(session)


def test_health_says_when_the_dead_live_bot_was_flat(session):
    session.run("activate.sh")
    session.state["running"]["butterfly_spx_live_app"] = False

    session.run("health.sh")

    assert "butterfly_guy_spx_live is flat" in session.notifications().splitlines()[-1]


def test_health_flags_a_changed_paper_container(session):
    session.run("activate.sh")
    session.state["fingerprint"]["butterfly_spx_app"] = "changed"

    result, _ = session.run("health.sh")

    assert result.returncode == 1
    assert "⚠️" in session.notifications() and "PAPER CONTAINER CHANGED" in (
        session.notifications()
    )


def test_health_is_silent_after_a_deliberate_stop(session):
    session.run("activate.sh")
    session.run("closeout.sh")
    calls_before = len(session.calls())
    notes_before = session.notifications()

    result, _ = session.run("health.sh")

    assert result.returncode == 0
    assert len(session.calls()) == calls_before
    assert session.notifications() == notes_before


def test_health_posts_each_docker_restart_once(session):
    session.run("activate.sh")
    session.state["restarts"] = {"butterfly_spx_live_app": 1}

    result, out = session.run("health.sh")
    assert result.returncode == 0, out  # running again after the restart
    assert "restart 1 of at most 3" in session.notifications().splitlines()[-1]

    session.run("health.sh")
    assert session.notifications().count("Docker restarted it") == 1

    session.state["restarts"] = {"butterfly_spx_live_app": 2}
    session.run("health.sh")
    assert "restart 2 of at most 3" in session.notifications().splitlines()[-1]
    assert_paper_never_changed(session)


@pytest.mark.parametrize("event", [
    "monitor_stopped_unknown_broker_state", "entry_loop_stopped_unknown_broker_state",
    "entry_blocked_active_intent",
])
def test_health_alerts_when_the_live_bot_halts_or_entries_are_blocked(session, event):
    # Live 2026-11-19: the bot stayed up but stopped monitoring an open fly for six hours.
    session.run("activate.sh")
    session.state["check_rc"] = 1
    # A real day's log is ~1 MB; the halt sits early in it, so an early-exiting grep would
    # SIGPIPE docker logs and pipefail would hide the halt.
    session.state["logs"] = "\n".join([
        '{"event": "live_trading_starting", "level": "info"}',
        json.dumps({"event": event}),
        *['{"event": "HTTP Request: GET https://api.schwabapi.com/x"}'] * 20000,
    ])

    result, out = session.run("health.sh")

    assert result.returncode == 1, out
    alert = session.notifications().splitlines()[-1]
    if event == "entry_blocked_active_intent":
        assert "⚠️" in alert and "entries BLOCKED by an active intent" in alert
        assert "HALTED" not in alert and "nothing is managing" not in alert
    else:
        assert "🚨" in alert and "HALTED on unknown broker state" in alert
        assert "may hold an OPEN live fly" in alert
    since = [c for c in session.calls() if c[0] == "logs" and "--since" in c]
    assert since and since[-1][-1] == "butterfly_spx_live_app"

    session.run("health.sh")
    assert session.notifications().count("health recovered") == 0
    assert session.notifications().count("entries BLOCKED" if event == "entry_blocked_active_intent"
                                         else "HALTED") == 1
    assert_paper_never_changed(session)


@pytest.mark.parametrize(
    ("problem", "expected"),
    [
        ({"fingerprint": {"butterfly_spx_app": "changed"}}, "PAPER CONTAINER CHANGED"),
        ({"token_override": {"butterfly_spx_live_app": "1 deadbeef"}}, "token file differs"),
    ],
    ids=["paper-changed", "token-mismatch"],
)
def test_health_reports_a_later_problem_over_an_earlier_blocked_entry(session, problem, expected):
    # The blocked-entry event stays in this run's log; it must not hide what breaks next.
    session.run("activate.sh")
    session.state["logs"] = '{"event": "entry_blocked_active_intent"}'
    session.run("health.sh")
    assert "entries BLOCKED" in session.notifications().splitlines()[-1]

    for key, value in problem.items():
        session.state[key] = {**session.state.get(key, {}), **value}
    result, out = session.run("health.sh")

    assert result.returncode == 1, out
    assert expected in session.notifications().splitlines()[-1]


def test_health_repeats_the_unmanaged_fly_alert_until_flat(session):
    session.run("activate.sh")
    session.state["check_rc"] = 1
    session.state["logs"] = '{"trade_id": 100000, "event": "monitor_stopped_unknown_broker_state"}'
    alerted = session.dir / "health.alerted"

    session.run("health.sh")
    session.run("health.sh")  # within the repeat window: silent
    assert session.notifications().count("HALTED") == 1

    alerted.write_text("0\n")  # the last post was long ago
    session.run("health.sh")
    last = session.notifications().splitlines()[-1]
    assert "HALTED" in last and "STILL UNRESOLVED" in last
    assert session.notifications().count("HALTED") == 2

    session.state["check_rc"] = 0  # settled: nothing left to manage
    alerted.write_text("0\n")
    session.run("health.sh")
    assert session.notifications().count("HALTED") == 2
    assert_paper_never_changed(session)


def test_health_does_not_repeat_other_problems(session):
    session.run("activate.sh")
    session.state["fingerprint"]["butterfly_spx_app"] = "changed"

    session.run("health.sh")
    (session.dir / "health.alerted").write_text("0\n")
    session.run("health.sh")

    assert session.notifications().count("PAPER CONTAINER CHANGED") == 1


def _up_files(session):
    up = next(c for c in session.calls() if c[0] == "compose" and "up" in c)
    return [Path(up[i + 1]).name for i, a in enumerate(up) if a == "-f"]


def test_default_session_runs_bid_ladder_exits(session):
    result, out = session.run("activate.sh")
    assert result.returncode == 0, out
    assert _up_files(session) == ["docker-compose.spx-live.yml"]
    assert "bid-ladder exits" in session.notifications()


def test_default_session_fails_verification_if_live_runs_mid_walk(session):
    session.state["env"]["butterfly_spx_live_app"] = [*LIVE_LIMITS,
                                                      "EXECUTION__EXIT_PRICING=mid_walk"]
    result, out = session.run("activate.sh")
    assert result.returncode == 1
    assert "live env must not set EXECUTION__EXIT_PRICING" in out
    assert session.state["running"]["butterfly_spx_live_app"] is False
    assert_paper_never_changed(session)


def test_mid_walk_session_adds_the_overlay_and_requires_the_rule(session):
    session.env_file(REHEARSAL=0, EXIT_PRICING="mid_walk")
    session.state["env"]["butterfly_spx_live_app"] = [*LIVE_LIMITS,
                                                      "EXECUTION__EXIT_PRICING=mid_walk"]
    result, out = session.run("activate.sh")
    assert result.returncode == 0, out
    assert "verify fail=none" in out
    assert _up_files(session) == ["docker-compose.spx-live.yml",
                                  "docker-compose.spx-live-mid-walk.yml"]
    assert "mid_walk exits (pilot)" in session.notifications().splitlines()[-1]
    assert_paper_never_changed(session)


def test_mid_walk_session_stops_live_if_the_rule_did_not_reach_it(session):
    session.env_file(REHEARSAL=0, EXIT_PRICING="mid_walk")
    result, out = session.run("activate.sh")
    assert result.returncode == 1
    assert "live env lacks EXECUTION__EXIT_PRICING=mid_walk" in out
    assert session.state["running"]["butterfly_spx_live_app"] is False


@pytest.mark.parametrize(
    "values, reason",
    [
        ({"REHEARSAL": 0, "EXIT_PRICING": "mid_capped_ladder"}, "unknown EXIT_PRICING"),
        ({"REHEARSAL": 1, "EXIT_PRICING": "mid_walk"}, "not a rehearsal"),
    ],
)
def test_bad_exit_pricing_aborts_before_anything_starts(session, values, reason):
    session.env_file(**values)
    result, out = session.run("activate.sh")
    assert result.returncode == 1
    assert reason in out and "NOT started" in session.notifications()
    assert not any(c[0] == "compose" for c in session.calls())
    assert not (session.dir / "ACTIVATED").exists()


def test_health_clears_blocked_entry_after_a_created_intent_and_warns_on_reblock(session):
    session.run("activate.sh")
    session.state["logs"] = json.dumps({"event": "entry_blocked_active_intent"})
    assert session.run("health.sh")[0].returncode == 1
    assert "entries BLOCKED" in session.notifications().splitlines()[-1]

    session.state["logs"] += "\n" + json.dumps({"event": "entry_intent_created"})
    result, out = session.run("health.sh")
    assert result.returncode == 0, out
    assert "health fail=none" in out
    assert session.notifications().count("health recovered") == 1
    session.run("health.sh")
    assert session.notifications().count("health recovered") == 1

    session.state["logs"] += "\n" + json.dumps({"event": "entry_blocked_active_intent"})
    assert session.run("health.sh")[0].returncode == 1
    assert "entries BLOCKED" in session.notifications().splitlines()[-1]
    assert session.notifications().count("entries BLOCKED") == 3  # includes recovered's 'was'
    assert_paper_never_changed(session)


@pytest.mark.parametrize("halt_first", [True, False])
def test_health_halt_stays_sticky_despite_entry_intent_recovery(session, halt_first):
    session.run("activate.sh")
    session.state["check_rc"] = 1
    events = ["entry_blocked_active_intent", "entry_intent_created"]
    events.insert(0 if halt_first else len(events), "monitor_stopped_unknown_broker_state")
    session.state["logs"] = "\n".join(json.dumps({"event": event}) for event in events)
    result, out = session.run("health.sh")
    assert result.returncode == 1, out
    assert "🚨" in session.notifications().splitlines()[-1]
    assert "HALTED on unknown broker state" in session.notifications().splitlines()[-1]
    assert "health recovered" not in session.notifications()


def test_health_noop_entry_loop_recovery_does_not_prove_the_intent_cleared(session):
    session.run("activate.sh")
    session.state["logs"] = "\n".join(json.dumps({"event": event}) for event in [
        "entry_blocked_active_intent", "entry_loop_recovered",
    ])
    assert session.run("health.sh")[0].returncode == 1
    assert "entries BLOCKED" in session.notifications().splitlines()[-1]


@pytest.mark.parametrize("halt", [False, True], ids=["warning", "halt"])
def test_health_retries_a_failed_problem_post_before_saving_state(session, halt):
    session.run("activate.sh")
    initial = session.notifications()
    session.state["check_rc"] = 1
    event = "monitor_stopped_unknown_broker_state" if halt else "entry_blocked_active_intent"
    session.state["logs"] = json.dumps({"event": event})
    result, out = session.run("health.sh", FAKE_NOTIFY_FAIL="1")
    assert result.returncode == 1, out
    assert "notify failed" in out
    assert session.notifications() == initial
    state = session.dir / "health.state"
    assert not state.exists() or not state.read_text().strip()
    assert not (session.dir / "health.alerted").exists()

    assert session.run("health.sh")[0].returncode == 1
    assert len(session.notifications().splitlines()) == len(initial.splitlines()) + 1
    assert state.read_text().strip()
    if halt:
        assert (session.dir / "health.alerted").read_text().strip()
    session.run("health.sh")  # normal dedup/repeat interval still applies after success
    assert len(session.notifications().splitlines()) == len(initial.splitlines()) + 1


def test_health_failed_halt_repeat_preserves_the_last_success_timestamp(session):
    session.run("activate.sh")
    session.state["check_rc"] = 1
    session.state["logs"] = json.dumps({"event": "monitor_stopped_unknown_broker_state"})
    session.run("health.sh")
    initial = session.notifications()
    state = (session.dir / "health.state").read_text()
    alerted = session.dir / "health.alerted"
    alerted.write_text("0\n")
    session.run("health.sh", FAKE_NOTIFY_FAIL="1")
    assert alerted.read_text() == "0\n"
    assert (session.dir / "health.state").read_text() == state
    assert session.notifications() == initial
    session.run("health.sh")
    assert "STILL UNRESOLVED" in session.notifications().splitlines()[-1]
    assert alerted.read_text() != "0\n"
    sent = session.notifications()
    session.run("health.sh")
    assert session.notifications() == sent


def test_health_failed_recovery_post_keeps_state_for_the_next_run(session):
    session.run("activate.sh")
    session.state["logs"] = json.dumps({"event": "entry_blocked_active_intent"})
    session.run("health.sh")
    previous = (session.dir / "health.state").read_text()
    session.state["logs"] += "\n" + json.dumps({"event": "entry_intent_created"})
    result, _ = session.run("health.sh", FAKE_NOTIFY_FAIL="1")
    assert result.returncode == 1
    assert (session.dir / "health.state").read_text() == previous
    assert "health recovered" not in session.notifications()
    assert session.run("health.sh")[0].returncode == 0
    assert session.notifications().count("health recovered") == 1
    session.run("health.sh")
    assert session.notifications().count("health recovered") == 1


def test_health_failed_restart_post_is_retried_before_saving_seen_count(session):
    session.run("activate.sh")
    session.state["restarts"] = {"butterfly_spx_live_app": 1}
    session.run("health.sh", FAKE_NOTIFY_FAIL="1")
    seen = session.dir / "restarts.seen"
    assert not seen.exists() or seen.read_text().strip() == "0"
    assert "restart 1 of at most 3" not in session.notifications()
    session.run("health.sh")
    assert seen.read_text().strip() == "1"
    assert session.notifications().count("restart 1 of at most 3") == 1
    session.run("health.sh")
    assert session.notifications().count("restart 1 of at most 3") == 1
