"""Generate trade context charts for Discord notifications."""

from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass
from zoneinfo import ZoneInfo

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from butterfly_guy.core.time_utils import EASTERN, MARKET_OPEN, market_close_time

# Dark terminal-style palette
_BG = "#1a1a2e"
_GRID = "#2d2d44"
_TEXT = "#e0e0e0"
_PRICE = "#4fc3f7"
_IN_TENT = "#66bb6a"
_OUT_TENT = "#ef5350"
_WING = "#ffa726"
_CENTER = "#ffee58"
_TENT_FILL = "#66bb6a"
_TENT_ALPHA = 0.15
_ENTRY_MARKER = "#ffee58"
_EXIT_MARKER = "#ab47bc"


@dataclass(frozen=True)
class ButterflyChartSpec:
    """Strike and timing context for chart overlays."""

    underlying: str
    direction: str
    lower_strike: float
    center_strike: float
    upper_strike: float
    wing_width: int
    entry_price: float
    entry_time: dt.datetime
    entry_spot: float | None = None
    exit_time: dt.datetime | None = None
    exit_reason: str | None = None

    @property
    def lower_be(self) -> float:
        return self.lower_strike + self.entry_price

    @property
    def upper_be(self) -> float:
        return self.upper_strike - self.entry_price


def parse_hhmm(value: str) -> dt.time:
    hour, minute = value.split(":", 1)
    return dt.time(int(hour), int(minute))


def entry_chart_window(
    session_date: dt.date,
    start_time: str,
    timezone: str,
    entry_time: dt.datetime,
    lookback_minutes: int = 30,
) -> tuple[dt.datetime, dt.datetime]:
    """Return [start_time - lookback, max(start_time, fill)] in the entry timezone."""
    tz = ZoneInfo(timezone)
    window_end = dt.datetime.combine(session_date, parse_hhmm(start_time), tzinfo=tz)
    fill_local = entry_time.astimezone(tz)
    if fill_local > window_end:
        window_end = fill_local
    window_start = window_end - dt.timedelta(minutes=lookback_minutes)
    return window_start, window_end


def candles_to_series(candles: list[dict]) -> list[tuple[dt.datetime, float]]:
    """Parse Schwab 1-min candles into Eastern (close, ts) pairs."""
    series: list[tuple[dt.datetime, float]] = []
    for candle in candles:
        ts_ms = candle.get("datetime")
        close = candle.get("close")
        if ts_ms is None or close is None:
            continue
        ts = dt.datetime.fromtimestamp(ts_ms / 1000, tz=dt.timezone.utc).astimezone(EASTERN)
        series.append((ts, float(close)))
    series.sort(key=lambda item: item[0])
    return series


def _filter_series(
    series: list[tuple[dt.datetime, float]],
    window_start: dt.datetime,
    window_end: dt.datetime,
) -> list[tuple[dt.datetime, float]]:
    start_utc = window_start.astimezone(dt.timezone.utc)
    end_utc = window_end.astimezone(dt.timezone.utc)
    return [
        (ts, price)
        for ts, price in series
        if start_utc <= ts.astimezone(dt.timezone.utc) <= end_utc
    ]


def _setup_axes(ax: plt.Axes, title: str, y_label: str = "Price") -> None:
    ax.set_facecolor(_BG)
    ax.set_title(title, color=_TEXT, fontsize=11, pad=8)
    ax.set_ylabel(y_label, color=_TEXT, fontsize=9)
    ax.tick_params(colors=_TEXT, labelsize=8)
    ax.grid(True, color=_GRID, alpha=0.5, linewidth=0.5)
    for spine in ax.spines.values():
        spine.set_color(_GRID)


def _draw_strike_overlays(ax: plt.Axes, spec: ButterflyChartSpec) -> None:
    ax.axhline(spec.lower_strike, color=_WING, linewidth=0.9, linestyle="--", alpha=0.7,
               label=f"Lower wing {spec.lower_strike:.0f}")
    ax.axhline(spec.center_strike, color=_CENTER, linewidth=1.2, linestyle="-", alpha=0.9,
               label=f"Center {spec.center_strike:.0f}")
    ax.axhline(spec.upper_strike, color=_WING, linewidth=0.9, linestyle="--", alpha=0.7,
               label=f"Upper wing {spec.upper_strike:.0f}")
    ax.axhspan(spec.lower_be, spec.upper_be, color=_TENT_FILL, alpha=_TENT_ALPHA,
               label=f"Profit tent {spec.lower_be:.0f}–{spec.upper_be:.0f}")


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, facecolor=_BG, edgecolor=_BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def build_entry_chart_png(
    spec: ButterflyChartSpec,
    candles: list[dict],
    *,
    start_time: str,
    timezone: str,
    lookback_minutes: int = 30,
) -> bytes | None:
    """Build pre-entry window chart: start_time - lookback → fill."""
    if not candles:
        return None

    entry_et = spec.entry_time.astimezone(EASTERN)
    window_start, window_end = entry_chart_window(
        entry_et.date(), start_time, timezone, spec.entry_time, lookback_minutes
    )
    series = _filter_series(candles_to_series(candles), window_start, window_end)
    if len(series) < 2:
        return None

    tz = ZoneInfo(timezone)
    start_label = window_start.astimezone(tz).strftime("%H:%M")
    end_label = window_end.astimezone(tz).strftime("%H:%M %Z")
    title = (
        f"{spec.underlying} {spec.direction} {spec.wing_width}-wide  |  "
        f"{start_label}–{end_label}"
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(_BG)
    _setup_axes(ax, title)

    times = [t.astimezone(tz) for t, _ in series]
    prices = [p for _, p in series]
    ax.plot(times, prices, color=_PRICE, linewidth=1.8, label=spec.underlying)
    _draw_strike_overlays(ax, spec)

    entry_local = spec.entry_time.astimezone(tz)
    if window_start <= entry_local <= window_end and spec.entry_spot is not None:
        ax.scatter([entry_local], [spec.entry_spot], color=_ENTRY_MARKER, s=60, zorder=5,
                   label="Entry", edgecolors="white", linewidths=0.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=tz))
    ax.legend(loc="upper left", fontsize=7, facecolor=_BG, edgecolor=_GRID, labelcolor=_TEXT)
    fig.autofmt_xdate()
    return _fig_to_png(fig)


def _session_series(
    series: list[tuple[dt.datetime, float]],
    session_date: dt.date,
) -> list[tuple[dt.datetime, float]]:
    open_dt = dt.datetime.combine(session_date, MARKET_OPEN, tzinfo=EASTERN)
    close_dt = dt.datetime.combine(session_date, market_close_time(session_date), tzinfo=EASTERN)
    return [(ts, price) for ts, price in series if open_dt <= ts <= close_dt]


def _tent_hit_stats(
    series: list[tuple[dt.datetime, float]],
    lower_be: float,
    upper_be: float,
) -> tuple[bool, int]:
    in_tent_bars = sum(1 for _, price in series if lower_be <= price <= upper_be)
    return in_tent_bars > 0, in_tent_bars


def _exit_window_end(spec: ButterflyChartSpec, *, full_session: bool) -> dt.datetime:
    entry_et = spec.entry_time.astimezone(EASTERN)
    close_dt = dt.datetime.combine(
        entry_et.date(),
        market_close_time(entry_et.date()),
        tzinfo=EASTERN,
    )
    if full_session:
        return close_dt
    exit_et = (spec.exit_time or dt.datetime.now(dt.timezone.utc)).astimezone(EASTERN)
    return min(exit_et, close_dt)


def _exit_chart_series(
    spec: ButterflyChartSpec,
    candles: list[dict],
    *,
    full_session: bool,
) -> list[tuple[dt.datetime, float]] | None:
    entry_et = spec.entry_time.astimezone(EASTERN)
    full_series = _session_series(candles_to_series(candles), entry_et.date())
    if len(full_series) < 2:
        return None
    window_end = _exit_window_end(spec, full_session=full_session)
    series = [(ts, price) for ts, price in full_series if ts <= window_end]
    if len(series) < 2:
        return None
    return series


def _exit_marker_point(
    spec: ButterflyChartSpec,
    series: list[tuple[dt.datetime, float]],
) -> tuple[dt.datetime, float]:
    if spec.exit_time is None:
        return series[-1]
    exit_et = spec.exit_time.astimezone(EASTERN)
    return min(series, key=lambda point: abs(point[0] - exit_et))


def summarize_exit_chart(
    spec: ButterflyChartSpec,
    candles: list[dict],
    *,
    full_session: bool = False,
) -> tuple[bytes | None, bool | None]:
    """Return EOD chart PNG and whether spot ever entered the profit tent."""
    series = _exit_chart_series(spec, candles, full_session=full_session)
    if series is None:
        return None, None

    tent_hit, _ = _tent_hit_stats(series, spec.lower_be, spec.upper_be)
    return build_exit_chart_png(spec, candles, full_session=full_session), tent_hit


def build_exit_chart_png(
    spec: ButterflyChartSpec,
    candles: list[dict],
    *,
    full_session: bool = False,
) -> bytes | None:
    """Build full-session chart with tent hit coloring."""
    series = _exit_chart_series(spec, candles, full_session=full_session)
    if series is None:
        return None

    tent_hit, tent_bars = _tent_hit_stats(series, spec.lower_be, spec.upper_be)
    hit_label = "YES" if tent_hit else "NO"
    title = (
        f"{spec.underlying} EOD  |  Tent hit: {hit_label} ({tent_bars} bars in zone)"
    )
    if spec.exit_reason:
        title += f"  |  {spec.exit_reason}"

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor(_BG)
    _setup_axes(ax, title)

    times = [t for t, _ in series]
    prices = [p for _, p in series]
    for i in range(len(times) - 1):
        mid = (prices[i] + prices[i + 1]) / 2
        color = _IN_TENT if spec.lower_be <= mid <= spec.upper_be else _OUT_TENT
        ax.plot(times[i : i + 2], prices[i : i + 2], color=color, linewidth=1.6)

    _draw_strike_overlays(ax, spec)

    entry_time = spec.entry_time.astimezone(EASTERN)
    if series and series[0][0] <= entry_time <= series[-1][0] and spec.entry_spot is not None:
        ax.scatter([entry_time], [spec.entry_spot], color=_ENTRY_MARKER, s=60, zorder=5,
                   label="Entry", edgecolors="white", linewidths=0.5)

    if series:
        exit_time, exit_price = _exit_marker_point(spec, series)
        ax.scatter([exit_time], [exit_price], color=_EXIT_MARKER, s=60, zorder=5,
                   label="Exit", edgecolors="white", linewidths=0.5)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=EASTERN))
    ax.legend(loc="upper left", fontsize=7, facecolor=_BG, edgecolor=_GRID, labelcolor=_TEXT)
    fig.autofmt_xdate()
    return _fig_to_png(fig)
