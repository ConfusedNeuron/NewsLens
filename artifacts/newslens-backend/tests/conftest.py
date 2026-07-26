"""
Shared pytest fixtures.

Every test runs against a throwaway SQLite file, never the developer's newslens.db.
The DB path is patched before any application module is imported, because
config.settings reads it at import time and db.database captures it at module load.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def temp_db(monkeypatch):
    """A fresh, schema-initialised database for one test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    import db.database as database

    monkeypatch.setattr(database, "_db_path", path)
    database.init_db()

    yield path

    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(path + suffix)
        except OSError:
            pass


@pytest.fixture()
def client(temp_db, monkeypatch):
    """FastAPI TestClient wired to the temp database, with no background scheduler."""
    monkeypatch.setenv("ENABLE_SCHEDULER", "0")

    from fastapi.testclient import TestClient
    from api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sample_card(temp_db):
    """One live card, inserted directly so tests don't depend on the LLM."""
    import json
    import uuid
    from datetime import datetime
    from db.database import get_conn

    card_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO cards
               (id, enriched_id, headline, summary_60w, what_happened, key_number,
                winners_json, losers_json, india_angle, usa_angle, china_angle,
                personal_impact, domain_tags, geo_tags, confidence_badge,
                source_name, source_url, is_live, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                card_id,
                "enriched-1",
                "RBI holds repo rate at 6.5%",
                "The central bank held rates steady for the fourth consecutive meeting.",
                "RBI held the repo rate at 6.5%.",
                "6.5% repo rate held",
                json.dumps([
                    {
                        "who": "Home loan borrowers",
                        "why": "EMIs stay flat",
                        "magnitude": "6.5% repo rate held",
                        "magnitude_source": "data",
                    }
                ]),
                json.dumps([
                    {
                        "who": "Savers",
                        "why": "Deposit rates stay capped",
                        "magnitude": "roughly 40bps below inflation",
                        # deliberately unlabelled — must be served as "estimate"
                    }
                ]),
                "Rate-sensitive sectors stay supported.",
                "Limited direct US impact.",
                "No direct China exposure.",
                "",
                json.dumps(["Finance"]),
                json.dumps(["India"]),
                "high",
                "Economic Times",
                "https://example.com/rbi",
                True,
                datetime.utcnow().isoformat(),
            ),
        )
    return card_id
