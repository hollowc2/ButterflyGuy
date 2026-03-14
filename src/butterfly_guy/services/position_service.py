"""Position monitoring service — runs state machine on open positions."""

from __future__ import annotations

import asyncio
import datetime as dt

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import daily_pnl, trades_active, trades_total
from butterfly_guy.core.time_utils import get_0dte_expiration, is_market_open, now_eastern
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import SchwabClientWrapper
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
        self.position_manager = PositionManager()
        self.state_machine = ProfitStateMachine(config.profit_management)

    async def monitor_loop(
        self, trade: TradeRecord, candidate: ButterflyCandidate
    ) -> None:
        """Monitor position every 10s, evaluate state machine, trigger exit if needed."""
        self.position_manager.reset(trade.entry_price)
        self.state_machine.reset()
        poll_interval = 10

        log.info("position_monitor_started", trade_id=trade.trade_id)

        while is_market_open():
            try:
                # Fetch latest chain for position valuation
                expiration = get_0dte_expiration()
                chain_data = await self.schwab.get_spx_option_chain(expiration)
                quotes = self._extract_quotes(chain_data, expiration, candidate)

                # Update position
                pos_state = self.position_manager.update_position_value(candidate, quotes)

                # Evaluate state machine
                signal = self.state_machine.evaluate(pos_state)

                if signal:
                    log.info(
                        "exit_signal",
                        reason=signal.reason,
                        urgency=signal.urgency,
                        value=pos_state.current_value,
                    )

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

                    await self.risk_engine.record_pnl(pnl)
                    trades_active.dec()
                    trades_total.labels(
                        direction=trade.direction,
                        outcome="win" if pnl > 0 else "loss",
                    ).inc()
                    daily_pnl.inc(pnl)

                    await self.decision_queries.log_event("trade_exited", {
                        "trade_id": trade.trade_id,
                        "exit_reason": signal.reason,
                        "pnl": pnl,
                        "peak_value": pos_state.peak_value,
                    })

                    log.info("trade_exited", trade_id=trade.trade_id, pnl=pnl, reason=signal.reason)
                    return

            except Exception as e:
                log.error("monitor_error", error=str(e))

            await asyncio.sleep(poll_interval)

        # Market closed — force exit at whatever the current value is
        log.warning("market_closed_force_exit", trade_id=trade.trade_id)
        current_value = 0.0
        peak = 0.0
        try:
            expiration = get_0dte_expiration()
            chain_data = await self.schwab.get_spx_option_chain(expiration)
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
        await self.risk_engine.record_pnl(pnl)
        trades_active.dec()
        trades_total.labels(direction=trade.direction, outcome="win" if pnl > 0 else "loss").inc()
        daily_pnl.inc(pnl)
        log.info("eod_force_exit_complete", trade_id=trade.trade_id, pnl=pnl)

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
