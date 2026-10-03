"""Synthetic regressions for the F2 draft; no market data or database required."""

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

SPEC = importlib.util.spec_from_file_location(
    "f2_shadow_report", Path(__file__).parents[1] / "tools/f2_shadow_report.py"
)
f2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(f2)


def row(index, pnl=100.0, status="traded"):
    day = dt.date(2026, 10, 2) + dt.timedelta(days=index)
    return {"trade_id": str(index), "session_date": str(day),
            "decision_time": f"{day}T14:00:00+00:00", "status": status,
            "f2_stressed": pnl, "f2_midpoint": pnl, "e0_stressed": 0.0}


def summary(rows):
    return f2.summarize(rows, Path("synthetic-cohort"), f2.START)[0]


def test_endpoint_uses_first_complete_sample_only():
    result = summary([row(i) for i in range(61)])
    assert result["f2_stressed"]["trades"] == 60
    assert result["f2_stressed"]["net"] == 6000.0
    assert result["endpoint_reached"]


def test_drawdown_stop_does_not_include_subsequent_recovery():
    result = summary([row(0, -9000), row(1, 10000), row(2, 10000)])
    assert result["f2_stressed"]["trades"] == 1
    assert result["f2_stressed"]["net"] == -9000
    assert result["stopped_early"]


def test_all_winning_sample_passes_profit_factor_gate():
    result = summary([row(i) for i in range(60)])
    assert result["gates"]["f2_profit_factor_above_one"]


def test_chronological_order_controls_drawdown_and_stop():
    result = summary([row(2, 10000), row(1, 10000), row(0, -9000)])
    assert result["f2_stressed"]["net"] == -9000


@pytest.mark.parametrize("status", ["pending_settlement", "no_fresh_vix"])
def test_unresolved_evidence_blocks_later_entries(status):
    result = summary([row(0), row(1, status=status), row(2, 10000)])
    assert result["f2_stressed"]["trades"] == 1
    assert not result["endpoint_reached"]


def test_endpoint_waits_for_registered_winner_count():
    rows = [row(i, 100 if i < 7 else -1) for i in range(60)]
    assert not summary(rows)["endpoint_reached"]
    assert summary([*rows, row(60)]) ["endpoint_reached"]


def test_drawdown_exactly_at_limit_does_not_stop():
    assert not summary([row(0, -8000)]) ["stopped_early"]


def test_profit_factor_gate_uses_unrounded_ratio():
    assert summary([row(0, 100.01), row(1, -100)]) ["gates"][
        "f2_profit_factor_above_one"]


def test_unpriced_paired_baseline_blocks_comparison():
    missing = {**row(0), "e0_stressed": None}
    assert summary([missing, row(1)])["f2_stressed"]["trades"] == 0


def test_frozen_manifest_and_integrity_are_required(monkeypatch, tmp_path):
    monkeypatch.setattr(f2, "input_hashes", lambda _: {"manifest.json": "wrong"})
    with pytest.raises(ValueError, match="original frozen"):
        f2.load_cohort(tmp_path)
    monkeypatch.setattr(f2, "input_hashes", lambda _: {"manifest.json": f2.MANIFEST_SHA256})
    monkeypatch.setattr(f2, "verify_cohort", lambda *_: ["record hash mismatch"])
    monkeypatch.setattr(f2, "load_manifest", lambda _: {})
    monkeypatch.setattr(f2, "manifest_drift", lambda *_: [])
    cohort = tmp_path / "reports/prospective_execution/study"
    with pytest.raises(ValueError, match="record hash mismatch"):
        f2.load_cohort(cohort)


def test_resolved_evidence_and_hashes_cannot_silently_change(tmp_path):
    original = row(0)
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({**original, "record_hash": f2.canonical_hash(original)}))
    f2.check_previous([original], ledger)
    with pytest.raises(ValueError, match="evidence changed"):
        f2.check_previous([row(0, 200)], ledger)
    ledger.write_text(json.dumps({**original, "record_hash": "tampered"}))
    with pytest.raises(ValueError, match="invalid record hash"):
        f2.check_previous([original], ledger)


def test_pending_evidence_can_be_completed_on_retry(tmp_path):
    pending = row(0, status="pending_settlement")
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({**pending, "record_hash": f2.canonical_hash(pending)}))
    f2.check_previous([row(0)], ledger)


def test_invalid_cohort_is_rejected_before_database_access(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["f2_shadow_report.py"])
    monkeypatch.setattr(f2, "input_hashes", lambda _: {})
    def reject(_):
        raise ValueError("cohort integrity failed")
    monkeypatch.setattr(f2, "load_cohort", reject)
    connect = AsyncMock()
    monkeypatch.setattr(f2.asyncpg, "connect", connect)
    with pytest.raises(ValueError, match="cohort integrity"):
        f2.main()
    connect.assert_not_called()


def test_dry_run_start_is_rejected_before_input_reads(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["f2_shadow_report.py", "--start", "2026-09-22"])
    def forbidden(_):
        pytest.fail("read cohort inputs for an earlier dry run")
    monkeypatch.setattr(f2, "input_hashes", forbidden)
    with pytest.raises(ValueError, match="fixed start"):
        f2.main()


def trade(index, entry=2.526):
    r = row(index)
    return {"session_date": r["session_date"], "decision_time": r["decision_time"],
            "trade_id": r["trade_id"], "record_hash": "synthetic", "direction": "CALL",
            "lower_strike": 80, "center_strike": 100, "upper_strike": 120,
            "wing_width": 20, "exit_reason": "cash_settled",
            "accounting": {model: {"status": "priced", "entry_price": entry,
                                    "net_pnl": round(100 * (20 - entry), 2)}
                           for model in f2.MODELS}}


@pytest.fixture
def database(monkeypatch):
    conn = AsyncMock()
    connect = AsyncMock(return_value=conn)
    monkeypatch.setattr(f2.asyncpg, "connect", connect)
    async def vix(_, decided):
        return 20, decided - dt.timedelta(seconds=60)
    monkeypatch.setattr(f2, "get_vix_snapshot_at", vix)
    close = AsyncMock(return_value=100)
    monkeypatch.setattr(f2, "get_official_settlement_spot", close)
    return conn, close


async def test_cash_settlement_equals_cohort_under_every_model(database):
    t = trade(0)
    rows = await f2.score("synthetic", [t], 300, f2.START)
    for model, short in f2.MODELS.items():
        assert rows[0][f"f2_{short}"] == t["accounting"][model]["net_pnl"]
    assert rows[0]["vix_snapshot_time"]
    assert rows[0]["cohort_record_hash"] == "synthetic"
    database[0].close.assert_awaited_once()


async def test_no_database_reads_after_endpoint(database):
    rows = await f2.score("synthetic", [trade(i) for i in range(61)], 300, f2.START)
    assert len(rows) == 60
    assert database[1].await_count == 60


async def test_no_database_reads_after_stop_or_missing_settlement(database):
    rows = await f2.score("synthetic", [trade(0, 110), trade(1)], 300, f2.START)
    assert len(rows) == 1
    database[1].reset_mock()
    database[1].return_value = None
    rows = await f2.score("synthetic", [trade(0), trade(1)], 300, f2.START)
    assert len(rows) == 1 and rows[0]["status"] == "pending_settlement"
    assert database[1].await_count == 1


@pytest.mark.parametrize("age", [-1, 301])
async def test_stale_or_future_vix_blocks_later_queries(database, monkeypatch, age):
    async def vix(_, decided):
        return 20, decided - dt.timedelta(seconds=age)
    monkeypatch.setattr(f2, "get_vix_snapshot_at", vix)
    rows = await f2.score("synthetic", [trade(0), trade(1)], 300, f2.START)
    assert len(rows) == 1 and rows[0]["status"] == "no_fresh_vix"
