"""NewsLens FastAPI application entry point."""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db.database import init_db
from api.routes.cards import router as cards_router
from api.routes.user import router as user_router
from api.routes.sources import router as sources_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NewsLens API",
    description="Multi-agent news intelligence platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(sources_router, prefix="/api")


@app.get("/api/healthz")
def health():
    return {"status": "ok", "service": "newslens-api"}


@app.get("/api/nerd-mode")
def nerd_mode_stub():
    return JSONResponse(
        status_code=501,
        content={"detail": "Nerd Mode coming in v2"},
    )


@app.on_event("startup")
def startup():
    logger.info("NewsLens API starting up...")
    init_db()

    from db.seed import seed_if_empty
    seed_if_empty()

    # Validate Gemini AI integration proxy is reachable before starting the scheduler.
    # This surfaces misconfigured endpoints immediately in logs instead of failing silently
    # the first time the pipeline runs.
    from agents.gemini_client import smoke_test as gemini_smoke_test
    gemini_ok = gemini_smoke_test()
    if gemini_ok:
        logger.info("[Startup] Gemini AI proxy: OK — LLM pipeline will be active")
    else:
        logger.warning(
            "[Startup] Gemini AI proxy: UNREACHABLE — pipeline will run but LLM stages "
            "(extract, analyze) will be skipped until the proxy is available. "
            "Check AI_INTEGRATIONS_GEMINI_BASE_URL and AI_INTEGRATIONS_GEMINI_API_KEY."
        )

    # Log Reddit credential status so operators know whether Reddit ingestion is active.
    from config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        logger.info("[Startup] Reddit credentials: configured — r/india, r/worldnews, r/investing will be ingested")
    else:
        logger.warning(
            "[Startup] Reddit credentials: NOT configured — Reddit ingestion will be skipped. "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET secrets to enable it."
        )

    try:
        from pipeline.orchestrator import start_scheduler
        _scheduler = start_scheduler()
        app.state.scheduler = _scheduler
    except Exception as e:
        logger.warning(f"Scheduler not started: {e}")

    logger.info("NewsLens API ready")


@app.on_event("shutdown")
def shutdown():
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        app.state.scheduler.shutdown(wait=False)
    logger.info("NewsLens API shutting down")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
