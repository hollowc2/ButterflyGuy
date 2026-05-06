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
