"""Configuration for the daily report card."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ReportCardThresholds(BaseModel):
    large_loss_day_pct: float = 2.0
    large_single_loss: float = 200.0
    low_buying_power: float = 500.0
    top_trades_count: int = 3


class DailyReportCardSettings(BaseModel):
    thresholds: ReportCardThresholds = Field(default_factory=ReportCardThresholds)
    report_dir: str = "reports/daily_report_card"


def load_daily_report_card_config(
    path: str | Path = "configs/daily_report_card.yaml",
) -> DailyReportCardSettings:
    config_path = Path(path)
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open() as f:
            data = yaml.safe_load(f) or {}
    return DailyReportCardSettings.model_validate(data)
