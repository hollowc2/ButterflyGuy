"""Tests for configuration loading."""

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


def test_allow_live_trading_requires_explicit_env(tmp_path, monkeypatch):
    config_data = {"execution": {"paper_trading": False}}
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump(config_data))

    monkeypatch.delenv("ALLOW_LIVE_TRADING", raising=False)
    config = load_config(config_path=config_file, env_file=str(tmp_path / ".env"))
    assert config.execution.paper_trading is False
    assert config.execution.allow_live_trading is False

    monkeypatch.setenv("ALLOW_LIVE_TRADING", "true")
    config = load_config(config_path=config_file, env_file=str(tmp_path / ".env"))
    assert config.execution.allow_live_trading is True


def test_database_dsn():
    config = AppConfig()
    dsn = config.database.dsn
    assert "postgresql://" in dsn
    assert "butterfly_guy" in dsn


def test_database_password_falls_back_to_compose_env(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    monkeypatch.delenv("DATABASE__PASSWORD", raising=False)
    monkeypatch.setenv("DATABASE_PASSWORD", "compose-secret")

    config = load_config(config_path=config_file, env_file=str(tmp_path / ".env"))

    assert config.database.password == "compose-secret"


def test_nested_database_password_overrides_compose_env(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    monkeypatch.setenv("DATABASE_PASSWORD", "compose-secret")
    monkeypatch.setenv("DATABASE__PASSWORD", "nested-secret")

    config = load_config(config_path=config_file, env_file=str(tmp_path / ".env"))

    assert config.database.password == "nested-secret"


def test_profit_management_regimes():
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


def test_profit_management_strategy_defaults_to_peak_value_trailer():
    config = AppConfig()

    assert config.profit_management.strategy == "peakvaluetrailer"
    assert config.profit_management.profitprotector.profit_lock_floor_profit == 0.75


def test_xsp_config_tracks_spx_proxy_widths():
    config = load_config(config_path="configs/config_xsp.yaml")

    assert config.strategy.underlying == "XSP"
    assert 1 not in config.strategy.wing_widths
    assert config.strategy.wing_widths == [2, 3, 4, 5, 6, 7]
    assert config.strategy.vix_width_buckets is not None
    assert config.strategy.vix_width_buckets[1].widths == [3, 4]
    assert config.execution.paper_slippage_per_spread == 0.005
    assert config.execution.paper_commission_per_contract == 0.65


def test_spx_goldilocks_width_bucket_uses_20_30_40():
    config = load_config(config_path="configs/config.yaml")

    assert config.strategy.vix_width_buckets is not None
    assert config.strategy.vix_width_buckets[1].vix_max == 24.5
    assert config.strategy.vix_width_buckets[1].widths == [20, 30, 40]
