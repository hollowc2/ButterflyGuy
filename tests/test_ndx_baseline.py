"""Independent accounting/timing fixtures for the offline NDX study, not strategy tests."""

import csv
import datetime as dt
import json
import socket
import subprocess
from dataclasses import replace

import pytest

from butterfly_guy.core.config import ProfitManagementSettings
from butterfly_guy.research.ndx_baseline import (
    Observation,
    coverage,
    event_accounting,
    exit_prices,
    fill_after,
    identity,
    normalize,
    pnl,
    recorded_stress,
    replay,
    run,
    settlement_payoff,
)
from butterfly_guy.research.ndx_evidence import digest, new_directory, verify

AT = dt.datetime(2026, 8, 6, 14, tzinfo=dt.timezone.utc)
CONTRACT = {
    "commission_points_per_side": 0.026,
    "slippage_points": 0.05,
    "continuity_seconds": 30,
    "fill_window_seconds": 30,
    "first_delay_seconds": 30,
    "tail_seconds": 120,
    "mark_tolerance_points": 0.00011,
    "dollar_tolerance": 0.01,
    "timestamp_tolerance_seconds": 0.000001,
}


def obs(seconds, mark, bid=None):
    return Observation(
        AT + dt.timedelta(seconds=seconds),
        mark,
        mark if bid is None else bid,
        mark + 0.2,
        0.2,
        0.1,
        mark,
    )


def trade(**changes):
    return {
        "id": "1",
        "trade_date": "2026-08-06",
        "direction": "PUT",
        "quantity": "1",
        "entry_price": "1.03",
        "entry_time": AT.isoformat(),
        "exit_time": (AT + dt.timedelta(seconds=25)).isoformat(),
        "exit_price": ".72",
        "pnl": "-.31",
        "exit_reason": "drawdown_morning",
        "fill_model": "mark_v1",
        "entry_diagnostics": '{"marketable_entry_estimate":1.28}',
        "exit_diagnostics": "",
        "entry_strategy": "{}",
        "settlement_source": "",
        "settlement_spot": "",
        "lower_strike": "100",
        "center_strike": "110",
        "upper_strike": "120",
        **changes,
    }


@pytest.fixture
def settings():
    return ProfitManagementSettings(
        regimes={
            key: {
                "start_minutes_after_open": start,
                "end_minutes_after_open": end,
                "drawdown_threshold": 0.5,
                "confirmation_polls": 2,
                "min_peak_profit_ratio": 1.5,
            }
            for key, start, end in [
                ("morning", 0, 120),
                ("late_morning", 120, 240),
                ("afternoon", 240, 390),
            ]
        }
    )


def test_accounting_is_embedded_and_rounded_once():
    # Broker paper diagnostic: mark 2.80 closes at 2.77; entry 7.28 is already paid.
    prices = exit_prices(2.8, 1.1, CONTRACT)
    assert prices["paper"] == 2.77
    assert prices["stress"] == 1.02
    assert pnl(prices["paper"], 7.28, 1) == -451
    assert pnl(prices["stress"], 11.18, 1) == -1016
    # Quarter-cent settlement precision survives; no closing commission.
    assert pnl(96.0246, 7.88, 1) == 8814.46


def test_historical_negative_credit_floor_is_counted():
    prices = exit_prices(0, -0.5, CONTRACT)
    assert prices["stress"] == 0
    assert prices["stress_floor_applied"]
    assert prices["stress_floor_points"] == 0.08
    value, floored = recorded_stress(trade(exit_diagnostics='{"marketable_exit_estimate":-0.57}'))
    assert value == -128
    assert floored


def test_next_observation_fill_differs_from_signal(settings):
    path = [obs(0, 1), obs(5, 3), obs(10, 1), obs(15, 0.9), obs(20, 0.8, 0.7)]
    r = replay(trade(), path, settings, CONTRACT)
    assert r["signal_time"] == path[3].ts.isoformat()
    assert r["exit_time"] == path[4].ts.isoformat()
    assert r["pnl"] == -26  # 0.77 received - 1.03 already paid
    assert r["executable_pnl"] == -66  # .62 received - 1.28 already paid


def test_confirmations_reset_across_gap(settings):
    path = [obs(0, 1), obs(5, 3), obs(10, 1), obs(50, 0.9), obs(55, 0.8)]
    t = trade(
        exit_time=(AT + dt.timedelta(seconds=60)).isoformat(),
        exit_diagnostics='{"observed_mark":0.75,"observed_bid":0.5}',
    )
    r = replay(t, path, settings, CONTRACT)
    assert r["signal_time"] == path[4].ts.isoformat()
    assert r["terminal_exit_observation"]
    assert r["pnl"] == -31


def test_terminal_fill_diagnostic_and_expired_window():
    path = [obs(0, 1)]
    t = trade(exit_diagnostics='{"observed_mark":0.75,"observed_bid":0.5}')
    assert fill_after(path, 0, t, 30)[3]
    assert fill_after(path, 0, t, 20) is None
    assert fill_after(path, 0, trade(), 30) is None
    # Never jump over a long intermediate gap to use a later terminal diagnostic.
    assert fill_after(path + [obs(40, 0.8)], 0, t, 30) is None


def test_missing_continuation_is_null_and_never_a_settlement_fallback(settings):
    t = trade(settlement_spot="110", exit_price="10")
    r = replay(t, [obs(0, 1), obs(5, 0.8)], settings, CONTRACT)
    assert r["status"] == "censored_continuation"
    assert r["pnl"] is None
    assert r["executable_pnl"] is None
    assert replay(t, [], settings, CONTRACT)["status"] == "missing_observations"


def test_censored_fill_has_no_pnl(settings):
    path = [obs(0, 1), obs(5, 3), obs(10, 1), obs(15, 0.9)]
    r = replay(trade(), path, settings, CONTRACT)
    assert r["status"] == "censored_fill"
    assert r["pnl"] is None


def test_actual_settlement_preserves_precision_and_attribution(settings):
    t = trade(
        exit_reason="cash_settled",
        exit_time="2026-08-06T20:00:02+00:00",
        exit_price=".3456",
        settlement_source="schwab_final_regular_session_1m_close",
        settlement_spot="119.6544",
    )
    path = [obs(0, 1), obs(21550, 0.4)]
    r = replay(t, path, settings, CONTRACT)
    assert r["status"] == "settlement"
    assert r["pnl"] == -68.44
    assert settlement_payoff(t) == 0.3456
    c = coverage(t, path, {}, {}, CONTRACT, r)
    assert c["settlement_timestamp"] is None
    assert not c["official_settlement_eligible"]
    assert not c["freshness_verified"]
    # A missing spot cannot become zero or a recomputed settlement.
    assert settlement_payoff(trade()) is None
    assert replay(t, [obs(0, 1)], settings, CONTRACT)["status"] == "censored_continuation"


def test_contract_identity_checks_all_three_symbols():
    t = trade()
    extra = {
        "lower_symbol": "NDXP  260806P00100000",
        "center_symbol": "NDXP  260806P00110000",
        "upper_symbol": "NDXP  260806P00120000",
    }
    assert identity(t, extra) == {
        "option_root": "NDXP",
        "expiration": "2026-08-06",
        "identity_verified": True,
    }
    assert not identity(t, extra | {"upper_symbol": "NDX  260807P00120000"})["identity_verified"]
    assert identity(t, {})["option_root"] is None


def write_csv(path, data):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def test_incomplete_observations_never_become_zero_and_duplicates_fail(tmp_path):
    p = tmp_path / "paths.csv"
    a = {
        "trade_id": "1",
        "ts": AT.isoformat(),
        "legs": "2",
        "invalid_legs": "0",
        "raw_mark": "",
        "raw_bid": "",
        "raw_ask": "",
        "recorded_mark": "",
        "max_leg_spread_abs": ".5",
        "max_leg_spread_to_mark_ratio": ".1",
        "recorded_peak": "2",
    }
    b = a | {
        "ts": (AT + dt.timedelta(seconds=5)).isoformat(),
        "legs": "3",
        "raw_mark": "1",
        "raw_bid": ".8",
        "raw_ask": "1.2",
        "recorded_mark": "1",
    }
    write_csv(p, [a, b])
    paths, audit = normalize(p, 0.00011)
    assert len(paths[1]) == 1
    assert paths[1][0].mark == 1
    assert audit[1]["incomplete"] == 1
    write_csv(p, [b, b])
    with pytest.raises(ValueError, match="duplicate"):
        normalize(p, 0.00011)


def test_hash_verification_and_overwrite_refusal(tmp_path):
    raw = tmp_path / "snapshot"
    raw.mkdir()
    (raw / "x").write_text("evidence")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": {"x": digest(raw / "x")}}))
    verify(raw, manifest)
    (raw / "x").write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify(raw, manifest)
    with pytest.raises(ValueError, match="outside"):
        new_directory(raw / "run", raw)
    with pytest.raises(FileExistsError):
        new_directory(raw)


def test_offline_run_explicit_evidence_directory(tmp_path, monkeypatch, settings):
    import yaml

    raw = tmp_path / "evidence/raw"
    raw.mkdir(parents=True)
    t = trade()
    write_csv(raw / "trades.csv", [t])
    path = [obs(0, 1), obs(5, 3), obs(10, 1), obs(15, 0.9), obs(20, 0.8, 0.7)]
    write_csv(
        raw / "paths.csv",
        [
            {
                "trade_id": 1,
                "ts": o.ts.isoformat(),
                "legs": 3,
                "invalid_legs": 0,
                "raw_mark": o.mark,
                "raw_bid": o.bid,
                "raw_ask": o.ask,
                "recorded_mark": o.mark,
                "max_leg_spread_abs": 0.2,
                "max_leg_spread_to_mark_ratio": 0.1,
                "recorded_peak": 3,
            }
            for o in path
        ],
    )
    # Independently expected signal/fill/accounting, rather than invoking replay to build targets.
    write_csv(
        raw / "replay-trades.csv",
        [
            {
                "id": 1,
                "variant": "baseline",
                "status": "exit",
                "reason": "drawdown_morning",
                "pnl": -26,
                "executable_pnl": -66,
                "signal_time": path[3].ts.isoformat(),
                "exit_time": path[4].ts.isoformat(),
            }
        ],
    )
    (raw / "events.csv").write_text("ts,event_type,data\n")
    (raw / "metrics.json").write_text('{"replay":{"modern":{"common_ids":[1]}}}')
    (raw / "policy.yaml").write_text(yaml.safe_dump({"profit_management": settings.model_dump()}))
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"snapshot_id": "fixture", "files": {"raw/" + p.name: digest(p) for p in raw.iterdir()}}
        )
    )
    config = tmp_path / "contract.json"
    contract = CONTRACT | {
        "model": "NDX-R0-baseline-approximation-v1",
        "parent": "independent_fixture",
        "snapshot_manifest_sha256": digest(manifest),
        "source_sha256": {},
        "policy_file": "policy.yaml",
        "qualifications": [],
    }
    config.write_text(json.dumps(contract))

    def no_network(*a, **kw):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", no_network)
    original_run = subprocess.run

    def only_git(command, *a, **kw):
        assert command[0] == "git", "external network command forbidden"
        return original_run(command, *a, **kw)

    monkeypatch.setattr(subprocess, "run", only_git)
    out = tmp_path / "new-run"
    summary = run(raw.parent, manifest, config, out)
    assert summary["recorded_mark_v1"]["n"] == 1
    assert not summary["historical_reproduction_differences"]
    assert (out / "run.json").exists()
    with pytest.raises(FileExistsError):
        run(raw.parent, manifest, config, out)
    # A changed policy implementation must never silently reinterpret an old run.
    contract["source_sha256"] = {"pyproject.toml": "wrong"}
    config.write_text(json.dumps(contract))
    with pytest.raises(ValueError, match="source drift"):
        run(raw.parent, manifest, config, tmp_path / "drift")


def test_outside_lifecycle_quotes_and_unsupported_quantity(settings):
    with pytest.raises(ValueError, match="outside"):
        replay(trade(), [replace(obs(0, 1), ts=AT - dt.timedelta(seconds=1))], settings, CONTRACT)
    r = replay(trade(quantity="2"), [obs(0, 1)], settings, CONTRACT)
    assert r["status"] == "unsupported_historical_quantity"
    assert r["pnl"] is None


def test_signal_mark_and_separate_diagnostic_have_distinct_accounting():
    t = trade(exit_price="1.29")
    event = {
        "event_type": "trade_exited",
        "ts": AT.isoformat(),
        "data": json.dumps(
            {"trade_id": 1, "mark_at_signal": 1.32, "spread_mark": 1.48, "fill_price": 1.29}
        ),
    }
    r = event_accounting([t], [event], CONTRACT)[0]
    assert r["signal_based_fill"] == 1.29
    assert r["separately_fetched_spread_mark"] == 1.48
    assert r["accounting_difference_points"] == 0


def test_historical_recorded_settlement_can_have_a_final_tick_after_close(settings):
    t = trade(exit_reason="cash_settled", exit_time="2026-08-06T20:00:02+00:00", exit_price=".3456")
    r = replay(t, [obs(0, 1), obs(21601, 0.4)], settings, CONTRACT)
    assert r["status"] == "settlement"
    assert r["pnl"] == -68.44
    assert r["settlement_basis"] == "recorded_paper_proxy_unverified_XQC"


@pytest.mark.research_data
def test_named_snapshot_reproduction_without_network(tmp_path, monkeypatch):
    import os
    from pathlib import Path

    from butterfly_guy.research.ndx_baseline import ROOT

    evidence_dir = os.environ.get("NDX_EVIDENCE")
    supplement_dir = os.environ.get("NDX_SUPPLEMENT")
    if not evidence_dir or not supplement_dir:
        pytest.skip("set NDX_EVIDENCE and NDX_SUPPLEMENT to verified private snapshots")

    def forbidden_network(*args, **kwargs):
        raise AssertionError("offline reproduction attempted a network socket")

    monkeypatch.setattr(socket, "socket", forbidden_network)
    original_run = subprocess.run

    def only_local_git(command, *args, **kwargs):
        assert command[0] == "git", "offline reproduction launched an external command"
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", only_local_git)
    small = ROOT / "docs/research/ndx-strategy/evidence/2026-10-15"
    summary = run(
        Path(evidence_dir),
        small / "snapshot.json",
        small / "r0-reproduction-final.json",
        tmp_path / "offline-run",
        Path(supplement_dir),
        small / "supplement-manifest.json",
    )
    historic = json.loads((Path(evidence_dir) / "raw/metrics.json").read_text())
    description = json.loads((Path(evidence_dir) / "raw/descriptive.json").read_text())
    assert not summary["historical_reproduction_differences"]
    assert summary["recorded_mark_v1"]["pnl"] == historic["recorded"]["mark_v1"]["pnl"]
    assert summary["stored_marketable_stress"]["pnl"] == description["execution_stress"]["pnl"]
