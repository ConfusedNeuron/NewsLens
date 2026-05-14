# NewsLens — Project Status (feature/live-pipeline-task6 branch)

> Branch: `feature/live-pipeline-task6` — Task #6: Fix Gemini AI proxy & wire live RSS/Reddit pipeline

## What's Done

### Tasks #1–#5 (carried from main)
- **Frontend** (`artifacts/newslens`): Full React + Vite app with swipe mode, reel mode, onboarding flow, complete design system, accessible reel indicators with countdown timer.
- **Backend** (`artifacts/newslens-backend`): FastAPI multi-agent pipeline — ingest → extract → analyze → score → store.
- pnpm monorepo, path-based artifact routing, 4 separate workflows.

### Task #6: Live Pipeline Fixes (this branch)
- **Fixed Gemini AI proxy** (`agents/gemini_client.py`):
  - Set `api_version=""` in `HttpOptions` — the root cause of the 403 proxy errors.
  - Raised `max_output_tokens` from 1024 → 8192 so full card JSON is never truncated.
  - Added `candidates` fallback parsing for edge-case Gemini responses.
  - Created centralized `build_client()` and `smoke_test()` helpers.
  - Hard-fail URL validation at startup — prevents silent misconfiguration.
- **Startup diagnostics** (`api/main.py`):
  - Gemini smoke test runs at boot; logs "Gemini AI proxy: OK" or hard error.
  - Reddit credential status logged at startup.
- **Reddit agent improvements** (`agents/ingest/reddit_agent.py`):
  - Module-level praw availability check.
  - `credentials_configured()` helper with explicit missing-key messages.
- **Pipeline verified end-to-end**: 29 live cards generated (14 fresh from BBC, The Hindu, TechCrunch, Hacker News via RSS).

## To-Do / Next Steps

- [ ] **Reddit credentials** (#9) — set `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` to enable Reddit ingest (create app at reddit.com/prefs/apps).
- [ ] **Concurrent LLM calls** (#10) — articles currently extracted sequentially; parallelise for speed.
- [ ] **Market/price data on cards** (#11) — add financial context (stock prices, macro indicators) to relevant cards.
- [ ] **Error surfacing in UI** — pipeline failures are currently silent to the user.

## Required API Keys / Secrets

| Secret | Purpose | Status |
|--------|---------|--------|
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Gemini AI proxy URL | Set (Replit-managed) |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Gemini AI proxy key | Set (Replit-managed) |
| `REDDIT_CLIENT_ID` | Reddit API — create at reddit.com/prefs/apps | **Not set** |
| `REDDIT_CLIENT_SECRET` | Reddit API secret | **Not set** |

## Key Files Changed in This Branch

| File | Change |
|------|--------|
| `artifacts/newslens-backend/agents/gemini_client.py` | **New** — centralized Gemini client with smoke test |
| `artifacts/newslens-backend/agents/extract_agent.py` | Uses `build_client()`, 8192 tokens, candidates fallback |
| `artifacts/newslens-backend/agents/analyze_agent.py` | Same Gemini client fixes |
| `artifacts/newslens-backend/agents/ingest/reddit_agent.py` | Credential wiring + explicit error messages |
| `artifacts/newslens-backend/api/main.py` | Startup smoke test + Reddit status logging |
| `artifacts/newslens-backend/config/settings.py` | Env var configuration |

## Known Errors / Remaining Issues

- Reddit ingest skipped (no credentials) — all current cards come from RSS feeds.
- `pnpm-lock.yaml` may need refresh if new Python deps are added.
