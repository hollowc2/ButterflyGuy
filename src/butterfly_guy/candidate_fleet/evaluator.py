"""Paper-only candidate evaluator built without broker execution dependencies."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prometheus_client import Counter, Gauge

from butterfly_guy.candidate_fleet.models import MarketSnapshot, SnapshotIdentity
from butterfly_guy.candidate_fleet.provider import MarketDataProvider
from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import (
    is_market_open,
    session_date,
    time_in_window,
)
from butterfly_guy.data.schemas import ButterflyCandidate, TradeRecord, fly_mark_value
from butterfly_guy.db.queries import (
    CandidateQueries,
    DecisionQueries,
    MonitoringLegQueries,
    RiskQueries,
    TentQueries,
    TradeQueries,
)
from butterfly_guy.position.position_manager import PositionManager
from butterfly_guy.position.state_machine import ProfitStateMachine
from butterfly_guy.risk.risk_engine import RiskEngine
from butterfly_guy.strategy.direction_filter import DirectionFilter
from butterfly_guy.strategy.entry_selection import entry_strategy_snapshot, select_entry_candidate

log = get_logger(__name__)

candidate_feed_sequence = Gauge(
    "candidate_evaluator_feed_sequence",
    "Latest feed sequence consumed by the evaluator",
    ["candidate_id"],
)
candidate_feed_age = Gauge(
    "candidate_evaluator_feed_age_seconds",
    "Age of the latest feed snapshot consumed",
    ["candidate_id"],
)
candidate_lease_active = Gauge(
    "candidate_evaluator_lease_active",
    "Whether the evaluator expects an active demand lease",
    ["candidate_id", "kind"],
)
candidate_trades = Counter(
    "candidate_evaluator_trades_total",
    "Paper trades accepted by candidate",
    ["candidate_id", "direction"],
)
candidate_realized_pnl = Gauge(
    "candidate_evaluator_realized_pnl_dollars",
    "Session realized PnL",
    ["candidate_id"],
)
candidate_trade_count = Gauge(
    "candidate_evaluator_trade_count",
    "Persisted paper trades for the candidate",
    ["candidate_id"],
)
candidate_win_rate = Gauge(
    "candidate_evaluator_win_rate",
    "Closed candidate trade win rate from zero to one",
    ["candidate_id"],
)
candidate_max_drawdown = Gauge(
    "candidate_evaluator_max_drawdown_dollars",
    "Maximum closed-trade equity drawdown",
    ["candidate_id"],
)
candidate_review_progress = Gauge(
    "candidate_evaluator_review_progress_ratio",
    "Review gate completion from zero to one",
    ["candidate_id"],
)
candidate_open_positions = Gauge(
    "candidate_evaluator_open_positions",
    "Persisted OPEN candidate positions",
    ["candidate_id"],
)

FORBIDDEN_CANDIDATE_ENV = {
    "SCHWAB_API_KEY",
    "SCHWAB_SECRET_KEY",
    "SCHWAB_ACCOUNT_ID",
    "SCHWAB_TOKEN_PATH",
    "ALLOW_LIVE_TRADING",
    "LIVE_EXPECTED_SCHWAB_ACCOUNT_ID",
    "DISCORD_WEBHOOK_URL",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
}


def assert_candidate_safety(config: AppConfig, environ: dict[str, str] | None = None) -> None:
    errors: list[str] = []
    if config.strategy.underlying != "SPX":
        errors.append("strategy.underlying must be SPX")
    if not config.execution.paper_trading:
        errors.append("execution.paper_trading must be true")
    if config.execution.allow_live_trading:
        errors.append("execution.allow_live_trading must be false")
    if config.risk.max_position_size != 1:
        errors.append("risk.max_position_size must be 1")
    env = environ if environ is not None else dict(os.environ)
    leaked = sorted(key for key in FORBIDDEN_CANDIDATE_ENV if env.get(key))
    if leaked:
        errors.append(f"candidate environment contains forbidden variables: {', '.join(leaked)}")
    if errors:
        raise RuntimeError("unsafe candidate configuration: " + "; ".join(errors))


def config_sha256(config_path: str | Path) -> str:
    return hashlib.sha256(Path(config_path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class CandidateAuditContext:
    candidate_id: str
    config_hash: str
    git_sha: str

    def metadata(self, snapshot: MarketSnapshot | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "config_hash": self.config_hash,
            "git_sha": self.git_sha,
        }
        if snapshot is not None:
            data.update(
                {
                    "feed_instance": snapshot.instance,
                    "feed_sequence": snapshot.sequence,
                    "feed_captured_at": snapshot.captured_at.isoformat(),
                }
            )
        return data


class CandidateDecisionQueries:
    def __init__(
        self,
        queries: DecisionQueries,
        audit: CandidateAuditContext,
    ) -> None:
        self.queries = queries
        self.audit = audit

    async def log(
        self,
        event_type: str,
        data: dict[str, Any],
        snapshot: MarketSnapshot | None = None,
    ) -> None:
        await self.queries.log_event(
            event_type,
            {**data, **self.audit.metadata(snapshot)},
            underlying="SPX",
        )


class CandidatePaperExecutor:
    """Mark-price fills only; this object intentionally has no broker methods."""

    def __init__(
        self,
        provider: MarketDataProvider,
        audit: CandidateAuditContext,
    ) -> None:
        self.provider = provider
        self.audit = audit

    async def entry(
        self,
        candidate: ButterflyCandidate,
        snapshot: MarketSnapshot,
    ) -> dict[str, Any]:
        # Pin before returning a fill. A failed pin therefore cannot produce a trade.
        await self.provider.pin(snapshot.identity)
        mark = _candidate_mark(candidate, snapshot)
        return self._fill(mark, snapshot, side="entry")

    def exit(
        self,
        mark: float,
        snapshot: MarketSnapshot,
    ) -> dict[str, Any]:
        return self._fill(mark, snapshot, side="exit")

    def _fill(
        self,
        mark: float,
        snapshot: MarketSnapshot,
        *,
        side: str,
    ) -> dict[str, Any]:
        return {
            "order_id": "CANDIDATE_PAPER",
            "fill_price": round(mark, 4),
            "fill_time": snapshot.captured_at,
            "paper_fill_model": "shared_feed_mark_v1",
            "execution_diagnostics": {
                "side": side,
                "observed_mark": round(mark, 4),
                **self.audit.metadata(snapshot),
            },
        }


class CandidateEvaluator:
    def __init__(
        self,
        *,
        candidate_id: str,
        config: AppConfig,
        provider: MarketDataProvider,
        audit: CandidateAuditContext,
        trade_queries: TradeQueries,
        risk_queries: RiskQueries,
        candidate_queries: CandidateQueries,
        decision_queries: DecisionQueries,
        monitoring_leg_queries: MonitoringLegQueries,
        tent_queries: TentQueries,
        review_trade_count: int = 1,
    ) -> None:
        self.candidate_id = candidate_id
        self.config = config
        self.provider = provider
        self.audit = audit
        self.trades = trade_queries
        self.risk = RiskEngine(config.risk, risk_queries, "SPX")
        self.candidates = candidate_queries
        self.decisions = CandidateDecisionQueries(decision_queries, audit)
        self.monitoring_legs = monitoring_leg_queries
        self.tents = tent_queries
        self.executor = CandidatePaperExecutor(provider, audit)
        self.position_manager = PositionManager("SPX", config.profit_management)
        self.state_machine = ProfitStateMachine(config.profit_management)
        self.review_trade_count = max(1, review_trade_count)
        self._last_identity: SnapshotIdentity | None = None

    async def run(self) -> None:
        await self.refresh_metrics()
        open_rows = await self.trades.get_open_trades("SPX")
        active: tuple[TradeRecord, ButterflyCandidate] | None = None
        if open_rows:
            active = _restore_trade(open_rows[0])
        while True:
            if active is None:
                active = await self.attempt_entry()
                await asyncio.sleep(10)
            else:
                trade, candidate = active
                await self.monitor_position(trade, candidate)
                active = None

    async def attempt_entry(self) -> tuple[TradeRecord, ButterflyCandidate] | None:
        if not time_in_window(
            self.config.entry.start_time,
            self.config.entry.end_time,
            self.config.entry.timezone,
        ):
            return None
        allowed, reason = await self.risk.can_trade(quantity=1)
        if not allowed:
            await self.decisions.log("entry_blocked", {"reason": reason})
            return None

        await self.provider.refresh_lease(self.candidate_id, "entry")
        candidate_lease_active.labels(
            candidate_id=self.candidate_id,
            kind="entry",
        ).set(1)
        try:
            snapshot = await self.provider.snapshot(
                after=self._last_identity,
                wait_seconds=10,
                max_age_seconds=65,
            )
            self._observe_snapshot(snapshot)
            direction = DirectionFilter().get_direction(
                snapshot.session_open,
                snapshot.previous_close,
            )
            selection = select_entry_candidate(
                quotes=list(snapshot.quotes),
                spot=snapshot.spot,
                direction=direction,
                vix=snapshot.vix,
                config=self.config,
                asset="SPX",
            )
            await self._persist_candidates(selection.candidates, selection.candidate, snapshot)
            best = selection.candidate
            if best is None:
                await self.decisions.log(
                    "no_candidates",
                    {"direction": direction, "spot": snapshot.spot},
                    snapshot,
                )
                return None
            fill = await self.executor.entry(best, snapshot)
            metadata = {
                **self.audit.metadata(snapshot),
                "selection_method": selection.selection_method,
                "entry_strategy": entry_strategy_snapshot(self.config),
                "entry_spot": snapshot.spot,
                "session_open": snapshot.session_open,
                "prev_close": snapshot.previous_close,
                "vix": snapshot.vix,
                "paper_fill_model": fill["paper_fill_model"],
                "entry_execution_diagnostics": fill["execution_diagnostics"],
            }
            trade_id = await self.trades.insert_trade(
                {
                    "underlying": "SPX",
                    "trade_date": snapshot.expiration,
                    "direction": best.direction,
                    "wing_width": best.wing_width,
                    "center_strike": best.center_strike,
                    "lower_strike": best.lower_strike,
                    "upper_strike": best.upper_strike,
                    "entry_price": fill["fill_price"],
                    "entry_time": fill["fill_time"],
                    "lower_symbol": best.lower_symbol,
                    "center_symbol": best.center_symbol,
                    "upper_symbol": best.upper_symbol,
                    "quantity": 1,
                    "metadata": metadata,
                }
            )
            await self.risk.record_trade(snapshot.expiration)
            trade = TradeRecord(
                trade_id=trade_id,
                trade_date=snapshot.expiration,
                direction=best.direction,
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
            candidate_trades.labels(
                candidate_id=self.candidate_id,
                direction=best.direction,
            ).inc()
            await self.refresh_metrics()
            await self.decisions.log(
                "trade_entered",
                {
                    "trade_id": trade_id,
                    "direction": best.direction,
                    "center": best.center_strike,
                    "width": best.wing_width,
                    "cost": fill["fill_price"],
                },
                snapshot,
            )
            return trade, best
        except Exception as exc:
            await self.decisions.log("entry_feed_blocked", {"error": str(exc)})
            log.warning("candidate_entry_feed_blocked", error=str(exc))
            return None
        finally:
            await self.provider.release_lease(self.candidate_id)
            candidate_lease_active.labels(
                candidate_id=self.candidate_id,
                kind="entry",
            ).set(0)

    async def monitor_position(
        self,
        trade: TradeRecord,
        candidate: ButterflyCandidate,
    ) -> None:
        self.position_manager.reset(trade.entry_price, peak_value=trade.peak_value)
        self.state_machine.reset()
        symbols = (
            trade.lower_symbol,
            trade.center_symbol,
            trade.upper_symbol,
        )
        lease_task = asyncio.create_task(
            self._lease_heartbeat("position"),
            name=f"candidate_lease_{self.candidate_id}",
        )
        candidate_lease_active.labels(
            candidate_id=self.candidate_id,
            kind="position",
        ).set(1)
        try:
            while is_market_open() and trade.trade_date == session_date():
                try:
                    snapshot = await self.provider.legs(
                        symbols,
                        after=self._last_identity,
                        wait_seconds=3,
                        max_age_seconds=3,
                    )
                    self._observe_snapshot(snapshot)
                    quotes = {
                        quote.strike: quote
                        for quote in snapshot.quotes
                        if quote.option_type == candidate.direction
                    }
                    if len(quotes) != 3:
                        raise RuntimeError("feed returned incomplete monitoring legs")
                    state = self.position_manager.update_position_value(candidate, quotes)
                    await self._persist_monitoring(trade, candidate, snapshot, quotes, state)
                    signal = self.state_machine.evaluate(state)
                    if signal is None:
                        continue
                    fill = self.executor.exit(state.current_value, snapshot)
                    pnl = float(fill["fill_price"]) - trade.entry_price
                    closed = await self.trades.close_trade(
                        trade.trade_id,
                        float(fill["fill_price"]),
                        fill["fill_time"],
                        signal.reason,
                        pnl,
                        state.peak_value,
                        metadata={
                            **self.audit.metadata(snapshot),
                            "paper_fill_model": fill["paper_fill_model"],
                            "exit_execution_diagnostics": fill["execution_diagnostics"],
                        },
                    )
                    if not closed:
                        raise RuntimeError("candidate trade was not OPEN at paper exit")
                    await self.risk.record_pnl(pnl * 100, trade.trade_date)
                    candidate_realized_pnl.labels(candidate_id=self.candidate_id).inc(
                        pnl * 100
                    )
                    await self.decisions.log(
                        "trade_exited",
                        {
                            "trade_id": trade.trade_id,
                            "exit_reason": signal.reason,
                            "fill_price": fill["fill_price"],
                            "pnl": pnl,
                            "peak_value": state.peak_value,
                        },
                        snapshot,
                    )
                    await self.refresh_metrics()
                    return
                except Exception as exc:
                    # Fail closed: no state-machine evaluation or persistence based on stale data.
                    await self.decisions.log(
                        "position_feed_blocked",
                        {"trade_id": trade.trade_id, "error": str(exc)},
                    )
                    log.warning(
                        "candidate_position_feed_blocked",
                        trade_id=trade.trade_id,
                        error=str(exc),
                    )
                    await asyncio.sleep(2)
        finally:
            lease_task.cancel()
            await asyncio.gather(lease_task, return_exceptions=True)
            await self.provider.release_lease(self.candidate_id)
            candidate_lease_active.labels(
                candidate_id=self.candidate_id,
                kind="position",
            ).set(0)

    async def _lease_heartbeat(self, kind: str) -> None:
        while True:
            await self.provider.refresh_lease(self.candidate_id, kind)  # type: ignore[arg-type]
            await asyncio.sleep(10)

    def _observe_snapshot(self, snapshot: MarketSnapshot) -> None:
        self._last_identity = snapshot.identity
        candidate_feed_sequence.labels(candidate_id=self.candidate_id).set(
            snapshot.sequence
        )
        candidate_feed_age.labels(candidate_id=self.candidate_id).set(
            snapshot.age_seconds()
        )

    async def _persist_candidates(
        self,
        candidates: tuple[ButterflyCandidate, ...],
        best: ButterflyCandidate | None,
        snapshot: MarketSnapshot,
    ) -> None:
        await self.candidates.bulk_insert(
            [
                {
                    "scan_time": snapshot.captured_at,
                    "underlying": "SPX",
                    "direction": candidate.direction,
                    "wing_width": candidate.wing_width,
                    "center_strike": candidate.center_strike,
                    "lower_strike": candidate.lower_strike,
                    "upper_strike": candidate.upper_strike,
                    "cost": candidate.cost,
                    "max_profit": candidate.max_profit,
                    "reward_risk": candidate.reward_risk,
                    "lower_be": candidate.lower_be,
                    "upper_be": candidate.upper_be,
                    "distance_from_spot": candidate.distance_from_spot,
                    "spot_price": candidate.spot_price,
                    "selected": candidate is best,
                }
                for candidate in candidates
            ]
        )

    async def _persist_monitoring(
        self,
        trade: TradeRecord,
        candidate: ButterflyCandidate,
        snapshot: MarketSnapshot,
        quotes: dict[float, Any],
        state: Any,
    ) -> None:
        await self.monitoring_legs.insert_quotes(
            ts=snapshot.captured_at,
            trade_id=trade.trade_id,
            underlying="SPX",
            expiration=snapshot.expiration,
            quotes=[
                {
                    "strike": quote.strike,
                    "option_type": quote.option_type,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "mark": quote.mark,
                    "symbol": quote.symbol,
                }
                for quote in quotes.values()
            ],
            spot_price=snapshot.spot,
            fly_mark=state.current_value,
            peak_value=state.peak_value,
            drawdown_pct=state.drawdown_from_peak * 100,
        )
        await self.tents.insert(
            snapshot.captured_at,
            "SPX",
            state.lower_tent,
            state.upper_tent,
        )
        if state.peak_value > trade.peak_value:
            trade.peak_value = state.peak_value
            await self.trades.update_peak_value(trade.trade_id, state.peak_value)

    async def refresh_metrics(self) -> None:
        rows = await self.trades.db.pool.fetch(
            """
            SELECT status, COALESCE(pnl, 0) * 100 * COALESCE(quantity, 1) AS pnl
            FROM butterfly_trades
            WHERE underlying = 'SPX'
            ORDER BY COALESCE(exit_time, entry_time), id
            """
        )
        pnls = [float(row["pnl"]) for row in rows if row["status"] == "CLOSED"]
        total = len(rows)
        closed = len(pnls)
        wins = sum(pnl > 0 for pnl in pnls)
        equity = 0.0
        peak = 0.0
        drawdown = 0.0
        for pnl in pnls:
            equity += pnl
            peak = max(peak, equity)
            drawdown = max(drawdown, peak - equity)
        candidate_trade_count.labels(candidate_id=self.candidate_id).set(total)
        candidate_realized_pnl.labels(candidate_id=self.candidate_id).set(sum(pnls))
        candidate_win_rate.labels(candidate_id=self.candidate_id).set(
            wins / closed if closed else 0
        )
        candidate_max_drawdown.labels(candidate_id=self.candidate_id).set(drawdown)
        candidate_review_progress.labels(candidate_id=self.candidate_id).set(
            min(1, total / self.review_trade_count)
        )
        candidate_open_positions.labels(candidate_id=self.candidate_id).set(
            sum(row["status"] == "OPEN" for row in rows)
        )


def _candidate_mark(candidate: ButterflyCandidate, snapshot: MarketSnapshot) -> float:
    by_symbol = snapshot.by_symbol()
    try:
        return max(
            0.0,
            fly_mark_value(
                by_symbol[candidate.lower_symbol],
                by_symbol[candidate.center_symbol],
                by_symbol[candidate.upper_symbol],
            ),
        )
    except KeyError as exc:
        raise RuntimeError("entry snapshot is missing a selected leg") from exc


def _restore_trade(row: dict[str, Any]) -> tuple[TradeRecord, ButterflyCandidate]:
    metadata = row.get("metadata") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    trade = TradeRecord(
        trade_id=int(row["id"]),
        trade_date=row["trade_date"],
        direction=str(row["direction"]),
        wing_width=int(row["wing_width"]),
        center_strike=float(row["center_strike"]),
        lower_strike=float(row["lower_strike"]),
        upper_strike=float(row["upper_strike"]),
        entry_price=float(row["entry_price"]),
        entry_time=row["entry_time"],
        lower_symbol=str(row["lower_symbol"]),
        center_symbol=str(row["center_symbol"]),
        upper_symbol=str(row["upper_symbol"]),
        peak_value=float(row.get("peak_value") or 0),
    )
    candidate = ButterflyCandidate(
        direction=trade.direction,  # type: ignore[arg-type]
        wing_width=trade.wing_width,
        center_strike=trade.center_strike,
        lower_strike=trade.lower_strike,
        upper_strike=trade.upper_strike,
        cost=trade.entry_price,
        max_profit=trade.wing_width - trade.entry_price,
        reward_risk=0,
        lower_be=trade.lower_strike + trade.entry_price,
        upper_be=trade.upper_strike - trade.entry_price,
        distance_from_spot=0,
        spot_price=float(metadata.get("entry_spot") or 0),
        lower_symbol=trade.lower_symbol,
        center_symbol=trade.center_symbol,
        upper_symbol=trade.upper_symbol,
    )
    return trade, candidate
