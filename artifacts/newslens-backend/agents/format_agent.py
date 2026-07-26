"""Format agent — maps analysis output to card schema."""
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, fetchone, execute

logger = logging.getLogger(__name__)


#: extract_agent and analyze_agent use different spellings for the same concept.
#: The API and UI speak only the right-hand side.
_HORIZON_ALIASES = {
    "immediate": "immediate",
    "short": "short",
    "short_term": "short",
    "near_term": "short",
    "long": "long",
    "long_term": "long",
}


def _normalize_horizon(raw) -> str:
    return _HORIZON_ALIASES.get(str(raw or "").strip().lower(), "short")


def format_winner_loser(items: list) -> str:
    if not items:
        return ""
    parts = []
    for item in items[:2]:
        who = item.get("who", "")
        why = item.get("why", "")
        magnitude = item.get("magnitude", "")
        parts.append(f"{who}: {why} ({magnitude})")
    return " | ".join(parts)


def map_to_card(enriched: dict, classified: dict, extracted: dict, clean: dict) -> dict | None:
    enrichment_raw = enriched.get("enrichment_json") or "{}"
    try:
        enrichment = json.loads(enrichment_raw)
    except Exception:
        enrichment = {}

    analysis = enrichment.get("_analysis")
    if not analysis:
        return None

    try:
        domain_tags = json.loads(classified.get("domain_tags", "[]")) if isinstance(classified.get("domain_tags"), str) else []
    except Exception:
        domain_tags = []

    try:
        geo_tags = json.loads(classified.get("geo_tags", "[]")) if isinstance(classified.get("geo_tags"), str) else []
    except Exception:
        geo_tags = []

    raw_item = None
    if clean.get("raw_id"):
        raw_item = fetchone("SELECT * FROM raw_items WHERE id = ?", (clean["raw_id"],))

    source_name = ""
    source_url = ""
    if raw_item:
        source_name = raw_item.get("source_name", "")
        source_url = raw_item.get("url", "")

    winners = analysis.get("winners", [])
    losers = analysis.get("losers", [])

    # Market data actually reaching the card.
    #
    # Enrichment was fetched, injected into the analyze prompt, and then thrown away —
    # no card field, no API field, nothing on screen. The numbers only ever surfaced
    # as unattributed prose inside india_angle. Everything except the private
    # "_analysis" key is now carried through so the UI can show what the analysis
    # was actually looking at.
    market_data = {k: v for k, v in enrichment.items() if k != "_analysis"}

    # time_horizon is produced by both stations but the vocabularies differ:
    # extract emits short_term/long_term, analyze emits short/long. Normalise here
    # so exactly one spelling ever leaves the backend.
    horizon = _normalize_horizon(
        analysis.get("time_horizon") or extracted.get("time_horizon")
    )

    card = {
        "id": str(uuid.uuid4()),
        "enriched_id": enriched["id"],
        "time_horizon": horizon,
        "market_data": json.dumps(market_data) if market_data else None,
        "headline": analysis.get("what_happened") or extracted.get("headline") or "",
        "summary_60w": analysis.get("summary_60w", ""),
        "what_happened": analysis.get("what_happened", ""),
        "key_number": analysis.get("key_number", ""),
        "winners_json": json.dumps(winners),
        "losers_json": json.dumps(losers),
        "india_angle": analysis.get("india_angle", ""),
        "usa_angle": analysis.get("usa_angle", ""),
        "china_angle": analysis.get("china_angle", ""),
        "personal_impact": analysis.get("personal_impact", ""),
        "domain_tags": json.dumps(domain_tags),
        "geo_tags": json.dumps(geo_tags),
        "confidence_badge": analysis.get("confidence", "medium"),
        "source_name": source_name,
        "source_url": source_url,
        "is_live": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    return card


def run() -> int:
    pending = fetchall("SELECT * FROM enriched_items WHERE status = 'analyzed'")
    formatted = 0

    for enriched in pending:
        classified = fetchone(
            "SELECT * FROM classified_items WHERE id = ?", (enriched["classified_id"],)
        ) or {}
        extracted_id = classified.get("extracted_id")
        extracted = fetchone("SELECT * FROM extracted_items WHERE id = ?", (extracted_id,)) or {} if extracted_id else {}
        clean_id = extracted.get("clean_id")
        clean = fetchone("SELECT * FROM clean_items WHERE id = ?", (clean_id,)) or {} if clean_id else {}

        card = map_to_card(enriched, classified, extracted, clean)
        if card is None:
            execute("UPDATE enriched_items SET status = 'format_failed' WHERE id = ?", (enriched["id"],))
            continue

        with get_conn() as conn:
            conn.execute(
                """INSERT INTO cards
                   (id, enriched_id, headline, summary_60w, what_happened, key_number,
                    winners_json, losers_json, india_angle, usa_angle, china_angle, personal_impact,
                    domain_tags, geo_tags, confidence_badge, time_horizon, market_data,
                    source_name, source_url, is_live, is_seed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    card["id"], card["enriched_id"], card["headline"], card["summary_60w"],
                    card["what_happened"], card["key_number"], card["winners_json"],
                    card["losers_json"], card["india_angle"], card["usa_angle"],
                    card["china_angle"], card["personal_impact"], card["domain_tags"],
                    card["geo_tags"], card["confidence_badge"], card["time_horizon"],
                    card["market_data"], card["source_name"],
                    card["source_url"], card["is_live"], False, card["created_at"],
                ),
            )
            conn.execute(
                "UPDATE enriched_items SET status = 'formatted' WHERE id = ?", (enriched["id"],)
            )
        formatted += 1

    logger.info(f"[Format] Created {formatted} cards")
    return formatted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
