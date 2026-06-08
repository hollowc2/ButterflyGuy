"""Core scan logic for equity morning reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.volume import compute_rvol


@dataclass(frozen=True)
class EquitySnapshot:
    symbol: str
    price: float
    prior_close: float
    prior_day_pct: float
    session_gap_pct: float
    volume: int
    premarket_volume: int
    avg_volume_20d: float | None
    rvol: float | None
    sector: str
    universes: tuple[str, ...]


@dataclass(frozen=True)
class MarketContext:
    symbol: str
    price: float
    change_pct: float


@dataclass(frozen=True)
class ScanResults:
    prior_gainers: list[EquitySnapshot]
    prior_losers: list[EquitySnapshot]
    premarket_gainers: list[EquitySnapshot]
    premarket_losers: list[EquitySnapshot]
    movers_up: list[dict[str, Any]]
    movers_down: list[dict[str, Any]]
    market_context: list[MarketContext]
    scanned_symbols: int
    matched_symbols: int


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_equity_quote(
    symbol: str,
    payload: dict[str, Any],
    *,
    universes: set[str],
    sector: str = "Unknown",
    avg_volume_20d: float | None = None,
) -> EquitySnapshot | None:
    """Normalize a Schwab quote payload into an EquitySnapshot."""
    quote = payload.get("quote", {})
    extended = payload.get("extended", {})

    prior_close = _as_float(quote.get("closePrice"))
    if prior_close is None or prior_close <= 0:
        return None

    regular_price = _as_float(quote.get("lastPrice")) or _as_float(quote.get("mark"))
    extended_price = _as_float(extended.get("lastPrice")) or _as_float(extended.get("mark"))
    price = extended_price or regular_price
    if price is None or price <= 0:
        return None

    prior_day_pct = _as_float(quote.get("netPercentChange"))
    if prior_day_pct is None:
        prior_day_pct = ((regular_price or price) - prior_close) / prior_close * 100.0

    session_gap_pct = (price - prior_close) / prior_close * 100.0
    volume = _as_int(quote.get("totalVolume"))
    premarket_volume = _as_int(extended.get("totalVolume"))
    rvol = compute_rvol(premarket_volume, avg_volume_20d)

    return EquitySnapshot(
        symbol=symbol,
        price=price,
        prior_close=prior_close,
        prior_day_pct=prior_day_pct,
        session_gap_pct=session_gap_pct,
        volume=volume,
        premarket_volume=premarket_volume,
        avg_volume_20d=avg_volume_20d,
        rvol=rvol,
        sector=sector,
        universes=tuple(sorted(universes)),
    )


def passes_filters(snapshot: EquitySnapshot, settings: EquityScanSettings) -> bool:
    filters = settings.filters
    if snapshot.price < filters.min_price or snapshot.volume < filters.min_volume:
        return False
    if filters.min_rvol <= 0:
        return True
    return snapshot.rvol is not None and snapshot.rvol >= filters.min_rvol


def build_snapshots(
    quotes: dict[str, dict[str, Any]],
    symbol_map: dict[str, set[str]],
    settings: EquityScanSettings,
    *,
    avg_volumes: dict[str, float] | None = None,
    sector_map: dict[str, str] | None = None,
) -> list[EquitySnapshot]:
    avg_volumes = avg_volumes or {}
    sector_map = sector_map or {}
    snapshots: list[EquitySnapshot] = []
    for symbol, payload in quotes.items():
        universes = symbol_map.get(symbol)
        if not universes:
            continue
        snapshot = parse_equity_quote(
            symbol,
            payload,
            universes=universes,
            sector=sector_map.get(symbol, "Unknown"),
            avg_volume_20d=avg_volumes.get(symbol),
        )
        if snapshot is None:
            continue
        if passes_filters(snapshot, settings):
            snapshots.append(snapshot)
    return snapshots


def _top(
    snapshots: list[EquitySnapshot],
    *,
    key: str,
    reverse: bool,
    min_abs_pct: float,
    limit: int,
) -> list[EquitySnapshot]:
    filtered = [
        snap
        for snap in snapshots
        if (getattr(snap, key) >= min_abs_pct if reverse else getattr(snap, key) <= -min_abs_pct)
    ]
    return sorted(filtered, key=lambda snap: getattr(snap, key), reverse=reverse)[:limit]


def parse_market_context(symbol: str, payload: dict[str, Any]) -> MarketContext | None:
    quote = payload.get("quote", {})
    price = _as_float(quote.get("lastPrice")) or _as_float(quote.get("mark"))
    change_pct = _as_float(quote.get("netPercentChange"))
    if price is None or change_pct is None:
        return None
    return MarketContext(symbol=symbol, price=price, change_pct=change_pct)


def rank_scan_results(
    snapshots: list[EquitySnapshot],
    *,
    settings: EquityScanSettings,
    movers_up: list[dict[str, Any]],
    movers_down: list[dict[str, Any]],
    market_context: list[MarketContext],
    scanned_symbols: int,
) -> ScanResults:
    limits = settings.limits
    filters = settings.filters
    return ScanResults(
        prior_gainers=_top(
            snapshots,
            key="prior_day_pct",
            reverse=True,
            min_abs_pct=filters.prior_day_min_pct,
            limit=limits.prior_gainers,
        ),
        prior_losers=_top(
            snapshots,
            key="prior_day_pct",
            reverse=False,
            min_abs_pct=filters.prior_day_min_pct,
            limit=limits.prior_losers,
        ),
        premarket_gainers=_top(
            snapshots,
            key="session_gap_pct",
            reverse=True,
            min_abs_pct=filters.premarket_min_gap_pct,
            limit=limits.premarket_gainers,
        ),
        premarket_losers=_top(
            snapshots,
            key="session_gap_pct",
            reverse=False,
            min_abs_pct=filters.premarket_min_gap_pct,
            limit=limits.premarket_losers,
        ),
        movers_up=movers_up[: limits.movers_per_bucket],
        movers_down=movers_down[: limits.movers_per_bucket],
        market_context=market_context,
        scanned_symbols=scanned_symbols,
        matched_symbols=len(snapshots),
    )
