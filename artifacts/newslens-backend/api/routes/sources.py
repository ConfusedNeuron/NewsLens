"""Source status and pipeline management routes."""
import logging
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from fastapi import APIRouter, BackgroundTasks

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import fetchall, fetchone
from api.models import SourceStatus, PipelineRunLog

router = APIRouter()
logger = logging.getLogger(__name__)

SOURCES_PATH = Path(__file__).parent.parent.parent / "config" / "sources.yaml"


@router.get("/sources/status")
def get_sources_status():
    with open(SOURCES_PATH) as f:
        sources_config = yaml.safe_load(f)

    statuses = []
    cutoff = (datetime.utcnow() - timedelta(hours=7)).isoformat()

    for src_type, sources in [("rss", sources_config.get("rss", [])),
                               ("reddit", sources_config.get("reddit", [])),
                               ("substack", sources_config.get("substack", []))]:
        for src in sources:
            name = src.get("name") or src.get("subreddit", "")
            display_name = name if src_type != "reddit" else f"r/{name}"

            last_item = fetchone(
                "SELECT ingested_at FROM raw_items WHERE source_name = ? ORDER BY ingested_at DESC LIMIT 1",
                (display_name,),
            )
            today_count_row = fetchone(
                "SELECT COUNT(*) as cnt FROM raw_items WHERE source_name = ? AND ingested_at > ?",
                (display_name, cutoff),
            )
            today_count = today_count_row["cnt"] if today_count_row else 0

            statuses.append({
                "name": display_name,
                "source_type": src_type,
                "last_run": last_item["ingested_at"] if last_item else None,
                "items_today": today_count,
                "status": "active" if today_count > 0 else "idle",
            })

    last_run_log = fetchone(
        "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1"
    )

    return {
        "sources": statuses,
        "last_pipeline_run": last_run_log,
        "total_cards_live": (fetchone("SELECT COUNT(*) as cnt FROM cards WHERE is_live = TRUE") or {}).get("cnt", 0),
    }


@router.post("/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    def _run():
        from pipeline.orchestrator import run_pipeline
        try:
            run_pipeline()
        except Exception as e:
            logger.error(f"Pipeline run failed: {e}")

    background_tasks.add_task(_run)
    return {"ok": True, "message": "Pipeline triggered in background"}


@router.get("/pipeline/logs")
def get_pipeline_logs(limit: int = 50):
    rows = fetchall(
        "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT ?", (limit,)
    )
    return {"logs": rows, "total": len(rows)}
