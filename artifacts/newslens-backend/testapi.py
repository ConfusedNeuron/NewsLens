"""
testapi.py — Verify your CommandCode API key and available models.

Usage:
  python testapi.py                   # quick ping with active model
  python testapi.py --list-models     # print every model your key can access
  python testapi.py --model <id>      # test a specific model ID
  python testapi.py --all-models      # test DeepSeek, Claude, GLM in one shot
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional

# Allow running from the backend root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI, AuthenticationError, APIConnectionError, RateLimitError
from config.settings import COMMANDCODE_API_KEY, COMMANDCODE_BASE_URL, ACTIVE_MODEL

# ── Config (read from settings.py + .env, never hardcoded here) ──────────
BASE_URL = COMMANDCODE_BASE_URL
API_KEY  = COMMANDCODE_API_KEY

# Models to test with --all-models (verified NVIDIA NIM IDs)
MODELS_TO_TEST = {
    ACTIVE_MODEL:                              f"Active model ({ACTIVE_MODEL})",
    "deepseek-ai/deepseek-v4-pro":             "DeepSeek V4 Pro",
    "meta/llama-3.3-70b-instruct":             "Llama 3.3 70B",
    "z-ai/glm-5.1":                            "GLM-5.1",
}

TEST_PROMPT = (
    "Output ONLY this exact JSON object, no explanation, no markdown, no reasoning:\n"
    '{"status": "ok", "message": "API is working"}'
)

# ─────────────────────────────────────────────────────────────────────────────


def check_key() -> bool:
    """Basic checks before hitting the API."""
    if not API_KEY:
        print("✗  COMMANDCODE_API_KEY is not set.")
        print("   → Copy .env.example to .env and paste your key.")
        print("   → Get a key at: https://commandcode.ai/studio → Settings → API Keys")
        return False
    if len(API_KEY) < 20:
        print(f"✗  COMMANDCODE_API_KEY looks too short ({len(API_KEY)} chars) — double-check it.")
        return False
    if " " in API_KEY or "\n" in API_KEY:
        print("✗  COMMANDCODE_API_KEY contains whitespace — remove it.")
        return False
    print(f"✓  Key found: {API_KEY[:8]}...{API_KEY[-4:]}  ({len(API_KEY)} chars)")
    return True


def get_client() -> OpenAI:
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def list_models(client: OpenAI) -> None:
    print("\n── Available models ─────────────────────────────────────────────")
    try:
        models = client.models.list()
        ids = sorted(m.id for m in models.data)
        for mid in ids:
            print(f"   {mid}")
        print(f"\n   Total: {len(ids)} models")
    except AuthenticationError:
        print("✗  Authentication failed — check your API key.")
    except APIConnectionError as e:
        print(f"✗  Cannot reach CommandCode API: {e}")
    except Exception as e:
        print(f"✗  Error listing models: {e}")


def test_model(client: OpenAI, model_id: str, label: Optional[str] = None) -> bool:
    name = label or model_id
    print(f"\n── Testing: {name} ({model_id}) ───────────────────────────────")
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            max_tokens=100,
            temperature=0,
        )
        raw = response.choices[0].message.content or ""
        # Fallback: some reasoning models use reasoning_content instead of content
        if not raw.strip():
            raw = getattr(response.choices[0].message, "reasoning_content", "") or ""
        if not raw.strip():
            print(f"   ⚠  Empty content field — completion tokens: "
                  f"{getattr(response.usage, 'completion_tokens', '?')}. "
                  f"Model may not support this prompt format.")
        else:
            print(f"   Raw response: {raw[:200]}")

        # Try to parse the expected JSON
        # Strip possible markdown fences
        content = raw.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            parsed = json.loads(content)
            if parsed.get("status") == "ok":
                print(f"   ✓  Response is valid JSON and status=ok")
            else:
                print(f"   ~  Response parsed but unexpected content: {parsed}")
        except json.JSONDecodeError:
            print(f"   ~  Response isn't JSON (model responded in plain text — still OK)")

        # Print token usage if available
        if response.usage:
            print(
                f"   Tokens — prompt: {response.usage.prompt_tokens}, "
                f"completion: {response.usage.completion_tokens}"
            )
        print(f"   ✓  {name} is working!")
        return True

    except AuthenticationError:
        print(f"   ✗  Authentication failed — key rejected by {BASE_URL}.")
        return False
    except RateLimitError as e:
        print(f"   ✗  Rate limit hit: {e}")
        return False
    except APIConnectionError as e:
        print(f"   ✗  Connection error: {e}")
        return False
    except Exception as e:
        err = str(e)
        if "model" in err.lower() and ("not found" in err.lower() or "invalid" in err.lower()):
            print(f"   ✗  Model ID '{model_id}' not found on your account.")
            print(f"      → Run: python testapi.py --list-models  to see available IDs.")
        else:
            print(f"   ✗  Error: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Test CommandCode API key")
    parser.add_argument("--list-models",  action="store_true", help="List all available model IDs")
    parser.add_argument("--all-models",   action="store_true", help="Test DeepSeek, Claude, and GLM-5")
    parser.add_argument("--model",        type=str,            help="Test a specific model ID")
    args = parser.parse_args()

    print("═" * 60)
    print("  NewsLens — LLM API Key Test")
    print(f"  Provider: {BASE_URL}")
    print("═" * 60)

    # Step 1: basic key sanity
    if not check_key():
        sys.exit(1)

    client = get_client()

    if args.list_models:
        list_models(client)
        return

    if args.model:
        ok = test_model(client, args.model)
        sys.exit(0 if ok else 1)

    if args.all_models:
        results = {}
        for model_id, label in MODELS_TO_TEST.items():
            results[label] = test_model(client, model_id, label)
        print("\n── Summary ──────────────────────────────────────────────────")
        for label, ok in results.items():
            icon = "✓" if ok else "✗"
            print(f"   {icon}  {label}")
        all_ok = all(results.values())
        sys.exit(0 if all_ok else 1)

    # Default: test active model from settings (already imported at top)
    ok = test_model(client, ACTIVE_MODEL, f"Active model ({ACTIVE_MODEL})")
    print()
    if ok:
        print("✓  API key is valid and the active model is responding.")
        print(f"   Active model: {ACTIVE_MODEL}")
        print("   Change ACTIVE_MODEL in config/settings.py to switch models.")
    else:
        print("✗  Something went wrong — see errors above.")
        print("   Try:  python testapi.py --list-models")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
