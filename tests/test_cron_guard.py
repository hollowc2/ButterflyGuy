"""Tests for tools/cron_guard.py and tools/check_runtime_configs.py."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cron_guard = _load("cron_guard")
check_runtime_configs = _load("check_runtime_configs")


def _capture_posts(monkeypatch) -> list[tuple[str, str]]:
    posts: list[tuple[str, str]] = []
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://example.invalid/hook")
    monkeypatch.setattr(cron_guard, "post", lambda url, content: posts.append((url, content)))
    return posts


def test_success_passes_output_through_without_alert(monkeypatch, capsys):
    posts = _capture_posts(monkeypatch)
    rc = cron_guard.main(["--job", "ok_job", "--", sys.executable, "-c", "print('hello')"])
    assert rc == 0
    assert "hello" in capsys.readouterr().out
    assert posts == []


def test_failure_alerts_with_job_exit_code_and_tail(monkeypatch, capsys):
    posts = _capture_posts(monkeypatch)
    script = (
        "import sys; print('line1'); print('ValidationError: boom', file=sys.stderr); sys.exit(3)"
    )
    rc = cron_guard.main(["--job", "daily_report_card", "--", sys.executable, "-c", script])
    assert rc == 3
    assert "ValidationError: boom" in capsys.readouterr().out
    [(url, content)] = posts
    assert url == "https://example.invalid/hook"
    assert "`daily_report_card`" in content and "exit 3" in content
    assert "ValidationError: boom" in content


def test_missing_command_binary_alerts(monkeypatch):
    posts = _capture_posts(monkeypatch)
    rc = cron_guard.main(["--job", "gone", "--", "/nonexistent/binary"])
    assert rc == 127
    assert len(posts) == 1 and "could not start" in posts[0][1]


def test_alert_fits_discord_limit():
    content = cron_guard.format_alert("job", 1, ["x" * 900] * 8)
    assert len(content) <= cron_guard.DISCORD_LIMIT
    assert content.endswith("```")


def test_shipped_runtime_configs_load():
    assert check_runtime_configs.main(ROOT / "configs") == 0


def test_runtime_config_check_flags_unknown_keys(tmp_path, capsys):
    for name in (*check_runtime_configs.APP_CONFIGS, "daily_report_card.yaml"):
        shutil.copy(ROOT / "configs" / name, tmp_path / name)
    with open(tmp_path / "config.yaml", "a") as f:
        f.write("\nnot_a_real_section:\n  key: 1\n")
    assert check_runtime_configs.main(tmp_path) == 1
    assert "FAIL config.yaml" in capsys.readouterr().out


def test_runtime_config_check_flags_missing_file(tmp_path, capsys):
    assert check_runtime_configs.main(tmp_path) == 1
    assert "FAIL config.yaml" in capsys.readouterr().out
