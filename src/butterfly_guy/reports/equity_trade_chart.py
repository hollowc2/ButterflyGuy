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

    times = [item["time"] for item in series]
    x_values = mdates.date2num(times)
    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"

    fig, (price_ax, volume_ax) = plt.subplots(
        2,
        1,
        figsize=(10, 5.4),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
    )
    fig.patch.set_facecolor(_BG)
    for ax in (price_ax, volume_ax):
        ax.set_facecolor(_BG)
        ax.tick_params(colors=_TEXT, labelsize=8)
        ax.grid(True, color=_GRID, alpha=0.5, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_color(_GRID)

    price_ax.set_title(
        f"{trade.symbol} | {times[-1].date()} | {pnl}",
        color=_TEXT,
        fontsize=11,
        pad=8,
    )
    price_ax.set_ylabel("Price", color=_TEXT, fontsize=9)
    volume_ax.set_ylabel("Vol", color=_TEXT, fontsize=9)

    candle_width = 45 / 86400
    volume_colors = []
    for x, candle in zip(x_values, series, strict=True):
        color = _UP if candle["close"] >= candle["open"] else _DOWN
        volume_colors.append(color)
        price_ax.vlines(x, candle["low"], candle["high"], color=_WICK, linewidth=0.8)
        body_low = min(candle["open"], candle["close"])
        body_height = abs(candle["close"] - candle["open"]) or 0.01
        price_ax.bar(
            x,
            body_height,
            bottom=body_low,
            width=candle_width,
            color=color,
            align="center",
            linewidth=0,
        )

    volumes = [item["volume"] for item in series]
    volume_ax.bar(x_values, volumes, width=candle_width, color=volume_colors, alpha=0.55)
    price_ax.set_xlim(x_values[0], x_values[-1])

    market_open_dt = dt.datetime.combine(times[-1].date(), MARKET_OPEN, tzinfo=EASTERN)
    price_ax.axvline(market_open_dt, color=_TEXT, alpha=0.35, linewidth=0.9, linestyle="--")

    entry = _nearest_price(series, trade.entry_time)
    if entry:
        price_ax.scatter([entry[0]], [entry[1]], color=_ENTRY, s=65, zorder=5, label="Entry")

    exit_mark = _nearest_price(series, trade.exit_time or trade.time)
    if exit_mark:
        price_ax.scatter([exit_mark[0]], [exit_mark[1]], color=_EXIT, s=65, zorder=5, label="Exit")

    volume_ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=EASTERN))
    price_ax.legend(loc="upper left", fontsize=7, facecolor=_BG, edgecolor=_GRID, labelcolor=_TEXT)
    fig.autofmt_xdate()
    return _fig_to_png(fig)


def format_equity_trade_chart_caption(trade: TradeResult) -> str:
    pnl = f"+${trade.pnl:.2f}" if trade.pnl >= 0 else f"-${abs(trade.pnl):.2f}"
    return f"📈 **{trade.symbol} Trade Chart**\n> {trade.label} | P&L: **{pnl}**"
