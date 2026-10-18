"""Hand-calculated accounting fixtures, independent of runtime fill implementation."""

import copy
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from butterfly_guy.research.ndx_evidence import digest, new_directory, write_json
from butterfly_guy.research.ndx_execution_audit import (
    ROOT,
    at,
    cohort,
    ledger_row,
    run,
    side_audit,
)

BASE = ROOT / "docs/research/ndx-strategy/evidence/2026-10-15"


@pytest.fixture
def contract():
    return json.loads((BASE / "ndx02-execution-contract.json").read_text())


@pytest.fixture
def trade():
    return {
        "id": "91",
        "trade_date": "2026-10-13",
        "quantity": "1",
        "status": "CLOSED",
        "fill_model": "mark_v1",
        "exit_reason": "drawdown_afternoon",
        "direction": "PUT",
        "lower_strike": "100",
        "center_strike": "200",
        "upper_strike": "300",
        "entry_price": "7.28",
        "exit_price": "2.77",
        "pnl": "-4.51",
        "entry_time": "2026-10-13T14:00:00+00:00",
        "exit_time": "2026-10-13T18:00:00.123456+00:00",
        "entry_diagnostics": json.dumps(
            {
                "observed_bid": 3.4,
                "observed_mark": 7.25,
                "observed_ask": 11.1,
                "configured_slippage": 0.05,
                "marketable_entry_estimate": 11.18,
            }
        ),
        "exit_diagnostics": json.dumps(
            {
                "observed_bid": 1.1,
                "observed_mark": 2.8,
                "observed_ask": 4.5,
                "configured_slippage": 0.05,
                "marketable_exit_estimate": 1.02,
            }
        ),
    }


def event(mark=2.8):
    return [
        {
            "event_type": "trade_exited",
            "ts": "2026-10-13T18:00:00.5+00:00",
            "payload": {"mark_at_signal": mark, "fill_price": 2.77},
        }
    ]


def test_independent_dollars_and_no_double_fee(trade, contract):
    r = ledger_row(trade, event(), {}, {"identity_verified": True}, contract)
    assert r["recorded_paper_pnl_dollars"] == pytest.approx(-451)
    assert r["historical_stored_stress_pnl_dollars"] == pytest.approx(-1016)
    assert r["entry"]["stress_drag_dollars"] == pytest.approx(390)
    assert r["exit"]["stress_drag_dollars"] == pytest.approx(175)
    assert r["drag_identity_difference_dollars"] == pytest.approx(0)
    assert r["entry"]["paper_fill_matches"]
    assert r["exit"]["paper_fill_matches"]
    assert r["entry"]["estimate_matches"]
    assert r["exit"]["estimate_matches"]


def test_signal_and_later_diagnostic(trade, contract):
    trade["exit_price"] = "1.29"
    trade["exit_diagnostics"] = json.dumps(
        {
            "observed_mark": 1.48,
            "observed_bid": 0.55,
            "observed_ask": 2.4,
            "configured_slippage": 0.05,
            "marketable_exit_estimate": 0.47,
        }
    )
    r = side_audit(trade, "exit", event(1.32), contract)
    assert r["paper_fill_matches"]
    assert r["diagnostic_paper_fill_counterfactual"] == 1.45
    assert r["diagnostic_minus_signal_points"] == pytest.approx(0.16)
    assert r["signal_observation_time"] is None
    assert r["signal_to_fill_latency_seconds"] is None
    assert r["diagnostic_collection_time"] is None
    assert r["telemetry_write_times"][0]["ts"] == "2026-10-13T18:00:00.5+00:00"


def test_missing_signal_is_not_reconstructed(trade, contract):
    r = side_audit(trade, "exit", [], contract)
    assert r["signal_mark"] is None
    assert r["paper_fill_matches"] is None
    assert r["estimate_matches"]


def test_entry_diagnostic_is_not_selection_signal(trade, contract):
    r = side_audit(trade, "entry", [], contract)
    assert r["signal_mark"] is None
    assert r["fill_input_mark"] == 7.25


def test_mark_fallback_194_hand_example(trade, contract):
    trade["exit_diagnostics"] = json.dumps(
        {
            "observed_mark": 3.92,
            "observed_bid": None,
            "observed_ask": None,
            "configured_slippage": 0.05,
            "marketable_exit_estimate": 3.84,
        }
    )
    r = side_audit(trade, "exit", [], contract)
    assert r["estimate_basis"] == "mark_fallback"
    assert r["estimate_recomputed"] == 3.84
    assert r["diagnostic_spread_points"] is None


def test_raw_negative_bid_and_proceeds_floor_are_separate(trade, contract):
    trade["exit_diagnostics"] = json.dumps(
        {
            "observed_mark": 0.1,
            "observed_bid": -0.2,
            "observed_ask": 0.4,
            "configured_slippage": 0.05,
            "marketable_exit_estimate": -0.28,
        }
    )
    r = side_audit(trade, "exit", [], contract)
    assert r["estimate_matches"]  # producer does NOT clip raw negative bids
    assert r["estimate_recomputed"] == -0.28
    assert r["historical_stress_price"] == 0
    assert r["raw_negative_bid"]
    assert r["stress_proceeds_floor_applied"]
    assert r["stress_floor_benefit_dollars"] == pytest.approx(28)


def test_positive_bid_can_still_floor_proceeds(trade, contract):
    trade["exit_diagnostics"] = json.dumps(
        {
            "observed_mark": 0.1,
            "observed_bid": 0.05,
            "observed_ask": 0.2,
            "configured_slippage": 0.05,
            "marketable_exit_estimate": -0.03,
        }
    )
    r = side_audit(trade, "exit", [], contract)
    assert not r["raw_negative_bid"]
    assert r["stress_proceeds_floor_applied"]
    assert r["stress_floor_benefit_dollars"] == pytest.approx(3)


def test_quantity_preserves_runtime_fee_convention(trade, contract):
    trade["quantity"] = "2"
    trade["entry_price"] = "7.30"  # 7.25 + 0.052 rounded, not quantity-normalized
    trade["exit_price"] = "2.75"
    trade["pnl"] = "-4.55"
    r = ledger_row(trade, event(), {}, {"identity_verified": True}, contract)
    assert r["entry"]["paper_fill_matches"]
    assert r["exit"]["paper_fill_matches"]
    assert r["recorded_paper_pnl_dollars"] == pytest.approx(-910)
    assert r["entry"]["embedded_commission_points"] == pytest.approx(0.052)


def test_cash_settlement_precision_and_no_close_fee(trade, contract):
    trade.update(
        exit_reason="cash_settled",
        exit_price="30.7966",
        entry_price="7.83",
        pnl="22.9666",
        exit_diagnostics="",
    )
    r = ledger_row(trade, [], {}, {"identity_verified": True}, contract)
    assert r["recorded_paper_pnl_dollars"] == pytest.approx(2296.66)
    assert r["exit"]["historical_stress_price"] == 30.7966
    assert r["exit"]["embedded_commission_points"] == 0
    assert r["exit"]["stress_drag_dollars"] == 0


def test_tolerances_reject_one_cent_of_price(trade, contract):
    trade["entry_price"] = "7.29"
    r = side_audit(trade, "entry", [], contract)
    assert r["paper_fill_matches"] is False


def test_cohort_derived_and_identity_checked(trade):
    inventory = [{"id": "91", "trade_date": trade["trade_date"], "exit_time": trade["exit_time"]}]
    coverage = [
        {
            "id": 91,
            "session": trade["trade_date"],
            "recorded_exit_time_utc": trade["exit_time"],
            "identity_verified": True,
        }
    ]
    assert cohort([trade], inventory, coverage, 0.000001) == {91}
    other = copy.deepcopy(trade)
    other.update(id="92", exit_reason="cash_settled")
    assert cohort([trade, other], inventory, coverage, 0.000001) == {91}
    with pytest.raises(ValueError, match="membership"):
        cohort([trade], [], coverage, 0.000001)
    with pytest.raises(ValueError, match="duplicate"):
        cohort([trade, trade], inventory, coverage, 0.000001)
    inventory[0]["exit_time"] = "2026-10-13T18:00:00.123458+00:00"
    with pytest.raises(ValueError, match="time mismatch"):
        cohort([trade], inventory, coverage, 0.000001)
    with pytest.raises(ValueError, match="naive"):
        at("2026-10-13T18:00:00")


def test_overwrite_and_evidence_protection(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    with pytest.raises(ValueError, match="outside"):
        new_directory(evidence / "output", evidence)
    with pytest.raises(FileExistsError):
        new_directory(evidence)


@pytest.mark.skipif(
    not os.environ.get("NDX_EXECUTION_EVIDENCE"), reason="private local snapshot required"
)
def test_full_offline_audit(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("network access forbidden")

    monkeypatch.setattr(socket, "socket", no_network)
    real_run = subprocess.run

    def restricted_run(cmd, *args, **kwargs):
        assert cmd in (["git", "rev-parse", "HEAD"], ["git", "status", "--short"])
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", restricted_run)
    root = Path(os.environ["NDX_EXECUTION_EVIDENCE"])
    args = dict(
        evidence=root / "ndx-r0-20261014",
        manifest=BASE / "snapshot.json",
        supplement=root / "ndx-01-supplement-20261015",
        supplement_manifest=BASE / "supplement-manifest.json",
        inventory=root / "ndx-continuation-inventory-20261015",
        inventory_manifest=BASE / "continuation-inventory-manifest.json",
        runtime_source=root / "helios-ndx-source-20261015",
        runtime_manifest=BASE / "runtime-source-manifest.json",
        parent=ROOT / "reports/research/ndx-01-20261015/run-03",
        config=BASE / "ndx02-execution-final.json",
        source_lock=BASE / "ndx02-execution-source-lock-final.json",
        previous_run=ROOT / "reports/research/ndx-02-20261015/run-01",
        output=tmp_path / "run",
    )
    result = run(**args)
    assert result["discretionary"]["n"] == 17
    assert result["all_modern_context"]["n"] == 53
    assert result["discretionary"]["sides"]["exit"]["mark_fallback_ids"] == [194]
    with pytest.raises(FileExistsError):
        run(**args)
    broken = json.loads(args["config"].read_text())
    broken["parent_run_sha256"] = "invalid"
    write_json(tmp_path / "bad-config.json", broken)
    lock = json.loads(args["source_lock"].read_text())
    lock["config_sha256"] = digest(tmp_path / "bad-config.json")
    write_json(tmp_path / "bad-lock.json", lock)
    with pytest.raises(ValueError, match="parent run"):
        run(
            **(
                args
                | {
                    "config": tmp_path / "bad-config.json",
                    "source_lock": tmp_path / "bad-lock.json",
                }
            )
        )
