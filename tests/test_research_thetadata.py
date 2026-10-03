"""ThetaData source: the quote mapping, the owner's minute files, the Cboe daily bars and
the terminal calls, all against a mock terminal (no subscription, no network)."""

from __future__ import annotations

import datetime as dt
import io
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest

from butterfly_guy.research import history
from butterfly_guy.research.dataset import Dataset
from butterfly_guy.research.holdout import HoldoutSealedError
from butterfly_guy.research.market import et_us
from butterfly_guy.research.thetadata import (
    ThetaDataError,
    ThetaDataSource,
    load_minute_file,
    parse_quotes,
)

D = dt.date(2026, 3, 16)  # validation window, EDT (UTC-4)
D2 = dt.date(2026, 3, 17)  # an SPX-stale day in the fixture files
HOLD = dt.date(2025, 8, 19)  # sealed holdout
BAND = (5600.0, 6400.0)

QUOTE_HEADER = ("symbol,expiration,strike,right,timestamp,bid_size,bid_exchange,bid,"
                "bid_condition,ask_size,ask_exchange,ask,ask_condition")


def _quote_csv(d: dt.date, rows: list[tuple]) -> str:
    """rows: (expiration, strike, right, HH:MM:SS[.fff], bid, ask)."""
    lines = [QUOTE_HEADER]
    for exp, k, right, hms, bid, ask in rows:
        lines.append(f"SPXW,{exp.isoformat()},{k:.3f},{right},{d.isoformat()}T{hms},"
                     f"1,5,{bid:.2f},50,1,5,{ask:.2f},50")
    return "\r\n".join(lines) + "\r\n"


def _day_quotes(d: dt.date, spot: float = 6000.0) -> str:
    """Strikes 5980-6020 by 5: a 0/0 row at 09:30, then quotes at six grid minutes."""
    rows = []
    for k in range(5980, 6021, 5):
        for right, intrinsic in (("CALL", max(spot - k, 0.0)), ("PUT", max(k - spot, 0.0))):
            rows.append((d, float(k), right, "09:30:00", 0.0, 0.0))
            mid = intrinsic + 2.0
            for hm in ("09:31", "09:32", "10:00", "15:59", "16:00"):
                rows.append((d, float(k), right, f"{hm}:00", mid - 0.05, mid + 0.05))
    return _quote_csv(d, rows)


def _minute_rows(d: dt.date, level: float, stale: bool = False) -> list[str]:
    """08:31-15:15 CT bar-end rows (`ts,close,high,low,open`); `stale` repeats one bar."""
    out = []
    t = dt.datetime.combine(d, dt.time(8, 31))
    i = 0
    while t.time() <= dt.time(15, 15):
        p = level if stale else level + (i % 7) * 0.25
        out.append(f"{t:%Y-%m-%d %H:%M:%S},{p},{p + 0.5},{p - 0.5},{p - 0.1}")
        t += dt.timedelta(minutes=1)
        i += 1
    return out


@pytest.fixture
def files(tmp_path: Path) -> tuple[Path, Path]:
    spx = tmp_path / "spx_1min.csv"
    vix = tmp_path / "vix_1min.csv"
    spx.write_text("\n".join(["ts,close,high,low,open", *_minute_rows(D, 6000.0),
                              *_minute_rows(D2, 6010.0, stale=True)]) + "\n")
    vix.write_text("\n".join(["ts,close,high,low,open", *_minute_rows(D, 18.0),
                              *_minute_rows(D2, 19.0)]) + "\n")
    return spx, vix


def _cboe(index: str) -> bytes:
    if index == "SPX":
        return (b"DATE,SPX\n03/13/2026,5990.000000\n03/16/2026,6002.500000\n"
                b"03/17/2026,6011.000000\n03/18/2026,6031.000000\n")
    return (b"DATE,OPEN,HIGH,LOW,CLOSE\n03/13/2026,17.5,18.5,17.0,18.0\n"
            b"03/16/2026,18.1,18.9,17.6,18.2\n03/17/2026,19.0,19.5,18.5,19.1\n"
            b"03/18/2026,20.4,21.2,20.1,21.0\n")


class Terminal:
    """Mock Theta Terminal. `script` maps a path (quotes: `path?right=R&date=D`, falling
    back to the bare path) to responses consumed in order; the last one repeats."""

    def __init__(self, script: dict[str, list[tuple[int, str]]]) -> None:
        self.script = script
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.removeprefix("/v3")
        key = path
        if path == "/option/history/quote":
            p = request.url.params
            key = f"{path}?right={p['right']}&date={p['date']}"
        responses = self.script.get(key) or self.script[path]
        status, body = responses.pop(0) if len(responses) > 1 else responses[0]
        return httpx.Response(status, text=body)


EXPIRATIONS = (200, "symbol,expiration\r\nSPXW,2025-08-19\r\nSPXW,2026-03-13\r\n"
                    "SPXW,2026-03-16\r\nSPXW,2026-03-17\r\nSPXW,2026-03-20\r\n")


def _source(files, terminal: Terminal) -> ThetaDataSource:
    return ThetaDataSource(*files, transport=httpx.MockTransport(terminal), cboe=_cboe,
                           sleep=lambda s: None)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_thetadata_is_registered_and_needs_the_minute_files(files, tmp_path):
    src = history.get_source("thetadata", spx_minutes=files[0], vix_minutes=files[1])
    assert isinstance(src, ThetaDataSource)
    with pytest.raises(FileNotFoundError, match="index minute file"):
        history.get_source("thetadata", spx_minutes=tmp_path / "nope.csv",
                           vix_minutes=files[1])


def test_source_satisfies_the_history_source_interface():
    names = [n for n in vars(history.HistorySource) if not n.startswith("_")]
    assert set(names) <= set(dir(ThetaDataSource))


# ---------------------------------------------------------------------------
# Quote mapping
# ---------------------------------------------------------------------------


def test_quotes_map_to_utc_and_types_and_a_0_0_row_is_no_quote():
    text = _quote_csv(D, [
        (D, 6000.0, "CALL", "09:30:00", 0.0, 0.0),   # no quote yet -> NaN
        (D, 6000.0, "CALL", "09:31:00", 4.5, 4.7),
        (D, 6300.0, "PUT", "09:31:00", 0.0, 0.05),   # real zero bid -> kept
        (D, 6000.5, "CALL", "09:31:00", 1.0, 1.1),   # non-integer strike -> dropped
        (D, 7000.0, "CALL", "09:31:00", 1.0, 1.1),   # outside the band -> dropped
        (D2, 6000.0, "CALL", "09:31:00", 1.0, 1.1),  # other expiration -> dropped
    ])
    q = parse_quotes(text, D, BAND)
    assert q["t"].tolist() == ["C", "C", "P"]
    assert np.isnan(q["bid"].iloc[0]) and np.isnan(q["ask"].iloc[0])
    assert (q["bid"].iloc[2], q["ask"].iloc[2]) == (0.0, 0.05)
    # 09:31 EDT = 13:31 UTC.
    assert q["ts_us"].iloc[1] == int(
        dt.datetime(2026, 3, 16, 13, 31, tzinfo=dt.UTC).timestamp()) * 10**6


def test_millisecond_timestamps_with_trimmed_zeros_parse():
    q = parse_quotes(_quote_csv(D, [(D, 6000.0, "PUT", "09:30:04.09", 1.0, 1.1)]), D, BAND)
    assert q["ts_us"].iloc[0] == et_us(D, 9, 30, 4) + 90_000


# ---------------------------------------------------------------------------
# Minute files and daily bars
# ---------------------------------------------------------------------------


def test_minute_file_is_central_time_bar_end_and_stale_days_are_dropped(files):
    spx, stale = load_minute_file(files[0])
    assert stale == [D2.isoformat()]
    day = spx[spx["date"] == D]
    # 08:31 CT bar end = 09:31 ET; 15:00 CT = 16:00 ET; the 16:01-16:15 ET bars are cut.
    assert day["ts_us"].iloc[0] == et_us(D, 9, 31)
    assert day["ts_us"].iloc[-1] == et_us(D, 16, 0)
    assert len(day) == 390
    assert (spx["date"] != D2).all()


def test_index_bars_serve_the_day_and_nothing_for_a_stale_day(files):
    src = _source(files, Terminal({}))
    assert len(src.index_bars(D, "SPX")) == 390
    assert src.index_bars(D2, "SPX").empty
    assert len(src.index_bars(D2, "$VIX")) == 390


def test_daily_bars_take_the_official_close_from_cboe_and_the_open_from_the_file(files):
    src = _source(files, Terminal({}))
    bars = src.daily_bars(dt.date(2026, 3, 13), D2).set_index(["underlying", "date"])
    assert bars.loc[("SPX", D), "close"] == 6002.5  # Cboe, not the file's last bar
    assert bars.loc[("SPX", D), "open"] == pytest.approx(5999.9)  # first bar's open
    assert np.isnan(bars.loc[("SPX", D2), "open"])  # stale day: official close only
    assert bars.loc[("SPX", D2), "close"] == 6011.0
    assert np.isnan(bars.loc[("SPX", dt.date(2026, 3, 13)), "open"])  # not in the file
    assert tuple(bars.loc[("$VIX", D), ["open", "high", "low", "close"]]) == (
        18.1, 18.9, 17.6, 18.2)


# ---------------------------------------------------------------------------
# Terminal calls
# ---------------------------------------------------------------------------


def test_quote_request_asks_for_one_day_all_strikes_one_minute_csv(files):
    term = Terminal({"/option/history/quote": [(200, _day_quotes(D))]})
    q = _source(files, term).quotes(D, BAND)
    req = term.requests[0]
    assert dict(req.url.params) == {
        "symbol": "SPXW", "expiration": "20260316", "date": "20260316", "strike": "*",
        "interval": "1m", "start_time": "09:30:00", "end_time": "16:00:00", "right": "both",
        "format": "csv"}
    assert req.url.host == "127.0.0.1"
    assert not {"authorization", "x-api-key"} & {h.lower() for h in req.headers}
    assert len(q) == 9 * 2 * 6


def test_no_data_is_empty_transient_errors_retry_and_large_requests_split(files):
    term = Terminal({"/option/history/quote": [(472, "NO_DATA")]})
    assert _source(files, term).quotes(D, BAND).empty

    term = Terminal({"/option/history/quote": [(474, "DISCONNECTED"), (429, "OS_LIMIT"),
                                               (200, _day_quotes(D))]})
    assert len(_source(files, term).quotes(D, BAND)) == 108
    assert len(term.requests) == 3

    calls = _quote_csv(D, [(D, 6000.0, "CALL", "09:31:00", 2.0, 2.1)])
    puts = _quote_csv(D, [(D, 6000.0, "PUT", "09:31:00", 2.0, 2.1)])
    term = Terminal({"/option/history/quote?right=both&date=20260316": [(570, "LARGE")],
                     "/option/history/quote?right=call&date=20260316": [(200, calls)],
                     "/option/history/quote?right=put&date=20260316": [(200, puts)]})
    assert sorted(_source(files, term).quotes(D, BAND)["t"]) == ["C", "P"]

    term = Terminal({"/option/history/quote": [(471, "PERMISSION")]})
    with pytest.raises(ThetaDataError, match="HTTP 471"):
        _source(files, term).quotes(D, BAND)


def test_sessions_are_expirations_inside_the_range(files):
    term = Terminal({"/option/list/expirations": [EXPIRATIONS]})
    assert _source(files, term).sessions(D, D2) == [D, D2]


def test_describe_pins_the_inputs_and_carries_no_credential(files):
    d = _source(files, Terminal({})).describe()
    assert d["plan"] == "Options Value"
    assert d["index_files"]["SPX"]["stale_days_excluded"] == [D2.isoformat()]
    assert d["index_files"]["$VIX"]["stale_days_excluded"] == []
    assert len(d["daily_bars"]["SPX"]["sha256"]) == 64
    assert not any(k in str(d).lower() for k in ("api_key", "apikey", "password", "td1_"))


# ---------------------------------------------------------------------------
# End to end through the guarded writer
# ---------------------------------------------------------------------------


def test_validation_pull_writes_real_levels_only_and_skips_the_stale_day(files, tmp_path):
    term = Terminal({"/option/list/expirations": [EXPIRATIONS],
                     "/option/history/quote?right=both&date=20260316": [(200, _day_quotes(D))],
                     "/option/history/quote?right=both&date=20260317": [
                         (200, _day_quotes(D2, spot=6010.0))]})
    plan = history.HistoryPlan(D, D2, "spx_0dte_thetadata", log=io.StringIO())
    m = history.write_history(_source(files, term), plan, tmp_path)
    ds = Dataset.open("spx_0dte_thetadata", tmp_path)
    assert ds.sessions()["date"].tolist() == [D]
    assert ds.sessions()["spot_source"].tolist() == ["index"]
    chain = ds.chain(D)
    assert chain.ts[0] == et_us(D, 9, 31)
    assert np.isfinite(chain.fields["C_bid"][0]).all()  # the 09:30 0/0 rows are off-grid
    # The stale SPX day is skipped before its quotes are fetched; nothing is derived.
    assert m.history[-1]["sessions_skipped"] == {D2.isoformat(): "no_spx_index"}
    assert not [r for r in m.history[-1]["requests"]
                if r["call"] == "quotes" and r["start"] == D2.isoformat()]
    assert m.source["plan"] == "Options Value"


@pytest.mark.usefixtures("sealed_holdout")
def test_a_holdout_pull_stops_before_any_terminal_request(files, tmp_path):
    term = Terminal({"/option/list/expirations": [EXPIRATIONS]})
    plan = history.HistoryPlan(HOLD, HOLD, "spx_0dte_thetadata", log=io.StringIO())
    with pytest.raises(HoldoutSealedError):
        history.write_history(_source(files, term), plan, tmp_path)
    assert term.requests == []


# ---------------------------------------------------------------------------
# After the minute files end: recorded SPX, $VIX and SPX open (never in the holdout)
# ---------------------------------------------------------------------------


class Recorded:
    """Stands in for the Helios `spx_0dte` dataset."""

    name, hash = "spx_0dte", "h" * 64
    LATER = dt.date(2026, 3, 18)

    def spot_ticks(self, underlying):
        ts = np.array([et_us(self.LATER, 9, 29), et_us(self.LATER, 9, 31),
                       et_us(self.LATER, 16, 0), et_us(self.LATER, 16, 5)], dtype=np.int64)
        return ts, np.array([20.0, 20.5, 21.0, 21.5])

    def daily_bars(self):
        return pd.DataFrame([{"date": self.LATER, "underlying": "SPX", "open": 6020.0,
                              "high": 6040.0, "low": 6005.0, "close": 6030.0},
                             {"date": D, "underlying": "SPX", "open": 1.0, "high": 1.0,
                              "low": 1.0, "close": 1.0}])


def test_after_the_files_end_spx_and_vix_come_from_the_recorded_dataset(files):
    later = Recorded.LATER
    src = ThetaDataSource(*files, recorded=Recorded(), cboe=_cboe)
    vix = src.index_bars(later, "$VIX")
    assert vix["price"].tolist() == [20.5, 21.0]  # 09:30-16:00 ET only
    assert src.index_bars(later, "SPX")["price"].tolist() == [20.5, 21.0]  # real ticks
    assert src.index_bars(D2, "SPX").empty  # a stale in-file day is not back-filled
    assert src.index_bars(D, "$VIX")["price"].iloc[0] == 18.0  # the file wins in range
    bars = src.daily_bars(D, later).set_index(["underlying", "date"])
    assert bars.loc[("SPX", D), "open"] == pytest.approx(5999.9)  # file, not recorded
    assert tuple(bars.loc[("SPX", later), ["open", "high", "low", "close"]]) == (
        6020.0, 6040.0, 6005.0, 6031.0)  # recorded open/high/low, Cboe close
    assert src.describe()["recorded"]["dataset"] == "spx_0dte"


def test_without_a_recorded_dataset_nothing_is_served_after_the_files_end(files):
    src = _source(files, Terminal({}))
    assert src.index_bars(Recorded.LATER, "$VIX").empty
    assert src.describe()["recorded"] is None


@pytest.mark.usefixtures("sealed_holdout")
def test_recorded_levels_are_never_served_inside_the_holdout(files):
    class InHoldout(Recorded):
        LATER = dt.date(2026, 3, 11)  # after the files end, inside the holdout

    src = ThetaDataSource(*files, recorded=InHoldout(), cboe=_cboe)
    assert src.index_bars(InHoldout.LATER, "SPX").empty
    assert src.index_bars(InHoldout.LATER, "$VIX").empty
