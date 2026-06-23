"""Daily report card orchestration — fetch Schwab data, build, post to Discord."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

from butterfly_guy.core.logging import get_logger
from butterfly_guy.core.time_utils import EASTERN, is_trading_day
from butterfly_guy.data.schwab_client import SchwabClientWrapper
from butterfly_guy.reports.daily_report_card import build_daily_report_card
from butterfly_guy.reports.daily_report_card_config import DailyReportCardSettings
from butterfly_guy.reports.daily_report_card_format import archive_report, build_report_messages
from butterfly_guy.reports.equity_trade_chart import (
    build_equity_trade_chart_png,
    chartable_equity_trades,
    format_equity_trade_chart_caption,
)
from butterfly_guy.services.notifier import DiscordNotifier

log = get_logger(__name__)
POST_DELAY_SECONDS = 1.0


@dataclass(frozen=True)
class ReportCardResult:
    skipped: bool
    reason: str
    report_date: dt.date | None = None
    messages_sent: int = 0
    trade_count: int = 0
    charts_sent: int = 0


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
        charts_sent = await _send_equity_trade_charts(
            schwab,
            report_date=report_date,
            trades=card.trades,
            notifier=None,
            dry_run=True,
            chart_dir=Path(settings.report_dir) / "charts" / report_date.isoformat(),
        )
        log.info(
            "daily_report_card_dry_run",
            report_date=str(report_date),
            trade_count=card.activity.trade_count,
            messages=len(messages),
            charts=charts_sent,
        )
        return ReportCardResult(
            skipped=False,
            reason="dry_run",
            report_date=report_date,
            messages_sent=len(messages),
            trade_count=card.activity.trade_count,
            charts_sent=charts_sent,
        )

    charts_sent = 0
    if notifier:
        await notifier.notify_messages(messages)
        charts_sent = await _send_equity_trade_charts(
            schwab,
            report_date=report_date,
            trades=card.trades,
            notifier=notifier,
            dry_run=False,
            chart_dir=None,
        )
        log.info(
            "daily_report_card_sent",
            report_date=str(report_date),
            trade_count=card.activity.trade_count,
            messages=len(messages),
            charts=charts_sent,
        )

    return ReportCardResult(
        skipped=False,
        reason="sent",
        report_date=report_date,
        messages_sent=len(messages),
        trade_count=card.activity.trade_count,
        charts_sent=charts_sent,
    )


async def _send_equity_trade_charts(
    schwab: SchwabClientWrapper,
    *,
    report_date: dt.date,
    trades: list,
    notifier: DiscordNotifier | None,
    dry_run: bool,
    chart_dir: Path | None,
) -> int:
    chart_trades = chartable_equity_trades(trades)
    if dry_run and chart_dir is not None:
        chart_dir.mkdir(parents=True, exist_ok=True)

    charts_sent = 0
    candles_by_symbol: dict[str, list[dict]] = {}
    for trade in chart_trades:
        if trade.symbol not in candles_by_symbol:
            candles_by_symbol[trade.symbol] = await schwab.get_intraday_bars_for_day(
                trade.symbol, report_date
            )
        candles = candles_by_symbol[trade.symbol]
        chart_png = build_equity_trade_chart_png(trade, candles)
        if chart_png is None:
            log.warning("daily_report_card_chart_unavailable", symbol=trade.symbol)
            continue

        charts_sent += 1
        image_name = f"{charts_sent:02d}_{trade.symbol}.png"
        caption = format_equity_trade_chart_caption(trade)
        if dry_run:
            if chart_dir is not None:
                (chart_dir / image_name).write_bytes(chart_png)
            print(caption)
            continue
        if notifier is not None:
            await notifier._post(caption, image_png=chart_png, image_name=image_name)
            await asyncio.sleep(POST_DELAY_SECONDS)

    return charts_sent
