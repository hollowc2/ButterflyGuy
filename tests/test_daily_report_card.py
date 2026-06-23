"""Tests for daily report card parsing and formatting."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from butterfly_guy.reports.daily_report_card import (
    build_daily_report_card,
    parse_account_balances,
    parse_trade_transactions,
    rank_trades,
)
from butterfly_guy.reports.daily_report_card_config import DailyReportCardSettings
from butterfly_guy.reports.daily_report_card_format import build_report_messages
from butterfly_guy.reports.equity_trade_chart import (
    _format_trade_stats,
    _price_limits,
    _slice_series,
    build_equity_trade_chart_png,
    candles_to_series,
    chartable_equity_trades,
    two_minute_candles,
)

EASTERN = ZoneInfo("America/New_York")

ACCOUNT_FIXTURE = {
    "securitiesAccount": {
        "type": "MARGIN",
        "initialBalances": {"liquidationValue": 50000.0},
        "currentBalances": {
            "liquidationValue": 50550.0,
            "buyingPower": 1200.0,
            "availableFunds": 1200.0,
            "maintenanceRequirement": 8000.0,
            "dayTradingBuyingPower": 24000.0,
        },
        "positions": [
            {
                "instrument": {
                    "symbol": "SPXW  250606C06010000",
                    "assetType": "OPTION",
                    "putCall": "CALL",
                    "strikePrice": 6010.0,
                    "expirationDate": "2026-06-06",
                    "underlyingSymbol": "SPX",
                },
                "longQuantity": 1,
                "shortQuantity": 0,
                "marketValue": 150.0,
                "longOpenProfitLoss": -25.0,
            }
        ],
    }
}

TRANSACTION_FIXTURE = [
    {
        "activityId": 1001,
        "type": "TRADE",
        "time": "2026-06-06T10:15:30-0400",
        "netAmount": 310.0,
        "orderId": 9001,
        "transferItems": [
            {
                "instrument": {
                    "symbol": "SPXW  250606C06010000",
                    "assetType": "OPTION",
                    "putCall": "CALL",
                    "strikePrice": 6010.0,
                    "expirationDate": "2026-06-06",
                },
                "amount": 1,
                "cost": 125.0,
            }
        ],
    },
    {
        "activityId": 1002,
        "type": "TRADE",
        "time": "2026-06-06T11:00:00-0400",
        "netAmount": 95.0,
        "orderId": 9002,
        "transferItems": [
            {
                "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
                "amount": 10,
                "cost": 1500.0,
            }
        ],
    },
    {
        "activityId": 1003,
        "type": "TRADE",
        "time": "2026-06-06T14:30:00-0400",
        "netAmount": -120.0,
        "orderId": 9003,
        "transferItems": [
            {
                "instrument": {
                    "symbol": "TSLA  250606P00250000",
                    "assetType": "OPTION",
                    "putCall": "PUT",
                    "strikePrice": 250.0,
                    "expirationDate": "2026-06-06",
                },
                "amount": 1,
                "cost": 80.0,
            }
        ],
    },
    {
        "activityId": 1004,
        "type": "ACH_RECEIPT",
        "time": "2026-06-06T08:00:00-0400",
        "netAmount": 265.0,
        "description": "ACH DEPOSIT",
    },
]

ORDERS_FIXTURE = [
    {"orderId": 8001, "status": "REJECTED"},
    {"orderId": 8002, "status": "FILLED"},
]


def test_parse_account_balances():
    balances = parse_account_balances(ACCOUNT_FIXTURE)
    assert balances.starting_liquidation == 50000.0
    assert balances.ending_liquidation == 50550.0
    assert balances.net_change == 550.0
    assert balances.net_change_pct == pytest.approx(1.1)
    assert balances.buying_power == 1200.0
    assert balances.account_type == "MARGIN"


def test_parse_trade_transactions_groups_by_order():
    """Without positionEffect, falls back to per-transaction P&L (e.g. options)."""
    trades = parse_trade_transactions(TRANSACTION_FIXTURE)
    assert len(trades) == 3
    pnls = sorted(t.pnl for t in trades)
    assert pnls == [-120.0, 95.0, 310.0]


def test_parse_trade_transactions_matches_round_trips():
    transactions = [
        {
            "activityId": 1,
            "type": "TRADE",
            "time": "2026-06-09T19:50:30-0400",
            "netAmount": -72.62,
            "orderId": 1,
            "transferItems": [
                {
                    "instrument": {"symbol": "TQQQ", "assetType": "COLLECTIVE_INVESTMENT"},
                    "amount": 1.0,
                    "positionEffect": "OPENING",
                }
            ],
        },
        {
            "activityId": 2,
            "type": "TRADE",
            "time": "2026-06-09T19:59:44-0400",
            "netAmount": 73.69,
            "orderId": 2,
            "transferItems": [
                {
                    "instrument": {"symbol": "TQQQ", "assetType": "COLLECTIVE_INVESTMENT"},
                    "amount": -1.0,
                    "positionEffect": "CLOSING",
                }
            ],
        },
    ]
    trades = parse_trade_transactions(transactions)
    assert len(trades) == 1
    assert trades[0].label == "TQQQ"
    assert trades[0].pnl == pytest.approx(1.07)
    assert trades[0].symbol == "TQQQ"
    assert trades[0].asset_type == "COLLECTIVE_INVESTMENT"
    assert trades[0].entry_time == dt.datetime(2026, 6, 9, 19, 50, 30, tzinfo=EASTERN)
    assert trades[0].exit_time == dt.datetime(2026, 6, 9, 19, 59, 44, tzinfo=EASTERN)


def test_chartable_equity_trades_skips_options():
    equity, option = parse_trade_transactions(
        [
            {
                "type": "TRADE",
                "time": "2026-06-09T09:50:30-0400",
                "netAmount": -72.62,
                "transferItems": [
                    {
                        "instrument": {
                            "symbol": "TQQQ",
                            "assetType": "COLLECTIVE_INVESTMENT",
                        },
                        "amount": 1.0,
                        "positionEffect": "OPENING",
                    }
                ],
            },
            {
                "type": "TRADE",
                "time": "2026-06-09T09:59:44-0400",
                "netAmount": 73.69,
                "transferItems": [
                    {
                        "instrument": {
                            "symbol": "TQQQ",
                            "assetType": "COLLECTIVE_INVESTMENT",
                        },
                        "amount": -1.0,
                        "positionEffect": "CLOSING",
                    }
                ],
            },
            {
                "type": "TRADE",
                "time": "2026-06-09T10:00:00-0400",
                "netAmount": 10.0,
                "transferItems": [
                    {
                        "instrument": {
                            "symbol": "SPXW  260609C06010000",
                            "assetType": "OPTION",
                        },
                        "amount": -1.0,
                        "positionEffect": "CLOSING",
                    }
                ],
            },
        ]
    )
    assert chartable_equity_trades([equity, option]) == [equity]


def test_build_equity_trade_chart_png_returns_png_bytes():
    trade = parse_trade_transactions(
        [
            {
                "type": "TRADE",
                "time": "2026-06-09T09:31:00-0400",
                "netAmount": -100.0,
                "transferItems": [
                    {
                        "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
                        "amount": 1.0,
                        "positionEffect": "OPENING",
                    }
                ],
            },
            {
                "type": "TRADE",
                "time": "2026-06-09T09:33:00-0400",
                "netAmount": 101.0,
                "transferItems": [
                    {
                        "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
                        "amount": -1.0,
                        "positionEffect": "CLOSING",
                    }
                ],
            },
        ]
    )[0]
    candles = []
    start = dt.datetime(2026, 6, 9, 7, 30, tzinfo=EASTERN)
    for i in range(5):
        ts = start + dt.timedelta(minutes=i)
        candles.append(
            {
                "datetime": int(ts.timestamp() * 1000),
                "open": 200.0 + i,
                "high": 201.0 + i,
                "low": 199.0 + i,
                "close": 200.5 + i,
                "volume": 1000 + i,
            }
        )

    png = build_equity_trade_chart_png(trade, candles)
    assert png is not None
    assert png.startswith(b"\x89PNG")


def test_equity_chart_window_keeps_6am_premarket_and_regular_session():
    candles = []
    for ts in (
        dt.datetime(2026, 6, 9, 5, 59, tzinfo=EASTERN),
        dt.datetime(2026, 6, 9, 6, 0, tzinfo=EASTERN),
        dt.datetime(2026, 6, 9, 9, 30, tzinfo=EASTERN),
        dt.datetime(2026, 6, 9, 16, 0, tzinfo=EASTERN),
        dt.datetime(2026, 6, 9, 16, 1, tzinfo=EASTERN),
    ):
        candles.append(
            {
                "datetime": int(ts.timestamp() * 1000),
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "volume": 100,
            }
        )

    series = candles_to_series(candles, dt.date(2026, 6, 9))
    assert [item["time"].time() for item in series] == [
        dt.time(6, 0),
        dt.time(9, 30),
        dt.time(16, 0),
    ]


def test_equity_chart_window_rejects_prior_day_same_times():
    candles = []
    for ts in (
        dt.datetime(2026, 6, 8, 6, 0, tzinfo=EASTERN),
        dt.datetime(2026, 6, 9, 6, 0, tzinfo=EASTERN),
    ):
        candles.append(
            {
                "datetime": int(ts.timestamp() * 1000),
                "open": 10,
                "high": 11,
                "low": 9,
                "close": 10.5,
                "volume": 100,
            }
        )

    series = candles_to_series(candles, dt.date(2026, 6, 9))
    assert [item["time"].date() for item in series] == [dt.date(2026, 6, 9)]


def test_equity_chart_aggregates_to_two_minute_candles():
    candles = []
    for i, close in enumerate((10.5, 11.5, 12.5)):
        ts = dt.datetime(2026, 6, 9, 9, 30 + i, tzinfo=EASTERN)
        candles.append(
            {
                "datetime": int(ts.timestamp() * 1000),
                "open": 10 + i,
                "high": 11 + i,
                "low": 9 + i,
                "close": close,
                "volume": 100 + i,
            }
        )

    series = two_minute_candles(candles_to_series(candles, dt.date(2026, 6, 9)))
    assert [item["time"].time() for item in series] == [dt.time(9, 30), dt.time(9, 32)]
    assert series[0]["open"] == 10
    assert series[0]["high"] == 12
    assert series[0]["low"] == 9
    assert series[0]["close"] == 11.5
    assert series[0]["volume"] == 201


def test_equity_chart_zoom_slice_is_independent():
    base = dt.datetime(2026, 6, 9, 9, 30, tzinfo=EASTERN)
    series = [
        {"time": base, "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5, "volume": 100},
        {
            "time": base + dt.timedelta(minutes=30),
            "open": 110.0,
            "high": 111.0,
            "low": 109.5,
            "close": 110.5,
            "volume": 100,
        },
        {
            "time": base + dt.timedelta(minutes=90),
            "open": 140.0,
            "high": 141.0,
            "low": 139.5,
            "close": 140.5,
            "volume": 100,
        },
    ]

    zoom = _slice_series(series, base + dt.timedelta(minutes=20), base + dt.timedelta(minutes=40))
    assert [candle["time"] for candle in zoom] == [base + dt.timedelta(minutes=30)]
    assert _price_limits(series) != _price_limits(zoom)


def test_equity_chart_stats_text_includes_key_fields():
    trade = parse_trade_transactions(
        [
            {
                "type": "TRADE",
                "time": "2026-06-09T09:31:00-0400",
                "netAmount": -100.0,
                "transferItems": [
                    {
                        "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
                        "amount": 1.0,
                        "positionEffect": "OPENING",
                    }
                ],
            },
            {
                "type": "TRADE",
                "time": "2026-06-09T09:33:00-0400",
                "netAmount": 101.0,
                "transferItems": [
                    {
                        "instrument": {"symbol": "AAPL", "assetType": "EQUITY"},
                        "amount": -1.0,
                        "positionEffect": "CLOSING",
                    }
                ],
            },
        ]
    )[0]

    lines = _format_trade_stats(trade, entry_price=100.25, exit_price=101.75)
    assert any(line.startswith("Symbol: AAPL") for line in lines)
    assert any(line.startswith("Entry: 09:31:00 ET @ $100.25") for line in lines)
    assert any(line.startswith("Exit: 09:33:00 ET @ $101.75") for line in lines)
    assert any(line.startswith("Size: 1") for line in lines)
    assert any(line.startswith("P&L: +$1.00") for line in lines)


def test_rank_trades():
    trades = parse_trade_transactions(TRANSACTION_FIXTURE)
    winners, losers = rank_trades(trades, top_n=2)
    assert len(winners) == 2
    assert winners[0].pnl == 310.0
    assert len(losers) == 1
    assert losers[0].pnl == -120.0


def test_build_daily_report_card_detects_problems():
    settings = DailyReportCardSettings()
    report_date = dt.date(2026, 6, 6)
    card = build_daily_report_card(
        report_date=report_date,
        generated_at=dt.datetime(2026, 6, 6, 16, 30, tzinfo=EASTERN),
        account_data=ACCOUNT_FIXTURE,
        transactions=TRANSACTION_FIXTURE,
        orders=ORDERS_FIXTURE,
        settings=settings,
    )
    assert card.activity.trade_count == 3
    assert card.activity.winners == 2
    assert card.activity.losers == 1
    assert card.rejected_order_count == 1
    assert any("0-DTE" in p for p in card.problems)
    assert any("REJECTED" in p for p in card.problems)


def test_report_separates_trading_pnl_from_transfers():
    settings = DailyReportCardSettings()
    report_date = dt.date(2026, 6, 9)
    account = {
        "securitiesAccount": {
            "type": "MARGIN",
            "initialBalances": {"liquidationValue": 100.0},
            "currentBalances": {
                "liquidationValue": 2507.37,
                "buyingPower": 1200.0,
                "availableFunds": 1200.0,
            },
            "positions": [],
        }
    }
    transactions = [
        {
            "activityId": 1,
            "type": "TRADE",
            "netAmount": 7.37,
            "orderId": 1,
            "transferItems": [
                {"instrument": {"symbol": "TQQQ", "assetType": "COLLECTIVE_INVESTMENT"}},
            ],
        },
        {
            "activityId": 2,
            "type": "JOURNAL",
            "netAmount": 2400.0,
            "description": "JOURNAL FRM 77549402",
        },
    ]
    card = build_daily_report_card(
        report_date=report_date,
        generated_at=dt.datetime(2026, 6, 9, 16, 30, tzinfo=EASTERN),
        account_data=account,
        transactions=transactions,
        orders=[],
        settings=settings,
    )
    messages = build_report_messages(card)
    text = messages[0]
    assert "Start: $2,500.00" in text
    assert "End: $2,507.37" in text
    assert "+$7.37" in text
    assert "+$2,400.00" in text
    assert "Schwab open: $100.00" in text
    assert "$2,407.37" not in text  # raw balance jump not shown as P&L
    assert not any("Journal" in p for p in card.problems)


def test_build_report_messages_format():
    settings = DailyReportCardSettings()
    report_date = dt.date(2026, 6, 6)
    card = build_daily_report_card(
        report_date=report_date,
        generated_at=dt.datetime(2026, 6, 6, 16, 30, tzinfo=EASTERN),
        account_data=ACCOUNT_FIXTURE,
        transactions=TRANSACTION_FIXTURE,
        orders=ORDERS_FIXTURE,
        settings=settings,
    )
    messages = build_report_messages(card)
    assert len(messages) >= 1
    text = messages[0]
    assert "Daily Report Card" in text
    assert "$50,000.00" in text
    assert "$50,550.00" in text
    assert "Big Winners" in text
    assert "Big Losers" in text
    assert "Watchlist" in text
    assert "AAPL" in text or "SPX" in text
