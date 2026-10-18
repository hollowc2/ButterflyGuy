"""Independent fixtures for continuation identity, raw prices and sampling coverage."""

import copy
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from butterfly_guy.research.ndx_continuation import (
    ROOT,
    at,
    audit,
    cadence,
    historical_inventory_group,
    normalize_group,
    run,
    stats,
    timing_diagnostics,
)
from butterfly_guy.research.ndx_evidence import digest, new_directory, verify, write_json

BASE = ROOT / "docs/research/ndx-strategy/evidence/2026-10-15"


@pytest.fixture
def contract():
    return json.loads((BASE / "ndx02-continuation-contract-v2.json").read_text())


@pytest.fixture
def spec():
    return {
        "id": 4,
        "session": "2026-08-13",
        "direction": "PUT",
        "exit_time": "2026-08-13T19:57:30+00:00",
        "close_time": "2026-08-13T20:00:00+00:00",
        "symbols": ["NDXP  260813P00100000", "NDXP  260813P00200000", "NDXP  260813P00300000"],
        "strikes": ["100", "200", "300"],
    }


def group(spec, ts="2026-08-13T19:58:10+00:00"):
    return [
        {
            "quote": {
                "snapshot_time": ts,
                "symbol": symbol,
                "strike": strike,
                "underlying": "NDX",
                "option_type": "PUT",
                "expiration": spec["session"],
                "bid": bid,
                "ask": bid + 1,
                "mark": mark,
                "quote_event_ts": None,
                "quote_age_s": None,
            },
            "meta": None,
        }
        for symbol, strike, bid, mark in zip(
            spec["symbols"], spec["strikes"], [1, 2, 4], [1.4, 2.41, 4.4]
        )
    ]


def test_raw_composite_and_provider_marks_preserved(spec, contract):
    obs = normalize_group(spec, at("2026-08-13T19:58:10+00:00"), group(spec), contract)
    assert obs["eligible"]
    assert obs["raw_composite_bid"] == -1  # never clipped to zero
    assert obs["raw_composite_ask"] == 3
    assert obs["provider_composite_mark"] == 0.98  # not the midpoint 1.00
    assert obs["mark_minus_composite_midpoint"] == -0.02
    assert obs["negative_composite_bid"]
    assert obs["availability_time"] is None
    assert not obs["freshness_verified"]
    assert not obs["minute_replay_eligible"]


@pytest.mark.parametrize(
    "change,reason",
    [
        ("missing", "incomplete_or_unexpected_symbols"),
        ("duplicate", "duplicate_symbol_key"),
        ("expiration", "wrong_underlying_expiration_or_type"),
        ("strike", "wrong_strike"),
        ("crossed", "negative_or_crossed_leg_quote"),
        ("nan", "missing_or_nonfinite_price"),
    ],
)
def test_bad_groups_are_reported_not_repaired(spec, contract, change, reason):
    raw = group(spec)
    if change == "missing":
        raw.pop()
    elif change == "duplicate":
        raw.append(copy.deepcopy(raw[0]))
    elif change == "expiration":
        raw[0]["quote"]["expiration"] = "2026-08-14"
    elif change == "strike":
        raw[0]["quote"]["strike"] = "101"
    elif change == "crossed":
        raw[0]["quote"]["ask"] = 0.5
    else:
        raw[0]["quote"]["mark"] = "NaN"
    result = normalize_group(spec, at("2026-08-13T19:58:10+00:00"), raw, contract)
    assert reason in result["reasons"]
    assert not result["eligible"]
    assert "raw_composite_bid" not in result


def test_historical_inventory_predicate_is_weaker(spec, contract):
    raw = group(spec)
    raw[0]["quote"]["mark"] = "NaN"
    assert historical_inventory_group(spec, raw)  # original SQL only required mark IS NOT NULL
    assert not normalize_group(spec, at("2026-08-13T19:58:10+00:00"), raw, contract)["eligible"]


def test_boundaries_and_naive_time(spec, contract):
    raw = group(spec)
    assert not normalize_group(spec, at(spec["exit_time"]), raw, contract)["eligible"]
    assert normalize_group(spec, at(spec["close_time"]), raw, contract)["eligible"]
    with pytest.raises(ValueError, match="naive"):
        at("2026-08-13T19:58:10")


def test_exact_thresholds_buckets_and_partial_minutes(spec):
    times = [
        at(x)
        for x in [
            "2026-08-13T19:58:10+00:00",
            "2026-08-13T19:59:10+00:00",
            "2026-08-13T19:59:40+00:00",
        ]
    ]
    c = cadence(spec, times, [30, 60, 90, 120])
    assert c["gaps_above_seconds"] == {"30": 1, "60": 0, "90": 0, "120": 0}
    assert c["expected_full_minute_buckets"] == 2
    assert c["missing_full_minute_buckets"] == []
    assert list(c["multiply_occupied_buckets"].values()) == [2]
    assert c["partial_exit_bucket_observations"] == 0
    assert c["exit_to_first_seconds"] == 40
    assert c["last_to_close_seconds"] == 20


def test_missing_bucket_not_interpolated_and_singleton(spec):
    ts = at("2026-08-13T19:59:10+00:00")
    c = cadence(spec, [ts], [30, 60, 90, 120])
    assert c["missing_full_minute_buckets"] == ["2026-08-13T19:58:00+00:00"]
    assert c["interval_seconds"] == {"n": 0}
    assert c["intervals"] == []
    assert stats([1, 2, 3, 100])["p95_nearest_rank"] == 100


def test_event_clock_diagnostics_do_not_create_availability(spec, contract):
    raw = group(spec)
    for r in raw:
        r["quote"]["quote_event_ts"] = "2026-08-13T19:58:12+00:00"
        r["meta"] = {
            "chain_fetch_started_at": "2026-08-13T19:58:11+00:00",
            "chain_fetch_completed_at": "2026-08-13T19:58:17+00:00",
        }
    obs = normalize_group(spec, at("2026-08-13T19:58:10+00:00"), raw, contract)
    timing = timing_diagnostics(spec, [obs], 0.000001)
    assert timing["event_to_local_fetch_completed_seconds"]["median"] == 5
    assert timing["snapshot_start_to_fetch_completed_seconds"]["median"] == 7
    assert timing["chain_fetch_duration_seconds"]["median"] == 6
    assert timing["counts"]["event_after_snapshot_start"] == 3
    assert timing["counts"]["event_after_fetch_completed"] == 0
    assert obs["availability_time"] is None
    assert not obs["freshness_verified"]


def test_inventory_discrepancy_and_timing_missingness(spec, contract):
    raw = [
        {"trade_id": "4", "raw_quote": json.dumps(r["quote"]), "raw_meta": ""} for r in group(spec)
    ]
    inv = [
        {
            "id": "4",
            "trade_date": spec["session"],
            "exit_time": spec["exit_time"],
            "complete_timestamps": "2",
            "first_ts": "2026-08-13T19:58:10+00:00",
            "last_ts": "2026-08-13T19:59:10+00:00",
        }
    ]
    observations, rejected, coverage, summary = audit([spec], raw, inv, contract)
    assert len(observations) == 1 and not rejected
    assert summary["inventory_mismatch_ids"] == [4]
    t = coverage[0]["timing_coverage"]
    assert t["quote_event_ts_present"] == 0
    assert t["metadata_rows_present"] == 0
    assert t["reported_quote_age_seconds"] == {"n": 0}
    assert summary["minute_replay_eligible_trades"] == 0


def test_manifest_drift_and_overwrite(tmp_path):
    evidence = tmp_path / "raw"
    evidence.mkdir()
    (evidence / "data").write_text("raw")
    write_json(evidence / "manifest.json", {"files": {"data": digest(evidence / "data")}})
    verify(evidence, evidence / "manifest.json")
    (evidence / "data").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify(evidence, evidence / "manifest.json")
    with pytest.raises(ValueError, match="outside"):
        new_directory(evidence / "derived", evidence)
    with pytest.raises(FileExistsError):
        new_directory(evidence)


@pytest.mark.skipif(
    not os.environ.get("NDX_CONTINUATION_EVIDENCE"), reason="private snapshot required"
)
def test_full_offline_snapshot(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    real_run = subprocess.run

    def git_only(cmd, *args, **kwargs):
        assert cmd in (["git", "rev-parse", "HEAD"], ["git", "status", "--short"])
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", git_only)
    root = Path(os.environ["NDX_CONTINUATION_EVIDENCE"])
    args = dict(
        evidence=root,
        manifest=BASE / "ndx02-continuation-snapshot.json",
        inventory=root.parent / "ndx-continuation-inventory-20261015",
        inventory_manifest=BASE / "continuation-inventory-manifest.json",
        execution_parent=ROOT / "reports/research/ndx-02-20261015/run-02",
        baseline_parent=ROOT / "reports/research/ndx-01-20261015/run-03",
        config=BASE / "ndx02-continuation-contract-v2.json",
        source_lock=BASE / "ndx02-continuation-source-lock.json",
        output=tmp_path / "run",
    )
    result = run(**args)
    assert result["trades"] == 17
    assert result["R0_eligible_trades"] == result["minute_replay_eligible_trades"] == 0
    assert result["inventory_mismatch_ids"] == []
    with pytest.raises(FileExistsError):
        run(**args)
