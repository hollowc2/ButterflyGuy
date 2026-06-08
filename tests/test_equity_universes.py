"""Tests for equity universe seed parsing and liquidity gates."""

from __future__ import annotations

import json

from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.universes import (
    build_liquid_meta,
    extract_quote_price,
    filter_symbols_by_avg_volume,
    filter_symbols_by_price,
    load_sector_map,
    parse_nasdaq_listed_text,
    parse_nyse_listed_text,
)

NASDAQ_SAMPLE = """\
Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
AAPL|Apple Inc. Common Stock|Q|N|N|100|N|N
QQQ|Invesco QQQ Trust, Series 1|G|N|N|100|Y|N
ZVZZT|Test Symbol|G|Y|N|100|N|N
BRK.A|Berkshire Hathaway Inc. Class A|Q|N|N|40|N|N
File Creation Time: 060820261200|||||||
"""

OTHERLISTED_SAMPLE = """\
ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
AAPL|Apple Inc. Common Stock|N|AAPL|N|100|N|AAPL
AAA|Alternative Access ETF|P|AAA|Y|100|N|AAA
ACCS|ACCESS Newswire Inc. Common Stock|A|ACCS|N|100|N|ACCS
ABR$F|Arbor Realty Preferred|N|ABRpF|N|100|N|ABR-F
ACHR.W|Archer Aviation Warrants|N|ACHR.WS|N|100|N|ACHR+
File Creation Time: 060820261200|||||||
"""


def test_parse_nasdaq_listed_text_filters_etfs_tests_and_preferreds():
    symbols = parse_nasdaq_listed_text(NASDAQ_SAMPLE)
    assert symbols == ["AAPL", "BRK.A"]


def test_parse_nyse_listed_text_keeps_nyse_common_stocks_only():
    symbols = parse_nyse_listed_text(OTHERLISTED_SAMPLE)
    assert symbols == ["AAPL"]


def test_extract_quote_price_prefers_extended_price():
    payload = {
        "quote": {"lastPrice": 8.0, "closePrice": 7.5},
        "extended": {"lastPrice": 9.0},
    }
    assert extract_quote_price(payload) == 9.0


def test_filter_symbols_by_price():
    quotes = {
        "AAA": {"quote": {"lastPrice": 4.99}},
        "BBB": {"quote": {"lastPrice": 5.0}},
        "CCC": {"quote": {"lastPrice": 12.5}},
    }
    passed, prices = filter_symbols_by_price(
        ["AAA", "BBB", "CCC", "MISSING"],
        quotes,
        min_price=5.0,
    )
    assert passed == ["BBB", "CCC"]
    assert prices == {"BBB": 5.0, "CCC": 12.5}


def test_filter_symbols_by_avg_volume():
    passed = filter_symbols_by_avg_volume(
        ["AAA", "BBB", "CCC"],
        {"AAA": 499_999.0, "BBB": 500_000.0, "CCC": 1_000_000.0},
        min_avg_volume=500_000.0,
    )
    assert passed == ["BBB", "CCC"]


def test_build_liquid_meta():
    meta = build_liquid_meta(
        ["AAA"],
        prices={"AAA": 10.0},
        avg_volumes={"AAA": 750_000.0},
        exchange_map={"AAA": "NASDAQ"},
    )
    assert meta == {
        "AAA": {
            "price": 10.0,
            "avg_volume_20d": 750_000.0,
            "exchange": "NASDAQ",
        }
    }


def test_equity_scan_settings_accepts_liquid_universe():
    settings = EquityScanSettings(universes=["sp500", "nq100", "liquid", "custom"])
    assert "liquid" in settings.universes


def test_load_sector_map_uses_liquid_meta_exchange_fallback(tmp_path):
    universe_dir = tmp_path / "universes"
    universe_dir.mkdir()
    (universe_dir / "sectors.json").write_text(json.dumps({"AAPL": "Information Technology"}))
    (universe_dir / "liquid_meta.json").write_text(
        json.dumps({"MARA": {"exchange": "NASDAQ", "price": 12.0}})
    )
    sectors = load_sector_map(universe_dir)
    assert sectors["AAPL"] == "Information Technology"
    assert sectors["MARA"] == "NASDAQ"
