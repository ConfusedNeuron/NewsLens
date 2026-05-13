# NewsLens — Project Status (main branch)

> Branch: `main` — original baseline before live-pipeline work (Task #6)

## What's Done

### Core Platform (Tasks #1–#5)
- **Frontend** (`artifacts/newslens`): Full React + Vite app with swipe mode, reel mode, onboarding flow, and a complete design system. Accessible reel indicators with countdown timer.
- **Backend** (`artifacts/newslens-backend`): FastAPI service with a multi-agent pipeline — ingest → extract → analyze → score → store.
- **Agents**:
  - `IngestAgent` — fetches RSS feeds (BBC, TechCrunch, The Hindu, Hacker News) and Reddit posts.
  - `ExtractAgent` — uses Gemini AI to extract structured card data (headline, summary, entities, sentiment, image prompt).
  - `AnalyzeAgent` — scores cards for relevance and freshness.
  - `StoreAgent` — persists cards to SQLite.
- **API routes**: `GET /api/cards`, `POST /api/pipeline/run`, `GET /api/pipeline/status`.
- **Scheduler**: Pipeline auto-runs every 6 hours.
- **Mock/seed data**: Cards seeded for demo purposes when pipeline hasn't run yet.

### Infrastructure
- pnpm monorepo with path-based artifact routing.
- Separate workflows for frontend, backend, API server, and mockup sandbox.

## To-Do / Known Issues at This Snapshot

- [ ] **Gemini AI endpoint broken** — `api_version` misconfiguration causes proxy calls to fail; pipeline falls back to seed data only.
- [ ] **Reddit credentials not wired** — `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` not yet set; Reddit ingest silently skipped.
- [ ] **No concurrent LLM calls** — articles extracted sequentially; slow for large batches.
- [ ] **No market/price data** on cards — financial context missing.
- [ ] **No error surfacing in UI** — pipeline failures are silent to the user.

## Required API Keys / Secrets

| Secret | Purpose | Status |
|--------|---------|--------|
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Gemini AI proxy URL | Set (Replit-managed) |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Gemini AI proxy key | Set (Replit-managed) |
| `REDDIT_CLIENT_ID` | Reddit API client ID | **Not set** |
| `REDDIT_CLIENT_SECRET` | Reddit API client secret | **Not set** |

## Known Errors (at this snapshot)

- `google.genai.errors.ClientError` or empty response from Gemini proxy due to wrong `api_version` in `HttpOptions`.
- Reddit `prawcore.exceptions.ResponseException` when credentials are absent.
- Pipeline returns 0 freshly-generated cards; falls back to seed data.
