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


class EquityScanLimits(BaseModel):
    prior_gainers: int = 15
    prior_losers: int = 15
    premarket_gainers: int = 15
    premarket_losers: int = 15
    movers_per_bucket: int = 10


class EquityScanSettings(BaseModel):
    universes: list[Literal["sp500", "nq100", "custom"]] = Field(
        default_factory=lambda: ["sp500", "nq100", "custom"]
    )
    universe_dir: str = "configs/universes"
    custom_watchlist: str = "configs/universes/custom.txt"
    filters: EquityScanFilters = Field(default_factory=EquityScanFilters)
    limits: EquityScanLimits = Field(default_factory=EquityScanLimits)
    batch_size: int = 150
    rvol_lookback_days: int = 20
    rvol_fetch_concurrency: int = 10
    group_by_sector: bool = True
    include_movers: bool = True
    mover_indexes: list[str] = Field(
        default_factory=lambda: ["NASDAQ", "NYSE", "EQUITY_ALL"]
    )
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
