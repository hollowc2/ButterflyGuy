"""Weekend review orchestration — date windows, charts, and Discord posting."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from butterfly_guy.core.logging import get_logger
from butterfly_guy.db.connection import DatabasePool
from butterfly_guy.reports.live_performance import (
    TradePoint,
    compute_stats,
    trade_pnl_dollars,
    trade_point_from_row,
)
from butterfly_guy.reports.performance_chart import build_combined_performance_chart_png
from butterfly_guy.services.chart_data import load_spot_series
from butterfly_guy.services.notifier import DiscordNotifier
from butterfly_guy.services.trade_chart import ButterflyChartSpec, summarize_exit_chart

log = get_logger(__name__)

POST_DELAY_SECONDS = 1.0
MIN_SPOT_ROWS = 10


@dataclass(frozen=True)
class ReviewWindows:
    week_start: dt.date
    week_end: dt.date
    month_start: dt.date
    month_end: dt.date


@dataclass(frozen=True)
class ReviewResult:
    skipped: bool
    reason: str
    weekly_trade_count: int = 0
    messages_sent: int = 0


def previous_mon_fri(reference: dt.date) -> tuple[dt.date, dt.date]:
    """Return Mon–Fri for the week ending on the Friday before reference."""
    if reference.weekday() == 4:
        friday = reference
    elif reference.weekday() == 5:
        friday = reference - dt.timedelta(days=1)
    else:
        days_since_friday = (reference.weekday() - 4) % 7
        friday = reference - dt.timedelta(days=days_since_friday or 7)
    monday = friday - dt.timedelta(days=4)
    return monday, friday


def calendar_month_to_date(end_date: dt.date) -> tuple[dt.date, dt.date]:
    month_start = end_date.replace(day=1)
    return month_start, end_date


def review_windows(reference: dt.date) -> ReviewWindows:
    week_start, week_end = previous_mon_fri(reference)
    month_start, month_end = calendar_month_to_date(week_end)
    return ReviewWindows(
        week_start=week_start,
        week_end=week_end,
        month_start=month_start,
        month_end=month_end,
    )


def _trade_date(row: dict[str, Any]) -> dt.date:
    trade_date = row["trade_date"]
    if isinstance(trade_date, dt.datetime):
        return trade_date.date()
    return trade_date


def trades_in_range(
    trades: list[TradePoint],
    start: dt.date,
    end: dt.date,
) -> list[TradePoint]:
    return [t for t in trades if start <= t.trade_date <= end]


def trades_in_range_rows(
    rows: list[dict[str, Any]],
    start: dt.date,
    end: dt.date,
) -> list[dict[str, Any]]:
    return [row for row in rows if start <= _trade_date(row) <= end]


def _parse_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def format_trade_recap(row: dict[str, Any], *, tent_hit: bool | None) -> str:
    trade_date = _trade_date(row)
    pnl_dollars = trade_pnl_dollars(
        float(row.get("pnl") or 0), int(row.get("quantity") or 1)
    )
    pnl_str = f"+${pnl_dollars:.2f}" if pnl_dollars >= 0 else f"-${abs(pnl_dollars):.2f}"
    tent_label = "HIT" if tent_hit else "MISSED" if tent_hit is not None else "N/A"
    exit_reason = row.get("exit_reason") or "unknown"
    return (
        f"🦋 **SPX #{row['id']}** ({trade_date})\n"
        f"> **{row['direction']}** {row['wing_width']}-wide | "
        f"{row['lower_strike']:.0f} / **{row['center_strike']:.0f}** / {row['upper_strike']:.0f}\n"
        f"> Entry ${float(row['entry_price']):.2f} → "
        f"Exit ${float(row.get('exit_price') or 0):.2f}\n"
        f"> P&L: **{pnl_str}** | Exit: `{exit_reason}` | Tent: **{tent_label}**"
    )


def format_performance_caption(label: str, trades: list[TradePoint]) -> str:
    pnls = [t.pnl_dollars for t in trades]
    stats = compute_stats(pnls)
    pnl_str = (
        f"+${stats.total_pnl:.2f}" if stats.total_pnl >= 0 else f"-${abs(stats.total_pnl):.2f}"
    )
    return (
        f"📊 **{label} Performance**\n"
        f"> Trades: {stats.trade_count} | P&L: **{pnl_str}** | "
        f"Win rate: {stats.win_rate:.0f}% | PF: {stats.profit_factor:.2f} | "
        f"Max DD: ${stats.max_drawdown:.2f}"
    )


def format_combined_performance_caption(
    weekly: list[TradePoint],
    monthly: list[TradePoint],
    all_time: list[TradePoint],
) -> str:
    fill_model = next(
        (trade.paper_fill_model for trades in (weekly, monthly, all_time) for trade in trades),
        "legacy",
    )
    lines = [f"📊 **Performance Summary · {fill_model}**"]
    for label, trades in (
        ("Weekly", weekly),
        ("Monthly", monthly),
        ("All-Time", all_time),
    ):
        lines.append(format_performance_caption(label, trades).split("\n", 1)[1])
    return "\n".join(lines)


def format_review_header(windows: ReviewWindows, trade_count: int) -> str:
    return (
        f"📋 **SPX Weekend Review** "
        f"({windows.week_start} → {windows.week_end})\n"
        f"> {trade_count} trade{'s' if trade_count != 1 else ''} this week | Paper Trading"
    )


async def fetch_closed_trades(db: DatabasePool, underlying: str) -> list[dict[str, Any]]:
    rows = await db.pool.fetch(
        """
        SELECT *
        FROM butterfly_trades
        WHERE underlying = $1 AND status = 'CLOSED'
        ORDER BY trade_date, entry_time
        """,
        underlying,
    )
    return [dict(row) for row in rows]


def closed_trades_to_points(rows: list[dict[str, Any]]) -> list[TradePoint]:
    return [trade_point_from_row(row) for row in rows]


def latest_fill_model_cohort(trades: list[TradePoint]) -> list[TradePoint]:
    """Keep performance math within the most recent paper fill model."""
    if not trades:
        return []
    fill_model = trades[-1].paper_fill_model
    return [trade for trade in trades if trade.paper_fill_model == fill_model]


async def build_eod_chart_for_row(
    db: DatabasePool,
    row: dict[str, Any],
) -> tuple[bytes | None, bool | None]:
    entry_time = row.get("entry_time")
    if entry_time is None:
        return None, None
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=dt.timezone.utc)

    session_date = _trade_date(row)
    underlying = row["underlying"]
    candles = await load_spot_series(db, underlying, session_date)
    if len(candles) < MIN_SPOT_ROWS:
        log.warning(
            "weekend_review_insufficient_spot",
            trade_id=row["id"],
            session_date=str(session_date),
            rows=len(candles),
        )
        return None, None

    metadata = _parse_metadata(row.get("metadata"))
    entry_spot = metadata.get("entry_spot")

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
    return summarize_exit_chart(spec, candles, full_session=True)


async def _post_with_delay(
    notifier: DiscordNotifier | None,
    *,
    content: str,
    image_png: bytes | None = None,
    image_name: str = "chart.png",
    dry_run: bool,
    dry_run_dir: Path | None,
    dry_run_counter: list[int],
) -> None:
    if dry_run:
        if image_png and dry_run_dir is not None:
            dry_run_counter[0] += 1
            path = dry_run_dir / f"{dry_run_counter[0]:02d}_{image_name}"
            path.write_bytes(image_png)
        print(content)
        return
    if notifier is None:
        return
    await notifier._post(content, image_png=image_png, image_name=image_name)
    await asyncio.sleep(POST_DELAY_SECONDS)


async def send_weekend_review(
    db: DatabasePool,
    *,
    underlying: str,
    reference: dt.date,
    notifier: DiscordNotifier | None,
    dry_run: bool = False,
    dry_run_dir: Path | None = None,
) -> ReviewResult:
    windows = review_windows(reference)
    all_rows = await fetch_closed_trades(db, underlying)
    all_points = closed_trades_to_points(all_rows)

    weekly_rows = trades_in_range_rows(all_rows, windows.week_start, windows.week_end)
    if not weekly_rows:
        log.info(
            "weekend_review_skipped",
            reason="no_weekly_trades",
            week_start=str(windows.week_start),
            week_end=str(windows.week_end),
        )
        return ReviewResult(skipped=True, reason="no_weekly_trades")

    cohort_points = latest_fill_model_cohort(all_points)
    fill_model = cohort_points[-1].paper_fill_model
    weekly_points = trades_in_range(cohort_points, windows.week_start, windows.week_end)
    monthly_points = trades_in_range(cohort_points, windows.month_start, windows.month_end)

    if dry_run and dry_run_dir is not None:
        dry_run_dir.mkdir(parents=True, exist_ok=True)

    dry_run_counter = [0]
    messages_sent = 0

    await _post_with_delay(
        notifier,
        content=format_review_header(windows, len(weekly_rows)),
        dry_run=dry_run,
        dry_run_dir=dry_run_dir,
        dry_run_counter=dry_run_counter,
    )
    messages_sent += 1

    for row in weekly_rows:
        chart_png, tent_hit = await build_eod_chart_for_row(db, row)
        recap = format_trade_recap(row, tent_hit=tent_hit)
        if chart_png is None:
            await _post_with_delay(
                notifier,
                content=recap + "\n> _EOD chart unavailable (insufficient spot data)_",
                dry_run=dry_run,
                dry_run_dir=dry_run_dir,
                dry_run_counter=dry_run_counter,
            )
        else:
            await _post_with_delay(
                notifier,
                content=recap,
                image_png=chart_png,
                image_name=f"eod_{row['id']}.png",
                dry_run=dry_run,
                dry_run_dir=dry_run_dir,
                dry_run_counter=dry_run_counter,
            )
        messages_sent += 1

    performance_periods = [
        (f"Weekly · {fill_model}", weekly_points),
        (f"Monthly · {fill_model}", monthly_points),
        (f"All-Time · {fill_model}", cohort_points),
    ]
    combined_caption = format_combined_performance_caption(
        weekly_points,
        monthly_points,
        cohort_points,
    )
    combined_png = build_combined_performance_chart_png(performance_periods)
    await _post_with_delay(
        notifier,
        content=combined_caption,
        image_png=combined_png,
        image_name="performance_summary.png",
        dry_run=dry_run,
        dry_run_dir=dry_run_dir,
        dry_run_counter=dry_run_counter,
    )
    messages_sent += 1

    log.info(
        "weekend_review_complete",
        week_start=str(windows.week_start),
        week_end=str(windows.week_end),
        weekly_trades=len(weekly_rows),
        messages_sent=messages_sent,
        dry_run=dry_run,
    )
    return ReviewResult(
        skipped=False,
        reason="sent",
        weekly_trade_count=len(weekly_rows),
        messages_sent=messages_sent,
    )
