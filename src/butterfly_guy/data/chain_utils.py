"""Shared utilities for parsing Schwab option chain responses."""

from __future__ import annotations

import datetime as dt
from collections.abc import Generator


def iter_chain_options(
    chain_data: dict,
    expiration: dt.date,
    direction: str | None = None,
) -> Generator[tuple[float, str, dict], None, None]:
    """Yield (strike, option_type, opt_dict) for each option matching the expiration.

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
                if options:
                    yield float(strike_str), option_type, options[0]
