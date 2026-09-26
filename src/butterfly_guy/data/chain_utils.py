"""Shared utilities for parsing Schwab option chain responses."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Generator, Iterable, Mapping, Sequence
from typing import Any, TypeVar

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

# PM-settled roots for the traded underlyings. On monthly-expiration days the index
# chain can list the AM-settled root (SPX, NDX) alongside these under one strike.
PM_SETTLED_ROOTS = frozenset({"SPXW", "NDXP", "XSP"})

_ROOT_RE = re.compile(r"^([A-Z]+)")

#: option_chain_snapshots columns that identify one strike's contracts at one snapshot.
SNAPSHOT_CONTRACT_KEY = ("snapshot_time", "strike", "option_type")

RowT = TypeVar("RowT", bound=Mapping[str, Any])


def _is_pm_settled(opt: dict) -> bool:
    """True when the contract is PM-settled, by symbol root, else by settlementType."""
    match = _ROOT_RE.match(str(opt.get("symbol") or ""))
    if match:
        return match.group(1) in PM_SETTLED_ROOTS
    return opt.get("settlementType") == "P"


def select_strike_contract(options: Sequence[RowT], **log_context: Any) -> RowT | None:
    """Return the contract to trade among those listed under one strike.

    One contract is returned as-is. Several (e.g. SPX and SPXW on a monthly expiration)
    resolve to the single PM-settled one; if there is not exactly one, None is returned
    with a warning rather than guessing.
    """
    if len(options) == 1:
        return options[0]
    pm_settled = [opt for opt in options if _is_pm_settled(opt)]
    if len(pm_settled) == 1:
        return pm_settled[0]
    log.warning(
        "chain_strike_ambiguous_contracts",
        **log_context,
        symbols=[opt.get("symbol") for opt in options],
        pm_settled_count=len(pm_settled),
    )
    return None


def select_pm_settled_rows(
    rows: Iterable[RowT],
    key_fields: Sequence[str] = SNAPSHOT_CONTRACT_KEY,
) -> list[RowT]:
    """Apply the live parser's one-contract-per-strike rule to option_chain_snapshots rows.

    The collector stores every contract a strike lists; selection and replay must see the
    same single contract live trading would. Rows are grouped by *key_fields* (missing
    fields count as None) and order of first appearance is kept.
    """
    groups: dict[tuple, list[RowT]] = {}
    for row in rows:
        groups.setdefault(tuple(row.get(field) for field in key_fields), []).append(row)
    selected: list[RowT] = []
    for key, options in groups.items():
        contract = select_strike_contract(options, key=[str(part) for part in key])
        if contract is not None:
            selected.append(contract)
    return selected


def iter_chain_options(
    chain_data: dict,
    expiration: dt.date,
    direction: str | None = None,
) -> Generator[tuple[float, str, dict], None, None]:
    """Yield (strike, option_type, opt_dict) for each option matching the expiration.

    A strike with one contract yields it. A strike with several contracts (e.g. SPX
    and SPXW on a monthly expiration) yields the single PM-settled one; if there is
    not exactly one, the strike is skipped with a warning rather than guessed.

    Args:
        chain_data: Raw Schwab option chain response.
        expiration: Target expiration date to filter on.
        direction: "CALL", "PUT", or None for both.
    """
    pairs: list[tuple[str, str]] = []
    if direction != "PUT":
        pairs.append(("CALL", "callExpDateMap"))
    if direction != "CALL":
        pairs.append(("PUT", "putExpDateMap"))

    exp_str = str(expiration)
    for option_type, map_key in pairs:
        exp_map = chain_data.get(map_key, {})
        for exp_key, strikes in exp_map.items():
            if exp_str not in exp_key:
                continue
            for strike_str, options in strikes.items():
                if not options:
                    continue
                contract = select_strike_contract(
                    options, strike=strike_str, option_type=option_type
                )
                if contract is not None:
                    yield float(strike_str), option_type, contract
