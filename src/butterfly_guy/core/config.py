"""Configuration management using Pydantic settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SchwabSettings(BaseModel):
    api_key: str = ""
    secret_key: str = ""
    token_path: str = "tokens.json"
    account_id: str = ""
    max_token_age: int = 518400


class StrategySettings(BaseModel):
    underlying: str = "SPX"
    wing_widths: list[int] = Field(default_factory=lambda: [10, 20, 30])
    spot_range: int = 100
    rr_min: float = 8.0
    max_cost_per_width: dict[int, float] = Field(
        default_factory=lambda: {10: 1.00, 20: 2.00, 30: 3.00}
    )


class EntrySettings(BaseModel):
    start_time: str = "07:00"
    end_time: str = "07:30"
    timezone: str = "America/Los_Angeles"


class ExecutionSettings(BaseModel):
    price_ladder_step: float = 0.05
    price_ladder_steps: int = 4
    retry_interval_seconds: int = 20
    order_timeout_seconds: int = 300


class TimeRegime(BaseModel):
    start_minutes_after_open: int
    end_minutes_after_open: int
    drawdown_threshold: float


class ProfitManagementSettings(BaseModel):
    regimes: dict[str, TimeRegime] = Field(default_factory=dict)
    exit_before_close_minutes: int = 5


class RiskSettings(BaseModel):
    max_daily_loss: float = 500.0
    max_trades_per_day: int = 2
    max_position_size: int = 1


class CollectorSettings(BaseModel):
    snapshot_interval_seconds: int = 60


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "butterfly_guy"
    user: str = "butterfly"
    password: str = "butterfly_dev"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class MonitoringSettings(BaseModel):
    metrics_port: int = 8000
    log_level: str = "INFO"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        extra="ignore",
    )

    schwab: SchwabSettings = Field(default_factory=SchwabSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)
    entry: EntrySettings = Field(default_factory=EntrySettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    profit_management: ProfitManagementSettings = Field(
        default_factory=ProfitManagementSettings
    )
    risk: RiskSettings = Field(default_factory=RiskSettings)
    collector: CollectorSettings = Field(default_factory=CollectorSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)


def load_config(config_path: str | Path = "config.yaml", env_file: str = ".env") -> AppConfig:
    """Load configuration from YAML file and environment variables."""
    config_path = Path(config_path)
    yaml_data: dict[str, Any] = {}

    if config_path.exists():
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f) or {}

    # Load env vars for Schwab credentials
    import os
    from dotenv import load_dotenv
    load_dotenv(env_file)

    schwab_data = yaml_data.get("schwab", {})
    schwab_data.setdefault("api_key", os.getenv("SCHWAB_API_KEY", ""))
    schwab_data.setdefault("secret_key", os.getenv("SCHWAB_SECRET_KEY", ""))
    schwab_data.setdefault("account_id", os.getenv("SCHWAB_ACCOUNT_ID", ""))
    
    if os.getenv("SCHWAB_TOKEN_PATH"):
        schwab_data.setdefault("token_path", os.getenv("SCHWAB_TOKEN_PATH"))
    yaml_data["schwab"] = schwab_data

    return AppConfig(**yaml_data)
