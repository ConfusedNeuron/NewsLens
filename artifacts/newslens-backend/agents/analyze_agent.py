"""Analyze agent — LLM call #2: quantified winner/loser impact analysis."""
import uuid
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, fetchone, execute
from config.settings import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL, LLM_CALL_DELAY_SECONDS

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "analyze.txt"
SOP_PATH = Path(__file__).parent.parent / "config" / "sop.yaml"

VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_HORIZONS = {"immediate", "short", "long"}


def load_sop() -> dict:
    with open(SOP_PATH) as f:
        return yaml.safe_load(f)


def get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("AI_INTEGRATIONS_GEMINI_API_KEY not configured")
    import google.generativeai as genai
    client_options = {}
    if GEMINI_BASE_URL:
        client_options["api_endpoint"] = GEMINI_BASE_URL
    genai.configure(api_key=GEMINI_API_KEY, client_options=client_options if client_options else None)
    return genai.GenerativeModel(GEMINI_MODEL)


def get_domain_sop(sectors: list, sop: dict) -> str:
    if not sectors:
        return str(sop.get("Finance", {}))
    domain = sectors[0] if sectors else "Finance"
    domain_key = {"Tech": "Technology"}.get(domain, domain)
    sop_data = sop.get(domain_key, sop.get(domain, {}))
    return yaml.dump(sop_data)


def validate_analysis(data: dict) -> bool:
    required = {"summary_60w", "what_happened", "key_number", "winners", "losers",
                "india_angle", "usa_angle", "china_angle", "confidence", "time_horizon"}
    if not required.issubset(data.keys()):
        return False
    if not isinstance(data.get("winners"), list) or not isinstance(data.get("losers"), list):
        return False
    if data.get("confidence") not in VALID_CONFIDENCE:
        data["confidence"] = "medium"
    if data.get("time_horizon") not in VALID_HORIZONS:
        data["time_horizon"] = "short"
    return True


def load_prompt_template() -> str:
    with open(PROMPT_PATH) as f:
        return f.read()


def analyze_item(model, enriched: dict, sop: dict, user_profile: dict | None = None) -> dict | None:
    classified_id = enriched["classified_id"]
    classified = fetchone("SELECT * FROM classified_items WHERE id = ?", (classified_id,)) or {}
    extracted_id = classified.get("extracted_id")
    extracted = fetchone("SELECT * FROM extracted_items WHERE id = ?", (extracted_id,)) or {}
    clean_id = extracted.get("clean_id")
    clean = fetchone("SELECT clean_text FROM clean_items WHERE id = ?", (clean_id,)) or {}

    clean_text = (clean.get("clean_text") or "")[:3000]
    extracted_json = json.dumps({
        k: (json.loads(v) if isinstance(v, str) and v.startswith("[") else v)
        for k, v in extracted.items()
        if k not in ("id", "clean_id", "extracted_at", "status")
    }, indent=2)

    try:
        enrichment_json = json.dumps(json.loads(enriched.get("enrichment_json") or "{}"), indent=2)
    except Exception:
        enrichment_json = "{}"

    try:
        sectors = json.loads(extracted.get("sectors", "[]")) if isinstance(extracted.get("sectors"), str) else []
    except Exception:
        sectors = []

    domain_sop = get_domain_sop(sectors, sop)
    user_profile_str = json.dumps(user_profile, indent=2) if user_profile else "Not provided"

    prompt_template = load_prompt_template()
    prompt = (prompt_template
              .replace("{clean_text}", clean_text)
              .replace("{extracted_json}", extracted_json)
              .replace("{enrichment_json}", enrichment_json[:2000])
              .replace("{domain_sop}", domain_sop[:1000])
              .replace("{user_profile}", user_profile_str))

    for attempt in range(2):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
            )
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            if validate_analysis(data):
                return data
            logger.warning(f"Invalid analysis schema (attempt {attempt + 1})")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.error(f"LLM analyze failed: {e}")
            break
        time.sleep(LLM_CALL_DELAY_SECONDS)

    return None


def run() -> int:
    if not GEMINI_API_KEY:
        logger.warning("[Analyze] Skipping — AI_INTEGRATIONS_GEMINI_API_KEY not configured")
        return 0

    pending = fetchall("SELECT * FROM enriched_items WHERE status = 'pending' LIMIT 30")
    model = get_client()
    sop = load_sop()
    analyzed = 0

    for enriched in pending:
        result = analyze_item(model, enriched, sop)
        if result is None:
            execute("UPDATE enriched_items SET status = 'failed' WHERE id = ?", (enriched["id"],))
            continue

        with get_conn() as conn:
            conn.execute(
                "UPDATE enriched_items SET status = 'analyzed', enrichment_json = ? WHERE id = ?",
                (json.dumps({**json.loads(enriched.get("enrichment_json") or "{}"), "_analysis": result}), enriched["id"]),
            )

        with get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO enrichment_cache (key, value_json, cached_at, expires_at) VALUES (?, ?, ?, ?)",
                (f"analysis:{enriched['id']}", json.dumps(result), datetime.utcnow().isoformat(), None),
            )

        analyzed += 1
        time.sleep(LLM_CALL_DELAY_SECONDS)

    logger.info(f"[Analyze] Analyzed {analyzed} items")
    return analyzed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
