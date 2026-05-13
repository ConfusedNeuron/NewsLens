"""Centralized Gemini client for the Replit AI Integration modelfarm proxy.

The Replit AI Integration proxy serves Gemini at a /modelfarm/gemini base URL.
The google-genai Python SDK appends /v1beta/ by default, which breaks the proxy.
Setting api_version="" prevents that suffix from being added.

Environment variables (auto-provisioned via Replit AI Integration setup):
  AI_INTEGRATIONS_GEMINI_BASE_URL — e.g. http://localhost:1106/modelfarm/gemini
  AI_INTEGRATIONS_GEMINI_API_KEY  — dummy string required by the SDK (proxy ignores it)
"""
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL

logger = logging.getLogger(__name__)

_EXPECTED_PATH_SEGMENT = "modelfarm"


def _validate_base_url(base_url: str) -> None:
    """Raise if the base URL does not look like the Replit modelfarm proxy."""
    if not base_url:
        raise RuntimeError(
            "AI_INTEGRATIONS_GEMINI_BASE_URL is not set. "
            "Run setupReplitAIIntegrations in the JS sandbox to provision it."
        )
    if _EXPECTED_PATH_SEGMENT not in base_url:
        logger.warning(
            "[GeminiClient] AI_INTEGRATIONS_GEMINI_BASE_URL does not contain '%s'. "
            "Expected the Replit modelfarm proxy URL. Got: %s",
            _EXPECTED_PATH_SEGMENT,
            base_url,
        )


def build_client():
    """Build and return a google-genai Client configured for the Replit AI proxy.

    Raises RuntimeError if required env vars are missing.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "AI_INTEGRATIONS_GEMINI_API_KEY is not set. "
            "Run setupReplitAIIntegrations in the JS sandbox to provision it."
        )
    _validate_base_url(GEMINI_BASE_URL)

    from google import genai
    from google.genai import types as genai_types

    http_options = genai_types.HttpOptions(
        base_url=GEMINI_BASE_URL,
        api_version="",
    )
    client = genai.Client(api_key=GEMINI_API_KEY, http_options=http_options)
    logger.debug("[GeminiClient] Client built — base_url=%s model=%s", GEMINI_BASE_URL, GEMINI_MODEL)
    return client


def smoke_test() -> bool:
    """Send a minimal generate_content request to confirm the proxy is reachable.

    Uses application/json response. Checks candidates directly so thinking-model
    responses that leave response.text=None still register as success when the
    proxy round-trip completed without error (HTTP 200 with a valid response object).
    Returns True on success, False on any failure. Never raises.
    """
    try:
        from google.genai import types as genai_types
        client = build_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents='Output the JSON object: {"ok": true}',
            config=genai_types.GenerateContentConfig(
                max_output_tokens=20,
                response_mime_type="application/json",
            ),
        )
        # A successful proxy round-trip always produces at least one candidate.
        # response.text may be None for thinking-mode models even on success.
        has_candidates = bool(response.candidates)
        text_snippet = (response.text or "").strip()[:40]

        if has_candidates or text_snippet:
            logger.info(
                "[GeminiClient] Smoke test OK — proxy reachable, model=%s%s",
                GEMINI_MODEL,
                f", response={text_snippet!r}" if text_snippet else " (candidates present)",
            )
            return True

        logger.warning(
            "[GeminiClient] Smoke test: HTTP 200 but no candidates/text — proxy may be misconfigured"
        )
        return False
    except Exception as exc:
        logger.error("[GeminiClient] Smoke test FAILED: %s", exc)
        return False
