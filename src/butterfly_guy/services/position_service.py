"""Position monitoring service — runs state machine on open positions."""

from __future__ import annotations

import asyncio
import datetime as dt

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    daily_pnl,
    position_peak_value,
    position_pnl,
    position_value,
    trades_active,
    trades_total,
)
from butterfly_guy.core.time_utils import (
    EASTERN,
    MARKET_CLOSE,
    MARKET_OPEN,
    get_0dte_expiration,
    is_market_open,
    now_eastern,
)
from butterfly_guy.data.chain_utils import iter_chain_options
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import (
    SCHWAB_CHAIN_SYMBOLS,
    SCHWAB_SPOT_SYMBOLS,
    SchwabClientWrapper,
)
from butterfly_guy.db.queries import (
    ChainQueries,
    DecisionQueries,
    MonitoringLegQueries,
    TentQueries,
    TradeQueries,
)
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.position.position_manager import PositionManager, fly_settlement_value
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.reports.live_performance import trade_pnl_dollars
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.trade_chart import ButterflyChartSpec, summarize_exit_chart
from butterfly_guy.strategy.exit_mark_parity import (
    DB_EXIT_PARITY_MAX_LAG_SECONDS,
    build_exit_mark_parity,
)

log = get_logger(__name__)


def final_regular_session_close_from_candles(
    candles: list[dict],
    session_date: dt.date,
) -> tuple[dt.datetime, float] | None:
    """Return the latest Schwab 1-minute close in the regular session."""
    closes: list[tuple[dt.datetime, float]] = []
    for candle in candles:
        ts_ms = candle.get("datetime")
        close = candle.get("close")
        if ts_ms is None or close is None:
            continue
        ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=dt.timezone.utc).astimezone(EASTERN)
        if ts.date() != session_date:
            continue
        if MARKET_OPEN <= ts.time() <= MARKET_CLOSE:
            closes.append((ts, float(close)))

    if not closes:
        return None

    closes.sort(key=lambda item: item[0])
    return closes[-1]


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
        chain_queries: ChainQueries,
        monitoring_leg_queries: MonitoringLegQueries | None,
        tent_queries: TentQueries,
        notifier: DiscordNotifier | None = None,
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.order_manager = order_manager
        self.risk_engine = risk_engine
        self.trade_queries = trade_queries
        self.decision_queries = decision_queries
        self.chain_queries = chain_queries
        self.monitoring_leg_queries = monitoring_leg_queries
        self.tent_queries = tent_queries
        self.notifier = notifier
        self.position_manager = PositionManager(
            config.strategy.underlying,
            config.profit_management,
        )
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
        self._last_persisted_peak = (
            recovered_peak if (recovered_peak and recovered_peak > 0) else trade.entry_price
        )
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
                        SCHWAB_CHAIN_SYMBOLS.get(
                            self.config.strategy.underlying,
                            self.config.strategy.underlying,
                        ),
                        expiration,
                    )
                chain_fetched_at = now_eastern()
                quotes = self._extract_quotes(chain_data, expiration, candidate)

                # Update position
                pos_state = self.position_manager.update_position_value(candidate, quotes)
                if trade.entry_time is not None:
                    pos_state.position_age_minutes = max(
                        0.0,
                        (chain_fetched_at - trade.entry_time.astimezone(EASTERN)).total_seconds()
                        / 60.0,
                    )

                if self.monitoring_leg_queries is not None:
                    await self._record_monitoring_leg_quotes(
                        trade=trade,
                        candidate=candidate,
                        expiration=expiration,
                        quotes=quotes,
                        ts=chain_fetched_at,
                        pos_state=pos_state,
                        spot_price=_chain_spot_price(chain_data),
                    )

                if pos_state.peak_update_rejected:
                    await self.decision_queries.log_event(
                        "peak_update_rejected",
                        {
                            "trade_id": trade.trade_id,
                            "reason": pos_state.peak_rejection_reason,
                            "raw_mark": pos_state.current_value,
                            "accepted_peak": pos_state.peak_value,
                            "pending_peak": pos_state.pending_peak_value,
                            "pending_confirmation_count": (
                                pos_state.pending_peak_confirmation_count
                            ),
                            "spread_bid": pos_state.spread_bid,
                            "spread_ask": pos_state.spread_ask,
                            "bid_to_mark_ratio": pos_state.bid_to_mark_ratio,
                            "max_leg_spread_to_mark_ratio": (
                                pos_state.max_leg_spread_to_mark_ratio
                            ),
                            "max_leg_spread_abs": pos_state.max_leg_spread_abs,
                        },
                        underlying=self.config.strategy.underlying,
                    )

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

                    exit_mark_parity = await self._exit_mark_parity_report(
                        candidate=candidate,
                        quotes=quotes,
                        pos_state=pos_state,
                        exit_reason=signal.reason,
                        chain_fetched_at=chain_fetched_at,
                    )
                    exit_mark_parity["trade_id"] = trade.trade_id
                    await self.decision_queries.log_event(
                        "exit_mark_parity",
                        exit_mark_parity,
                        underlying=self.config.strategy.underlying,
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
                        "exit_mark_parity": exit_mark_parity,
                    }, underlying=self.config.strategy.underlying)

                    fill = await self.order_manager.execute_exit(
                        candidate,
                        pos_state.current_value,
                        trade.quantity,
                        exit_reason=signal.reason,
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
                        exit_ladder_steps = fill.get("ladder_steps", [])

                        await self.trade_queries.close_trade(
                            trade.trade_id,
                            exit_price,
                            exit_time,
                            signal.reason,
                            pnl,
                            pos_state.peak_value,
                            metadata={
                                "exit_ladder_steps": exit_ladder_steps,
                                "exit_signal_reason": signal.reason,
                                "exit_mark_at_signal": pos_state.current_value,
                                "exit_mark_parity": exit_mark_parity,
                            },
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
                        await self.decision_queries.log_event("exit_ladder_trace", {
                            "trade_id": trade.trade_id,
                            "exit_reason": signal.reason,
                            "entry_price": trade.entry_price,
                            "fill_price": exit_price,
                            "peak_value": pos_state.peak_value,
                            "exit_ladder_steps": exit_ladder_steps,
                            "forced": fill.get("forced", False),
                            "exit_mark_parity": exit_mark_parity,
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
                                    quantity=trade.quantity,
                                )
                            except Exception as e:
                                log.warning("notify_exit_failed", error=str(e))

                        log.info(
                            "trade_exited",
                            trade_id=trade.trade_id,
                            pnl=pnl,
                            reason=signal.reason,
                        )

            except Exception as e:
                log.error("monitor_error", error=str(e))

            if not exited:
                await asyncio.sleep(poll_interval)

        if exited:
            return

        # Market closed — XSP/SPX/NDX are cash-settled; no exit order needed.
        # Use the underlying index close to compute the actual cash-settlement value.
        log.info("market_closed_cash_settle", trade_id=trade.trade_id)
        settlement_value = 0.0
        settlement_spot: float | None = None
        settlement_source = "unknown"
        settlement_ts: dt.datetime | None = None
        peak = max(self._last_persisted_peak, trade.peak_value or 0.0)
        try:
            settlement_spot, settlement_source, settlement_ts = await self._settlement_spot_price(
                self.config.strategy.underlying,
                trade.trade_date,
            )
            settlement_value = fly_settlement_value(candidate, settlement_spot)
        except Exception as e:
            log.error("eod_settlement_valuation_failed", error=str(e))
            settlement_source = "option_chain_mark_fallback"
            settlement_ts = None
            try:
                expiration = get_0dte_expiration()
                chain_data = await self.schwab.get_option_chain(
                    SCHWAB_CHAIN_SYMBOLS.get(
                        self.config.strategy.underlying,
                        self.config.strategy.underlying,
                    ),
                    expiration,
                )
                settlement_spot = _chain_spot_price(chain_data)
                quotes = self._extract_quotes(chain_data, expiration, candidate)
                pos_state = self.position_manager.update_position_value(candidate, quotes)
                settlement_value = pos_state.current_value
                peak = pos_state.peak_value
            except Exception as fallback_error:
                log.error("eod_valuation_failed", error=str(fallback_error))

        pnl = settlement_value - trade.entry_price
        await self.trade_queries.close_trade(
            trade.trade_id,
            settlement_value,
            now_eastern(),
            "cash_settled",
            pnl,
            peak,
            metadata={
                "exit_ladder_steps": [],
                "exit_signal_reason": "cash_settled",
                "exit_mark_at_signal": settlement_value,
                "settlement_source": settlement_source,
                "settlement_spot": settlement_spot,
                "settlement_spot_time": settlement_ts.isoformat() if settlement_ts else None,
            },
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
                    quantity=trade.quantity,
                )
            except Exception as e:
                log.warning("notify_exit_failed", error=str(e))

        log.info(
            "cash_settle_complete",
            trade_id=trade.trade_id,
            settlement_value=settlement_value,
            pnl=pnl,
        )

    async def _settlement_spot_price(
        self,
        underlying: str,
        session_date: dt.date,
    ) -> tuple[float, str, dt.datetime | None]:
        """Use Schwab's final regular-session 1-minute close for cash settlement."""
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        candles = await self.schwab.get_intraday_bars(spot_symbol, days_back=1)
        final_close = final_regular_session_close_from_candles(candles, session_date)
        if final_close is not None:
            close_ts, close_price = final_close
            log.info(
                "cash_settlement_final_1m_close",
                underlying=underlying,
                spot=close_price,
                bar_time=close_ts.isoformat(),
            )
            return close_price, "schwab_final_regular_session_1m_close", close_ts

        spot_price = await self.schwab.get_spot_price(spot_symbol)
        if spot_price is None:
            raise ValueError(f"missing_spot_price_for_{underlying}")
        log.warning(
            "cash_settlement_spot_quote_fallback",
            underlying=underlying,
            spot=spot_price,
        )
        return spot_price, "schwab_spot_quote_fallback", None

    async def _record_exit_metrics(self, pnl: float, trade: TradeRecord) -> None:
        """Record trade exit metrics and update risk engine."""
        underlying = self.config.strategy.underlying
        pnl_dollars = trade_pnl_dollars(pnl, trade.quantity)
        await self.risk_engine.record_pnl(pnl_dollars)

        # Update prometheus metrics
        trades_active.labels(underlying=underlying).set(0)
        position_value.labels(underlying=underlying).set(0)
        position_peak_value.labels(underlying=underlying).set(0)
        position_pnl.labels(underlying=underlying).set(0)
        trades_total.labels(
            underlying=underlying,
            direction=trade.direction,
            outcome="win" if pnl > 0 else "loss",
        ).inc()
        daily_pnl.labels(underlying=underlying).inc(pnl_dollars)

    async def send_pending_eod_charts(self, trade_date: dt.date) -> int:
        """Send full-session EOD charts for closed trades after market close."""
        if not self.notifier:
            return 0

        pending = await self.trade_queries.get_trades_pending_eod_chart(
            trade_date, self.config.strategy.underlying
        )
        sent = 0
        for row in pending:
            try:
                chart_png, tent_hit = await self._build_exit_chart_from_row(row, full_session=True)
                if chart_png is None:
                    continue
                trade_date_val = row["trade_date"]
                if isinstance(trade_date_val, dt.datetime):
                    trade_date_val = trade_date_val.date()
                await self.notifier.notify_eod_chart(
                    trade_id=row["id"],
                    underlying=row["underlying"],
                    trade_date=trade_date_val,
                    direction=row["direction"],
                    exit_reason=row.get("exit_reason") or "unknown",
                    pnl=float(row.get("pnl") or 0),
                    quantity=int(row.get("quantity") or 1),
                    tent_hit=tent_hit,
                    chart_png=chart_png,
                )
                await self.trade_queries.mark_eod_chart_sent(row["id"])
                sent += 1
                log.info("eod_chart_sent", trade_id=row["id"], trade_date=str(trade_date))
            except Exception as e:
                log.warning("eod_chart_send_failed", trade_id=row["id"], error=str(e))
        return sent

    async def _build_exit_chart_from_row(
        self,
        row: dict,
        *,
        full_session: bool,
    ) -> tuple[bytes | None, bool | None]:
        entry_time = row.get("entry_time")
        if entry_time is None:
            return None, None
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=dt.timezone.utc)

        metadata = row.get("metadata") or {}
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)
        entry_spot = metadata.get("entry_spot")

        underlying = row["underlying"]
        spot_sym = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        candles = await self.schwab.get_intraday_bars(spot_sym, days_back=1)
        spec = ButterflyChartSpec(
            underlying=underlying,
            direction=row["direction"],
            lower_strike=float(row["lower_strike"]),
            center_strike=float(row["center_strike"]),
            upper_strike=float(row["upper_strike"]),
            wing_width=int(row["wing_width"]),
            entry_price=float(row["entry_price"]),
            entry_time=entry_time,
            entry_spot=float(entry_spot) if entry_spot is not None else None,
            exit_time=row.get("exit_time"),
            exit_reason=row.get("exit_reason"),
        )
        return summarize_exit_chart(spec, candles, full_session=full_session)

    async def _exit_mark_parity_report(
        self,
        *,
        candidate: ButterflyCandidate,
        quotes: dict[float, OptionQuote],
        pos_state,
        exit_reason: str,
        chain_fetched_at: dt.datetime,
    ) -> dict[str, object]:
        """Compare live Schwab exit marks with the nearest DB collector snapshot."""
        expiration = get_0dte_expiration()
        underlying = self.config.strategy.underlying
        at_utc = chain_fetched_at.astimezone(dt.timezone.utc)
        snapshot = await self.chain_queries.get_nearest_snapshot_chain(
            underlying,
            expiration,
            at_utc,
            max_lag_seconds=DB_EXIT_PARITY_MAX_LAG_SECONDS,
        )
        return build_exit_mark_parity(
            candidate=candidate,
            live_quotes=quotes,
            live_fly_mark=pos_state.current_value,
            live_peak=pos_state.peak_value,
            live_drawdown_pct=round(pos_state.drawdown_from_peak * 100, 1),
            exit_reason=exit_reason,
            live_spread_bid=pos_state.spread_bid,
            snapshot=snapshot,
            underlying=underlying,
            expiration=expiration,
        )

    async def _record_monitoring_leg_quotes(
        self,
        *,
        trade: TradeRecord,
        candidate: ButterflyCandidate,
        expiration: dt.date,
        quotes: dict[float, OptionQuote],
        ts: dt.datetime,
        pos_state,
        spot_price: float | None,
    ) -> None:
        """Persist the three live-polled legs so DB replay can match monitor timing."""
        rows = []
        for strike in (candidate.lower_strike, candidate.center_strike, candidate.upper_strike):
            quote = quotes.get(strike)
            if quote is None:
                continue
            rows.append(
                {
                    "strike": quote.strike,
                    "option_type": quote.option_type,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "mark": quote.mark,
                    "symbol": quote.symbol,
                }
            )
        try:
            await self.monitoring_leg_queries.insert_quotes(
                ts=ts,
                trade_id=trade.trade_id,
                underlying=self.config.strategy.underlying,
                expiration=expiration,
                quotes=rows,
                spot_price=spot_price,
                fly_mark=pos_state.current_value,
                peak_value=pos_state.peak_value,
                drawdown_pct=round(pos_state.drawdown_from_peak * 100, 4),
            )
        except Exception as e:
            log.warning(
                "monitoring_leg_quote_persist_failed",
                trade_id=trade.trade_id,
                error=str(e),
            )

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
            for strike, _, opt in iter_chain_options(
                chain_data, expiration, direction=candidate.direction
            )
            if strike in target_strikes
        }


def _chain_spot_price(chain_data: dict) -> float | None:
    for key in ("underlyingPrice", "underlying_price", "lastPrice", "last"):
        value = chain_data.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None
