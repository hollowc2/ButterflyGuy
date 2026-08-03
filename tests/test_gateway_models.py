from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from butterfly_guy.schwab_gateway.upstream import normalize_schwab_quote


def test_quote_normalization_preserves_missing_fields_and_staleness() -> None:
    received_at = dt.datetime(2026, 8, 3, 21, 0, tzinfo=dt.timezone.utc)
    quote = normalize_schwab_quote(
        "AAPL",
        {
            "quote": {
                "lastPrice": 201.5,
                "tradeTime": int((received_at - dt.timedelta(seconds=20)).timestamp() * 1000),
            }
        },
        received_at=received_at,
        stale_after_seconds=15,
    )

    assert quote.bid is None
    assert quote.ask is None
    assert quote.last == 201.5
    assert quote.age_seconds == 20
    assert quote.stale is True
    assert quote.data_quality_flags == ("missing_bid", "missing_ask", "stale")


def test_quote_normalization_uses_fresher_extended_session() -> None:
    received_at = dt.datetime(2026, 8, 3, 21, 0, tzinfo=dt.timezone.utc)
    quote = normalize_schwab_quote(
        "AAPL",
        {
            "quote": {
                "lastPrice": 200,
                "tradeTime": int((received_at - dt.timedelta(minutes=5)).timestamp() * 1000),
            },
            "extended": {
                "bidPrice": 201,
                "askPrice": 201.2,
                "lastPrice": 201.1,
                "tradeTime": int((received_at - dt.timedelta(seconds=2)).timestamp() * 1000),
            },
        },
        received_at=received_at,
        stale_after_seconds=15,
    )

    assert quote.session == "extended"
    assert quote.bid == 201
    assert quote.ask == 201.2
    assert quote.stale is False
    assert quote.data_quality_flags == ()


def test_quote_contract_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        normalize_schwab_quote(
            "AAPL",
            {},
            received_at=dt.datetime(2026, 8, 3, 21, 0),
            stale_after_seconds=15,
        )
