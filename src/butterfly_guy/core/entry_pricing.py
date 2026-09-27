"""Shared entry-price limit policy for production and candidate runtimes."""

from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_UP, Decimal

# Minimum net price increment for a complex (multi-leg) order, by underlying.
# SPX/SPXW: $0.05; Cboe rejects other net prices (Cboe notice C2022032100,
# effective 2022-04-24). XSP and other Cboe classes: $0.01 (same notice).
# NDX/NDXP: $0.01 (Nasdaq PHLX Options 3, Section 14(b)).
COMPLEX_NET_PRICE_INCREMENT = {
    "SPX": Decimal("0.05"),
    "XSP": Decimal("0.01"),
    "NDX": Decimal("0.01"),
}


def net_price_increment(underlying: str) -> Decimal:
    """Complex-order net price increment; unknown underlyings fail closed."""
    try:
        return COMPLEX_NET_PRICE_INCREMENT[underlying.upper()]
    except KeyError:
        raise ValueError(f"no complex-order price increment for {underlying!r}") from None


def _to_increment(price: float, underlying: str, rounding: str) -> float:
    increment = net_price_increment(underlying)
    # Drop float noise first (3.2 + 0.15 == 3.3500000000000005) so an on-increment
    # price never moves a whole step.
    normalized = Decimal(str(price)).quantize(Decimal("0.0001"))
    steps = (normalized / increment).quantize(Decimal("1"), rounding=rounding)
    return float(steps * increment)


def round_debit_limit(price: float, underlying: str) -> float:
    """Round a debit (buy) limit down to a valid increment, so it never pays more."""
    return _to_increment(price, underlying, ROUND_DOWN)


def round_credit_limit(price: float, underlying: str) -> float:
    """Round a credit (sell) limit up to a valid increment, so it never accepts less."""
    return _to_increment(price, underlying, ROUND_UP)


def capped_entry_limit(
    unconstrained_limit: float,
    max_entry_price: float,
    underlying: str,
) -> float:
    """Return an increment-valid debit limit that never exceeds the configured maximum."""
    ceiling = min(unconstrained_limit, max_entry_price)
    return round_debit_limit(ceiling, underlying)


def entry_fill_within_limit(fill_price: float, limit_price: float) -> bool:
    """Return whether an entry fill respects its hard debit ceiling."""
    return Decimal(str(fill_price)) <= Decimal(str(limit_price))
