"""iter_chain_options picks the PM-settled contract when a strike lists several."""

from __future__ import annotations

import datetime as dt
from typing import Any

from butterfly_guy.data.chain_utils import iter_chain_options

EXPIRATION = dt.date(2026, 9, 18)


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
