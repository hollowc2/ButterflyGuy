"""Shared entry-price limit policy for production and candidate runtimes."""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

PRICE_INCREMENT = Decimal("0.01")


def capped_entry_limit(
    unconstrained_limit: float,
    max_entry_price: float,
) -> float:
    """Return a cent-valid debit limit that never exceeds the configured maximum."""
    ceiling = min(
        Decimal(str(unconstrained_limit)),
        Decimal(str(max_entry_price)),
    )
    return float(ceiling.quantize(PRICE_INCREMENT, rounding=ROUND_DOWN))


def entry_fill_within_limit(fill_price: float, limit_price: float) -> bool:
    """Return whether an entry fill respects its hard debit ceiling."""
    return Decimal(str(fill_price)) <= Decimal(str(limit_price))
