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
import matplotlib.transforms as mtransforms

from butterfly_guy.core.time_utils import EASTERN, MARKET_OPEN, PACIFIC, market_close_time

# Dark palette; series steps validated for the dark surface (dataviz skill).
_BG = "#1a1a2e"
_GRID = "#2d2d44"
_TEXT = "#e0e0e0"
_MUTED = "#8a8aa3"
_PRICE = "#3987e5"
_WING = "#c98500"
_CENTER = "#e0e0e0"
_TENT_FILL = "#199e70"
_TENT_ALPHA = 0.14
_GAIN = "#0ca30c"
_LOSS = "#d03b3b"
_ENTRY_MARKER = "#fab219"
_EXIT_MARKER = "#9085e9"
# Session math stays in Eastern; EOD chart labels and axis read in Pacific.
_DISPLAY_TZ = PACIFIC


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
    trade_id: int | None = None
    exit_price: float | None = None

    @property
    def lower_be(self) -> float:
        return self.lower_strike + self.entry_price

    @property
    def upper_be(self) -> float:
        return self.upper_strike - self.entry_price


@dataclass(frozen=True)
class FlyMarkPoint:
    """One monitor poll of the held fly's mark."""

    ts: dt.datetime
    mark: float


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


def _setup_axes(ax: plt.Axes, y_label: str) -> None:
    ax.set_facecolor(_BG)
    ax.set_ylabel(y_label, color=_MUTED, fontsize=10)
    ax.tick_params(colors=_MUTED, labelsize=9, length=0)
    ax.grid(True, axis="y", color=_GRID, alpha=0.6, linewidth=0.6)
    for side, spine in ax.spines.items():
        spine.set_visible(side == "bottom")
        spine.set_color(_GRID)


def _set_header(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.01, 0.985, title, color=_TEXT, fontsize=13, fontweight="bold",
             ha="left", va="top")
    fig.text(0.01, 0.94, subtitle, color=_MUTED, fontsize=10, ha="left", va="top")


def _right_label(ax: plt.Axes, y: float, text: str, color: str) -> None:
    """Label a horizontal level just outside the right edge of the plot."""
    trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(1.008, y, text, transform=trans, color=color, fontsize=9,
            ha="left", va="center", clip_on=False)


def _draw_strike_overlays(ax: plt.Axes, spec: ButterflyChartSpec) -> None:
    ax.axhspan(spec.lower_be, spec.upper_be, color=_TENT_FILL, alpha=_TENT_ALPHA, linewidth=0)
    ax.axhline(spec.lower_strike, color=_WING, linewidth=1.0, linestyle="--", alpha=0.8)
    ax.axhline(spec.center_strike, color=_CENTER, linewidth=1.2, alpha=0.8)
    ax.axhline(spec.upper_strike, color=_WING, linewidth=1.0, linestyle="--", alpha=0.8)
    _right_label(ax, spec.upper_strike, f"{spec.upper_strike:.0f} wing", _WING)
    _right_label(ax, spec.center_strike, f"{spec.center_strike:.0f} center", _CENTER)
    _right_label(ax, spec.lower_strike, f"{spec.lower_strike:.0f} wing", _WING)


def _marker(
    ax: plt.Axes, x: dt.datetime, y: float, color: str, label: str, *, left: bool = False
) -> None:
    ax.scatter([x], [y], color=color, s=70, zorder=6, edgecolors=_BG, linewidths=2)
    ax.annotate(label, (x, y), xytext=(-6 if left else 6, 8), textcoords="offset points",
                ha="right" if left else "left", color=_TEXT, fontsize=9, zorder=7,
                bbox={"boxstyle": "round,pad=0.2", "facecolor": _BG, "edgecolor": "none",
                      "alpha": 0.75})


def _hhmm(ts: dt.datetime) -> str:
    return ts.astimezone(_DISPLAY_TZ).strftime("%H:%M")


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, facecolor=_BG, edgecolor=_BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _strikes_text(spec: ButterflyChartSpec) -> str:
    return (
        f"{spec.direction} {spec.wing_width}-wide  "
        f"{spec.lower_strike:.0f} / {spec.center_strike:.0f} / {spec.upper_strike:.0f}"
    )


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

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.patch.set_facecolor(_BG)
    _set_header(
        fig,
        f"{spec.underlying} entry  ·  {_strikes_text(spec)}",
        f"Debit ${spec.entry_price:.2f}  ·  expiry tent {spec.lower_be:.0f}–{spec.upper_be:.0f}"
        f"  ·  spot {start_label}–{end_label}",
    )
    _setup_axes(ax, spec.underlying)

    times = [t.astimezone(tz) for t, _ in series]
    prices = [p for _, p in series]
    _draw_strike_overlays(ax, spec)
    ax.plot(times, prices, color=_PRICE, linewidth=2.0, zorder=4)

    entry_local = spec.entry_time.astimezone(tz)
    if window_start <= entry_local <= window_end and spec.entry_spot is not None:
        _marker(ax, entry_local, spec.entry_spot, _ENTRY_MARKER,
                f"fill {entry_local:%H:%M}  {spec.entry_spot:.0f}")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=tz))
    fig.subplots_adjust(top=0.86)
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
    spec: ButterflyChartSpec,
) -> tuple[bool, int]:
    """Count bars in the expiry tent from entry onward; pre-entry bars don't count."""
    entry_et = spec.entry_time.astimezone(EASTERN)
    in_tent_bars = sum(
        1
        for ts, price in series
        if ts >= entry_et and spec.lower_be <= price <= spec.upper_be
    )
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
    marks: list[FlyMarkPoint] | None = None,
) -> tuple[bytes | None, bool | None]:
    """Return EOD chart PNG and whether spot entered the profit tent after entry."""
    series = _exit_chart_series(spec, candles, full_session=full_session)
    if series is None:
        return None, None

    tent_hit, _ = _tent_hit_stats(series, spec)
    png = build_exit_chart_png(spec, candles, full_session=full_session, marks=marks)
    return png, tent_hit


def _draw_spot_panel(
    ax: plt.Axes,
    spec: ButterflyChartSpec,
    series: list[tuple[dt.datetime, float]],
    held_start: dt.datetime,
    held_end: dt.datetime,
) -> None:
    _setup_axes(ax, spec.underlying)
    ax.margins(y=0.08)
    _draw_strike_overlays(ax, spec)
    times = [t for t, _ in series]
    prices = [p for _, p in series]
    # Full session in muted ink; the held stretch on top in the series color.
    ax.plot(times, prices, color=_MUTED, linewidth=1.3, alpha=0.7, zorder=3)
    held = [(t, p) for t, p in series if held_start <= t <= held_end]
    if len(held) >= 2:
        ax.plot([t for t, _ in held], [p for _, p in held], color=_PRICE, linewidth=2.0, zorder=4)

    if times[0] <= held_start <= times[-1]:
        # Sit the marker on the plotted bar; the fill-time spot goes in the label.
        entry_bar = min(series, key=lambda point: abs(point[0] - held_start))
        entry_spot = spec.entry_spot if spec.entry_spot is not None else entry_bar[1]
        _marker(ax, entry_bar[0], entry_bar[1], _ENTRY_MARKER,
                f"entry {_hhmm(held_start)} @ {entry_spot:.0f}")
    exit_time, exit_spot = _exit_marker_point(spec, series)
    _marker(ax, exit_time, exit_spot, _EXIT_MARKER, f"exit {_hhmm(exit_time)}")


def _draw_mark_panel(
    ax: plt.Axes,
    spec: ButterflyChartSpec,
    marks: list[FlyMarkPoint],
    exit_time: dt.datetime,
) -> None:
    _setup_axes(ax, "Fly value ($)")
    times = [m.ts.astimezone(EASTERN) for m in marks]
    values = [m.mark for m in marks]
    debit = spec.entry_price
    ax.fill_between(times, values, debit, where=[v >= debit for v in values],
                    color=_GAIN, alpha=0.25, linewidth=0, interpolate=True)
    ax.fill_between(times, values, debit, where=[v < debit for v in values],
                    color=_LOSS, alpha=0.25, linewidth=0, interpolate=True)
    ax.axhline(debit, color=_MUTED, linewidth=1.0, linestyle="--")
    _right_label(ax, debit, f"debit {debit:.2f}", _MUTED)
    ax.plot(times, values, color=_PRICE, linewidth=1.4, zorder=4)

    peak_point = max(marks, key=lambda m: m.mark)
    peak_time = peak_point.ts.astimezone(EASTERN)
    late_peak = peak_time > times[0] + (exit_time - times[0]) / 2
    _marker(ax, peak_time, peak_point.mark, _TEXT,
            f"peak {peak_point.mark:.2f} @ {_hhmm(peak_time)}", left=late_peak)

    exit_value = spec.exit_price if spec.exit_price is not None else values[-1]
    _marker(ax, exit_time, exit_value, _EXIT_MARKER, f"exit {exit_value:.2f}")


def build_exit_chart_png(
    spec: ButterflyChartSpec,
    candles: list[dict],
    *,
    full_session: bool = False,
    marks: list[FlyMarkPoint] | None = None,
) -> bytes | None:
    """Session spot with the tent, plus the fly's own value path when marks exist."""
    series = _exit_chart_series(spec, candles, full_session=full_session)
    if series is None:
        return None

    _, tent_bars = _tent_hit_stats(series, spec)
    entry_et = spec.entry_time.astimezone(EASTERN)
    exit_time, _ = _exit_marker_point(spec, series)

    trade_label = f"#{spec.trade_id}  ·  " if spec.trade_id is not None else ""
    title = f"{spec.underlying} {trade_label}{entry_et:%a %Y-%m-%d}  ·  {_strikes_text(spec)}"
    subtitle_parts = [f"Exit {spec.exit_reason or 'open'} {_hhmm(exit_time)} PT"]
    if spec.exit_price is not None:
        change = spec.exit_price - spec.entry_price
        subtitle_parts.append(
            f"fly {spec.entry_price:.2f} → {spec.exit_price:.2f} ({change:+.2f})"
        )
    subtitle_parts.append(
        f"spot in expiry tent {spec.lower_be:.0f}–{spec.upper_be:.0f}: "
        f"{tent_bars} min after entry"
    )

    has_marks = bool(marks) and len(marks) >= 2
    if has_marks:
        fig, (ax_spot, ax_mark) = plt.subplots(
            2, 1, figsize=(10, 6.6), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
        )
    else:
        fig, ax_spot = plt.subplots(figsize=(10, 4.8))
        ax_mark = None
    fig.patch.set_facecolor(_BG)
    _set_header(fig, title, "  ·  ".join(subtitle_parts))

    _draw_spot_panel(ax_spot, spec, series, entry_et, exit_time)
    if ax_mark is not None:
        _draw_mark_panel(ax_mark, spec, marks, exit_time)

    bottom_ax = ax_mark if ax_mark is not None else ax_spot
    bottom_ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=_DISPLAY_TZ))
    bottom_ax.set_xlabel("PT", color=_MUTED, fontsize=9, loc="right")
    fig.subplots_adjust(top=0.88 if has_marks else 0.84, hspace=0.08)
    return _fig_to_png(fig)
