import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from config.settings import DB_PATH

_db_path = DB_PATH
_schema_path = Path(__file__).parent / "schema.sql"


def get_db_path() -> str:
    return _db_path


# Columns added to existing tables after the first release.
#
# schema.sql uses CREATE TABLE IF NOT EXISTS, which is a no-op against a database
# that already has the table — so new columns never appear on an existing dev DB.
# These ALTERs run on every startup and are idempotent: adding a column that is
# already there raises OperationalError, which is caught and ignored.
#
# SQLite only supports adding nullable columns without a table rebuild, which is
# exactly what all of these are.
_MIGRATIONS = [
    ("cards", "time_horizon", "TEXT"),
    ("cards", "market_data", "TEXT"),
    ("cards", "is_seed", "BOOLEAN DEFAULT FALSE"),
]


def _apply_migrations(conn) -> None:
    for table, column, decl in _MIGRATIONS:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column in existing:
            continue
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        except sqlite3.OperationalError:
            # Table doesn't exist yet (fresh DB — schema.sql already created it with
            # the column), or the column was added concurrently. Either way, fine.
            pass


def init_db():
    """Initialize the database, creating all tables if they don't exist."""
    os.makedirs(os.path.dirname(os.path.abspath(_db_path)), exist_ok=True) if os.path.dirname(_db_path) else None
    conn = sqlite3.connect(_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    with open(_schema_path, "r") as f:
        conn.executescript(f.read())
    _apply_migrations(conn)
    conn.commit()
    conn.close()


@contextmanager
def get_conn():
    """Context manager for database connections."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchone(query: str, params: tuple = ()) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def fetchall(query: str, params: tuple = ()) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def execute(query: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.rowcount


def executemany(query: str, params_list: list[tuple]) -> int:
    with get_conn() as conn:
        cur = conn.executemany(query, params_list)
        return cur.rowcount
