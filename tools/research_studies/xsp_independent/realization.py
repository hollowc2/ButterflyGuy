"""Frozen XSP butterfly lifecycle study, offline retrospective development only.

Reuse entry-only decisions. Never condition admission on an earlier exit replay.
Sampled quote/proxy triggers require a later fill; no interpolation or oracle exits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from butterfly_guy.core.time_utils import is_trading_day
from tools.research_studies.xsp_independent.common import (
    derive_proxy,
    fly_quotes,
    load_session,
    session_end,
)
from tools.research_studies.xsp_independent.mean_reversion import entry_signals
from tools.research_studies.xsp_independent.trend_range import signals as trend_signals

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = ROOT / "reports/research/xsp-realization-2026-11-11/realization/run-01"
SETTLEMENTS = ROOT / "reports/research/xsp-realization-2026-11-11/settlement/settlements-native.csv"
FEE = 2.60
STRESS = 0.05
FAMILIES = ("MR1", "MR2", "T1", "T2")
POLICIES = ("baseline_60m", "center_cross", "net_profit_25pct", "settlement")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def new_json(path: Path, value: object) -> None:
    with path.open("x") as f:
        json.dump(value, f, indent=2, default=str, allow_nan=False)
        f.write("\n")


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("x") as f:
        for row in rows:
            f.write(json.dumps(row, default=str, allow_nan=False) + "\n")


def select_quote(path: pd.DataFrame, when: pd.Timestamp, *, later: bool,
                 cutoff: pd.Timestamp) -> pd.Series | None:
    mask = path.timestamp.gt(when) if later else path.timestamp.ge(when)
    x = path[mask & path.timestamp.le(when + pd.Timedelta(minutes=2))
             & path.timestamp.le(cutoff)]
    return x.iloc[0] if len(x) else None


def get_signals(proxy: pd.DataFrame, day: dt.date) -> dict[str, dict]:
    reversion = entry_signals(proxy, day)
    trend, reasons = trend_signals(proxy)
    out = {}
    for family, key in (("MR1", "failed_breakout"), ("MR2", "excursion_reversal")):
        out[family] = dict(reversion[key])
    for family in ("T1", "T2"):
        if family in trend:
            s = trend[family]
            out[family] = {"status": "signal", "signal_time": s.timestamp,
                           "target": s.target, "right": s.right,
                           "opening_range": s.opening_range}
        else:
            reason = reasons.get("all", reasons.get(family, "unknown_signal_state"))
            out[family] = {
                "status": "no_signal" if reason in (
                    "no_breakout_before_cutoff", "range_filter_no_setup") else "excluded_signal",
                "signal_reason": reason}
    return out


def make_entry(quotes: pd.DataFrame, signal: dict, day: dt.date, family: str,
               width: int) -> tuple[dict, pd.DataFrame | None]:
    base = {"date": str(day), "family": family, "width": width, **signal}
    if signal["status"] != "signal":
        return base, None
    # Auditor established identical raw strike universe at09:31 for all185 dates.
    strikes = np.sort(quotes.strike.unique())
    center = float(strikes[np.argmin(abs(strikes - signal["target"]))])
    path = fly_quotes(quotes, center, width, signal["right"])
    cutoff = session_end(day) - pd.Timedelta(minutes=15)
    entry = select_quote(path, signal["signal_time"], later=True, cutoff=cutoff)
    base.update(center=center, cutoff=cutoff)
    if entry is None:
        return {**base, "status": "excluded_entry_quote"}, None
    if entry.timestamp >= cutoff:
        return {**base, "status": "excluded_entry_deadline"}, None
    debit = float(entry.entry_ask)
    if not 0 < debit < width:
        return {**base, "status": "excluded_entry_debit", "entry_ask": debit}, None
    return {**base, "status": "accepted", "entry_time": entry.timestamp,
            "entry_ask": debit, "entry_mark": float(entry.mark),
            "initial_risk_dollars": 100 * debit + FEE,
            "stressed_initial_risk_dollars": 100 * (debit + STRESS) + FEE}, path


def first_cross(proxy: pd.DataFrame, entry: dict) -> dict:
    """First knowable post-entry sampled equality or strict sign change about center."""
    start, end, center = entry["entry_time"], entry["cutoff"], entry["center"]
    anchor = proxy[proxy.timestamp == start]
    if anchor.empty:
        return {"status": "excluded_center_anchor_missing", "gap_time": start}
    previous = anchor.iloc[-1]
    last_ts, last_distance = previous.timestamp, float(previous.forward_proxy) - center
    for row in proxy[(proxy.timestamp > start) & (proxy.timestamp < end)].itertuples():
        gap = (row.timestamp - last_ts).total_seconds()
        if gap > 120:
            return {"status": "excluded_center_prefix_gap", "gap_time": row.timestamp,
                    "gap_seconds": gap}
        distance = float(row.forward_proxy) - center
        if distance == 0 or last_distance * distance < 0:
            return {"status": "trigger", "trigger_time": row.timestamp,
                    "trigger_forward_proxy": float(row.forward_proxy),
                    "previous_proxy_time": last_ts, "previous_distance": last_distance}
        last_ts, last_distance = row.timestamp, distance
    gap = (end - last_ts).total_seconds()
    if gap > 120:
        return {"status": "excluded_center_terminal_gap", "gap_time": end,
                "gap_seconds": gap}
    return {"status": "no_trigger"}


def first_profit(path: pd.DataFrame, entry: dict) -> dict:
    """Nominal net liquidation threshold is observed, then acted on next snapshot."""
    last_ts = entry["entry_time"]
    threshold = 0.25 * entry["initial_risk_dollars"]
    for row in path[(path.timestamp > last_ts) & (path.timestamp < entry["cutoff"])].itertuples():
        gap = (row.timestamp - last_ts).total_seconds()
        if gap > 120:
            return {"status": "excluded_profit_prefix_gap", "gap_time": row.timestamp,
                    "gap_seconds": gap, "profit_threshold_dollars": threshold}
        net = 100 * (float(row.liquidation_bid) - entry["entry_ask"]) - 2 * FEE
        if net >= threshold:
            return {"status": "trigger", "trigger_time": row.timestamp,
                    "trigger_liquidation_bid": float(row.liquidation_bid),
                    "trigger_net_dollars": net, "profit_threshold_dollars": threshold}
        last_ts = row.timestamp
    gap = (entry["cutoff"] - last_ts).total_seconds()
    if gap > 120:
        return {"status": "excluded_profit_terminal_gap", "gap_time": entry["cutoff"],
                "gap_seconds": gap, "profit_threshold_dollars": threshold}
    return {"status": "no_trigger", "profit_threshold_dollars": threshold}


def liquidation_cash(entry: dict, exit_row: pd.Series) -> dict:
    credit = float(exit_row.liquidation_bid)
    net = 100 * (credit - entry["entry_ask"]) - 2 * FEE
    stressed = net - 200 * STRESS
    return {"status": "completed", "exit_time": exit_row.timestamp,
            "liquidation_bid": credit, "exit_mark": float(exit_row.mark),
            "marketable_net": net, "stressed_net": stressed,
            "midpoint_net": 100 * (float(exit_row.mark) - entry["entry_mark"]) - 2 * FEE,
            "marketable_r": net / entry["initial_risk_dollars"],
            "stressed_r": stressed / entry["stressed_initial_risk_dollars"],
            "closing_fee_dollars": FEE, "closing_stress_dollars": 100 * STRESS,
            "exposure_minutes": (exit_row.timestamp - entry["entry_time"]).total_seconds() / 60}


def settle_cash(entry: dict, settlement: dict | None) -> dict:
    if settlement is None:
        return {"status": "excluded_missing_settlement"}
    level = float(settlement["settlement"])
    if not np.isfinite(level) or level <= 0:
        return {"status": "excluded_invalid_settlement"}
    intrinsic = max(0., entry["width"] - abs(level - entry["center"]))
    net = 100 * (intrinsic - entry["entry_ask"]) - FEE
    stressed = net - 100 * STRESS
    expiry = session_end(entry["date"])
    return {"status": "completed", "exit_time": expiry,
            "settlement": level, "settlement_source": settlement.get("source_type"),
            "settlement_intrinsic": intrinsic, "marketable_net": net,
            "stressed_net": stressed,
            "midpoint_net": 100 * (intrinsic - entry["entry_mark"]) - FEE,
            "marketable_r": net / entry["initial_risk_dollars"],
            "stressed_r": stressed / entry["stressed_initial_risk_dollars"],
            "closing_fee_dollars": 0., "closing_stress_dollars": 0.,
            "exposure_minutes": (expiry - entry["entry_time"]).total_seconds() / 60}


def evaluate_policy(entry: dict, path: pd.DataFrame, proxy: pd.DataFrame,
                    policy: str, settlement: dict | None = None) -> dict:
    base = {**entry, "policy": policy}
    if policy == "settlement":
        return {**base, "exit_reason": "native_published_settlement", **settle_cash(entry, settlement)}
    if policy == "baseline_60m":
        deadline = min(entry["entry_time"] + pd.Timedelta(minutes=60), entry["cutoff"])
        row = select_quote(path, deadline, later=False, cutoff=entry["cutoff"])
        if row is None:
            return {**base, "status": "excluded_baseline_exit_quote", "exit_deadline": deadline}
        return {**base, "exit_reason": "fixed_60m", "exit_deadline": deadline,
                **liquidation_cash(entry, row)}
    trigger = first_cross(proxy, entry) if policy == "center_cross" else first_profit(path, entry)
    if trigger["status"].startswith("excluded"):
        return {**base, **trigger}
    if trigger["status"] == "trigger":
        row = select_quote(path, trigger["trigger_time"], later=True, cutoff=entry["cutoff"])
        if row is None:
            return {**base, **trigger, "status": "excluded_trigger_exit_quote"}
        return {**base, **trigger, "exit_reason": "first_trigger", **liquidation_cash(entry, row)}
    row = select_quote(path, entry["cutoff"], later=False, cutoff=entry["cutoff"])
    if row is None:
        return {**base, **trigger, "status": "excluded_fallback_exit_quote"}
    return {**base, **trigger, "exit_reason": "scheduled_close_minus_15m", **liquidation_cash(entry, row)}


def geometry(proxy: pd.DataFrame, entry: dict) -> dict:
    p = proxy[(proxy.timestamp >= entry["entry_time"]) & (proxy.timestamp <= entry["cutoff"])]
    if p.empty:
        return {"proxy_observations": 0, "geometry_status": "unavailable"}
    distance = abs(p.forward_proxy.to_numpy(float) - entry["center"])
    times = pd.DatetimeIndex(p.timestamp)
    anchor_gap = (times[0] - entry["entry_time"]).total_seconds()
    terminal_gap = (entry["cutoff"] - times[-1]).total_seconds()
    # Parquet may retain microsecond resolution; asi8 is not guaranteed nanoseconds.
    internal = pd.Series(times).diff().dt.total_seconds().dropna().to_numpy()
    largest = float(max(anchor_gap, terminal_gap, internal.max() if len(internal) else 0))
    cross = first_cross(proxy, entry)
    anchor = proxy[proxy.timestamp == entry["entry_time"]]
    forward = float(anchor.forward_proxy.iloc[-1]) if len(anchor) else None
    return {"proxy_observations": len(p), "tent_samples": int((distance <= entry["width"]).sum()),
            "central_band_samples": int((distance <= entry["width"] / 4).sum()),
            "tent_fraction_of_observed_samples": float((distance <= entry["width"]).mean()),
            "central_fraction_of_observed_samples": float((distance <= entry["width"] / 4).mean()),
            "max_proxy_gap_seconds": largest,
            "geometry_status": "complete_120s" if largest <= 120 else "gapped",
            "entry_forward_proxy": forward,
            "entry_inside_tent": bool(abs(forward - entry["center"]) <= entry["width"]) if forward is not None else None,
            "center_cross_status": cross["status"],
            "first_center_cross_time": cross.get("trigger_time")}


def stats(rows: list[dict], split: str) -> dict:
    done = [r for r in rows if r["status"] == "completed"]
    out = {"cases": len(rows), "completed": len(done), "statuses": dict(Counter(r["status"] for r in rows)),
           "exit_reasons": dict(Counter(r.get("exit_reason", "excluded") for r in rows)),
           "capital_return": None, "drawdown_resolution": "trade close; not intraday"}
    for model in ("midpoint_net", "marketable_net", "stressed_net"):
        values = np.array([r[model] for r in done], dtype=float)
        wins, losses = values[values > 0], values[values < 0]
        eq = np.r_[0., values.cumsum()]
        out[model] = {"total": float(values.sum()),
                      "expectancy": float(values.mean()) if len(values) else None,
                      "win_rate": float((values > 0).mean()) if len(values) else None,
                      "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
                      "average_win": float(wins.mean()) if len(wins) else None,
                      "average_loss": float(losses.mean()) if len(losses) else None,
                      "top3_removed": float(values.sum() - np.sort(wins)[-3:].sum()),
                      "max_drawdown": float((np.maximum.accumulate(eq) - eq).max()),
                      "p10_median_p90": [float(x) for x in np.percentile(values, [10, 50, 90])] if len(values) else None,
                      "halves": {label: float(sum(r[model] for r in done if (r["date"] < split) == first))
                                 for label, first in (("first", True), ("second", False))},
                      "monthly": {month: float(sum(r[model] for r in done if r["date"].startswith(month)))
                                  for month in sorted({r["date"][:7] for r in rows})}}
    out["average_stressed_r"] = float(np.mean([r["stressed_r"] for r in done])) if done else None
    out["exposure_minutes"] = float(sum(r["exposure_minutes"] for r in done))
    return out


def paired(rows: list[dict], policy: str) -> dict:
    baseline = {r["date"]: r for r in rows if r["policy"] == "baseline_60m"}
    pairs = [(r, baseline[r["date"]]) for r in rows if r["policy"] == policy
             and r["status"] == "completed" and baseline[r["date"]]["status"] == "completed"]
    return {"common_completed_entries": len(pairs),
            "candidate_stressed": float(sum(r["stressed_net"] for r, b in pairs)),
            "baseline_stressed": float(sum(b["stressed_net"] for r, b in pairs)),
            "stressed_difference": float(sum(r["stressed_net"] - b["stressed_net"] for r, b in pairs)),
            "candidate_marketable": float(sum(r["marketable_net"] for r, b in pairs)),
            "baseline_marketable": float(sum(b["marketable_net"] for r, b in pairs)),
            "baseline_missing_but_candidate_completed": sum(
                r["policy"] == policy and r["status"] == "completed"
                and baseline[r["date"]]["status"] != "completed" for r in rows)}


def summarize(entries: list[dict], rows: list[dict], days: list[str]) -> dict:
    split = days[len(days) // 2]
    cells = {}
    for family in FAMILIES:
        for width in (2, 4):
            cell_entries = [r for r in entries if r["family"] == family and r["width"] == width]
            x = [r for r in rows if r["family"] == family and r["width"] == width]
            cells[f"{family}_w{width}"] = {
                "entry_statuses": dict(Counter(r["status"] for r in cell_entries)),
                "geometry": {"accepted": sum(r["status"] == "accepted" for r in cell_entries),
                             "complete_prefix_to_cutoff": sum(r.get("geometry_status") == "complete_120s" for r in cell_entries),
                             "center_cross_known": sum(r.get("center_cross_status") == "trigger" for r in cell_entries),
                             "ever_observed_inside_tent": sum(r.get("tent_samples", 0) > 0 for r in cell_entries),
                             "ever_observed_central_band": sum(r.get("central_band_samples", 0) > 0 for r in cell_entries)},
                "policies": {p: {**stats([r for r in x if r["policy"] == p], split),
                                 "paired_baseline": paired(x, p)} for p in POLICIES}}
    return {"decision": "pending independent review", "sessions": len(days),
            "split_date": split, "entry_cells": 8, "exit_policies": POLICIES,
            "data_interpretation": "Retrospective development, approximate forward and component quotes",
            "cells": cells}


def freeze(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    new_json(out / "specification.json", {
        "frozen_at": dt.datetime.now(dt.UTC), "dates": ["2026-01-02", "2026-09-28"],
        "development_only": True, "entries": "Frozen MR1/MR2/T1/T2 signal functions, widths2/4; reconstruct ENTRY-ONLY admission irrespective of old60m exits",
        "baseline": "Unchanged first usable quote at/afterentry+60m orcutoff earlier;<=120sdelay<=cutoff",
        "center": "First postentry equality or strict signflip aboutcenter, exactentrytimestamp proxy REQUIRED orpathunknown; then first strictlylater usablequote<=120s<=cutoff. Entryatcenter thenaway isnotcross.",
        "profit": "First nominal component liquidation net100*(bid−entryask)−5.20>=.25*(100*entryask+2.60); then strictlylaterquote<=120s<=cutoff. Actualfillprofitneednotmeetthreshold. Stress SAMEdecisions.",
        "fallback": "If no trigger on complete inputprefix, predeclared liquidation atcalendarclose−15m; unavailablequote excluded. Trigger search strictlybeforecutoff; cutoffobservationdoesnotcreateareactivefill.",
        "gaps": "No interpolation. Proxy-prefixgap>120s invalidatescenterfirsttrigger; quote-prefixgap>120s invalidatesprofitfirsttrigger. Missingtriggerfill<=120s excludes, noretry. Requiredinputpathsseparate.",
        "settlement": "Only auditorattributed native Cboe published XSP settlement, as published without derivation or rerounding; missingnot0. Intrinsic100*max(0,width−abs(S−center)) lessentryask100 andopeningfee2.60. Stressentryonly5;noexitfee/slippage. Earlier3dpformula input superseded and unused.",
        "geometry": "Sampled tentabs(F−center)<=width; centralband<=width/4; occupancy fractions of OBSERVEDsamples, gaps disclosed; no oraclemaxexit.",
        "costs": "Assumed fourcontract65cfee eachside; adverse .05 netpackagepoints/transaction. No fundingaccountreturn or executionclaim.",
        "trials": "8 frozen entrycells x4exitpolicies, no entryorparametersearch; all existinghistorydevelopment",
        "lead_gate": "Rootindependentreview: stressednetpositive,top3removedpositive,bothchronologicalhalvespositive andpaired60min advantage oncommonlycompletedentries;coveragequalifiesinterpretation,no promotion"})


def run(out: Path, settlements_path: Path, limit: int | None) -> None:
    if not (out / "specification.json").exists():
        raise ValueError("Freeze specification before evaluating")
    settlement_df = pd.read_csv(settlements_path, dtype={"date": str})
    required = {"date", "settlement", "source_type"}
    if not required.issubset(settlement_df) or settlement_df.date.duplicated().any():
        raise ValueError("Invalid audited settlement inputs")
    if set(settlement_df.source_type) != {"cboe_native_xsp_published_settlement"}:
        raise ValueError("Only native published XSP settlement admitted; superseded derived inputs refused")
    settlement_manifest_path = settlements_path.with_name("native-manifest.json")
    settlement_manifest = json.loads(settlement_manifest_path.read_text())
    if (settlement_manifest.get("source_type") != "cboe_native_xsp_published_settlement"
            or settlement_manifest.get("files", {}).get(settlements_path.name) != sha(settlements_path)):
        raise ValueError("Native settlement receipt source/hash mismatch")
    settlements = {r["date"]: r for r in settlement_df.to_dict("records")}
    paths = [p for p in sorted((ROOT / "data/thetadata/xsp_0dte/quote_1m/2026").glob("*.parquet"))
             if "2026-01-02" <= p.stem <= "2026-09-28" and is_trading_day(dt.date.fromisoformat(p.stem))]
    if limit:
        paths = paths[:limit]
    manifest = {"started_at": dt.datetime.now(dt.UTC),
                "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "dirty_status": subprocess.check_output(["git", "status", "--short"], text=True),
                "command": sys.argv, "spec_sha256": sha(out / "specification.json"),
                "settlement_input": str(settlements_path),
                "settlement_manifest": str(settlement_manifest_path),
                "settlement_manifest_sha256": sha(settlement_manifest_path),
                "settlement_sha256": sha(settlements_path), "inputs": [], "sources": {},
                "pandas": pd.__version__, "numpy": np.__version__, "limit": limit}
    for p in [Path(__file__), Path(__file__).with_name("common.py"),
              Path(__file__).with_name("mean_reversion.py"), Path(__file__).with_name("trend_range.py"),
              ROOT / "src/butterfly_guy/core/time_utils.py",
              ROOT / "src/butterfly_guy/research/event_calendar.py",
              ROOT / "src/butterfly_guy/research/data/market_events_v1.csv"]:
        manifest["sources"][str(p.relative_to(ROOT))] = sha(p)
    entries, journal = [], []
    for i, path in enumerate(paths):
        day = dt.date.fromisoformat(path.stem)
        quotes = load_session(path)
        proxy = derive_proxy(quotes)
        for family, signal in get_signals(proxy, day).items():
            for width in (2, 4):
                entry, fly_path = make_entry(quotes, signal, day, family, width)
                if entry["status"] == "accepted":
                    entry.update(geometry(proxy, entry))
                    for policy in POLICIES:
                        journal.append(evaluate_policy(entry, fly_path, proxy, policy, settlements.get(str(day))))
                entries.append(entry)
        manifest["inputs"].append({"path": str(path.relative_to(ROOT)), "sha256": sha(path),
                                   "rows": len(quotes), "proxy_observations": len(proxy)})
        if i % 20 == 0:
            print(f"{i + 1}/{len(paths)} {day}", flush=True)
    write_rows(out / "entries.jsonl", entries)
    write_rows(out / "journal.jsonl", journal)
    manifest["finished_at"] = dt.datetime.now(dt.UTC)
    new_json(out / "manifest.json", manifest)
    summary = summarize(entries, journal, [p.stem for p in paths])
    new_json(out / "summary.json", summary)
    print(json.dumps({k: {p: {"n": z["completed"], "stress": z["stressed_net"]["total"]}
                                for p, z in v["policies"].items()} for k, v in summary["cells"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--settlements", type=Path, default=SETTLEMENTS)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.freeze:
        freeze(args.out)
    if args.run:
        run(args.out, args.settlements, args.limit)


if __name__ == "__main__":
    main()
