"""
API contract tests.

The single most valuable test in this file is test_profile_put_round_trip. The
OpenAPI spec declared PUT for /user/profile while the backend registered only POST,
so every profile save from the UI returned 405 — silently, because the frontend
mutation had no error handler. That shipped and survived two months and three
written audits. One request-level assertion would have caught it on day one.
"""
import json


def test_healthz(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_cards_returns_live_card(client, sample_card):
    r = client.get("/api/cards")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert any(c["id"] == sample_card for c in body["cards"])


def test_get_single_card(client, sample_card):
    r = client.get(f"/api/cards/{sample_card}")
    assert r.status_code == 200
    assert r.json()["headline"] == "RBI holds repo rate at 6.5%"


def test_get_missing_card_404s(client):
    assert client.get("/api/cards/does-not-exist").status_code == 404


# ---------------------------------------------------------------------------
# Profile — the 405 regression guard
# ---------------------------------------------------------------------------

PROFILE = {
    "user_id": "test_user",
    "income_type": "Salaried Employee",
    "sector_exposure": "IT / Software, Banking & Finance",
    "investment_profile": "Mutual funds / SIPs",
    "city": "Bengaluru",
    "companies_of_interest": "Infosys, HDFC Bank",
}


def test_profile_put_round_trip(client):
    """PUT is the verb the generated client actually sends. It must work."""
    put = client.put("/api/user/profile", json=PROFILE)
    assert put.status_code == 200, f"PUT /user/profile returned {put.status_code}"

    got = client.get("/api/user/profile", params={"user_id": "test_user"})
    assert got.status_code == 200
    assert got.json()["city"] == "Bengaluru"
    assert got.json()["sector_exposure"] == "IT / Software, Banking & Finance"


def test_profile_post_still_works(client):
    """POST is kept for older client builds."""
    assert client.post("/api/user/profile", json=PROFILE).status_code == 200


def test_profile_put_is_idempotent_upsert(client):
    client.put("/api/user/profile", json=PROFILE)
    updated = {**PROFILE, "city": "Mumbai"}
    r = client.put("/api/user/profile", json=updated)
    assert r.status_code == 200
    assert r.json()["city"] == "Mumbai"

    got = client.get("/api/user/profile", params={"user_id": "test_user"})
    assert got.json()["city"] == "Mumbai"


def test_missing_profile_404s(client):
    r = client.get("/api/user/profile", params={"user_id": "nobody"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Magnitude provenance
# ---------------------------------------------------------------------------

def test_unlabelled_magnitude_is_served_as_estimate(client, sample_card):
    """
    Fail safe, not open. A figure with no explicit "data" label must never be
    presented to the reader as sourced — including the cards generated before the
    provenance field existed.
    """
    body = client.get(f"/api/cards/{sample_card}").json()
    assert body["winners"][0]["magnitude_source"] == "data"
    assert body["losers"][0]["magnitude_source"] == "estimate"


# ---------------------------------------------------------------------------
# Personalized feed
# ---------------------------------------------------------------------------

def test_personalized_requires_profile(client, sample_card):
    r = client.get("/api/cards/personalized", params={"user_id": "ghost"})
    assert r.status_code == 404


def test_personalized_matches_any_declared_sector(client, sample_card, monkeypatch):
    """
    The user declares two sectors; the card is tagged Finance, which is the SECOND
    one. This previously filtered on sectors[0] only, so the card was invisible.
    """
    import agents.personalize_agent as pa
    # No LLM in tests — personalization degrades to "no impact text", not an error.
    monkeypatch.setattr(pa, "COMMANDCODE_API_KEY", "")

    client.put("/api/user/profile", json={**PROFILE, "sector_exposure": "Tech, Finance"})
    r = client.get("/api/cards/personalized", params={"user_id": "test_user"})
    assert r.status_code == 200
    assert any(c["id"] == sample_card for c in r.json()["cards"])


def test_personalization_uses_cache_without_llm(client, sample_card, monkeypatch, temp_db):
    """A cached personalization is served even when no LLM is configured."""
    import agents.personalize_agent as pa
    from db.database import get_conn

    monkeypatch.setattr(pa, "COMMANDCODE_API_KEY", "")
    # Sector must overlap the sample card's domain_tags (["Finance"]) or the
    # personalized feed correctly filters it out before personalization runs.
    client.put("/api/user/profile", json={**PROFILE, "sector_exposure": "Finance"})

    profile = pa.get_profile("test_user")
    phash = pa.profile_hash(profile)
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO card_personalizations
               (card_id, user_id, personal_impact, profile_hash) VALUES (?, ?, ?, ?)""",
            (sample_card, "test_user", "Your SIPs stay unaffected.", phash),
        )

    r = client.get("/api/cards/personalized", params={"user_id": "test_user"})
    assert r.status_code == 200
    card = next(c for c in r.json()["cards"] if c["id"] == sample_card)
    assert card["personal_impact"] == "Your SIPs stay unaffected."


def test_profile_edit_invalidates_cached_impact(client, sample_card, monkeypatch):
    """
    Stale personalization is worse than none. Changing the profile changes its hash,
    which must make the cached row a miss rather than serving the old text.
    """
    import agents.personalize_agent as pa
    from db.database import get_conn

    monkeypatch.setattr(pa, "COMMANDCODE_API_KEY", "")
    # Sector must overlap the sample card's domain_tags (["Finance"]) or the
    # personalized feed correctly filters it out before personalization runs.
    client.put("/api/user/profile", json={**PROFILE, "sector_exposure": "Finance"})

    old_hash = pa.profile_hash(pa.get_profile("test_user"))
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO card_personalizations
               (card_id, user_id, personal_impact, profile_hash) VALUES (?, ?, ?, ?)""",
            (sample_card, "test_user", "Stale text from the old profile.", old_hash),
        )

    client.put("/api/user/profile", json={**PROFILE, "city": "Mumbai"})
    new_hash = pa.profile_hash(pa.get_profile("test_user"))
    assert new_hash != old_hash
    assert pa.get_cached(sample_card, "test_user", new_hash) is None


# ---------------------------------------------------------------------------
# Market data, horizon, seed provenance
# ---------------------------------------------------------------------------

def test_market_data_is_flattened_for_display(client, temp_db):
    """The nested enrichment blob must arrive as a flat, renderable list."""
    import uuid
    from datetime import datetime
    from db.database import get_conn

    card_id = str(uuid.uuid4())
    blob = {
        "stocks": {"Google": {"symbol": "GOOGL", "price": 382.97,
                              "pct_change_1d": -1.21, "currency": "USD"}},
        "commodities": {"usd_inr": {"symbol": "USDINR=X", "price": 95.68,
                                    "pct_change_1d": -0.51, "currency": "INR"}},
        "macro_us": {"fed_funds_rate": 4.25},
        "_analysis": {"should": "be stripped"},
    }
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO cards (id, headline, summary_60w, confidence_badge,
                                  time_horizon, market_data, is_live, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (card_id, "Test", "Summary", "high", "long", json.dumps(blob), True,
             datetime.utcnow().isoformat()),
        )

    body = client.get(f"/api/cards/{card_id}").json()
    labels = {q["label"] for q in body["market_data"]}
    assert {"Google", "USD/INR", "Fed funds"} <= labels
    assert "_analysis" not in labels
    assert body["time_horizon"] == "long"


def test_malformed_market_data_does_not_break_card(client, temp_db):
    import uuid
    from datetime import datetime
    from db.database import get_conn

    card_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO cards (id, headline, summary_60w, confidence_badge,
                                  market_data, is_live, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (card_id, "Test", "Summary", "high", "not json at all", True,
             datetime.utcnow().isoformat()),
        )

    r = client.get(f"/api/cards/{card_id}")
    assert r.status_code == 200
    assert r.json()["market_data"] == []


def test_seed_cards_are_flagged(client, temp_db):
    """Invented demo news must be distinguishable from pipeline output."""
    from db.seed import seed_demo_cards

    seed_demo_cards()
    body = client.get("/api/cards").json()
    assert body["total"] > 0
    assert all(c["is_seed"] for c in body["cards"])


def test_seed_is_not_inserted_on_startup(client):
    """
    Startup must never inject fabricated news. This used to happen automatically
    whenever the live card count was zero.
    """
    assert client.get("/api/cards").json()["total"] == 0


def test_clear_seed_leaves_real_cards(client, sample_card, temp_db):
    from db.seed import seed_demo_cards, clear_seed_cards

    seed_demo_cards()
    assert client.get("/api/cards").json()["total"] > 1

    clear_seed_cards()
    body = client.get("/api/cards").json()
    assert body["total"] == 1
    assert body["cards"][0]["id"] == sample_card


def test_swipe_is_recorded(client, sample_card):
    r = client.post(
        f"/api/cards/{sample_card}/swipe",
        json={"direction": "right", "user_id": "test_user"},
    )
    assert r.status_code == 200

    from db.database import fetchall
    rows = fetchall("SELECT * FROM swipe_events WHERE card_id = ?", (sample_card,))
    assert len(rows) == 1
    assert rows[0]["direction"] == "right"


def test_swipe_rejects_bad_direction(client, sample_card):
    r = client.post(f"/api/cards/{sample_card}/swipe", json={"direction": "sideways"})
    assert r.status_code == 422
