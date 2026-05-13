"""Reddit ingestion agent using PRAW.

Requires:
  REDDIT_CLIENT_ID    — from https://www.reddit.com/prefs/apps (script app)
  REDDIT_CLIENT_SECRET

When either credential is missing the agent skips gracefully and logs a warning.
The startup check in api/main.py surfaces this status at boot time.
"""
import uuid
import logging
from datetime import datetime
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import get_conn, fetchone
from config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SCORE_THRESHOLD

logger = logging.getLogger(__name__)

SOURCES_PATH = Path(__file__).parent.parent.parent / "config" / "sources.yaml"

# Check praw availability once at import time so errors are surfaced early.
try:
    import praw as _praw_module
    _PRAW_AVAILABLE = True
except ImportError:
    _praw_module = None
    _PRAW_AVAILABLE = False
    logger.warning("[Reddit] praw package not installed — Reddit ingestion unavailable")


def load_reddit_sources() -> list[dict]:
    with open(SOURCES_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("reddit", [])


def credentials_configured() -> bool:
    """Return True if both Reddit API credentials are present in the environment."""
    return bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)


def get_reddit_client():
    """Build and return an authenticated PRAW Reddit client.

    Raises RuntimeError with a clear message if credentials are missing or praw
    is not installed — callers should catch this and log rather than crash.
    """
    if not _PRAW_AVAILABLE:
        raise RuntimeError(
            "praw is not installed. Run: pip install praw"
        )
    if not credentials_configured():
        raise RuntimeError(
            "Reddit credentials not configured. "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment secrets. "
            "Create a 'script' app at https://www.reddit.com/prefs/apps to obtain them."
        )
    return _praw_module.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def ingest_subreddit(reddit, source: dict) -> int:
    subreddit_name = source["subreddit"]
    domain = source.get("domain", "")
    geo = source.get("geo", "Global")
    count = 0

    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = list(subreddit.hot(limit=50))
    except Exception as e:
        logger.warning(f"Failed to fetch r/{subreddit_name}: {e}")
        return 0

    for post in posts:
        if post.score < REDDIT_SCORE_THRESHOLD:
            continue
        if post.is_self is False and not post.selftext:
            pass
        if hasattr(post, "crosspost_parent"):
            continue

        post_url = f"https://reddit.com{post.permalink}"
        existing = fetchone("SELECT id FROM raw_items WHERE url = ?", (post_url,))
        if existing:
            continue

        title = post.title or ""
        body = post.selftext or ""
        top_comments = []
        try:
            post.comment_limit = 3
            post.comments.replace_more(limit=0)
            for comment in list(post.comments)[:3]:
                if hasattr(comment, "body") and len(comment.body) > 20:
                    top_comments.append(comment.body)
        except Exception:
            pass

        raw_text = f"{title}\n\n{body}\n\n" + "\n".join(top_comments)
        raw_text = raw_text.strip()

        if not raw_text or len(raw_text) < 50:
            continue

        metadata = {
            "subreddit": subreddit_name,
            "score": post.score,
            "domain": domain,
            "geo": geo,
            "credibility": "medium",
            "post_id": post.id,
        }

        item_id = str(uuid.uuid4())
        with get_conn() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO raw_items
                   (id, source_type, source_name, url, raw_text, metadata_json, ingested_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item_id,
                    "reddit",
                    f"r/{subreddit_name}",
                    post_url,
                    raw_text,
                    str(metadata),
                    datetime.utcnow().isoformat(),
                    "pending",
                ),
            )
        count += 1

    logger.info(f"[Reddit] r/{subreddit_name}: {count} new posts")
    return count


def run() -> int:
    sources = load_reddit_sources()
    if not credentials_configured():
        logger.warning(
            "[Reddit] Skipping — REDDIT_CLIENT_ID and/or REDDIT_CLIENT_SECRET not configured. "
            "Set these secrets to enable ingestion from: %s",
            ", ".join(f"r/{s['subreddit']}" for s in sources),
        )
        return 0
    try:
        reddit = get_reddit_client()
        total = 0
        for source in sources:
            total += ingest_subreddit(reddit, source)
        logger.info(f"[Reddit] Total new items: {total}")
        return total
    except Exception as e:
        logger.error(f"[Reddit] Failed: {e}")
        return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
