"""Core scan logic for equity morning reports."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from butterfly_guy.core.time_utils import is_market_open, is_premarket_window
from butterfly_guy.equity_scan.config import EquityScanSettings
from butterfly_guy.equity_scan.volume import compute_rvol

INDEX_UNIVERSES = frozenset({"sp500", "nq100"})


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
    show_premarket: bool = True
    show_movers: bool = True


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


def _mid_bid_ask(payload: dict[str, Any]) -> float | None:
    bid = _as_float(payload.get("bidPrice"))
    ask = _as_float(payload.get("askPrice"))
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return None
    return (bid + ask) / 2.0


def _quote_trade_time_ms(payload: dict[str, Any]) -> int:
    return _as_int(payload.get("tradeTime"))


def _live_price(
    quote: dict[str, Any],
    extended: dict[str, Any],
    *,
    in_premarket: bool,
) -> float | None:
    """Pick the best current price; during premarket prefer the fresher quote side."""
    regular = _as_float(quote.get("lastPrice")) or _as_float(quote.get("mark"))
    extended_px = _as_float(extended.get("lastPrice")) or _as_float(extended.get("mark"))

    if not in_premarket:
        return regular or extended_px

    ext_time = _quote_trade_time_ms(extended)
    reg_time = _quote_trade_time_ms(quote)
    if ext_time and reg_time:
        if ext_time >= reg_time:
            return extended_px or regular or _mid_bid_ask(extended) or _mid_bid_ask(quote)
        return regular or extended_px or _mid_bid_ask(quote) or _mid_bid_ask(extended)

    return (
        extended_px
        or regular
        or _mid_bid_ask(extended)
        or _mid_bid_ask(quote)
    )


def parse_equity_quote(
    symbol: str,
    payload: dict[str, Any],
    *,
    universes: set[str],
    sector: str = "Unknown",
    avg_volume_20d: float | None = None,
    in_premarket: bool = False,
) -> EquitySnapshot | None:
    """Normalize a Schwab quote payload into an EquitySnapshot."""
    quote = payload.get("quote", {})
    extended = payload.get("extended", {})

    prior_close = _as_float(quote.get("closePrice"))
    if prior_close is None or prior_close <= 0:
        return None

    regular_price = _as_float(quote.get("lastPrice")) or _as_float(quote.get("mark"))
    price = _live_price(quote, extended, in_premarket=in_premarket)
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
    if filters.require_index_membership and not (INDEX_UNIVERSES & set(snapshot.universes)):
        return False
    if filters.max_abs_pct is not None:
        cap = filters.max_abs_pct
        if abs(snapshot.prior_day_pct) > cap or abs(snapshot.session_gap_pct) > cap:
            return False
    if filters.min_rvol > 0 and snapshot.premarket_volume > 0:
        return snapshot.rvol is not None and snapshot.rvol >= filters.min_rvol
    return True


def _is_duplicate_premarket(snapshot: EquitySnapshot, *, tolerance_pct: float) -> bool:
    """True when the gap is essentially the same as the prior-day move."""
    return abs(snapshot.session_gap_pct - snapshot.prior_day_pct) <= tolerance_pct


def _dedupe_premarket(
    snapshots: list[EquitySnapshot],
    *,
    tolerance_pct: float,
) -> list[EquitySnapshot]:
    return [
        snap
        for snap in snapshots
        if not _is_duplicate_premarket(snap, tolerance_pct=tolerance_pct)
    ]


def _mover_change_pct(item: dict[str, Any]) -> float | None:
    pct = item.get("changePercent") or item.get("netPercentChange")
    if pct is None:
        change = item.get("change") or item.get("netChange")
        if change is None:
            return None
        try:
            return float(change)
        except (TypeError, ValueError):
            return None
    try:
        return float(pct)
    except (TypeError, ValueError):
        return None


def _mover_symbol(item: dict[str, Any]) -> str:
    return str(item.get("symbol") or item.get("ticker") or "?")


def filter_movers(
    movers_up: list[dict[str, Any]],
    movers_down: list[dict[str, Any]],
    *,
    min_abs_pct: float,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Drop stale/trivial movers and collapse identical up/down lists."""

    def _filter(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in items:
            pct = _mover_change_pct(item)
            if pct is None or abs(pct) < min_abs_pct:
                continue
            symbol = _mover_symbol(item)
            if symbol in seen:
                continue
            seen.add(symbol)
            filtered.append(item)
        return filtered[:limit]

    up = _filter(movers_up)
    down = _filter(movers_down)
    up_symbols = {_mover_symbol(item) for item in up}
    down_symbols = {_mover_symbol(item) for item in down}
    if up_symbols and up_symbols == down_symbols:
        return [], []
    return up, down


def build_snapshots(
    quotes: dict[str, dict[str, Any]],
    symbol_map: dict[str, set[str]],
    settings: EquityScanSettings,
    *,
    avg_volumes: dict[str, float] | None = None,
    sector_map: dict[str, str] | None = None,
    in_premarket: bool = False,
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
            in_premarket=in_premarket,
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
    generated_at: dt.datetime | None = None,
) -> ScanResults:
    limits = settings.limits
    filters = settings.filters
    show_premarket = is_premarket_window(
        generated_at,
        start=settings.premarket_start_et,
    )
    show_movers = settings.include_movers and is_market_open(generated_at)

    prior_gainers = _top(
        snapshots,
        key="prior_day_pct",
        reverse=True,
        min_abs_pct=filters.prior_day_min_pct,
        limit=limits.prior_gainers,
    )
    prior_losers = _top(
        snapshots,
        key="prior_day_pct",
        reverse=False,
        min_abs_pct=filters.prior_day_min_pct,
        limit=limits.prior_losers,
    )

    premarket_gainers: list[EquitySnapshot] = []
    premarket_losers: list[EquitySnapshot] = []
    if show_premarket:
        premarket_gainers = _top(
            snapshots,
            key="session_gap_pct",
            reverse=True,
            min_abs_pct=filters.premarket_min_gap_pct,
            limit=limits.premarket_gainers,
        )
        premarket_losers = _top(
            snapshots,
            key="session_gap_pct",
            reverse=False,
            min_abs_pct=filters.premarket_min_gap_pct,
            limit=limits.premarket_losers,
        )
        if settings.dedupe_premarket_with_prior:
            premarket_gainers = _dedupe_premarket(
                premarket_gainers,
                tolerance_pct=settings.gap_overlap_tolerance_pct,
            )
            premarket_losers = _dedupe_premarket(
                premarket_losers,
                tolerance_pct=settings.gap_overlap_tolerance_pct,
            )

    filtered_movers_up: list[dict[str, Any]] = []
    filtered_movers_down: list[dict[str, Any]] = []
    if show_movers:
        filtered_movers_up, filtered_movers_down = filter_movers(
            movers_up,
            movers_down,
            min_abs_pct=settings.movers_min_abs_pct,
            limit=limits.movers_per_bucket,
        )

    return ScanResults(
        prior_gainers=prior_gainers,
        prior_losers=prior_losers,
        premarket_gainers=premarket_gainers,
        premarket_losers=premarket_losers,
        movers_up=filtered_movers_up,
        movers_down=filtered_movers_down,
        market_context=market_context,
        scanned_symbols=scanned_symbols,
        matched_symbols=len(snapshots),
        show_premarket=show_premarket,
        show_movers=show_movers,
    )
