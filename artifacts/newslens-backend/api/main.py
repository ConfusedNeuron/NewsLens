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

# CORS.
#
# `allow_origins=["*"]` together with `allow_credentials=True` is an invalid
# combination — browsers reject credentialed responses from a wildcard origin, so the
# previous config would have silently failed the moment cookie auth was introduced.
# Origins are now explicit and overridable, and credentials are only enabled when the
# origin list is explicit.
_default_origins = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]
_allow_all = ALLOWED_ORIGINS == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=not _allow_all,
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

    # Demo cards are NOT seeded here any more.
    #
    # Startup used to call seed_if_empty(), which inserted 15 fabricated stories
    # whenever the live card count hit zero. That turned any pipeline failure or LLM
    # outage into a feed silently repopulated with invented news, indistinguishable
    # from real output. Seeding is now explicit: `python db/seed.py --demo`.

    # The scheduler is opt-in too. Importing this module in a test or a one-off
    # script should not start a background job that spends LLM credits.
    if os.getenv("ENABLE_SCHEDULER", "1") not in ("0", "false", "False"):
        try:
            from pipeline.orchestrator import start_scheduler
            _scheduler = start_scheduler()
            app.state.scheduler = _scheduler
        except Exception as e:
            logger.warning(f"Scheduler not started: {e}")
    else:
        logger.info("Scheduler disabled via ENABLE_SCHEDULER=0")

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
