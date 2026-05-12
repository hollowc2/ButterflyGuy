"""Trade service — orchestrates entry flow."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from butterfly_guy.backtest.data_loader import MinuteBar
from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    butterfly_candidates_found,
    butterfly_scans_total,
    daily_trade_count,
    entry_center_strike,
    entry_cost,
    entry_expected_move,
    entry_lower_be,
    entry_max_profit,
    entry_upper_be,
    entry_vix,
    entry_wing_width,
    trades_active,
)
from butterfly_guy.core.time_utils import (
    EASTERN,
    MARKET_OPEN,
    get_0dte_expiration,
    now_eastern,
    time_in_window,
)
from butterfly_guy.data.chain_utils import iter_chain_options
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote, TradeRecord
from butterfly_guy.data.schwab_client import (
    SCHWAB_CHAIN_SYMBOLS,
    SCHWAB_SPOT_SYMBOLS,
    SchwabClientWrapper,
)
from butterfly_guy.db.queries import CandidateQueries, ChainQueries, DecisionQueries, TradeQueries
from butterfly_guy.execution.order_manager import OrderManager
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.strategy.bias_filter import BiasScoreFilter
from butterfly_guy.strategy.butterfly_builder import (
    ButterflyBuilder,
    resolve_wing_widths_for_vix,
    vix_target_center,
)
from butterfly_guy.strategy.butterfly_builder import vix_expected_move as _vix_expected_move
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.direction_filter import DirectionFilter
from butterfly_guy.strategy.gap_regime_filter import GapRegimeFilter
from butterfly_guy.strategy.regime_classifier import Regime

log = get_logger(__name__)


def _session_open_from_intraday_candles(
    candles: list[dict],
    session_date: dt.date,
) -> float | None:
    """Return the first regular-session open for the requested Eastern date."""
    regular_session: list[tuple[dt.datetime, float]] = []
    for candle in candles:
        open_price = candle.get("open")
        ts_ms = candle.get("datetime")
        if open_price is None or ts_ms is None:
            continue

        ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=dt.timezone.utc)
        ts_et = ts.astimezone(EASTERN)
        if ts_et.date() != session_date or ts_et.time() < MARKET_OPEN:
            continue

        regular_session.append((ts, float(open_price)))

    if not regular_session:
        return None
    regular_session.sort(key=lambda item: item[0])
    return regular_session[0][1]


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
        notifier: DiscordNotifier | None = None,
        regime: Regime = Regime.UNKNOWN,
        gap_regime_filter: GapRegimeFilter | None = None,
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
        self.notifier = notifier
        self.regime = regime
        self.gap_regime_filter = gap_regime_filter

    async def attempt_entry(self) -> tuple[TradeRecord, ButterflyCandidate] | None:
        """Full entry flow from eligibility checks through entry fill."""
        # Time window check first — cheapest guard, avoids unnecessary API calls outside window
        if not time_in_window(
            self.config.entry.start_time,
            self.config.entry.end_time,
            self.config.entry.timezone,
        ):
            return None

        # Fetch account balances for PDT floor and buying power checks (live trading only)
        account_value: float | None = None
        buying_power: float | None = None
        if not self.config.execution.paper_trading:
            try:
                balances = await self.schwab.get_account_balances()
                account_value = balances["liquidation_value"]
                buying_power = balances["buying_power"]
                log.info(
                    "account_balances_fetched",
                    account_value=round(account_value, 2),
                    buying_power=round(buying_power, 2),
                )
            except Exception as e:
                log.error("account_balance_fetch_failed", error=str(e))
                if self.config.risk.fail_safe_on_balance_error:
                    await self.decision_queries.log_event(
                        "entry_blocked",
                        {"reason": "balance_fetch_failed", "error": str(e)},
                        underlying=self.config.strategy.underlying,
                    )
                    return None

        # Risk check (includes account floor, weekly loss, consecutive loss checks)
        allowed, reason = await self.risk_engine.can_trade(
            account_value=account_value,
            buying_power=buying_power,
        )
        if not allowed:
            await self.decision_queries.log_event(
                "entry_blocked",
                {"reason": reason},
                underlying=self.config.strategy.underlying,
            )
            log.info("entry_blocked", reason=reason)
            return None

        expiration = get_0dte_expiration()
        underlying = self.config.strategy.underlying
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(underlying, underlying)

        # Get initial spot price for chain scanning and VIX anchoring
        try:
            spot_price = await self.schwab.get_spot_price(spot_symbol)
        except Exception as e:
            log.error("spot_fetch_failed", error=str(e))
            return None

        # Previous close from daily_bars (official close, not last spot snapshot)
        previous_close = spot_price
        try:
            row = await self.chain_queries.db.pool.fetchval(
                """
                SELECT close FROM daily_bars
                WHERE underlying = $1 AND date < CURRENT_DATE
                ORDER BY date DESC LIMIT 1
                """,
                self.config.strategy.underlying,
            )
            if row:
                previous_close = float(row)
        except Exception:
            pass

        # Opening price for gap direction — first regular-session 1-min bar.
        # Stored spot snapshots can be stale at 09:30, so do not guess if
        # Schwab's intraday open is unavailable.
        session_open = await self._session_open_price()
        if session_open is None:
            await self.decision_queries.log_event(
                "entry_blocked",
                {"reason": "session_open_unavailable"},
                underlying=underlying,
            )
            log.info("entry_blocked", reason="session_open_unavailable")
            return None
        open_price = session_open

        log.info(
            "direction_inputs",
            open_price=round(open_price, 2),
            previous_close=round(previous_close, 2),
            spot_price=round(spot_price, 2),
            gap_pct=round((open_price - previous_close) / previous_close * 100, 3),
        )

        direction = None

        if self.gap_regime_filter:
            override, skip_reason = self.gap_regime_filter.apply(
                open_price, previous_close, self.regime
            )
            if skip_reason:
                await self.decision_queries.log_event(
                    "gap_regime_skip",
                    {"reason": skip_reason, "open": open_price},
                    underlying=underlying,
                )
                log.info("gap_regime_skip", reason=skip_reason)
                return None
            if override:
                direction = override
                log.info("gap_regime_override", direction=direction)

        if direction is None:
            # Determine direction once — bias filter or simple gap
            if self.config.entry.use_bias_filter:
                direction = await self._bias_direction(previous_close, spot_price)
                if direction is None:
                    await self.decision_queries.log_event(
                        "bias_filter_no_signal",
                        {"spot": spot_price},
                        underlying=underlying,
                    )
                    log.info("bias_filter_no_signal", spot=spot_price)
                    return None
            else:
                direction = self.direction_filter.get_direction(open_price, previous_close)

        # Fetch VIX for metrics or VIX selection method
        vix_price: float | None = None
        try:
            raw = await self.chain_queries.db.pool.fetchval(
                "SELECT price FROM spot_prices WHERE underlying = '$VIX' ORDER BY ts DESC LIMIT 1"
            )
            if raw:
                vix_price = float(raw)
                log.debug("vix_fetched", vix=round(vix_price, 2))
        except Exception as e:
            log.warning("vix_fetch_failed", error=str(e))

        # Entry retry loop: re-scan chain each attempt so strikes flex with price movement.
        # Start at fly's composite ask, add price_step each retry to sweeten the offer.
        max_steps = self.config.execution.price_ladder_steps
        price_step = self.config.execution.price_ladder_step
        candidates_logged = False
        entry_attempts: list[dict[str, object]] = []

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

            # Select best candidate based on configured method
            best: ButterflyCandidate | None = None
            selection_method = self.config.entry.strike_selection_method

            if selection_method == "VIX":
                vix_buckets = self.config.strategy.vix_width_buckets
                if vix_buckets:
                    if not vix_price:
                        log.warning(
                            "vix_width_buckets configured but VIX unavailable — skipping entry"
                        )
                        return None
                    effective_widths, sigmas = resolve_wing_widths_for_vix(
                        vix_price,
                        vix_buckets,
                    )
                    log.info(
                        "vix_bucket_selected",
                        vix=round(vix_price, 2),
                        widths=effective_widths,
                    )
                else:
                    effective_widths = self.config.strategy.wing_widths
                    sigmas = tuple(None for _ in effective_widths)

                if vix_price:
                    per_width_bests = []
                    for i, width in enumerate(effective_widths):
                        target_center = vix_target_center(
                            vix=vix_price,
                            spot=spot_price,
                            direction=direction,
                            wing_width=None if sigmas[i] is not None else width,
                            sigma_fraction=sigmas[i],
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
                        best = min(
                            per_width_bests,
                            key=lambda c: abs(
                                c.reward_risk - self.config.strategy.rr_target
                            ),
                        )
                        log.info(
                            "vix_center_selected",
                            vix=round(vix_price, 2),
                            width=best.wing_width,
                            center=best.center_strike,
                            rr=round(best.reward_risk, 2),
                        )
            elif selection_method == "TARGET_COST":
                best = self.selector.select_best_by_target_cost(candidates)

            if best is None:
                # Fallback or BEST_RR method
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
                        if (
                            row["center_strike"] == best.center_strike
                            and row["wing_width"] == best.wing_width
                        ):
                            row["selected"] = True
                if candidate_rows:
                    await self.candidate_queries.bulk_insert(candidate_rows)

            if not best:
                await self.decision_queries.log_event(
                    "no_candidates",
                    {"direction": direction, "spot": spot_price, "step": step},
                    underlying=underlying,
                )
                log.info("no_candidates", step=step, direction=direction)
                break

            # Price at fly's composite ask + per-step increment to sweeten the offer
            limit_price = round(best.ask + step * price_step, 2)
            attempt_record = {
                "step": step,
                "limit": limit_price,
                "bid": getattr(best, "bid", None),
                "mark": best.cost,
                "ask": best.ask,
                "center": best.center_strike,
                "width": best.wing_width,
                "reward_risk": best.reward_risk,
            }
            entry_attempts.append(attempt_record)
            log.debug(
                "entry_attempt",
                step=step,
                center=best.center_strike,
                width=best.wing_width,
                ask=best.ask,
                limit=limit_price,
            )

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
                    "metadata": {
                        "selection_method": selection_method,
                        "entry_spot": spot_price,
                        "prev_close": previous_close,
                        "vix": vix_price,
                        "entry_attempts": entry_attempts,
                    },
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
                    entry_expected_move.labels(underlying=underlying).set(
                        _vix_expected_move(vix_price, spot_price)
                    )

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

                await self.decision_queries.log_event(
                    "trade_entered",
                    {
                        "trade_id": trade_id,
                        "center": best.center_strike,
                        "width": best.wing_width,
                        "cost": fill["fill_price"],
                        "direction": direction,
                        "entry_step": step,
                    },
                    underlying=underlying,
                )
                await self.decision_queries.log_event(
                    "entry_ladder_trace",
                    {
                        "trade_id": trade_id,
                        "selection_method": selection_method,
                        "direction": direction,
                        "entry_spot": spot_price,
                        "prev_close": previous_close,
                        "vix": vix_price,
                        "selected_center": best.center_strike,
                        "selected_width": best.wing_width,
                        "entry_attempts": entry_attempts,
                    },
                    underlying=underlying,
                )

                if self.notifier:
                    try:
                        await self.notifier.notify_entry(
                            trade_id=trade_id,
                            underlying=underlying,
                            direction=direction,
                            expiration=expiration,
                            lower_strike=best.lower_strike,
                            center_strike=best.center_strike,
                            upper_strike=best.upper_strike,
                            wing_width=best.wing_width,
                            entry_price=fill["fill_price"],
                            spot=spot_price,
                            order_id=str(fill.get("order_id", "")),
                        )
                    except Exception as e:
                        log.warning("notify_entry_failed", error=str(e))

                log.info(
                    "trade_entered",
                    trade_id=trade_id,
                    center=best.center_strike,
                    step=step,
                )
                return record, best

            await self.decision_queries.log_event(
                "entry_step_unfilled",
                {
                    "step": step,
                    "limit": limit_price,
                    "mark": best.cost,
                    "ask": best.ask,
                    "center": best.center_strike,
                    "width": best.wing_width,
                },
                underlying=underlying,
            )
            log.debug(
                "entry_step_unfilled",
                step=step,
                limit=limit_price,
                ask=best.ask,
                center=best.center_strike,
            )

        await self.decision_queries.log_event(
            "entry_exhausted",
            {
                "direction": direction,
                "entry_attempts": entry_attempts,
            },
            underlying=underlying,
        )
        log.warning("entry_exhausted", direction=direction)
        return None

    async def _bias_direction(
        self, prev_close: float, entry_close: float
    ) -> Literal["CALL", "PUT"] | None:
        """Fetch today's 1-min bars from Schwab and run BiasScoreFilter."""

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

    async def _session_open_price(self) -> float | None:
        """Fetch today's first regular-session open from Schwab intraday bars."""
        try:
            underlying = self.config.strategy.underlying
            spot_sym = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
            candles = await self.schwab.get_intraday_bars(spot_sym, days_back=1)
            return _session_open_from_intraday_candles(candles, now_eastern().date())
        except Exception as e:
            log.warning("session_open_fetch_failed", error=str(e))
            return None

    def _parse_chain_to_quotes(
        self, chain_data: dict, expiration: dt.date
    ) -> list[OptionQuote]:
        """Parse Schwab chain response into OptionQuote objects."""
        underlying = self.config.strategy.underlying
        return [
            OptionQuote(
                symbol=opt.get("symbol", ""),
                underlying=underlying,
                expiration=expiration,
                strike=strike,
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
            for strike, option_type, opt in iter_chain_options(chain_data, expiration)
        ]
