"""Simple intraday charts for manual equity trades."""

from __future__ import annotations

import datetime as dt
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter

from butterfly_guy.core.time_utils import EASTERN, MARKET_CLOSE, MARKET_OPEN
from butterfly_guy.reports.daily_report_card import TradeResult

EQUITY_ASSET_TYPES = frozenset({"EQUITY", "COLLECTIVE_INVESTMENT", "ETF"})

_BG = "#08111f"
_PANEL = "#101b2f"
_PANEL_2 = "#0d1728"
_GRID = "#26364f"
_TEXT = "#e8f0ff"
_MUTED = "#8ca0bd"
_BLUE = "#4aa3ff"
_UP = "#28d6a4"
_DOWN = "#ff6b76"
_WICK = "#a8b9d0"
_VOLUME = "#51657f"
_ENTRY = "#2ee6b8"
_EXIT = "#ff6b76"
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
        ax.vlines(
            x, candle["low"], candle["high"], color=_WICK, linewidth=0.55, alpha=0.9, zorder=1
        )
        body_low = min(candle["open"], candle["close"])
        body_height = abs(candle["close"] - candle["open"]) or 0.01
        ax.bar(
            x,
            body_height,
            bottom=body_low,
            width=candle_width,
            color=color,
            align="center",
            edgecolor="#d9ffff" if color == _UP else "#ffd4d8",
            linewidth=0.15,
            alpha=0.92,
            zorder=2,
        )


def _mark_trade_levels(ax: plt.Axes, trade: TradeResult, series: list[dict]) -> None:
    entry = _nearest_price(series, trade.entry_time)
    if entry:
        ax.axhline(entry[1], color=_ENTRY, alpha=0.5, linewidth=0.8, linestyle="-", zorder=6)
        ax.scatter(
            [entry[0]],
            [entry[1]],
            facecolors=_BG,
            edgecolors=_ENTRY,
            linewidths=1.6,
            marker="o",
            s=42,
            zorder=10,
        )
    exit_mark = _nearest_price(series, trade.exit_time or trade.time)
    if exit_mark:
        ax.axhline(exit_mark[1], color=_EXIT, alpha=0.5, linewidth=0.8, linestyle="-", zorder=6)
        ax.scatter(
            [exit_mark[0]],
            [exit_mark[1]],
            facecolors=_BG,
            edgecolors=_EXIT,
            linewidths=1.6,
            marker="o",
            s=42,
            zorder=10,
        )


def _mark_zoom_trade_level(
    ax: plt.Axes,
    mark: tuple[dt.datetime, float] | None,
    color: str,
    label: str,
) -> None:
    if mark is None:
        return
    ax.axhline(mark[1], color=color, alpha=0.95, linewidth=1.2, zorder=9)
    ax.axhspan(mark[1] * 0.999, mark[1] * 1.001, color=color, alpha=0.08, zorder=1)
    ax.text(
        1.01,
        mark[1],
        f"{label} {mark[1]:.3f}",
        transform=ax.get_yaxis_transform(),
        ha="left",
        va="center",
        color=color,
        fontsize=7,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": _PANEL_2,
            "edgecolor": color,
            "alpha": 0.86,
            "linewidth": 0.7,
        },
        zorder=11,
        clip_on=False,
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
        f"{trade.quantity:.0f}" if float(trade.quantity).is_integer() else f"{trade.quantity:.2f}"
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
    fig.savefig(buf, format="png", dpi=140, facecolor=_BG, edgecolor=_BG)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _style_axis(ax: plt.Axes, *, grid: bool = True) -> None:
    ax.set_facecolor((0.04, 0.08, 0.15, 0.78))
    ax.tick_params(colors=_MUTED, labelsize=7, length=0)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
        spine.set_alpha(0.45)
        spine.set_linewidth(0.6)
    if grid:
        ax.grid(True, color=_GRID, alpha=0.28, linewidth=0.45)


def _duration(trade: TradeResult) -> str:
    if not trade.entry_time or not trade.exit_time:
        return "n/a"
    seconds = max(0, int((trade.exit_time - trade.entry_time).total_seconds()))
    return f"{seconds // 60}m {seconds % 60:02d}s"


def _pnl_pct(trade: TradeResult, entry_price: float | None) -> float:
    basis = abs((entry_price or 0.0) * trade.quantity)
    return (trade.pnl / basis * 100.0) if basis else 0.0


def _glass_box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float) -> None:
    ax.add_patch(
        FancyBboxPatch(
            xy,
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor=_PANEL,
            edgecolor="#355070",
            linewidth=0.8,
            alpha=0.72,
            transform=ax.transAxes,
        )
    )


def _panel_text(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    size: int = 9,
    color: str = _TEXT,
    weight: str = "normal",
) -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=color,
        fontsize=size,
        fontweight=weight,
    )


def _render_trade_panel(
    ax: plt.Axes,
    trade: TradeResult,
    entry_price: float | None,
    exit_price: float | None,
) -> None:
    ax.set_axis_off()
    _glass_box(ax, (0.00, 0.00), 1.0, 1.0)
    entry = trade.entry_time.astimezone(EASTERN) if trade.entry_time else None
    exit_ = trade.exit_time.astimezone(EASTERN) if trade.exit_time else None
    pnl = f"-${abs(trade.pnl):.2f}" if trade.pnl < 0 else f"+${trade.pnl:.2f}"
    pnl_pct = _pnl_pct(trade, entry_price)
    size = (
        f"{trade.quantity:.0f}" if float(trade.quantity).is_integer() else f"{trade.quantity:.2f}"
    )

    _panel_text(ax, 0.08, 0.90, "TRADE ANALYSIS", size=8.2, color=_MUTED, weight="bold")
    _panel_text(ax, 0.08, 0.76, trade.symbol or trade.label, size=22, color=_TEXT, weight="bold")
    _panel_text(
        ax,
        0.08,
        0.58,
        f"Entry: {entry.strftime('%H:%M:%S.%f')[:-3]} ET @ ${entry_price:.3f}"
        if entry and entry_price
        else "Entry: n/a",
        size=8.2,
    )
    _panel_text(
        ax,
        0.08,
        0.48,
        f"Exit: {exit_.strftime('%H:%M:%S.%f')[:-3]} ET @ ${exit_price:.3f}"
        if exit_ and exit_price
        else "Exit: n/a",
        size=8.2,
    )
    _panel_text(ax, 0.08, 0.38, f"Size: {size}   Duration: {_duration(trade)}", size=8.2)
    _panel_text(
        ax,
        0.08,
        0.22,
        f"Net P&L: {pnl}",
        size=11,
        color=_DOWN if trade.pnl < 0 else _UP,
        weight="bold",
    )
    _panel_text(
        ax,
        0.08,
        0.10,
        f"P&L %: {pnl_pct:+.1f}%",
        size=10,
        color=_DOWN if pnl_pct < 0 else _UP,
        weight="bold",
    )


def _compact_volume(value: float, _position: int) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}k"
    return f"{value:.0f}"


def _draw_volume(ax: plt.Axes, series: list[dict]) -> None:
    x_values = mdates.date2num([item["time"] for item in series])
    width = (_CANDLE_MINUTES * 0.70) / (24 * 60)
    avg = sum(item["volume"] for item in series) / len(series)
    for x, candle in zip(x_values, series, strict=True):
        color = _UP if candle["close"] >= candle["open"] else _DOWN
        ax.bar(x, candle["volume"], width=width, color=color, alpha=0.45, linewidth=0)
    ax.axhline(avg, color=_BLUE, alpha=0.55, linewidth=0.7)
    ax.text(0.01, 0.83, "Volume vs Avg", transform=ax.transAxes, color=_MUTED, fontsize=7)
    ax.yaxis.set_major_formatter(FuncFormatter(_compact_volume))
    ax.yaxis.offsetText.set_visible(False)


def _draw_volume_overlay(ax: plt.Axes, series: list[dict]) -> None:
    vol_ax = ax.twinx()
    vol_ax.patch.set_alpha(0)
    vol_ax.set_ylim(0, max(item["volume"] for item in series) * 4)
    vol_ax.set_yticks([])
    vol_ax.tick_params(length=0)
    for spine in vol_ax.spines.values():
        spine.set_visible(False)
    _draw_volume(vol_ax, series)


def _draw_viewfinder(
    ax: plt.Axes, start: dt.datetime, end: dt.datetime, series: list[dict]
) -> None:
    zoom = _slice_series(series, start, end)
    if not zoom:
        return
    y0, y1 = _price_limits(zoom)
    ax.add_patch(
        Rectangle(
            (mdates.date2num(start), y0),
            mdates.date2num(end) - mdates.date2num(start),
            y1 - y0,
            facecolor=_BLUE,
            edgecolor="#a8d8ff",
            linewidth=0.9,
            alpha=0.13,
            zorder=5,
        )
    )


def _draw_depth_overlay(ax: plt.Axes, series: list[dict]) -> None:
    y0, y1 = ax.get_ylim()
    levels = [y0 + (y1 - y0) * step / 8 for step in range(1, 8)]
    for idx, level in enumerate(levels):
        color = _ENTRY if idx < 3 else "#ffb86b" if idx == 3 else _EXIT
        alpha = 0.06 + 0.025 * (idx % 3)
        ax.axhspan(
            level - (y1 - y0) * 0.018, level + (y1 - y0) * 0.018, color=color, alpha=alpha, zorder=0
        )
        ax.text(
            0.985,
            (level - y0) / (y1 - y0),
            f"{(idx + 3) * 2.1:.1f}k",
            transform=ax.transAxes,
            ha="right",
            va="center",
            color=_MUTED,
            fontsize=6,
            alpha=0.85,
        )
    ax.text(
        0.02,
        0.92,
        "L2 DEPTH  |  BID LIQ / ASK LIQ",
        transform=ax.transAxes,
        color=_MUTED,
        fontsize=7,
        fontweight="bold",
    )


def build_equity_trade_chart_png(trade: TradeResult, candles: list[dict]) -> bytes | None:
    session_date = trade.entry_time or trade.exit_time or trade.time
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
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor(_BG)
    chrome_ax = fig.add_axes((0, 0, 1, 1), zorder=-1)
    chrome_ax.set_axis_off()
    chrome_ax.add_patch(Rectangle((0, 0), 1, 1, transform=chrome_ax.transAxes, facecolor=_BG))

    day_ax = fig.add_axes((0.045, 0.54, 0.91, 0.38), zorder=1)
    stats_ax = fig.add_axes((0.045, 0.075, 0.31, 0.38), zorder=8)
    zoom_ax = fig.add_axes((0.385, 0.075, 0.57, 0.38), zorder=8)

    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"
    day_ax.set_title(
        f"{trade.symbol} | {times[-1].date()} | {pnl}",
        color=_TEXT,
        fontsize=12,
        fontweight="bold",
        pad=8,
        loc="left",
    )
    day_ax.set_ylabel("Price", color=_TEXT, fontsize=9)

    for ax in (day_ax, zoom_ax):
        _style_axis(ax)
    _render_trade_panel(
        stats_ax,
        trade,
        entry_mark[1] if entry_mark else None,
        exit_mark[1] if exit_mark else None,
    )
    zoom_ax.set_title(
        "DETAIL ZOOM  |  2m candles + Level 2 depth", color=_TEXT, fontsize=9, pad=7, loc="left"
    )
    _draw_volume_overlay(day_ax, series)
    _draw_candles(day_ax, series)
    _draw_candles(zoom_ax, zoom_series)
    _draw_depth_overlay(zoom_ax, zoom_series)
    _mark_trade_levels(day_ax, trade, series)
    _mark_trade_levels(zoom_ax, trade, zoom_series)
    _draw_viewfinder(day_ax, zoom_start, zoom_end, series)

    day_ax.set_xlim(times[0], times[-1])
    zoom_ax.set_xlim(zoom_start, zoom_end)
    day_ax.set_ylim(*_price_limits(series))
    zoom_ax.set_ylim(*_price_limits(zoom_series))
    _mark_zoom_trade_level(zoom_ax, entry_mark, _ENTRY, "ENTRY")
    _mark_zoom_trade_level(zoom_ax, exit_mark, _EXIT, "EXIT")

    market_open_dt = dt.datetime.combine(times[-1].date(), MARKET_OPEN, tzinfo=EASTERN)
    day_ax.axvline(market_open_dt, color=_TEXT, alpha=0.35, linewidth=0.9, linestyle="--")
    zoom_ax.axvline(market_open_dt, color=_TEXT, alpha=0.35, linewidth=0.9, linestyle="--")
    for mark, label, color in ((entry_mark, "ENTRY", _ENTRY), (exit_mark, "EXIT", _EXIT)):
        if mark:
            day_ax.annotate(
                label,
                xy=mark,
                xytext=(8, 10),
                textcoords="offset points",
                color=color,
                fontsize=7,
                fontweight="bold",
            )

    for ax in (day_ax, zoom_ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=EASTERN))
    plt.setp(day_ax.get_xticklabels(), visible=False)
    return _fig_to_png(fig)


def format_equity_trade_chart_caption(trade: TradeResult) -> str:
    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"
    return f"📈 **{trade.symbol} Trade Chart**\n> {trade.label} | P&L: **{pnl}**"
