"""Quality gate — rules-based filter before cards go live."""
import json
import logging
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, execute

logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    return len((text or "").split())


def evaluate_card(card: dict) -> str:
    """Returns: 'approve' | 'hold' | 'discard'"""
    confidence = card.get("confidence_badge", "medium")
    summary = card.get("summary_60w", "") or ""
    winners_raw = card.get("winners_json", "[]") or "[]"
    losers_raw = card.get("losers_json", "[]") or "[]"
    headline = card.get("headline", "") or ""
    personal_impact = card.get("personal_impact", "") or ""
    key_number = card.get("key_number", "") or ""

    try:
        winners = json.loads(winners_raw)
        losers = json.loads(losers_raw)
    except Exception:
        winners, losers = [], []

    try:
        classified_row = None
        if card.get("enriched_id"):
            from db.database import fetchone
            enriched = fetchone("SELECT classified_id FROM enriched_items WHERE id = ?", (card["enriched_id"],))
            if enriched:
                classified_row = fetchone("SELECT * FROM classified_items WHERE id = ?", (enriched["classified_id"],))
    except Exception:
        classified_row = None

    is_cross_domain = classified_row.get("is_cross_domain", False) if classified_row else False

    # Auto-discard conditions
    if confidence == "low" and not key_number and len(winners) == 0 and len(losers) == 0:
        return "discard"
    if count_words(summary) < 20 and count_words(headline) < 5:
        return "discard"
    if len(winners) == 0 and len(losers) == 0:
        return "discard"

    # Hold conditions — only hold cross-domain medium-confidence cards (rare edge case)
    if is_cross_domain and confidence == "medium" and count_words(summary) < 40:
        return "hold"

    return "approve"


def run() -> dict:
    unreviewed = fetchall(
        "SELECT * FROM cards WHERE is_live = FALSE AND confidence_badge IS NOT NULL"
    )
    approved = 0
    held = 0
    discarded = 0

    for card in unreviewed:
        verdict = evaluate_card(card)

        if verdict == "approve":
            execute("UPDATE cards SET is_live = TRUE WHERE id = ?", (card["id"],))
            approved += 1
        elif verdict == "hold":
            # Hold cards remain is_live = FALSE until manually reviewed or re-processed
            held += 1
        else:
            execute("DELETE FROM cards WHERE id = ?", (card["id"],))
            discarded += 1

    logger.info(f"[QualityGate] Approved={approved}, Held={held}, Discarded={discarded}")
    return {"approved": approved, "held": held, "discarded": discarded}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
