"""Independent hand arithmetic and causal clock fixtures; no strategy outcomes."""

import json
import os
import socket
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from butterfly_guy.research.ndx_continuation import ROOT, at, normalize_group
from butterfly_guy.research.ndx_evidence import digest, write_json
from butterfly_guy.research.ndx_quote_fidelity import aggregate, analyze, attribute, leg_record, run

BASE = ROOT / "docs/research/ndx-strategy/evidence/2026-10-15"


@pytest.fixture
def fixture():
    contract = json.loads((BASE / "ndx02-fidelity-contract.json").read_text())
    old = json.loads((BASE / "ndx02-continuation-contract-v2.json").read_text())
    spec = {
        "id": 9,
        "session": "2026-10-09",
        "direction": "CALL",
        "exit_time": "2026-10-09T19:00:00+00:00",
        "close_time": "2026-10-09T20:00:00+00:00",
        "symbols": ["NDXP  261009C00100000", "NDXP  261009C00200000", "NDXP  261009C00300000"],
        "strikes": [100, 200, 300],
    }
    raw = []
    for i, (bid, ask, mark) in enumerate([(1, 3, 2.01), (3, 5, 4.01), (2, 4, 3.0)]):
        q = dict(
            symbol=spec["symbols"][i],
            strike=spec["strikes"][i],
            bid=bid,
            ask=ask,
            mark=mark,
            expiration=spec["session"],
            underlying="NDX",
            option_type="CALL",
            snapshot_time="2026-10-09T19:01:00+00:00",
        )
        raw.append({"trade_id": "9", "_record": i + 1, "raw_quote": json.dumps(q), "raw_meta": ""})
    normalized = normalize_group(
        spec,
        at("2026-10-09T19:01:00+00:00"),
        [{"quote": json.loads(r["raw_quote"]), "meta": None} for r in raw],
        old,
    )
    return contract, spec, raw, normalized


def test_independent_signed_arithmetic(fixture):
    contract, spec, raw, normalized = fixture
    obs, legs = attribute(spec, normalized, raw, contract)
    assert Decimal(obs["provider_composite_mark"]) == Decimal("-3.01")
    assert Decimal(obs["raw_composite_bid"]) == -7
    assert Decimal(obs["raw_composite_ask"]) == 1
    assert Decimal(obs["composite_midpoint"]) == -3
    assert Decimal(obs["mark_minus_composite_midpoint"]) == Decimal("-.01")
    assert [Decimal(q["weighted_mark_minus_midpoint"]) for q in legs] == [
        Decimal(".01"),
        Decimal("-.02"),
        0,
    ]
    assert obs["flags"]["negative_mark"] and obs["flags"]["midpoint_difference"]
    assert not obs["flags"]["any_leg_outside_market"]
    assert obs["timing_coverage"] == "unknown"
    assert obs["event_time_dispersion_seconds"] is None
    assert obs["consumer_availability_time"] is None
    assert not obs["minute_replay_eligible"] and not obs["R0_30_second_continuation_eligible"]
    assert obs["raw_csv_records"] == [1, 2, 3]


def test_partial_clocks_old_leg_and_pass_start(fixture):
    contract, spec, raw, normalized = fixture
    normalized["snapshot_metadata"] = {"chain_fetch_completed_at": "2026-10-09T19:01:03+00:00"}
    for i, (event, age) in enumerate(
        [("2026-10-09T19:01:02+00:00", 1), ("2026-10-09T18:56:33+00:00", 270)]
    ):
        q = json.loads(raw[i]["raw_quote"])
        q.update(quote_event_ts=event, quote_age_s=age, bid_size=0)
        raw[i]["raw_quote"] = json.dumps(q)
    obs, legs = attribute(spec, normalized, raw, contract)
    assert obs["timing_coverage"] == "partial"
    assert obs["known_event_count"] == 2
    assert obs["event_time_dispersion_seconds"] is None
    assert obs["known_event_time_dispersion_seconds"] == 269
    assert obs["oldest_reported_age_seconds"] == 270
    assert legs[0]["event_after_pass_start_seconds"] == 2
    assert legs[0]["event_to_local_fetch_completion_seconds"] == 1
    assert legs[1]["bid_size"] == 0
    assert obs["consumer_availability_time"] is None
    assert not obs["freshness_verified"]


@pytest.mark.parametrize(
    "quote,category,outside",
    [
        ({"bid": 1, "ask": 2, "mark": 3}, "recorded_nonnegative_uncrossed", True),
        ({"bid": 0, "ask": 0, "mark": 0}, "recorded_nonnegative_uncrossed", False),
        ({"bid": 2, "ask": 1, "mark": 1.5}, "invalid", True),
        ({"bid": None, "ask": 1, "mark": 1}, "unknown", None),
    ],
)
def test_unknown_zero_invalid_and_market(quote, category, outside):
    r = leg_record(quote, 1, {}, "2026-10-09T19:00:00+00:00", Decimal(".00011"), Decimal(".005"))
    assert r["price_sanity"] == category
    assert r["mark_outside_own_market"] is outside
    assert r["quote_event_ts"] is None
    assert r["timing_coverage"] == "unknown"


def test_overlap_cancellation_and_exclusions(fixture):
    contract, spec, raw, normalized = fixture
    # Equal +.005 residuals cancel exactly under +1/-2/+1, despite leg differences.
    for row in raw:
        q = json.loads(row["raw_quote"])
        q["mark"] = (q["bid"] + q["ask"]) / 2 + 0.005
        row["raw_quote"] = json.dumps(q)
    normalized["provider_composite_mark"] = -3
    normalized["mark_minus_composite_midpoint"] = 0
    obs, legs = attribute(spec, normalized, raw, contract)
    assert not obs["flags"]["midpoint_difference"]
    assert obs["flags"]["any_leg_midpoint_difference"]
    assert all(q["compatible_with_half_cent_midpoint_rounding"] for q in legs)
    counts = aggregate([obs])
    assert counts["flags"]["negative_mark"] == 1
    assert counts["negative_mark_and_midpoint_difference"] == 0
    # Retain incomplete groups and their individual raw rows as explicit exclusions.
    rejected = {"id": 9, "snapshot_time": normalized["snapshot_time"], "reasons": ["incomplete"]}
    results = analyze([spec], [], [rejected], raw[:2], contract)
    assert len(results[1]) == 2 and len(results[2]) == 1
    assert results[-1]["excluded_groups"] == 1
    assert all(q["structural_category"] == "excluded" for q in results[1])


def test_timestamp_requires_timezone():
    with pytest.raises(ValueError, match="naive"):
        at("2026-10-09T19:00:00")


@pytest.mark.skipif(not os.environ.get("NDX_FIDELITY_EVIDENCE"), reason="private snapshot required")
def test_private_offline_and_integrity(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    real_run = subprocess.run

    def git_only(cmd, *args, **kwargs):
        assert cmd in (["git", "rev-parse", "HEAD"], ["git", "status", "--short"])
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", git_only)
    args = dict(
        evidence_root=Path(os.environ["NDX_FIDELITY_EVIDENCE"]),
        manifest=BASE / "ndx02-continuation-snapshot.json",
        continuation_parent=ROOT / "reports/research/ndx-02-continuation-20261015/run-01",
        execution_parent=ROOT / "reports/research/ndx-02-20261015/run-02",
        baseline_parent=ROOT / "reports/research/ndx-01-20261015/run-03",
        config=BASE / "ndx02-fidelity-contract.json",
        source_lock=BASE / "ndx02-fidelity-source-lock.json",
        output=tmp_path / "run",
    )
    result = run(**args)
    assert (result["observations"], result["raw_leg_rows"], result["excluded_groups"]) == (
        1114,
        3364,
        11,
    )
    assert result["flags"]["negative_mark"] == 157
    assert result["flags"]["negative_bid"] == 635
    assert result["flags"]["midpoint_difference"] == 816
    assert result["timing_coverage"] == {"all": 148, "unknown": 966}
    assert result["minute_replay_eligible_trades"] == result["R0_eligible_trades"] == 0
    with pytest.raises(FileExistsError):
        run(**args)
    lock = json.loads(args["source_lock"].read_text())
    lock["config_sha256"] = "bad"
    bad = tmp_path / "bad-lock.json"
    write_json(bad, lock)
    with pytest.raises(ValueError, match="lock/config"):
        run(**(args | {"source_lock": bad, "output": tmp_path / "bad-run"}))
    assert not (tmp_path / "bad-run").exists()
    manifest = json.loads((args["output"] / "run.json").read_text())
    assert all(digest(args["output"] / p) == h for p, h in manifest["output_sha256"].items())
