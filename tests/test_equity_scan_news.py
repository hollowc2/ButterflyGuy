"""Tests for free-source equity catalyst parsing."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.equity_scan.config import EquityNewsSettings, EquityScanSettings
from butterfly_guy.equity_scan.news import (
    NewsImpact,
    _recent_sec_filings,
    merge_news_impacts,
)


def test_equity_scan_settings_accepts_news_config():
    settings = EquityScanSettings(
        news={
            "enabled": True,
            "providers": ["sec"],
            "recent_days": 2,
            "upcoming_days": 4,
            "max_symbols": 25,
        }
    )
    assert settings.news.providers == ["sec"]
    assert settings.news.recent_days == 2
    assert settings.news.upcoming_days == 4
    assert settings.news.max_symbols == 25


def test_recent_sec_filings_scores_impact_forms():
    settings = EquityNewsSettings(recent_days=3)
    today = dt.datetime(2026, 6, 8, 8, 0, tzinfo=EASTERN).date()
    impact = _recent_sec_filings(
        "AAPL",
        {
            "filings": {
                "recent": {
                    "form": ["8-K", "4", "10-Q"],
                    "filingDate": ["2026-06-07", "2026-06-07", "2026-06-01"],
                    "primaryDocDescription": ["Current report", "", "Quarterly report"],
                }
            }
        },
        today=today,
        settings=settings,
    )
    assert impact is not None
    assert impact.symbol == "AAPL"
    assert impact.score == 6.0
    assert impact.reasons == ("recent SEC filing",)
    assert impact.sec_forms == ("8-K",)
    assert impact.providers == ("sec",)
    assert impact.recent_headlines == ("8-K filed 2026-06-07: Current report",)


def test_merge_news_impacts_dedupes_context():
    merged = merge_news_impacts(
        {
            "AAPL": NewsImpact(
                symbol="AAPL",
                score=6.0,
                reasons=("recent SEC filing",),
                recent_headlines=("8-K filed 2026-06-07",),
                providers=("sec",),
            )
        },
        {
            "AAPL": NewsImpact(
                symbol="AAPL",
                score=5.0,
                reasons=("upcoming earnings",),
                upcoming_events=("earnings expected 2026-06-10",),
                providers=("alpha_vantage",),
            )
        },
    )
    impact = merged["AAPL"]
    assert impact.score == 11.0
    assert impact.reasons == ("recent SEC filing", "upcoming earnings")
    assert impact.providers == ("sec", "alpha_vantage")
