"""Independently reconcile quiet-fly opening prices and native expiry cash."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent.mean_reversion import digest, write_new
from tools.research_studies.xsp_independent.realization import SETTLEMENTS

ROOT = Path(__file__).resolve().parents[3]


def review(run: Path) -> dict:
    rows = [json.loads(line) for line in (run / "journal.jsonl").read_text().splitlines()]
    manifest = json.loads((run / "completed-manifest.json").read_text())
    settlements = pd.read_csv(SETTLEMENTS).set_index("date").settlement.to_dict()
    assert digest(SETTLEMENTS) == manifest["settlement_sha256"]
    completed, checks = [r for r in rows if r["status"] == "completed"], []
    for source in manifest["inputs"]:
        path = ROOT / source["path"]
        assert digest(path) == source["sha256"]
        day_rows = [r for r in completed if r["date"] == path.stem]
        raw = pd.read_parquet(path)
        for r in day_rows:
            stamp = pd.Timestamp(r["entry_time"])
            assert stamp.date().isoformat() == r["date"]
            assert dt.time(10, 30) < stamp.time() <= dt.time(10, 32)
            snap = raw[raw.timestamp == stamp].set_index(["right", "strike"])
            cash, mid_cash, expiry, contracts = 0.0, 0.0, 0.0, 0
            needs = Counter()
            for c in r["centers"]:
                w = r["width"]
                if r["form"] == "IRON":
                    legs = [("PUT", c - w, 1), ("PUT", c, -1),
                            ("CALL", c, -1), ("CALL", c + w, 1)]
                else:
                    legs = [(r["form"], c - w, 1), (r["form"], c, -2),
                            (r["form"], c + w, 1)]
                for right, strike, qty in legs:
                    quote = snap.loc[(right, strike)]
                    assert 0 <= quote.bid <= quote.ask and quote.ask > 0
                    needs[(right, strike, qty > 0)] += abs(qty)
                    cash -= qty * (quote.ask if qty > 0 else quote.bid) * 100
                    mid_cash -= qty * (quote.bid + quote.ask) * 50
                    s = settlements[r["date"]]
                    value = max(s - strike, 0) if right == "CALL" else max(strike - s, 0)
                    expiry += qty * value * 100
                    contracts += abs(qty)
            for (right, strike, buy), size in needs.items():
                quote = snap.loc[(right, strike)]
                assert quote.ask_size >= size if buy else quote.bid_size >= size and quote.bid > 0
            fee, stress = contracts * .65, len(r["centers"]) * 5
            expected = {"entry_debit": -cash / 100, "gross": cash + expiry,
                        "net": cash + expiry - fee, "stressed": cash + expiry - fee - stress,
                        "midpoint": mid_cash + expiry - fee, "fee": fee,
                        "stress_cost": stress, "gross_contracts": contracts,
                        "terminal_cash_points": expiry / 100}
            for key, value in expected.items():
                assert np.isclose(r[key], value, atol=1e-8, rtol=0), (r["date"], key)
            assert r["stressed"] >= -r["initial_risk"] - 1e-8
            checks.append({"date": r["date"], "arm": r["arm"], "form": r["form"],
                           "width": r["width"], "net": expected["stressed"]})
    assert len(checks) == len(completed)
    summary = json.loads((run / "summary.json").read_text())
    for key, cell in summary["cells"].items():
        group = [r for r in rows if f'{r["arm"]}_w{r["width"]}_{r["form"]}' == key]
        assert sum(cell["statuses"].values()) == summary["sessions"] == len(group)
        net = sum(r["stressed"] for r in group if r["status"] == "completed")
        assert np.isclose(cell.get("stressed", 0), net, atol=1e-8, rtol=0)
    # Match construction comparisons by geometry AND identical opening snapshot.
    matched = []
    for key, iron in {(r["date"], r["arm"], r["width"]): r for r in completed
                      if r["form"] == "IRON"}.items():
        for form in ("CALL", "PUT"):
            other = next((r for r in completed if (r["date"], r["arm"], r["width"]) == key
                          and r["form"] == form), None)
            if other and other["entry_time"] == iron["entry_time"] and other["centers"] == iron["centers"]:
                matched.append({"date": key[0], "arm": key[1], "width": key[2],
                                "comparison": f"IRON_minus_{form}",
                                "net_difference": iron["stressed"] - other["stressed"]})
    comparisons = {}
    for arm in sorted({r["arm"] for r in rows}):
        for width in (2, 4):
            for form in ("CALL", "PUT"):
                group = [r for r in matched if r["arm"] == arm and r["width"] == width
                         and r["comparison"] == f"IRON_minus_{form}"]
                comparisons[f"{arm}_w{width}_IRON_minus_{form}"] = {
                    "matched_snapshots": len(group),
                    "net_difference": sum(r["net_difference"] for r in group)}
    return {"reviewed_at": dt.datetime.now(dt.UTC), "journal_sha256": digest(run / "journal.jsonl"),
            "review_source_sha256": digest(Path(__file__)), "records": len(rows),
            "completed_cash_records": len(checks), "settlement_dates": len(settlements),
            "statuses": dict(Counter(r["status"] for r in rows)),
            "matched_construction_comparisons": comparisons,
            "result": "Every completed record reconciles to raw component quotes and independent option intrinsic cash; no broker fills established."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    result = review(args.run)
    write_new(args.run / "cash-review.json", result)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
