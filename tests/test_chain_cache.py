import datetime as dt
import json

from butterfly_guy.backtest.chain_cache import chain_cache_path, load_chain_day, save_snapshot


def test_chain_cache_path_is_partitioned_by_underlying(tmp_path):
    date = dt.date(2026, 5, 6)

    assert chain_cache_path(date, tmp_path, "SPX") == tmp_path / "SPX" / "2026-05-06.json"
    assert chain_cache_path(date, tmp_path, "NDX") == tmp_path / "NDX" / "2026-05-06.json"
    assert chain_cache_path(date, tmp_path) == tmp_path / "2026-05-06.json"


def test_save_snapshot_writes_to_underlying_cache(tmp_path):
    date = dt.date(2026, 5, 6)
    snapshot_time = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    rows = [
        {
            "underlying": "NDX",
            "strike": 28500.0,
            "option_type": "CALL",
            "bid": 1.0,
            "ask": 1.2,
            "mark": 1.1,
            "iv": 0.2,
            "delta": 0.5,
            "gamma": 0.01,
            "symbol": "NDXP  260506C28500000",
            "bid_size": 10,
            "ask_size": 10,
        }
    ]

    save_snapshot(date, snapshot_time, 28500.0, rows, cache_dir=tmp_path)

    path = tmp_path / "NDX" / "2026-05-06.json"
    assert path.exists()
    assert not (tmp_path / "2026-05-06.json").exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["snapshots"][snapshot_time.isoformat()]["spot"] == 28500.0


def test_load_chain_day_falls_back_to_partitioned_spx_cache(tmp_path):
    date = dt.date(2026, 5, 6)
    snapshot_time = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    rows = [
        {
            "underlying": "SPX",
            "strike": 7350.0,
            "option_type": "CALL",
            "bid": 1.0,
            "ask": 1.2,
            "mark": 1.1,
        }
    ]

    save_snapshot(date, snapshot_time, 7350.0, rows, cache_dir=tmp_path)

    chains = load_chain_day(date, cache_dir=tmp_path)
    assert chains is not None
    assert list(chains.keys()) == [snapshot_time]


def test_load_chain_day_skips_corrupt_legacy_cache(tmp_path):
    date = dt.date(2026, 5, 6)
    snapshot_time = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    legacy_path = tmp_path / "2026-05-06.json"
    legacy_path.write_text('{"snapshots": {}} trailing', encoding="utf-8")
    rows = [
        {
            "underlying": "SPX",
            "strike": 7350.0,
            "option_type": "CALL",
            "bid": 1.0,
            "ask": 1.2,
            "mark": 1.1,
        }
    ]
    save_snapshot(date, snapshot_time, 7350.0, rows, cache_dir=tmp_path)

    chains = load_chain_day(date, cache_dir=tmp_path)
    assert chains is not None
    assert list(chains.keys()) == [snapshot_time]
