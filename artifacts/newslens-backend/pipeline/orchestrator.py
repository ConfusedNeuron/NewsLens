"""Pipeline orchestrator — sequences all agents and schedules runs."""
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, execute
from config.settings import PIPELINE_INTERVAL_HOURS

logger = logging.getLogger(__name__)

# Guards against two pipeline runs overlapping. APScheduler's max_instances=1 covers
# the scheduled path, but POST /api/pipeline/run goes through BackgroundTasks and is
# not covered by it — two concurrent calls would both read status='pending' rows and
# process (and pay for) the same items twice.
_pipeline_lock = threading.Lock()


def log_stage(stage: str, items_processed: int = 0, items_failed: int = 0,
              status: str = "complete", error_log: str = None,
              started_at: str = None) -> str:
    """
    Record one stage execution.

    `started_at` must be captured by the caller BEFORE the stage runs. Until 2026-07-26
    this function stamped started_at and completed_at with the same `utcnow()` call at
    the end of the stage, so every recorded duration was exactly zero and the pipeline
    page's timing column was decorative.
    """
    run_id = str(uuid.uuid4())
    completed_at = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO pipeline_runs
               (id, stage, items_processed, items_failed, started_at, completed_at, status, error_log)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, stage, items_processed, items_failed,
             started_at or completed_at, completed_at,
             status, error_log),
        )
    return run_id


def _run_stage(name: str, fn) -> int:
    """
    Run one pipeline stage with real timing, error isolation, and logging.

    Replaces eight near-identical try/except blocks. A stage that raises is logged
    as failed and returns 0 — the pipeline continues, and because every agent polls
    for status='pending' rows, the next run picks up whatever this one dropped.
    """
    started_at = datetime.utcnow().isoformat()
    try:
        count = fn()
        log_stage(name, items_processed=count, status="complete", started_at=started_at)
        return count
    except Exception as e:
        logger.error(f"{name} failed: {e}", exc_info=True)
        log_stage(name, status="failed", error_log=str(e), started_at=started_at)
        return 0


def run_ingest() -> int:
    from agents.ingest.rss_agent import run as rss_run
    from agents.ingest.substack_agent import run as substack_run
    from agents.ingest.reddit_agent import run as reddit_run

    total = 0
    for name, fn in [("rss", rss_run), ("substack", substack_run), ("reddit", reddit_run)]:
        total += _run_stage(f"ingest:{name}", fn)
    return total


def run_clean() -> int:
    from agents.clean_agent import run
    return _run_stage("clean", run)


def run_extract() -> int:
    from agents.extract_agent import run
    return _run_stage("extract", run)


def run_classify() -> int:
    from agents.classify_agent import run
    return _run_stage("classify", run)


def run_enrich() -> int:
    from agents.enrich_agent import run
    return _run_stage("enrich", run)


def run_analyze() -> int:
    from agents.analyze_agent import run
    return _run_stage("analyze", run)


def run_format() -> int:
    from agents.format_agent import run
    return _run_stage("format", run)


def run_quality_gate() -> dict:
    from pipeline.quality_gate import run

    started_at = datetime.utcnow().isoformat()
    try:
        result = run()
        log_stage("quality_gate", items_processed=result.get("approved", 0),
                  items_failed=result.get("discarded", 0), status="complete",
                  started_at=started_at)
        return result
    except Exception as e:
        logger.error(f"Quality gate failed: {e}", exc_info=True)
        log_stage("quality_gate", status="failed", error_log=str(e), started_at=started_at)
        return {}


def run_pipeline() -> dict:
    """
    Run the full 8-station pipeline.

    Returns a stats dict. If another run is already in flight this returns immediately
    with skipped=True rather than double-processing (and double-paying for) the same
    pending rows.
    """
    if not _pipeline_lock.acquire(blocking=False):
        logger.warning("Pipeline run requested while another run is in flight — skipping.")
        return {"skipped": True, "reason": "a pipeline run is already in progress"}

    try:
        logger.info("=== Pipeline run starting ===")
        started_at = datetime.utcnow().isoformat()

        stats = {}
        stats["ingested"] = run_ingest()
        stats["cleaned"] = run_clean()
        stats["extracted"] = run_extract()
        stats["classified"] = run_classify()
        stats["enriched"] = run_enrich()
        stats["analyzed"] = run_analyze()
        stats["formatted"] = run_format()
        stats["quality_gate"] = run_quality_gate()

        logger.info(f"=== Pipeline complete: {stats} ===")
        return {"started_at": started_at, "completed_at": datetime.utcnow().isoformat(), **stats}
    finally:
        _pipeline_lock.release()


def start_scheduler():
    """Start APScheduler for periodic pipeline runs."""
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_pipeline,
        "interval",
        hours=PIPELINE_INTERVAL_HOURS,
        id="pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — pipeline runs every {PIPELINE_INTERVAL_HOURS}h")
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()
