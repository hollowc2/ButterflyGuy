from pathlib import Path


def test_open_trade_uniqueness_migration_is_partial_unique_index():
    sql = Path(
        "src/butterfly_guy/db/migrations/008_one_open_trade_per_underlying_day.sql"
    ).read_text()

    assert "CREATE UNIQUE INDEX" in sql
    assert "butterfly_trades (underlying, trade_date)" in sql
    assert "WHERE status = 'OPEN'" in sql
