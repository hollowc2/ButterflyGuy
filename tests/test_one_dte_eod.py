"""Independent accounting/timing fixtures for overnight research only."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location(
    "one_dte_eod", Path(__file__).resolve().parents[1] / "tools/research_studies/one_dte_eod.py"
)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


def test_late_decision_has_strictly_later_entry_and_tie_rounding():
    assert s.ts("2023-01-03", "15:46") > s.ts("2023-01-03", "15:45")
    assert s.snap(4002.5) == 4000
    assert s.snap(4002.51) == 4005


def test_friday_monday_and_holiday_are_next_session_but_skips_fail():
    days = ["2023-05-26", "2023-05-30", "2023-05-31"]
    assert s.next_session("2023-05-26", "2023-05-30", days)
    assert not s.next_session("2023-05-26", "2023-05-31", days)
    assert not s.allowed("2024-07-01")
    assert s.allowed("2024-06-28")


def test_signed_payable_exit_is_preserved_and_unresolved_is_missing():
    # Pay $300 opening, $20 to close, $5.20 fees and $10 stress.
    assert s.cashflow(3, -0.2, settlement=False) == pytest.approx(-335.2)
    assert s.cashflow(3, None, settlement=False) is None
    # Center settlement receives $2,000, pays $300 entry + $2.60 fee + $5 stress.
    assert s.cashflow(3, s.payoff(4000, 4000, 20), settlement=True) == pytest.approx(1692.4)
    assert s.payoff(4020, 4000, 20) == 0


def test_component_prices_use_correct_sides_sizes_and_frozen_strikes():
    q = pd.DataFrame(
        [
            {
                "right": "CALL",
                "strike": 3980.0,
                "bid": 23.0,
                "ask": 24.0,
                "bid_size": 1,
                "ask_size": 1,
            },
            {
                "right": "CALL",
                "strike": 4000.0,
                "bid": 12.0,
                "ask": 13.0,
                "bid_size": 2,
                "ask_size": 2,
            },
            {
                "right": "CALL",
                "strike": 4020.0,
                "bid": 4.0,
                "ask": 5.0,
                "bid_size": 1,
                "ask_size": 1,
            },
        ]
    ).set_index(["right", "strike"])
    assert s.fly(q, 4000, 20, entry=True)["price"] == 5
    assert s.fly(q, 4000, 20, entry=False)["price"] == 1
    q.loc[("CALL", 4000.0), "bid_size"] = 1
    assert s.fly(q, 4000, 20, entry=True) is None
    assert s.fly(q, 4000, 20, entry=False)["price"] == 1


def test_exact_snapshot_does_not_backfill_later_or_protected(tmp_path):
    f = pd.DataFrame(
        [
            dict(
                symbol="SPXW",
                expiration="2023-01-04",
                strike=4000.0,
                right="CALL",
                timestamp=s.ts("2023-01-03", "15:47"),
                bid=1.0,
                ask=2.0,
                bid_size=1,
                ask_size=1,
            )
        ]
    )
    path = tmp_path / "test.parquet"
    f.to_parquet(path)
    snaps, _ = s.snapshots(path, "2023-01-03", "2023-01-04", ("15:46",))
    assert snaps["15:46"].empty
    with pytest.raises(ValueError, match="protected"):
        s.snapshots(path, "2024-06-28", "2024-07-01", ("15:46",))


def test_early_close_expiry_timestamp_and_zero_direction_exclusions(monkeypatch):
    def fake_snapshots(path, day, expiry, times):
        return dict.fromkeys(times, object()), {"path": str(path)}

    monkeypatch.setattr(s, "snapshots", fake_snapshots)
    monkeypatch.setattr(
        s, "proxy", lambda q: {"forward": 4000.0, "straddle": 30.0, "pairs": 5, "dispersion": 0.1}
    )
    monkeypatch.setattr(s, "fly", lambda *args, **kwargs: {"price": 4.0, "mark": 3.0, "legs": []})
    rows, _, _ = s.session_job(("2023-11-22", "2023-11-24", "development", 4000.0, False, "13:00"))
    neutral = [r for r in rows if r["signal"] == "neutral"]
    directional = [r for r in rows if r["signal"] != "neutral"]
    assert all(r["status"] == "no_direction_signal" for r in directional)
    settlement = [r for r in neutral if r["exit"] == "settlement"]
    assert all(r["exit_time"] == "2023-11-24T13:00:00-05:00" for r in settlement)
    assert all(r["status"] == "completed" for r in settlement)
