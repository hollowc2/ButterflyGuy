"""Configuration for the equity morning scan."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class EquityScanFilters(BaseModel):
    min_price: float = 5.0
    min_volume: int = 500_000
    prior_day_min_pct: float = 3.0
    premarket_min_gap_pct: float = 2.0
    min_rvol: float = 0.0  # 0 = disabled; e.g. 0.05 = 5% of 20d avg daily volume
    max_abs_pct: float | None = 50.0  # cap extreme % moves; None = off
    max_price_disagreement_pct: float | None = 5.0
    max_reference_price_deviation_pct: float | None = 25.0
    require_index_membership: bool = False  # symbol must be in sp500 or nq100


class EquityScanLimits(BaseModel):
    prior_gainers: int = 15
    prior_losers: int = 15
    premarket_gainers: int = 15
    premarket_losers: int = 15
    opening_focus: int = 12
    catalyst_watch: int = 12
    movers_per_bucket: int = 10


class EquityNewsSettings(BaseModel):
    enabled: bool = True
    providers: list[Literal["sec", "alpha_vantage"]] = Field(
        default_factory=lambda: ["sec", "alpha_vantage"]
    )
    recent_days: int = 3
    upcoming_days: int = 5
    max_symbols: int = 80
    min_score_for_focus: float = 4.0
    request_timeout_seconds: float = 10.0
    sec_user_agent: str = "butterfly-guy-equity-scan/0.1 (set SEC_USER_AGENT)"
    sec_user_agent_env: str = "SEC_USER_AGENT"
    sec_forms: list[str] = Field(
        default_factory=lambda: [
            "8-K",
            "10-Q",
            "10-K",
            "S-1",
            "S-3",
            "SC 13D",
            "SC 13G",
            "DEF 14A",
            "PRE 14A",
        ]
    )
    alpha_vantage_api_key_env: str = "ALPHA_VANTAGE_API_KEY"
    alpha_vantage_max_news_symbols: int = 20
    alpha_vantage_news_limit: int = 20


class EquityScanSettings(BaseModel):
    universes: list[Literal["sp500", "nq100", "liquid", "custom"]] = Field(
        default_factory=lambda: ["sp500", "nq100", "liquid", "custom"]
    )
    universe_dir: str = "configs/universes"
    custom_watchlist: str = "configs/universes/custom.txt"
    filters: EquityScanFilters = Field(default_factory=EquityScanFilters)
    limits: EquityScanLimits = Field(default_factory=EquityScanLimits)
    news: EquityNewsSettings = Field(default_factory=EquityNewsSettings)
    batch_size: int = 150
    rvol_lookback_days: int = 20
    rvol_fetch_concurrency: int = 4
    group_by_sector: bool = True
    include_movers: bool = False
    movers_min_abs_pct: float = 1.0
    mover_indexes: list[str] = Field(
        default_factory=lambda: ["NASDAQ", "NYSE", "EQUITY_ALL"]
    )
    premarket_start_et: str = "04:00"
    report_dir: str = "reports/equity_scans"
    context_symbols: list[str] = Field(
        default_factory=lambda: ["$SPX", "$COMPX", "$DJI", "SPY", "QQQ"]
    )


def load_equity_scan_config(path: str | Path = "configs/equity_scan.yaml") -> EquityScanSettings:
    """Load equity scan settings from YAML."""
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
    return EquityScanSettings(**data)
