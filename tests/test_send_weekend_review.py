"""The read-only reporting CLI must not validate unrelated trading settings."""

import pytest
from pydantic import ValidationError

from tools.send_weekend_review import load_review_database


@pytest.fixture(autouse=True)
def clean_database_environment(monkeypatch):
    import os

    for key in os.environ:
        if key.startswith("DATABASE__") or key == "DATABASE_PASSWORD":
            monkeypatch.delenv(key)


def test_load_review_database_ignores_new_trading_schema(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "database:\n  host: reporting-db\n  name: review\n"
        "collector:\n  record_timing: true\n  align_to_minute: true\n"
        "  align_offset_seconds: 0.0\n  future_collector_setting: true\n"
        "execution:\n  future_execution_setting: true\n"
    )
    settings = load_review_database(config, tmp_path / "absent.env")
    assert settings.host == "reporting-db"
    assert settings.name == "review"


def test_load_review_database_preserves_password_and_nested_env_precedence(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("database:\n  password: yaml-password\n")
    env = tmp_path / "report.env"
    env.write_text("DATABASE_PASSWORD=legacy-password\n")
    assert load_review_database(config, env).password == "yaml-password"
    config.write_text("database: {}\n")
    assert load_review_database(config, env).password == "legacy-password"
    monkeypatch.setenv("DATABASE__PASSWORD", "nested-password")
    monkeypatch.setenv("DATABASE__HOST", "nested-host")
    settings = load_review_database(config, env)
    assert settings.password == "nested-password"
    assert settings.host == "nested-host"


def test_load_review_database_rejects_bad_database_settings(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("database:\n  port: invalid\n")
    with pytest.raises(ValidationError):
        load_review_database(config, tmp_path / "absent.env")


def test_load_review_database_requires_config_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_review_database(tmp_path / "absent.yaml", tmp_path / "absent.env")
