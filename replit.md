# NewsLens

Multi-agent news intelligence platform. Ingests news from RSS feeds, Reddit, and Substack through an 8-station AI pipeline, then serves structured "impact cards" via a FastAPI backend.

## Architecture

### Backend (`artifacts/newslens-backend/`)
Python FastAPI service. Runs on port 8000.

**8-station pipeline:**
1. **Ingest** — RSS (10 feeds), Reddit (9 subreddits), Substack (3 newsletters)
2. **Clean** — HTML stripping, boilerplate removal, language detection (en/hi), deduplication
3. **Extract** — Gemini 2.5 Flash extracts entities, event type, geography, sectors
4. **Classify** — Rule-based importance scoring, domain/geo tagging
5. **Enrich** — Live stock prices (yfinance), commodity data, macro indicators (FRED)
6. **Analyze** — Gemini 2.5 Flash generates winners/losers/angles with quantified magnitude
7. **Format** — Maps analysis to card schema
8. **Quality Gate** — Rules-based filter before cards go live

**API endpoints:**
- `GET /api/healthz` — health check
- `GET /api/cards` — list live cards (filter by domain, geo, confidence)
- `GET /api/cards/:id` — card detail
- `POST /api/cards/:id/swipe` — record swipe feedback
- `GET /api/cards/personalized` — personalized feed
- `POST /api/user/profile` — save user profile
- `GET /api/user/profile?user_id=` — get profile
- `GET /api/sources/status` — source and pipeline status
- `POST /api/pipeline/run` — trigger pipeline manually
- `GET /api/pipeline/logs` — pipeline run history

**Database:** SQLite at `artifacts/newslens-backend/newslens.db`

**Demo data:** 15 pre-seeded live cards across Finance, Tech, Geopolitics, and Environment domains.

### Workflow
- `NewsLens Backend` — runs uvicorn on port 8000

## Environment Variables
- `AI_INTEGRATIONS_GEMINI_API_KEY` — auto-provisioned via Replit AI integrations
- `AI_INTEGRATIONS_GEMINI_BASE_URL` — auto-provisioned via Replit AI integrations
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — optional, enables Reddit ingestion
- `FRED_API_KEY` — optional, enables US macro data enrichment

## User Preferences
- Use Gemini (via Replit AI integrations) for all LLM calls
- Pipeline model: `gemini-2.5-flash`
