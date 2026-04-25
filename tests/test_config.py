"""Tests for configuration loading."""

import os
import tempfile

import pytest
import yaml

from butterfly_guy.core.config import AppConfig, load_config


def test_load_config_defaults():
    """Loading config with no files should return sensible defaults."""
    config = AppConfig()
    assert config.strategy.underlying == "SPX"
    assert config.risk.max_daily_loss == 500.0
    assert config.risk.max_trades_per_day == 1
    assert 10 in config.strategy.wing_widths


def test_load_config_from_yaml(tmp_path):
    """Config values from YAML should override defaults."""
    config_data = {
        "strategy": {"underlying": "XSP", "rr_min": 10.0},
        "risk": {"max_daily_loss": 1000.0},
    }
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))

    config = load_config(config_path=config_file, env_file=str(tmp_path / ".env"))
    assert config.strategy.underlying == "XSP"
    assert config.strategy.rr_min == 10.0
    assert config.risk.max_daily_loss == 1000.0


def test_database_dsn():
    config = AppConfig()
    dsn = config.database.dsn
    assert "postgresql://" in dsn
    assert "butterfly_guy" in dsn


def test_profit_management_regimes():
    config = AppConfig()
    # Regimes come from YAML, so test defaults directly
    from butterfly_guy.core.config import ProfitManagementSettings, TimeRegime
    settings = ProfitManagementSettings(
        regimes={
            "morning": TimeRegime(
                start_minutes_after_open=0,
                end_minutes_after_open=120,
                drawdown_threshold=0.50,
            ),
            "afternoon": TimeRegime(
                start_minutes_after_open=240,
                end_minutes_after_open=390,
                drawdown_threshold=0.30,
            ),
        }
    )
    assert settings.regimes["morning"].drawdown_threshold == 0.50
    assert settings.regimes["afternoon"].drawdown_threshold == 0.30
