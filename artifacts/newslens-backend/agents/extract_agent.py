"""Extract agent — LLM call #1: structured extraction from clean text."""
import uuid
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, execute
from config.settings import GEMINI_API_KEY, GEMINI_MODEL, LLM_CALL_DELAY_SECONDS
from agents.gemini_client import build_client

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extract.txt"

REQUIRED_FIELDS = {"headline", "entities", "event_type", "numbers_mentioned",
                   "geography_primary", "sector", "time_horizon", "source_credibility", "confidence"}

VALID_EVENT_TYPES = {"monetary_policy", "earnings", "regulation", "conflict",
                     "discovery", "market_move", "policy", "other"}
VALID_GEOS = {"India", "USA", "China", "Global", "Continental"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_HORIZONS = {"immediate", "short_term", "long_term"}


def get_client():
    return build_client()


def load_prompt() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


def validate_extraction(data: dict) -> bool:
    if not REQUIRED_FIELDS.issubset(data.keys()):
        return False
    if not isinstance(data.get("entities"), dict):
        return False
    if data.get("event_type") not in VALID_EVENT_TYPES:
        data["event_type"] = "other"
    if data.get("geography_primary") not in VALID_GEOS:
        data["geography_primary"] = "Global"
    if data.get("confidence") not in VALID_CONFIDENCE:
        data["confidence"] = "medium"
    if data.get("time_horizon") not in VALID_HORIZONS:
        data["time_horizon"] = "short_term"
    return True


def extract_item(client, clean: dict) -> dict | None:
    from google.genai import types as genai_types
    prompt_template = load_prompt()
    text = clean["clean_text"][:4000]
    prompt = prompt_template.replace("{article_text}", text)

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            if not response.text:
                logger.warning(f"Empty response from LLM (attempt {attempt + 1})")
                continue
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            if validate_extraction(data):
                return data
            logger.warning(f"Invalid extraction schema (attempt {attempt + 1})")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            break
        time.sleep(LLM_CALL_DELAY_SECONDS)

    return None


def run() -> int:
    if not GEMINI_API_KEY:
        logger.warning("[Extract] Skipping — AI_INTEGRATIONS_GEMINI_API_KEY not configured")
        return 0

    pending = fetchall("SELECT * FROM clean_items WHERE status = 'pending' LIMIT 50")
    client = get_client()
    extracted = 0

    for clean in pending:
        result = extract_item(client, clean)
        if result is None:
            execute("UPDATE clean_items SET status = 'failed' WHERE id = ?", (clean["id"],))
            continue

        extracted_id = str(uuid.uuid4())
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO extracted_items
                   (id, clean_id, headline, entities_json, event_type, numbers_mentioned,
                    geography_primary, sectors, time_horizon, source_credibility, confidence, extracted_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    extracted_id,
                    clean["id"],
                    result.get("headline", ""),
                    json.dumps(result.get("entities", {})),
                    result.get("event_type", "other"),
                    json.dumps(result.get("numbers_mentioned", [])),
                    result.get("geography_primary", "Global"),
                    json.dumps(result.get("sector", [])),
                    result.get("time_horizon", "short_term"),
                    result.get("source_credibility", "medium"),
                    result.get("confidence", "medium"),
                    datetime.utcnow().isoformat(),
                    "pending",
                ),
            )
            conn.execute("UPDATE clean_items SET status = 'extracted' WHERE id = ?", (clean["id"],))

        extracted += 1
        time.sleep(LLM_CALL_DELAY_SECONDS)

    logger.info(f"[Extract] Extracted {extracted} of {len(pending)} items")
    return extracted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
