"""Gmail newsletter ingestion agent (requires OAuth2 setup).

This agent is optional — the pipeline runs without it.
To enable: set GMAIL_CREDENTIALS_PATH and run the OAuth flow.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def run() -> int:
    """Gmail agent stub — requires OAuth setup to activate."""
    logger.info("[Gmail] Skipping — Gmail OAuth not configured for this deployment")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
