import datetime as dt
import importlib.util
import math
from pathlib import Path

from butterfly_guy.reports.realized_vs_implied import (
    SessionMove,
    atm_straddle,
    format_message,
    summarize,
)

D = dt.date(2026, 9, 21)


def move(close, gap_sign=1, straddle=20.0, spot=7000.0, day=D):
    return SessionMove(date=day, spot_10=spot, straddle=straddle, close=close, gap_sign=gap_sign)


def test_z_uses_125x_straddle_and_landing_is_gap_directional():
    up = move(7040.0)  # +40 pts on sigma 25 -> z = 1.6
    assert math.isclose(up.z, 1.6)
    assert up.landed is True
    assert move(6960.0).landed is False  # same size, against the gap
    assert move(6960.0, gap_sign=-1).landed is True
    assert move(7010.0).landed is False  # z = 0.4, short of the tent
    assert move(None).z is None and move(None).landed is None


def test_summarize_known_answer_and_skips_pending_closes():
    s = summarize([move(7025.0), move(6975.0), move(None)])  # z = +1, -1
    assert s.sessions == 2
    assert math.isclose(s.rms_z, 1.0)
    assert math.isclose(s.mean_abs_z, 1.0)
    assert s.share_over_1sd == 0.0
    assert math.isclose(s.straddle_pnl_mean, 5.0)  # |25| - 20
    assert summarize([move(None)]).rms_z is None


def test_atm_straddle_needs_both_sides_at_nearest_strike():
    rows = [(7000.0, "CALL", 10.0), (7000.0, "PUT", 11.0), (7005.0, "CALL", 8.0)]
    assert atm_straddle(rows, 7001.0) == 21.0
    assert atm_straddle(rows, 7004.0) is None  # nearest strike 7005 lacks a put
    assert atm_straddle([], 7000.0) is None


def test_format_message_fits_discord_and_marks_pending():
    week = [move(7040.0, day=D), move(None, day=D + dt.timedelta(days=1))]
    text = format_message(week_start=D, week_end=D + dt.timedelta(days=4), week=week,
                          cohort=week, cohort_start=D, trailing=week[:1])
    assert "pending close" in text
    assert "Diagnostic only" in text
    assert len(text) < 2000


def _tool():
    path = Path(__file__).parent.parent / "tools" / "send_realized_vs_implied.py"
    spec = importlib.util.spec_from_file_location("send_rvi", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_review_week_is_last_completed_week():
    review_week = _tool().review_week
    assert review_week(dt.date(2026, 9, 26)) == (dt.date(2026, 9, 21), dt.date(2026, 9, 25))
    assert review_week(dt.date(2026, 9, 25)) == (dt.date(2026, 9, 14), dt.date(2026, 9, 18))
    assert review_week(dt.date(2026, 9, 28)) == (dt.date(2026, 9, 21), dt.date(2026, 9, 25))
