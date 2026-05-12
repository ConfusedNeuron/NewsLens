"""Card API routes."""
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import fetchall, fetchone, execute
from api.models import CardResponse, CardListResponse, CardAngles, CardTags, CardSource, Winner, SwipeRequest

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_json_list(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return []


def _row_to_card(row: dict) -> CardResponse:
    winners_raw = _parse_json_list(row.get("winners_json"))
    losers_raw = _parse_json_list(row.get("losers_json"))
    domain_tags = _parse_json_list(row.get("domain_tags"))
    geo_tags = _parse_json_list(row.get("geo_tags"))

    winners = []
    for w in winners_raw:
        if isinstance(w, dict):
            winners.append(Winner(who=w.get("who", ""), why=w.get("why", ""), magnitude=w.get("magnitude", "")))

    losers = []
    for l in losers_raw:
        if isinstance(l, dict):
            losers.append(Winner(who=l.get("who", ""), why=l.get("why", ""), magnitude=l.get("magnitude", "")))

    return CardResponse(
        id=row["id"],
        headline=row.get("headline") or "",
        summary=row.get("summary_60w") or "",
        key_number=row.get("key_number"),
        winners=winners,
        losers=losers,
        personal_impact=row.get("personal_impact"),
        angles=CardAngles(
            india=row.get("india_angle"),
            usa=row.get("usa_angle"),
            china=row.get("china_angle"),
        ),
        tags=CardTags(domain=domain_tags, geo=geo_tags),
        confidence=row.get("confidence_badge") or "medium",
        source=CardSource(
            name=row.get("source_name") or "",
            url=row.get("source_url") or "",
        ),
        created_at=row.get("created_at") or datetime.utcnow().isoformat(),
    )


@router.get("/cards", response_model=CardListResponse)
def get_cards(
    domain: Optional[str] = Query(None),
    geo: Optional[str] = Query(None),
    confidence: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    conditions = ["is_live = TRUE"]
    params = []

    if domain and domain.lower() != "all":
        conditions.append("domain_tags LIKE ?")
        params.append(f"%{domain}%")

    if geo and geo.lower() != "global":
        conditions.append("geo_tags LIKE ?")
        params.append(f"%{geo}%")

    if confidence:
        conditions.append("confidence_badge = ?")
        params.append(confidence)

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit

    total_row = fetchone(f"SELECT COUNT(*) as cnt FROM cards WHERE {where_clause}", tuple(params))
    total = total_row["cnt"] if total_row else 0

    rows = fetchall(
        f"SELECT * FROM cards WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params + [limit, offset]),
    )

    cards = [_row_to_card(r) for r in rows]
    return CardListResponse(
        cards=cards,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/cards/personalized", response_model=CardListResponse)
def get_personalized_cards(
    user_id: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    geo: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    profile = fetchone("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    conditions = ["is_live = TRUE"]
    params = []

    if profile.get("sector_exposure"):
        sectors = [s.strip() for s in profile["sector_exposure"].split(",")]
        if sectors:
            conditions.append(f"domain_tags LIKE ?")
            params.append(f"%{sectors[0]}%")

    if domain and domain.lower() != "all":
        conditions.append("domain_tags LIKE ?")
        params.append(f"%{domain}%")

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit

    total_row = fetchone(f"SELECT COUNT(*) as cnt FROM cards WHERE {where_clause}", tuple(params))
    total = total_row["cnt"] if total_row else 0

    rows = fetchall(
        f"SELECT * FROM cards WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params + [limit, offset]),
    )

    cards = [_row_to_card(r) for r in rows]
    return CardListResponse(cards=cards, total=total, page=page, limit=limit, has_more=(offset + limit) < total)


@router.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: str):
    row = fetchone("SELECT * FROM cards WHERE id = ?", (card_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Card not found")
    return _row_to_card(row)


@router.post("/cards/{card_id}/swipe")
def record_swipe(card_id: str, body: SwipeRequest):
    card = fetchone("SELECT id FROM cards WHERE id = ?", (card_id,))
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    user_id = body.user_id or "anonymous"
    event_id = str(uuid.uuid4())
    execute(
        """INSERT INTO swipe_events (id, user_id, card_id, direction, swiped_at)
           VALUES (?, ?, ?, ?, ?)""",
        (event_id, user_id, card_id, body.direction, datetime.utcnow().isoformat()),
    )
    return {"ok": True, "direction": body.direction}
