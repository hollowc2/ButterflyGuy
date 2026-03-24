"""Trade service — orchestrates entry flow."""

from __future__ import annotations

import datetime as dt

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    daily_pnl, daily_trade_count, trades_active, trades_total,
    entry_vix, entry_expected_move, entry_center_strike, entry_wing_width,
    entry_cost, entry_max_profit, entry_lower_be, entry_upper_be,
    butterfly_candidates_found, butterfly_scans_total,
)
from butterfly_guy.strategy.butterfly_builder import vix_expected_move as _vix_expected_move
from butterfly_guy.core.time_utils import get_0dte_expiration, now_eastern, time_in_window
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import SCHWAB_CHAIN_SYMBOLS, SCHWAB_SPOT_SYMBOLS, SchwabClientWrapper
from butterfly_guy.db.queries import CandidateQueries, ChainQueries, DecisionQueries, TradeQueries
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.strategy.bias_filter import BiasScoreFilter
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder, vix_target_center
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter

log = get_logger(__name__)


class TradeService:
    """Orchestrates the full entry/exit trading flow."""

    def __init__(
        self,
        config: AppConfig,
        schwab: SchwabClientWrapper,
        risk_engine: RiskEngine,
        order_manager: OrderManager,
        builder: ButterflyBuilder,
        selector: ButterflySelector,
        direction_filter: DirectionFilter,
        chain_queries: ChainQueries,
        trade_queries: TradeQueries,
        candidate_queries: CandidateQueries,
        decision_queries: DecisionQueries,
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.risk_engine = risk_engine
        self.order_manager = order_manager
        self.builder = builder
        self.selector = selector
        self.direction_filter = direction_filter
        self.chain_queries = chain_queries
        self.trade_queries = trade_queries
        self.candidate_queries = candidate_queries
        self.decision_queries = decision_queries

    async def attempt_entry(self) -> tuple[TradeRecord, ButterflyCandidate] | None:
        """Full entry flow: risk → time → direction (once) → retry loop (re-scan + fill)."""
        # Risk check
        allowed, reason = await self.risk_engine.can_trade()
        if not allowed:
            await self.decision_queries.log_event("entry_blocked", {"reason": reason})
            log.info("entry_blocked", reason=reason)
            return None

        # Time window check
        if not time_in_window(
            self.config.entry.start_time,
            self.config.entry.end_time,
            self.config.entry.timezone,
        ):
            return None

        expiration = get_0dte_expiration()
        underlying = self.config.strategy.underlying
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(underlying, underlying)

        # Get initial spot price for direction determination
        try:
            spot_price = await self.schwab.get_spot_price(spot_symbol)
        except Exception as e:
            log.error("spot_fetch_failed", error=str(e))
            return None

        # Fetch previous close from DB (fallback to spot_price = neutral)
        previous_close = spot_price
        try:
            latest_spot = await self.chain_queries.db.fetchval(
                """
                SELECT price FROM spot_prices
                WHERE underlying = $1 AND ts < CURRENT_DATE
                ORDER BY ts DESC LIMIT 1
                """,
                self.config.strategy.underlying,
            )
            if latest_spot:
                previous_close = float(latest_spot)
        except Exception:
            pass

        # Determine direction once — bias filter or simple gap
        if self.config.entry.use_bias_filter:
            direction = await self._bias_direction(previous_close, spot_price)
            if direction is None:
                await self.decision_queries.log_event("bias_filter_no_signal", {"spot": spot_price})
                log.info("bias_filter_no_signal", spot=spot_price)
                return None
        else:
            direction = self.direction_filter.get_direction(spot_price, previous_close)

        # Fetch VIX once for center anchoring (stable throughout the entry window)
        vix_price: float | None = None
        if self.config.entry.use_vix_center:
            try:
                raw = await self.chain_queries.db.fetchval(
                    "SELECT price FROM spot_prices WHERE underlying = '$VIX' ORDER BY ts DESC LIMIT 1"
                )
                if raw:
                    vix_price = float(raw)
                    log.info("vix_fetched", vix=round(vix_price, 2))
            except Exception as e:
                log.warning("vix_fetch_failed", error=str(e))

        # Entry retry loop: re-scan chain each attempt so strikes flex with price movement.
        # Start at fly's composite ask, add price_step each retry to sweeten the offer.
        max_steps = self.config.execution.price_ladder_steps
        price_step = self.config.execution.price_ladder_step
        candidates_logged = False

        for step in range(max_steps):
            # Re-fetch chain + spot each attempt — market may have moved
            try:
                chain_data = await self.schwab.get_option_chain(chain_symbol, expiration)
                spot_price = await self.schwab.get_spot_price(spot_symbol)
            except Exception as e:
                log.error("chain_fetch_failed", step=step, error=str(e))
                break

            quotes = self._parse_chain_to_quotes(chain_data, expiration)
            if not quotes:
                log.warning("empty_chain", step=step)
                break

            candidates = self.builder.build_candidates(quotes, spot_price, direction)

            # Select best — VIX-anchored per width if enabled, else global R/R
            best: ButterflyCandidate | None = None
            if vix_price and self.config.entry.use_vix_center:
                per_width_bests = []
                for width in self.config.strategy.wing_widths:
                    target_center = vix_target_center(
                        vix=vix_price, spot=spot_price,
                        direction=direction, wing_width=width,
                    )
                    width_candidates = [c for c in candidates if c.wing_width == width]
                    w_best = self.selector.select_best(
                        width_candidates,
                        target_center=target_center,
                        center_tolerance=self.config.entry.center_tolerance,
                    )
                    if w_best:
                        per_width_bests.append(w_best)
                if per_width_bests:
                    best = min(per_width_bests,
                               key=lambda c: abs(c.reward_risk - self.config.strategy.rr_target))
                    log.info("vix_center_selected", vix=round(vix_price, 2),
                             width=best.wing_width, center=best.center_strike,
                             rr=round(best.reward_risk, 2))
            if best is None:
                best = self.selector.select_best(candidates)

            # Log candidates to DB on first scan only (avoid noise from retries)
            if not candidates_logged:
                candidates_logged = True
                butterfly_scans_total.labels(underlying=underlying).inc()
                butterfly_candidates_found.labels(underlying=underlying).set(len(candidates))
                scan_time = now_eastern()
                candidate_rows = [
                    {
                        "scan_time": scan_time,
                        "underlying": underlying,
                        "direction": c.direction,
                        "wing_width": c.wing_width,
                        "center_strike": c.center_strike,
                        "lower_strike": c.lower_strike,
                        "upper_strike": c.upper_strike,
                        "cost": c.cost,
                        "max_profit": c.max_profit,
                        "reward_risk": c.reward_risk,
                        "lower_be": c.lower_be,
                        "upper_be": c.upper_be,
                        "distance_from_spot": c.distance_from_spot,
                        "spot_price": c.spot_price,
                        "selected": False,
                    }
                    for c in candidates
                ]
                if best:
                    for row in candidate_rows:
                        if row["center_strike"] == best.center_strike and row["wing_width"] == best.wing_width:
                            row["selected"] = True
                if candidate_rows:
                    await self.candidate_queries.bulk_insert(candidate_rows)

            if not best:
                await self.decision_queries.log_event("no_candidates", {"direction": direction, "spot": spot_price, "step": step})
                log.info("no_candidates", step=step, direction=direction)
                break

            # Price at fly's composite ask + per-step increment to sweeten the offer
            limit_price = round(best.ask + step * price_step, 2)
            log.info("entry_attempt", step=step, center=best.center_strike,
                     width=best.wing_width, ask=best.ask, limit=limit_price)

            fill = await self.order_manager.execute_single_attempt(best, limit_price)
            if fill:
                trade_data = {
                    "underlying": underlying,
                    "trade_date": expiration,
                    "direction": direction,
                    "wing_width": best.wing_width,
                    "center_strike": best.center_strike,
                    "lower_strike": best.lower_strike,
                    "upper_strike": best.upper_strike,
                    "entry_price": fill["fill_price"],
                    "entry_time": fill["fill_time"],
                    "lower_symbol": best.lower_symbol,
                    "center_symbol": best.center_symbol,
                    "upper_symbol": best.upper_symbol,
                }
                trade_id = await self.trade_queries.insert_trade(trade_data)
                await self.risk_engine.record_trade()

                trades_active.labels(underlying=underlying).inc()
                daily_trade_count.labels(underlying=underlying).inc()

                # Emit entry detail metrics for Grafana
                entry_center_strike.labels(underlying=underlying).set(best.center_strike)
                entry_wing_width.labels(underlying=underlying).set(best.wing_width)
                entry_cost.labels(underlying=underlying).set(best.cost)
                entry_max_profit.labels(underlying=underlying).set(best.max_profit)
                entry_lower_be.labels(underlying=underlying).set(best.lower_be)
                entry_upper_be.labels(underlying=underlying).set(best.upper_be)
                if vix_price:
                    entry_vix.labels(underlying=underlying).set(vix_price)
                    entry_expected_move.labels(underlying=underlying).set(_vix_expected_move(vix_price, spot_price))

                record = TradeRecord(
                    trade_id=trade_id,
                    trade_date=expiration,
                    direction=direction,
                    wing_width=best.wing_width,
                    center_strike=best.center_strike,
                    lower_strike=best.lower_strike,
                    upper_strike=best.upper_strike,
                    entry_price=fill["fill_price"],
                    entry_time=fill["fill_time"],
                    lower_symbol=best.lower_symbol,
                    center_symbol=best.center_symbol,
                    upper_symbol=best.upper_symbol,
                )

                await self.decision_queries.log_event("trade_entered", {
                    "trade_id": trade_id,
                    "center": best.center_strike,
                    "width": best.wing_width,
                    "cost": fill["fill_price"],
                    "direction": direction,
                    "entry_step": step,
                })

                log.info("trade_entered", trade_id=trade_id, center=best.center_strike, step=step)
                return record, best

            log.info("entry_step_unfilled", step=step, limit=limit_price, center=best.center_strike)

        await self.decision_queries.log_event("entry_exhausted", {"direction": direction})
        log.warning("entry_exhausted", direction=direction)
        return None

    async def _bias_direction(
        self, prev_close: float, entry_close: float
    ) -> "Literal['CALL', 'PUT'] | None":
        """Fetch today's 1-min bars from Schwab and run BiasScoreFilter."""
        from typing import Literal

        try:
            underlying = self.config.strategy.underlying
            spot_sym = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
            candles = await self.schwab.get_intraday_bars(spot_sym, days_back=1)
            bars: list[MinuteBar] = []
            for c in candles:
                ts_ms = c.get("datetime", 0)
                ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=dt.timezone.utc)
                bars.append(
                    MinuteBar(
                        ts=ts,
                        open=c.get("open", 0.0),
                        high=c.get("high", 0.0),
                        low=c.get("low", 0.0),
                        close=c.get("close", 0.0),
                        volume=int(c.get("volume", 0)),
                    )
                )
            return BiasScoreFilter().get_direction(bars, prev_close, entry_close)
        except Exception as e:
            log.warning("bias_filter_fallback", error=str(e))
            return self.direction_filter.get_direction(entry_close, prev_close)

    def _parse_chain_to_quotes(
        self, chain_data: dict, expiration: dt.date
    ) -> list[OptionQuote]:
        """Parse Schwab chain response into OptionQuote objects."""
        quotes: list[OptionQuote] = []
        underlying = self.config.strategy.underlying

        for option_type, map_key in [("CALL", "callExpDateMap"), ("PUT", "putExpDateMap")]:
            exp_map = chain_data.get(map_key, {})
            for exp_key, strikes in exp_map.items():
                if str(expiration) not in exp_key:
                    continue
                for strike_str, options in strikes.items():
                    for opt in options:
                        quotes.append(
                            OptionQuote(
                                symbol=opt.get("symbol", ""),
                                underlying=underlying,
                                expiration=expiration,
                                strike=float(strike_str),
                                option_type=option_type,
                                bid=opt.get("bid", 0),
                                ask=opt.get("ask", 0),
                                mark=opt.get("mark", 0),
                                last=opt.get("last", 0),
                                volume=opt.get("totalVolume", 0),
                                open_interest=opt.get("openInterest", 0),
                                iv=opt.get("volatility", 0),
                                delta=opt.get("delta", 0),
                                gamma=opt.get("gamma", 0),
                                theta=opt.get("theta", 0),
                                vega=opt.get("vega", 0),
                            )
                        )
        return quotes
