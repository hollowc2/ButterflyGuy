"""Live parsing and DB replay pick the PM-settled contract when a strike lists several."""

from __future__ import annotations

import datetime as dt
from typing import Any

from butterfly_guy.data.chain_utils import iter_chain_options, select_pm_settled_rows
from butterfly_guy.data.db_chain_quotes import rows_to_option_quotes

EXPIRATION = dt.date(2026, 9, 18)
SNAP_1 = dt.datetime(2026, 9, 18, 14, 0, tzinfo=dt.timezone.utc)
SNAP_2 = dt.datetime(2026, 9, 18, 14, 1, tzinfo=dt.timezone.utc)


def _chain(call_options: list[dict[str, Any]]) -> dict[str, Any]:
    return {"callExpDateMap": {"2026-09-18:0": {"6600.0": call_options}}}


def _symbols(chain: dict[str, Any]) -> list[str]:
    return [opt["symbol"] for _, _, opt in iter_chain_options(chain, EXPIRATION)]


def test_single_contract_is_yielded_unchanged() -> None:
    assert _symbols(_chain([{"symbol": "SPX   260918C06600000"}])) == [
        "SPX   260918C06600000"
    ]


def test_spx_and_spxw_at_one_strike_yields_spxw() -> None:
    chain = _chain(
        [{"symbol": "SPX   260918C06600000"}, {"symbol": "SPXW  260918C06600000"}]
    )
    assert _symbols(chain) == ["SPXW  260918C06600000"]


def test_ndx_and_ndxp_at_one_strike_yields_ndxp() -> None:
    chain = _chain(
        [{"symbol": "NDXP  260918C06600000"}, {"symbol": "NDX   260918C06600000"}]
    )
    assert _symbols(chain) == ["NDXP  260918C06600000"]


def test_settlement_type_is_used_when_symbol_is_missing() -> None:
    chain = _chain(
        [
            {"settlementType": "A", "bid": 1.0},
            {"settlementType": "P", "bid": 2.0},
        ]
    )
    opts = [opt for _, _, opt in iter_chain_options(chain, EXPIRATION)]
    assert opts == [{"settlementType": "P", "bid": 2.0}]


def test_duplicates_with_no_pm_settled_contract_are_skipped() -> None:
    chain = _chain(
        [{"symbol": "SPX   260918C06600000"}, {"symbol": "SPX   260918C06600000"}]
    )
    assert _symbols(chain) == []


def test_duplicates_with_two_pm_settled_contracts_are_skipped() -> None:
    chain = _chain(
        [{"symbol": "SPXW  260918C06600000"}, {"symbol": "SPXW  260918C06600000"}]
    )
    assert _symbols(chain) == []


def _row(symbol: str, *, strike: float = 6600.0, option_type: str = "CALL",
         snapshot_time: dt.datetime = SNAP_1, bid: float = 1.0) -> dict[str, Any]:
    return {
        "snapshot_time": snapshot_time,
        "strike": strike,
        "option_type": option_type,
        "symbol": symbol,
        "bid": bid,
        "ask": bid + 0.2,
        "mark": bid + 0.1,
    }


def test_snapshot_rows_keep_only_the_pm_settled_contract_per_strike() -> None:
    rows = [
        _row("SPX   260918C06600000", bid=9.0),
        _row("SPXW  260918C06600000"),
        _row("SPX   260918P06600000", option_type="PUT", bid=9.0),
        _row("SPXW  260918P06600000", option_type="PUT"),
        _row("SPXW  260918C06605000", strike=6605.0),
    ]
    assert [row["symbol"] for row in select_pm_settled_rows(rows)] == [
        "SPXW  260918C06600000",
        "SPXW  260918P06600000",
        "SPXW  260918C06605000",
    ]


def test_snapshot_rows_are_grouped_per_snapshot_time() -> None:
    rows = [
        _row("SPXW  260918C06600000", snapshot_time=SNAP_1),
        _row("SPXW  260918C06600000", snapshot_time=SNAP_2),
    ]
    assert select_pm_settled_rows(rows) == rows


def test_ambiguous_snapshot_rows_are_dropped() -> None:
    rows = [_row("SPX   260918C06600000"), _row("SPX   260918C06600000")]
    assert select_pm_settled_rows(rows) == []


def test_custom_key_fields_group_rows() -> None:
    rows = [
        {**_row("SPX   260918C06600000"), "label": "entry"},
        {**_row("SPXW  260918C06600000"), "label": "entry"},
        {**_row("SPX   260918C06600000"), "label": "exit"},
    ]
    selected = select_pm_settled_rows(rows, ("label", "strike", "option_type"))
    assert [(row["label"], row["symbol"]) for row in selected] == [
        ("entry", "SPXW  260918C06600000"),
        ("exit", "SPX   260918C06600000"),
    ]


def test_rows_to_option_quotes_uses_the_pm_settled_contract() -> None:
    rows = [
        {k: v for k, v in _row("SPX   260918C06600000", bid=9.0).items() if k != "snapshot_time"},
        {k: v for k, v in _row("SPXW  260918C06600000").items() if k != "snapshot_time"},
    ]
    quotes = rows_to_option_quotes(rows, underlying="SPX", expiration=EXPIRATION)
    assert [(q.symbol, q.bid) for q in quotes] == [("SPXW  260918C06600000", 1.0)]
