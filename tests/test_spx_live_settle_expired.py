"""The operator settle tool for an expired live fly (replaces 11-19's settle_100000.py)."""
import datetime as dt
import runpy

import pytest

TOOL = runpy.run_path("tools/spx_live_settle_expired.py", run_name="spx_live_settle_expired")
plan_settlement, Refused = TOOL["plan_settlement"], TOOL["Refused"]

LOWER, CENTER, UPPER = (f"SPXW  261119C0{k}000" for k in (7435, 7475, 7515))


def trade_100000(**overrides):
    row = {
        "id": 100000, "status": "OPEN", "trade_date": dt.date(2026, 11, 19),
        "direction": "CALL", "lower_strike": 7435.0, "center_strike": 7475.0,
        "upper_strike": 7515.0, "entry_price": 3.75, "quantity": 1,
        "lower_symbol": LOWER, "center_symbol": CENTER, "upper_symbol": UPPER,
        "underlying": "SPX", "peak_value": 4.93,
    }
    return {**row, **overrides}


def tx(effect, amounts, net, time="2026-11-19T15:00:18+0000"):
    return {
        "activityId": 1, "time": time, "netAmount": net,
        "transferItems": [
            {"instrument": {"symbol": s}, "amount": a, "price": p, "positionEffect": effect}
            for s, a, p in amounts
        ],
    }


OPENING = tx("OPENING", [(LOWER, 1.0, 8.0), (CENTER, -2.0, 3.5), (UPPER, 1.0, 2.75)], -379.79)


def test_worthless_fly_before_schwab_posts_settles_at_zero_with_fees():
    value, pnl, meta = plan_settlement(trade_100000(), [OPENING], spx_close=7176.0)

    assert value == 0.0
    assert pnl == pytest.approx(-3.7979)  # the 11-19 manual close
    assert meta["settlement_source"] == "operator_spx_close_all_legs_otm"


@pytest.mark.parametrize("spx_close", [7420.0, 7450.0, 7600.0])
def test_close_near_or_inside_the_strikes_waits_for_schwab(spx_close):
    with pytest.raises(Refused, match="wait for Schwab"):
        plan_settlement(trade_100000(), [OPENING], spx_close=spx_close)


def test_posted_expiration_transactions_settle_like_the_bot():
    closing = tx(
        "CLOSING", [(LOWER, -1.0, 15.0), (CENTER, 2.0, 0.0), (UPPER, -1.0, 0.0)], 1500.0,
        time="2026-11-20T06:00:00+0000",
    )
    value, pnl, meta = plan_settlement(trade_100000(), [OPENING, closing], spx_close=7450.0)

    assert value == pytest.approx(15.0)
    assert pnl == pytest.approx((1500.0 - 379.79) / 100)
    assert meta["settlement_source"] == "schwab_expiration_transactions"


def test_refuses_a_closed_row_and_a_partly_closed_fly():
    with pytest.raises(Refused, match="not OPEN"):
        plan_settlement(trade_100000(status="CLOSED"), [OPENING], spx_close=7176.0)
    part_close = tx("CLOSING", [(LOWER, -1.0, 1.0)], 100.0)
    with pytest.raises(Refused, match="non-opening"):
        plan_settlement(trade_100000(), [OPENING, part_close], spx_close=7176.0)


def test_refuses_opening_legs_that_are_not_the_fly():
    wrong = tx("OPENING", [(LOWER, 1.0, 8.0), (CENTER, -1.0, 3.5), (UPPER, 1.0, 2.75)], -100.0)
    with pytest.raises(Refused, match="do not match"):
        plan_settlement(trade_100000(), [wrong], spx_close=7176.0)
