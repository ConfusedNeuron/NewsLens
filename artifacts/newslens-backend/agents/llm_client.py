"""
CommandCode LLM client + input validators for NewsLens.

HOW TO SWITCH MODELS
────────────────────
Open  config/settings.py  and change the ACTIVE_MODEL line:

  ACTIVE_MODEL = "deepseek/deepseek-v4-pro"   ← current default
  ACTIVE_MODEL = "claude-sonnet-4-6"           ← Claude Sonnet 4.6
  ACTIVE_MODEL = "zhipuai/glm-5"              ← GLM-5

That's the only change needed — all three go through the same
OpenAI-compatible endpoint (CommandCode proxies them uniformly).

To confirm exact model IDs on your account:
  python testapi.py --list-models
"""

import json
import logging
from pathlib import Path

from openai import OpenAI, APIConnectionError, AuthenticationError, RateLimitError

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import COMMANDCODE_API_KEY, COMMANDCODE_BASE_URL, ACTIVE_MODEL

logger = logging.getLogger(__name__)

# ── Quality thresholds ────────────────────────────────────────────────────
MIN_ARTICLE_WORDS  = 20     # fewer → not worth extracting
MIN_HEADLINE_CHARS = 5      # shorter → malformed extraction
MAX_INPUT_CHARS    = 12_000 # hard cap; text is truncated before this point anyway

BOILERPLATE_SIGNALS = [
    "subscribe to our newsletter",
    "javascript is disabled",
    "enable cookies to continue",
    "access denied",
    "403 forbidden",
    "404 not found",
    "page not found",
    "loading...",
    "please wait",
    "cookies are required",
]


class InputValidationError(ValueError):
    """
    Raised when the input fails a quality check.
    The caller must SKIP (log + mark as skipped) — there is no point retrying
    because retrying won't fix bad data.
    """


# ─────────────────────────────────────────────────────────────────────────────
# CLIENT FACTORY
# ─────────────────────────────────────────────────────────────────────────────

def get_llm_client() -> OpenAI:
    """Return an OpenAI client pointed at the CommandCode proxy."""
    if not COMMANDCODE_API_KEY:
        raise RuntimeError(
            "COMMANDCODE_API_KEY is not set.\n"
            "  1. Copy .env.example → .env\n"
            "  2. Paste your key:  COMMANDCODE_API_KEY=your_key_here\n"
            "  3. Get a key at:    https://commandcode.ai/studio → Settings → API Keys"
        )
    return OpenAI(
        api_key=COMMANDCODE_API_KEY,
        base_url=COMMANDCODE_BASE_URL,
    )


# ─────────────────────────────────────────────────────────────────────────────
# UNIFIED LLM CALL
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(
    client: OpenAI,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """
    Send a prompt and return the raw text response.

    Active model: DeepSeek V4 Pro  (change ACTIVE_MODEL in settings.py)

    # ── Claude Sonnet 4.6 ───────────────────────────────────────────────────
    # Set in settings.py:  ACTIVE_MODEL = "claude-sonnet-4-6"
    #
    # Notes:
    #   • CommandCode proxies Claude through the same /chat/completions endpoint.
    #   • response_format JSON mode is supported through the proxy.
    #   • Native Anthropic format (/messages) also available at the same base_url
    #     if you ever want to use the Anthropic SDK directly:
    #       client = anthropic.Anthropic(
    #           api_key=COMMANDCODE_API_KEY,
    #           base_url="https://api.commandcode.ai/provider/v1",
    #       )
    # ────────────────────────────────────────────────────────────────────────

    # ── GLM-5 ────────────────────────────────────────────────────────────────
    # Set in settings.py:  ACTIVE_MODEL = "zhipuai/glm-5"
    #
    # Notes:
    #   • If response_format JSON mode causes errors with GLM-5, remove the
    #     response_format parameter from the create() call below and rely on
    #     the JSON-strip fallback in extract_agent / analyze_agent instead.
    #   • Verify the exact ID via:  python testapi.py --list-models
    # ────────────────────────────────────────────────────────────────────────
    """
    # response_format={"type": "json_object"} is NOT used here intentionally.
    # Reasoning models (MiniMax M2.7, DeepSeek R1, etc.) burn internal chain-of-thought
    # tokens when JSON mode is forced, and some NIM endpoints return empty content as a
    # result. The prompts already instruct the model to return only JSON — that's enough.
    response = client.chat.completions.create(
        model=ACTIVE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    content = response.choices[0].message.content

    # Some reasoning models put output in reasoning_content instead of content
    if not content or not content.strip():
        choice = response.choices[0]
        # Check for reasoning_content field (DeepSeek R1, some NIM models)
        reasoning = getattr(choice.message, "reasoning_content", None)
        if reasoning and reasoning.strip():
            content = reasoning
        else:
            raise ValueError(
                f"LLM returned empty content. "
                f"Completion tokens: {getattr(response.usage, 'completion_tokens', '?')}. "
                f"Try a different model or check NIM quota."
            )
    return content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR: EXTRACT
# ─────────────────────────────────────────────────────────────────────────────

def validate_extract_input(text: str) -> None:
    """
    Check article text quality before the Extract LLM call.

    Raises InputValidationError immediately — caller must skip, not retry.
    All retry logic lives AFTER this check so we never waste API calls on
    garbage input.
    """
    # 1. Type check
    if not isinstance(text, str):
        raise InputValidationError(
            f"Expected str, got {type(text).__name__}."
        )

    # 2. Empty / blank
    stripped = text.strip()
    if not stripped:
        raise InputValidationError("Article text is empty or whitespace-only.")

    # 3. Minimum length
    words = stripped.split()
    if len(words) < MIN_ARTICLE_WORDS:
        raise InputValidationError(
            f"Article too short: {len(words)} words (minimum {MIN_ARTICLE_WORDS})."
        )

    # 4. Boilerplate / error page detection
    #
    # Two independent signals, because they catch different failures:
    #   (a) a boilerplate phrase in a SHORT document — the classic error page;
    #   (b) a boilerplate phrase REPEATED — a consent wall or paywall interstitial
    #       padded out past the length floor. A genuine article may mention cookies
    #       once; it does not say "please enable cookies to continue" three times.
    lower = stripped.lower()
    for signal in BOILERPLATE_SIGNALS:
        if signal not in lower:
            continue
        if len(words) < 60:
            raise InputValidationError(
                f"Text looks like a boilerplate/error page "
                f"('{signal}' with only {len(words)} words)."
            )
        occurrences = lower.count(signal)
        if occurrences >= 3:
            raise InputValidationError(
                f"Text looks like a boilerplate wall "
                f"('{signal}' repeated {occurrences} times)."
            )

    # 5. Must contain at least one sentence-ending character
    if not any(c in stripped for c in ".!?"):
        raise InputValidationError(
            "Text has no sentence-ending punctuation — likely garbled or truncated."
        )

    # 6. Not just a URL list
    non_url_words = [w for w in words if not w.startswith(("http", "www."))]
    if len(non_url_words) < MIN_ARTICLE_WORDS:
        raise InputValidationError(
            "Text is almost entirely URLs — no readable content to extract."
        )

    # 7. Repetition check — if >60% of words are the same word it's garbage
    if words:
        most_common = max(set(words), key=words.count)
        if words.count(most_common) / len(words) > 0.6 and len(words) > 30:
            raise InputValidationError(
                f"Text looks like garbage — word '{most_common}' repeated "
                f"{words.count(most_common)}/{len(words)} times."
            )


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR: ANALYZE
# ─────────────────────────────────────────────────────────────────────────────

def validate_analyze_input(
    clean_text: str,
    extracted: dict,
    enrichment_json: str,
) -> None:
    """
    Check all three inputs before the Analyze LLM call.

    Raises InputValidationError immediately — caller must skip, not retry.
    """
    # ── 1. clean_text ─────────────────────────────────────────────────────
    if not isinstance(clean_text, str):
        raise InputValidationError(
            f"clean_text must be str, got {type(clean_text).__name__}."
        )
    stripped = clean_text.strip()
    if not stripped:
        raise InputValidationError("clean_text is empty.")
    if len(stripped.split()) < MIN_ARTICLE_WORDS:
        raise InputValidationError(
            f"clean_text too short: {len(stripped.split())} words "
            f"(minimum {MIN_ARTICLE_WORDS})."
        )

    # ── 2. extracted dict ─────────────────────────────────────────────────
    if not extracted or not isinstance(extracted, dict):
        raise InputValidationError(
            "Extracted data is empty or not a dict — extraction likely failed."
        )

    required = {"headline", "event_type", "geography_primary"}
    missing  = required - set(extracted.keys())
    if missing:
        raise InputValidationError(
            f"Extracted data is missing required fields: {missing}"
        )

    headline = str(extracted.get("headline", "")).strip()
    if not headline or len(headline) < MIN_HEADLINE_CHARS:
        raise InputValidationError(
            f"Headline is missing or too short: '{headline}'"
        )

    event_type = extracted.get("event_type", "")
    if not event_type:
        raise InputValidationError("event_type is empty in extracted data.")

    # Don't spend an LLM call on low-confidence items with no numbers
    confidence       = extracted.get("confidence", "medium")
    numbers_mentioned = extracted.get("numbers_mentioned") or []
    if confidence == "low" and not numbers_mentioned:
        raise InputValidationError(
            "Low-confidence extraction with zero numbers — "
            "not worth running analyze (output would be pure speculation)."
        )

    # Sectors must be a non-empty list
    sectors = extracted.get("sectors") or extracted.get("sector") or []
    if isinstance(sectors, str):
        try:
            sectors = json.loads(sectors)
        except json.JSONDecodeError:
            sectors = [sectors]
    if not sectors:
        raise InputValidationError(
            "Extracted sectors list is empty — cannot determine analysis SOP."
        )

    # ── 3. enrichment_json ────────────────────────────────────────────────
    if enrichment_json and enrichment_json not in ("{}", ""):
        try:
            parsed = json.loads(enrichment_json)
        except json.JSONDecodeError as e:
            raise InputValidationError(
                f"enrichment_json is not valid JSON: {e}"
            )
        if not isinstance(parsed, dict):
            raise InputValidationError(
                "enrichment_json must be a JSON object, not an array or scalar."
            )
