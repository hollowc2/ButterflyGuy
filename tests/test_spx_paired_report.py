from __future__ import annotations

import datetime as dt
import json

from butterfly_guy.reports.spx_paired import (
    intent_order_marks,
    pair_report,
    render_markdown,
    session_window,
)

DAY = dt.date(2026, 11, 20)
UTC = dt.timezone.utc


def _trade(trade_id, *, center=7440.0, width=20, entry=2.0, mark=1.85, exit_price=1.3,
           exit_mark=1.65, exit_minute=23, reason="drawdown_afternoon", paper=False,
           chain_read="2026-11-20T10:00:12.30-05:00", spot=7420.5, vix=21.07,
           order_mark=None, exit_order_mark=None):
    # Order-time marks default to the selection/signal marks (no drift).
    order_mark = mark if order_mark is None else order_mark
    exit_order_mark = exit_mark if exit_order_mark is None else exit_order_mark
    meta = {
        "per_width_bests": [
            {"cost": mark, "width": width, "center": center, "reward_risk": 9.81},
            {"cost": 3.9, "width": 40, "center": 7400.0, "reward_risk": 9.26},
        ],
        "exit_mark_at_signal": exit_mark,
        "vix": vix,
        "vix_timestamp": "2026-11-20T15:00:00.013267+00:00",
        "selected_chain_snapshot_time": chain_read,
        "entry_spot": spot,
    }
    intent_marks = {}
    if paper:
        meta["paper_fill_model"] = "mark_v1"
        meta["entry_execution_diagnostics"] = {"observed_mark": order_mark}
        if reason != "cash_settled":
            meta["exit_execution_diagnostics"] = {"observed_mark": exit_order_mark}
    else:
        intent_marks = {"ENTRY": order_mark, "EXIT": exit_order_mark}
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
        "intent_order_marks": intent_marks,
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


def test_live_fill_check_prices_lives_own_fly_at_its_marks():
    live = _trade(100_000)  # entry 2.00 vs mark 1.85; exit 1.30 vs mark 1.65

    report = pair_report(DAY, [], [live], [], [])

    assert report["live_fill_check"] == {
        "order_mark_pnl_usd": -20.0,
        "actual_pnl_usd": -70.0,
        "fill_cost_usd": -50.0,
        "entry_fill_usd": -15.0,
        "exit_fill_usd": -35.0,
    }
    assert "Live fill check" in render_markdown(report)


def test_live_fill_check_needs_both_order_marks():
    live = _trade(100_000)
    live["intent_order_marks"] = {"ENTRY": 1.85}  # no recorded exit quote

    assert "live_fill_check" not in pair_report(DAY, [], [live], [], [])


def test_paper_fees_are_backed_out_so_both_sides_are_pre_fee():
    # Paper books 4 x $1.15 = $0.046 per side into its fills: 1.85 + 0.046 -> 1.90 entry,
    # 1.65 - 0.046 -> 1.60 exit.
    paper = _trade(418, entry=1.90, exit_price=1.60, paper=True)
    live = _trade(100_000)

    report = pair_report(DAY, [paper], [live], [], [], paper_commission_per_contract=1.15)
    p = report["paper"][0]

    assert p["entry_fill"] == 1.854 and p["exit_fill"] == 1.646
    assert p["pnl_usd"] == -20.8
    assert p["paper_fees_backed_out_usd"] == 9.2
    assert report["live"][0]["pnl_usd"] == -70.0  # live rows are never adjusted
    assert report["live"][0]["paper_fees_backed_out_usd"] == 0.0
    assert report["pnl_attribution"]["live_minus_paper_usd"] == -49.2


def test_cash_settled_paper_trade_backs_out_only_the_entry_fee():
    paper = _trade(418, entry=1.90, exit_price=0.0, exit_mark=0.0, reason="cash_settled",
                   paper=True)

    p = pair_report(DAY, [paper], [], [], [], paper_commission_per_contract=1.15)["paper"][0]

    assert p["exit_fill"] == 0.0
    assert p["paper_fees_backed_out_usd"] == 4.6
    assert p["pnl_usd"] == -185.4


def test_fill_check_uses_order_time_marks_and_reports_drift_apart():
    # Selection mark 1.85 but 1.95 at the order: 0.10 is drift, only 0.05 is fill cost.
    # Exit signal mark 1.65, 1.60 at the order, filled 1.30.
    live = _trade(100_000, order_mark=1.95, exit_order_mark=1.60)

    report = pair_report(DAY, [], [live], [], [])
    q = report["live"][0]

    assert q["entry_drift"] == 0.1 and q["entry_vs_order_mark"] == 0.05
    assert q["exit_drift"] == -0.05 and q["exit_vs_order_mark"] == -0.3
    assert report["live_fill_check"] == {
        "order_mark_pnl_usd": -35.0,
        "actual_pnl_usd": -70.0,
        "fill_cost_usd": -35.0,
        "entry_fill_usd": -5.0,
        "exit_fill_usd": -30.0,
    }


def test_paper_order_marks_come_from_its_execution_diagnostics():
    # 2026-11-18 trade 420: selection 3.45, order-time mark 3.63, booked 3.68 with fees.
    paper = _trade(420, entry=3.68, mark=3.45, order_mark=3.63, paper=True)

    p = pair_report(DAY, [paper], [], [], [], paper_commission_per_contract=1.15)["paper"][0]

    assert p["entry_drift"] == 0.18
    assert abs(p["entry_vs_order_mark"]) < 0.005  # only cent rounding of the booked fee


def test_cash_settled_exit_uses_the_settlement_value_as_its_order_mark():
    live = _trade(100_000, exit_price=0.0, exit_mark=0.0, reason="cash_settled")
    live["intent_order_marks"] = {"ENTRY": 1.85}

    report = pair_report(DAY, [], [live], [], [])

    assert report["live"][0]["exit_order_mark"] == 0.0
    assert report["live_fill_check"]["exit_fill_usd"] == 0.0


def test_intent_order_marks_reads_before_submit_quotes():
    rows = [
        {"side": "ENTRY", "observations": json.dumps([
            {"phase": "before_submit", "quote": {"spread": {"mark": 2.1000000000000014}}},
            {"phase": "fill_detected", "quote": {"spread": {"mark": 1.95}}},
        ])},
        {"side": "EXIT", "observations": [{"phase": "before_submit", "quote": None}]},
    ]

    assert intent_order_marks(rows) == {"ENTRY": 2.1, "EXIT": None}


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
    assert report["live_fill_check"]["fill_cost_usd"] == -50.0  # still isolated
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


def test_entry_inputs_read_seconds_apart_are_flagged_as_timing():
    # 2026-11-18 rehearsal: the 15 s entry loops ran 4.9 s apart and picked 7455 vs 7450.
    paper = _trade(420, center=7455.0, paper=True, chain_read="2026-11-18T10:00:07.426487-05:00",
                   spot=7360.16, vix=24.49)
    live = _trade(100_000, center=7450.0, chain_read="2026-11-18T10:00:12.316712-05:00",
                  spot=7358.14, vix=24.33)

    report = pair_report(DAY, [paper], [live], [], [])

    assert report["entry_inputs_live_minus_paper"] == {
        "chain_read_gap_s": 4.9, "spot_diff": -2.02, "vix_diff": -0.16,
    }
    assert any(f.startswith("entry inputs read +4.9 s apart") for f in report["flags"])
    markdown = render_markdown(report)
    assert "| entry chain read | 07:00:07.4 | 07:00:12.3 |" in markdown
    assert "| VIX as of | 07:00:00.0 | 07:00:00.0 |" in markdown


def test_entry_inputs_read_together_are_not_flagged():
    report = pair_report(DAY, [_trade(418, paper=True)], [_trade(100_000)], [], [])

    assert report["entry_inputs_live_minus_paper"]["chain_read_gap_s"] == 0.0
    assert report["flags"] == []


def test_monitor_polls_and_rate_limits_are_shown_per_bot():
    paper, live = _trade(418, paper=True), _trade(100_000)
    paper.update(monitor_polls=215, monitor_median_gap_s=2.64)
    live.update(monitor_polls=224, monitor_median_gap_s=2.61)

    report = pair_report(DAY, [paper], [live], [], [], rate_limited={"paper": 6, "live": 8})
    markdown = render_markdown(report)

    assert "| monitor polls | 215 | 224 |" in markdown
    assert "| median poll gap s | 2.64 | 2.61 |" in markdown
    assert "| Schwab 429s | 6 | 8 |" in markdown


def test_rate_limit_row_is_omitted_when_counts_are_unknown():
    report = pair_report(DAY, [_trade(418, paper=True)], [_trade(100_000)], [], [])
    assert "Schwab 429s" not in render_markdown(report)
