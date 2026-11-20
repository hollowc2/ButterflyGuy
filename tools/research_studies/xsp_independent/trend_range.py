"""Frozen retrospective XSP quote-proxy butterfly hypotheses; never connects to a broker."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/research/xsp-independent-2026-11-11/trend-range"
FEE = 2.60
SPEC = {
    "decision": "retrospective development only; no untouched holdout",
    "dates": ["2026-01-02", "2026-09-28"],
    "signal": "XSP put-call-parity approximate forward proxy, not observed index; common.py fixed quality filters",
    "T1": "first completed 5-minute close 10:05..13:00 outside 09:31..09:59 sampled opening range; center close+/-0.5 range, call up/put down",
    "T2": "14:00; 13:00..13:59 sampled range <= opening range and absolute first-to-last proxy change <=25% last-hour range; center last-hour midrange, calls",
    "B1": "unconditional 10:05; projection 0.5 opening range in direction of last proxy relative to opening midpoint; calls up/puts down",
    "B2": "unconditional 14:00; center prior-hour midrange, calls",
    "coverage": "opening range >=25 of29 minutes; hour >=54 of60; completed5min>=4 of5; no internal gap>120s; window boundary missing <=120s",
    "widths": [2, 4],
    "center": "nearest listed strike, lower strike on exact tie; no retry alternatives",
    "execution": "strictly later valid quote <=120s after signal; exit first valid quote at/after entry+60min or calendar close-15min earlier; <=120s delay capped strictly at deadline",
    "selection": "one signal attempt/session/candidate; fixed entry construction not outcome-ranked",
    "accounting": "one fly, 100 multiplier, 4contracts*$0.65 each side assumption; marketable component quotes; signed negative liquidation retained",
    "stress": "$0.05 adverse per fly per transaction ($10 round trip); midpoint is diagnostic",
    "exclusions": "missing inputs/quotes/strikes, crossed/invalid legs, component entry <=0 or>=width; no synthetic settlement or interpolation",
    "falsification": "not interesting if net<=0 under marketable+fees+stress, top3-removed net<=0, chronological halves nonpositive, or candidate fails paired baseline; passing warrants refinement only",
}


@dataclass(frozen=True)
class Signal:
    family: str
    timestamp: pd.Timestamp
    target: float
    right: str
    direction: int
    opening_range: float


def window(proxy: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, minimum: int):
    x = proxy[(proxy.timestamp >= start) & (proxy.timestamp < end)].sort_values("timestamp")
    if len(x) < minimum:
        return None
    stamps = np.array([pd.Timestamp(t).value for t in x.timestamp], dtype=np.int64)
    if (
        (stamps[0] - start.value > 120e9)
        or (end.value - stamps[-1] > 120e9)
        or (len(stamps) > 1 and np.diff(stamps).max() > 120e9)
    ):
        return None
    return x


def signals(proxy: pd.DataFrame) -> tuple[dict[str, Signal], dict[str, str]]:
    if proxy.empty:
        return {}, {"all": "no_proxy"}
    day = pd.Timestamp(proxy.timestamp.iloc[0]).normalize()

    def at(h, m=0):
        return day + pd.Timedelta(hours=h, minutes=m)

    opening = window(proxy, at(9, 31), at(10), 25)
    if opening is None:
        return {}, {"all": "opening_proxy_coverage"}
    high, low = float(opening.forward_proxy.max()), float(opening.forward_proxy.min())
    span = high - low
    if span <= 0:
        return {}, {"all": "zero_opening_range"}
    found, reasons = {}, {}
    b = window(proxy, at(10), at(10, 5), 4)
    if b is not None:
        last = float(b.forward_proxy.iloc[-1])
        direction = 1 if last >= (high + low) / 2 else -1
        found["B1"] = Signal(
            "B1",
            at(10, 5),
            last + direction * 0.5 * span,
            "CALL" if direction > 0 else "PUT",
            direction,
            span,
        )
    else:
        reasons["B1"] = "five_minute_proxy_coverage"
    for boundary in pd.date_range(at(10, 5), at(13), freq="5min"):
        b = window(proxy, boundary - pd.Timedelta(minutes=5), boundary, 4)
        if b is None:
            reasons["T1"] = "breakout_path_proxy_coverage_unknown_first_signal"
            break
        last = float(b.forward_proxy.iloc[-1])
        direction = 1 if last > high else -1 if last < low else 0
        if direction:
            found["T1"] = Signal(
                "T1",
                boundary,
                last + direction * 0.5 * span,
                "CALL" if direction > 0 else "PUT",
                direction,
                span,
            )
            break
    if "T1" not in found and "T1" not in reasons:
        reasons["T1"] = "no_breakout_before_cutoff"
    hour = window(proxy, at(13), at(14), 54)
    if hour is None:
        reasons["T2"] = reasons["B2"] = "hour_proxy_coverage"
    else:
        hour_high, hour_low = float(hour.forward_proxy.max()), float(hour.forward_proxy.min())
        found["B2"] = Signal("B2", at(14), (hour_high + hour_low) / 2, "CALL", 0, span)
        if (
            hour_high - hour_low > 0
            and hour_high - hour_low <= span
            and abs(float(hour.forward_proxy.iloc[-1] - hour.forward_proxy.iloc[0]))
            <= 0.25 * (hour_high - hour_low)
        ):
            found["T2"] = Signal("T2", at(14), (hour_high + hour_low) / 2, "CALL", 0, span)
        else:
            reasons["T2"] = "range_filter_no_setup"
    return found, reasons


def simulate(
    path: pd.DataFrame,
    signal: Signal,
    width: float,
    center: float,
    cutoff: pd.Timestamp | None = None,
) -> dict:
    cutoff = (
        cutoff
        if cutoff is not None
        else signal.timestamp.normalize() + pd.Timedelta(hours=15, minutes=45)
    )
    if signal.timestamp >= cutoff:
        return {"status": "signal_after_deadline"}
    later = path[
        (path.timestamp > signal.timestamp)
        & (path.timestamp <= signal.timestamp + pd.Timedelta(minutes=2))
    ].sort_values("timestamp")
    if later.empty:
        return {"status": "missing_entry"}
    entry = later.iloc[0]
    if entry.timestamp >= cutoff:
        return {"status": "entry_after_deadline"}
    if not np.isfinite(entry.entry_ask) or not 0 < float(entry.entry_ask) < width:
        return {"status": "invalid_debit"}
    target = min(entry.timestamp + pd.Timedelta(minutes=60), cutoff)
    exit_path = path[
        (path.timestamp >= target)
        & (path.timestamp <= target + pd.Timedelta(minutes=2))
        & (path.timestamp <= cutoff)
    ].sort_values("timestamp")
    if exit_path.empty:
        return {"status": "missing_exit"}
    exit = exit_path.iloc[0]
    debit, credit = float(entry.entry_ask), float(exit.liquidation_bid)
    if not np.isfinite(credit):
        return {"status": "invalid_exit"}
    net = (credit - debit) * 100 - 2 * FEE
    mid = (float(exit.mark) - float(entry.mark)) * 100 - 2 * FEE
    return {
        "status": "completed",
        "signal_time": str(signal.timestamp),
        "entry_time": str(entry.timestamp),
        "exit_time": str(exit.timestamp),
        "signal_target": signal.target,
        "center": center,
        "right": signal.right,
        "width": width,
        "opening_range": signal.opening_range,
        "entry_ask": debit,
        "liquidation_bid": credit,
        "entry_mark": float(entry.mark),
        "exit_mark": float(exit.mark),
        "midpoint_net": mid,
        "net": net,
        "stressed_net": net - 10,
        "initial_risk": 100 * debit + FEE,
        "risk_units": net / (100 * debit + FEE),
        "exposure_minutes": (exit.timestamp - entry.timestamp).total_seconds() / 60,
        "entry_delay_seconds": (entry.timestamp - signal.timestamp).total_seconds(),
        "exit_delay_seconds": (exit.timestamp - target).total_seconds(),
    }


def metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"completed": 0}
    f = pd.DataFrame(rows).sort_values("date")
    x = f.net.to_numpy()
    stress = f.stressed_net.to_numpy()
    eq = np.r_[0, np.cumsum(x)]
    wins = x[x > 0]
    losses = x[x < 0]
    monthly = f.groupby(f.date.str[:7]).net.sum().to_dict()
    return {
        "completed": len(f),
        "net": float(x.sum()),
        "stressed_net": float(stress.sum()),
        "midpoint_net": float(f.midpoint_net.sum()),
        "expectancy": float(x.mean()),
        "win_rate": float((x > 0).mean()),
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
        "average_win": float(wins.mean()) if len(wins) else None,
        "average_loss": float(losses.mean()) if len(losses) else None,
        "drawdown_trade_close": float((np.maximum.accumulate(eq) - eq).max()),
        "top3_removed_net": float(x.sum() - np.sort(wins)[-3:].sum()),
        "stressed_top3_removed_net": float(stress.sum() - np.sort(stress[stress > 0])[-3:].sum()),
        "average_risk_units": float(f.risk_units.mean()),
        "average_initial_risk": float(f.initial_risk.mean()),
        "exposure_minutes": float(f.exposure_minutes.sum()),
        "monthly_net": monthly,
        "negative_liquidations": int((f.liquidation_bid < 0).sum()),
        "h1_net": float(f.loc[f.date < "2026-07-01", "net"].sum()),
        "h2_net": float(f.loc[f.date >= "2026-07-01", "net"].sum()),
    }


def sha(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT / "run-02")
    parser.add_argument("--start", default="2026-01-02")
    parser.add_argument("--end", default="2026-09-28")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "spec.json").write_text(json.dumps(SPEC, indent=2))
    sys.path.insert(0, str(Path(__file__).parent))
    from common import derive_proxy, fly_quotes, load_session, session_end

    paths = sorted((ROOT / "data/thetadata/xsp_0dte/quote_1m/2026").glob("*.parquet"))
    paths = [p for p in paths if args.start <= p.stem <= args.end]
    trials = []
    inputs = []
    errors = Counter()
    excluded = Counter()
    statuses = []
    for n, p in enumerate(paths):
        quotes = load_session(p)
        proxy = derive_proxy(quotes)
        found, reasons = signals(proxy)
        for k, v in reasons.items():
            excluded[f"{k}/{v}"] += 1
        for family in ["T1", "T2", "B1", "B2"]:
            reason = reasons.get(family, reasons.get("all"))
            if family not in found:
                statuses.append(
                    {
                        "date": p.stem,
                        "family": family,
                        "status": "valid_no_setup"
                        if reason in {"range_filter_no_setup", "no_breakout_before_cutoff"}
                        else "data_excluded",
                        "reason": reason,
                    }
                )
        strikes = np.sort(quotes.strike.unique())
        for family, signal in found.items():
            center = float(min(strikes, key=lambda k: (abs(k - signal.target), k)))
            for width in [2, 4]:
                if center - width not in strikes or center + width not in strikes:
                    result = {"status": "missing_strikes"}
                else:
                    fq = fly_quotes(quotes, center, width, signal.right)
                    result = simulate(
                        fq, signal, width, center, session_end(p.stem) - pd.Timedelta(minutes=15)
                    )
                row = {"date": p.stem, "family": family, "width": width, **result}
                trials.append(row)
                statuses.append(
                    {
                        "date": p.stem,
                        "family": family,
                        "width": width,
                        "status": row["status"],
                        "reason": row["status"],
                    }
                )
                if row["status"] != "completed":
                    errors[f"{family}/{row['status']}"] += 1
        inputs.append(
            {"path": str(p.relative_to(ROOT)), "sha256": sha(p), "proxy_rows": len(proxy)}
        )
        if n % 20 == 0:
            print(f"processed {n + 1}/{len(paths)}", flush=True)
    (args.out / "trials.jsonl").write_text("".join(json.dumps(r) + "\n" for r in trials))
    (args.out / "session-status.jsonl").write_text("".join(json.dumps(r) + "\n" for r in statuses))
    summaries = {}
    completed = [r for r in trials if r["status"] == "completed"]
    for family in ["T1", "T2", "B1", "B2"]:
        for width in [2, 4]:
            rs = [r for r in completed if r["family"] == family and r["width"] == width]
            summaries[f"{family}/w{width}"] = metrics(rs)
            if family in ["T1", "T2"]:
                base = "B1" if family == "T1" else "B2"
                matched = {
                    r["date"]: r for r in completed if r["family"] == base and r["width"] == width
                }
                pairs = [r for r in rs if r["date"] in matched]
                summaries[f"{family}/w{width}"]["paired_baseline"] = {
                    "count": len(pairs),
                    "candidate_net": sum(r["net"] for r in pairs),
                    "baseline_net": sum(matched[r["date"]]["net"] for r in pairs),
                    "difference": sum(r["net"] - matched[r["date"]]["net"] for r in pairs),
                }
                no_setup = {
                    r["date"]
                    for r in statuses
                    if r["family"] == family and r["status"] == "valid_no_setup"
                }
                by_date = {r["date"]: r for r in rs}
                all_dates = sorted(set(matched) & (set(by_date) | no_setup))
                candidate_values = [by_date[d]["net"] if d in by_date else 0.0 for d in all_dates]
                baseline_values = [matched[d]["net"] for d in all_dates]
                summaries[f"{family}/w{width}"]["paired_all_eligible_days"] = {
                    "count": len(all_dates),
                    "valid_no_setup_days": len(set(all_dates) & no_setup),
                    "candidate_net": sum(candidate_values),
                    "baseline_net": sum(baseline_values),
                    "difference": sum(candidate_values) - sum(baseline_values),
                    "mean_daily_difference": (sum(candidate_values) - sum(baseline_values))
                    / len(all_dates)
                    if all_dates
                    else None,
                    "no_trade_days_are_zero": True,
                    "missing_execution_days_excluded": True,
                }

    result = {
        "spec": SPEC,
        "sessions_in_archive": len(paths),
        "summary": summaries,
        "excluded_signals": dict(excluded),
        "excluded_trade_attempts": dict(errors),
        "decision": "refine only if frozen gates pass; all retrospective and quote-derived proxy",
        "limitations": [
            "No complex-order fills; leg-market quote model only",
            "Unknown NBBO event age",
            "Proxy direction and strike targets derived from option mids; not official XSP levels",
            "No account-capital return; unequal initial dollar risk across widths",
            "Drawdown from completed-trade closes only",
            "No settlement inference; scheduled early closes cap liquidation15min before close",
            "No slippage-dependent selection or order partial fills/rejections",
            "Input windows previously used in other research; no fresh holdout",
        ],
    }
    (args.out / "summary.json").write_text(json.dumps(result, indent=2))
    mapping = {
        "family": "variant",
        "signal_time": "signal_ts",
        "entry_time": "entry_ts",
        "exit_time": "exit_ts",
        "midpoint_net": "pnl_mark",
        "net": "pnl_marketable",
        "stressed_net": "pnl_stressed",
    }
    journal = pd.DataFrame(completed).rename(columns=mapping)
    journal.to_csv(args.out / "journal.csv", index=False)
    manifest = {
        "git_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "dirty_paths": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ).splitlines(),
        "sources": {
            str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
            "src/butterfly_guy/research/event_calendar.py": sha(
                ROOT / "src/butterfly_guy/research/event_calendar.py"
            ),
            "src/butterfly_guy/research/data/market_events_v1.csv": sha(
                ROOT / "src/butterfly_guy/research/data/market_events_v1.csv"
            ),
            "tools/research_studies/xsp_independent/common.py": sha(
                Path(__file__).with_name("common.py")
            ),
        },
        "inputs": inputs,
        "command": sys.argv,
        "python": sys.version,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "created_utc": str(pd.Timestamp.now(tz="UTC")),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
