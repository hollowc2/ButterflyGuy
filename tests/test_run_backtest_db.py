import datetime as dt
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

import butterfly_guy.scripts.run_backtest_db as run_backtest_db
from butterfly_guy.backtest.chain_cache import ChainDay
from butterfly_guy.backtest.data_loader import MinuteBar


def test_resolve_db_dsn_uses_config_even_if_database_url_is_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://explicit@example/db")
    monkeypatch.setattr(
        run_backtest_db,
        "load_config",
        lambda: SimpleNamespace(database=SimpleNamespace(dsn="postgresql://cfg@example/db")),
    )

    assert run_backtest_db.resolve_db_dsn() == "postgresql://cfg@example/db"


def test_resolve_db_dsn_falls_back_to_config(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        run_backtest_db,
        "load_config",
        lambda: SimpleNamespace(database=SimpleNamespace(dsn="postgresql://cfg@example/db")),
    )

    assert run_backtest_db.resolve_db_dsn() == "postgresql://cfg@example/db"


def test_fitted_density_counts_returns_bucket_heights():
    fitted = run_backtest_db._fitted_density_counts(
        [-300.0, -250.0, 100.0, 150.0, 175.0, 900.0],
        start=-400.0,
        bucket_w=200,
        n_buckets=8,
    )

    assert len(fitted) == 8
    assert max(fitted) > 0
    assert all(height >= 0 for height in fitted)


def test_print_pnl_histogram_overlays_fitted_density(capsys):
    run_backtest_db._print_pnl_histogram(
        [-300.0, -250.0, 100.0, 150.0, 175.0, 900.0]
    )

    output = capsys.readouterr().out
    assert "fitted density" in output
    assert "╳╳╳╳" in output


@pytest.mark.asyncio
async def test_entry_window_skips_stale_vix_and_uses_first_fresh_snapshot(monkeypatch):
    eastern = ZoneInfo("America/New_York")
    date = dt.date(2026, 7, 20)
    bars = [
        MinuteBar(
            ts=dt.datetime(2026, 7, 20, 10, minute, tzinfo=eastern),
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0,
        )
        for minute in (0, 1)
    ]
    candidate = SimpleNamespace(direction="CALL")

    async def fake_vix(_conn, at_time):
        age = 301 if at_time == bars[0].ts else 0
        return 20.0, at_time - dt.timedelta(seconds=age)

    monkeypatch.setattr(run_backtest_db, "get_vix_snapshot_at", fake_vix)
    monkeypatch.setattr(
        run_backtest_db,
        "select_entry_candidate",
        lambda **_kwargs: SimpleNamespace(candidate=candidate),
    )
    args = SimpleNamespace(
        entry_window_minutes=45,
        vix_max=None,
        gap_filter=0.0,
        strategy_f=False,
        bull_call_bias=False,
        min_gap_pct=None,
    )
    config = SimpleNamespace(
        entry=SimpleNamespace(
            strike_selection_method="VIX",
            max_vix_age_seconds=300,
        ),
        strategy=SimpleNamespace(vix_width_buckets=[object()]),
    )
    data = {
        "bars": bars,
        "chains": ChainDay({bar.ts: [object()] for bar in bars}),
        "open_spot": 101.0,
        "prev_close": 100.0,
        "vix_prev_close": 21.0,
        "day": SimpleNamespace(recent_closes=[]),
    }

    entry = await run_backtest_db.find_entry_in_window(
        object(),
        data=data,
        date=date,
        asset="SPX",
        direction_arg="auto",
        entry_pst=dt.time(7, 0),
        args=args,
        config=config,
        wing_widths=None,
    )

    assert entry == (bars[1], 20.0, "CALL", candidate)


@pytest.mark.asyncio
async def test_hypothetical_monitoring_load_uses_collector_only():
    class Connection:
        def __init__(self):
            self.fetch_calls = 0

        async def fetch(self, *_args):
            self.fetch_calls += 1
            return []

        async def fetchval(self, *_args):
            return True

    conn = Connection()
    await run_backtest_db.load_monitoring_chains(
        conn,
        dt.date(2026, 7, 20),
        "SPX",
        [7000.0, 7030.0, 7060.0],
        ["CALL"],
    )

    assert conn.fetch_calls == 1
