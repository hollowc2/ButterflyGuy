"""Read-only account equity checks, independent of strategy and order execution.

State and a nonblocking PostgreSQL advisory lock coordinate runtimes sharing a DB.
The DB must belong to the configured brokerage account (trades have no account ID).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from decimal import Decimal, InvalidOperation
from typing import Any

from butterfly_guy.core.config import AccountMonitorSettings
from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.metrics import (
    account_monitor_enabled,
    account_monitor_last_success,
    account_monitor_last_tick,
    account_monitor_required_check,
)
from butterfly_guy.core.time_utils import (
    EASTERN,
    is_trading_day,
    market_close_time,
    now_eastern,
    previous_trading_day,
)
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.notify import send_checked_async
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger(__name__)
POLL_SECONDS = 60
RECHECK_SECONDS = 300
BALANCE_TIMEOUT_SECONDS = 15
DELIVERY_TIMEOUT_SECONDS = 20  # Above the senders' internal 10-second HTTP total.
ACCOUNT_KEY = "brokerage_account"  # Each database belongs to one brokerage account.
MONITOR_LOCK_ID = 810_770_013  # Fixed namespace; reveals no account information.


def parse_margin_equity(snapshot: dict[str, Any]) -> Decimal:
    """Read currentBalances.equity strictly; never substitute cash or buying power."""
    try:
        account = snapshot["securitiesAccount"]
        if account["type"] != "MARGIN":
            raise ValueError("not_margin_account")
        value = account["currentBalances"]["equity"]
        if isinstance(value, bool) or value is None:
            raise ValueError("invalid_margin_equity")
        equity = Decimal(str(value))
        if not equity.is_finite():
            raise ValueError("invalid_margin_equity")
        return equity
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError("missing_or_invalid_margin_equity") from exc


def next_session(now: dt.datetime) -> dt.date:
    """Today's session before the open, otherwise the next trading day."""
    day = now.date()
    if is_trading_day(day) and now.time() < dt.time(9, 30):
        return day
    day += dt.timedelta(days=1)
    while not is_trading_day(day):
        day += dt.timedelta(days=1)
    return day


def required_check_at(now: dt.datetime) -> dt.datetime:
    """Latest scheduled check, including the previous close before today's 09:00."""
    if is_trading_day(now.date()) and now.time() >= dt.time(9):
        eod = dt.datetime.combine(now.date(), market_close_time(now.date()), EASTERN)
        eod += dt.timedelta(minutes=15)
        return eod if now >= eod else now.replace(hour=9, minute=0, second=0, microsecond=0)
    previous = previous_trading_day(now.date())
    return dt.datetime.combine(previous, market_close_time(previous), EASTERN) + dt.timedelta(
        minutes=15
    )


class AccountMonitor:
    def __init__(
        self,
        db: DatabasePool,
        schwab: Any,
        settings: AccountMonitorSettings,
        discord: DiscordNotifier | None,
    ) -> None:
        self.db = db
        self.schwab = schwab
        self.settings = settings
        self.discord = discord
        self.account_key = ACCOUNT_KEY
        self.lock_id = MONITOR_LOCK_ID
        self.floor = Decimal(str(settings.minimum_equity))
        account_monitor_enabled.set(settings.enabled is not False)

    async def run(self) -> None:
        """Failures in this optional alert task must never cancel position monitoring."""
        while True:
            try:
                await self.tick(now_eastern())
            except Exception as exc:
                # Broker exceptions can embed sensitive request URLs.
                log.error("account_monitor_failed", error_type=type(exc).__name__)
            await asyncio.sleep(POLL_SECONDS)

    async def _save(self, conn: Any, state: dict[str, Any]) -> None:
        await conn.execute(
            """
            INSERT INTO account_monitor_state (account_key, state) VALUES ($1, $2::jsonb)
            ON CONFLICT (account_key) DO UPDATE
            SET state = EXCLUDED.state, updated_at = NOW()
            """,
            self.account_key, json.dumps(state),
        )

    async def tick(self, at: dt.datetime) -> None:
        if self.settings.enabled is False:
            return
        now = at.astimezone(EASTERN)
        account_monitor_required_check.set(required_check_at(now).timestamp())
        async with self.db.pool.acquire() as conn:
            locked = await conn.fetchval("SELECT pg_try_advisory_lock($1)", self.lock_id)
            if not locked:
                return
            try:
                raw = await conn.fetchval(
                    "SELECT state FROM account_monitor_state WHERE account_key = $1",
                    self.account_key,
                )
                state = json.loads(raw) if raw else {}
                if state.get("last_success_at"):
                    account_monitor_last_success.set(
                        dt.datetime.fromisoformat(state["last_success_at"]).timestamp()
                    )
                if is_trading_day(now.date()):
                    await self._check_due(conn, state, now)
                # Delivery retries continue on weekends, too.
                await self._deliver(conn, state)
                account_monitor_last_tick.set(now.timestamp())
            finally:
                await conn.execute("SELECT pg_advisory_unlock($1)", self.lock_id)

    async def _check_due(self, conn: Any, state: dict[str, Any], now: dt.datetime) -> None:
        rows = await conn.fetch(
            """
            SELECT id, status, metadata->>'settlement_provisional' AS provisional
            FROM butterfly_trades
            WHERE trade_date >= $1 OR status IN ('OPEN', 'SUBMITTED')
               OR metadata->>'settlement_provisional' = 'true'
            ORDER BY id
            """,
            previous_trading_day(now.date()),
        )
        closes = [[r["id"], r["provisional"]] for r in rows if r["status"] == "CLOSED"]
        provisional = any(
            r["status"] in {"OPEN", "SUBMITTED"} or r["provisional"] == "true" for r in rows
        )
        previous_closes = dict(state.get("closes", []))
        changed_close = any(
            trade_id not in previous_closes or flag != previous_closes[trade_id]
            for trade_id, flag in closes
        )
        if closes != state.get("closes", []):
            state["closes"] = closes
            if changed_close:
                # Removed rows only prune the remembered window; they are not exits.
                state["close_due"] = (now + dt.timedelta(seconds=60)).isoformat()
                state["close_recheck_due"] = (
                    now + dt.timedelta(seconds=RECHECK_SECONDS)
                ).isoformat()
            await self._save(conn, state)

        day = now.date().isoformat()
        close = dt.datetime.combine(now.date(), market_close_time(now.date()), EASTERN)
        in_check_window = dt.time(9) <= now.time() and now <= close + dt.timedelta(hours=1)
        morning_due = (
            dt.time(9) <= now.time() and now < close and state.get("morning_day") != day
        )
        eod_due = (
            in_check_window and now >= close + dt.timedelta(minutes=15)
            and state.get("eod_day") != day
        )
        close_due = in_check_window and any(
            state.get(key) and now >= dt.datetime.fromisoformat(state[key])
            for key in ("close_due", "close_recheck_due")
        )
        last = state.get("snapshot", {})
        retry_due = (
            last.get("status") in {"low", "unknown"}
            and now >= dt.datetime.fromisoformat(last["checked_at"])
            + dt.timedelta(seconds=RECHECK_SECONDS)
            and in_check_window
        )
        if not (morning_due or eod_due or close_due or retry_due):
            return

        trigger = (
            "end_of_day" if eod_due else "pre_session" if morning_due
            else "post_close" if close_due else "retry"
        )
        result = await self._snapshot(now, provisional, trigger)
        state["snapshot"] = result
        if morning_due:
            state["morning_day"] = day
        if eod_due:
            state["eod_day"] = day
        for key in ("close_due", "close_recheck_due"):
            if state.get(key) and now >= dt.datetime.fromisoformat(state[key]):
                state.pop(key)

        # One failed read is recorded and retried, but does not change the confirmed
        # condition or replace an outstanding low warning with a transient API error.
        failed = result["status"] == "unknown"
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1 if failed else 0
        if not failed:
            state["last_success_at"] = result["checked_at"]
            account_monitor_last_success.set(now.timestamp())
        confirmed = not failed or state["consecutive_failures"] >= 2
        previous_condition = state.get("condition")
        changed = result["status"] != previous_condition
        unhealthy = result["status"] in {"low", "unknown"}
        daily_reminder = state.get("alert", {}).get("day") != day
        if confirmed and (
            (unhealthy and (changed or daily_reminder))
            or (not unhealthy and changed and previous_condition in {"low", "unknown"})
        ):
            state["alert"] = {
                "day": day,
                "message": self._message(result, now),
                "delivered": {"telegram": False, "discord": False},
            }
        if confirmed:
            state["condition"] = result["status"]
        await self._save(conn, state)
        log.info("account_equity_checked", status=result["status"], trigger=trigger)

    async def _snapshot(
        self, now: dt.datetime, provisional: bool, trigger: str,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "checked_at": now.isoformat(),
            "trigger": trigger,
            "provisional": provisional,
            "equity": None,
        }
        try:
            snapshot = await asyncio.wait_for(
                self.schwab.get_account_snapshot(), timeout=BALANCE_TIMEOUT_SECONDS,
            )
            equity = parse_margin_equity(snapshot)
            result["equity"] = str(equity)
            result["status"] = "low" if equity <= self.floor else "healthy"
        except Exception as exc:
            result["status"] = "unknown"
            log.warning("account_equity_unavailable", error_type=type(exc).__name__)
        return result

    def _message(self, result: dict[str, Any], now: dt.datetime) -> str:
        status = result["status"]
        title = {
            "low": "⚠️ MARGIN EQUITY WARNING",
            "unknown": "⚠️ UNABLE TO VERIFY MARGIN EQUITY",
            "healthy": "✅ MARGIN EQUITY CHECK RECOVERED",
        }[status]
        lines = [title, "Source: actual Schwab brokerage account (including in paper mode)."]
        if result["equity"] is not None:
            equity = Decimal(result["equity"])
            lines.append(f"Current account equity: ${equity:,.2f}")
            if status == "low":
                shortfall = max(Decimal(0), self.floor - equity)
                lines.append(f"Amount below floor: ${shortfall:,.2f}")
        else:
            lines.append("A valid current margin-account equity balance could not be retrieved.")
        lines.append(f"Required operating floor: above ${self.floor:,.2f}")
        if result["provisional"]:
            lines.append(
                "Local ledger note: open/submitted trades or provisional settlements remain. "
                "This does not change the broker-reported equity."
            )
        lines += [
            f"Next trading session: {next_session(now).isoformat()}",
            f"Checked: {now.strftime('%Y-%m-%d %H:%M:%S %Z')} ({result['trigger']})",
            "Review broker balances and funding before the next entry. "
            "Transfers count only when reflected by Schwab.",
            "This is an equity-floor alert, "
            "not confirmation of options eligibility or buying power. "
            "It does not block trading.",
        ]
        return "\n".join(lines)

    async def _deliver(self, conn: Any, state: dict[str, Any]) -> None:
        alert = state.get("alert")
        if not alert:
            return
        for channel in ("telegram", "discord"):
            if alert["delivered"][channel]:
                continue
            try:
                if channel == "telegram":
                    accepted = await asyncio.wait_for(
                        send_checked_async(alert["message"]), timeout=DELIVERY_TIMEOUT_SECONDS,
                    )
                else:
                    accepted = self.discord is not None and await asyncio.wait_for(
                        self.discord.send_checked(alert["message"]),
                        timeout=DELIVERY_TIMEOUT_SECONDS,
                    )
            except Exception as exc:
                accepted = False
                log.warning("account_alert_error", channel=channel, error_type=type(exc).__name__)
            if accepted:
                alert["delivered"][channel] = True
                await self._save(conn, state)
            else:
                log.warning("account_alert_delivery_failed", channel=channel)
