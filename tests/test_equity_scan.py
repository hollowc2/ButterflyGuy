"""Tests for equity morning scan logic."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.report import archive_report, build_report
from butterfly_guy.equity_scan.scanner import (
    build_snapshots,
    filter_movers,
    parse_equity_quote,
    rank_scan_results,
)
from butterfly_guy.equity_scan.universes import build_symbol_map
from butterfly_guy.equity_scan.volume import avg_daily_volume, compute_rvol, symbols_needing_rvol_fetch


def _premarket_et() -> dt.datetime:
    return dt.datetime(2026, 6, 8, 8, 0, tzinfo=EASTERN)


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
        in_premarket=True,
    )
    assert snap is not None
    assert snap.price == 105.0
    assert snap.prior_day_pct == -2.0
    assert snap.session_gap_pct == 5.0
    assert snap.premarket_volume == 250_000
    assert snap.rvol == 0.25
    assert snap.sector == "Information Technology"


def test_parse_equity_quote_prefers_fresher_quote_during_premarket():
    payload = {
        "quote": {
            "closePrice": 100.0,
            "lastPrice": 101.0,
            "netPercentChange": 1.0,
            "totalVolume": 1_000_000,
            "tradeTime": 2_000,
        },
        "extended": {
            "lastPrice": 104.0,
            "totalVolume": 50_000,
            "tradeTime": 3_000,
        },
    }
    snap = parse_equity_quote(
        "GAP",
        payload,
        universes={"sp500"},
        in_premarket=True,
    )
    assert snap is not None
    assert snap.price == 104.0
    assert snap.session_gap_pct == 4.0


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


def test_build_snapshots_skips_rvol_filter_without_premarket_volume():
    settings = EquityScanSettings()
    settings.filters.min_rvol = 0.10
    symbol_map = build_symbol_map({"sp500": ["NOWVOL"]})
    quotes = {
        "NOWVOL": _quote_payload(
            close=100,
            last=112,
            net_pct=12.0,
            volume=1_000_000,
            extended_volume=0,
        ),
    }
    avg_volumes = {"NOWVOL": 1_000_000.0}
    snapshots = build_snapshots(
        quotes,
        symbol_map,
        settings,
        avg_volumes=avg_volumes,
    )
    assert [snap.symbol for snap in snapshots] == ["NOWVOL"]


def test_rank_scan_results_returns_expected_sections():
    settings = EquityScanSettings()
    snapshots = [
        parse_equity_quote(
            "WIN",
            _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000, extended_last=112),
            universes={"sp500"},
            sector="Information Technology",
            in_premarket=True,
        ),
        parse_equity_quote(
            "LOSE",
            _quote_payload(close=100, last=90, net_pct=-10.0, volume=1_000_000, extended_last=88),
            universes={"nq100"},
            sector="Health Care",
            in_premarket=True,
        ),
        parse_equity_quote(
            "GAPUP",
            _quote_payload(close=100, last=101, net_pct=1.0, volume=1_000_000, extended_last=104),
            universes={"custom"},
            sector="Information Technology",
            in_premarket=True,
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
        generated_at=_premarket_et(),
    )
    assert [snap.symbol for snap in results.prior_gainers] == ["WIN"]
    assert [snap.symbol for snap in results.prior_losers] == ["LOSE"]
    assert [snap.symbol for snap in results.premarket_gainers] == ["WIN", "GAPUP"]
    assert [snap.symbol for snap in results.premarket_losers] == ["LOSE"]
    assert results.movers_up == []
    assert results.movers_down == []


def test_rank_scan_results_dedupes_premarket_when_gap_matches_prior():
    settings = EquityScanSettings()
    settings.dedupe_premarket_with_prior = True
    settings.gap_overlap_tolerance_pct = 0.5
    snap = parse_equity_quote(
        "WIN",
        _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000, extended_last=110.2),
        universes={"sp500"},
    )
    assert snap is not None
    results = rank_scan_results(
        [snap],
        settings=settings,
        movers_up=[],
        movers_down=[],
        market_context=[],
        scanned_symbols=1,
        generated_at=_premarket_et(),
    )
    assert results.prior_gainers[0].symbol == "WIN"
    assert results.premarket_gainers == []


def test_filter_movers_drops_stale_identical_lists():
    up, down = filter_movers(
        [
            {"symbol": "NVDA", "changePercent": 0.0},
            {"symbol": "INTC", "changePercent": 0.1},
        ],
        [
            {"symbol": "NVDA", "changePercent": 0.0},
            {"symbol": "INTC", "changePercent": 0.1},
        ],
        min_abs_pct=1.0,
        limit=10,
    )
    assert up == []
    assert down == []


def test_build_snapshots_requires_index_membership_when_enabled():
    settings = EquityScanSettings()
    settings.filters.require_index_membership = True
    settings.filters.min_rvol = 0.0
    symbol_map = build_symbol_map({"custom": ["ONLY"], "sp500": ["INDEX"]})
    quotes = {
        "ONLY": _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000),
        "INDEX": _quote_payload(close=100, last=110, net_pct=10.0, volume=1_000_000),
    }
    snapshots = build_snapshots(quotes, symbol_map, settings)
    assert [snap.symbol for snap in snapshots] == ["INDEX"]


def test_archive_report_writes_dated_markdown(tmp_path):
    generated_at = _premarket_et()
    path = archive_report(
        ["line one", "line two"],
        report_dir=str(tmp_path),
        generated_at=generated_at,
    )
    assert path.name == "2026-06-08.md"
    assert "line one" in path.read_text()


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
        generated_at=_premarket_et(),
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


def test_symbols_needing_rvol_fetch_only_includes_premarket_volume():
    quotes = {
        "GAP": _quote_payload(
            close=100, last=105, net_pct=5.0, volume=1_000_000, extended_volume=50_000
        ),
        "FLAT": _quote_payload(close=100, last=101, net_pct=1.0, volume=1_000_000),
        "ZERO": _quote_payload(
            close=100, last=105, net_pct=5.0, volume=1_000_000, extended_volume=0
        ),
    }
    assert symbols_needing_rvol_fetch(quotes) == ["GAP"]


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
        generated_at=_premarket_et(),
    )
    messages = build_report(results, settings=settings)
    assert len(messages) >= 1
    assert all(len(message) <= 2000 for message in messages)
    assert "Equity Morning Scan" in messages[0]
