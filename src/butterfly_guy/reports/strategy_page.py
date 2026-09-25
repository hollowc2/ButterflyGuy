"""Static "strategy explained" page published beside the live performance page.

The page copy and the interactive lab are driven by the checked-in runtime
config, so the explainer stays true when strategy parameters change. The lab's
script ships as a separate same-origin file (``strategy.js``) rather than an
inline block, which keeps it inside the site's ``script-src 'self'`` CSP without
needing a new nginx hash.
"""

# Generated HTML strings in this module intentionally exceed 100 columns.
# ruff: noqa: E501

from __future__ import annotations

import datetime as dt
import hashlib
import html
from pathlib import Path
from zoneinfo import ZoneInfo

from butterfly_guy.core.config import AppConfig
from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.reports.live_performance import (
    _BASE_CSS,
    _SOURCE_URL,
    TradePoint,
    _json_data_block,
)
from butterfly_guy.strategy.butterfly_builder import resolve_wing_widths_for_vix

STRATEGY_SCRIPT_NAME = "strategy.js"
DEFAULT_REFERENCE_SPOT = 7650.0

_ASSET_DIR = Path(__file__).with_name("strategy_page")
# Names the VIX buckets carry in configs/config.yaml comments, lowest bucket first.
_REGIME_NAMES = ("Zombieland", "Goldilocks 1", "Goldilocks 2", "Chaos")
_VIX_SCALE_MIN = 10.0
_VIX_SCALE_MAX = 45.0
_MARKET_OPEN_ET = dt.time(9, 30)
_MARKET_CLOSE_ET = dt.time(16, 0)


def strategy_script() -> str:
    return (_ASSET_DIR / STRATEGY_SCRIPT_NAME).read_text(encoding="utf-8")


def _script_version() -> str:
    return hashlib.sha256(strategy_script().encode("utf-8")).hexdigest()[:10]


def reference_spot(trades: list[TradePoint]) -> float:
    """A current-looking SPX level for the modeled chain: latest center, rounded to 50."""
    if not trades:
        return DEFAULT_REFERENCE_SPOT
    return float(round(trades[-1].center_strike / 50) * 50)


def best_trade(trades: list[TradePoint]) -> TradePoint | None:
    winners = [t for t in trades if t.pnl_dollars > 0]
    return max(winners, key=lambda t: t.pnl_dollars) if winners else None


def _entry_window_et(config: AppConfig) -> tuple[dt.time, dt.time]:
    tz = ZoneInfo(config.entry.timezone)
    # Any trading date works; both zones shift for DST on the same days.
    day = dt.date(2026, 1, 5)

    def to_et(value: str) -> dt.time:
        hour, minute = (int(part) for part in value.split(":"))
        local = dt.datetime.combine(day, dt.time(hour, minute), tzinfo=tz)
        return local.astimezone(EASTERN).time()

    return to_et(config.entry.start_time), to_et(config.entry.end_time)


def _clock(value: dt.time) -> str:
    return f"{value.hour % 12 or 12}:{value.minute:02d}"


def _minutes_between(start: dt.time, end: dt.time) -> int:
    return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)


def _et_after_open(minutes: int) -> dt.time:
    total = _MARKET_OPEN_ET.hour * 60 + _MARKET_OPEN_ET.minute + minutes
    return dt.time(total // 60, total % 60)


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def strategy_params(config: AppConfig, *, spot: float) -> dict:
    strategy = config.strategy
    buckets = sorted(strategy.vix_width_buckets or [], key=lambda b: b.vix_max)
    bucket_payload = []
    lower = _VIX_SCALE_MIN
    for index, bucket in enumerate(buckets):
        widths, sigmas = resolve_wing_widths_for_vix(lower, buckets)
        bucket_payload.append({
            "name": _REGIME_NAMES[index] if index < len(_REGIME_NAMES) else f"Regime {index + 1}",
            "vixMin": lower,
            "vixMax": bucket.vix_max,
            "widths": list(widths),
            "sigmas": [round(s, 4) for s in sigmas],
        })
        lower = bucket.vix_max

    entry_start, _ = _entry_window_et(config)
    return {
        "underlying": strategy.underlying,
        "spot": spot,
        "hoursLeft": round(_minutes_between(entry_start, _MARKET_CLOSE_ET) / 60, 4),
        "entryEt": _clock(entry_start),
        "rrMin": strategy.rr_min,
        "rrTarget": strategy.rr_target,
        "rrMax": strategy.rr_max,
        "minDebit": strategy.min_debit,
        "centerTolerance": config.entry.center_tolerance,
        "maxCostPerWidth": {str(w): c for w, c in strategy.max_cost_per_width.items()},
        "buckets": bucket_payload,
        "vixScale": [_VIX_SCALE_MIN, _VIX_SCALE_MAX],
    }


def _regime_bar(buckets: list[dict]) -> str:
    segments = []
    for bucket in buckets:
        hi = min(bucket["vixMax"], _VIX_SCALE_MAX)
        span = max(hi - bucket["vixMin"], 1.0)
        label = f"&lt;{bucket['vixMax']:g}" if bucket["vixMax"] <= _VIX_SCALE_MAX else f"{bucket['vixMin']:g}+"
        widths = "/".join(str(w) for w in bucket["widths"])
        segments.append(
            f"<div class='regime' style='flex-grow:{span:g}' data-vix-min='{bucket['vixMin']:g}' data-vix-max='{bucket['vixMax']:g}'>"
            f"<span class='regime-name'>{html.escape(bucket['name'])}</span>"
            f"<span class='regime-meta'>VIX {label} · {widths}</span>"
            "</div>"
        )
    return "".join(segments)


def _trail_bar(config: AppConfig) -> str:
    regimes = sorted(
        config.profit_management.regimes.values(), key=lambda r: r.start_minutes_after_open
    )
    session = _minutes_between(_MARKET_OPEN_ET, _MARKET_CLOSE_ET)
    segments = []
    for regime in regimes:
        start = max(regime.start_minutes_after_open, 0)
        end = min(regime.end_minutes_after_open, session)
        if end <= start:
            continue
        segments.append(
            f"<div class='trail-seg' style='flex-grow:{end - start}'>"
            f"<span class='trail-pct'>{_pct(regime.drawdown_threshold)}</span>"
            f"<span class='trail-time'>{_clock(_et_after_open(start))}–<wbr>{_clock(_et_after_open(end))}</span>"
            "</div>"
        )
    return "".join(segments)


def _case_study(trade: TradePoint | None) -> str:
    if trade is None or trade.exit_price is None:
        return ""
    multiple = trade.exit_price / trade.entry_price if trade.entry_price else 0.0
    side = "Call" if trade.direction == "CALL" else "Put"
    strikes = f"{trade.lower_strike:,.0f} / {trade.center_strike:,.0f} / {trade.upper_strike:,.0f}"
    return f"""
  <section class="case panel" aria-labelledby="case-title">
    <div class="case-copy">
      <div class="eyebrow">Best paper hit so far</div>
      <h2 id="case-title" class="case-title">{trade.trade_date:%b} {trade.trade_date.day}, {trade.trade_date.year} · {side} fly {html.escape(strikes)}</h2>
      <p>Paid <b>${trade.entry_price * 100:,.0f}</b>. Came back as <b>${trade.exit_price * 100:,.0f}</b>.
      One day like this covers a long run of small misses — which is the whole design.</p>
    </div>
    <div class="case-figs">
      <div><span class="label">Return</span><span class="value pos">{multiple:.1f}×</span></div>
      <div><span class="label">PnL</span><span class="value pos">+${trade.pnl_dollars:,.0f}</span></div>
    </div>
  </section>"""


def render_strategy_html(
    config: AppConfig,
    *,
    spot: float,
    best: TradePoint | None,
) -> str:
    params = strategy_params(config, spot=spot)
    strategy = config.strategy
    entry_start, entry_end = _entry_window_et(config)
    max_cost_ratio = max(
        (cost / width for width, cost in strategy.max_cost_per_width.items() if width),
        default=0.1,
    )
    underlying = html.escape(strategy.underlying)
    risk = config.risk
    per_day = "One trade a day" if risk.max_trades_per_day == 1 else f"Up to {risk.max_trades_per_day} trades a day"
    contracts = "one contract" if risk.max_position_size == 1 else f"up to {risk.max_position_size} contracts"
    sigmas = " / ".join(f"{s:g}σ" for s in (params["buckets"][0]["sigmas"] if params["buckets"] else []))

    template = (_ASSET_DIR / "index.html").read_text(encoding="utf-8")
    replacements = {
        "__BASE_CSS__": _BASE_CSS,
        "__UNDERLYING__": underlying,
        "__SOURCE_URL__": _SOURCE_URL,
        "__PARAMS_JSON__": _json_data_block(params),
        # nginx caches .js for 7 days; the content hash busts it when the script changes.
        "__SCRIPT_SRC__": f"{STRATEGY_SCRIPT_NAME}?v={_script_version()}",
        "__MAX_COST_PCT__": _pct(max_cost_ratio),
        "__RR_MIN__": f"{strategy.rr_min:g}",
        "__RR_TARGET__": f"{strategy.rr_target:g}",
        "__RR_MAX__": f"{strategy.rr_max:g}",
        "__ENTRY_WINDOW__": f"{_clock(entry_start)}–{_clock(entry_end)} ET",
        "__PER_DAY__": per_day,
        "__CONTRACTS__": contracts,
        "__SIGMAS__": sigmas,
        "__REGIME_BAR__": _regime_bar(params["buckets"]),
        "__TRAIL_BAR__": _trail_bar(config),
        "__CASE_STUDY__": _case_study(best),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template
