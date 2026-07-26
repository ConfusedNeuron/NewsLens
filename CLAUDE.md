# NewsLens — CLAUDE.md

Read this at the start of every session. **Verified build state + key decisions live in `GROUND_TRUTH.md` (authoritative — when it disagrees with this file, it wins).** Current state also in `STATUS.md`. PRD and specs in `../replit prompt/`.

---

## What This Is

**NewsLens** — Personal news intelligence system. Transforms raw news from RSS feeds + Reddit into quantified impact cards. Tells you *what it means in numbers* (e.g., "Nifty down 1.8%, ₹2.1L Cr market cap erased"), not just what happened.

**Target user:** Indian professional, 25–45, in tech/finance. Wants informed perspectives on Finance, Tech, Geopolitics, Environment — India + global (USA and China as counterweights).

Full PRD: `../replit prompt/PRD.md` | UI spec: `../replit prompt/UI_SPEC.md`

---

## Current State (DO THIS FIRST)

> ⚠️ **Partly superseded by `GROUND_TRUTH.md` (2026-06-05 verified audit).** Notably: **Fix 1 (Gemini) is obsolete** — the LLM stack already migrated to NVIDIA NIM + DeepSeek, so there is no Gemini `api_version` bug, only dead Gemini deps to delete. The pipeline is the full **8 stations**, not 4 agents. `GET /api/pipeline/status` doesn't exist (it's `/api/pipeline/logs`). **Fix 2 (Reddit creds) and Fix 3 (sequential extraction) are still valid.** See `GROUND_TRUTH.md`.

The platform is **built but broken**. Core issues to fix before any new feature work:

### Fix 1 — Gemini endpoint (BLOCKER)
`google.genai.errors.ClientError` due to wrong `api_version` in `HttpOptions`.  
**Fix:** Find `HttpOptions` config in `artifacts/newslens-backend/` and correct the `api_version` field to match current Gemini API docs.

### Fix 2 — Reddit credentials
`prawcore.exceptions.ResponseException` — `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` not set.  
**Fix:** Create Reddit app at reddit.com/prefs/apps → populate both secrets in `.env`.

### Fix 3 — Sequential LLM calls (performance)
`ExtractAgent` processes articles one by one — slow for batches.  
**Fix:** Wrap extraction calls in `asyncio.gather()` so articles process concurrently.

**Definition of fixed:** `POST /api/pipeline/run` returns freshly generated cards (not seed data) with real Gemini-extracted content.

---

## Monorepo Layout

```
NewsLens/               ← this directory
├── artifacts/
│   ├── newslens/           # React + Vite frontend (swipe mode, reel mode, design system)
│   └── newslens-backend/   # FastAPI backend
│       └── agents/
│           ├── ingest_agent.py    # RSS (BBC, TechCrunch, The Hindu, HN) + Reddit
│           ├── extract_agent.py   # Gemini AI → structured card data
│           ├── analyze_agent.py   # scores cards for relevance + freshness
│           └── store_agent.py     # persists to SQLite
├── STATUS.md               ← current known issues + API key status
└── CLAUDE.md               ← you are here
```

**API routes:** `GET /api/cards`, `POST /api/pipeline/run`, `GET /api/pipeline/status`  
**Scheduler:** Pipeline auto-runs every 6 hours  
**DB:** SQLite

---

## Upcoming Feature 1: Tool Use (Native Gemini Function Calling)

**Why:** The PRD promises quantified impact cards — "Nifty down 1.8%, ₹2.1L Cr market cap erased." RSS feeds give headlines and 2-sentence summaries. The `ExtractAgent` cannot quantify what it can't see. Giving it tools lets it fetch full articles and live market data to actually deliver the promise. This uses Gemini's native function calling API — not manual RAG dispatch — which is the current production pattern.

### Tools to Give ExtractAgent

**`web_search(query: str) -> str`**
- Fetches full article body when RSS only has title/description
- Implementation: call SerpAPI or DuckDuckGo API, return top result's full text
- When to call: whenever `article.full_text` is empty or under 200 chars

**`get_market_data(symbol: str) -> dict`**
- Returns `{price, change_pct, change_abs, volume, market_cap}` for a ticker or index
- Implementation: `yfinance` for stocks, NSE API for Indian indices (NIFTY, SENSEX, BANKNIFTY)
- Returns human-readable string for injection into prompt: `"NIFTY 50: 22,450 (-1.8%, ₹2.1L Cr market cap impact)"`
- When to call: whenever an entity in the article is a known ticker/index

**`calculate_impact(base_value: float, change_pct: float, unit: str) -> str`**
- Arithmetic helper: computes absolute change from percentage
- Returns formatted string: `"₹2.1L Cr market cap erased"` / `"$4.2B wiped from market cap"`
- Keeps LLM from doing unreliable arithmetic

### How to Implement

1. Define tools as a list of Gemini `FunctionDeclaration` objects
2. Pass to `GenerativeModel` via `tools=[...]` parameter
3. In `ExtractAgent._run()`: after initial model call, check for `function_call` parts in response, execute the tool, feed result back as `function_response`, continue until model returns final text
4. Add `tools/web_search.py`, `tools/market_data.py`, `tools/calculator.py` — each a simple function
5. `ExtractAgent` imports and registers all three

### PRD Update Required
> **TODO:** Add Tool Use spec to `../replit prompt/PRD.md` — new section covering: tool definitions (name, description, parameters, return format), which agent uses which tools, tool call limits per card (max 3 to control latency + cost), fallback behaviour when tool fails (skip quantification, not card failure).

---

## Upcoming Feature 2: Streaming SSE Pipeline

**Why:** Currently `/api/pipeline/run` is fire-and-wait — nothing appears until the full batch is done (could be 30+ seconds). Streaming lets cards appear in the frontend one by one as they're processed, which is both better UX and demonstrates the SSE streaming pattern that every modern AI product uses.

### What to Build

**New endpoint: `GET /api/pipeline/stream`** (Server-Sent Events)

```python
from fastapi.responses import StreamingResponse

@app.get("/api/pipeline/stream")
async def stream_pipeline():
    async def event_generator():
        async for card in pipeline.run_streaming():
            yield f"data: {card.model_dump_json()}\n\n"
        yield "data: {\"done\": true}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Pipeline change:** Refactor `run_pipeline()` into an async generator that `yield`s each card after it's stored, rather than returning all cards at the end.

**Frontend change:** Replace `POST /api/pipeline/run` poll with `EventSource('/api/pipeline/stream')`. On each event, prepend the new card to the feed. Show a "Loading..." skeleton while streaming.

**Progress events:** Also emit non-card events: `{"type": "progress", "stage": "ingest", "count": 12}` so the frontend can show "Fetching 12 articles..."

### PRD Update Required
> **TODO:** Add Streaming spec to `../replit prompt/UI_SPEC.md` — new section covering: SSE endpoint contract (event types: `card`, `progress`, `done`, `error`), frontend EventSource lifecycle, loading state design, and error surfacing (currently pipeline failures are silent — streaming makes them visible).

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite, swipe mode + reel mode, pnpm monorepo |
| Backend | FastAPI (Python) |
| Agents | IngestAgent, ExtractAgent, AnalyzeAgent, StoreAgent |
| LLM | Gemini AI (via proxy — `AI_INTEGRATIONS_GEMINI_BASE_URL`) |
| Tool Use (upcoming) | Gemini native function calling |
| DB | SQLite |
| Scheduler | APScheduler (6h interval) |

---

## Required Secrets

| Secret | Purpose | Status |
|---|---|---|
| `AI_INTEGRATIONS_GEMINI_BASE_URL` | Gemini proxy URL | Set |
| `AI_INTEGRATIONS_GEMINI_API_KEY` | Gemini proxy key | Set |
| `REDDIT_CLIENT_ID` | Reddit API | **NOT SET** |
| `REDDIT_CLIENT_SECRET` | Reddit API | **NOT SET** |

---

## Session Checklist

1. Check `STATUS.md` for current known issues
2. Fix blockers (Gemini endpoint, Reddit creds) before adding features
3. After fixing: verify `/api/pipeline/run` returns real cards, not seed data
4. Then: implement tool use → then streaming
5. Update `STATUS.md` at end of session
