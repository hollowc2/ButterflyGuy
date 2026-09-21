import datetime as dt

from replay import ROOT, ProfitManagementSettings, metrics, path_for, replay


def trade():
    return dict(
        entry_price="2",
        quantity=1,
        entry_time="2026-08-03T14:00:00+00:00",
        trade_date="2026-08-03",
        exit_reason="drawdown_morning",
        exit_price="1",
        lower_strike=100,
        center_strike=120,
        upper_strike=140,
        peak_value="9999",
    )


def settings(policy):
    return ProfitManagementSettings(
        strategy=policy,
        regimes={
            "morning": dict(
                start_minutes_after_open=0, end_minutes_after_open=120, drawdown_threshold=0.6
            )
        },
    )


def points(values):
    return [
        dict(
            time=dt.datetime(2026, 8, 3, 14, i, tzinfo=dt.timezone.utc),
            mark=v,
            bid=v - 0.2,
            ask=v + 0.2,
        )
        for i, v in enumerate(values)
    ]


def test_protector_locks_but_does_not_fill_at_floor_or_peak():
    p = points([2, 4.5, 2.1, 1.5])
    b = replay(trade(), p, settings("peakvaluetrailer"), 0.026)
    c = replay(trade(), p, settings("profitprotector"), 0.026)
    assert b["exit_price"] == 1.47
    assert c["exit_price"] == 2.07
    assert c["peak_replayed"] == 4.5
    assert c["reason"] == "profitprotector_profit_floor"


def test_commission_once_and_latency_uses_next_quote():
    p = points([2, 4.5, 2.1, 1.5])
    t = trade()
    t["entry_price"] = "2.03"
    r = replay(t, p, settings("profitprotector"), 0.026, "next_quote_halfspread_005")
    assert r["exit_price"] == 1.32
    assert r["pnl"] == -71


def test_no_signal_is_censored_not_last_quote_close():
    assert (
        replay(trade(), points([2, 2.5]), settings("peakvaluetrailer"), 0.026)["status"]
        == "censored_no_exit"
    )


def test_incomplete_or_duplicate_snapshot_not_forward_filled():
    q = dict(snapshot_time="2026-08-03T14:00:00+00:00", strike=100, bid=1, ask=2, mark=1.5)
    path, audit = path_for(trade(), [q, q])
    assert not path and audit["invalid_groups"] == 1


def test_drawdown_includes_zero_start_and_positive_winners_only():
    rows = [
        dict(pnl=x, minutes=1, exit_time=f"2026-08-03T14:0{i}:00+00:00")
        for i, x in enumerate([-100, 50, -80])
    ]
    m = metrics(rows)
    assert m["closed_trade_drawdown"] == 130
    assert m["net_excluding_top_5"] == -180


def test_all_mark_v1_baselines_reproduce_ledger():
    import json

    with (ROOT / "raw/export.jsonl").open() as f:
        baseline = json.loads(next(f))
        trades = json.loads(next(f))["rows"]
    trades = {t["id"]: t for t in trades if t["fill_model"] == "mark_v1"}
    cfg = ProfitManagementSettings(**baseline["effective"]["profit_management"])
    count = 0
    with (ROOT / "raw/monitor.jsonl").open() as f:
        for line in f:
            q = json.loads(line)
            if q["trade_id"] not in trades:
                continue
            t = trades[q["trade_id"]]
            path, _ = path_for(t, q["rows"])
            r = replay(t, path, cfg, 0.026)
            assert abs(r["pnl"] - float(t["pnl"]) * 100 * int(t["quantity"])) < 0.01
            assert r["reason"] == t["exit_reason"]
            count += 1
    assert count == 33
