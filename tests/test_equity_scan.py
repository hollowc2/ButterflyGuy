"""Tests for equity morning scan logic."""

from __future__ import annotations

from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.report import build_report
from butterfly_guy.equity_scan.scanner import (
    build_snapshots,
    parse_equity_quote,
    rank_scan_results,
)
from butterfly_guy.equity_scan.universes import build_symbol_map
from butterfly_guy.equity_scan.volume import avg_daily_volume, compute_rvol


def _quote_payload(
    *,
    close: float,
    last: float,
    net_pct: float,
    volume: int,
    extended_last: float | None = None,
    extended_volume: int = 0,
) -> dict:
    payload = {
        "quote": {
            "closePrice": close,
            "lastPrice": last,
            "netPercentChange": net_pct,
            "totalVolume": volume,
        }
    }
    if extended_last is not None or extended_volume:
        payload["extended"] = {
            "lastPrice": extended_last,
            "totalVolume": extended_volume,
        }
    return payload


def test_parse_equity_quote_uses_extended_price_for_gap():
    snap = parse_equity_quote(
        "AAPL",
        _quote_payload(
            close=100.0,
            last=98.0,
            net_pct=-2.0,
            volume=1_000_000,
            extended_last=105.0,
            extended_volume=250_000,
        ),
        universes={"sp500"},
        sector="Information Technology",
        avg_volume_20d=1_000_000.0,
    )
    assert snap is not None
    assert snap.price == 105.0
    assert snap.prior_day_pct == -2.0
    assert snap.session_gap_pct == 5.0
    assert snap.premarket_volume == 250_000
    assert snap.rvol == 0.25
    assert snap.sector == "Information Technology"


def test_build_snapshots_filters_by_price_volume_and_rvol():
    settings = EquityScanSettings()
    settings.filters.min_price = 10.0
    settings.filters.min_volume = 500_000
    settings.filters.min_rvol = 0.10
    symbol_map = build_symbol_map(
        {
            "custom": ["GOOD", "CHEAP", "LOWVOL", "LOWRVOL"],
        }
    )
    quotes = {
        "GOOD": _quote_payload(
            close=100,
            last=112,
            net_pct=12.0,
            volume=1_000_000,
            extended_volume=200_000,
        ),
        "CHEAP": _quote_payload(close=4, last=4.5, net_pct=12.5, volume=1_000_000),
        "LOWVOL": _quote_payload(close=100, last=112, net_pct=12.0, volume=10_000),
        "LOWRVOL": _quote_payload(
            close=100,
            last=112,
            net_pct=12.0,
            volume=1_000_000,
            extended_volume=10_000,
        ),
    }
    avg_volumes = {
        "GOOD": 1_000_000.0,
        "LOWRVOL": 1_000_000.0,
    }
    snapshots = build_snapshots(
        quotes,
        symbol_map,
        settings,
        avg_volumes=avg_volumes,
        sector_map={"GOOD": "Information Technology", "LOWRVOL": "Energy"},
    )
    assert [snap.symbol for snap in snapshots] == ["GOOD"]
    assert snapshots[0].rvol == 0.2


def test_rank_scan_results_returns_expected_sections():
    settings = EquityScanSettings()
    snapshots = [
        parse_equity_quote(
            "WIN",
            _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000, extended_last=112),
            universes={"sp500"},
            sector="Information Technology",
        ),
        parse_equity_quote(
            "LOSE",
            _quote_payload(close=100, last=90, net_pct=-10.0, volume=1_000_000, extended_last=88),
            universes={"nq100"},
            sector="Health Care",
        ),
        parse_equity_quote(
            "GAPUP",
            _quote_payload(close=100, last=101, net_pct=1.0, volume=1_000_000, extended_last=104),
            universes={"custom"},
            sector="Information Technology",
        ),
    ]
    snapshots = [snap for snap in snapshots if snap is not None]
    results = rank_scan_results(
        snapshots,
        settings=settings,
        movers_up=[{"symbol": "XYZ", "changePercent": 12.3}],
        movers_down=[{"symbol": "ABC", "changePercent": -8.1}],
        market_context=[],
        scanned_symbols=3,
    )
    assert [snap.symbol for snap in results.prior_gainers] == ["WIN"]
    assert [snap.symbol for snap in results.prior_losers] == ["LOSE"]
    assert [snap.symbol for snap in results.premarket_gainers] == ["WIN", "GAPUP"]
    assert [snap.symbol for snap in results.premarket_losers] == ["LOSE"]
    assert results.movers_up[0]["symbol"] == "XYZ"


def test_build_report_groups_snapshots_by_sector():
    settings = EquityScanSettings()
    settings.group_by_sector = True
    snapshots = [
        parse_equity_quote(
            "WIN",
            _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000),
            universes={"sp500"},
            sector="Information Technology",
        ),
        parse_equity_quote(
            "LOSE",
            _quote_payload(close=100, last=90, net_pct=-10.0, volume=1_000_000),
            universes={"sp500"},
            sector="Health Care",
        ),
    ]
    snapshots = [snap for snap in snapshots if snap is not None]
    results = rank_scan_results(
        snapshots,
        settings=settings,
        movers_up=[],
        movers_down=[],
        market_context=[],
        scanned_symbols=2,
    )
    messages = build_report(results, settings=settings)
    report = "\n".join(messages)
    assert "_Information Technology_" in report
    assert "_Health Care_" in report


def test_avg_daily_volume_ignores_today_and_compute_rvol():
    import datetime as dt

    today_start_ms = int(
        dt.datetime.combine(dt.date.today(), dt.time.min).timestamp() * 1000
    )
    candles = [
        {"volume": 1_000_000, "datetime": today_start_ms - 259_200_000},
        {"volume": 2_000_000, "datetime": today_start_ms - 172_800_000},
        {"volume": 3_000_000, "datetime": today_start_ms - 86_400_000},
        {"volume": 9_999_999, "datetime": today_start_ms},
    ]
    avg = avg_daily_volume(candles, lookback=3)
    assert avg == 2_000_000.0
    assert compute_rvol(400_000, avg) == 0.2


def test_build_report_splits_long_output():
    settings = EquityScanSettings()
    settings.limits.prior_gainers = 30
    snapshots = []
    for i in range(30):
        snap = parse_equity_quote(
            f"T{i:02d}",
            _quote_payload(close=100, last=110 + i, net_pct=10 + i, volume=1_000_000),
            universes={"sp500"},
        )
        assert snap is not None
        snapshots.append(snap)
    results = rank_scan_results(
        snapshots,
        settings=settings,
        movers_up=[],
        movers_down=[],
        market_context=[],
        scanned_symbols=30,
    )
    messages = build_report(results, settings=settings)
    assert len(messages) >= 1
    assert all(len(message) <= 2000 for message in messages)
    assert "Equity Morning Scan" in messages[0]
