"""Daily report card orchestration — fetch Schwab data, build, post to Discord."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import EASTERN, is_trading_day
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.reports.daily_report_card import build_daily_report_card
from butterfly_guy.reports.daily_report_card_config import DailyReportCardSettings
from butterfly_guy.reports.daily_report_card_format import archive_report, build_report_messages
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger(__name__)


@dataclass(frozen=True)
class ReportCardResult:
    skipped: bool
    reason: str
    report_date: dt.date | None = None
    messages_sent: int = 0
    trade_count: int = 0


async def send_daily_report_card(
    schwab: SchwabClientWrapper,
    *,
    report_date: dt.date,
    generated_at: dt.datetime,
    settings: DailyReportCardSettings,
    notifier: DiscordNotifier | None = None,
    dry_run: bool = False,
    dump_raw: bool = False,
    dump_raw_dir: Path | None = None,
) -> ReportCardResult:
    if not is_trading_day(report_date):
        return ReportCardResult(skipped=True, reason=f"{report_date} is not a trading day")

    account_data = await schwab.get_account_snapshot()
    all_txns = await schwab.get_transactions_for_day(report_date)
    orders = await schwab.get_orders_for_day(report_date)

    if dump_raw and dump_raw_dir:
        dump_raw_dir.mkdir(parents=True, exist_ok=True)
        prefix = report_date.isoformat()
        (dump_raw_dir / f"{prefix}_account.json").write_text(
            json.dumps(account_data, indent=2, default=str)
        )
        (dump_raw_dir / f"{prefix}_transactions.json").write_text(
            json.dumps(all_txns, indent=2, default=str)
        )
        (dump_raw_dir / f"{prefix}_orders.json").write_text(
            json.dumps(orders, indent=2, default=str)
        )

    card = build_daily_report_card(
        report_date=report_date,
        generated_at=generated_at.astimezone(EASTERN),
        account_data=account_data,
        transactions=all_txns,
        orders=orders,
        settings=settings,
    )
    messages = build_report_messages(card)

    archive_report(
        messages,
        report_dir=settings.report_dir,
        report_date=report_date,
    )

    if dry_run:
        for message in messages:
            print(message)
            print()
        log.info(
            "daily_report_card_dry_run",
            report_date=str(report_date),
            trade_count=card.activity.trade_count,
            messages=len(messages),
        )
        return ReportCardResult(
            skipped=False,
            reason="dry_run",
            report_date=report_date,
            messages_sent=len(messages),
            trade_count=card.activity.trade_count,
        )

    if notifier:
        await notifier.notify_messages(messages)
        log.info(
            "daily_report_card_sent",
            report_date=str(report_date),
            trade_count=card.activity.trade_count,
            messages=len(messages),
        )

    return ReportCardResult(
        skipped=False,
        reason="sent",
        report_date=report_date,
        messages_sent=len(messages),
        trade_count=card.activity.trade_count,
    )
