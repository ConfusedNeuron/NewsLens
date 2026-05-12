"""Substack newsletter ingestion agent (RSS-based)."""
import uuid
import logging
from datetime import datetime
from pathlib import Path

import yaml
import feedparser

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import get_conn, fetchone
from config.settings import MAX_ARTICLES_PER_FEED

logger = logging.getLogger(__name__)

SOURCES_PATH = Path(__file__).parent.parent.parent / "config" / "sources.yaml"


def load_substack_sources() -> list[dict]:
    with open(SOURCES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("substack", [])


def ingest_substack(source: dict) -> int:
    name = source["name"]
    url = source["url"]
    credibility = source.get("credibility", "medium")
    count = 0

    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "NewsLens/1.0"})
    except Exception as e:
        logger.warning(f"Failed to fetch {name}: {e}")
        return 0

    entries = feed.entries[:MAX_ARTICLES_PER_FEED]

    for entry in entries:
        entry_url = getattr(entry, "link", None)
        if not entry_url:
            continue

        existing = fetchone("SELECT id FROM raw_items WHERE url = ?", (entry_url,))
        if existing:
            continue

        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "") or ""
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        raw_text = f"{title}\n\n{summary}\n\n{content}".strip()

        if not raw_text or len(raw_text) < 50:
            continue

        metadata = {
            "source_name": name,
            "source_url": url,
            "domain": source.get("domain", ""),
            "geo": source.get("geo", "Global"),
            "credibility": credibility,
            "source_type": "substack",
        }

        item_id = str(uuid.uuid4())
        with get_conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO raw_items
                   (id, source_type, source_name, url, raw_text, metadata_json, ingested_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item_id,
                    "substack",
                    name,
                    entry_url,
                    raw_text,
                    str(metadata),
                    datetime.utcnow().isoformat(),
                    "pending",
                ),
            )
        count += 1

    logger.info(f"[Substack] {name}: {count} new items")
    return count


def run() -> int:
    sources = load_substack_sources()
    total = 0
    for source in sources:
        total += ingest_substack(source)
    logger.info(f"[Substack] Total new items: {total}")
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
