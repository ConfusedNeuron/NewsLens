"""Clean agent — strips HTML, deduplicates, language-filters raw items."""
import uuid
import re
import logging
import hashlib
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, fetchall, execute
from config.settings import LANGUAGES_ALLOWED, DEDUP_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

BOILERPLATE_PATTERNS = [
    r"subscribe\s+(to|now|here)",
    r"click here to",
    r"cookie\s+policy",
    r"privacy\s+policy",
    r"terms\s+of\s+service",
    r"all rights reserved",
    r"copyright \d{4}",
    r"follow us on",
    r"share this article",
    r"advertisement",
    r"loading\.\.\.",
    r"please enable javascript",
]
BOILERPLATE_RE = [re.compile(p, re.IGNORECASE) for p in BOILERPLATE_PATTERNS]

_embedding_model = None
_recent_embeddings: list = []
_recent_hashes: list = []
MAX_DEDUP_WINDOW = 500


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not available — dedup disabled")
    return _embedding_model


def strip_html(text: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ")
    except ImportError:
        clean = re.sub(r"<[^>]+>", " ", text)
        return clean


def remove_boilerplate(text: str) -> str:
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(p.search(line) for p in BOILERPLATE_RE):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines)


def detect_language(text: str) -> str | None:
    try:
        from langdetect import detect
        return detect(text[:2000])
    except Exception:
        return "en"


def compute_dedup_hash(text: str) -> str:
    return hashlib.sha256(text[:500].encode()).hexdigest()


def is_duplicate(text: str) -> bool:
    global _recent_embeddings, _recent_hashes
    model = get_embedding_model()

    dedup_hash = compute_dedup_hash(text)
    if dedup_hash in _recent_hashes:
        return True

    if model is None:
        return False

    try:
        import numpy as np
        new_emb = model.encode(text[:1000], normalize_embeddings=True)
        for existing_emb in _recent_embeddings[-MAX_DEDUP_WINDOW:]:
            similarity = float(np.dot(new_emb, existing_emb))
            if similarity > DEDUP_SIMILARITY_THRESHOLD:
                return True
        _recent_embeddings.append(new_emb)
        _recent_hashes.append(dedup_hash)
        if len(_recent_embeddings) > MAX_DEDUP_WINDOW:
            _recent_embeddings.pop(0)
            _recent_hashes.pop(0)
        return False
    except Exception as e:
        logger.debug(f"Dedup check failed: {e}")
        return False


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def clean_item(raw: dict) -> dict | None:
    raw_text = raw.get("raw_text", "")
    text = strip_html(raw_text)
    text = remove_boilerplate(text)
    text = normalize(text)

    if len(text.split()) < 30:
        return None

    lang = detect_language(text)
    if lang not in LANGUAGES_ALLOWED:
        return None

    if is_duplicate(text):
        return None

    return {
        "id": str(uuid.uuid4()),
        "raw_id": raw["id"],
        "clean_text": text,
        "language": lang,
        "word_count": len(text.split()),
        "dedup_hash": compute_dedup_hash(text),
        "cleaned_at": datetime.utcnow().isoformat(),
        "status": "pending",
    }


def run() -> int:
    pending = fetchall("SELECT * FROM raw_items WHERE status = 'pending'")
    processed = 0
    cleaned = 0

    for raw in pending:
        result = clean_item(raw)
        processed += 1

        if result is None:
            execute("UPDATE raw_items SET status = 'failed' WHERE id = ?", (raw["id"],))
            continue

        with get_conn() as conn:
            conn.execute(
                """INSERT INTO clean_items (id, raw_id, clean_text, language, word_count, dedup_hash, cleaned_at, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (result["id"], result["raw_id"], result["clean_text"], result["language"],
                 result["word_count"], result["dedup_hash"], result["cleaned_at"], result["status"]),
            )
            conn.execute("UPDATE raw_items SET status = 'cleaned' WHERE id = ?", (raw["id"],))
        cleaned += 1

    logger.info(f"[Clean] Processed {processed}, cleaned {cleaned}")
    return cleaned


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
