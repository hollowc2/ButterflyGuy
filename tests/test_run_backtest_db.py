from types import SimpleNamespace

import butterfly_guy.scripts.run_backtest_db as run_backtest_db


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
