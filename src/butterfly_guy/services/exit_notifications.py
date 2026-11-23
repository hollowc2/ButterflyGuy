"""Retry closed-trade Discord receipts independently of position management.

Delivery is at least once: acceptance followed by a lost acknowledgment or failed
receipt commit can produce a duplicate. The worker never calls a broker or books P&L.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger(__name__)
RETRY_SECONDS = 60
DELIVERY_TIMEOUT_SECONDS = 15


def trade_notifier(
    underlying: str, role: str | None, paper_webhook: str, live_webhook: str,
    *, paper_trading: bool = True,
) -> DiscordNotifier | None:
    """Live/rehearsal must never fall back to the paper channel."""
    use_live_channel = not paper_trading or role in {"live", "live_rehearsal"}
    webhook = live_webhook if use_live_channel else paper_webhook
    return DiscordNotifier(webhook) if underlying == "SPX" and webhook else None


class ExitNotifications:
    def __init__(
        self, db: DatabasePool, underlying: str, role: str | None,
        notifier: DiscordNotifier | None, *, enabled: bool,
    ) -> None:
        self.db = db
        self.underlying = underlying
        self.role = role
        self.notifier = notifier
        self.enabled = enabled

    async def run(self) -> None:
        """Poll even outside market hours; a restart resumes CLOSED pending rows."""
        while True:
            try:
                await self.tick()
            except Exception as error:
                # Transport and database exception strings may contain credentials.
                log.error("exit_notification_tick_failed", error_type=type(error).__name__)
            await asyncio.sleep(RETRY_SECONDS)

    async def tick(self, now: dt.datetime | None = None) -> None:
        now = now or dt.datetime.now(dt.timezone.utc)
        async with self.db.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT * FROM butterfly_trades
                WHERE status = 'CLOSED' AND underlying = $1
                  AND COALESCE(metadata->>'exit_notification_role', $2, '')
                      = COALESCE($2, '')
                  AND (
                    metadata->>'exit_notification_status' = 'pending'
                    OR (NOT metadata ? 'exit_notification_status'
                        AND metadata->>'exit_secondary_work_pending' = 'true')
                  )
                  AND (metadata->>'exit_notification_retry_at' IS NULL
                       OR (metadata->>'exit_notification_retry_at')::timestamptz <= $3)
                ORDER BY exit_time, id
                LIMIT 1 FOR UPDATE SKIP LOCKED
                """,
                self.underlying, self.role, now,
            )
            if row is None:
                return
            # Hold just this closed row through the bounded request and receipt
            # commit. Competing workers skip it; cancellation/crash releases it.
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            state = {
                "exit_notification_status": "pending",
                "exit_notification_retry_at": (
                    now + dt.timedelta(seconds=RETRY_SECONDS)
                ).isoformat(),
                "exit_notification_attempts": metadata.get("exit_notification_attempts", 0) + 1,
            }
            if not self.enabled:
                state.update(
                    exit_notification_status="disabled",
                    exit_notification_error="intentionally_disabled",
                )
            elif self.notifier is None:
                state["exit_notification_error"] = "unconfigured"
                log.warning("exit_notification_unconfigured", trade_id=row["id"], role=self.role)
            else:
                detail = None
                if row["exit_reason"] == "manual_close":
                    filled = row["exit_time"].astimezone(EASTERN).strftime("%H:%M:%S ET")
                    detail = f"Closed by you in Schwab (filled {filled}); no bot exit order."
                    signal = metadata.get("suppressed_exit_signal")
                    if signal:
                        detail += (
                            f" Bot signal was `{signal['reason']}` at mark "
                            f"${float(signal['mark_at_signal']):.2f}."
                        )
                try:
                    async with asyncio.timeout(DELIVERY_TIMEOUT_SECONDS):
                        accepted = await self.notifier.notify_exit(
                            trade_id=row["id"], underlying=row["underlying"],
                            direction=row["direction"], exit_reason=row["exit_reason"],
                            entry_price=float(row["entry_price"]),
                            exit_price=float(row["exit_price"]), pnl=float(row["pnl"]),
                            peak_value=float(row["peak_value"] or 0),
                            entry_time=row["entry_time"], exit_time=row["exit_time"],
                            quantity=row["quantity"], manual_detail=detail,
                            instance_role=self.role,
                        )
                    if accepted is True:
                        state.update(
                            exit_notification_status="sent",
                            exit_notification_accepted_at=now.isoformat(),
                            exit_notification_error=None,
                        )
                    else:
                        state["exit_notification_error"] = "not_accepted"
                except Exception as error:
                    state["exit_notification_error"] = type(error).__name__
                log.info(
                    "exit_notification_delivery", trade_id=row["id"],
                    status=state["exit_notification_status"], role=self.role,
                )
            await conn.execute(
                "UPDATE butterfly_trades SET metadata = metadata || $2::jsonb WHERE id = $1",
                row["id"], json.dumps(state),
            )
