import re
from pathlib import Path

MIGRATIONS_DIR = (
    Path(__file__).parents[1] / "src" / "butterfly_guy" / "db" / "migrations"
)


def test_migrations_add_decision_log_underlying_column() -> None:
    migration_sql = "\n".join(
        path.read_text() for path in sorted(MIGRATIONS_DIR.glob("*.sql"))
    )

    assert re.search(
        r"ALTER\s+TABLE\s+decision_log\s+"
        r"ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+underlying\s+TEXT",
        migration_sql,
        flags=re.IGNORECASE,
    )
