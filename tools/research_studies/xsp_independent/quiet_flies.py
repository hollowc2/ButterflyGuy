"""Frozen quiet-day XSP iron/debit and OTM-body study; offline research only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent.common import (
    calendar,
    derive_proxy,
    load_session,
    session_end,
    valid_quotes,
)
from tools.research_studies.xsp_independent.mean_reversion import digest, wall, write_new
from tools.research_studies.xsp_independent.realization import SETTLEMENTS
from tools.research_studies.xsp_independent.settlement_data import tent_value
from tools.research_studies.xsp_independent.trend_range import window

ROOT = Path(__file__).resolve().parents[3]
ARMS = ("atm_all", "atm_quiet", "otm_drift_quiet", "otm_pair_quiet")
FORMS = ("CALL", "PUT", "IRON")
WIDTHS = (2, 4)
SUPPORT = ROOT / "data/research_cache/local_support_v1"
SPEC = {
    "period": ["2026-01-02", "2026-09-28"],
    "status": "Retrospective development; previously inspected sample; no untouched holdout",
    "new_mechanism": "First-hour realized/implied quiet gate; identical-strike iron versus debit execution; OTM bodies at fixed time without breakout/reversal triggers. Original MR1/MR2/T1/T2 are not reopened.",
    "signal": "10:30 ET, completed [09:31,10:30) approximate parity forward, >=54/59 observations, boundary/internal gaps<=120s, last proxy exactly10:29. Not native spot.",
    "implied": "10:29 nearest listed strike with valid paired call/put, lower tie; straddle midpoint * sqrt(pi/2) approximates remaining normal sigma. No annualization or claim of model-free expected move.",
    "forecast": "sqrt(sum(proxy increments squared)/sum(elapsed minutes) * minutes from10:30 to calendar close); gaps<=2min normalized by elapsed time, no interpolation",
    "quiet": "forecast/implied<=0.75 AND absolute net proxy change/sum absolute increments<=0.30 AND no visible scheduled CPI/NFP/PCE/FOMC date. Provisional fixed thresholds, no optimization; calendar absence is not evidence of no other catalysts.",
    "arms": {"atm_all": "Unconditional ATM benchmark on same feature-covered sessions",
             "atm_quiet": "ATM only when quiet gate passes",
             "otm_drift_quiet": "Quiet gate; target proxy+sign(first-hour drift)*0.5straddle, strictly beyond proxy; zero drift no signal",
             "otm_pair_quiet": "Quiet gate; simultaneous upper/lower bodies proxy+/-0.5straddle, each strictly beyond proxy; TWO independently priced flies, 8 gross contracts, no netting"},
    "geometry": "Nearest 10:29 listed strike to target, lower tie, constrained to correct side for OTM bodies; no retry alternative strikes. OTM refers to BODY relative to forward proxy, wings may be ITM. widths2,4.",
    "forms": "Same centers/wings CALL +1/-2/+1, PUT +1/-2/+1; credit IRON +1 lower put,-1 center put,-1 center call,+1 upper call. Same expiry payoff tent minus width for IRON.",
    "entry": "First synchronous snapshot strictly after10:30, <=10:32; transaction-needed opening sizes only, aggregated by contract and side for pairs. Positive bid and enough bid size required on sells; buys need positive ask and ask size, may have zero bid/size. Reject crossed/negative/nonfinite prices. Preserve all entries regardless of terminal quote coverage.",
    "admission": "Each debit fly 0<debit<width; each iron0<credit<width; stress can exceed width; no outcome-based construction choice",
    "terminal": "Always hold to native published XSP cash settlement. No targets/stops/reentries, no closing quote/commission. Missing settlement remains unresolved, never zero.",
    "costs": "$0.65/gross contract opening fee assumption, $0.05 adverse/package opening stress. Pair costs double. Broker/exchange/exercise fees unverified; midpoint diagnostic only; no demonstrated complex-order fills or leg update ages.",
    "sizing": "One fly or fixed two-fly pair/session; unequal risk, compare $ and initial-risk units. No funded-account return/margin model. No overlapping sessions.",
    "budget": "4arms x2widths x3forms=24 correlated cells; no outcome-led expansion",
    "gate": "Refine only if complete terminal cohort, stressed net>0, positive both chronological halves, positive after removing top3 wins, and positive paired daily difference versus same-form/width unconditional ATM on common valid days. Otherwise reject exact cell or insufficient evidence; no promotion from this inspected sample.",
}


def specification(signal_source: str, quiet_gate: str = "absolute") -> dict:
    if quiet_gate == "relative":
        if signal_source != "spx":
            raise ValueError("Relative gate requires independent SPX signals")
        return {**specification("spx"),
                "new_hypothesis": "Both absolute realized/implied filters admitted zero non-event quiet days. Final bounded alternative asks whether RELATIVELY calm mornings, without an implied-overpricing requirement, support ATM or OTM pin payoffs. This removes a distinct volatility-risk-premium condition; it is not a profitable-result-driven threshold search.",
                "quiet": "Current first-hour volatility rate normalized by current index proxy <=lower tercile (linear quantile1/3) of PRIOR20 feature-covered session rates; efficiency<=0.30; no visible CPI/NFP/PCE/FOMC. Previous20 observations exclude current/future session. Initial20 covered sessions are warmup exclusions for all arms. No realized/implied ratio gate; ratio retained as diagnostic.",
                "budget": "Final24-cell relative-calm experiment, after2x24 absolute-filter cells (72 correlated campaign cells total). Stop after this run regardless of outcomes; no source/threshold/exit search."}
    if signal_source == "parity":
        return SPEC
    if signal_source != "spx":
        raise ValueError("unknown signal source")
    return {**SPEC,
            "new_evidence": "First parity run admitted zero quiet days. Replace noisy option-implied increments with independent recorded SPX ticks /10; same numerical gate, entry time, arms, geometry and costs. This is an additional retrospective 24-cell trial, not independent validation.",
            "signal": "10:30 ET, completed [09:31,10:30) observed SPX last tick per minute divided by10; minute-start labels available only at minute-end; >=54/59 observations and gaps<=120s, last minute10:29. Cross-index proxy, NOT native XSP. No interpolation; missing spot prefix remains exclusion.",
            "implied": "10:29 XSP strike nearest SPX/10; paired XSP straddle midpoint*sqrt(pi/2). Independent SPX signal but XSP entry quotes/settlement remain unchanged."}


def spx_minutes(ticks: pd.DataFrame) -> pd.DataFrame:
    """Completed minute last observations; label interval start, available +1min."""
    x = ticks.loc[ticks.underlying == "SPX", ["ts_us", "price"]].copy()
    if x.ts_us.duplicated().any() or not (np.isfinite(x.price) & (x.price > 0)).all():
        raise ValueError("Invalid independent SPX observations")
    x["observed_time"] = pd.to_datetime(x.ts_us, unit="us", utc=True).dt.tz_convert(
        "America/New_York")
    x["timestamp"] = x.observed_time.dt.floor("min")
    x = x.sort_values("observed_time").groupby("timestamp", sort=True).tail(1)
    x["forward_proxy"] = x.price / 10
    return x[["timestamp", "forward_proxy"]].sort_values("timestamp").reset_index(drop=True)


def relative_calm(f: dict, prior: list[float], day: dt.date) -> tuple[dict, float | None]:
    """Lower-tercile comparison uses only earlier sessions; append current AFTER."""
    if f["status"] != "covered":
        return f, None
    remaining = (session_end(day) - f["signal_time"]).total_seconds() / 60
    rate = f["sigma_forecast"] / np.sqrt(remaining) / f["proxy"]
    if len(prior) < 20:
        return {**f, "status": "excluded_warmup", "quiet": False,
                "normalized_volatility_rate": rate, "training_sessions": len(prior)}, rate
    threshold = float(np.quantile(prior[-20:], 1 / 3))
    return {**f, "quiet": bool(rate <= threshold and f["efficiency"] <= .30
                              and not f["event_types"]),
            "normalized_volatility_rate": rate, "prior20_lower_tercile": threshold,
            "training_sessions": 20}, rate


def features(quotes: pd.DataFrame, proxy: pd.DataFrame, day: dt.date) -> dict:
    start, when = wall(day, "09:31"), wall(day, "10:30")
    prefix = window(proxy, start, when, 54)
    if prefix is None or prefix.timestamp.iloc[-1] != when - pd.Timedelta(minutes=1):
        return {"status": "excluded_prefix"}
    last = float(prefix.forward_proxy.iloc[-1])
    snap = quotes[quotes.timestamp == when - pd.Timedelta(minutes=1)]
    strikes = np.sort(snap.strike.unique())
    if not len(strikes):
        return {"status": "excluded_signal_quotes"}
    center = float(strikes[np.argmin(abs(strikes - last))])
    pair = snap[(snap.strike == center) & valid_quotes(snap)]
    if len(pair) != 2 or set(pair.right) != {"CALL", "PUT"}:
        return {"status": "excluded_straddle"}
    straddle = float(((pair.bid + pair.ask) / 2).sum())
    increments = np.diff(prefix.forward_proxy.to_numpy(dtype=float))
    elapsed = (prefix.timestamp.iloc[-1] - prefix.timestamp.iloc[0]).total_seconds() / 60
    remaining = (session_end(day) - when).total_seconds() / 60
    sigma = float(np.sqrt(np.sum(increments**2) / elapsed * remaining))
    implied = straddle * np.sqrt(np.pi / 2)
    variation = float(np.abs(increments).sum())
    drift = last - float(prefix.forward_proxy.iloc[0])
    efficiency = abs(drift) / variation if variation else 0.0
    events = sorted(set(calendar().event_types(day)) & {"CPI", "NFP", "PCE", "FOMC"})
    ratio = sigma / implied
    return {"status": "covered", "signal_time": when, "proxy": last,
            "atm": center, "straddle": straddle, "sigma_forecast": sigma,
            "implied_sigma": implied, "ratio": ratio, "efficiency": efficiency,
            "drift": drift, "event_types": events, "prefix_count": len(prefix),
            "quiet": bool(ratio <= .75 and efficiency <= .30 and not events)}


def centers_for(arm: str, f: dict, strikes: np.ndarray) -> list[float]:
    if arm in ("atm_all", "atm_quiet"):
        return [f["atm"]]
    directions = [-1, 1] if arm == "otm_pair_quiet" else [int(np.sign(f["drift"]))]
    centers = []
    for direction in directions:
        if not direction:
            return []
        candidates = strikes[(strikes - f["proxy"]) * direction > 0]
        if not len(candidates):
            return []
        target = f["proxy"] + direction * .5 * f["straddle"]
        centers.append(float(candidates[np.argmin(abs(candidates - target))]))
    return centers


def legs_for(center: float, width: int, form: str) -> list[tuple[str, float, int]]:
    if form == "IRON":
        return [("PUT", center - width, 1), ("PUT", center, -1),
                ("CALL", center, -1), ("CALL", center + width, 1)]
    if form not in ("CALL", "PUT"):
        raise ValueError("unknown construction")
    return [(form, center - width, 1), (form, center, -2), (form, center + width, 1)]


def entry_price(snapshot: pd.DataFrame, centers: list[float], width: int,
                form: str) -> dict | None:
    """Gross orders, no netting; enforce shared contract-side quantities."""
    needs = Counter()
    packages = [legs_for(c, width, form) for c in centers]
    for legs in packages:
        for right, strike, qty in legs:
            needs[(right, strike, qty > 0)] += abs(qty)
    lookup = {}
    for (right, strike, buy), size in needs.items():
        leg = snapshot[(snapshot.right == right) & (snapshot.strike == strike)]
        if len(leg) != 1:
            return None
        q = leg.iloc[0]
        if not (np.isfinite([q.bid, q.ask]).all() and 0 <= q.bid <= q.ask and q.ask > 0):
            return None
        if buy:
            if not np.isfinite(q.ask_size) or q.ask_size < size:
                return None
        elif not (q.bid > 0 and np.isfinite(q.bid_size) and q.bid_size >= size):
            return None
        lookup[(right, strike)] = q
    debits, marks = [], []
    for legs in packages:
        debit = sum(qty * (lookup[(right, strike)].ask if qty > 0
                           else lookup[(right, strike)].bid) for right, strike, qty in legs)
        mark = sum(qty * (lookup[(right, strike)].ask + lookup[(right, strike)].bid) / 2
                   for right, strike, qty in legs)
        if not (0 < -debit < width if form == "IRON" else 0 < debit < width):
            return None
        debits.append(float(debit))
        marks.append(float(mark))
    return {"entry_debit": sum(debits), "entry_mark": sum(marks),
            "package_debits": debits, "gross_contracts": 4 * len(centers)}


def outcome(entry: dict, centers: list[float], width: int, form: str,
            settlement: float) -> dict:
    packages = len(centers)
    intrinsic = sum(tent_value(c, width, settlement) for c in centers)
    terminal = intrinsic - (packages * width if form == "IRON" else 0)
    fee, stress = 2.60 * packages, 5.0 * packages
    effective_debit = entry["entry_debit"] + (packages * width if form == "IRON" else 0)
    risk = 100 * effective_debit + fee + stress
    gross = 100 * (terminal - entry["entry_debit"])
    net = gross - fee
    return {"terminal_cash_points": terminal, "settlement": settlement,
            "gross": gross, "net": net, "stressed": net - stress,
            "midpoint": 100 * (terminal - entry["entry_mark"]) - fee,
            "fee": fee, "stress_cost": stress, "initial_risk": risk,
            "risk_units": (net - stress) / risk}


def simulate(quotes: pd.DataFrame, f: dict, day: dt.date, arm: str,
             width: int, form: str, settlement: float | None) -> dict:
    row = {"date": str(day), "arm": arm, "width": width, "form": form}
    if f["status"] != "covered":
        return {**row, "status": f["status"]}
    if arm != "atm_all" and not f["quiet"]:
        return {**row, "status": "no_signal"}
    signal_snap = quotes[quotes.timestamp == f["signal_time"] - pd.Timedelta(minutes=1)]
    centers = centers_for(arm, f, np.sort(signal_snap.strike.unique()))
    if not centers:
        return {**row, "status": "no_signal" if f["drift"] == 0 else "excluded_center"}
    row["centers"] = centers
    later = quotes[(quotes.timestamp > f["signal_time"])
                   & (quotes.timestamp <= f["signal_time"] + pd.Timedelta(minutes=2))]
    for stamp, snap in later.groupby("timestamp", sort=True):
        entry = entry_price(snap, centers, width, form)
        if entry is not None:
            row.update(entry, entry_time=stamp, packages=len(centers),
                       exposure_minutes=(session_end(day) - stamp).total_seconds() / 60)
            if settlement is None or not np.isfinite(settlement) or settlement <= 0:
                return {**row, "status": "unresolved_settlement"}
            return {**row, "status": "completed",
                    **outcome(entry, centers, width, form, settlement)}
    return {**row, "status": "excluded_entry"}


def metrics(rows: list[dict]) -> dict:
    completed = sorted((r for r in rows if r["status"] == "completed"), key=lambda r: r["date"])
    result = {"statuses": dict(Counter(r["status"] for r in rows)), "trades": len(completed)}
    if not completed:
        return result
    x = np.array([r["stressed"] for r in completed])
    wins, losses = x[x > 0], x[x < 0]
    eq = np.r_[0, x.cumsum()]
    result.update(stressed=float(x.sum()), net=float(sum(r["net"] for r in completed)),
                  midpoint=float(sum(r["midpoint"] for r in completed)),
                  gross=float(sum(r["gross"] for r in completed)),
                  fees=float(sum(r["fee"] for r in completed)),
                  stress_cost=float(sum(r["stress_cost"] for r in completed)),
                  expectancy=float(x.mean()), win_rate=float((x > 0).mean()),
                  profit_factor=float(wins.sum() / -losses.sum()) if len(losses) else None,
                  average_win=float(wins.mean()) if len(wins) else None,
                  average_loss=float(losses.mean()) if len(losses) else None,
                  top3_removed=float(x.sum() - np.sort(x[x > 0])[-3:].sum()),
                  terminal_drawdown=float((np.maximum.accumulate(eq) - eq).max()),
                  mean_initial_risk=float(np.mean([r["initial_risk"] for r in completed])),
                  mean_risk_units=float(np.mean([r["risk_units"] for r in completed])),
                  exposure_minutes=float(sum(r["exposure_minutes"] for r in completed)))
    return result


def summarize(rows: list[dict], dates: list[str]) -> dict:
    split = dates[len(dates) // 2]
    cells = {}
    for arm in ARMS:
        for width in WIDTHS:
            for form in FORMS:
                selected = [r for r in rows if (r["arm"], r["width"], r["form"]) == (arm, width, form)]
                cell = metrics(selected)
                cell["halves"] = {name: metrics([r for r in selected if (r["date"] < split) == first])
                                  for name, first in (("first", True), ("second", False))}
                cell["monthly"] = {month: metrics([r for r in selected if r["date"].startswith(month)])
                                   for month in sorted({d[:7] for d in dates})}
                baseline = {r["date"]: r for r in rows if r["arm"] == "atm_all"
                            and r["width"] == width and r["form"] == form}
                pairs = [(r, baseline[r["date"]]) for r in selected
                         if r["status"] in ("completed", "no_signal")
                         and baseline[r["date"]]["status"] == "completed"]
                cell["paired"] = {"days": len(pairs), "difference": sum(
                    r.get("stressed", 0) - b["stressed"] for r, b in pairs),
                    "candidate": sum(r.get("stressed", 0) for r, b in pairs),
                    "benchmark": sum(b["stressed"] for r, b in pairs)}
                cell["conditional_paired"] = {"days": sum(r["status"] == "completed" for r, b in pairs),
                    "difference": sum(r["stressed"] - b["stressed"] for r, b in pairs
                                      if r["status"] == "completed")}
                passing = (cell.get("stressed", 0) > 0 and cell.get("top3_removed", 0) > 0
                           and all(v.get("stressed", 0) > 0 for v in cell["halves"].values())
                           and cell["paired"]["difference"] > 0)
                if cell["statuses"].get("unresolved_settlement") or not cell["trades"]:
                    cell["decision"] = "insufficient evidence"
                else:
                    cell["decision"] = "refine" if passing else "reject exact cell"
                cells[f"{arm}_w{width}_{form}"] = cell
    return {"sessions": len(dates), "split_date": split, "cells": cells,
            "interpretation": "24 correlated retrospective development cells; no funded return or independent edge. DD is terminal outcome only. Pair uses twice the packages; component fills modeled."}


def run(out: Path, limit: int | None, signal_source: str = "parity",
        quiet_gate: str = "absolute") -> None:
    spec_path = out / "specification.json"
    if json.loads(spec_path.read_text())["rules"] != specification(signal_source, quiet_gate):
        raise ValueError("Frozen spec differs from current rules")
    if (out / "manifest.json").exists():
        raise FileExistsError("Use a fresh output directory")
    settlements = pd.read_csv(SETTLEMENTS, dtype={"date": str})
    receipt = SETTLEMENTS.with_name("native-manifest.json")
    meta = json.loads(receipt.read_text())
    if (set(settlements.source_type) != {"cboe_native_xsp_published_settlement"}
            or settlements.date.duplicated().any()
            or meta.get("source_type") != "cboe_native_xsp_published_settlement"
            or meta.get("files", {}).get(SETTLEMENTS.name) != digest(SETTLEMENTS)):
        raise ValueError("Native settlement provenance mismatch")
    settlement_map = dict(zip(settlements.date, settlements.settlement, strict=True))
    paths = sorted((ROOT / "data/thetadata/xsp_0dte/quote_1m/2026").glob("*.parquet"))
    paths = [p for p in paths if SPEC["period"][0] <= p.stem <= SPEC["period"][1]]
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        paths = paths[:limit]
    if not paths:
        raise ValueError("No local XSP quote sessions")
    sources = [Path(__file__), Path(__file__).with_name("common.py"),
               Path(__file__).with_name("mean_reversion.py"),
               Path(__file__).with_name("trend_range.py"),
               Path(__file__).with_name("realization.py"),
               Path(__file__).with_name("settlement_data.py"),
               ROOT / "src/butterfly_guy/research/event_calendar.py"]
    manifest = {"started": dt.datetime.now(dt.UTC), "command": sys.argv,
                "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "dirty_status": subprocess.check_output(["git", "status", "--short"], text=True),
                "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in sources},
                "spec_sha256": digest(spec_path), "calendar": calendar().meta(),
                "settlement_sha256": digest(SETTLEMENTS), "receipt_sha256": digest(receipt),
                "versions": {"pandas": pd.__version__, "numpy": np.__version__},
                "inputs": [], "limit": limit, "signal_source": signal_source,
                "quiet_gate": quiet_gate}
    independent = None
    if signal_source == "spx":
        support_receipt = SUPPORT / "manifest.json"
        support_file = SUPPORT / "spot_ticks.parquet"
        source_meta = json.loads(support_receipt.read_text())
        if source_meta["files"][support_file.name]["sha256"] != digest(support_file):
            raise ValueError("Independent price source hash mismatch")
        independent = spx_minutes(pd.read_parquet(support_file))
        manifest["support"] = {"file": str(support_file.relative_to(ROOT)),
                               "sha256": digest(support_file),
                               "receipt_sha256": digest(support_receipt),
                               "first": str(independent.timestamp.min()),
                               "last": str(independent.timestamp.max()),
                               "minutes": len(independent),
                               "origin": "local_support_v1 recorded SPX ticks, /10 cross-index proxy"}
    # Persist before looking at outcomes; an interrupted run cannot be silently reused.
    write_new(out / "manifest.json", manifest)
    rows, feature_rows, prior_rates = [], [], []
    for i, path in enumerate(paths):
        day = dt.date.fromisoformat(path.stem)
        quotes = load_session(path)
        proxy = (derive_proxy(quotes) if independent is None else independent.loc[
            independent.timestamp.dt.date == day])
        f = features(quotes, proxy, day)
        if quiet_gate == "relative":
            f, rate = relative_calm(f, prior_rates, day)
            if rate is not None:
                prior_rates.append(rate)
        feature_rows.append({"date": str(day), **f})
        for arm in ARMS:
            for width in WIDTHS:
                for form in FORMS:
                    rows.append(simulate(quotes, f, day, arm, width, form, settlement_map.get(str(day))))
        manifest["inputs"].append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                                   "rows": len(quotes), "proxy_rows": len(proxy),
                                   "first": str(quotes.timestamp.min()), "last": str(quotes.timestamp.max())})
        if i % 20 == 0:
            print(f"{i + 1}/{len(paths)} {day}", flush=True)
    for name, items in (("journal.jsonl", rows), ("features.jsonl", feature_rows)):
        with (out / name).open("x") as handle:
            for row in items:
                handle.write(json.dumps(row, default=str, allow_nan=False) + "\n")
    pd.DataFrame(rows).to_csv(out / "journal.csv", index=False, mode="x")
    manifest["finished"] = dt.datetime.now(dt.UTC)
    write_new(out / "completed-manifest.json", manifest)
    summary = summarize(rows, [p.stem for p in paths])
    summary["features"] = {"statuses": dict(Counter(f["status"] for f in feature_rows)),
                           "quiet_days": sum(f.get("quiet", False) for f in feature_rows)}
    write_new(out / "summary.json", summary)
    print(json.dumps({k: {field: v.get(field) for field in ("trades", "stressed", "decision")}
                      for k, v in summary["cells"].items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--signal-source", choices=("parity", "spx"), default="parity")
    parser.add_argument("--quiet-gate", choices=("absolute", "relative"), default="absolute")
    args = parser.parse_args()
    if args.freeze:
        args.out.mkdir(parents=True, exist_ok=True)
        write_new(args.out / "specification.json", {
            "frozen_at": dt.datetime.now(dt.UTC),
            "rules": specification(args.signal_source, args.quiet_gate)})
    if args.run:
        run(args.out, args.limit, args.signal_source, args.quiet_gate)


if __name__ == "__main__":
    main()
