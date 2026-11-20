"""Bounded mixed PUT/CALL XSP research. Offline inputs only; no runtime APIs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent.common import calendar, load_session, session_end
from tools.research_studies.xsp_independent.mean_reversion import digest, write_new
from tools.research_studies.xsp_independent.quiet_flies import (
    SUPPORT,
    features,
    legs_for,
    metrics,
    spx_minutes,
)
from tools.research_studies.xsp_independent.realization import SETTLEMENTS

ROOT = Path(__file__).resolve().parents[3]
PRIOR = ROOT / "reports/research/xsp-quiet-flies-2026-11-12/run-03-relative"
QUOTES = ROOT / "data/thetadata/xsp_0dte/quote_1m"
WIDTH = 4
CELLS = [(geometry, gate, exit_policy) for geometry in ("body", "all_strikes")
         for gate in ("unconditional", "movement")
         for exit_policy in ("settlement", "zone_exit")]
RULES = {
    "period_inclusive_et": ["2026-01-02", "2026-09-28"],
    "utc_session_bounds": "09:31 ET through actual scheduled close exclusive; DST-aware. Jan2 14:31Z; Sep28 close20:00Z.",
    "prior_inspection": "All Jan-Sep2026 development, including quiet30 outcomes; previous neutral pairs same-right/iron, never exact mixed Batman. No untouched holdout. No outcome inspection of this new mixed construction before freeze.",
    "quiet_baseline": "Import exact completed run-03-relative atm_quiet_w4_IRON and atm_all_w4_IRON records/spec/source hashes unchanged. No new quiet parameters, exits, widths or filters. Reconcile every imported completed cash record. Fresh validation only if new joint input coverage exists.",
    "budget": "8 new Batman cells:2geometries x2entry gates x2exits. Plus2 reused iron benchmark cells =10 total, <=12. Stop after this matrix. No optimization or outcome-led expansion.",
    "features": "Reuse quiet_flies.features on completed independent SPX/10 [09:31,10:30), >=54/59 minutes, <=120s gaps, final10:29. It is a cross-index proxy, not native XSP. Genuine XSP10:29 paired ATM straddle midpoint sets offset. No quiet filter or rolling warmup for Batman.",
    "movement_hypothesis": "At10:30 efficiency=abs(first-hour drift)/sum(abs increments)>=0.30 AND abs(drift)>=0.5*ATM straddle. Provisional persistence hypothesis: an efficient already material first-hour move predicts reaching finite payoff zones after entry; either direction allowed, also measure drift-side reach. No calendar exclusion or quiet condition.",
    "geometry": "Width4 fixed per fly. Lower PUT and upper CALL, each+1/-2/+1. BODY targets proxy+/-0.5*straddle. ALL_STRIKES targets proxy+/-(4+0.5*straddle). Nearest10:29 listed body constrained respectively c_put<proxy<c_call or c_put+4<proxy<c_call-4, lower strike on ties. Require all3 strikes listed10:29. Frozen centers, no alternative strike search. Provisional interpretations relative SPX/10, native XSP OTM status unestablished.",
    "entry": "First simultaneous usable XSP snapshot strictly after10:30 through10:32. Verify intended geometry against last completed SPX minute (stamp-1min) at fill; unavailable reference/failed geometry skips snapshot, no alternate strikes. Six distinct option contracts, eight gross units, two flies together; each0<component debit<4. Transaction-needed sides/sizes aggregated by contract+side. No future exit admission test.",
    "sizing_risk": "One lower put fly plus one upper call fly per session; no netting, reentry or carry. Entry maximum expiry loss =100*(both debits)+$5.20 opening fees+$10 stress, since separated bodies have zero combined tails. Risk units use this expiry risk; a payable component liquidation plus closing costs can lose more. No capital return/margin assumption.",
    "settlement": "Hold both to native Cboe-published XSP settlement; preserve source receipt; missing terminal remains unresolved, not zero. No settlement fee/exercise charge modeled (unverified).",
    "zone_exit": "Combined EXPIRY-profit intervals fixed at entry using total debit+opening fee+opening stress. From entry minute onward inspect completed SPX minute at its end, strictly after entry, through close-15min. First observed proxy within either interval triggers exit; a body touch/crossing alone does not. First subsequent simultaneous usable component close strictly after trigger and <=trigger+2min AND <=cutoff. Close BOTH flies, including signed payable values; no profit requirement on fill. If entry-minute or later prefix gap first exceeds120s (known last_observation_available+3min, start+4min), or first fill window expires, irreversibly settle BOTH; no recovery retry. If no zone trigger, schedule combined cutoff close at cutoff..cutoff+2min capped at cutoff (only cutoff snapshot); otherwise settle. Never interpolate. Late triggers without a later window settle at cutoff. No partial fills assumed: modeled atomic full-pair estimate, not demonstrated package fill.",
    "costs": "$0.65/gross contract per transaction:opening5.20, closing5.20 if liquidated; additional adverse0.05points/fly/transaction=$10 per pair per transaction. Crossing all component sides, transaction-needed displayed sizes only, no age evidence. Midpoint diagnostic on SAME entries/exit choices only; no new cells. Broker/exchange/exercise extra fees unknown.",
    "diagnostics": "Expiry intervals piecewise linear exact combined tents, entry-specific all-in cost; sampled reach through cutoff, complete-prefix required for yes/no comparable reach rates, gaps unknown rather than false. Track any observed reach separately on incomplete paths. Report drift side and body crossing as observations only. Native settlement zone outcome separate from proxy path.",
    "evaluation": "Complete cohort; trade/day metrics, monthly and fixed prior split2026-05-15, top3 positive winners removed, terminal-outcome drawdown incl initial0, risk units, all costs and midpoint drag. Matched dates for gates and single-iron/two-fly comparison, no zero for excluded/unresolved. Valid no_signal may equal0 in daily participation comparison. No independent causal forecast claim from this observational archive.",
    "decision": "Reject exact cell if stressed total<=0 or either fixed half<=0 or top3removed<=0 or movement gate fails matched participation improvement. Incomplete outcomes => insufficient evidence. Passing retrospective screen=>refine only; never promote/activate from retrospective result. Quiet idea=>insufficient evidence for fresh validation if no new joint coverage; retain prior exact-policy rejection.",
}


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("x") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str, allow_nan=False) + "\n")


def audit(out: Path) -> None:
    """Coverage only, before freezing or evaluating new strategy outcomes."""
    out.mkdir(parents=True, exist_ok=False)
    inventories = {}
    for kind in ("quote_1m", "ohlc_1m", "open_interest", "eod"):
        paths = sorted((QUOTES.parent / kind).rglob("*.parquet"))
        inventories[kind] = {"count": len(paths), "first": paths[0].stem if paths else None,
                             "last": paths[-1].stem if paths else None,
                             "by_year": dict(Counter(p.parent.name for p in paths))}
    ticks = pd.read_parquet(SUPPORT / "spot_ticks.parquet")
    proxy = spx_minutes(ticks)
    paths = sorted((QUOTES / "2026").glob("*.parquet"))
    sessions = []
    for path in paths:
        day = dt.date.fromisoformat(path.stem)
        quotes = load_session(path)
        p = proxy[proxy.timestamp.dt.date == day]
        f = features(quotes, p, day)
        sessions.append({"date": str(day), "sha256": digest(path),
                         "rows": len(quotes), "raw_rows": quotes.attrs["raw_rows"],
                         "minutes": quotes.timestamp.nunique(), "signal_status": f["status"],
                         "spx_minutes": len(p), "close": session_end(day),
                         "first": quotes.timestamp.min(), "last": quotes.timestamp.max()})
    native = pd.read_csv(SETTLEMENTS)
    receipt = json.loads(SETTLEMENTS.with_name("native-manifest.json").read_text())
    if (receipt["files"][SETTLEMENTS.name] != digest(SETTLEMENTS)
            or set(native.source_type) != {"cboe_native_xsp_published_settlement"}
            or native.date.duplicated().any()):
        raise ValueError("Native settlement receipt invalid")
    result = {"at_utc": dt.datetime.now(dt.UTC), "inventories": inventories,
              "signal_statuses": dict(Counter(r["signal_status"] for r in sessions)),
              "support_underlyings": sorted(ticks.underlying.unique().tolist()),
              "proxy_bounds": [proxy.timestamp.min(), proxy.timestamp.max()],
              "native_settlement_dates": len(native),
              "missing_native_dates": sorted({p.stem for p in paths} - set(native.date)),
              "new_quote_dates_after_prior_end": [p.stem for p in paths if p.stem > "2026-09-28"],
              "calendar": calendar().meta(),
              "visible_early_closes": {r["date"]: str(r["close"]) for r in sessions
                                       if r["close"].hour != 16},
              "hashes": {str(p.relative_to(ROOT)): digest(p) for p in (
                  SUPPORT / "spot_ticks.parquet", SUPPORT / "manifest.json", SETTLEMENTS,
                  SETTLEMENTS.with_name("native-manifest.json"), calendar().path)},
              "prior_inspection": RULES["prior_inspection"],
              "execution_evidence": "Minute NBBO component sizes; no new observed complex fills, per-leg update ages, or native intraday XSP in canonical support. Older quote files alone are not validated joint cohorts; no acquisition/runtime access in this bounded study.",
              "sessions": sessions}
    write_new(out / "coverage.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("sessions", "hashes")}, default=str, indent=2))


def freeze(out: Path, audit_path: Path) -> None:
    out.mkdir(parents=True, exist_ok=False)
    write_new(out / "specification.json", {"frozen_at": dt.datetime.now(dt.UTC),
              "coverage_sha256": digest(audit_path), "rules": RULES,
              "cells": ["_".join(c) for c in CELLS]})
    (out / "coverage.json").write_bytes(audit_path.read_bytes())


def movement(f: dict) -> bool:
    return bool(f["efficiency"] >= .30 and abs(f["drift"]) >= .5 * f["straddle"])


def geometry_ok(centers: list[float], proxy: float, geometry: str) -> bool:
    inset = WIDTH if geometry == "all_strikes" else 0
    return centers[0] + inset < proxy < centers[1] - inset


def select_centers(f: dict, strikes: np.ndarray, geometry: str) -> list[float]:
    inset = WIDTH if geometry == "all_strikes" else 0
    centers = []
    for side in (-1, 1):
        candidates = strikes[(strikes - f["proxy"]) * side > inset]
        if not len(candidates):
            return []
        target = f["proxy"] + side * (inset + .5 * f["straddle"])
        centers.append(float(candidates[np.argmin(abs(candidates - target))]))
    return centers if all(c - WIDTH in strikes and c + WIDTH in strikes for c in centers) else []


def packages(centers: list[float]) -> list[list[tuple[str, float, int]]]:
    return [legs_for(centers[0], WIDTH, "PUT"), legs_for(centers[1], WIDTH, "CALL")]


def component(snapshot: pd.DataFrame, centers: list[float], opening: bool) -> dict | None:
    """Signed debit when opening, signed credit when closing; no price clipping."""
    packs = packages(centers)
    needs = Counter()
    for legs in packs:
        for right, strike, quantity in legs:
            needs[right, strike, (quantity > 0) == opening] += abs(quantity)
    lookup = {}
    for (right, strike, buy), size in needs.items():
        x = snapshot[(snapshot.right == right) & (snapshot.strike == strike)]
        if len(x) != 1:
            return None
        q = x.iloc[0]
        if not (np.isfinite([q.bid, q.ask]).all() and 0 <= q.bid <= q.ask and q.ask > 0):
            return None
        price, displayed = (q.ask, q.ask_size) if buy else (q.bid, q.bid_size)
        if not (np.isfinite(displayed) and displayed >= size and price > 0):
            return None
        lookup[right, strike] = q
    prices, marks = [], []
    for legs in packs:
        prices.append(float(sum(qty * (lookup[r, k].ask if (qty > 0) == opening
                                       else lookup[r, k].bid) for r, k, qty in legs)))
        marks.append(float(sum(qty * (lookup[r, k].bid + lookup[r, k].ask) / 2
                               for r, k, qty in legs)))
    if opening and not all(0 < debit < WIDTH for debit in prices):
        return None
    return {"price": sum(prices), "mark": sum(marks), "package_prices": prices}


def payoff(centers: list[float], price: float) -> float:
    return sum(max(WIDTH - abs(price - c), 0) for c in centers)


def profit_zones(centers: list[float], cost_points: float) -> list[list[float]]:
    """Exact open intervals of sum of tents > cost, including overlap/plateau."""
    knots = sorted({v for c in centers for v in (c - WIDTH, c, c + WIDTH)})
    intervals = []
    for a, b in zip(knots[:-1], knots[1:], strict=True):
        ya, yb = payoff(centers, a) - cost_points, payoff(centers, b) - cost_points
        if max(ya, yb) <= 0:
            continue
        lo = a if ya >= 0 else a + (b - a) * (-ya) / (yb - ya)
        hi = b if yb >= 0 else a + (b - a) * (-ya) / (yb - ya)
        if intervals and abs(intervals[-1][1] - lo) < 1e-9 and payoff(centers, lo) > cost_points:
            intervals[-1][1] = hi
        else:
            intervals.append([lo, hi])
    return intervals


def inside(price: float, zones: list[list[float]]) -> bool:
    return any(lo < price < hi for lo, hi in zones)


def lifecycle(quotes: pd.DataFrame, proxy: pd.DataFrame, day: dt.date,
              row: dict, exit_policy: str) -> dict:
    """Irrevocable settlement fallback; every decision carries known-at time."""
    if exit_policy == "settlement":
        return {"terminal": "settlement", "reason": "planned_settlement",
                "decision_time": row["entry_time"]}
    entry = row["entry_time"]
    cutoff = session_end(day) - pd.Timedelta(minutes=15)
    observed = proxy.set_index("timestamp").forward_proxy.to_dict()
    last = entry - pd.Timedelta(minutes=1)  # reference verified for admission
    for available in pd.date_range(entry + pd.Timedelta(minutes=1), cutoff, freq="min"):
        stamp = available - pd.Timedelta(minutes=1)
        if stamp not in observed:
            if stamp - last > pd.Timedelta(minutes=2):
                return {"terminal": "settlement", "reason": "signal_gap",
                        "decision_time": available}
            continue
        last = stamp
        if inside(float(observed[stamp]), row["profit_zones"]):
            deadline = min(available + pd.Timedelta(minutes=2), cutoff)
            candidates = quotes[(quotes.timestamp > available) & (quotes.timestamp <= deadline)]
            for when, snap in candidates.groupby("timestamp", sort=True):
                close = component(snap, row["centers"], False)
                if close is not None:
                    return {"terminal": "liquidation", "reason": "zone_trigger",
                            "trigger_time": available, "decision_time": when,
                            "exit_time": when, "exit_price": close["price"],
                            "exit_mark": close["mark"], "exit_package_prices": close["package_prices"]}
            return {"terminal": "settlement", "reason": "zone_fill_missing",
                    "trigger_time": available, "decision_time": deadline}
    close = component(quotes[quotes.timestamp == cutoff], row["centers"], False)
    if close is None:
        return {"terminal": "settlement", "reason": "cutoff_fill_missing", "decision_time": cutoff}
    return {"terminal": "liquidation", "reason": "cutoff_close", "decision_time": cutoff,
            "exit_time": cutoff, "exit_price": close["price"], "exit_mark": close["mark"],
            "exit_package_prices": close["package_prices"]}


def account(row: dict, settlement: float | None, day: dt.date) -> dict:
    closing = row["terminal"] == "liquidation"
    if not closing and (settlement is None or not np.isfinite(settlement) or settlement <= 0):
        return {"status": "unresolved_settlement"}
    terminal = row["exit_price"] if closing else payoff(row["centers"], settlement)
    mark = row["exit_mark"] if closing else terminal
    fee, stress = 5.20 * (1 + closing), 10.0 * (1 + closing)
    gross = 100 * (terminal - row["entry_debit"])
    risk = 100 * row["entry_debit"] + 15.20
    return {"status": "completed", "settlement": settlement,
            "terminal_cash_points": terminal, "gross": gross, "net": gross - fee,
            "stressed": gross - fee - stress, "fee": fee, "stress_cost": stress,
            "midpoint": 100 * (mark - row["entry_mark"]) - fee,
            "initial_risk": risk, "risk_units": (gross - fee - stress) / risk,
            "exposure_minutes": ((row["exit_time"] if closing else session_end(day))
                                 - row["entry_time"]).total_seconds() / 60}


def reach_diagnostic(proxy: pd.DataFrame, row: dict, day: dt.date) -> dict:
    start, end = row["entry_time"], session_end(day) - pd.Timedelta(minutes=15)
    p = proxy[(proxy.timestamp >= start) & (proxy.timestamp < end)]
    reference = start - pd.Timedelta(minutes=1)
    times = [reference, *p.timestamp.tolist(), end - pd.Timedelta(minutes=1)]
    covered = max(b - a for a, b in zip(times[:-1], times[1:], strict=True)) <= pd.Timedelta(minutes=2)
    observed = [float(x) for x in p.forward_proxy]
    hit = any(inside(x, row["profit_zones"]) for x in observed)
    side = np.sign(row["signal_drift"])
    side_hit = any(inside(x, row["profit_zones"]) and (x - row["signal_proxy"]) * side > 0
                   for x in observed)
    body_cross = any(min(row["signal_proxy"], x) <= c <= max(row["signal_proxy"], x)
                     for x in observed for c in row["centers"])
    return {"reach_prefix_complete": covered, "zone_reach": hit if covered else None,
            "observed_zone_reach": hit, "drift_side_zone_reach": side_hit if covered else None,
            "observed_body_cross_from_signal": body_cross,
            "diagnostic_minutes": len(p)}


def simulate(quotes: pd.DataFrame, proxy: pd.DataFrame, f: dict, day: dt.date,
             geometry: str, gate: str, exit_policy: str, settlement: float | None) -> dict:
    row = {"date": str(day), "cell": "_".join((geometry, gate, exit_policy)),
           "geometry": geometry, "gate": gate, "exit_policy": exit_policy,
           "width": WIDTH, "packages": 2, "gross_contracts": 8}
    if f["status"] != "covered":
        return {**row, "status": f["status"]}
    if gate == "movement" and not movement(f):
        return {**row, "status": "no_signal"}
    signal = f["signal_time"]
    strikes = np.sort(quotes.loc[quotes.timestamp == signal - pd.Timedelta(minutes=1), "strike"].unique())
    centers = select_centers(f, strikes, geometry)
    if not centers:
        return {**row, "status": "excluded_geometry"}
    row.update(centers=centers, signal_proxy=f["proxy"], signal_drift=f["drift"],
               movement_signal=movement(f), signal_time=signal)
    later = quotes[(quotes.timestamp > signal) & (quotes.timestamp <= signal + pd.Timedelta(minutes=2))]
    for stamp, snap in later.groupby("timestamp", sort=True):
        ref = proxy[proxy.timestamp == stamp - pd.Timedelta(minutes=1)]
        if len(ref) != 1 or not geometry_ok(centers, float(ref.forward_proxy.iloc[0]), geometry):
            continue
        entry = component(snap, centers, True)
        if entry is None:
            continue
        row.update(entry_time=stamp, entry_debit=entry["price"], entry_mark=entry["mark"],
                   package_debits=entry["package_prices"], entry_proxy=float(ref.forward_proxy.iloc[0]))
        row["profit_zones"] = profit_zones(centers, entry["price"] + .152)
        row["expiry_peak_net"] = 100 * max(payoff(centers, c) for c in centers) - 100 * entry["price"] - 15.20
        row.update(lifecycle(quotes, proxy, day, row, exit_policy))
        row.update(account(row, settlement, day))
        row.update(reach_diagnostic(proxy, row, day))
        return row
    return {**row, "status": "excluded_entry"}


def cell_metrics(rows: list[dict]) -> dict:
    result = metrics(rows)
    dates = sorted({r["date"] for r in rows})
    result["halves"] = {name: metrics([r for r in rows if (r["date"] < "2026-05-15") == first])
                        for name, first in (("first", True), ("second", False))}
    result["monthly"] = {m: metrics([r for r in rows if r["date"].startswith(m)])
                         for m in sorted({d[:7] for d in dates})}
    completed = [r for r in rows if r["status"] == "completed"]
    result["terminal_reasons"] = dict(Counter(r.get("reason", "imported_settlement") for r in completed))
    if completed:
        covered = [r for r in completed if r.get("reach_prefix_complete")]
        result["reach"] = {"complete_paths": len(covered), "unknown_paths": len(completed) - len(covered),
                           "zone_hits": sum(r["zone_reach"] for r in covered),
                           "drift_side_hits": sum(r["drift_side_zone_reach"] for r in covered)}
        result["expiry_possible"] = sum(r.get("expiry_peak_net", 1) > 0 for r in completed)
        result["spread_drag_vs_midpoint"] = result["midpoint"] - result["net"]
        result["max_initial_risk"] = max(r["initial_risk"] for r in completed)
    return result


def paired(a: list[dict], b: list[dict], participation: bool = False) -> dict:
    bm = {r["date"]: r for r in b}
    matches = [(r, bm[r["date"]]) for r in a if r["date"] in bm
               and (r["status"] == "completed" or participation and r["status"] == "no_signal")
               and bm[r["date"]]["status"] == "completed"]
    return {"dates": [r["date"] for r, _ in matches], "days": len(matches),
            "candidate": sum(r["stressed"] if r["status"] == "completed" else 0 for r, _ in matches),
            "benchmark": sum(b["stressed"] for _, b in matches),
            "difference": sum((r["stressed"] if r["status"] == "completed" else 0) - b["stressed"]
                              for r, b in matches)}


def run(out: Path) -> None:
    spec = json.loads((out / "specification.json").read_text())
    if spec["rules"] != RULES or digest(out / "coverage.json") != spec["coverage_sha256"]:
        raise ValueError("Frozen rules/coverage mismatch")
    sources = sorted(Path(__file__).parent.glob("*.py")) + [calendar().path,
        ROOT / "src/butterfly_guy/research/event_calendar.py"]
    manifest = {"started_utc": dt.datetime.now(dt.UTC), "command": sys.argv,
                "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                "dirty_status": subprocess.check_output(["git", "status", "--short"], text=True),
                "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in sources},
                "spec_sha256": digest(out / "specification.json"), "calendar": calendar().meta(),
                "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
                "inputs": {str(p.relative_to(ROOT)): digest(p) for p in (
                    SETTLEMENTS, SETTLEMENTS.with_name("native-manifest.json"), SUPPORT / "spot_ticks.parquet",
                    SUPPORT / "manifest.json", PRIOR / "specification.json", PRIOR / "completed-manifest.json",
                    PRIOR / "journal.jsonl", PRIOR / "summary.json")}}
    coverage = json.loads((out / "coverage.json").read_text())
    if any(digest(ROOT / p) != h for p, h in coverage["hashes"].items()):
        raise ValueError("Coverage inputs changed")
    write_new(out / "manifest.json", manifest)
    (out / "source").mkdir()
    for p in sources:
        target = out / "source" / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    (out / "initial-working-tree.patch").write_bytes(subprocess.check_output(["git", "diff", "--no-ext-diff"]))
    for name in ("specification.json", "completed-manifest.json", "summary.json"):
        (out / ("prior-quiet-" + name)).write_bytes((PRIOR / name).read_bytes())
    native = pd.read_csv(SETTLEMENTS)
    settlements = dict(zip(native.date, native.settlement, strict=True))
    independent = spx_minutes(pd.read_parquet(SUPPORT / "spot_ticks.parquet"))
    rows, fs = [], []
    for i, receipt in enumerate(coverage["sessions"]):
        day = dt.date.fromisoformat(receipt["date"])
        path = QUOTES / str(day.year) / f"{day}.parquet"
        if digest(path) != receipt["sha256"]:
            raise ValueError("Quote input changed")
        manifest["inputs"][str(path.relative_to(ROOT))] = receipt["sha256"]
        q = load_session(path)
        p = independent[independent.timestamp.dt.date == day]
        f = features(q, p, day)
        fs.append({"date": str(day), **f, "movement": movement(f) if f["status"] == "covered" else None})
        for geometry, gate, policy in CELLS:
            rows.append(simulate(q, p, f, day, geometry, gate, policy, settlements.get(str(day))))
        if i % 20 == 0:
            print(f"{i + 1}/{len(coverage['sessions'])} {day}", flush=True)
    prior = [r for r in read_rows(PRIOR / "journal.jsonl") if r["form"] == "IRON"
             and r["width"] == 4 and r["arm"] in ("atm_all", "atm_quiet")]
    for r in prior:
        r["cell"] = "prior_" + r["arm"] + "_IRON_w4"
    rows.extend(prior)
    write_rows(out / "journal.jsonl", rows)
    write_rows(out / "features.jsonl", fs)
    pd.DataFrame(rows).to_csv(out / "journal.csv", index=False, mode="x")
    cells = {cell: cell_metrics([r for r in rows if r["cell"] == cell])
             for cell in sorted({r["cell"] for r in rows})}
    comparisons = {}
    for geometry, gate, policy in CELLS:
        key = "_".join((geometry, gate, policy))
        selected = [r for r in rows if r["cell"] == key]
        baseline = [r for r in rows if r["cell"] == "_".join((geometry, "unconditional", policy))]
        comparisons[key] = {"vs_unconditional_participation": paired(selected, baseline, True),
                            "vs_unconditional_traded": paired(selected, baseline),
                            "vs_single_iron": paired(selected, [r for r in prior if r["arm"] == "atm_all"])}
        m = cells[key]
        complete = not any(r["status"].startswith("unresolved") for r in selected)
        passes = (m.get("stressed", 0) > 0 and m.get("top3_removed", 0) > 0
                  and all(v.get("stressed", 0) > 0 for v in m["halves"].values())
                  and (gate == "unconditional" or comparisons[key]["vs_unconditional_participation"]["difference"] > 0))
        m["decision"] = "insufficient evidence" if not complete or not m["trades"] else "refine" if passes else "reject"
    write_new(out / "summary.json", {"cells": cells, "comparisons": comparisons,
              "feature_statuses": dict(Counter(f["status"] for f in fs)),
              "movement_dates": [f["date"] for f in fs if f["movement"]],
              "split_date": "2026-05-15", "valuation": "Terminal outcome once/session, not intraday DD",
              "quiet_decision": "insufficient evidence for new validation; exact baseline retains prior rejection",
              "batman_decision": "refine" if any(cells["_".join(c)]["decision"] == "refine" for c in CELLS) else "reject"})
    manifest["finished_utc"] = dt.datetime.now(dt.UTC)
    write_new(out / "completed-manifest.json", manifest)
    print(json.dumps({k: {n: m.get(n) for n in ("trades", "stressed", "decision")}
                      for k, m in cells.items()}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--coverage", type=Path)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.audit:
        audit(args.out)
    if args.freeze:
        if args.coverage is None:
            parser.error("--freeze requires --coverage")
        freeze(args.out, args.coverage)
    if args.run:
        run(args.out)


if __name__ == "__main__":
    main()
