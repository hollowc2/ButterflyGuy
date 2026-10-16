"""Second implementation: validate the frozen fidelity run directly against raw JSON."""

import csv
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(not os.environ.get("NDX_FIDELITY_EVIDENCE"), reason="private snapshot required")
def test_decimal_raw_rows_independently_reconcile_frozen_run():
    evidence = Path(os.environ["NDX_FIDELITY_EVIDENCE"]) / "ndx-minute-continuation-20261015-v2"
    run = REPO / "reports/research/ndx-02-fidelity-20261015/run-01"
    records = [json.loads(line) for line in (run / "observations.jsonl").read_text().splitlines()]
    details = [json.loads(line) for line in (run / "legs.jsonl").read_text().splitlines()]
    groups = defaultdict(list)
    with (evidence / "prices/extract.csv").open(newline="") as stream:
        raw = list(csv.DictReader(stream))
    for i, row in enumerate(raw, 1):
        q = json.loads(row["raw_quote"], parse_float=Decimal)
        groups[int(row["trade_id"]), dt.datetime.fromisoformat(q["snapshot_time"])].append((i, q))
    specs = {s["id"]: s for s in json.loads((evidence / "cohort.json").read_text())}
    counts, residuals, negative_midpoints, negative_marks = Counter(), [], set(), set()
    for obs in records:
        key = obs["id"], dt.datetime.fromisoformat(obs["snapshot_time"])
        rows = groups[key]
        q = {q["symbol"]: q for _, q in rows}
        lo, ce, up = [q[s] for s in specs[key[0]]["symbols"]]
        mark = lo["mark"] - ce["mark"] - ce["mark"] + up["mark"]
        bid = lo["bid"] - ce["ask"] - ce["ask"] + up["bid"]
        ask = lo["ask"] - ce["bid"] - ce["bid"] + up["ask"]
        mid = (bid + ask) / Decimal(2)
        assert Decimal(obs["provider_composite_mark"]) == mark
        assert Decimal(obs["raw_composite_bid"]) == bid
        assert Decimal(obs["raw_composite_ask"]) == ask
        assert Decimal(obs["mark_minus_composite_midpoint"]) == mark - mid
        if mark < 0:
            negative_marks.add(key)
        if mid < 0:
            negative_midpoints.add(key)
        flags = {
            "negative_mark": mark < Decimal("-.00011"),
            "negative_bid": bid < Decimal("-.00011"),
            "midpoint_difference": abs(mark - mid) > Decimal(".00011"),
        }
        for flag, value in flags.items():
            assert obs["flags"][flag] == value
            counts[flag] += value
        counts["overlap"] += flags["negative_mark"] and flags["midpoint_difference"]
        assert sorted(obs["raw_csv_records"]) == sorted(i for i, _ in rows)
        for quote in [lo, ce, up]:
            assert quote["bid"] <= quote["mark"] <= quote["ask"]
            residuals.append(quote["mark"] - (quote["bid"] + quote["ask"]) / Decimal(2))
        assert obs["consumer_availability_time"] is None
        assert not obs["minute_replay_eligible"]
    assert negative_marks == negative_midpoints
    assert max(abs(x) for x in residuals) == Decimal(".005")
    assert counts == {
        "negative_mark": 157,
        "negative_bid": 635,
        "midpoint_difference": 816,
        "overlap": 103,
    }
    # Every raw row, including incomplete groups, survives in the leg ledger exactly once.
    assert sorted(q["raw_csv_record"] for q in details) == list(range(1, len(raw) + 1))
    for q in details:
        row = raw[q["raw_csv_record"] - 1]
        assert q["raw_quote_json"] == row["raw_quote"]
        assert q["raw_meta_json"] == row["raw_meta"]
    assert len(records) == 1114 and len(details) == 3364
