"""Convert option_chain_snapshots rows into OptionQuote objects."""

from __future__ import annotations

import datetime as dt
from typing import Any

from butterfly_guy.data.schemas import OptionQuote


def rows_to_option_quotes(
    rows: list[dict[str, Any]],
    *,
    underlying: str,
    expiration: dt.date,
) -> list[OptionQuote]:
    """Build OptionQuote list from option_chain_snapshots query rows."""
    quotes: list[OptionQuote] = []
    for row in rows:
        quotes.append(
            OptionQuote(
                symbol=row.get("symbol") or "",
                underlying=underlying,
                expiration=expiration,
                strike=float(row["strike"]),
                option_type=row["option_type"],
                bid=_as_float(row.get("bid")),
                ask=_as_float(row.get("ask")),
                mark=_as_float(row.get("mark")),
                last=_as_float(row.get("last")),
                volume=_as_int(row.get("volume")),
                open_interest=_as_int(row.get("open_interest")),
                iv=_as_float(row.get("iv")),
                delta=_as_float(row.get("delta")),
                gamma=_as_float(row.get("gamma")),
                theta=_as_float(row.get("theta")),
                vega=_as_float(row.get("vega")),
                bid_size=_as_int(row.get("bid_size")),
                ask_size=_as_int(row.get("ask_size")),
                rho=_as_float(row.get("rho")),
                intrinsic_value=_as_float(row.get("intrinsic_value")),
                time_value=_as_float(row.get("time_value")),
                in_the_money=bool(row.get("in_the_money") or False),
                days_to_expiration=_as_int(row.get("days_to_expiration")),
            )
        )
    return quotes


def _as_float(value: Any, default: float = 0.0) -> float:
    return float(value) if value is not None else default


def _as_int(value: Any, default: int = 0) -> int:
    return int(value) if value is not None else default
