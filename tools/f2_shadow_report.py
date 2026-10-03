"""Score the F2 draft (VIX >= 16 at entry, hold to cash settlement) as exploratory shadow.

F2 takes the live strategy's own entries from the frozen v2 prospective cohort ledger, so
entry selection never drifts from what the live strategy would do. For each cohort trade
it looks up the VIX at the decision time and the official close, then values the fly
held to settlement. Read-only: it reads the cohort ledger and the database and writes
only its own report directory.

    uv run python tools/f2_shadow_report.py
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import asyncpg

from butterfly_guy.backtest.prospective_execution import (
    canonical_hash,
    git_state,
    load_manifest,
    manifest_drift,
    read_jsonl,
    verify_cohort,
)
from butterfly_guy.core.config import load_config
from butterfly_guy.data.schemas import ButterflyCandidate
from butterfly_guy.position.position_manager import fly_settlement_value
from butterfly_guy.scripts.run_backtest_db import (
    get_official_settlement_spot,
    get_vix_snapshot_at,
)

COHORT = Path(
    "/mnt/Repos/Trading/Butterflyguy/.worktrees/spx-prospective-v2/"
    "reports/prospective_execution/spx-prospective-v2-2026-10-02"
)
OUT = Path(__file__).resolve().parents[1] / "reports" / "f2_shadow"
VIX_FLOOR = 16.0
START = dt.date(2026, 10, 2)
MODELS = {"corrected_midpoint": "midpoint", "marketable": "marketable",
          "stressed_marketable": "stressed"}
# Registered endpoint and gates (docs/research/f2-shadow-registration-2026-10-02.md).
TARGET_TRADES = 60
MIN_WINNERS = 8
MAX_DRAWDOWN = 8000.0
MANIFEST_SHA256 = "ce7144c24d3f0620b45501b224eaf55d5c0431be81285a5df11bcebe87d779db"
INPUT_FILES = ("manifest.json", "trades.jsonl", "daily_runs.jsonl", "deferred_runs.jsonl")


def input_hashes(cohort: Path) -> dict[str, str]:
    return {name: hashlib.sha256((cohort / name).read_bytes()).hexdigest()
            for name in INPUT_FILES}


def load_cohort(cohort: Path) -> tuple[dict, list[dict], Path]:
    """Accept only the original v2 manifest and its verified frozen ledger."""
    if input_hashes(cohort)["manifest.json"] != MANIFEST_SHA256:
        raise ValueError("F2 requires the original frozen SPX v2 manifest")
    root = cohort.resolve().parents[2]
    problems = verify_cohort(cohort, root)
    manifest = load_manifest(cohort)
    # The scorer imports shared pricing/query helpers from its own checkout.
    problems += manifest_drift(manifest, Path(__file__).resolve().parents[1])
    if problems:
        raise ValueError("cohort integrity failed: " + "; ".join(problems))
    return manifest, read_jsonl(cohort / "trades.jsonl"), root


def _candidate(trade: dict) -> ButterflyCandidate:
    return ButterflyCandidate(
        direction=trade["direction"],
        lower_strike=float(trade["lower_strike"]),
        center_strike=float(trade["center_strike"]),
        upper_strike=float(trade["upper_strike"]),
        wing_width=int(trade["wing_width"]),
        cost=0.0, max_profit=0.0, reward_risk=0.0, lower_be=0.0, upper_be=0.0,
        distance_from_spot=0.0, spot_price=0.0,
    )


async def score(dsn: str, trades: list[dict], max_vix_age: float, start: dt.date) -> list[dict]:
    conn = await asyncpg.connect(dsn)
    rows = []
    try:
        for t in sorted(trades, key=lambda t: t["decision_time"]):
            date = dt.date.fromisoformat(t["session_date"])
            if date < start:
                continue
            decided = dt.datetime.fromisoformat(t["decision_time"])
            vix = await get_vix_snapshot_at(conn, decided)
            close = await get_official_settlement_spot(conn, date, "SPX")
            row = {"session_date": t["session_date"], "trade_id": t["trade_id"],
                   "decision_time": t["decision_time"],
                   "cohort_record_hash": t["record_hash"],
                   "direction": t["direction"], "wing_width": t["wing_width"],
                   "center_strike": t["center_strike"],
                   "vix": vix[0] if vix else None,
                   "vix_age_s": (decided - vix[1]).total_seconds() if vix else None,
                   "vix_snapshot_time": vix[1].isoformat() if vix else None,
                   "settlement_spot": close, "e0_exit_reason": t["exit_reason"]}
            if (vix is None or not math.isfinite(vix[0]) or vix[0] <= 0
                    or not 0 <= row["vix_age_s"] <= max_vix_age):
                row["status"] = "no_fresh_vix"
            elif vix[0] < VIX_FLOOR:
                row["status"] = "filtered_vix"
            elif close is None or not math.isfinite(close) or close <= 0:
                row["status"] = "pending_settlement"
            else:
                row["status"] = "traded"
                settle = fly_settlement_value(_candidate(t), close)
                row["settlement_value"] = settle
            for model, short in MODELS.items():
                acct = t["accounting"][model]
                row[f"e0_{short}"] = acct["net_pnl"] if acct["status"] == "priced" else None
                if row["status"] == "traded" and acct["status"] == "priced":
                    # Cohort entry prices already include commission (and stress), and
                    # cash settlement has no closing order, as in the cohort's own net_pnl.
                    row[f"f2_{short}"] = round(
                        100.0 * (row["settlement_value"] - acct["entry_price"]), 2)
            rows.append(row)
            _, state = completed_sample(rows)
            if state != "collecting":
                break
    finally:
        await conn.close()
    return rows


def _stats(pnl: list[float]) -> dict:
    wins, losses = [p for p in pnl if p > 0], [p for p in pnl if p < 0]
    eq = peak = dd = 0.0
    for p in pnl:
        eq += p
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    top3 = sum(sorted(wins, reverse=True)[:3])
    return {"trades": len(pnl), "net": round(sum(pnl), 2),
            "expectancy": round(sum(pnl) / len(pnl), 2) if pnl else None,
            "profit_factor": sum(wins) / -sum(losses) if losses else None,
            "profit_factor_unbounded": bool(wins and not losses),
            "winners": len(wins), "max_drawdown": round(dd, 2),
            "top3_share": top3 / sum(wins) if wins else None}


def completed_sample(rows: list[dict]) -> tuple[list[dict], str]:
    """Stop at the first endpoint/early failure; unresolved evidence blocks later rows."""
    sample = []
    pnl = []
    for r in sorted(rows, key=lambda r: r["decision_time"]):
        if r["status"] == "filtered_vix":
            sample.append(r)
            continue
        if r["status"] != "traded" or any(
                r.get(k) is None or not math.isfinite(r[k])
                for k in ("f2_stressed", "f2_midpoint", "e0_stressed")):
            return sample, "pending_evidence"
        sample.append(r)
        pnl.append(r["f2_stressed"])
        stats = _stats(pnl)
        if stats["max_drawdown"] > MAX_DRAWDOWN:
            return sample, "stopped_early"
        if stats["trades"] >= TARGET_TRADES and stats["winners"] >= MIN_WINNERS:
            return sample, "endpoint_reached"
    return sample, "collecting"


def check_previous(rows: list[dict], path: Path) -> None:
    """Do not silently rewrite previously resolved market evidence."""
    current = {r["trade_id"]: r for r in rows}
    for previous in read_jsonl(path):
        body = {k: v for k, v in previous.items() if k != "record_hash"}
        if previous.get("record_hash") != canonical_hash(body):
            raise ValueError("previous F2 ledger has an invalid record hash")
        if previous["status"] in ("traded", "filtered_vix"):
            if current.get(previous["trade_id"]) != body:
                raise ValueError("resolved F2 evidence changed; preserve and investigate it")


def summarize(rows: list[dict], cohort: Path, start: dt.date) -> tuple[dict, str]:
    sample, state = completed_sample(rows)
    traded = [r for r in sample if r["status"] == "traded"]
    f2 = _stats([r["f2_stressed"] for r in traded])
    same = _stats([r["e0_stressed"] for r in traded if r["e0_stressed"] is not None])
    all_e0 = _stats([r["e0_stressed"] for r in sample if r.get("e0_stressed") is not None])
    diff = round(f2["net"] - same["net"], 2)
    endpoint = state == "endpoint_reached"
    gates = {
        "f2_stressed_net_positive": f2["net"] > 0,
        "f2_profit_factor_above_one": (
            f2["profit_factor_unbounded"] or (f2["profit_factor"] or 0) > 1),
        "f2_beats_e0_on_same_entries": diff > 0,
        "f2_top3_share_below_half": f2["top3_share"] is not None and f2["top3_share"] < 0.5,
        "f2_drawdown_within_limit": f2["max_drawdown"] <= MAX_DRAWDOWN,
    }
    summary = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "cohort": str(cohort), "start": str(start), "vix_floor": VIX_FLOOR,
               "label": "exploratory shadow; pre-observation registration not verified",
               "study_state": state, "sessions_with_e0_trade": len(sample),
               "status_counts": {s: sum(r["status"] == s for r in rows)
                                 for s in sorted({r["status"] for r in rows})},
               "f2_stressed": f2, "e0_stressed_same_entries": same,
               "e0_stressed_all": all_e0, "f2_minus_e0_same_entries": diff,
               "f2_midpoint_net": round(sum(r["f2_midpoint"] for r in traded), 2),
               "endpoint_reached": endpoint, "gates": gates,
               "stopped_early": state == "stopped_early"}
    lines = [
        "# F2 exploratory shadow", "",
        "Pre-observation registration has not been verified. No strategy promotion.", "",
        f"Generated {summary['generated']}. Rule: live entry, VIX >= {VIX_FLOOR:g}, held to "
        f"cash settlement. Entries from `{cohort.name}`; sessions from {start}.", "",
        f"- Study state: {state}",
        f"- Completed entries: {len(sample)} ({summary['status_counts']})",
        f"- Endpoint: {f2['trades']}/{TARGET_TRADES} F2 trades, {f2['winners']}/{MIN_WINNERS} "
        f"winners — {'reached' if endpoint else 'not reached'}",
        f"- Stopped early (drawdown > ${MAX_DRAWDOWN:,.0f}): {summary['stopped_early']}", "",
        "| Stressed | Trades | Net | Exp | PF | Win | Max DD | Top-3 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, s in (("F2", f2), ("E0, same entries", same), ("E0, all entries", all_e0)):
        lines.append(f"| {name} | {s['trades']} | {s['net']:,.2f} | {s['expectancy']} | "
                     f"{s['profit_factor']} | {s['winners']} | {s['max_drawdown']:,.2f} | "
                     f"{s['top3_share']} |")
    lines += ["", f"F2 minus E0 on the same entries: **{diff:+,.2f}**", "",
              "Gates (judged only at the endpoint):", ""]
    lines += [f"- {k}: {'pass' if v else 'fail'}" for k, v in gates.items()]
    return summary, "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cohort", type=Path, default=COHORT)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--start", type=dt.date.fromisoformat, default=START,
                   help="fixed first session to score: %(default)s")
    args = p.parse_args()
    if args.start != START:
        raise ValueError("F2's fixed start is 2026-10-02; dry runs require a separate study")
    before = input_hashes(args.cohort)
    manifest, trades, cohort_root = load_cohort(args.cohort)
    config = load_config(cohort_root / manifest["config"]["path"])
    rows = asyncio.run(score(config.database.dsn, trades,
                             float(config.entry.max_vix_age_seconds), args.start))
    if input_hashes(args.cohort) != before:
        raise ValueError("cohort inputs changed during scoring; retry from a stable snapshot")
    check_previous(rows, args.out / "ledger.jsonl")
    summary, md = summarize(rows, args.cohort, args.start)
    summary["provenance"] = {
        "cohort_input_sha256": before, "cohort_registration": manifest["git"],
        "scorer_git": git_state(Path(__file__).resolve().parents[1]),
        "scorer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "shared_source_hashes": manifest["source_hashes"],
        "draft_sha256": "da47c54bef0cb13e3a56d1e3e5949eb47f9d18a2a347b0d63deae7d00b74f2ec",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "ledger.jsonl").write_text("".join(
        json.dumps({**r, "record_hash": canonical_hash(r)}, allow_nan=False) + "\n"
        for r in rows))
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    (args.out / "summary.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
