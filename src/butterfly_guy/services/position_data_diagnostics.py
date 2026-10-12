"""Read-only held-leg evidence. Shadow prices never reach the position manager."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from butterfly_guy.core.config import PositionDataSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import now_eastern
from butterfly_guy.data.providers import ChainObservation, GatewayAuthoritativeMarketDataProvider
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.db.queries import DecisionQueries

log = get_logger(__name__)


def held_leg_evidence(
    trade: TradeRecord,
    candidate: ButterflyCandidate,
    quotes: dict[float, OptionQuote],
    observation: ChainObservation | None,
    *,
    chain_failed: bool = False,
) -> list[dict[str, Any]]:
    """Distinguish provider omission from stale filtering using the same chain read."""
    legs = []
    for name in ("lower", "center", "upper"):
        strike = getattr(candidate, f"{name}_strike")
        quote = quotes.get(strike)
        omitted = next((o for o in observation.omitted
                        if o.strike == strike and o.option_type == candidate.direction), None
                       ) if observation else None
        symbol = (getattr(trade, f"{name}_symbol")
                  or getattr(candidate, f"{name}_symbol")
                  or (quote.symbol if quote else "")
                  or (omitted.symbol if omitted else ""))
        timing = observation.contracts.get(symbol) if observation else None
        if quote:
            reason = "usable"
        elif chain_failed:
            reason = "chain_read_failed"
        elif omitted:
            reason = ("missing_quote_timestamp" if omitted.age_seconds is None
                      or "missing_event_timestamp" in omitted.flags else "stale_quote")
        else:
            reason = "missing_from_gateway_chain" if observation else "missing_from_chain"
        event = omitted.event_timestamp if omitted else timing.event_timestamp if timing else None
        legs.append({
            "symbol": symbol, "strike": strike, "option_type": candidate.direction,
            "reason": reason,
            "bid": quote.bid if quote else omitted.bid if omitted else None,
            "ask": quote.ask if quote else omitted.ask if omitted else None,
            "mark": quote.mark if quote else omitted.mark if omitted else None,
            "event_timestamp": event.isoformat() if event else None,
            "age_seconds": (omitted.age_seconds if omitted
                            else timing.age_seconds if timing else None),
            "stale": omitted.stale if omitted else False if timing else None,
            "flags": list(omitted.flags) if omitted else [],
        })
    return legs


def _fly_mark(legs: list[dict[str, Any]]) -> float | None:
    marks = [leg.get("mark") for leg in legs]
    if len(marks) != 3 or any(
        not isinstance(mark, (int, float)) or not math.isfinite(mark) for mark in marks
    ):
        return None
    return marks[0] - 2 * marks[1] + marks[2]


class PositionQuoteShadow:
    """At most one timed request/write in flight; bounded sampling with no trading effects."""

    def __init__(
        self, provider: GatewayAuthoritativeMarketDataProvider,
        decisions: DecisionQueries, settings: PositionDataSettings,
        *, trade_id: int, underlying: str,
    ) -> None:
        self.provider = provider
        self.decisions = decisions
        self.settings = settings
        self.trade_id = trade_id
        self.underlying = underlying
        self.task: asyncio.Task | None = None
        self.next_sample_at = 0.0

    def submit(self, legs: list[dict[str, Any]], observation: ChainObservation | None) -> None:
        loop = asyncio.get_running_loop()
        if (self.task is not None and not self.task.done()) or loop.time() < self.next_sample_at:
            return
        self.next_sample_at = loop.time() + self.settings.shadow_interval_seconds
        self.task = asyncio.create_task(self._sample(legs, observation))

    async def close(self) -> None:
        if self.task is not None:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def _sample(
        self, legs: list[dict[str, Any]], observation: ChainObservation | None,
    ) -> None:
        symbols = tuple(leg["symbol"] for leg in legs)
        data: dict[str, Any] = {
            "trade_id": self.trade_id, "sampled_at": now_eastern().isoformat(),
            "mode": "shadow_only", "chain_legs": legs,
            "chain_gateway_received_at": (
                observation.gateway_received_at.isoformat()
                if observation and observation.gateway_received_at else None
            ),
            "chain_age_seconds": observation.age_seconds if observation else None,
            "chain_source": observation.source if observation else None,
            "chain_event_timestamp": (
                observation.event_timestamp.isoformat()
                if observation and observation.event_timestamp else None
            ),
            "chain_flags": list(observation.data_quality_flags) if observation else [],
        }
        if not all(symbols) or len(set(symbols)) != 3:
            data["targeted_status"] = "held_symbols_unavailable"
        else:
            try:
                response = await asyncio.wait_for(
                    self.provider.get_held_quotes_observed(symbols),
                    timeout=self.settings.shadow_timeout_seconds,
                )
                by_symbol = {quote.symbol: quote for quote in response.quotes}
                targeted = []
                for symbol in symbols:
                    quote = by_symbol.get(symbol)
                    targeted.append({
                        "symbol": symbol,
                        "reason": "missing_from_quote_response" if not quote
                        else "missing_quote_timestamp" if quote.age_seconds is None
                        else "stale_quote" if quote.stale
                        else "quality_rejected" if quote.data_quality_flags else "usable",
                        "bid": quote.bid if quote else None,
                        "ask": quote.ask if quote else None,
                        "mark": quote.mark if quote else None,
                        "source": quote.source if quote else None,
                        "event_timestamp": (quote.event_timestamp.isoformat()
                                            if quote and quote.event_timestamp else None),
                        "gateway_received_at": (quote.gateway_received_at.isoformat()
                                                if quote else None),
                        "age_seconds": quote.age_seconds if quote else None,
                        "stale": quote.stale if quote else None,
                        "flags": list(quote.data_quality_flags) if quote else [],
                    })
                data.update(targeted_status="response_received", targeted_legs=targeted)
                # Marks are evidence only, and are comparable only with usable bid/ask data.
                targeted_usable = all(
                    leg["reason"] == "usable" and leg["age_seconds"] is not None
                    and not leg["flags"]
                    and all(isinstance(leg[k], (int, float)) and math.isfinite(leg[k])
                            and leg[k] >= 0 for k in ("bid", "ask", "mark"))
                    and leg["bid"] <= leg["ask"] for leg in targeted
                )
                chain_usable = all(leg["reason"] == "usable" for leg in legs)
                data["targeted_all_usable"] = targeted_usable
                data["chain_all_usable"] = chain_usable
                data["targeted_fly_mark"] = _fly_mark(targeted) if targeted_usable else None
                data["chain_fly_mark"] = _fly_mark(legs) if chain_usable else None
                data["mark_difference"] = (
                    data["targeted_fly_mark"] - data["chain_fly_mark"]
                    if data["targeted_fly_mark"] is not None
                    and data["chain_fly_mark"] is not None else None
                )
            except Exception as error:
                # Exception messages from HTTP clients can contain connection details.
                data.update(targeted_status="request_failed", error_type=type(error).__name__)
        log.info("position_held_quote_shadow", **data)
        try:
            await asyncio.wait_for(
                self.decisions.log_event("position_held_quote_shadow", data,
                                         underlying=self.underlying),
                timeout=self.settings.shadow_timeout_seconds,
            )
        except Exception as error:
            log.warning("position_shadow_write_failed", trade_id=self.trade_id,
                        error_type=type(error).__name__)
