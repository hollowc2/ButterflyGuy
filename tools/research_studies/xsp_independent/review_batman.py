"""Independent raw-option cash ledger for every completed mixed-study episode."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent.mean_reversion import digest, write_new

ROOT = Path(__file__).resolve().parents[3]


def reconcile(run: Path) -> dict:
    rows = [json.loads(line) for line in (run / "journal.jsonl").read_text().splitlines()]
    manifest = json.loads((run / "completed-manifest.json").read_text())
    if any(digest(ROOT / name) != h for name, h in manifest["inputs"].items()):
        raise ValueError("Study inputs changed")
    native_path = ROOT / "reports/research/xsp-realization-2026-11-11/settlement/settlements-native.csv"
    settlements = pd.read_csv(native_path).set_index("date").settlement.to_dict()
    examples, ledgers, errors = [], [], []
    for date in sorted({r["date"] for r in rows if r["status"] == "completed"}):
        # Direct raw Parquet and per-option intrinsic; no simulator pricing/payoff functions.
        raw = pd.read_parquet(ROOT / f"data/thetadata/xsp_0dte/quote_1m/2026/{date}.parquet")
        if set(raw.symbol) != {"XSP"} or set(pd.to_datetime(raw.expiration).dt.strftime("%Y-%m-%d")) != {date}:
            raise ValueError("Raw identity mismatch")
        raw["timestamp"] = raw.timestamp.dt.tz_convert("America/New_York")
        raw = raw.set_index(["timestamp", "right", "strike"])
        for row in (r for r in rows if r["date"] == date and r["status"] == "completed"):
            iron = row["cell"].startswith("prior_")
            centers = row["centers"]
            if iron:
                c = centers[0]
                legs = [("PUT", c-4, 1), ("PUT", c, -1),
                        ("CALL", c, -1), ("CALL", c+4, 1)]
            else:
                low, high = centers
                legs = [("PUT", low-4, 1), ("PUT", low, -2), ("PUT", low+4, 1),
                        ("CALL", high-4, 1), ("CALL", high, -2), ("CALL", high+4, 1)]
            transactions = [("open", pd.Timestamp(row["entry_time"]))]
            if row.get("terminal") == "liquidation":
                transactions.append(("close", pd.Timestamp(row["exit_time"])))
            opening_debit = 0.
            closing_credit = 0.
            open_mid = close_mid = 0.
            raw_records = []
            for label, stamp in transactions:
                for right, strike, qty in legs:
                    q = raw.loc[(stamp, right, strike)]
                    if not isinstance(q, pd.Series):
                        raise ValueError("Duplicate raw quote")
                    buy = (qty > 0) == (label == "open")
                    price = float(q["ask" if buy else "bid"])
                    size = float(q["ask_size" if buy else "bid_size"])
                    if not (np.isfinite([price, size, q.bid, q.ask]).all()
                            and 0 <= q.bid <= q.ask and price > 0 and size >= abs(qty)):
                        errors.append([row["cell"], date, label, right, strike, "invalid side/size"])
                    amount = qty * price
                    mark = qty * (q.bid + q.ask) / 2
                    if label == "open":
                        opening_debit += amount
                        open_mid += mark
                    else:
                        closing_credit += amount
                        close_mid += mark
                    raw_records.append({"transaction": label, "timestamp": stamp.isoformat(),
                                        "right": right, "strike": strike, "position_qty": qty,
                                        "side": "buy" if buy else "sell", "price": price,
                                        "needed_size": abs(qty), "displayed_size": size,
                                        "bid": float(q.bid), "ask": float(q.ask),
                                        "bid_size": float(q.bid_size), "ask_size": float(q.ask_size),
                                        "signed_cash_dollars": (-1 if label == "open" else 1)*100*amount})
            settled_cash = 0.
            if len(transactions) == 1:
                s = settlements[date]
                for right, strike, qty in legs:
                    intrinsic = max(s-strike, 0) if right == "CALL" else max(strike-s, 0)
                    settled_cash += 100*qty*intrinsic
            gross_units = sum(abs(qty) for _, _, qty in legs)
            fees = gross_units * .65 * len(transactions)
            stress = (5 if iron else 10) * len(transactions)
            terminal_cash = 100*closing_credit if len(transactions) == 2 else settled_cash
            result = terminal_cash - 100*opening_debit - fees - stress
            risk = 100 * (opening_debit + (4 if iron else 0)) + gross_units*.65 + (5 if iron else 10)
            midpoint = ((100*close_mid if len(transactions) == 2 else settled_cash)
                        - 100*open_mid - fees)
            checks = {"entry_debit": opening_debit, "stressed": result,
                      "fee": fees, "stress_cost": stress, "initial_risk": risk,
                      "midpoint": midpoint, "risk_units": result/risk}
            for key, value in checks.items():
                if abs(row[key] - value) > 1e-7:
                    errors.append([row["cell"], date, key, row[key], value])
            ledger = {"date": date, "cell": row["cell"], "opening_cash": -100*opening_debit,
                      "terminal_cash": terminal_cash, "fees": fees, "stress": stress,
                      "stressed": result, "initial_risk": risk,
                      "terminal": "liquidation" if len(transactions) == 2 else "settlement",
                      "final_option_inventory": 0}
            ledgers.append(ledger)
            # Preserve every raw side, not only attractive examples.
            examples.append({**ledger, "raw_quotes": raw_records,
                             "native_settlement": settlements[date] if len(transactions) == 1 else None})
    out = run / "cash-review"
    out.mkdir(exist_ok=False)
    for name, data in (("ledger.jsonl", ledgers), ("raw-quotes.jsonl", examples)):
        with (out / name).open("x") as handle:
            for item in data:
                handle.write(json.dumps(item, allow_nan=False) + "\n")
    report = {"method": "Independent direct raw contract-side cash sums and individual option intrinsic settlement. No simulator component/payoff/account calls. All completed episodes checked, all raw sides retained.",
              "completed_records": len(ledgers), "errors": errors,
              "terminal_counts": dict(Counter(r["terminal"] for r in ledgers)),
              "cell_totals": {key: sum(r["stressed"] for r in ledgers if r["cell"] == key)
                              for key in sorted({r["cell"] for r in ledgers})},
              "journal_sha256": digest(run / "journal.jsonl"),
              "review_source_sha256": digest(Path(__file__)),
              "files": {name: digest(out / name) for name in ("ledger.jsonl", "raw-quotes.jsonl")}}
    write_new(out / "review.json", report)
    if errors:
        raise AssertionError(errors[:10])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(reconcile(args.run), indent=2))


if __name__ == "__main__":
    main()
