"""Term-structure features never use a value from after the decision; aux-file plumbing."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from butterfly_guy.research.dataset import Dataset, Manifest
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.features import DailyVol, IntradayVol, SessionFeatures
from butterfly_guy.research.market import et_us
from butterfly_guy.research.volindex import (
    DAILY_FILE,
    INTRADAY_FILE,
    daily_table,
    ingest_intraday,
    intraday_table,
    merge_intraday,
    parse_cboe_csv,
    write_aux,
)

FIXTURE = Path(__file__).parent / "fixtures" / "research" / "mini_spx"
D = dt.date


def _daily(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.to_datetime([r[1] for r in rows]), "index": [r[0] for r in rows],
        "open": [r[2] for r in rows], "high": [r[2] for r in rows],
        "low": [r[2] for r in rows], "close": [r[2] for r in rows]})


def test_daily_features_use_the_prior_session_close_never_the_session_row():
    vol = DailyVol(_daily([
        ("VIX", "2026-06-08", 16.0), ("VIX", "2026-06-09", 17.0), ("VIX", "2026-06-10", 99.0),
        ("VIX9D", "2026-06-09", 15.3), ("VIX9D", "2026-06-10", 99.0),
        ("VIX3M", "2026-06-09", 20.0), ("VIX1D", "2026-06-09", 11.9),
    ]))
    f = vol.features(D(2026, 6, 10))
    assert f["prior_session"] == "2026-06-09"
    assert f["vix_prior_close"] == 17.0
    assert f["vix9d_prior_close"] == 15.3
    assert f["vix9d_vix_prior"] == pytest.approx(0.9)
    assert f["vix_vix3m_prior"] == pytest.approx(0.85)
    assert f["vix1d_vix_prior"] == pytest.approx(0.7)


def test_stale_or_missing_prior_close_stays_missing():
    vol = DailyVol(_daily([
        ("VIX", "2026-06-08", 16.0), ("VIX", "2026-06-09", 17.0),
        ("VIX1D", "2026-06-08", 11.0),  # no 06-09 row: stale for 06-10
    ]))
    f = vol.features(D(2026, 6, 10))
    assert f["vix1d_prior_close"] is None and f["vix1d_vix_prior"] is None
    assert f["vix9d_prior_close"] is None and f["vix9d_vix_prior"] is None
    assert vol.features(D(2026, 6, 8))["vix_prior_close"] is None  # nothing before


def test_holiday_vix_print_is_not_the_prior_session():
    # Cboe prints VIX on some exchange holidays (2026-07-03); the prior session is 07-02.
    vol = DailyVol(_daily([
        ("VIX", "2026-07-02", 16.15), ("VIX", "2026-07-03", 15.81),
        ("VIX9D", "2026-07-02", 14.0), ("VIX3M", "2026-07-02", 19.0),
    ]))
    f = vol.features(D(2026, 7, 6), previous_session=D(2026, 7, 2))
    assert f["prior_session"] == "2026-07-02"
    assert f["vix_prior_close"] == 16.15
    assert f["vix9d_vix_prior"] == pytest.approx(14.0 / 16.15)
    # Without the session calendar the holiday row stands in, and the others go missing.
    assert vol.features(D(2026, 7, 6))["vix9d_prior_close"] is None
    with pytest.raises(ValueError):
        vol.features(D(2026, 7, 6), previous_session=D(2026, 7, 6))


def _bars(index: str, starts: list[int], closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"ts_us": starts, "index": index, "bar_seconds": 60,
                         "open": closes, "high": closes, "low": closes, "close": closes})


def test_intraday_uses_only_bars_complete_at_the_decision():
    decision = et_us(D(2026, 9, 1), 10, 0)
    minute = 60_000_000
    vol = IntradayVol(pd.concat([
        # 09:58 bar (done 09:59), 09:59 bar (done 10:00:00), 10:00 bar (still open)
        _bars("VIX9D", [decision - 2 * minute, decision - minute, decision], [13.0, 14.0, 99.0]),
        _bars("VIX", [decision - minute], [16.0]),
    ]))
    assert vol.at("VIX9D", decision) == 14.0
    assert vol.at("VIX9D", decision - 1) == 13.0  # one microsecond earlier: 09:59 bar open
    f = vol.features(decision)
    assert f["vix9d_intraday"] == 14.0 and f["vix_intraday"] == 16.0
    assert f["vix9d_vix_intraday"] == pytest.approx(14.0 / 16.0)
    assert f["vix3m_intraday"] is None and f["vix_vix3m_intraday"] is None


def test_intraday_bar_timestamped_one_second_late_is_rejected():
    decision = et_us(D(2026, 9, 1), 10, 0)
    vol = IntradayVol(_bars("VIX", [decision - 59_000_000], [16.0]))  # done at 10:00:01
    assert vol.at("VIX", decision) is None
    assert vol.at("VIX", decision + 1_000_000) == 16.0


def test_intraday_value_too_old_is_missing():
    decision = et_us(D(2026, 9, 1), 10, 0)
    vol = IntradayVol(_bars("VIX", [decision - 10 * 60_000_000], [16.0]))
    assert vol.at("VIX", decision) is None
    assert vol.at("VIX", decision, max_age_s=600) == 16.0


def test_cboe_parser_and_gateway_dump():
    raw = (b"DATE,OPEN,HIGH,LOW,CLOSE\n09/24/2026,15.8,16.5,15.3,15.67\n"
           b"09/25/2026,15.6,15.9,14.7,14.87\n")
    df = parse_cboe_csv(raw, "VIX")
    assert df["date"].dt.date.tolist() == [D(2026, 9, 24), D(2026, 9, 25)]
    assert df["close"].tolist() == [15.67, 14.87]
    with pytest.raises(ValueError, match="columns"):
        parse_cboe_csv(b"Date,Close\n09/24/2026,1\n", "VIX")
    table = daily_table({"VIX": ("u", raw), "VIX9D": ("u", raw)})
    assert table["index"].tolist() == ["VIX", "VIX", "VIX9D", "VIX9D"]

    lines = [json.dumps({"symbol": "$VIX9D", "date": "2026-09-01", "bar_seconds": 60,
                         "flags": ["stale"], "candles": [
                             {"ts": "2026-09-01T13:31:00+00:00", "open": 1, "high": 2,
                              "low": 0.5, "close": 1.5}]}),
             json.dumps({"symbol": "$VIX1D", "date": "2026-09-01", "candles": [],
                         "flags": ["no_bars_returned"]})]
    bars, coverage = intraday_table(lines)
    assert bars["index"].tolist() == ["VIX9D"]
    assert bars["ts_us"].tolist() == [int(pd.Timestamp("2026-09-01T13:31:00Z").value // 1000)]
    assert [c["bars"] for c in coverage] == [1, 0]
    naive = json.dumps({"symbol": "$VIX", "date": "2026-09-01", "candles": [
        {"ts": "2026-09-01T13:31:00", "open": 1, "high": 1, "low": 1, "close": 1}]})
    with pytest.raises(ValueError, match="naive"):
        intraday_table([naive])


# ---------------------------------------------------------------------------
# Manifest compatibility: aux files are hashed separately from the chain data
# ---------------------------------------------------------------------------


def test_v1_manifest_loads_and_resaves_byte_identically(tmp_path):
    text = (FIXTURE / "manifest.json").read_text()
    body = json.loads(text)
    assert body["schema_version"] == 1 and "aux" not in body
    m = Manifest.load(FIXTURE / "manifest.json")
    assert m.schema_version == 1 and m.aux == {} and m.aux_hash is None
    assert m.dataset_hash == body["dataset_hash"]
    assert m.to_json() == text


def _copy_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "mini_spx"
    shutil.copytree(FIXTURE, root)
    return root


def test_adding_aux_files_keeps_the_dataset_hash(tmp_path):
    root = _copy_fixture(tmp_path)
    before = Manifest.load(root / "manifest.json")
    daily = _daily([("VIX", "2026-06-09", 17.0), ("VIX", "2026-06-10", 18.0)])
    m = write_aux(root, DAILY_FILE, daily, {"kind": "test"}, ["index", "date"])
    assert m.dataset_hash == before.dataset_hash
    assert m.schema_version == 2 and m.aux_hash is not None
    body = json.loads((root / "manifest.json").read_text())
    assert body["schema_version"] == 2 and body["dataset_hash"] == before.dataset_hash
    assert body["history"][-1]["mode"] == "aux" and body["history"][-1]["rows_added"] == 2

    ds = Dataset(root)
    assert ds.hash == before.dataset_hash and ds.verify() == []
    assert ds.aux_table(DAILY_FILE)["close"].tolist() == [17.0, 18.0]

    revised = _daily([("VIX", "2026-06-09", 17.5), ("VIX", "2026-06-10", 18.0),
                      ("VIX", "2026-06-11", 19.0)])
    m2 = write_aux(root, DAILY_FILE, revised, {"kind": "test"}, ["index", "date"])
    change = m2.history[-1]
    assert change["rows_added"] == 1 and change["rows_removed"] == 0
    assert change["revised"] == [{"index": "VIX", "date": "2026-06-09", "open": [17.0, 17.5],
                                  "high": [17.0, 17.5], "low": [17.0, 17.5],
                                  "close": [17.0, 17.5]}]
    assert m2.dataset_hash == before.dataset_hash and m2.aux_hash != m.aux_hash


def test_tampered_aux_file_or_hash_is_caught(tmp_path):
    root = _copy_fixture(tmp_path)
    write_aux(root, DAILY_FILE, _daily([("VIX", "2026-06-09", 17.0)]), {}, ["index", "date"])
    (root / DAILY_FILE).write_bytes((root / DAILY_FILE).read_bytes() + b"x")
    assert Dataset(root).verify() == [f"sha256 mismatch {DAILY_FILE}"]
    with pytest.raises(ValueError, match="sha256"):
        Dataset(root).aux_table(DAILY_FILE)

    body = json.loads((root / "manifest.json").read_text())
    body["aux_hash"] = "0" * 64
    (root / "manifest.json").write_text(json.dumps(body))
    with pytest.raises(ValueError, match="aux_hash"):
        Manifest.load(root / "manifest.json")



# ---------------------------------------------------------------------------
# Intraday ingest merges: kept, added, revised, never silently removed
# ---------------------------------------------------------------------------


def _dump(path: Path, days: dict[str, list[tuple[str, float]]], symbol: str = "$VIX",
          bar_seconds: int = 60) -> Path:
    """A gateway dump with one record per date: {date: [(utc iso ts, close), ...]}."""
    lines = [json.dumps({"symbol": symbol, "date": d, "bar_seconds": bar_seconds,
                         "candles": [{"ts": ts, "open": c, "high": c, "low": c, "close": c}
                                     for ts, c in bars]})
             for d, bars in days.items()]
    path.write_text("\n".join(lines) + "\n")
    return path


def _us(ts: str) -> int:
    return int(pd.Timestamp(ts).value // 1000)


def test_intraday_ingest_keeps_adds_and_revises(tmp_path):
    _copy_fixture(tmp_path)
    first = _dump(tmp_path / "a.jsonl", {
        "2026-08-12": [("2026-08-12T13:30:00+00:00", 16.0), ("2026-08-12T13:31:00+00:00", 16.1)],
        "2026-08-13": [("2026-08-13T13:30:00+00:00", 17.0)]})
    m1 = ingest_intraday("mini_spx", first, tmp_path)
    assert m1.history[-1]["rows_added"] == 3 and m1.history[-1]["kept_not_in_dump"] == 0

    # Retention rolled past 08-12; 08-13's bar was revised; 08-14 is new.
    second = _dump(tmp_path / "b.jsonl", {
        "2026-08-13": [("2026-08-13T13:30:00+00:00", 17.5)],
        "2026-08-14": [("2026-08-14T13:30:00+00:00", 18.0)]})
    m2 = ingest_intraday("mini_spx", second, tmp_path)
    h = m2.history[-1]
    assert h["rows_added"] == 1 and h["rows_removed"] == 0 and h["kept_not_in_dump"] == 2
    assert h["revised"] == [{"index": "VIX", "ts_us": str(_us("2026-08-13T13:30:00Z")),
                             **{c: [17.0, 17.5] for c in ("open", "high", "low", "close")}}]
    assert h["dump_sha256"] == m2.aux[INTRADAY_FILE]["source"]["dumps"][-1]["dump_sha256"]
    assert len(m2.aux[INTRADAY_FILE]["source"]["dumps"]) == 2

    table = Dataset(tmp_path / "mini_spx").aux_table(INTRADAY_FILE)
    assert table["ts_us"].tolist() == [_us("2026-08-12T13:30:00Z"), _us("2026-08-12T13:31:00Z"),
                                       _us("2026-08-13T13:30:00Z"), _us("2026-08-14T13:30:00Z")]
    assert table["close"].tolist() == [16.0, 16.1, 17.5, 18.0]
    assert m2.dataset_hash == m1.dataset_hash and m2.aux_hash != m1.aux_hash


def test_intraday_reingest_of_the_same_dump_changes_nothing(tmp_path):
    _copy_fixture(tmp_path)
    dump = _dump(tmp_path / "a.jsonl", {"2026-08-12": [("2026-08-12T13:30:00+00:00", 16.0)]})
    m1 = ingest_intraday("mini_spx", dump, tmp_path)
    m2 = ingest_intraday("mini_spx", dump, tmp_path)
    h = m2.history[-1]
    assert (h["rows_added"], h["rows_removed"], h["revised"]) == (0, 0, [])
    assert m2.aux[INTRADAY_FILE]["sha256"] == m1.aux[INTRADAY_FILE]["sha256"]
    assert m2.aux_hash == m1.aux_hash


def test_intraday_ingest_converts_a_pre_merge_source(tmp_path):
    root = _copy_fixture(tmp_path)
    write_aux(root, INTRADAY_FILE, _bars("VIX", [_us("2026-08-12T13:30:00Z")], [16.0]),
              {"kind": "schwab_gateway_session_history", "dump_sha256": "ab" * 32,
               "ingested_at": "2026-09-28T06:18:00+00:00", "coverage": []},
              ["index", "ts_us"])
    dump = _dump(tmp_path / "b.jsonl", {"2026-08-13": [("2026-08-13T13:30:00+00:00", 17.0)]})
    m = ingest_intraday("mini_spx", dump, tmp_path)
    dumps = m.aux[INTRADAY_FILE]["source"]["dumps"]
    assert [d["dump_sha256"] for d in dumps][0] == "ab" * 32 and len(dumps) == 2
    assert m.aux[INTRADAY_FILE]["rows"] == 2


def test_merge_never_removes_and_rejects_a_bar_size_clash():
    old = _bars("VIX", [1, 2, 3], [16.0, 16.1, 16.2])
    merged, kept = merge_intraday(old, _bars("VIX", [3, 4], [16.2, 16.3]))
    assert merged["ts_us"].tolist() == [1, 2, 3, 4] and kept == 2
    merged, kept = merge_intraday(old, _bars("VIX", [], []))
    assert merged["ts_us"].tolist() == [1, 2, 3] and kept == 3
    clash = _bars("VIX", [2], [16.1]).assign(bar_seconds=300)
    with pytest.raises(ValueError, match="bar_seconds"):
        merge_intraday(old, clash)


def test_aux_write_refuses_to_remove_rows_when_asked(tmp_path):
    root = _copy_fixture(tmp_path)
    write_aux(root, INTRADAY_FILE, _bars("VIX", [1, 2], [16.0, 16.1]), {}, ["index", "ts_us"])
    before = (root / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="remove 1 existing rows"):
        write_aux(root, INTRADAY_FILE, _bars("VIX", [2], [16.1]), {}, ["index", "ts_us"],
                  allow_removal=False)
    assert (root / "manifest.json").read_bytes() == before
    assert Dataset(root).aux_table(INTRADAY_FILE)["ts_us"].tolist() == [1, 2]

def test_session_features_record_their_inputs(tmp_path):
    root = _copy_fixture(tmp_path)
    write_aux(root, DAILY_FILE, _daily([("VIX", "2026-06-09", 17.0)]), {}, ["index", "date"])
    decision = et_us(D(2026, 6, 10), 10, 0)
    write_aux(root, INTRADAY_FILE, _bars("VIX", [decision - 60_000_000], [18.0]), {},
              ["index", "ts_us"])
    ds = Dataset(root)
    cal = EventCalendar()
    f = SessionFeatures.load(ds, cal)
    assert f.inputs["event_calendar"]["sha256"] == cal.sha256
    assert f.inputs["aux_hash"] == ds.aux_hash
    assert set(f.inputs["aux_files"]) == {DAILY_FILE, INTRADAY_FILE}
    ts = f.term_structure(D(2026, 6, 10), decision)
    assert ts["vix_prior_close"] == 17.0 and ts["vix_intraday"] == 18.0
    assert f.term_structure(D(2026, 6, 10))["vix_prior_close"] == 17.0


def test_session_features_without_aux_files():
    f = SessionFeatures.load(Dataset(FIXTURE))
    assert f.daily is None and f.intraday is None and f.inputs["aux_hash"] is None
    assert f.term_structure(D(2026, 6, 10), 0) == {}


@pytest.mark.research_data
def test_the_published_dataset_still_loads_with_its_hash():
    try:
        ds = Dataset.open()
    except (FileNotFoundError, ValueError):
        pytest.skip("research cache not present (see docs/research/research-core.md)")
    # dd38a5ec... until 2026-09-25's official close landed (bars-only refresh, 2026-09-28);
    # aux files never change it.
    assert ds.hash == "b76dc6c9e1c77a4ca15aa2aa4be73bcc86e3c6e5e5314e634d9dacf839ae0f45"
    assert ds.manifest.schema_version in (1, 2)
