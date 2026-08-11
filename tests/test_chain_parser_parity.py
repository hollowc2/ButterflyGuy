"""Differential tests pinning the three Schwab option-chain parsers against each other.

Three functions independently walk the same ``callExpDateMap``/``putExpDateMap`` shape
and answer different questions about it:

- ``data.chain_utils.iter_chain_options`` yields one contract per strike, for trading;
- ``data.collector.OptionChainCollector._parse_chain_response`` emits every contract as
  a database row;
- ``gateway_client.chain_metadata.extract_chain_metadata`` derives bounded counts for
  the gateway's ``/v1/chain`` surface and the shadow comparator.

The live parsers are read-only here. These tests assert the *relationship* between the
three so the trio cannot drift apart silently, and deliberately record the one place
where the semantics genuinely differ rather than papering over it.

A second divergence used to be pinned here: a payload with neither expiration map raised
``ValueError`` from ``extract_chain_metadata`` while both live parsers tolerated it as a
zero-result shape. That divergence was removed (not papered over) by relaxing
``extract_chain_metadata`` to agree with the live parsers on that shape, because the
raise had a real production cost — the gateway's ``/v1/chain`` upstream turned it into a
502 and the shadow comparator logged a false "parsing" discrepancy for degenerate-but-
legitimate responses (e.g. after-hours or halted-symbol chains) that the collector
already handles as zero rows. See ``test_neither_expiration_map_present_is_tolerated_by_all_three``
below, which now asserts agreement instead of divergence.

These are **synthetic fixtures, not golden recorded inputs**. No raw Schwab
``callExpDateMap`` payload exists anywhere in this repository outside test files —
``data/chains/`` holds already-parsed rows — and one cannot be captured offline. The
requirement at ``docs/architecture/schwab-gateway-migration.md`` line 199, that golden
recorded inputs precede consolidating the duplicated parsers, therefore remains
unsatisfied. These tests pin current behaviour; they do not license consolidation.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import MagicMock

import pytest
from schwab_gateway_sdk.chain_metadata import extract_chain_metadata

from butterfly_guy.core.config import AppConfig
from butterfly_guy.data.chain_utils import iter_chain_options
from butterfly_guy.data.collector import OptionChainCollector

EXPIRATION = dt.date(2026, 3, 10)
OTHER_EXPIRATION = dt.date(2026, 3, 11)
SNAPSHOT_TIME = dt.datetime(2026, 3, 10, 17, 0, tzinfo=dt.timezone.utc)
SPOT = 5500.0


def _contract(symbol: str) -> dict[str, Any]:
    return {"symbol": symbol, "bid": 1.5, "ask": 1.7, "mark": 1.6}


# --- Shared synthetic fixtures -------------------------------------------------------

# Two contracts at one strike, which the row parser expands and the trading parser
# collapses to the first entry.
MULTI_CONTRACT_AT_ONE_STRIKE: dict[str, Any] = {
    "callExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("C5500-a"), _contract("C5500-b")],
            "5510.0": [_contract("C5510")],
        }
    },
    "putExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("P5500")],
        }
    },
}

# The defect fixture: 5520.0 exists as a key but carries no contract.
STRIKE_WITH_EMPTY_OPTION_LIST: dict[str, Any] = {
    "callExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("C5500")],
            "5520.0": [],
        }
    },
    "putExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("P5500")],
            "5530.0": [],
        }
    },
}

# One map holding several expirations; only the requested one may be counted.
SEVERAL_EXPIRATIONS: dict[str, Any] = {
    "callExpDateMap": {
        "2026-03-10:0": {"5500.0": [_contract("C0310")]},
        "2026-03-11:1": {"5500.0": [_contract("C0311-a")], "5510.0": [_contract("C0311-b")]},
    },
    "putExpDateMap": {
        "2026-03-10:0": {"5500.0": [_contract("P0310")]},
        "2026-03-11:1": {"5500.0": [_contract("P0311")]},
    },
}

# A strike key that is not a number. The two live parsers raise; the metadata skips.
NON_NUMERIC_STRIKE_KEY: dict[str, Any] = {
    "callExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("C5500")],
            "NOT_A_STRIKE": [_contract("C-bogus")],
        }
    },
    "putExpDateMap": {},
}

# Both maps present, both empty.
EMPTY_MAPS: dict[str, Any] = {"callExpDateMap": {}, "putExpDateMap": {}}

# Calls present, puts absent entirely.
CALLS_ONLY: dict[str, Any] = {
    "callExpDateMap": {
        "2026-03-10:0": {
            "5500.0": [_contract("C5500")],
            "5510.0": [_contract("C5510")],
        }
    }
}

TOTAL_FIXTURES = [
    pytest.param(MULTI_CONTRACT_AT_ONE_STRIKE, id="multi_contract_at_one_strike"),
    pytest.param(STRIKE_WITH_EMPTY_OPTION_LIST, id="strike_with_empty_option_list"),
    pytest.param(SEVERAL_EXPIRATIONS, id="several_expirations"),
    pytest.param(EMPTY_MAPS, id="empty_maps"),
    pytest.param(CALLS_ONLY, id="calls_only"),
]


def _parse_rows(payload: dict[str, Any], expiration: dt.date) -> list[dict[str, Any]]:
    """Run the live collector row parser without touching the database or Schwab."""
    collector = OptionChainCollector(
        config=AppConfig(),
        schwab=MagicMock(),
        chain_queries=MagicMock(),
        spot_queries=MagicMock(),
    )
    return collector._parse_chain_response(payload, SNAPSHOT_TIME, expiration, SPOT)


# --- The pinned relationships --------------------------------------------------------


@pytest.mark.parametrize("payload", TOTAL_FIXTURES)
def test_contract_counts_equal_the_rows_the_collector_would_write(
    payload: dict[str, Any],
) -> None:
    """call + put contract counts equal the row count the collector writes."""
    fields = extract_chain_metadata(payload, EXPIRATION)
    rows = _parse_rows(payload, EXPIRATION)

    assert fields.call_contract_count + fields.put_contract_count == len(rows)
    assert fields.call_contract_count == sum(r["option_type"] == "CALL" for r in rows)
    assert fields.put_contract_count == sum(r["option_type"] == "PUT" for r in rows)


@pytest.mark.parametrize("payload", TOTAL_FIXTURES)
def test_strike_count_equals_the_distinct_strikes_the_trading_parser_yields(
    payload: dict[str, Any],
) -> None:
    """strike_count equals the distinct strikes iter_chain_options yields, both ways."""
    fields = extract_chain_metadata(payload, EXPIRATION)
    yielded = {strike for strike, _, _ in iter_chain_options(payload, EXPIRATION)}

    assert fields.strike_count == len(yielded)


@pytest.mark.parametrize("payload", TOTAL_FIXTURES)
def test_strike_count_equals_the_distinct_strikes_the_collector_writes(
    payload: dict[str, Any],
) -> None:
    """The same strike set is what the collector's rows cover."""
    fields = extract_chain_metadata(payload, EXPIRATION)
    rows = _parse_rows(payload, EXPIRATION)

    assert fields.strike_count == len({row["strike"] for row in rows})


def test_a_strike_with_an_empty_option_list_is_excluded_by_all_three() -> None:
    """The regression case: an empty option list must not inflate strike_count.

    Before the fix, ``strike_count`` was 3 here (5500/5520/5530) while the contract
    counts were 2, so the two fields disagreed about whether 5520 and 5530 existed.
    """
    fields = extract_chain_metadata(STRIKE_WITH_EMPTY_OPTION_LIST, EXPIRATION)

    assert fields.call_contract_count == 1
    assert fields.put_contract_count == 1
    assert fields.strike_count == 1

    yielded = {
        strike for strike, _, _ in iter_chain_options(STRIKE_WITH_EMPTY_OPTION_LIST, EXPIRATION)
    }
    assert yielded == {5500.0}
    assert {row["strike"] for row in _parse_rows(STRIKE_WITH_EMPTY_OPTION_LIST, EXPIRATION)} == {
        5500.0
    }


def test_multiple_contracts_at_one_strike_expand_for_rows_but_not_for_strikes() -> None:
    """The row parser expands duplicates; the trading parser takes only options[0]."""
    fields = extract_chain_metadata(MULTI_CONTRACT_AT_ONE_STRIKE, EXPIRATION)
    rows = _parse_rows(MULTI_CONTRACT_AT_ONE_STRIKE, EXPIRATION)

    assert fields.call_contract_count == 3
    assert fields.put_contract_count == 1
    assert fields.strike_count == 2
    assert len(rows) == 4

    calls = [opt for _, option_type, opt in iter_chain_options(
        MULTI_CONTRACT_AT_ONE_STRIKE, EXPIRATION, direction="CALL"
    )]
    # Only the first contract at 5500 is tradeable through iter_chain_options.
    assert [opt["symbol"] for opt in calls] == ["C5500-a", "C5510"]


@pytest.mark.parametrize("expiration", [EXPIRATION, OTHER_EXPIRATION])
def test_all_three_agree_on_which_expiration_matches(expiration: dt.date) -> None:
    """When one map holds several expirations, all three select the same one."""
    fields = extract_chain_metadata(SEVERAL_EXPIRATIONS, expiration)
    rows = _parse_rows(SEVERAL_EXPIRATIONS, expiration)
    yielded = {strike for strike, _, _ in iter_chain_options(SEVERAL_EXPIRATIONS, expiration)}

    assert fields.call_contract_count + fields.put_contract_count == len(rows)
    assert fields.strike_count == len(yielded)
    assert all(row["expiration"] == expiration for row in rows)

    if expiration == EXPIRATION:
        assert (fields.call_contract_count, fields.put_contract_count) == (1, 1)
        assert yielded == {5500.0}
    else:
        assert (fields.call_contract_count, fields.put_contract_count) == (2, 1)
        assert yielded == {5500.0, 5510.0}


def test_a_map_present_but_empty_produces_zero_everywhere() -> None:
    fields = extract_chain_metadata(EMPTY_MAPS, EXPIRATION)

    assert (fields.call_contract_count, fields.put_contract_count, fields.strike_count) == (
        0,
        0,
        0,
    )
    assert "missing_call_contracts" in fields.data_quality_flags
    assert "missing_put_contracts" in fields.data_quality_flags
    assert _parse_rows(EMPTY_MAPS, EXPIRATION) == []
    assert list(iter_chain_options(EMPTY_MAPS, EXPIRATION)) == []


def test_calls_present_with_puts_absent_is_handled_identically_by_all_three() -> None:
    fields = extract_chain_metadata(CALLS_ONLY, EXPIRATION)
    rows = _parse_rows(CALLS_ONLY, EXPIRATION)

    assert fields.call_contract_count == 2
    assert fields.put_contract_count == 0
    assert fields.strike_count == 2
    assert "missing_put_contracts" in fields.data_quality_flags
    assert [row["option_type"] for row in rows] == ["CALL", "CALL"]
    assert {strike for strike, _, _ in iter_chain_options(CALLS_ONLY, EXPIRATION)} == {
        5500.0,
        5510.0,
    }


# --- Recorded divergences, asserted rather than reconciled ---------------------------


def test_a_non_numeric_strike_key_diverges_and_the_divergence_is_recorded() -> None:
    """The metadata skips an unparseable strike key; both live parsers raise ValueError.

    This is a genuine semantic difference, not a defect in the metadata: a bounded
    summary surface must not raise on malformed upstream data, while the live parsers
    are allowed to fail loudly on it. It is pinned here so a future consolidation has
    to decide which behaviour wins instead of inheriting one by accident.
    """
    fields = extract_chain_metadata(NON_NUMERIC_STRIKE_KEY, EXPIRATION)
    assert fields.call_contract_count == 1
    assert fields.strike_count == 1

    with pytest.raises(ValueError):
        list(iter_chain_options(NON_NUMERIC_STRIKE_KEY, EXPIRATION))
    with pytest.raises(ValueError):
        _parse_rows(NON_NUMERIC_STRIKE_KEY, EXPIRATION)


def test_neither_expiration_map_present_is_tolerated_by_all_three() -> None:
    """A payload with no expiration maps is a normal zero-result shape for all three.

    ``extract_chain_metadata`` used to raise ``ValueError`` on this shape while both live
    parsers quietly produced zero rows/yields for it. That was a genuine divergence with
    a real cost once shadow reads compare the two: a degenerate-but-legitimate response
    (e.g. after-hours or a halted symbol) made the gateway's ``/v1/chain`` return 502 and
    made the shadow comparator log a false "parsing" discrepancy, for a shape the direct
    collector path never treated as an error. The raise was removed so all three now
    agree: this is tolerated, not refused.
    """
    payload: dict[str, Any] = {"underlyingPrice": 5500.0}

    fields = extract_chain_metadata(payload, EXPIRATION)
    assert (fields.call_contract_count, fields.put_contract_count, fields.strike_count) == (
        0,
        0,
        0,
    )

    assert _parse_rows(payload, EXPIRATION) == []
    assert list(iter_chain_options(payload, EXPIRATION)) == []
