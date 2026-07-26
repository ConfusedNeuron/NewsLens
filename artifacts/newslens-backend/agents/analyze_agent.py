"""Analyze agent — LLM call #2: quantified winner/loser impact analysis."""
import uuid
import json
import time
import logging
from datetime import datetime
from pathlib import Path

import yaml
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, fetchone, execute
from config.settings import COMMANDCODE_API_KEY, LLM_CALL_DELAY_SECONDS
from agents.llm_client import (
    get_llm_client,
    call_llm,
    validate_analyze_input,
    InputValidationError,
)

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "analyze.txt"
SOP_PATH    = Path(__file__).parent.parent / "config" / "sop.yaml"

VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_HORIZONS   = {"immediate", "short", "long"}
VALID_MAG_SOURCE = {"data", "estimate"}


def load_sop() -> dict:
    with open(SOP_PATH) as f:
        return yaml.safe_load(f)


def get_domain_sop(sectors: list, sop: dict) -> str:
    if not sectors:
        return str(sop.get("Finance", {}))
    domain     = sectors[0]
    domain_key = {"Tech": "Technology"}.get(domain, domain)
    sop_data   = sop.get(domain_key, sop.get(domain, {}))
    return yaml.dump(sop_data)


def validate_analysis_output(data: dict) -> bool:
    """Validate LLM output schema — called AFTER the API response."""
    required = {"summary_60w", "what_happened", "key_number", "winners", "losers",
                "india_angle", "usa_angle", "china_angle", "confidence", "time_horizon"}
    if not required.issubset(data.keys()):
        missing = required - set(data.keys())
        logger.warning(f"[Analyze] Output missing fields: {missing}")
        return False
    if not isinstance(data.get("winners"), list) or not isinstance(data.get("losers"), list):
        logger.warning("[Analyze] winners/losers are not lists.")
        return False
    # Coerce invalid enum values
    if data.get("confidence") not in VALID_CONFIDENCE:
        data["confidence"] = "medium"
    if data.get("time_horizon") not in VALID_HORIZONS:
        data["time_horizon"] = "short"

    # Magnitude provenance — fail SAFE, not open.
    #
    # Every winner/loser must declare whether its number came from the enrichment
    # payload ("data") or from the model's own background knowledge ("estimate").
    # Anything missing, malformed, or unrecognised is demoted to "estimate": the
    # failure mode we must never have is an inference being presented as sourced.
    # (Before 2026-07-26 the prompt actively invited invented figures behind an
    # "est." prefix, and the UI had no way to distinguish them.)
    for bucket in ("winners", "losers"):
        for item in data.get(bucket, []):
            if not isinstance(item, dict):
                continue
            source = str(item.get("magnitude_source", "")).strip().lower()
            if source not in VALID_MAG_SOURCE:
                if source:
                    logger.debug(f"[Analyze] Unrecognised magnitude_source {source!r} — demoting to 'estimate'.")
                source = "estimate"
            item["magnitude_source"] = source
    return True


def strip_json_fence(content: str) -> str:
    if content.startswith("```"):
        parts = content.split("```")
        content = parts[1]
        if content.startswith("json"):
            content = content[4:]
    return content.strip()


def _build_extracted_dict(extracted: dict) -> dict:
    """Return a clean dict from extracted_items row for validation and prompt."""
    result = {}
    for k, v in extracted.items():
        if k in ("id", "clean_id", "extracted_at", "status"):
            continue
        if isinstance(v, str) and v.startswith(("[", "{")):
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v
        else:
            result[k] = v
    return result


def analyze_item(
    client,
    enriched: dict,
    sop: dict,
    user_profile: Optional[dict] = None,
) -> Optional[dict]:
    # ── Fetch chain: enriched → classified → extracted → clean ───────────
    classified = fetchone(
        "SELECT * FROM classified_items WHERE id = ?",
        (enriched["classified_id"],),
    ) or {}
    extracted_row = fetchone(
        "SELECT * FROM extracted_items WHERE id = ?",
        (classified.get("extracted_id"),),
    ) or {}
    clean = fetchone(
        "SELECT clean_text FROM clean_items WHERE id = ?",
        (extracted_row.get("clean_id"),),
    ) or {}

    clean_text   = (clean.get("clean_text") or "")[:3000]
    extracted    = _build_extracted_dict(extracted_row)
    try:
        enrichment_json = json.dumps(
            json.loads(enriched.get("enrichment_json") or "{}"), indent=2
        )
    except Exception:
        enrichment_json = "{}"

    # ── INPUT VALIDATION (before any retry) ──────────────────────────────
    # Raises InputValidationError if data is bad — caller handles skip.
    # This runs ONCE; the retry loop below is only for transient LLM errors.
    # ─────────────────────────────────────────────────────────────────────
    validate_analyze_input(clean_text, extracted, enrichment_json)

    # ── Build prompt ──────────────────────────────────────────────────────
    try:
        sectors = json.loads(extracted_row.get("sectors", "[]")) \
            if isinstance(extracted_row.get("sectors"), str) else []
    except Exception:
        sectors = []

    domain_sop       = get_domain_sop(sectors, sop)
    user_profile_str = json.dumps(user_profile, indent=2) if user_profile else "Not provided"

    with open(PROMPT_PATH) as f:
        prompt_template = f.read()

    prompt = (
        prompt_template
        .replace("{clean_text}",     clean_text)
        .replace("{extracted_json}", json.dumps(extracted, indent=2))
        .replace("{enrichment_json}", enrichment_json[:2000])
        .replace("{domain_sop}",     domain_sop[:1000])
        .replace("{user_profile}",   user_profile_str)
    )

    # ── RETRY LOOP (only for transient LLM / network failures) ───────────
    for attempt in range(2):
        try:
            content = call_llm(client, prompt, max_tokens=1200, temperature=0.3)
            content = strip_json_fence(content)
            data    = json.loads(content)
            if validate_analysis_output(data):
                return data
            logger.warning(f"[Analyze] Invalid schema on attempt {attempt + 1} — retrying.")
        except json.JSONDecodeError as e:
            logger.warning(f"[Analyze] JSON parse error (attempt {attempt + 1}): {e}")
        except Exception as e:
            logger.error(f"[Analyze] LLM call failed (attempt {attempt + 1}): {e}")
            break

        if attempt == 0:
            time.sleep(LLM_CALL_DELAY_SECONDS)

    return None


def run() -> int:
    if not COMMANDCODE_API_KEY:
        logger.warning(
            "[Analyze] Skipping — COMMANDCODE_API_KEY not set. "
            "Add it to your .env file."
        )
        return 0

    pending = fetchall(
        "SELECT * FROM enriched_items WHERE status = 'pending' LIMIT 30"
    )
    client   = get_llm_client()
    sop      = load_sop()
    analyzed = 0

    for enriched in pending:
        # ── Fetch chain for validation ────────────────────────────────────
        classified = fetchone(
            "SELECT * FROM classified_items WHERE id = ?",
            (enriched["classified_id"],),
        ) or {}
        extracted_row = fetchone(
            "SELECT * FROM extracted_items WHERE id = ?",
            (classified.get("extracted_id"),),
        ) or {}
        clean = fetchone(
            "SELECT clean_text FROM clean_items WHERE id = ?",
            (extracted_row.get("clean_id"),),
        ) or {}

        clean_text   = (clean.get("clean_text") or "")[:3000]
        extracted    = _build_extracted_dict(extracted_row)
        enrichment_json = "{}"
        try:
            enrichment_json = json.dumps(
                json.loads(enriched.get("enrichment_json") or "{}"), indent=2
            )
        except Exception:
            pass

        # ── Pre-flight validation ─────────────────────────────────────────
        try:
            validate_analyze_input(clean_text, extracted, enrichment_json)
        except InputValidationError as e:
            logger.warning(f"[Analyze] Skipping enriched item {enriched['id']}: {e}")
            execute(
                "UPDATE enriched_items SET status = 'skipped' WHERE id = ?",
                (enriched["id"],),
            )
            continue

        result = analyze_item(client, enriched, sop)
        if result is None:
            execute(
                "UPDATE enriched_items SET status = 'failed' WHERE id = ?",
                (enriched["id"],),
            )
            continue

        with get_conn() as conn:
            conn.execute(
                "UPDATE enriched_items SET status = 'analyzed', enrichment_json = ? WHERE id = ?",
                (
                    json.dumps({
                        **json.loads(enriched.get("enrichment_json") or "{}"),
                        "_analysis": result,
                    }),
                    enriched["id"],
                ),
            )
            conn.execute(
                """INSERT OR REPLACE INTO enrichment_cache
                   (key, value_json, cached_at, expires_at) VALUES (?, ?, ?, ?)""",
                (
                    f"analysis:{enriched['id']}",
                    json.dumps(result),
                    datetime.utcnow().isoformat(),
                    None,
                ),
            )

        analyzed += 1
        time.sleep(LLM_CALL_DELAY_SECONDS)

    logger.info(f"[Analyze] Analyzed {analyzed} items")
    return analyzed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
