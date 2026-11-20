"""Independent price/cash and identity fixtures for offline XSP experiments."""
from pathlib import Path

import pandas as pd
import pytest

from tools.research_studies.xsp_independent.common import (
    derive_proxy,
    fly_quotes,
    load_session,
    round_trip_pnl,
    session_end,
)


def quote(strike, bid, ask, right="CALL", timestamp="2026-09-25 10:00", size=10):
    return {"symbol": "XSP", "expiration": pd.Timestamp(timestamp).date(),
            "timestamp": pd.Timestamp(timestamp, tz="America/New_York"),
            "strike": float(strike), "right": right, "bid": bid, "ask": ask,
            "bid_size": size, "ask_size": size}


@pytest.mark.parametrize("right", ["CALL", "PUT"])
def test_signed_payable_close_and_four_contract_cash_ledger(right):
    prices = [(99, .9, 1.0), (100, .5, .6), (101, .1, .2)]
    if right == "PUT":
        prices = [(99, .1, .2), (100, .5, .6), (101, .9, 1.0)]
    fly = fly_quotes(pd.DataFrame([quote(k, bid, ask, right) for k, bid, ask in prices]),
                     100, 1, right).iloc[0]
    assert fly.entry_ask == pytest.approx(.2)
    assert fly.liquidation_bid == pytest.approx(-.2)
    # $20 to buy, $20 to close, eight contract-side fees of $0.65.
    assert round_trip_pnl(fly.entry_ask, fly.liquidation_bid) == pytest.approx(-45.2)
    assert round_trip_pnl(.2, -.2, stress_per_side=.03) == pytest.approx(-51.2)


def test_no_liquidation_price_is_invented_for_absent_or_undersized_body():
    rows = [quote(99, .9, 1), quote(100, .5, .6, size=1), quote(101, .1, .2)]
    assert fly_quotes(pd.DataFrame(rows), 100, 1).empty
    rows[1]["bid_size"] = rows[1]["ask_size"] = 10
    rows[2]["timestamp"] += pd.Timedelta(minutes=1)
    assert fly_quotes(pd.DataFrame(rows), 100, 1).empty


def parity_frame(forward=100.2):
    rows = []
    for strike in (98, 99, 100, 101, 102):
        for right, mid in (("CALL", max(forward - strike, 0) + 1),
                           ("PUT", max(strike - forward, 0) + 1)):
            rows.append(quote(strike, mid - .05, mid + .05, right))
    return pd.DataFrame(rows)


def test_parity_recovers_known_zero_carry_forward_but_is_not_spot():
    proxy = derive_proxy(parity_frame()).iloc[0]
    assert proxy.forward_proxy == pytest.approx(100.2)
    assert proxy.pair_count == 5
    assert proxy.dispersion == pytest.approx(0)
    assert proxy.parity_width == pytest.approx(.2)


def test_parity_refuses_insufficient_or_inconsistent_pairs():
    frame = parity_frame()
    assert derive_proxy(frame[frame.strike.isin([99, 100])]).empty
    frame.loc[(frame.strike == 98) & (frame.right == "CALL"), ["bid", "ask"]] += .6
    assert derive_proxy(frame).empty


def test_post_expiry_grid_and_halfday_are_removed(tmp_path: Path):
    rows = [quote(100, 1, 1.1, timestamp=f"2025-11-28 {t}")
            for t in ("09:30", "09:31", "12:59", "13:00", "16:15")]
    path = tmp_path / "2025-11-28.parquet"
    pd.DataFrame(rows).to_parquet(path)
    frame = load_session(path)
    assert frame.timestamp.dt.strftime("%H:%M").tolist() == ["09:31", "12:59"]
    assert frame.attrs["filtered_rows"] == 3
    assert session_end("2025-11-28").hour == 13


@pytest.mark.parametrize("bad", ["identity", "duplicate", "expiration"])
def test_mixed_or_ambiguous_quote_evidence_fails_closed(tmp_path: Path, bad):
    frame = pd.DataFrame([quote(100, 1, 1.1)])
    if bad == "identity":
        frame.loc[0, "symbol"] = "SPXW"
    elif bad == "expiration":
        frame.loc[0, "expiration"] = pd.Timestamp("2026-09-28").date()
    else:
        frame = pd.concat([frame, frame], ignore_index=True)
    path = tmp_path / "2026-09-25.parquet"
    frame.to_parquet(path)
    with pytest.raises(ValueError):
        load_session(path)
