import datetime as dt
import json

import pytest
from run_all_history import (
    PARENT,
    ProfitManagementSettings,
    all_stresses,
    assert_prior_result,
    ledger_parity,
    paired_comparison,
    replay,
    select_sources,
    variants,
)


def trade():
    return dict(id=1, entry_price="2", quantity=1,
                entry_time="2026-08-03T14:00:00+00:00", trade_date="2026-08-03",
                exit_time="2026-08-03T14:00:07+00:00", exit_reason="drawdown_morning",
                exit_price="1.37", pnl="-0.63", fill_model="mark_v1")


def points(values):
    start = dt.datetime(2026, 8, 3, 14, tzinfo=dt.timezone.utc)
    return [dict(time=start + dt.timedelta(seconds=seconds), mark=value,
                 bid=value - 0.2, ask=value + 0.2) for seconds, value in values]


@pytest.mark.parametrize("observations", [
    [(0, 2), (1, 4), (2, 1.5), (7, 1.4), (8, 1.2)],
    [(0, 2), (1, 4), (2, 1.5)],
    [(0, 1.8), (5, 0.9)],
    [],
    [(0, 2), (21599, 3)],
])
def test_all_scenarios_equal_original_replays(observations):
    with (PARENT / "raw/export.jsonl").open() as f:
        raw = json.loads(next(f))
    cfg = ProfitManagementSettings(**raw["effective"]["profit_management"])
    t = trade()
    if observations and observations[-1][0] == 21599:
        t.update(exit_reason="cash_settled", exit_price="3")
    path = points(observations)
    for config, seconds in variants(cfg).values():
        actual = all_stresses(t, path, config, 0.026, seconds)
        for stress, result in actual.items():
            assert result == replay(t, path, config, 0.026, stress, seconds)


def test_source_choice_keeps_unusable_monitoring_and_never_looks_at_outcome():
    mapping = select_sources([dict(trade_id=1, rows=[{"invalid": True}]),
                              dict(trade_id=2, rows=[])])
    assert mapping == {1: "monitor", 2: "collector"}


def test_parity_requires_price_reason_and_time():
    result = dict(status="exit", pnl=-63, reason="drawdown_morning",
                  exit_time="2026-08-03T14:00:07+00:00")
    assert ledger_parity(trade(), result)["ledger_match"]
    for changes in (dict(pnl=-70), dict(reason="absolute_loss_stop"),
                    dict(exit_time="2026-08-03T14:00:30+00:00")):
        assert not ledger_parity(trade(), {**result, **changes})["ledger_match"]
    missing = ledger_parity(trade(), {"status": "censored_no_exit"})
    assert not missing["ledger_match"] and not missing["resolved"]


def test_pair_metrics_and_fee_sensitivity_use_same_resolved_ids():
    common = dict(minutes=1, exit_drag_dollars=0, exit_time="2026-08-03T14:00:00+00:00")
    baseline = [dict(id=1, fill_model="legacy", pnl=-50, **common),
                dict(id=2, fill_model="mark_v1", pnl=500, **common),
                dict(id=3, fill_model="legacy", status="censored_no_exit")]
    candidate = [dict(id=1, fill_model="legacy", pnl=-20, **common),
                 dict(id=2, fill_model="mark_v1", status="censored_no_exit"),
                 dict(id=3, fill_model="legacy", pnl=100, **common)]
    parity = {i: dict(ledger_match=i == 2, material_pnl_error=i == 1) for i in (1, 2, 3)}
    result = paired_comparison(baseline, candidate, parity)
    assert result["paired_ids"] == [1]
    assert result["excluded_ids"] == [2, 3]
    assert result["baseline_unresolved_ids"] == [3]
    assert result["candidate_unresolved_ids"] == [2]
    assert result["paired_delta_pnl"] == 30
    assert result["paired_baseline_ledger_matches"] == 0
    assert result["paired_baseline_material_pnl_errors"] == 1
    assert result["paired_candidate"]["net_extra_legacy_entry_fee"] == -22.6
    assert result["same_id_top5_retention"] is None


def test_regression_checks_reject_changed_outcomes():
    assert_prior_result(dict(status="exit", pnl=1.25), dict(status="exit", pnl="1.25"))
    with pytest.raises(AssertionError):
        assert_prior_result(dict(status="exit", pnl=1.25), dict(status="exit", pnl="1.26"))
