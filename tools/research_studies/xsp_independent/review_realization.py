"""Independent cash, original-baseline parity and raw evidence lifecycle review."""
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PRIOR = ROOT / "reports/research/xsp-independent-2026-11-11/root-review-01/normalized-journal.csv"
SETTLEMENT_ROOT = ROOT / "reports/research/xsp-realization-2026-11-11/settlement"


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def independent_payoff(center: float, width: float, settlement: float, right: str) -> float:
    """Leg-by-leg option exercise, independent of the study's compact tent formula."""
    center, width, settlement = (Decimal(str(x)) for x in (center, width, settlement))
    value = Decimal(0)
    for strike, quantity in ((center - width, 1), (center, -2), (center + width, 1)):
        intrinsic = max(Decimal(0), settlement - strike if right == "CALL" else strike - settlement)
        value += quantity * intrinsic
    return float(100 * value)


def cash_check(row: dict, native: dict[str, float]) -> None:
    from tools.research_studies.xsp_independent.common import session_end

    signal, entry, exit_time = (pd.Timestamp(row[k]) for k in ("signal_time", "entry_time", "exit_time"))
    cutoff = session_end(row["date"]) - pd.Timedelta(minutes=15)
    assert pd.Timedelta(0) < entry - signal <= pd.Timedelta(minutes=2), row
    assert entry < exit_time, row
    opening_cash = -100 * row["entry_ask"] - 2.60
    assert np.isclose(-opening_cash, row["initial_risk_dollars"]), row
    assert np.isclose(-opening_cash + 5, row["stressed_initial_risk_dollars"]), row
    if row["policy"] == "settlement":
        assert row["settlement_source"] == "cboe_native_xsp_published_settlement", row
        assert row["settlement"] == native[row["date"]], row
        cash = opening_cash + independent_payoff(row["center"], row["width"], native[row["date"]], row["right"])
        assert exit_time == session_end(row["date"]), row
        assert row["closing_fee_dollars"] == row["closing_stress_dollars"] == 0, row
        stress_cost = 5
        mid_cash = cash + 100 * (row["entry_ask"] - row["entry_mark"])
    else:
        assert exit_time <= cutoff, row
        assert row["closing_fee_dollars"] == 2.60, row
        assert row["closing_stress_dollars"] == 5., row
        cash = opening_cash + 100 * row["liquidation_bid"] - 2.60
        stress_cost = 10
        mid_cash = 100 * (row["exit_mark"] - row["entry_mark"]) - 5.20
        if row["exit_reason"] == "first_trigger":
            trigger = pd.Timestamp(row["trigger_time"])
            assert entry < trigger < exit_time <= trigger + pd.Timedelta(minutes=2), row
            if row["policy"] == "net_profit_25pct":
                observed = 100 * (row["trigger_liquidation_bid"] - row["entry_ask"]) - 5.20
                assert observed >= .25 * (-opening_cash), row
        elif row["policy"] == "baseline_60m":
            target = min(entry + pd.Timedelta(minutes=60), cutoff)
            assert target <= exit_time <= min(target + pd.Timedelta(minutes=2), cutoff), row
        else:
            assert exit_time == cutoff, row
    for key, expected in (("marketable_net", cash), ("stressed_net", cash - stress_cost),
                          ("midpoint_net", mid_cash)):
        assert np.isclose(row[key], expected, atol=1e-7), (key, row)


def native_check() -> dict[str, float]:
    """Match every derived CSV row back to raw Cboe records without parser reuse."""
    frame = pd.read_csv(SETTLEMENT_ROOT / "settlements-native.csv")
    raw_values: dict[str, set[float]] = {}
    for name in ("cboe-weeklys-2026.json", "cboe-monthly-2026.json", "cboe-eom-2026.json"):
        for row in json.loads((SETTLEMENT_ROOT / "raw" / name).read_text())["data"]:
            if row["trading_symbol"] == row["settlement_symbol"] == "XSP":
                raw_values.setdefault(row["expiration_date"], set()).add(float(row["settlement_value"]))
    for row in frame.itertuples():
        assert raw_values[row.date] == {row.settlement}, row
    assert len(frame) == frame.date.nunique() == 185
    return dict(zip(frame.date, frame.settlement, strict=True))


def raw_examples(rows: list[dict]) -> list[dict]:
    selected = []
    keys = sorted({(r["family"], r["width"], r["policy"]) for r in rows})
    for key in keys:
        cell = sorted([r for r in rows if (r["family"], r["width"], r["policy"]) == key
                       and r["status"] == "completed"], key=lambda r: r["date"])
        if cell:
            selected.extend(cell[:1] + cell[-1:])
    checked = []
    for day in sorted({r["date"] for r in selected}):
        raw = pd.read_parquet(ROOT / f"data/thetadata/xsp_0dte/quote_1m/2026/{day}.parquet")
        for row in (r for r in selected if r["date"] == day):
            phases = [("entry", row["entry_time"], row["entry_ask"])]
            if row["policy"] != "settlement":
                phases.append(("exit", row["exit_time"], row["liquidation_bid"]))
            for phase, when, expected in phases:
                snap = raw[(raw.timestamp == pd.Timestamp(when)) & (raw.right == row["right"])]
                value = 0.
                for k, quantity in ((row["center"] - row["width"], 1), (row["center"], -2),
                                    (row["center"] + row["width"], 1)):
                    leg = snap[snap.strike == k]
                    assert len(leg) == 1, row
                    leg = leg.iloc[0]
                    side = "ask" if (phase == "entry") == (quantity > 0) else "bid"
                    assert leg[side + "_size"] >= abs(quantity), row
                    value += quantity * leg[side]
                assert np.isclose(value, expected, atol=1e-8), row
            checked.append({k: row[k] for k in ("date", "family", "width", "policy", "entry_time", "exit_time")})
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    entries = read_rows(args.run / "entries.jsonl")
    journal = read_rows(args.run / "journal.jsonl")
    summary = json.loads((args.run / "summary.json").read_text())
    manifest = json.loads((args.run / "manifest.json").read_text())
    for path, expected in manifest["sources"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    assert len(entries) == 185 * 8
    assert len({(r["date"], r["family"], r["width"]) for r in entries}) == len(entries)
    accepted = [r for r in entries if r["status"] == "accepted"]
    assert len(journal) == 4 * len(accepted)
    assert len({(r["date"], r["family"], r["width"], r["policy"]) for r in journal}) == len(journal)
    native = native_check()
    complete = [r for r in journal if r["status"] == "completed"]
    for row in complete:
        cash_check(row, native)
    old = pd.read_csv(PRIOR)
    old = old[(old.status == "completed") & old.variant.isin(["MR1", "MR2", "T1", "T2"])]
    current = {(r["date"], r["family"], r["width"]): r for r in complete if r["policy"] == "baseline_60m"}
    old_keys = {(r.date, r.variant, r.width) for r in old.itertuples()}
    assert old_keys == set(current), "timed-exit baseline opportunity set changed"
    for row in old.itertuples():
        now = current[row.date, row.variant, row.width]
        assert row.center == now["center"] and row.right == now["right"]
        for field in ("entry_ask", "liquidation_bid", "entry_mark", "exit_mark"):
            assert np.isclose(getattr(row, field), now[field])
        assert pd.Timestamp(row.entry_ts) == pd.Timestamp(now["entry_time"])
        assert pd.Timestamp(row.exit_ts) == pd.Timestamp(now["exit_time"])
        assert np.isclose(row.pnl_marketable, now["marketable_net"])
        assert np.isclose(row.pnl_stressed, now["stressed_net"])
    cells = {}
    for key, cell in summary["cells"].items():
        family, width_text = key.split("_w")
        width = int(width_text)
        cell_rows = [r for r in journal if r["family"] == family and r["width"] == width]
        for policy, stats in cell["policies"].items():
            observed = [r for r in cell_rows if r["policy"] == policy and r["status"] == "completed"]
            assert stats["completed"] == len(observed), (key, policy)
            for model in ("midpoint_net", "marketable_net", "stressed_net"):
                x = np.array([r[model] for r in observed], dtype=float)
                assert np.isclose(stats[model]["total"], x.sum()), (key, policy, model)
                positives = x[x > 0]
                assert np.isclose(stats[model]["top3_removed"], x.sum() - np.sort(positives)[-3:].sum())
                for half, first in (("first", True), ("second", False)):
                    expected = sum(r[model] for r in observed
                                   if (r["date"] < summary["split_date"]) == first)
                    assert np.isclose(stats[model]["halves"][half], expected)
            baseline = {r["date"]: r for r in cell_rows if r["policy"] == "baseline_60m"
                        and r["status"] == "completed"}
            paired = [r for r in observed if r["date"] in baseline]
            assert stats["paired_baseline"]["common_completed_entries"] == len(paired)
            delta = sum(r["stressed_net"] - baseline[r["date"]]["stressed_net"] for r in paired)
            assert np.isclose(stats["paired_baseline"]["stressed_difference"], delta)
            if policy == "baseline_60m":
                continue
            net = stats["stressed_net"]
            gates = {"stressed_positive": net["total"] > 0, "top3_removed_positive": net["top3_removed"] > 0,
                     "both_halves_positive": all(x > 0 for x in net["halves"].values()),
                     "paired_advantage": stats["paired_baseline"]["stressed_difference"] > 0}
            cells[f"{key}/{policy}"] = {"completed": stats["completed"], "stressed_net": net["total"],
                                        "gates": gates, "interesting": all(gates.values())}
    raw = raw_examples(journal)
    result = {"native_settlements_matched_to_raw": len(native), "entry_opportunities": len(entries),
              "accepted_entries": len(accepted), "completed_records_cash_clock_checked": len(complete),
              "original_baseline_records_exactly_matched": len(old), "raw_example_records": len(raw),
              "new_exit_cells": cells, "interesting_leads": [k for k, v in cells.items() if v["interesting"]],
              "raw_examples": raw, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
                  args.run / "entries.jsonl", args.run / "journal.jsonl", args.run / "summary.json")}}
    (args.out / "review.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k not in ("raw_examples", "input_sha256")}, indent=2))


if __name__ == "__main__":
    main()
