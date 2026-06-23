"""Simple intraday charts for manual equity trades."""

from __future__ import annotations

import datetime as dt
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from butterfly_guy.core.time_utils import EASTERN, MARKET_CLOSE, MARKET_OPEN
from butterfly_guy.reports.daily_report_card import TradeResult

EQUITY_ASSET_TYPES = frozenset({"EQUITY", "COLLECTIVE_INVESTMENT", "ETF"})

_BG = "#1a1a2e"
_GRID = "#2d2d44"
_TEXT = "#e0e0e0"
_UP = "#66bb6a"
_DOWN = "#ef5350"
_WICK = "#b0bec5"
_VOLUME = "#546e7a"
_ENTRY = "#66bb6a"
_EXIT = "#ef5350"
_PREMARKET_START = dt.time(6, 0)
_CANDLE_MINUTES = 2
_ZOOM_PADDING_MINUTES = 10
_MIN_ZOOM_MINUTES = 30


def chartable_equity_trades(trades: list[TradeResult]) -> list[TradeResult]:
    return [
        trade
        for trade in trades
        if trade.symbol
        and trade.asset_type in EQUITY_ASSET_TYPES
        and trade.entry_time is not None
        and trade.exit_time is not None
        and trade.entry_time < trade.exit_time
    ]


def candles_to_series(candles: list[dict], session_date: dt.date) -> list[dict]:
    series: list[dict] = []
    for candle in candles:
        ts_ms = candle.get("datetime")
        if ts_ms is None or candle.get("close") is None:
            continue
        ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=dt.timezone.utc).astimezone(EASTERN)
        if ts.date() != session_date:
            continue
        if not (_PREMARKET_START <= ts.time() <= MARKET_CLOSE):
            continue
        close = float(candle["close"])
        open_ = float(candle.get("open", close))
        high = float(candle.get("high", max(open_, close)))
        low = float(candle.get("low", min(open_, close)))
        series.append(
            {
                "time": ts,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": float(candle.get("volume") or 0),
            }
        )
    return sorted(series, key=lambda item: item["time"])


def _nearest_price(
    series: list[dict],
    mark_time: dt.datetime | None,
) -> tuple[dt.datetime, float] | None:
    if not series or mark_time is None:
        return None
    mark_et = mark_time.astimezone(EASTERN)
    candle = min(series, key=lambda item: abs((item["time"] - mark_et).total_seconds()))
    return candle["time"], candle["close"]


def two_minute_candles(series: list[dict]) -> list[dict]:
    buckets: dict[dt.datetime, dict] = {}
    for candle in series:
        ts = candle["time"]
        bucket_time = ts.replace(
            minute=(ts.minute // _CANDLE_MINUTES) * _CANDLE_MINUTES,
            second=0,
            microsecond=0,
        )
        bucket = buckets.get(bucket_time)
        if bucket is None:
            buckets[bucket_time] = {
                "time": bucket_time,
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["volume"],
            }
            continue
        bucket["high"] = max(bucket["high"], candle["high"])
        bucket["low"] = min(bucket["low"], candle["low"])
        bucket["close"] = candle["close"]
        bucket["volume"] += candle["volume"]
    return [buckets[key] for key in sorted(buckets)]


def _zoom_bounds(trade: TradeResult, series: list[dict]) -> tuple[dt.datetime, dt.datetime]:
    first = series[0]["time"]
    last = series[-1]["time"]
    entry_time = (trade.entry_time or first).astimezone(EASTERN)
    exit_time = (trade.exit_time or trade.time or entry_time).astimezone(EASTERN)
    start = min(entry_time, exit_time) - dt.timedelta(minutes=_ZOOM_PADDING_MINUTES)
    end = max(entry_time, exit_time) + dt.timedelta(minutes=_ZOOM_PADDING_MINUTES)
    if (end - start).total_seconds() < _MIN_ZOOM_MINUTES * 60:
        midpoint = start + (end - start) / 2
        half_window = dt.timedelta(minutes=_MIN_ZOOM_MINUTES / 2)
        start = midpoint - half_window
        end = midpoint + half_window
    start = max(first, start)
    end = min(last, end)
    return (first, last) if start >= end else (start, end)


def _draw_candles(ax: plt.Axes, series: list[dict]) -> None:
    x_values = mdates.date2num([item["time"] for item in series])
    candle_width = (_CANDLE_MINUTES * 0.70) / (24 * 60)
    for x, candle in zip(x_values, series, strict=True):
        color = _UP if candle["close"] >= candle["open"] else _DOWN
        ax.vlines(x, candle["low"], candle["high"], color=_WICK, linewidth=0.8, zorder=1)
        body_low = min(candle["open"], candle["close"])
        body_height = abs(candle["close"] - candle["open"]) or 0.01
        ax.bar(
            x,
            body_height,
            bottom=body_low,
            width=candle_width,
            color=color,
            align="center",
            linewidth=0,
            zorder=2,
        )


def _mark_trade(ax: plt.Axes, trade: TradeResult, series: list[dict]) -> None:
    entry = _nearest_price(series, trade.entry_time)
    if entry:
        ax.scatter(
            [entry[0]],
            [entry[1]],
            color=_ENTRY,
            edgecolors=_TEXT,
            linewidths=1.2,
            marker="o",
            s=110,
            zorder=8,
            label="Entry",
        )
    exit_mark = _nearest_price(series, trade.exit_time or trade.time)
    if exit_mark:
        ax.scatter(
            [exit_mark[0]],
            [exit_mark[1]],
            color=_EXIT,
            edgecolors=_TEXT,
            linewidths=1.2,
            marker="o",
            s=110,
            zorder=8,
            label="Exit",
        )


def _slice_series(
    series: list[dict],
    start: dt.datetime | None,
    end: dt.datetime | None,
) -> list[dict]:
    if start is None and end is None:
        return series
    return [
        candle
        for candle in series
        if (start is None or candle["time"] >= start) and (end is None or candle["time"] <= end)
    ]


def _price_limits(series: list[dict]) -> tuple[float, float]:
    low = min(candle["low"] for candle in series)
    high = max(candle["high"] for candle in series)
    spread = max(high - low, 0.01)
    pad = spread * 0.08
    return low - pad, high + pad


def _format_trade_stats(
    trade: TradeResult,
    *,
    entry_price: float | None = None,
    exit_price: float | None = None,
) -> list[str]:
    entry = trade.entry_time.astimezone(EASTERN) if trade.entry_time else None
    exit_ = trade.exit_time.astimezone(EASTERN) if trade.exit_time else None
    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"
    size = (
        f"{trade.quantity:.0f}"
        if float(trade.quantity).is_integer()
        else f"{trade.quantity:.2f}"
    )
    return [
        f"Symbol: {trade.symbol or trade.label}",
        f"Entry: {entry.strftime('%H:%M:%S ET') if entry else '—'}"
        f"{f' @ ${entry_price:.2f}' if entry_price is not None else ''}",
        f"Exit: {exit_.strftime('%H:%M:%S ET') if exit_ else '—'}"
        f"{f' @ ${exit_price:.2f}' if exit_price is not None else ''}",
        f"Size: {size}",
        f"P&L: {pnl}",
    ]

def _render_trade_stats(
    ax: plt.Axes,
    trade: TradeResult,
    *,
    entry_price: float | None = None,
    exit_price: float | None = None,
) -> None:
    ax.set_facecolor(_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.text(
        0.04,
        0.92,
        "Trade Stats",
        color=_TEXT,
        fontsize=11,
        fontweight="bold",
        ha="left",
        va="top",
        transform=ax.transAxes,
    )
    lines = _format_trade_stats(
        trade,
        entry_price=entry_price,
        exit_price=exit_price,
    )
    for idx, line in enumerate(lines):
        ax.text(
            0.04,
            0.76 - idx * 0.15,
            line,
            color=_TEXT,
            fontsize=10,
            ha="left",
            va="top",
            transform=ax.transAxes,
        )


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=_BG, edgecolor=_BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def build_equity_trade_chart_png(trade: TradeResult, candles: list[dict]) -> bytes | None:
    session_date = (trade.entry_time or trade.exit_time or trade.time)
    if session_date is None:
        return None
    series = candles_to_series(candles, session_date.astimezone(EASTERN).date())
    if len(series) < 2:
        return None
    series = two_minute_candles(series)

    times = [item["time"] for item in series]
    zoom_start, zoom_end = _zoom_bounds(trade, series)
    zoom_series = _slice_series(series, zoom_start, zoom_end)
    if len(zoom_series) < 2:
        zoom_series = series
    entry_mark = _nearest_price(series, trade.entry_time)
    exit_mark = _nearest_price(series, trade.exit_time or trade.time)
    fig = plt.figure(figsize=(14, 8.2))
    gs = fig.add_gridspec(
        2,
        2,
        width_ratios=[2.0, 3.0],
        height_ratios=[1.25, 2.0],
        hspace=0.30,
        wspace=0.16,
    )
    stats_ax = fig.add_subplot(gs[0, 0])
    zoom_ax = fig.add_subplot(gs[0, 1])
    day_ax = fig.add_subplot(gs[1, :])
    fig.patch.set_facecolor(_BG)
    for ax in (day_ax, zoom_ax, stats_ax):
        ax.set_facecolor(_BG)
        ax.tick_params(colors=_TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(_GRID)
    stats_ax.grid(False)
    zoom_ax.grid(False)
    day_ax.grid(False)

    day_ax.set_title(
        f"{trade.symbol} | full day 2m candles | {times[-1].date()}",
        color=_TEXT,
        fontsize=11,
        pad=8,
    )
    day_ax.set_ylabel("Price", color=_TEXT, fontsize=9)
    zoom_ax.set_ylabel("Price", color=_TEXT, fontsize=9)

    _render_trade_stats(
        stats_ax,
        trade,
        entry_price=entry_mark[1] if entry_mark else None,
        exit_price=exit_mark[1] if exit_mark else None,
    )
    zoom_ax.set_title("entry/exit zoom", color=_TEXT, fontsize=10, pad=8)
    _draw_candles(day_ax, series)
    _draw_candles(zoom_ax, zoom_series)
    _mark_trade(day_ax, trade, series)
    _mark_trade(zoom_ax, trade, zoom_series)

    day_ax.set_xlim(times[0], times[-1])
    zoom_ax.set_xlim(zoom_start, zoom_end)
    day_ax.set_ylim(*_price_limits(series))
    zoom_ax.set_ylim(*_price_limits(zoom_series))

    market_open_dt = dt.datetime.combine(times[-1].date(), MARKET_OPEN, tzinfo=EASTERN)
    day_ax.axvline(market_open_dt, color=_TEXT, alpha=0.35, linewidth=0.9, linestyle="--")
    zoom_ax.axvline(market_open_dt, color=_TEXT, alpha=0.35, linewidth=0.9, linestyle="--")

    for ax in (day_ax, zoom_ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=EASTERN))
    day_ax.legend(loc="upper left", fontsize=7, facecolor=_BG, edgecolor=_GRID, labelcolor=_TEXT)
    fig.autofmt_xdate()
    return _fig_to_png(fig)


def format_equity_trade_chart_caption(trade: TradeResult) -> str:
    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"
    return f"📈 **{trade.symbol} Trade Chart**\n> {trade.label} | P&L: **{pnl}**"
