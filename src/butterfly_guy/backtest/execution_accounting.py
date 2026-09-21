"""Post-process frozen butterfly decisions with explicit executable quote sides."""

from __future__ import annotations

import bisect
import datetime as dt
import math
from dataclasses import dataclass
from typing import Literal

from butterfly_guy.backtest.chain_cache import ChainDay
from butterfly_guy.backtest.simulation_engine import DayResult
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.position.position_manager import fly_settlement_value

ExecutionModel = Literal["marketable", "stressed_marketable"]
MarketStatus = Literal[
    "priced",
    "missing_entry_market",
    "crossed_entry_market",
    "missing_exit_market",
    "crossed_exit_market",
]

CONTRACTS_PER_BUTTERFLY = 4
STRESSED_LEG_SLIPPAGE = 0.05


@dataclass(frozen=True)
class QuoteMarket:
    """The three recorded leg quotes needed to price a 1/-2/1 butterfly."""

    lower: OptionQuote | None
    center: OptionQuote | None
    upper: OptionQuote | None
    missing_strikes: tuple[float, ...]
    crossed_strikes: tuple[float, ...]

    @property
    def usable(self) -> bool:
        return not self.missing_strikes and not self.crossed_strikes


@dataclass(frozen=True)
class ExecutableTrade:
    """Executable accounting for one already-frozen simulated trade."""

    date: dt.date
    model: ExecutionModel
    status: MarketStatus
    exit_reason: str
    entry_price: float | None = None
    exit_price: float | None = None
    pnl: float | None = None
    mfe: float | None = None
    entry_snapshot_time: dt.datetime | None = None
    exit_snapshot_time: dt.datetime | None = None
    missing_strikes: tuple[float, ...] = ()
    crossed_strikes: tuple[float, ...] = ()
    skipped_exit_observations: int = 0
    settlement_fallback: bool = False
    path_snapshots: int = 0
    usable_path_snapshots: int = 0
    missing_path_snapshots: int = 0
    crossed_path_snapshots: int = 0

    @property
    def priced(self) -> bool:
        return self.status == "priced"


def _finite_quote_side(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def inspect_quote_market(
    quotes: list[OptionQuote] | None,
    candidate: ButterflyCandidate,
) -> QuoteMarket:
    """Validate all recorded legs without substituting or carrying quotes forward."""
    by_strike = {
        quote.strike: quote
        for quote in quotes or []
        if quote.option_type == candidate.direction
    }
    strikes = (
        candidate.lower_strike,
        candidate.center_strike,
        candidate.upper_strike,
    )
    legs = tuple(by_strike.get(strike) for strike in strikes)
    missing = tuple(
        strike
        for strike, quote in zip(strikes, legs, strict=True)
        if quote is None
        or not _finite_quote_side(quote.bid)
        or not _finite_quote_side(quote.ask)
    )
    crossed = tuple(
        strike
        for strike, quote in zip(strikes, legs, strict=True)
        if quote is not None
        and _finite_quote_side(quote.bid)
        and _finite_quote_side(quote.ask)
        and quote.bid > quote.ask
    )
    return QuoteMarket(
        lower=legs[0],
        center=legs[1],
        upper=legs[2],
        missing_strikes=missing,
        crossed_strikes=crossed,
    )


def snapshot_keys(chains: dict[dt.datetime, list[OptionQuote]]) -> list[dt.datetime]:
    """Return the recorded snapshot times in ascending order."""
    return chains._sorted_keys if isinstance(chains, ChainDay) else sorted(chains)


def snapshot_at_or_before(
    chains: dict[dt.datetime, list[OptionQuote]],
    decision_time: dt.datetime,
) -> tuple[dt.datetime | None, list[OptionQuote] | None]:
    """Return only a snapshot recorded no later than the simulated decision."""
    keys = snapshot_keys(chains)
    index = bisect.bisect_right(keys, decision_time) - 1
    if index < 0:
        return None, None
    snapshot_time = keys[index]
    return snapshot_time, chains[snapshot_time]


def _entry_debit(market: QuoteMarket) -> float:
    assert market.lower is not None and market.center is not None and market.upper is not None
    return market.lower.ask + market.upper.ask - 2 * market.center.bid


def _exit_credit(market: QuoteMarket) -> float:
    assert market.lower is not None and market.center is not None and market.upper is not None
    return market.lower.bid + market.upper.bid - 2 * market.center.ask


def price_frozen_trade(
    *,
    baseline: DayResult,
    candidate: ButterflyCandidate,
    chains: dict[dt.datetime, list[OptionQuote]],
    model: ExecutionModel,
    commission_per_contract: float = 0.65,
    settlement_spot: float | None = None,
) -> ExecutableTrade:
    """Reprice a frozen baseline trade at executable sides without changing decisions.

    Entry buys the two outer contracts at ask and sells two center contracts at bid.
    Intraday exit uses the inverse sides. Cash settlement has no closing order. The
    stressed model moves every contract fill $0.05 adversely from its executable side.

    An intraday exit observation that is missing or crossed is skipped, and the exit
    rolls forward to the next recorded monitoring time. If no executable exit remains
    before settlement, *settlement_spot* supplies the settlement-correct exit; without
    one the trade stays unpriced.
    """
    if not baseline.traded or baseline.entry_time is None or baseline.exit_time is None:
        raise ValueError("baseline must be a completed, traded simulation result")
    if model not in {"marketable", "stressed_marketable"}:
        raise ValueError(f"unsupported execution model: {model}")

    adverse_slippage = STRESSED_LEG_SLIPPAGE if model == "stressed_marketable" else 0.0
    commission = CONTRACTS_PER_BUTTERFLY * commission_per_contract / 100
    per_side_stress = CONTRACTS_PER_BUTTERFLY * adverse_slippage

    entry_ts, entry_quotes = snapshot_at_or_before(chains, baseline.entry_time)
    entry_market = inspect_quote_market(entry_quotes, candidate)
    if entry_market.missing_strikes:
        return ExecutableTrade(
            date=baseline.date,
            model=model,
            status="missing_entry_market",
            exit_reason=baseline.exit_reason,
            entry_snapshot_time=entry_ts,
            missing_strikes=entry_market.missing_strikes,
        )
    if entry_market.crossed_strikes:
        return ExecutableTrade(
            date=baseline.date,
            model=model,
            status="crossed_entry_market",
            exit_reason=baseline.exit_reason,
            entry_snapshot_time=entry_ts,
            crossed_strikes=entry_market.crossed_strikes,
        )

    entry_price = _entry_debit(entry_market) + commission + per_side_stress
    exit_ts: dt.datetime | None = None
    exit_price: float | None = None
    skipped_exit_observations = 0
    settlement_fallback = False
    gap_status: MarketStatus = "missing_exit_market"
    gap_missing: tuple[float, ...] = ()
    gap_crossed: tuple[float, ...] = ()
    if baseline.exit_reason == "cash_settled":
        exit_price = baseline.exit_price
    else:
        keys = snapshot_keys(chains)
        index = max(0, bisect.bisect_right(keys, baseline.exit_time) - 1)
        for snapshot_time in keys[index:]:
            exit_market = inspect_quote_market(chains[snapshot_time], candidate)
            if exit_market.missing_strikes:
                skipped_exit_observations += 1
                gap_status = "missing_exit_market"
                gap_missing = exit_market.missing_strikes
                gap_crossed = ()
                continue
            if exit_market.crossed_strikes:
                skipped_exit_observations += 1
                gap_status = "crossed_exit_market"
                gap_missing = ()
                gap_crossed = exit_market.crossed_strikes
                continue
            exit_ts = snapshot_time
            exit_price = _exit_credit(exit_market) - commission - per_side_stress
            break
        if exit_price is None:
            if settlement_spot is None:
                return ExecutableTrade(
                    date=baseline.date,
                    model=model,
                    status=gap_status,
                    exit_reason=baseline.exit_reason,
                    entry_price=entry_price,
                    entry_snapshot_time=entry_ts,
                    missing_strikes=gap_missing,
                    crossed_strikes=gap_crossed,
                    skipped_exit_observations=skipped_exit_observations,
                )
            exit_price = fly_settlement_value(candidate, settlement_spot)
            settlement_fallback = True

    path_snapshots = 0
    usable_path_snapshots = 0
    missing_path_snapshots = 0
    crossed_path_snapshots = 0
    executable_pnls: list[float] = []
    path_end = max(baseline.exit_time, exit_ts) if exit_ts else baseline.exit_time
    for snapshot_time in snapshot_keys(chains):
        if not baseline.entry_time < snapshot_time <= path_end:
            continue
        path_snapshots += 1
        market = inspect_quote_market(chains[snapshot_time], candidate)
        if market.missing_strikes:
            missing_path_snapshots += 1
            continue
        if market.crossed_strikes:
            crossed_path_snapshots += 1
            continue
        usable_path_snapshots += 1
        executable_pnls.append(
            _exit_credit(market) - commission - per_side_stress - entry_price
        )

    pnl = exit_price - entry_price
    mfe = max(0.0, pnl, *executable_pnls)
    return ExecutableTrade(
        date=baseline.date,
        model=model,
        status="priced",
        exit_reason=baseline.exit_reason,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        mfe=mfe,
        entry_snapshot_time=entry_ts,
        exit_snapshot_time=exit_ts,
        skipped_exit_observations=skipped_exit_observations,
        settlement_fallback=settlement_fallback,
        path_snapshots=path_snapshots,
        usable_path_snapshots=usable_path_snapshots,
        missing_path_snapshots=missing_path_snapshots,
        crossed_path_snapshots=crossed_path_snapshots,
    )
