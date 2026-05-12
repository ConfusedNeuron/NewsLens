"""Pipeline orchestrator — sequences all agents and schedules runs."""
import uuid
import logging
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_conn, execute
from config.settings import PIPELINE_INTERVAL_HOURS

logger = logging.getLogger(__name__)


def log_stage(stage: str, items_processed: int = 0, items_failed: int = 0,
              status: str = "running", error_log: str = None) -> str:
    run_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO pipeline_runs
               (id, stage, items_processed, items_failed, started_at, completed_at, status, error_log)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, stage, items_processed, items_failed,
             datetime.utcnow().isoformat(), datetime.utcnow().isoformat(),
             status, error_log),
        )
    return run_id


def run_ingest() -> int:
    from agents.ingest.rss_agent import run as rss_run
    from agents.ingest.substack_agent import run as substack_run
    from agents.ingest.reddit_agent import run as reddit_run

    total = 0
    for name, fn in [("rss", rss_run), ("substack", substack_run), ("reddit", reddit_run)]:
        try:
            count = fn()
            total += count
            log_stage(f"ingest:{name}", items_processed=count, status="complete")
        except Exception as e:
            logger.error(f"Ingest {name} failed: {e}")
            log_stage(f"ingest:{name}", status="failed", error_log=str(e))
    return total


def run_clean() -> int:
    from agents.clean_agent import run
    try:
        count = run()
        log_stage("clean", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Clean failed: {e}")
        log_stage("clean", status="failed", error_log=str(e))
        return 0


def run_extract() -> int:
    from agents.extract_agent import run
    try:
        count = run()
        log_stage("extract", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Extract failed: {e}")
        log_stage("extract", status="failed", error_log=str(e))
        return 0


def run_classify() -> int:
    from agents.classify_agent import run
    try:
        count = run()
        log_stage("classify", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Classify failed: {e}")
        log_stage("classify", status="failed", error_log=str(e))
        return 0


def run_enrich() -> int:
    from agents.enrich_agent import run
    try:
        count = run()
        log_stage("enrich", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Enrich failed: {e}")
        log_stage("enrich", status="failed", error_log=str(e))
        return 0


def run_analyze() -> int:
    from agents.analyze_agent import run
    try:
        count = run()
        log_stage("analyze", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        log_stage("analyze", status="failed", error_log=str(e))
        return 0


def run_format() -> int:
    from agents.format_agent import run
    try:
        count = run()
        log_stage("format", items_processed=count, status="complete")
        return count
    except Exception as e:
        logger.error(f"Format failed: {e}")
        log_stage("format", status="failed", error_log=str(e))
        return 0


def run_quality_gate() -> dict:
    from pipeline.quality_gate import run
    try:
        result = run()
        log_stage("quality_gate", items_processed=result.get("approved", 0),
                  items_failed=result.get("discarded", 0), status="complete")
        return result
    except Exception as e:
        logger.error(f"Quality gate failed: {e}")
        log_stage("quality_gate", status="failed", error_log=str(e))
        return {}


def run_pipeline() -> dict:
    """Run the full 8-station pipeline."""
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
