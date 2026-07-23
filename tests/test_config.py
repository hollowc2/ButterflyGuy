"""Tests for configuration loading."""

import pytest
import yaml
from pydantic import ValidationError

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


def test_config_rejects_unknown_keys():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        AppConfig(risk={"max_daily_los": 500})


@pytest.mark.parametrize(
    "override",
    [
        {"strategy": {"wing_widths": [10, 10]}},
        {"strategy": {"rr_min": 12, "rr_target": 10}},
        {"execution": {"price_ladder_steps": 0}},
        {"risk": {"max_position_size": 0}},
        {"entry": {"start_time": "08:00", "end_time": "07:00"}},
    ],
)
def test_config_rejects_unsafe_trading_values(override):
    with pytest.raises(ValidationError):
        AppConfig(**override)


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


def test_xsp_config_uses_independent_noisy_product_controls():
    config = load_config(config_path="configs/config_xsp.yaml")

    assert config.strategy.underlying == "XSP"
    assert 2 not in config.strategy.wing_widths
    assert config.strategy.wing_widths == [3, 4, 5]
    assert config.strategy.min_debit == 0.25
    assert config.strategy.vix_width_buckets is not None
    assert config.strategy.vix_width_buckets[1].widths == [3, 4, 5]
    assert config.execution.paper_slippage_per_spread == 0.005
    assert config.execution.paper_commission_per_contract == 0.65
    assert config.risk.max_weekly_loss is None
    assert config.profit_management.regimes["morning"].drawdown_threshold == 0.80
    assert config.profit_management.regimes["morning"].confirmation_polls == 3
    assert config.profit_management.regimes["morning"].min_peak_profit_ratio == 1.25
    assert config.profit_management.regimes["morning"].min_hold_minutes == 30
    assert config.profit_management.quote_quality.enabled is True
    assert config.profit_management.quote_quality.min_bid_to_mark_ratio == 0.75
    assert config.profit_management.quote_quality.max_spread_width_ratio == 0.50
    assert config.profit_management.quote_quality.min_mark_value == 0.25
    assert config.profit_management.peak_tracking.confirmation_polls == 3
    assert config.profit_management.peak_tracking.require_quote_quality is True


def test_ndx_config_uses_larger_weekly_loss_limit():
    config = load_config(config_path="configs/config_ndx.yaml")

    assert config.strategy.underlying == "NDX"
    assert config.risk.max_daily_loss == 500.0
    assert config.risk.max_weekly_loss == 5000.0


def test_spx_goldilocks_width_bucket_uses_20_30_40():
    config = load_config(config_path="configs/config.yaml")

    assert config.strategy.vix_width_buckets is not None
    assert config.strategy.vix_width_buckets[1].vix_max == 24.5
    assert config.strategy.vix_width_buckets[1].widths == [20, 30, 40]


def test_spx_candidate_is_isolated_paper_profile():
    config = load_config(config_path="configs/config_spx_candidate.yaml")

    assert config.strategy.underlying == "SPX"
    assert config.entry.start_time == "06:45"
    assert config.entry.end_time == "07:30"
    assert config.entry.strike_selection_method == "BEST_RR"
    assert config.execution.paper_trading is True
    assert config.execution.allow_live_trading is False
    assert config.profit_management.strategy == "profitprotector"
    assert {
        name: (regime.drawdown_threshold, regime.confirmation_polls)
        for name, regime in config.profit_management.regimes.items()
    } == {
        "morning": (0.45, 2),
        "late_morning": (0.65, 2),
        "afternoon": (0.55, 2),
    }


def test_ndx_config_keeps_spx_style_rr_target_with_10pt_grid_wing_widths():
    config = load_config(config_path="configs/config_ndx.yaml")

    assert config.strategy.underlying == "NDX"
    assert config.strategy.rr_target == 10.0
    assert config.strategy.wing_widths == [80, 100, 150]
    assert config.strategy.max_cost_per_width[100] == 8.0
