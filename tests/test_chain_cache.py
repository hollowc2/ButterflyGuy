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

    path = tmp_path / "NDX" / "2026-05-06.jsonl"
    assert path.exists()
    assert not (tmp_path / "2026-05-06.jsonl").exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["ts"] == snapshot_time.isoformat()
    assert data["spot"] == 28500.0


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


def test_load_chain_day_preserves_explicit_underlying(tmp_path):
    date = dt.date(2026, 5, 6)
    snapshot_time = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    save_snapshot(
        date,
        snapshot_time,
        28500.0,
        [
            {
                "underlying": "NDX",
                "strike": 28500.0,
                "option_type": "CALL",
                "bid": 1.0,
                "ask": 1.2,
                "mark": 1.1,
            }
        ],
        cache_dir=tmp_path,
    )

    chains = load_chain_day(date, cache_dir=tmp_path, underlying="NDX")

    assert chains is not None
    assert chains[snapshot_time][0].underlying == "NDX"


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


_SPX_ROWS = [
    {
        "underlying": "SPX",
        "strike": 7350.0,
        "option_type": "CALL",
        "bid": 1.0,
        "ask": 1.2,
        "mark": 1.1,
    }
]


def test_save_snapshot_appends_one_line_per_snapshot(tmp_path):
    date = dt.date(2026, 5, 6)
    first = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    second = first + dt.timedelta(minutes=1)

    save_snapshot(date, first, 7350.0, _SPX_ROWS, cache_dir=tmp_path)
    path = tmp_path / "SPX" / "2026-05-06.jsonl"
    first_bytes = path.read_bytes()
    save_snapshot(date, second, 7351.0, _SPX_ROWS, cache_dir=tmp_path)

    assert path.read_bytes().startswith(first_bytes)
    chains = load_chain_day(date, cache_dir=tmp_path, underlying="SPX")
    assert chains is not None
    assert sorted(chains.keys()) == [first, second]


def test_load_chain_day_skips_truncated_line_and_keeps_later_snapshots(tmp_path):
    date = dt.date(2026, 5, 6)
    first = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    third = first + dt.timedelta(minutes=2)
    save_snapshot(date, first, 7350.0, _SPX_ROWS, cache_dir=tmp_path)
    path = tmp_path / "SPX" / "2026-05-06.jsonl"
    with path.open("ab") as f:
        f.write(b'{"ts": "2026-05-06T14:31:00+00:00", "spot": 73')  # interrupted append

    save_snapshot(date, third, 7352.0, _SPX_ROWS, cache_dir=tmp_path)

    chains = load_chain_day(date, cache_dir=tmp_path, underlying="SPX")
    assert chains is not None
    assert sorted(chains.keys()) == [first, third]


def test_load_chain_day_merges_legacy_json_with_jsonl(tmp_path):
    date = dt.date(2026, 5, 6)
    legacy_ts = dt.datetime(2026, 5, 6, 14, 30, tzinfo=dt.timezone.utc)
    new_ts = legacy_ts + dt.timedelta(minutes=1)
    legacy_path = chain_cache_path(date, tmp_path, "SPX")
    legacy_path.parent.mkdir(parents=True)
    legacy_quote = {"strike": 7350.0, "type": "CALL", "bid": 1.0, "ask": 1.2, "mark": 1.1}
    legacy_path.write_text(
        json.dumps(
            {
                "date": date.isoformat(),
                "snapshots": {
                    legacy_ts.isoformat(): {"spot": 7350.0, "quotes": [legacy_quote]}
                },
            }
        ),
        encoding="utf-8",
    )
    save_snapshot(date, new_ts, 7351.0, _SPX_ROWS, cache_dir=tmp_path)

    chains = load_chain_day(date, cache_dir=tmp_path, underlying="SPX")

    assert chains is not None
    assert sorted(chains.keys()) == [legacy_ts, new_ts]
