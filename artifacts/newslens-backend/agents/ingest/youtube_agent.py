"""YouTube transcript ingestion agent (skeleton).

Requires youtube-transcript-api and channel IDs configured in sources.yaml.
"""
import logging

logger = logging.getLogger(__name__)


def run() -> int:
    """YouTube agent skeleton — configure channel IDs in sources.yaml to activate."""
    logger.info("[YouTube] Skipping — no YouTube channels configured")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
