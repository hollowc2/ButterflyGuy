"""Position monitoring service — runs state machine on open positions."""

from __future__ import annotations

import asyncio
import datetime as dt

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import daily_pnl, trades_active, trades_total
from butterfly_guy.core.time_utils import get_0dte_expiration, is_market_open, now_eastern
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import SCHWAB_CHAIN_SYMBOLS, SchwabClientWrapper
from butterfly_guy.db.queries import DecisionQueries, TradeQueries
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.risk.risk_engine import RiskEngine

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
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.order_manager = order_manager
        self.risk_engine = risk_engine
        self.trade_queries = trade_queries
        self.decision_queries = decision_queries
        self.position_manager = PositionManager(config.strategy.underlying)
        self.state_machine = ProfitStateMachine(config.profit_management)
        self._last_profit_state: str | None = None

    async def monitor_loop(
        self, trade: TradeRecord, candidate: ButterflyCandidate
    ) -> None:
        """Monitor position every 10s, evaluate state machine, trigger exit if needed."""
        self.position_manager.reset(trade.entry_price)
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

                    exit_price = fill["fill_price"] if fill else 0.0
                    exit_time = fill["fill_time"] if fill else now_eastern()
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
                        "spread_bid": fill.get("spread_bid") if fill else None,
                        "spread_mark": fill.get("spread_mark") if fill else None,
                        "spread_ask": fill.get("spread_ask") if fill else None,
                        "fill_price": exit_price,
                        "pnl": pnl,
                        "peak_value": pos_state.peak_value,
                        "forced": fill.get("forced", False) if fill else True,
                    }, underlying=self.config.strategy.underlying)

                    log.info("trade_exited", trade_id=trade.trade_id, pnl=pnl, reason=signal.reason)

            except Exception as e:
                log.error("monitor_error", error=str(e))

            if not exited:
                await asyncio.sleep(poll_interval)

        if exited:
            return

        # Market closed — force exit at whatever the current value is
        log.warning("market_closed_force_exit", trade_id=trade.trade_id)
        current_value = 0.0
        peak = 0.0
        try:
            expiration = get_0dte_expiration()
            chain_data = await self.schwab.get_option_chain(
                        SCHWAB_CHAIN_SYMBOLS.get(self.config.strategy.underlying, self.config.strategy.underlying),
                        expiration,
                    )
            quotes = self._extract_quotes(chain_data, expiration, candidate)
            pos_state = self.position_manager.update_position_value(candidate, quotes)
            current_value = pos_state.current_value
            peak = pos_state.peak_value
        except Exception as e:
            log.error("eod_valuation_failed", error=str(e))

        fill = await self.order_manager.execute_exit(candidate, current_value, trade.quantity)
        exit_price = fill["fill_price"] if fill else 0.0
        exit_time = fill["fill_time"] if fill else now_eastern()
        pnl = exit_price - trade.entry_price

        await self.trade_queries.close_trade(
            trade.trade_id,
            exit_price,
            exit_time,
            "eod_force_exit",
            pnl,
            peak,
        )
        await self._record_exit_metrics(pnl, trade)
        log.info("eod_force_exit_complete", trade_id=trade.trade_id, pnl=pnl)

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
        """Extract relevant quotes for position valuation."""
        quotes: dict[float, OptionQuote] = {}
        target_strikes = {candidate.lower_strike, candidate.center_strike, candidate.upper_strike}
        map_key = "callExpDateMap" if candidate.direction == "CALL" else "putExpDateMap"

        exp_map = chain_data.get(map_key, {})
        for exp_key, strikes in exp_map.items():
            if str(expiration) not in exp_key:
                continue
            for strike_str, options in strikes.items():
                strike = float(strike_str)
                if strike in target_strikes and options:
                    opt = options[0]
                    quotes[strike] = OptionQuote(
                        symbol=opt.get("symbol", ""),
                        underlying=self.config.strategy.underlying,
                        expiration=expiration,
                        strike=strike,
                        option_type=candidate.direction,
                        bid=opt.get("bid", 0),
                        ask=opt.get("ask", 0),
                        mark=opt.get("mark", 0),
                    )
        return quotes
