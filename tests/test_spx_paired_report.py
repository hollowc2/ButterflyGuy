from __future__ import annotations

import datetime as dt
import json

from butterfly_guy.reports.spx_paired import pair_report, render_markdown, session_window

DAY = dt.date(2026, 11, 20)
UTC = dt.timezone.utc


def _trade(trade_id, *, center=7440.0, width=20, entry=2.0, mark=1.85, exit_price=1.3,
           exit_mark=1.65, exit_minute=23, reason="drawdown_afternoon", paper=False):
    meta = {
        "per_width_bests": [
            {"cost": mark, "width": width, "center": center, "reward_risk": 9.81},
            {"cost": 3.9, "width": 40, "center": 7400.0, "reward_risk": 9.26},
        ],
        "exit_mark_at_signal": exit_mark,
        "vix": 21.07,
    }
    if paper:
        meta["paper_fill_model"] = "mark_v1"
    return {
        "id": trade_id,
        "status": "CLOSED",
        "entry_time": dt.datetime(2026, 11, 20, 15, 0, 15, tzinfo=UTC),
        "direction": "PUT",
        "lower_strike": center - width,
        "center_strike": center,
        "upper_strike": center + width,
        "wing_width": width,
        "entry_price": entry,
        "exit_time": dt.datetime(2026, 11, 20, 20, exit_minute, tzinfo=UTC),
        "exit_price": exit_price,
        "exit_reason": reason,
        "pnl": exit_price - entry,
        "quantity": 1,
        "metadata": json.dumps(meta),
    }


def test_same_fly_attributes_pnl_to_fills_and_path():
    paper = _trade(418, entry=1.85, exit_price=1.65, paper=True)
    live = _trade(100_000)

    report = pair_report(DAY, [paper], [live], [], [])

    assert report["paper"][0]["entry_vs_mark"] == 0.0
    assert report["live"][0]["entry_vs_mark"] == 0.15
    assert report["live"][0]["exit_vs_mark"] == -0.35
    assert report["live"][0]["entry_time_pt"] == "07:00:15"
    assert report["pnl_attribution"] == {
        "live_minus_paper_usd": -50.0,
        "entry_fill_usd": -15.0,
        "exit_fill_usd": -35.0,
        "path_and_timing_usd": 0.0,
    }
    assert report["flags"] == []


def test_different_fly_exit_and_timing_are_flagged():
    paper = _trade(418, center=7400.0, width=40, mark=3.9, entry=3.9, exit_price=3.0,
                   exit_mark=3.0, exit_minute=0, reason="cash_settled", paper=True)
    live = _trade(100_000)

    report = pair_report(DAY, [paper], [live], [], [])
    flags = "\n".join(report["flags"])

    assert "different fly" in flags
    assert "different exit: paper cash_settled vs live drawdown_afternoon" in flags
    assert "exit time gap +23.0 min" in flags
    assert set(report["pnl_attribution"]) == {"live_minus_paper_usd"}  # no fill split
    assert "Candidates at selection" in render_markdown(report)


def test_one_bot_without_a_trade_shows_its_last_entry_decisions():
    blocks = [{
        "ts": dt.datetime(2026, 11, 20, 15, 44, tzinfo=UTC),
        "event_type": "entry_blocked",
        "data": json.dumps({"reason": "chain_snapshot_stale"}),
    }]

    report = pair_report(DAY, [_trade(418, paper=True)], [], [], blocks)

    assert report["flags"] == ["only paper traded"]
    assert report["live_no_trade_reasons"] == [
        {"time_pt": "07:44:00", "event": "entry_blocked", "reason": "chain_snapshot_stale"}
    ]
    assert "live did not trade:** 07:44:00 entry_blocked chain_snapshot_stale" in (
        render_markdown(report)
    )


def test_paper_row_in_the_live_db_is_flagged():
    report = pair_report(DAY, [_trade(418, paper=True)], [_trade(5, paper=True)], [], [])
    assert report["flags"][0].startswith("live DB holds a paper trade")


def test_session_window_is_the_eastern_calendar_day():
    start, end = session_window(DAY)
    assert start.isoformat() == "2026-11-20T00:00:00-05:00"
    assert end - start == dt.timedelta(days=1)
