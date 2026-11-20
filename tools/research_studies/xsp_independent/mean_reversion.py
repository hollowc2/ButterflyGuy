"""Bounded retrospective XSP butterfly reversal study; no broker/runtime operations.

Signals use an approximate option-implied forward, not observed index prices.
All 2026 observations are development evidence. Run with --freeze before --run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.core.time_utils import is_trading_day

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "reports/research/xsp-independent-2026-11-11/mean-reversion"
FEE_SIDE = 2.60
STRESS_SIDE = 0.05
WIDTHS = (2, 4)
ARMS = ("failed_breakout", "excursion_reversal", "time_1005")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_new(path: Path, value: object) -> None:
    with path.open("x") as f:
        json.dump(value, f, indent=2, default=str, allow_nan=False)
        f.write("\n")


def wall(day: dt.date, value: str) -> pd.Timestamp:
    return pd.Timestamp(f"{day} {value}", tz="America/New_York")


def five_minute_bars(proxy: pd.DataFrame, day: dt.date) -> pd.DataFrame:
    """[start,end) sampled proxy bars, available at end; no OHLC ordering inferred."""
    p = proxy[["timestamp", "forward_proxy"]].copy().dropna()
    p = p.sort_values("timestamp")
    p = p[(p.timestamp >= wall(day, "09:30")) & (p.timestamp < wall(day, "13:00"))]
    if p.empty:
        return pd.DataFrame()
    p["gap_ok"] = p.timestamp.diff().le(pd.Timedelta(minutes=2)).fillna(True)
    p.loc[p.index[0], "gap_ok"] = True
    p["end"] = p.timestamp.dt.floor("5min") + pd.Timedelta(minutes=5)
    rows = []
    for end, group in p.groupby("end", sort=True):
        start = end - pd.Timedelta(minutes=5)
        times = pd.DatetimeIndex(group.timestamp)
        # Four of five minute observations allowed; the opening 09:30 no-quote is absent.
        valid = (len(times) >= 4 and group.gap_ok.all()
                 and times[0] <= start + pd.Timedelta(minutes=2)
                 and times[-1] >= end - pd.Timedelta(minutes=2)
                 and (len(times) < 2 or np.diff(times.asi8).max() <= 120_000_000_000))
        rows.append({"timestamp": end, "close": float(group.forward_proxy.iloc[-1]),
                     "high": float(group.forward_proxy.max()),
                     "low": float(group.forward_proxy.min()), "valid": bool(valid)})
    return pd.DataFrame(rows)


def entry_signals(proxy: pd.DataFrame, day: dt.date) -> dict[str, dict]:
    """One causal signal/session/arm; an unavailable prefix is exclusion, not no trade."""
    bars = five_minute_bars(proxy, day)
    invalid = {arm: {"status": "excluded_opening_proxy_coverage"} for arm in ARMS}
    if bars.empty:
        return invalid
    opening = bars[bars.timestamp <= wall(day, "10:00")]
    if (len(opening) != 6 or not opening.valid.all()
            or opening.timestamp.iloc[0] != wall(day, "09:35")):
        return invalid
    lo, hi = float(opening.low.min()), float(opening.high.max())
    mid, span = (lo + hi) / 2, hi - lo
    if span <= 0:
        return {arm: {"status": "excluded_zero_opening_range"} for arm in ARMS}
    common = {"target": mid, "opening_low": lo, "opening_high": hi,
              "opening_range": span}
    result = {arm: {"status": "no_signal", **common} for arm in ARMS}
    previous = float(opening.close.iloc[-1])
    prior_end = wall(day, "10:00")
    breakout_side = 0
    excursion_side = 0
    for row in bars[bars.timestamp > wall(day, "10:00")].itertuples():
        if not row.valid or row.timestamp != prior_end + pd.Timedelta(minutes=5):
            for arm in ARMS:
                if result[arm]["status"] == "no_signal":
                    result[arm] = {"status": "excluded_signal_proxy_gap", **common}
            break
        price = row.close
        side = 1 if price > hi else -1 if price < lo else 0
        if row.timestamp == wall(day, "10:05"):
            result["time_1005"] = {
                "status": "signal", "signal_time": row.timestamp,
                "right": "PUT" if price >= mid else "CALL", **common}
        if breakout_side and lo <= price <= hi and result["failed_breakout"]["status"] == "no_signal":
            result["failed_breakout"] = {
                "status": "signal", "signal_time": row.timestamp,
                "right": "PUT" if breakout_side > 0 else "CALL", **common}
        if side:
            breakout_side = side
        if (excursion_side and (price - mid) * excursion_side > 0
                and abs(price - mid) < abs(previous - mid)
                and result["excursion_reversal"]["status"] == "no_signal"):
            result["excursion_reversal"] = {
                "status": "signal", "signal_time": row.timestamp,
                "right": "PUT" if excursion_side > 0 else "CALL", **common}
        if not excursion_side and abs(price - mid) >= span:
            excursion_side = 1 if price > mid else -1
        previous, prior_end = price, row.timestamp
    if prior_end < wall(day, "13:00"):
        for arm in ARMS:
            if result[arm]["status"] == "no_signal":
                result[arm] = {"status": "excluded_signal_proxy_coverage", **common}
    return result


def first_quote(frame: pd.DataFrame, stamp: pd.Timestamp, *, strict: bool) -> pd.Series | None:
    """Never use the signal snapshot; wait at most 120s for complete usable legs."""
    later = frame.timestamp > stamp if strict else frame.timestamp >= stamp
    candidates = frame[later & (frame.timestamp <= stamp + pd.Timedelta(minutes=2))]
    return candidates.iloc[0] if len(candidates) else None


def account(entry: float, exit_value: float, entry_mark: float, exit_mark: float) -> dict:
    """4-contract 1/-2/1 fly; signed liquidation may require paying to close."""
    risk = 100 * entry + FEE_SIDE
    stress_risk = 100 * (entry + STRESS_SIDE) + FEE_SIDE
    pnl = 100 * (exit_value - entry) - 2 * FEE_SIDE
    stressed = pnl - 200 * STRESS_SIDE
    return {"marketable": pnl, "stressed": stressed,
            "midpoint": 100 * (exit_mark - entry_mark) - 2 * FEE_SIDE,
            "initial_risk_dollars": risk, "stressed_initial_risk_dollars": stress_risk,
            "marketable_r": pnl / risk, "stressed_r": stressed / stress_risk}


def price_signal(quotes: pd.DataFrame, signal: dict, width: int, day: dt.date) -> dict:
    from tools.research_studies.xsp_independent.common import fly_quotes, session_end

    base = {**signal, "date": str(day), "width": width}
    if signal["status"] != "signal":
        return base
    strikes = np.sort(quotes.strike.unique())
    center = float(strikes[np.argmin(abs(strikes - signal["target"]))])
    base.update(center=center)
    path = fly_quotes(quotes, center, width, signal["right"])
    entry = first_quote(path, signal["signal_time"], strict=True)
    if entry is None:
        return {**base, "status": "excluded_entry_quote"}
    if not 0 < entry.entry_ask < width:
        return {**base, "status": "excluded_entry_debit", "entry_ask": float(entry.entry_ask)}
    cutoff = session_end(day) - pd.Timedelta(minutes=15)
    target_exit = min(entry.timestamp + pd.Timedelta(minutes=60), cutoff)
    if entry.timestamp >= target_exit:
        return {**base, "status": "excluded_after_exit_cutoff"}
    exit_row = first_quote(path, target_exit, strict=False)
    if exit_row is None or exit_row.timestamp > cutoff:
        return {**base, "status": "excluded_exit_quote", "entry_time": entry.timestamp,
                "entry_ask": float(entry.entry_ask), "target_exit": target_exit}
    ledger = account(entry.entry_ask, exit_row.liquidation_bid, entry.mark, exit_row.mark)
    return {**base, "status": "completed", "entry_time": entry.timestamp,
            "exit_time": exit_row.timestamp, "entry_ask": float(entry.entry_ask),
            "liquidation_bid": float(exit_row.liquidation_bid),
            "entry_mark": float(entry.mark), "exit_mark": float(exit_row.mark),
            "minutes_held": (exit_row.timestamp - entry.timestamp).total_seconds() / 60,
            **ledger}


def metrics(rows: list[dict], model: str) -> dict:
    complete = [r for r in rows if r["status"] == "completed"]
    pnl = np.array([r[model] for r in complete], dtype=float)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    equity = np.r_[0., pnl.cumsum()]
    risk_key = "stressed_initial_risk_dollars" if model == "stressed" else "initial_risk_dollars"
    return {"completed": len(pnl), "no_signal": sum(r["status"] == "no_signal" for r in rows),
            "excluded": sum(r["status"].startswith("excluded") for r in rows),
            "net_dollars": float(pnl.sum()), "expectancy_dollars": float(pnl.mean()) if len(pnl) else None,
            "win_rate": float((pnl > 0).mean()) if len(pnl) else None,
            "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
            "average_win": float(wins.mean()) if len(wins) else None,
            "average_loss": float(losses.mean()) if len(losses) else None,
            "max_trade_close_drawdown": float((np.maximum.accumulate(equity) - equity).max()),
            "top3_wins_removed_net": float(pnl.sum() - np.sort(wins)[-3:].sum()),
            "expectancy_r": float(np.mean([r[model] / r[risk_key] for r in complete])) if complete else None,
            "exposure_minutes": float(sum(r["minutes_held"] for r in complete)),
            "negative_liquidations": sum(r["liquidation_bid"] < 0 for r in complete),
            "capital_return": None,
            "capital_return_reason": "No funded-account capital denominator; research 1-lot dollars only."}


def summarize(rows: list[dict], days: list[str]) -> dict:
    out = {}
    midpoint_date = days[len(days) // 2]
    for arm in ARMS:
        for width in WIDTHS:
            selected = [r for r in rows if r["arm"] == arm and r["width"] == width]
            cell = {model: metrics(selected, model) for model in ("midpoint", "marketable", "stressed")}
            cell["status_counts"] = dict(pd.Series([r["status"] for r in selected]).value_counts().items())
            cell["chronological_halves"] = {
                label: metrics([r for r in selected if (r["date"] < midpoint_date) == first], "stressed")
                for label, first in (("first", True), ("second", False))}
            cell["monthly"] = {
                month: metrics([r for r in selected if r["date"].startswith(month)], "stressed")
                for month in sorted({r["date"][:7] for r in selected})}
            if arm != "time_1005":
                bench = {r["date"]: r for r in rows if r["arm"] == "time_1005" and r["width"] == width}
                pairs = [(r, bench[r["date"]]) for r in selected
                         if r["status"] in ("completed", "no_signal")
                         and bench[r["date"]]["status"] == "completed"]
                conditional = [(r, b) for r, b in pairs if r["status"] == "completed"]
                cell["paired_benchmark"] = {}
                for label, group in (("all_common_valid_days", pairs), ("conditional_trades", conditional)):
                    delta = np.array([r.get("stressed", 0) - b["stressed"] for r, b in group])
                    cell["paired_benchmark"][label] = {
                        "days": len(group), "strategy_net": float(sum(r.get("stressed", 0) for r, b in group)),
                        "benchmark_net": float(sum(b["stressed"] for r, b in group)),
                        "net_difference": float(delta.sum()),
                        "mean_daily_difference": float(delta.mean()) if len(delta) else None}
            out[f"{arm}_w{width}"] = cell
    return {"decision": "insufficient evidence pending review", "sessions": len(days),
            "split_date": midpoint_date, "arms": out}


def freeze(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_new(out / "specification.json", {
        "frozen_at": dt.datetime.now(dt.UTC), "period": ["2026-01-02", "2026-09-28"],
        "status": "Retrospective development; no independent holdout or trading authorization",
        "signal_source": "Approximate XSP put-call-parity forward proxy, not native index",
        "proxy": "common.derive_proxy: >=3 of up to5 low-straddle-cost call/put pairs; dispersion<=0.50",
        "opening": "[09:30,10:00) sampled proxy high/low; six valid 5-minute bins",
        "five_minute": "[start,end) bins known at end, >=4 samples, no intra-bin gap>120s",
        "failed_breakout": "First 5m close back inside opening range after prior post-10:00 close outside",
        "excursion_reversal": "Arm first close >=one full opening-range width from midpoint; first later close closer to midpoint than prior close while still on armed side; no reset/rearm",
        "direction": "CALL on downside failure; PUT on upside failure",
        "center": "Listed strike nearest opening midpoint, lower on tie", "widths": WIDTHS,
        "signal_cutoff": "13:00 ET; one signal/arm/session",
        "timing": "First usable quote strictly after signal within120s; exit >=entry+60min or calendar close-15min, within120s and not beyond cutoff",
        "benchmark": "time_1005: same midpoint target, side from 10:05 close vs midpoint, same widths/hold",
        "fees": "Assumed $0.65/contract/side = $2.60/fly/side; not verified broker all-in tariff",
        "stress": "$0.05 adverse per butterfly per transaction, $10 roundtrip additional",
        "primary": "Marketable leg-side and stressed, midpoint diagnostic only; signed negative liquidation retained",
        "data_exclusion": "Missing opening/prefix, absent/invalid/undersized legs, debit<=0 or>=width, unavailable timed exit; excluded distinct from no signal",
        "interpretation": "Snapshot quotes not complex-order fills; quote-event ages unknown; proxy may inherit quote artifacts",
        "interesting_lead_gate": "Stressed net>0, top3 removed>0, positive chronological halves, conditional paired advantage vs benchmark; descriptive only",
        "trial_budget": "2 hypotheses x2 widths plus 2 fixed-time benchmark cells; never expand from outcomes"})


def run(out: Path, limit: int | None) -> None:
    from tools.research_studies.xsp_independent.common import derive_proxy, load_session

    if not (out / "specification.json").exists():
        raise ValueError("Freeze specification first")
    if (out / "summary.json").exists():
        raise FileExistsError("Use a new run directory; do not overwrite evidence")
    paths = [p for p in sorted((ROOT / "data/thetadata/xsp_0dte/quote_1m/2026").glob("*.parquet"))
             if "2026-01-02" <= p.stem <= "2026-09-28" and is_trading_day(dt.date.fromisoformat(p.stem))]
    if limit:
        paths = paths[:limit]
    manifest = {"started": dt.datetime.now(dt.UTC), "git_sha": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "spec_sha256": digest(out / "specification.json"), "sources": {}, "inputs": [],
        "command": " ".join(__import__("sys").argv),
        "versions": {"pandas": pd.__version__, "numpy": np.__version__}, "limit": limit}
    for p in (Path(__file__), Path(__file__).with_name("common.py"),
              ROOT / "src/butterfly_guy/core/time_utils.py"):
        manifest["sources"][str(p.relative_to(ROOT))] = digest(p)
    rows = []
    for i, path in enumerate(paths):
        day = dt.date.fromisoformat(path.stem)
        quotes = load_session(path)
        proxy = derive_proxy(quotes)
        signals = entry_signals(proxy, day)
        for arm, signal in signals.items():
            for width in WIDTHS:
                rows.append({"arm": arm, **price_signal(quotes, signal, width, day)})
        manifest["inputs"].append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                                   "rows": len(quotes), "proxy_rows": len(proxy)})
        if i % 20 == 0:
            print(f"{i + 1}/{len(paths)} {day}", flush=True)
    with (out / "journal.jsonl").open("x") as f:
        for row in rows:
            f.write(json.dumps(row, default=str, allow_nan=False) + "\n")
    manifest["finished"] = dt.datetime.now(dt.UTC)
    write_new(out / "manifest.json", manifest)
    summary = summarize(rows, [p.stem for p in paths])
    write_new(out / "summary.json", summary)
    print(json.dumps({key: {m: v[m]["net_dollars"] for m in ("midpoint", "marketable", "stressed")}
                      for key, v in summary["arms"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.out)
    if args.run:
        run(args.out, args.limit)


if __name__ == "__main__":
    main()
