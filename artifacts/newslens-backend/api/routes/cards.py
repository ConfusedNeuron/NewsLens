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
from api.models import (
    CardResponse, CardListResponse, CardAngles, CardTags, CardSource,
    Winner, MarketQuote, SwipeRequest,
)
from agents.personalize_agent import personalize_cards

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


def _to_impact(item: dict) -> Winner:
    """
    Build a Winner/Loser from a stored analysis dict.

    Cards written before 2026-07-26 have no `magnitude_source` key. They are served
    as "estimate", which is the honest reading: they were produced under a prompt
    that explicitly permitted invented figures behind an "est." prefix.
    """
    source = str(item.get("magnitude_source", "")).strip().lower()
    if source not in ("data", "estimate"):
        source = "estimate"
    return Winner(
        who=item.get("who", ""),
        why=item.get("why", ""),
        magnitude=item.get("magnitude", ""),
        magnitude_source=source,
    )


#: Display names for the instruments the enrich agent tracks.
_QUOTE_LABELS = {
    "crude_oil": "Crude",
    "gold": "Gold",
    "silver": "Silver",
    "usd_inr": "USD/INR",
    "usd_cny": "USD/CNY",
    "fed_funds_rate": "Fed funds",
    "us_cpi": "US CPI",
    "us_gdp": "US GDP",
    "us_unemployment": "US unemployment",
}


def _flatten_market_data(raw) -> list[MarketQuote]:
    """
    Turn the stored enrichment blob into a flat, display-ready list.

    The blob is nested by category (stocks / commodities / macro_us) and every
    category has a slightly different shape. The UI should not have to know that.
    Anything unparseable yields an empty list — market data is decoration, and a
    malformed payload must never break a card.
    """
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    if not isinstance(data, dict):
        return []

    quotes: list[MarketQuote] = []
    for group in ("stocks", "commodities"):
        for name, q in (data.get(group) or {}).items():
            if not isinstance(q, dict):
                continue
            quotes.append(MarketQuote(
                label=_QUOTE_LABELS.get(name, name),
                symbol=q.get("symbol"),
                price=q.get("price"),
                pct_change_1d=q.get("pct_change_1d"),
                currency=q.get("currency"),
            ))

    for name, value in (data.get("macro_us") or {}).items():
        if isinstance(value, dict):
            price = value.get("value", value.get("price"))
        else:
            price = value
        try:
            price = float(price) if price is not None else None
        except (TypeError, ValueError):
            price = None
        quotes.append(MarketQuote(label=_QUOTE_LABELS.get(name, name), price=price))

    return quotes


def _row_to_card(row: dict) -> CardResponse:
    winners_raw = _parse_json_list(row.get("winners_json"))
    losers_raw = _parse_json_list(row.get("losers_json"))
    domain_tags = _parse_json_list(row.get("domain_tags"))
    geo_tags = _parse_json_list(row.get("geo_tags"))

    winners = [_to_impact(w) for w in winners_raw if isinstance(w, dict)]
    losers = [_to_impact(l) for l in losers_raw if isinstance(l, dict)]

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
        time_horizon=row.get("time_horizon"),
        market_data=_flatten_market_data(row.get("market_data")),
        source=CardSource(
            name=row.get("source_name") or "",
            url=row.get("source_url") or "",
        ),
        is_seed=bool(row.get("is_seed")),
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

    # Match ANY of the user's declared sectors, not just the first one.
    # This previously read sectors[0] and silently ignored the rest, so a user who
    # selected "IT / Software, Banking & Finance" only ever saw IT cards.
    sectors = [s.strip() for s in (profile.get("sector_exposure") or "").split(",") if s.strip()]
    if sectors:
        conditions.append("(" + " OR ".join(["domain_tags LIKE ?"] * len(sectors)) + ")")
        params.extend(f"%{s}%" for s in sectors)

    if domain and domain.lower() != "all":
        conditions.append("domain_tags LIKE ?")
        params.append(f"%{domain}%")

    if geo and geo.lower() != "global":
        conditions.append("geo_tags LIKE ?")
        params.append(f"%{geo}%")

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * limit

    total_row = fetchone(f"SELECT COUNT(*) as cnt FROM cards WHERE {where_clause}", tuple(params))
    total = total_row["cnt"] if total_row else 0

    rows = fetchall(
        f"SELECT * FROM cards WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params + [limit, offset]),
    )

    # Read-time personalization: cache hits are free, misses cost one short LLM call
    # each and are then cached forever (see agents/personalize_agent.py).
    # This is what actually fills `personal_impact`; the analyze station leaves it
    # empty on purpose because cards are global and shared between users.
    impacts = {}
    try:
        impacts = personalize_cards(rows, user_id)
    except Exception as e:
        # Personalization is an enhancement, never a dependency. A failure here
        # must degrade to a normal card feed, not a 500.
        logger.warning(f"Personalization failed for user {user_id}: {e}")

    cards = []
    for r in rows:
        card = _row_to_card(r)
        if impacts.get(r["id"]):
            card.personal_impact = impacts[r["id"]]
        cards.append(card)

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
