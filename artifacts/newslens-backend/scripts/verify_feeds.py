#!/usr/bin/env python3
"""
Verify every feed in config/sources.yaml is alive AND carries usable text.

Why this exists
───────────────
Two feeds (Reuters Business, Down To Earth) returned zero items for over two months
and nothing noticed, because a dead feed and a quiet news day look identical to the
ingest agent. This script makes that failure loud.

It checks two different things, and the second one matters more:

  1. Is the feed reachable and does it parse?
  2. Do its items carry a <description>/<content> body, or only a headline?

A title-only feed (many government/regulator feeds are) is *worse* than no feed until
full-text fetching exists — the Extract station gets a headline with no numbers in it
and either fails or invents them.

Usage
─────
    python scripts/verify_feeds.py            # check everything
    python scripts/verify_feeds.py --json     # machine-readable, for CI

Exit codes: 0 = all healthy, 1 = at least one feed dead or title-only.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = ROOT / "config" / "sources.yaml"

# An item body shorter than this is treated as "headline only" — not enough for
# the Extract station to find numbers in.
MIN_BODY_CHARS = 120
# How many items to sample per feed when measuring body length.
SAMPLE_SIZE = 5


def load_feeds() -> list[dict]:
    with open(SOURCES_PATH) as f:
        data = yaml.safe_load(f) or {}
    feeds = []
    for key in ("rss", "substack"):
        for entry in data.get(key) or []:
            feeds.append({"kind": key, **entry})
    return feeds


def item_body(entry) -> str:
    """Best-effort extraction of an item's text body across feed dialects."""
    for attr in ("content", "summary_detail"):
        val = getattr(entry, attr, None)
        if isinstance(val, list) and val:
            return (val[0].get("value") or "").strip()
        if isinstance(val, dict):
            return (val.get("value") or "").strip()
    return (getattr(entry, "summary", "") or getattr(entry, "description", "") or "").strip()


def check_feed(feed: dict) -> dict:
    import feedparser

    result = {
        "name": feed.get("name", "?"),
        "url": feed.get("url", ""),
        "kind": feed["kind"],
        "ok": False,
        "items": 0,
        "median_body_chars": 0,
        "verdict": "",
    }

    try:
        parsed = feedparser.parse(feed["url"])
    except Exception as e:
        result["verdict"] = f"UNREACHABLE — {e}"
        return result

    entries = parsed.entries or []
    result["items"] = len(entries)

    if getattr(parsed, "bozo", 0) and not entries:
        result["verdict"] = f"UNPARSEABLE — {getattr(parsed, 'bozo_exception', 'unknown error')}"
        return result

    if not entries:
        result["verdict"] = "DEAD — feed parsed but returned 0 items"
        return result

    lengths = sorted(len(item_body(e)) for e in entries[:SAMPLE_SIZE])
    median = lengths[len(lengths) // 2]
    result["median_body_chars"] = median

    if median < MIN_BODY_CHARS:
        result["verdict"] = (
            f"TITLE-ONLY — {len(entries)} items but median body {median} chars. "
            "Not usable until full-text fetching lands."
        )
        return result

    result["ok"] = True
    result["verdict"] = f"OK — {len(entries)} items, median body {median} chars"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    try:
        import feedparser  # noqa: F401
    except ImportError:
        print("feedparser not installed — run: pip install -r requirements.txt", file=sys.stderr)
        return 2

    results = [check_feed(f) for f in load_feeds()]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        width = max((len(r["name"]) for r in results), default=10)
        for r in results:
            mark = "PASS" if r["ok"] else "FAIL"
            print(f"[{mark}] {r['name']:<{width}}  {r['verdict']}")
        failed = [r for r in results if not r["ok"]]
        print()
        print(f"{len(results) - len(failed)}/{len(results)} feeds healthy.")
        if failed:
            print("Unhealthy: " + ", ".join(r["name"] for r in failed))

    return 1 if any(not r["ok"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
