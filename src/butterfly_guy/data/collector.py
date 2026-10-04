"""Option chain collector — fetches and stores SPX chain snapshots."""

from __future__ import annotations

import asyncio
import datetime as dt
import time
from typing import Any

from butterfly_guy.backtest.chain_cache import save_snapshot
from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    chain_snapshot_duration,
    chain_snapshot_rows,
    chain_snapshots_total,
    collector_missed_ticks,
    collector_tick_lateness,
)
from butterfly_guy.core.time_utils import (
    get_0dte_expiration,
    is_market_open,
    now_eastern,
    session_date,
)
from butterfly_guy.data.providers import (
    ChainObservation,
    CollectorMarketDataProvider,
    SpotObservation,
)
from butterfly_guy.data.schwab_client import SCHWAB_CHAIN_SYMBOLS, SCHWAB_SPOT_SYMBOLS
from butterfly_guy.db.queries import ChainQueries, DailyBarQueries, SpotQueries
from butterfly_guy.notify import send_async as notify

log = get_logger(__name__)
UNOBSERVED_SOURCE = "unobserved"  # a provider without timing metadata (shadow reads)


TICK = dt.timedelta(minutes=1)
MISSED_TICK_ALERT = 3  # consecutive skipped grid ticks before alerting


def _wall_clock() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def next_tick(now: dt.datetime, offset_seconds: float) -> dt.datetime:
    """The first grid tick (HH:MM:00 + offset) at or after `now`."""
    offset = dt.timedelta(seconds=offset_seconds)
    tick = (now - offset).replace(second=0, microsecond=0) + offset
    return tick if tick >= now else tick + TICK


class OptionChainCollector:
    """Collects option chain snapshots at regular intervals."""

    def __init__(
        self,
        config: AppConfig,
        schwab: CollectorMarketDataProvider,
        chain_queries: ChainQueries,
        spot_queries: SpotQueries,
        daily_bar_queries: DailyBarQueries | None = None,
    ) -> None:
        self.config = config
        self.schwab = schwab
        self.chain_queries = chain_queries
        self.spot_queries = spot_queries
        self.daily_bar_queries = daily_bar_queries
        self._daily_bars_date: dt.date | None = None
        self._meta_alert_sent = False
        # Clocks of the aligned loop (replaced by a fake clock in tests).
        self._now = _wall_clock
        self._monotonic = time.monotonic
        self._sleep = asyncio.sleep

    def _parse_chain_response(
        self,
        data: dict[str, Any],
        snapshot_time: dt.datetime,
        expiration: dt.date,
        spot_price: float,
    ) -> list[dict[str, Any]]:
        """Parse Schwab callExpDateMap/putExpDateMap into flat rows."""
        rows: list[dict[str, Any]] = []
        underlying = self.config.strategy.underlying

        for option_type, map_key in [("CALL", "callExpDateMap"), ("PUT", "putExpDateMap")]:
            exp_map = data.get(map_key, {})
            for exp_key, strikes in exp_map.items():
                # exp_key format: "2026-03-10:0"
                if str(expiration) not in exp_key:
                    continue
                for strike_str, options in strikes.items():
                    for opt in options:
                        rows.append({
                            "snapshot_time": snapshot_time,
                            "underlying": underlying,
                            "expiration": expiration,
                            "strike": float(strike_str),
                            "option_type": option_type,
                            "bid": opt.get("bid"),
                            "ask": opt.get("ask"),
                            "mark": opt.get("mark"),
                            "last": opt.get("last"),
                            "volume": opt.get("totalVolume", 0),
                            "open_interest": opt.get("openInterest", 0),
                            "iv": opt.get("volatility"),
                            "delta": opt.get("delta"),
                            "gamma": opt.get("gamma"),
                            "theta": opt.get("theta"),
                            "vega": opt.get("vega"),
                            "symbol": opt.get("symbol"),
                            "spot_price": spot_price,
                            "bid_size": opt.get("bidSize"),
                            "ask_size": opt.get("askSize"),
                            "rho": opt.get("rho"),
                            "intrinsic_value": opt.get("intrinsicValue"),
                            "time_value": opt.get("timeValue"),
                            "in_the_money": opt.get("inTheMoney"),
                            "days_to_expiration": opt.get("daysToExpiration"),
                            "multiplier": opt.get("multiplier"),
                            "theoretical_value": opt.get("theoreticalOptionValue"),
                        })
        return rows

    async def collect_daily_bars(self) -> None:
        """Fetch and store daily OHLCV bars for SPX and VIX.

        Runs once per Eastern session date. Today's in-progress candle is never
        stored, and a failed symbol leaves the refresh pending so the next
        snapshot retries it.
        """
        if self.daily_bar_queries is None:
            return
        today = session_date()
        if self._daily_bars_date == today:
            return

        underlying = self.config.strategy.underlying
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")

        symbols_to_fetch = [(spot_symbol, underlying)]
        if underlying == "SPX":
            symbols_to_fetch.append(("$VIX", "$VIX"))

        all_succeeded = True
        for symbol, label in symbols_to_fetch:
            try:
                candles = await self.schwab.get_daily_bars(symbol)
                rows = []
                for c in candles:
                    if c.get("close") is None:
                        continue
                    bar_date = dt.datetime.fromtimestamp(
                        c["datetime"] / 1000,
                        tz=dt.timezone.utc,
                    ).date()
                    if bar_date >= today:
                        # Today's candle is still in progress; storing it would
                        # leave an intraday price as this date's "close".
                        continue
                    rows.append({
                        "date": bar_date,
                        "underlying": label,
                        "open": c.get("open"),
                        "high": c.get("high"),
                        "low": c.get("low"),
                        "close": c["close"],
                        "volume": c.get("volume", 0),
                    })
                count = await self.daily_bar_queries.bulk_upsert(rows)
                log.info("daily_bars_collected", symbol=label, rows=count)
            except Exception as e:
                all_succeeded = False
                log.warning("daily_bars_fetch_failed", symbol=label, error=str(e))

        if all_succeeded:
            self._daily_bars_date = today

    async def _spot(self, symbol: str) -> tuple[SpotObservation, dt.datetime, dt.datetime]:
        """Spot with its timing metadata, and wall-clock times around the fetch."""
        observed = getattr(self.schwab, "get_spot_observed", None)
        started = _wall_clock()
        if observed is not None:
            spot = await observed(symbol)
        else:
            spot = SpotObservation(price=await self.schwab.get_spot_price(symbol),
                                   source=UNOBSERVED_SOURCE)
        return spot, started, _wall_clock()

    async def collect_snapshot(self) -> int:
        """Fetch current chain and store snapshot. Returns row count."""
        if self.config.collector.record_timing:
            return await self._collect_timed_snapshot()
        snapshot_time = now_eastern()
        expiration = get_0dte_expiration()
        underlying = self.config.strategy.underlying
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(underlying, underlying)

        with chain_snapshot_duration.labels(underlying=underlying).time():
            # Get spot price
            spot_price = await self.schwab.get_spot_price(spot_symbol)
            await self.spot_queries.insert(underlying, spot_price, snapshot_time)

            # Get VIX spot price (only for SPX to prevent duplicate requests/writes)
            if underlying == "SPX":
                try:
                    vix_price = await self.schwab.get_spot_price("$VIX")
                    await self.spot_queries.insert("$VIX", vix_price, snapshot_time)
                    log.info("vix_snapshot_collected", vix=vix_price)
                except Exception as e:
                    log.warning("vix_fetch_failed", error=str(e))

            # Get chain
            chain_data = await self.schwab.get_option_chain(chain_symbol, expiration)
            rows = self._parse_chain_response(chain_data, snapshot_time, expiration, spot_price)
            return await self._store_chain(rows, snapshot_time, expiration, spot_price)

    async def _store_chain(
        self,
        rows: list[dict[str, Any]],
        snapshot_time: dt.datetime,
        expiration: dt.date,
        spot_price: float,
    ) -> int:
        underlying = self.config.strategy.underlying
        if rows:
            count = await self.chain_queries.bulk_insert_snapshot(rows)
            chain_snapshots_total.labels(underlying=underlying).inc()
            chain_snapshot_rows.labels(underlying=underlying).set(count)
            try:
                await asyncio.to_thread(
                    save_snapshot,
                    expiration,
                    snapshot_time,
                    spot_price,
                    rows,
                    underlying=underlying,
                )
            except OSError as e:
                log.warning("chain_cache_write_failed", error=str(e))
            log.info("snapshot_collected", rows=count, spot=spot_price)
            return count

        log.warning("snapshot_empty", expiration=str(expiration))
        return 0

    async def _collect_timed_snapshot(
        self, scheduled_at: dt.datetime | None = None, *, chain_first: bool = False
    ) -> int:
        """`collect_snapshot` that also records when each quote was made.

        `snapshot_time` keeps its meaning (the stamp at the start of the pass). Quote event
        times and ages go into the new nullable columns, and fetch timings, the chain's
        gateway metadata and the contracts the gateway delivered but the strategy chain
        omits go into `chain_snapshot_meta`. A meta-write failure is logged and alerted
        but never blocks the chain insert.
        """
        snapshot_time = now_eastern()
        expiration = get_0dte_expiration()
        underlying = self.config.strategy.underlying
        spot_symbol = SCHWAB_SPOT_SYMBOLS.get(underlying, f"${underlying}")
        chain_symbol = SCHWAB_CHAIN_SYMBOLS.get(underlying, underlying)
        meta: dict[str, Any] = {"snapshot_time": snapshot_time, "underlying": underlying,
                                "expiration": expiration, "scheduled_at": scheduled_at}

        async def fetch_chain() -> tuple[dict[str, Any], ChainObservation]:
            observed = getattr(self.schwab, "get_option_chain_observed", None)
            started = _wall_clock()
            if observed is not None:
                data, chain = await observed(chain_symbol, expiration)
            else:
                data = await self.schwab.get_option_chain(chain_symbol, expiration)
                chain = ChainObservation(source=UNOBSERVED_SOURCE)
            meta.update(chain_fetch_started_at=started, chain_fetch_completed_at=_wall_clock())
            return data, chain

        with chain_snapshot_duration.labels(underlying=underlying).time():
            if chain_first:
                # The chain's quotes land closest to the minute mark ThetaData's row
                # represents; spot and VIX follow, and their fetch times are recorded.
                chain_data, chain = await fetch_chain()
            spot, started, done = await self._spot(spot_symbol)
            spot_price = spot.price
            meta.update(spot_fetch_started_at=started, spot_fetch_completed_at=done,
                        spot_event_ts=spot.event_timestamp, spot_age_s=spot.age_seconds)
            await self.spot_queries.insert(underlying, spot_price, snapshot_time,
                                           event_ts=spot.event_timestamp,
                                           age_s=spot.age_seconds)

            if underlying == "SPX":
                try:
                    vix, started, done = await self._spot("$VIX")
                    meta.update(vix_fetch_started_at=started, vix_fetch_completed_at=done,
                                vix_event_ts=vix.event_timestamp, vix_age_s=vix.age_seconds)
                    await self.spot_queries.insert("$VIX", vix.price, snapshot_time,
                                                   event_ts=vix.event_timestamp,
                                                   age_s=vix.age_seconds)
                    log.info("vix_snapshot_collected", vix=vix.price)
                except Exception as e:
                    log.warning("vix_fetch_failed", error=str(e))

            if not chain_first:
                chain_data, chain = await fetch_chain()
            rows = self._parse_chain_response(chain_data, snapshot_time, expiration, spot_price)
            for row in rows:
                timing = chain.contracts.get(row.get("symbol") or "")
                row["quote_event_ts"] = timing.event_timestamp if timing else None
                row["quote_age_s"] = timing.age_seconds if timing else None
            spot_range = self.config.strategy.spot_range
            meta.update(
                chain_gateway_received_at=chain.gateway_received_at,
                chain_event_ts=chain.event_timestamp,
                chain_age_s=chain.age_seconds,
                chain_source=chain.source,
                chain_flags=list(chain.data_quality_flags),
                contracts_delivered=chain.contracts_delivered,
                contracts_stored=len(rows),
                contracts_omitted=len(chain.omitted),
                omitted=[{"symbol": o.symbol, "option_type": o.option_type,
                          "strike": o.strike, "stale": o.stale, "age_s": o.age_seconds,
                          "flags": list(o.flags)} for o in chain.omitted],
                strikes_within_spot_range=len({r["strike"] for r in rows
                                               if abs(r["strike"] - spot_price) <= spot_range}),
            )
            count = await self._store_chain(rows, snapshot_time, expiration, spot_price)
            await self._store_meta(meta)
            return count

    async def _store_meta(self, meta: dict[str, Any]) -> None:
        underlying = self.config.strategy.underlying
        try:
            await self.chain_queries.insert_snapshot_meta(meta)
        except Exception as e:
            log.error("snapshot_meta_write_failed", error=str(e))
            if not self._meta_alert_sent:
                self._meta_alert_sent = True
                try:
                    await notify(f"⚠️ {underlying} snapshot timing metadata write failed: {e}")
                except Exception:  # noqa: BLE001 - alerting must not break collection
                    pass
            return
        if self._meta_alert_sent:
            self._meta_alert_sent = False
            await notify(f"✅ {underlying} snapshot timing metadata writes recovered.")

    async def _sleep_until(self, deadline: dt.datetime) -> None:
        """Sleep to an absolute wall-clock deadline, measured on the monotonic clock."""
        target = self._monotonic() + (deadline - self._now()).total_seconds()
        while (remaining := target - self._monotonic()) > 0:
            await self._sleep(remaining)

    async def run_aligned_loop(self) -> None:
        """Collect on the fixed grid HH:MM:00 + `align_offset_seconds` while the market is
        open. Each sleep runs to an absolute deadline; a pass that overruns its slot makes
        the loop skip the missed ticks (no catch-up burst), count them and record them.
        """
        collector = self.config.collector
        offset = collector.align_offset_seconds
        underlying = self.config.strategy.underlying
        log.info("collector_starting", aligned=True, offset_seconds=offset)
        deadline: dt.datetime | None = None
        consecutive_failures = 0
        alert_sent = False
        missed_streak = 0
        missed_alert_sent = False

        closed_logged = False
        while True:
            now = self._now()
            if deadline is None:
                deadline = next_tick(now, offset)
            elif now > deadline:
                upcoming = next_tick(now, offset)
                skipped = round((upcoming - deadline) / TICK)
                if is_market_open(deadline):
                    collector_missed_ticks.labels(underlying=underlying).inc(skipped)
                    missed_streak += skipped
                    log.warning("collector_ticks_missed", scheduled_at=deadline.isoformat(),
                                skipped=skipped, streak=missed_streak)
                    if missed_streak >= MISSED_TICK_ALERT and not missed_alert_sent:
                        await notify(f"⚠️ {underlying} collector missed {missed_streak} "
                                     "minute ticks in a row (passes overrunning their slot).")
                        missed_alert_sent = True
                deadline = upcoming
            await self._sleep_until(deadline)
            if not is_market_open(deadline):
                # Step through the grid while closed, so the first tick after the open
                # (09:30:00 + offset) is not missed.
                if not closed_logged:
                    log.info("market_closed_waiting")
                    closed_logged = True
                deadline += TICK
                continue
            closed_logged = False

            collector_tick_lateness.labels(underlying=underlying).observe(
                max(0.0, (self._now() - deadline).total_seconds()))
            try:
                if collector.record_timing:
                    await self._collect_timed_snapshot(deadline, chain_first=True)
                else:
                    await self.collect_snapshot()
                # After the minute's snapshot, so a once-a-day refresh never delays it.
                await self.collect_daily_bars()
                if alert_sent:
                    await notify(f"✅ {underlying} data collection recovered.")
                    alert_sent = False
                consecutive_failures = 0
            except Exception as e:
                log.error("snapshot_failed", error=str(e))
                consecutive_failures += 1
                if consecutive_failures >= 3 and not alert_sent:
                    await notify(
                        f"⚠️ {underlying} data collection has failed "
                        f"{consecutive_failures} times in a row. Last error: {e}"
                    )
                    alert_sent = True
            deadline += TICK
            if self._now() <= deadline:
                missed_streak = 0
                if missed_alert_sent:
                    await notify(f"✅ {underlying} collector is back on its minute grid.")
                    missed_alert_sent = False

    async def run_loop(self) -> None:
        """Main collector loop — runs while market is open."""
        if self.config.collector.align_to_minute:
            await self.run_aligned_loop()
            return
        interval = self.config.collector.snapshot_interval_seconds
        underlying = self.config.strategy.underlying
        log.info("collector_starting", interval=interval)

        consecutive_failures = 0
        alert_sent = False

        while True:
            if not is_market_open():
                log.info("market_closed_waiting")
                await asyncio.sleep(30)
                continue

            try:
                await self.collect_daily_bars()
                await self.collect_snapshot()
                if alert_sent:
                    await notify(f"✅ {underlying} data collection recovered.")
                    alert_sent = False
                consecutive_failures = 0
            except Exception as e:
                log.error("snapshot_failed", error=str(e))
                consecutive_failures += 1
                if consecutive_failures >= 3 and not alert_sent:
                    await notify(
                        f"⚠️ {underlying} data collection has failed "
                        f"{consecutive_failures} times in a row. Last error: {e}"
                    )
                    alert_sent = True

            await asyncio.sleep(interval)
