"""Configuration management using Pydantic settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SchwabSettings(BaseModel):
    api_key: str = ""
    secret_key: str = ""
    token_path: str = "tokens.json"
    account_id: str = ""
    max_token_age: int = 518400


class VixWidthBucket(BaseModel):
    vix_max: float       # exclusive upper bound; use 9999.0 for the catch-all last bucket
    widths: list[int]    # widths to scan in this regime (narrow → wide, typically 3 entries)


class StrategySettings(BaseModel):
    underlying: str = "SPX"
    wing_widths: list[int] = Field(default_factory=lambda: [10, 20, 30])
    vix_width_buckets: list[VixWidthBucket] | None = None
    spot_range: int = 100
    min_debit: float = 0.05
    rr_min: float = 8.0
    rr_max: float = 12.0
    rr_target: float = 10.0
    max_cost_per_width: dict[int, float] = Field(
        default_factory=lambda: {10: 1.00, 20: 2.00, 30: 3.00}
    )


class EntrySettings(BaseModel):
    start_time: str = "07:00"
    end_time: str = "07:30"
    timezone: str = "America/Los_Angeles"
    use_bias_filter: bool = False  # if True, use BiasScoreFilter instead of simple gap
    strike_selection_method: Literal["VIX", "TARGET_COST", "BEST_RR"] = "TARGET_COST"
    center_tolerance: float = 15.0  # pts; how far a candidate's center can stray from VIX target
    max_vix_age_seconds: int = 300  # VIX-based entries require a recent $VIX snapshot
    bull_call_bias: bool = False  # Override to CALL in BULL regime on gap-down days
    min_gap_pct: float | None = None  # Skip days where |gap| < this (e.g. 0.0025 = 0.25%)


class ExecutionSettings(BaseModel):
    price_ladder_step: float = 0.05
    price_ladder_steps: int = 4
    retry_interval_seconds: int = 20
    order_timeout_seconds: int = 300
    paper_trading: bool = True  # default safe — set False to go live
    paper_fill_buffer: float = 0.05          # extra width beyond synthetic ask/bid required to fill
    paper_slippage_per_spread: float = 0.05  # additional cost/credit lost on fill_price
    paper_commission_per_contract: float = 0.65  # per option contract (4 per butterfly)
    paper_min_oi_per_leg: int = 0            # 0 = disabled; minimum open interest per leg
    # Must be true, or ALLOW_LIVE_TRADING=true, to place live orders.
    allow_live_trading: bool = False


class TimeRegime(BaseModel):
    start_minutes_after_open: int
    end_minutes_after_open: int
    drawdown_threshold: float
    confirmation_polls: int = 1
    min_peak_profit_ratio: float = 1.0
    min_hold_minutes: float = 0.0


class QuoteQualitySettings(BaseModel):
    enabled: bool = False
    min_bid_to_mark_ratio: float = 0.0
    max_spread_width_ratio: float | None = None
    min_mark_value: float = 0.0
    max_leg_spread_to_mark_ratio: float | None = None
    max_leg_spread_abs: float | None = None


class PeakTrackingSettings(BaseModel):
    confirmation_polls: int = 1
    confirmation_tolerance_ratio: float = 0.05
    require_quote_quality: bool = False
    max_jump_ratio: float | None = None
    max_jump_abs: float | None = None


class ProfitProtectorSettings(BaseModel):
    breakeven_activation_profit: float = 1.00
    breakeven_floor_profit: float = 0.00
    profit_lock_activation_profit: float = 2.00
    profit_lock_floor_profit: float = 0.75
    large_peak_profit_ratio: float = 2.00
    large_peak_drawdown_threshold: float = 0.50


class ProfitManagementSettings(BaseModel):
    strategy: Literal["peakvaluetrailer", "profitprotector"] = "peakvaluetrailer"
    regimes: dict[str, TimeRegime] = Field(default_factory=dict)
    # 0 disables pre-close liquidation; cash-settled index butterflies should run to close.
    exit_before_close_minutes: int = 0
    max_loss_from_cost: float = 0.50
    use_absolute_loss_stop: bool = False
    quote_quality: QuoteQualitySettings = Field(default_factory=QuoteQualitySettings)
    peak_tracking: PeakTrackingSettings = Field(default_factory=PeakTrackingSettings)
    profitprotector: ProfitProtectorSettings = Field(default_factory=ProfitProtectorSettings)


class RiskSettings(BaseModel):
    max_daily_loss: float = 500.0
    max_trades_per_day: int = 1
    max_position_size: int = 1
    max_weekly_loss: float = 1500.0        # 3x daily default; halt for week if exceeded
    max_consecutive_losses: int = 10        # warn after N consecutive losing trades (0 = disabled)
    min_buying_power: float = 500.0        # minimum buying power required to enter
    fail_safe_on_balance_error: bool = True  # if True, block trading when balance API unavailable


class CollectorSettings(BaseModel):
    snapshot_interval_seconds: int = 60


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "butterfly_guy"
    user: str = "butterfly"
    password: str = ""

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
    load_dotenv(env_file)

    schwab_data = yaml_data.get("schwab", {})
    schwab_data.setdefault("api_key", os.getenv("SCHWAB_API_KEY", ""))
    schwab_data.setdefault("secret_key", os.getenv("SCHWAB_SECRET_KEY", ""))
    schwab_data.setdefault("account_id", os.getenv("SCHWAB_ACCOUNT_ID", ""))

    if os.getenv("SCHWAB_TOKEN_PATH"):
        schwab_data.setdefault("token_path", os.getenv("SCHWAB_TOKEN_PATH"))
    yaml_data["schwab"] = schwab_data

    database_data = yaml_data.get("database", {})
    if os.getenv("DATABASE_PASSWORD") and not os.getenv("DATABASE__PASSWORD"):
        database_data.setdefault("password", os.getenv("DATABASE_PASSWORD"))
    yaml_data["database"] = database_data

    execution_data = yaml_data.get("execution", {})
    allow_live = os.getenv("ALLOW_LIVE_TRADING", "").lower() in {"1", "true", "yes"}
    if allow_live:
        execution_data["allow_live_trading"] = True
    yaml_data["execution"] = execution_data

    return AppConfig(**yaml_data)
