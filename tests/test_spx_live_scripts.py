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
    elif rest[1:] == ["python", "-"]:
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
    notify.write_text(f'#!/bin/sh\necho "$2" >> {tmp_path}/notify.log\n')
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
            assert call[-2:] == ["python", "-"] or call[-2] == "-c", joined
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
    assert "RUNNING beside paper" in session.notifications()
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
    assert_paper_never_changed(session)


def test_closeout_when_flat_exports_reports_and_stops_live(session):
    session.run("activate.sh")

    result, out = session.run("closeout.sh")

    assert result.returncode == 0, out
    evidence = next(session.dir.glob("evidence-*"))
    assert (evidence / "paired-report.md").read_text() == "# paired report\n"
    assert (evidence / "container.log").exists()
    compare = next(c for c in session.calls() if "compare" in c)
    assert compare[-4:] == ["--date", TODAY, "--live-db", "butterfly_guy_spx_live"]
    assert session.state["running"]["butterfly_spx_live_app"] is False
    assert "live container stopped, paper untouched" in session.notifications()
    assert_paper_never_changed(session)


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
