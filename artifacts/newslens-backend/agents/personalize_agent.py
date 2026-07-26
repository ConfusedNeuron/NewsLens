"""
Personalize agent — turns a global card into "what this means for you".

Design note (this is the architecture decision the audits kept asking for)
─────────────────────────────────────────────────────────────────────────
The analyze station produces ONE card per news event, shared by every user. It does
not know who is reading. Personalization happens here instead, at read time:

    GET /cards/personalized?user_id=X
        → for each card, look for a cached (card_id, user_id) row
        → on miss, one cheap LLM call fills it, and the result is cached forever

Why not personalize inside the analyze station (the obvious shortcut)?
  * The card is shared. Writing one user's `personal_impact` into `cards` makes the
    card wrong for everyone else.
  * Cost would be O(cards x all users) at generation time, paid whether or not anyone
    ever reads the card, and using the EXPENSIVE analyze prompt (~1200 output tokens).
  * Profiles change. A baked-in impact silently goes stale.

Here the cost is O(cards x ACTIVE users), paid lazily, using a ~120-token prompt. A
registered user who never opens the app costs nothing. A profile edit changes the
profile hash, which invalidates exactly that user's rows and nobody else's.

This module finally uses prompts/personal_impact.txt, which existed in the repo from
the beginning and was read by no code until 2026-07-26.
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchone
from config.settings import COMMANDCODE_API_KEY
from agents.llm_client import get_llm_client, call_llm

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "personal_impact.txt"

# Personalization is a short, cheap call — two sentences. Keep the ceiling low so a
# runaway model can't turn a read-time path into an expensive one.
MAX_TOKENS = 220
TEMPERATURE = 0.4

PROFILE_FIELDS = (
    "income_type",
    "sector_exposure",
    "investment_profile",
    "city",
    "companies_of_interest",
)


def profile_hash(profile: dict) -> str:
    """
    Stable fingerprint of the profile fields that actually affect the output.

    Only the five prompt inputs are hashed — updating `updated_at` alone must not
    invalidate every cached personalization the user has.
    """
    payload = json.dumps(
        {k: (profile.get(k) or "") for k in PROFILE_FIELDS},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def get_profile(user_id: str) -> Optional[dict]:
    return fetchone("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))


def get_cached(card_id: str, user_id: str, phash: str) -> Optional[str]:
    row = fetchone(
        """SELECT personal_impact, profile_hash FROM card_personalizations
           WHERE card_id = ? AND user_id = ?""",
        (card_id, user_id),
    )
    if not row:
        return None
    if row.get("profile_hash") != phash:
        # Profile changed since this was written — treat as a miss and regenerate.
        return None
    return row.get("personal_impact")


def put_cached(card_id: str, user_id: str, phash: str, text: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO card_personalizations
               (card_id, user_id, personal_impact, profile_hash)
               VALUES (?, ?, ?, ?)""",
            (card_id, user_id, text, phash),
        )


def build_prompt(card: dict, profile: dict) -> str:
    """Render personal_impact.txt with this card's analysis and this user's profile."""
    analysis = {
        "what_happened": card.get("what_happened") or card.get("headline") or "",
        "summary_60w": card.get("summary_60w") or "",
        "key_number": card.get("key_number") or "",
        "winners": _safe_list(card.get("winners_json")),
        "losers": _safe_list(card.get("losers_json")),
        "india_angle": card.get("india_angle") or "",
    }

    with open(PROMPT_PATH) as f:
        template = f.read()

    return (
        template
        .replace("{analysis_json}", json.dumps(analysis, indent=2)[:2000])
        .replace("{income_type}", profile.get("income_type") or "Not specified")
        .replace("{sector_exposure}", profile.get("sector_exposure") or "Not specified")
        .replace("{investment_profile}", profile.get("investment_profile") or "Not specified")
        .replace("{city}", profile.get("city") or "Not specified")
        .replace("{companies_of_interest}", profile.get("companies_of_interest") or "None")
    )


def _safe_list(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return []


def personalize_card(client, card: dict, profile: dict, phash: str) -> Optional[str]:
    """One LLM call. Returns the impact text, or None if the call failed."""
    try:
        text = call_llm(
            client,
            build_prompt(card, profile),
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
    except Exception as e:
        logger.warning(f"[Personalize] LLM call failed for card {card.get('id')}: {e}")
        return None

    text = (text or "").strip()
    if not text:
        return None

    put_cached(card["id"], profile["user_id"], phash, text)
    return text


def personalize_cards(cards: list[dict], user_id: str) -> dict[str, str]:
    """
    Return {card_id: personal_impact} for the given cards and user.

    Serves cache hits for free. Generates misses one at a time. Degrades gracefully
    in every failure mode — no profile, no API key, LLM down — by returning whatever
    it has. A missing personal impact must never break the feed.
    """
    if not cards:
        return {}

    profile = get_profile(user_id)
    if not profile:
        logger.debug(f"[Personalize] No profile for {user_id} — skipping.")
        return {}

    phash = profile_hash(profile)
    out: dict[str, str] = {}
    misses: list[dict] = []

    for card in cards:
        cached = get_cached(card["id"], user_id, phash)
        if cached:
            out[card["id"]] = cached
        else:
            misses.append(card)

    if not misses:
        return out

    if not COMMANDCODE_API_KEY:
        logger.warning(
            f"[Personalize] {len(misses)} cards need personalization but "
            "COMMANDCODE_API_KEY is not set — serving cached entries only."
        )
        return out

    try:
        client = get_llm_client()
    except Exception as e:
        logger.warning(f"[Personalize] Could not create LLM client: {e}")
        return out

    generated = 0
    for card in misses:
        text = personalize_card(client, card, profile, phash)
        if text:
            out[card["id"]] = text
            generated += 1

    logger.info(
        f"[Personalize] user={user_id} cached={len(out) - generated} generated={generated}"
    )
    return out
