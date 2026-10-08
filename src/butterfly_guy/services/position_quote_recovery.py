"""Opt-in XSP paper recovery from fresh targeted quotes, never stale estimates."""

from __future__ import annotations

import asyncio
import math

from butterfly_guy.core.time_utils import now_eastern
from butterfly_guy.data.providers import GatewayAuthoritativeMarketDataProvider
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord


class HeldQuoteRecovery:
    """One bounded read per 30 seconds; require all held legs from the same response."""

    def __init__(self, provider: GatewayAuthoritativeMarketDataProvider) -> None:
        self.provider = provider
        self.next_attempt_at = 0.0

    async def recover(
        self, trade: TradeRecord, candidate: ButterflyCandidate,
    ) -> tuple[dict[float, OptionQuote] | None, dict]:
        loop = asyncio.get_running_loop()
        if loop.time() < self.next_attempt_at:
            return None, {}
        self.next_attempt_at = loop.time() + 30.0
        symbols = tuple(
            getattr(trade, f"{name}_symbol") or getattr(candidate, f"{name}_symbol")
            for name in ("lower", "center", "upper")
        )
        evidence = {"trade_id": trade.trade_id, "mode": "fresh_targeted_recovery"}
        if not all(symbols) or len(set(symbols)) != 3:
            return None, {**evidence, "status": "held_symbols_unavailable"}
        try:
            response = await asyncio.wait_for(
                self.provider.get_held_quotes_observed(symbols), timeout=3.0,
            )
        except Exception as error:
            return None, {**evidence, "status": "request_failed",
                          "error_type": type(error).__name__}
        by_symbol = {q.symbol: q for q in response.quotes}
        if (response.missing_symbols or len(response.quotes) != 3
                or set(by_symbol) != set(symbols)):
            return None, {**evidence, "status": "incomplete_response"}
        at = now_eastern()
        quotes = {}
        legs = []
        for name, symbol in zip(("lower", "center", "upper"), symbols, strict=True):
            q = by_symbol[symbol]
            event_age = (at - q.event_timestamp).total_seconds() if q.event_timestamp else None
            received_age = (at - q.gateway_received_at).total_seconds()
            # A fresh HTTP response alone does not refresh an old exchange event.
            usable = (
                not q.stale and not q.data_quality_flags
                and q.age_seconds is not None and 0 <= q.age_seconds <= 30
                and event_age is not None and 0 <= event_age <= 30
                and 0 <= received_age <= 30
                and all(math.isfinite(v) and v >= 0 for v in (q.bid, q.ask, q.mark))
                and q.bid <= q.mark <= q.ask
            )
            legs.append({"symbol": symbol, "usable": usable, "bid": q.bid,
                         "ask": q.ask, "mark": q.mark, "source": q.source,
                         "event_timestamp": q.event_timestamp.isoformat()
                         if q.event_timestamp else None,
                         "age_seconds": q.age_seconds,
                         "gateway_received_at": q.gateway_received_at.isoformat(),
                         "flags": list(q.data_quality_flags)})
            if usable:
                strike = getattr(candidate, f"{name}_strike")
                quotes[strike] = OptionQuote(
                    symbol=symbol, underlying="XSP", expiration=trade.trade_date,
                    strike=strike, option_type=candidate.direction,
                    bid=q.bid, ask=q.ask, mark=(q.bid + q.ask) / 2,
                )
        evidence.update(legs=legs, status="recovered" if len(quotes) == 3 else "unusable_quotes")
        return (quotes if len(quotes) == 3 else None), evidence
