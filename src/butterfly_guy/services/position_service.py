"""Position monitoring service — runs state machine on open positions."""

from __future__ import annotations

import asyncio
import datetime as dt

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import daily_pnl, trades_active, trades_total
from butterfly_guy.core.time_utils import get_0dte_expiration, is_market_open, now_eastern
from butterfly_guy.data.chain_utils import iter_chain_options
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import SCHWAB_CHAIN_SYMBOLS, SchwabClientWrapper
from butterfly_guy.db.queries import DecisionQueries, TentQueries, TradeQueries
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger(__name__)


class PositionService:
    """Monitors open positions and manages exits via the profit state machine."""

    def __init__(
        self,
        config: AppConfig,
        schwab: SchwabClientWrapper,
        order_manager: OrderManager,
        risk_engine: RiskEngine,
        trade_queries: TradeQueries,
        decision_queries: DecisionQueries,
        tent_queries: TentQueries,
        notifier: DiscordNotifier | None = None,
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.order_manager = order_manager
        self.risk_engine = risk_engine
        self.trade_queries = trade_queries
        self.decision_queries = decision_queries
        self.tent_queries = tent_queries
        self.notifier = notifier
        self.position_manager = PositionManager(config.strategy.underlying)
        self.state_machine = ProfitStateMachine(config.profit_management)
        self._last_profit_state: str | None = None
        self._last_persisted_peak: float = 0.0

    async def monitor_loop(
        self,
        trade: TradeRecord,
        candidate: ButterflyCandidate,
        recovered_peak: float | None = None,
    ) -> None:
        """Monitor position every 10s, evaluate state machine, trigger exit if needed."""
        self.position_manager.reset(trade.entry_price, peak_value=recovered_peak)
        self._last_persisted_peak = recovered_peak if (recovered_peak and recovered_peak > 0) else trade.entry_price
        self.state_machine.reset()
        self._last_profit_state = None
        poll_interval = 2

        log.info("position_monitor_started", trade_id=trade.trade_id)

        exited = False
        while is_market_open() and not exited:
            try:
                # Fetch latest chain for position valuation
                expiration = get_0dte_expiration()
                chain_data = await self.schwab.get_option_chain(
                        SCHWAB_CHAIN_SYMBOLS.get(self.config.strategy.underlying, self.config.strategy.underlying),
                        expiration,
                    )
                quotes = self._extract_quotes(chain_data, expiration, candidate)

                # Update position
                pos_state = self.position_manager.update_position_value(candidate, quotes)

                # Persist new peak to DB so it survives a restart
                if pos_state.peak_value > self._last_persisted_peak:
                    self._last_persisted_peak = pos_state.peak_value
                    await self.trade_queries.update_peak_value(trade.trade_id, pos_state.peak_value)

                # Persist tent boundaries for Grafana visualization
                await self.tent_queries.insert(
                    ts=now_eastern(),
                    underlying=self.config.strategy.underlying,
                    lower_tent=pos_state.lower_tent,
                    upper_tent=pos_state.upper_tent,
                )

                # Evaluate state machine
                signal = self.state_machine.evaluate(pos_state)

                # Log profit state transitions
                current_profit_state = self.state_machine.state.name
                if current_profit_state != self._last_profit_state:
                    await self.decision_queries.log_event("profit_state_transition", {
                        "trade_id": trade.trade_id,
                        "from": self._last_profit_state,
                        "to": current_profit_state,
                        "mark_value": pos_state.current_value,
                        "peak_value": pos_state.peak_value,
                        "pnl": pos_state.pnl,
                        "regime": pos_state.time_regime,
                    }, underlying=self.config.strategy.underlying)
                    self._last_profit_state = current_profit_state

                if signal:
                    log.info(
                        "exit_signal",
                        reason=signal.reason,
                        urgency=signal.urgency,
                        value=pos_state.current_value,
                    )

                    await self.decision_queries.log_event("exit_signal_fired", {
                        "trade_id": trade.trade_id,
                        "reason": signal.reason,
                        "urgency": signal.urgency,
                        "mark_value": pos_state.current_value,
                        "peak_value": pos_state.peak_value,
                        "drawdown_pct": round(pos_state.drawdown_from_peak * 100, 1),
                        "regime": pos_state.time_regime,
                        "entry_price": pos_state.entry_price,
                    }, underlying=self.config.strategy.underlying)

                    fill = await self.order_manager.execute_exit(
                        candidate, pos_state.current_value, trade.quantity
                    )

                    if fill is None:
                        # Exit order failed — keep position OPEN and retry next iteration
                        log.error(
                            "exit_order_failed_retrying",
                            trade_id=trade.trade_id,
                            reason=signal.reason,
                            current_value=pos_state.current_value,
                        )
                        await self.decision_queries.log_event("exit_order_failed", {
                            "trade_id": trade.trade_id,
                            "reason": signal.reason,
                            "current_value": pos_state.current_value,
                        }, underlying=self.config.strategy.underlying)
                        if self.notifier:
                            await self.notifier._post(
                                f"WARNING: EXIT ORDER FAILED for trade {trade.trade_id} "
                                f"({signal.reason}). Position still OPEN in Schwab. Retrying."
                            )
                        # Do NOT set exited=True — loop continues and retries on next signal
                    else:
                        exit_price = fill["fill_price"]
                        exit_time = fill["fill_time"]
                        pnl = exit_price - trade.entry_price

                        await self.trade_queries.close_trade(
                            trade.trade_id,
                            exit_price,
                            exit_time,
                            signal.reason,
                            pnl,
                            pos_state.peak_value,
                        )

                        await self._record_exit_metrics(pnl, trade)

                        # Mark exited before logging so any downstream exception
                        # cannot cause the loop to re-trigger the exit path.
                        exited = True

                        await self.decision_queries.log_event("trade_exited", {
                            "trade_id": trade.trade_id,
                            "exit_reason": signal.reason,
                            "entry_price": trade.entry_price,
                            "mark_at_signal": pos_state.current_value,
                            "spread_bid": fill.get("spread_bid"),
                            "spread_mark": fill.get("spread_mark"),
                            "spread_ask": fill.get("spread_ask"),
                            "fill_price": exit_price,
                            "pnl": pnl,
                            "peak_value": pos_state.peak_value,
                            "peak_bid": pos_state.peak_bid,
                            "bid_to_mark_at_exit": pos_state.bid_to_mark_ratio,
                            "forced": fill.get("forced", False),
                        }, underlying=self.config.strategy.underlying)

                        if self.notifier:
                            try:
                                await self.notifier.notify_exit(
                                    trade_id=trade.trade_id,
                                    underlying=self.config.strategy.underlying,
                                    direction=trade.direction,
                                    exit_reason=signal.reason,
                                    entry_price=trade.entry_price,
                                    exit_price=exit_price,
                                    pnl=pnl,
                                    peak_value=pos_state.peak_value,
                                    entry_time=trade.entry_time,
                                )
                            except Exception as e:
                                log.warning("notify_exit_failed", error=str(e))

                        log.info("trade_exited", trade_id=trade.trade_id, pnl=pnl, reason=signal.reason)

            except Exception as e:
                log.error("monitor_error", error=str(e))

            if not exited:
                await asyncio.sleep(poll_interval)

        if exited:
            return

        # Market closed — XSP/SPX/NDX are cash-settled; no exit order needed.
        # Record the final mark price as the settlement value.
        log.info("market_closed_cash_settle", trade_id=trade.trade_id)
        settlement_value = 0.0
        peak = 0.0
        try:
            expiration = get_0dte_expiration()
            chain_data = await self.schwab.get_option_chain(
                        SCHWAB_CHAIN_SYMBOLS.get(self.config.strategy.underlying, self.config.strategy.underlying),
                        expiration,
                    )
            quotes = self._extract_quotes(chain_data, expiration, candidate)
            pos_state = self.position_manager.update_position_value(candidate, quotes)
            settlement_value = pos_state.current_value
            peak = pos_state.peak_value
        except Exception as e:
            log.error("eod_valuation_failed", error=str(e))

        pnl = settlement_value - trade.entry_price
        await self.trade_queries.close_trade(
            trade.trade_id,
            settlement_value,
            now_eastern(),
            "cash_settled",
            pnl,
            peak,
        )
        await self._record_exit_metrics(pnl, trade)

        if self.notifier:
            try:
                await self.notifier.notify_exit(
                    trade_id=trade.trade_id,
                    underlying=self.config.strategy.underlying,
                    direction=trade.direction,
                    exit_reason="cash_settled",
                    entry_price=trade.entry_price,
                    exit_price=settlement_value,
                    pnl=pnl,
                    peak_value=peak,
                    entry_time=trade.entry_time,
                )
            except Exception as e:
                log.warning("notify_exit_failed", error=str(e))

        log.info("cash_settle_complete", trade_id=trade.trade_id, settlement_value=settlement_value, pnl=pnl)

    async def _record_exit_metrics(self, pnl: float, trade: TradeRecord) -> None:
        """Record trade exit metrics and update risk engine."""
        underlying = self.config.strategy.underlying
        await self.risk_engine.record_pnl(pnl)

        # Update prometheus metrics
        trades_active.labels(underlying=underlying).set(0)
        trades_total.labels(
            underlying=underlying,
            direction=trade.direction,
            outcome="win" if pnl > 0 else "loss",
        ).inc()
        daily_pnl.labels(underlying=underlying).inc(pnl)

    def _extract_quotes(
        self,
        chain_data: dict,
        expiration: dt.date,
        candidate: ButterflyCandidate,
    ) -> dict[float, OptionQuote]:
        """Extract the three butterfly leg quotes from the chain for position valuation."""
        target_strikes = {candidate.lower_strike, candidate.center_strike, candidate.upper_strike}
        underlying = self.config.strategy.underlying
        return {
            strike: OptionQuote(
                symbol=opt.get("symbol", ""),
                underlying=underlying,
                expiration=expiration,
                strike=strike,
                option_type=candidate.direction,
                bid=opt.get("bid", 0),
                ask=opt.get("ask", 0),
                mark=opt.get("mark", 0),
                # Schwab returns null/-999 for index options (SPX, NDX);
                # treat as 0 here and let compute_tent_boundaries impute via BS inverse
                iv=float(opt.get("volatility") or 0.0),
            )
            for strike, _, opt in iter_chain_options(chain_data, expiration, direction=candidate.direction)
            if strike in target_strikes
        }
