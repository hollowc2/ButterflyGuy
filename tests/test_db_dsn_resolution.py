from types import SimpleNamespace

import butterfly_guy.scripts.run_entry_analysis as run_entry_analysis
import butterfly_guy.scripts.run_paper_replay as run_paper_replay


def test_run_entry_analysis_uses_config_dsn(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://shell@example/db")
    monkeypatch.setattr(
        run_entry_analysis,
        "load_config",
        lambda: SimpleNamespace(database=SimpleNamespace(dsn="postgresql://cfg@example/db")),
    )

    assert run_entry_analysis.resolve_db_dsn() == "postgresql://cfg@example/db"


def test_run_paper_replay_uses_config_dsn(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://shell@example/db")
    monkeypatch.setattr(
        run_paper_replay,
        "load_config",
        lambda: SimpleNamespace(database=SimpleNamespace(dsn="postgresql://cfg@example/db")),
    )

    assert run_paper_replay.resolve_db_dsn() == "postgresql://cfg@example/db"
