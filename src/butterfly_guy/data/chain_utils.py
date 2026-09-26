"""Shared utilities for parsing Schwab option chain responses."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Generator

from butterfly_guy.core.logging import get_logger

log = get_logger(__name__)

# PM-settled roots for the traded underlyings. On monthly-expiration days the index
# chain can list the AM-settled root (SPX, NDX) alongside these under one strike.
PM_SETTLED_ROOTS = frozenset({"SPXW", "NDXP", "XSP"})

_ROOT_RE = re.compile(r"^([A-Z]+)")


def _is_pm_settled(opt: dict) -> bool:
    """True when the contract is PM-settled, by symbol root, else by settlementType."""
    match = _ROOT_RE.match(str(opt.get("symbol") or ""))
    if match:
        return match.group(1) in PM_SETTLED_ROOTS
    return opt.get("settlementType") == "P"


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
                if len(options) == 1:
                    yield float(strike_str), option_type, options[0]
                    continue
                pm_settled = [opt for opt in options if _is_pm_settled(opt)]
                if len(pm_settled) == 1:
                    yield float(strike_str), option_type, pm_settled[0]
                    continue
                log.warning(
                    "chain_strike_ambiguous_contracts",
                    strike=strike_str,
                    option_type=option_type,
                    symbols=[opt.get("symbol") for opt in options],
                    pm_settled_count=len(pm_settled),
                )
