import datetime as dt
import json

import pytest
from run_trials import PARENT, ProfitManagementSettings, compare, replay, variants


@pytest.fixture
def config():
    with (PARENT / "raw/export.jsonl").open() as f:
        raw = json.loads(next(f))
    return ProfitManagementSettings(**raw["effective"]["profit_management"])


def trade():
    return dict(entry_price="2", quantity=1, entry_time="2026-08-03T14:00:00+00:00",
                trade_date="2026-08-03", exit_reason="drawdown_morning", exit_price="1")


def points(observations):
    start = dt.datetime(2026, 8, 3, 14, tzinfo=dt.timezone.utc)
    return [dict(time=start + dt.timedelta(seconds=seconds), mark=value,
                 bid=value - 0.2, ask=value + 0.2) for seconds, value in observations]


def test_late_morning_only_and_configuration_isolation(config):
    configs = variants(config)
    assert config.regimes["late_morning"].drawdown_threshold == 0.9
    assert not config.use_absolute_loss_stop
    cfg, _ = configs["trail_60"]
    assert cfg.regimes["morning"] == config.regimes["morning"]
    assert cfg.regimes["afternoon"] == config.regimes["afternoon"]
    path = points([(0, 2), (5400, 4), (5405, 1.5)])
    assert replay(trade(), path, config, 0.026)["status"] == "censored_no_exit"
    result = replay(trade(), path, cfg, 0.026)
    assert result["reason"] == "drawdown_late_morning"
    assert result["pnl"] == -53


def test_stop_applies_when_never_profitable(config):
    path = points([(0, 1.8), (5, 0.9)])
    assert replay(trade(), path, config, 0.026)["status"] == "censored_no_exit"
    cfg, _ = variants(config)["stop_50"]
    result = replay(trade(), path, cfg, 0.026, confirmation_seconds=5)
    assert result["reason"] == "absolute_loss_stop"
    assert result["exit_price"] == 0.87
    assert result["pnl"] == -113  # observed fill, never the 50% threshold


@pytest.mark.parametrize("seconds", [2, 5, 10])
def test_confirmation_uses_elapsed_time_and_observed_fill(config, seconds):
    path = points([(0, 2), (1, 4), (2, 1.5), (2 + seconds, 1.4)])
    result = replay(trade(), path, config, 0.026, confirmation_seconds=seconds)
    assert result["exit_price"] == 1.37
    assert result["signal_time"] == path[-1]["time"].isoformat()


def test_recovery_resets_confirmation(config):
    path = points([(0, 2), (1, 4), (2, 1.5), (4, 2), (7, 1.5), (10, 1.4)])
    assert replay(trade(), path, config, 0.026, confirmation_seconds=5)[
        "status"] == "censored_no_exit"


def test_gap_resets_confirmation(config):
    path = points([(0, 2), (1, 4), (2, 1.5), (20, 1.4)])
    assert replay(trade(), path, config, 0.026, confirmation_seconds=5)[
        "status"] == "censored_no_exit"


def test_regime_change_resets_confirmation(config):
    path = points([(0, 2), (1, 4), (5398, 0.3), (5403, 0.3)])
    assert replay(trade(), path, config, 0.026, confirmation_seconds=5)[
        "status"] == "censored_no_exit"


def test_confirmation_does_not_delay_hard_end_of_day(config):
    config.exit_before_close_minutes = 5
    path = points([(0, 2), (21300, 1)])
    result = replay(trade(), path, config, 0.026, confirmation_seconds=10)
    assert result["reason"] == "end_of_day"


def test_confirmation_missing_followup_is_censored(config):
    path = points([(0, 2), (1, 4), (2, 1.5)])
    assert replay(trade(), path, config, 0.026)["status"] == "exit"
    assert replay(trade(), path, config, 0.026, confirmation_seconds=5)[
        "status"] == "censored_no_exit"


def test_latency_after_confirmation_requires_another_quote(config):
    path = points([(0, 2), (1, 4), (2, 1.5), (7, 1.4)])
    stress = "next_quote_halfspread_005"
    assert replay(trade(), path, config, 0.026, stress, 5)[
        "status"] == "censored_fill_latency"
    path += points([(8, 1.2)])
    result = replay(trade(), path, config, 0.026, stress, 5)
    assert result["exit_price"] == 1.02
    assert result["pnl"] == -98


def test_settlement_is_conditional_not_last_quote_fill(config):
    t = trade()
    t.update(exit_reason="cash_settled", exit_price="3")
    assert replay(t, points([(0, 2)]), config, 0.026)["status"] == "censored_no_exit"
    result = replay(t, points([(0, 2), (21599, 3)]), config, 0.026)
    assert result["status"] == "settlement"
    assert result["pnl"] == 100  # no second exit commission on settlement


def test_pairing_never_presents_missing_winner_as_zero():
    baseline = [dict(id=1, pnl=100, minutes=1, exit_drag_dollars=0,
                     exit_time="2026-08-03T14:00:00+00:00")]
    candidate = [dict(id=1, status="censored_no_exit")]
    result = compare(baseline, candidate)
    assert result["paired_count"] == 0
    assert not result["complete"]
    assert result["candidate_unresolved_ids"] == [1]
    assert result["same_id_top5_retention"] is None


def test_frozen_baseline_matches_original_replay(config):
    from replay import replay as original

    paths = [points([(0, 2), (1, 4), (2, 1.5)]), points([(0, 1.8), (5, 0.9)])]
    for path in paths:
        for stress in ("mark", "quarter_halfspread_005", "halfspread_005", "crossed_010",
                       "next_quote_halfspread_005"):
            assert replay(trade(), path, config, 0.026, stress) == original(
                trade(), path, config, 0.026, stress)
