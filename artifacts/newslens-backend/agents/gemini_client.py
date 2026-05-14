"""Centralized Gemini AI client factory and smoke test."""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import GEMINI_API_KEY, GEMINI_BASE_URL

logger = logging.getLogger(__name__)


def build_client():
    """Build and return a configured Gemini AI client."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "AI_INTEGRATIONS_GEMINI_API_KEY is not set. "
            "Cannot build Gemini client."
        )
    if not GEMINI_BASE_URL:
        raise RuntimeError(
            "AI_INTEGRATIONS_GEMINI_BASE_URL is not set. "
            "Cannot build Gemini client."
        )

    from google import genai
    from google.genai import types as genai_types

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=genai_types.HttpOptions(
            base_url=GEMINI_BASE_URL,
            api_version="",
        ),
    )
    return client


def smoke_test() -> bool:
    """
    Send a minimal request to verify the Gemini proxy is reachable.
    Returns True if the proxy responds correctly, False otherwise.
    Does NOT raise — callers decide how to handle failure.
    """
    try:
        client = build_client()
        from google.genai import types as genai_types

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with the single word: OK",
            config=genai_types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=16,
            ),
        )
        text = response.text or ""
        if response.candidates and not text:
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            text = "".join(p.text for p in parts if hasattr(p, "text") and p.text)
        logger.info(f"[Gemini smoke test] response: {text.strip()!r}")
        return True
    except Exception as exc:
        logger.warning(f"[Gemini smoke test] FAILED: {exc}")
        return False
