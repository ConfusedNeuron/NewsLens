"""Classify agent — deterministic rule engine for tagging and scoring."""
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, execute
from config.settings import SOURCE_CREDIBILITY_WEIGHTS, IMPORTANCE_SCORE_THRESHOLD

logger = logging.getLogger(__name__)


def compute_importance_score(extracted: dict) -> float:
    try:
        entities = json.loads(extracted.get("entities_json", "{}")) if isinstance(extracted.get("entities_json"), str) else {}
    except Exception:
        entities = {}

    try:
        sectors = json.loads(extracted.get("sectors", "[]")) if isinstance(extracted.get("sectors"), str) else []
        if isinstance(sectors, str):
            sectors = [sectors]
    except Exception:
        sectors = []

    credibility = extracted.get("source_credibility", "medium")
    cred_weight = SOURCE_CREDIBILITY_WEIGHTS.get(credibility, 0.6)

    company_count = len(entities.get("companies", []))
    sector_count = len(sectors)
    is_cross_domain = sector_count > 1
    cross_domain_bonus = 1.0 if is_cross_domain else 0.0

    score = (
        cred_weight * 0.4
        + min(company_count, 5) * 0.02
        + min(sector_count, 4) * 0.2
        + cross_domain_bonus * 0.3
    )
    return min(score, 1.0)


def parse_domain_tags(sectors_raw) -> list[str]:
    valid = {"Finance", "Tech", "Geopolitics", "Environment"}
    if isinstance(sectors_raw, str):
        try:
            sectors = json.loads(sectors_raw)
        except Exception:
            sectors = [sectors_raw]
    else:
        sectors = sectors_raw or []
    return [s for s in sectors if s in valid]


def parse_geo_tags(extracted: dict) -> list[str]:
    geo_primary = extracted.get("geography_primary", "Global")
    try:
        entities = json.loads(extracted.get("entities_json", "{}")) if isinstance(extracted.get("entities_json"), str) else {}
    except Exception:
        entities = {}
    countries = entities.get("countries", [])

    geo_tags = set()
    if geo_primary:
        geo_tags.add(geo_primary)

    country_to_geo = {
        "India": "India", "USA": "USA", "United States": "USA",
        "America": "USA", "China": "China", "PRC": "China",
    }
    for country in countries:
        tag = country_to_geo.get(country)
        if tag:
            geo_tags.add(tag)

    if not geo_tags:
        geo_tags.add("Global")

    return list(geo_tags)


def run() -> int:
    pending = fetchall("SELECT * FROM extracted_items WHERE status = 'pending'")
    classified = 0

    for item in pending:
        score = compute_importance_score(item)
        execute("UPDATE extracted_items SET status = 'classified' WHERE id = ?", (item["id"],))

        if score < IMPORTANCE_SCORE_THRESHOLD:
            logger.debug(f"Discarding low-score item {item['id']} (score={score:.2f})")
            continue

        try:
            sectors = json.loads(item.get("sectors", "[]")) if isinstance(item.get("sectors"), str) else []
        except Exception:
            sectors = []

        domain_tags = parse_domain_tags(sectors)
        geo_tags = parse_geo_tags(item)
        is_cross_domain = len(domain_tags) > 1

        classified_id = str(uuid.uuid4())
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO classified_items
                   (id, extracted_id, domain_tags, geo_tags, importance_score, is_cross_domain, classified_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    classified_id,
                    item["id"],
                    json.dumps(domain_tags),
                    json.dumps(geo_tags),
                    score,
                    is_cross_domain,
                    datetime.utcnow().isoformat(),
                    "pending",
                ),
            )
        classified += 1

    logger.info(f"[Classify] Classified {classified} of {len(pending)} items")
    return classified


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
