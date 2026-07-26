# NewsLens — Ground Truth & Decisions

**Purpose:** The authoritative record of *what is actually built* (vs. what the PRD / specs / CLAUDE.md / STATUS.md claim) and *key decisions not derivable from the code*. When this file disagrees with CLAUDE.md or STATUS.md, **this file wins** — it was produced from a verified read of the live working tree; the others are older and partly aspirational.

**As of:** 2026-06-05. Produced by a 4-agent audit — 2 investigators (backend + frontend) and 2 independent verifiers — reading the on-disk code. Evidence is cited as `file:line` so any claim can be re-checked.

> **📌 2026-07-05 re-audit:** a full line-by-line re-audit re-verified every claim in this file (nothing wrong, some incomplete) and found **5 major new issues** — see **`AUDIT_2026-07-05.md`** (authoritative addendum). Headlines: (1) profile save is dead — OpenAPI PUT vs backend POST-only → every save 405s; (2) `analyze_agent.py:220` never passes `user_profile` → `personal_impact` structurally always empty; (3) real `nvapi-` key in local `.env` — NOT on GitHub (verified), `.gitignore` fixed, **rotation still pending**; (4) dedup is in-memory only, resets every restart; (5) classify weights + quality-gate rules silently deviate from specs, and "hold" cards can never resolve. GitHub repo (`ConfusedNeuron/NewsLens`) is public, last pushed 2026-05-14 (pre-NIM), has `newslens.db` committed, and the local tree has no `.git`.

**Legend:** ✅ Built (works & wired) · 🟡 Partial (exists, incomplete or not wired) · 📋 Planned (referenced, not implemented) · ❌ Dropped (in docs, absent from code) · 🔀 Different (built, but not as documented)

---

## ⚠️ Corrections to CLAUDE.md / STATUS.md (read first)

These are stated in CLAUDE.md/STATUS.md but are **wrong against the current tree**:

1. **"Fix 1 — Gemini endpoint (BLOCKER)" is obsolete.** There is no Gemini call, no `HttpOptions`, and no `api_version` anywhere in live code. The LLM stack was **already migrated off Gemini** onto an OpenAI-compatible proxy (NVIDIA NIM + DeepSeek). The `google.genai.ClientError` blocker can no longer occur. *Residual dead code only:* `google-genai==1.16.0` (`requirements.txt:4`), `GEMINI_*` shell vars (`config/settings.py:70-73`), `AI_INTEGRATIONS_GEMINI_*` (`.env.example`). **Correct action:** delete the dead Gemini deps/config — do **not** patch `HttpOptions`.
2. **"4 agents (Ingest, Extract, Analyze, Store)" is wrong.** The real pipeline is the full **8 stations** from `specs.md`: Ingest → Clean → Extract → Classify → Enrich → Analyze → Format → QualityGate — all implemented and wired in `pipeline/orchestrator.py:31-146`. There is **no StoreAgent**.
3. **"GET /api/pipeline/status" does not exist.** The actual route is **`GET /api/pipeline/logs`** (`api/routes/sources.py:78-83`). The API prefix is `/api`, **not** `/api/v1` (`api/main.py:38-40`).
4. **The "Required Secrets" table is stale.** The live LLM secret is `COMMANDCODE_API_KEY` (NIM / OpenAI-compatible key) + optional `LLM_BASE_URL` override — not the Gemini/Anthropic keys listed.

**Still accurate from CLAUDE.md:**
- **Fix 2 (Reddit creds)** — Reddit ingest needs `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET`; still unset.
- **Fix 3 (sequential extraction)** — real and unfixed: `extract_agent.py:106` is a sync `def run()`, `:118` a sequential `for` loop, `:168`/`:101` `time.sleep()`. No `asyncio.gather` anywhere. (`analyze_agent.py:169` is sync too.)

---

## Backend — as-built

Scope: `artifacts/newslens-backend/`

| Element | Docs claim | Reality (as-built) | Status | Evidence |
|---|---|---|---|---|
| Pipeline shape | 8 stations (specs) vs 4 agents (CLAUDE.md) | Full 8 stations, all wired | ✅ | `pipeline/orchestrator.py:31-146` |
| DB schema | 9 tables (specs §4) | All 9 present **+ extra** `enrichment_cache` | ✅ / 🔀 | `db/schema.sql:2-125` |
| **LLM provider** | Claude Sonnet 4 (specs) / Gemini 2.5 Flash (replit.md) | **NVIDIA NIM + `deepseek-ai/deepseek-v4-flash`** via `openai` SDK | 🔀 | `config/settings.py:48`, `:34-37`; `agents/llm_client.py:23,71-73` |
| Gemini integration | replit.md: active | Removed from runtime; **dead deps/config only** | ❌ | `requirements.txt:4`; `config/settings.py:70-73`; `.env.example` |
| `llm_client.py` abstraction | undocumented | New file; centralizes all LLM calls (both extract + analyze route through it); raises `RuntimeError` if key unset | 🔀 | `agents/llm_client.py:64-73`; `extract_agent.py:16-21`; `analyze_agent.py:17-22` |
| Enrichment (market data) | consultant: "exists, never surfaces" | yfinance + 5 commodities + FRED fetched → `enriched_items.enrichment_json`; injected into ANALYZE prompt; **never mapped to a typed `cards` field** | 🟡 | `enrich_agent.py:41-177`; `analyze_agent.py:114,143`; `format_agent.py:35`; `schema.sql:63-84` (no enrichment column) |
| Analyze output storage | implied: own table | Written back into `enriched_items.enrichment_json` under a hidden `_analysis` key; FORMAT reads it out | 🔀 | `analyze_agent.py:228-248`; `format_agent.py:35` |
| Sources — RSS | 12 (specs) / 4 (CLAUDE.md) | **10 feeds** (ET, Mint, Reuters, TechCrunch, HN, BBC, The Hindu, SCMP, Carbon Brief, Down To Earth) | 🔀 | `config/sources.yaml:1-55` |
| Sources — Reddit | 9 subs | 9 subs (matches spec) | ✅ | `config/sources.yaml:62-97` |
| Sources — Substack | 4 | 3 (Finshots, Import AI, The Overshoot) | 🔀 | `config/sources.yaml:99-113` |
| Sources — Gmail / YouTube | Tier-2 features | Stubs return 0; **not called** by orchestrator | 📋 | `agents/ingest/gmail_agent.py:12-15`; `youtube_agent.py:10-13`; `orchestrator.py:32-45` |
| Concurrent extraction | CLAUDE.md Fix 3 | Still sequential loop + `time.sleep()`; agents sync, not async | 🟡 bug | `extract_agent.py:106,118,168` |
| API routes | cards / swipe / profile / sources.status / pipeline.run | All present | ✅ | `api/routes/cards.py`, `user.py`, `sources.py` |
| `GET /api/pipeline/status` | CLAUDE.md | Does not exist — actual is `/api/pipeline/logs` | ❌ | `api/routes/sources.py:78-83` |
| `GET /api/nerd-mode` | undocumented | Stub returns 501 | 🔀 | `api/main.py:48-52` |

**Pipeline as-built:** `Ingest (RSS+Substack+Reddit) → Clean → Extract [LLM#1] → Classify → Enrich (yfinance/FRED) → Analyze [LLM#2] → Format → QualityGate → cards.is_live=TRUE`

**Two non-obvious sequencing facts** (not in any doc):
- Cards are inserted with `is_live = FALSE` (`format_agent.py:80`); **only the quality gate flips them live** — fresh cards are invisible until QualityGate runs.
- QualityGate **discards any card with no winners AND no losers** (`pipeline/quality_gate.py:51-53`) — if the LLM returns empty arrays, the card is silently dropped.

---

## Frontend — as-built

Scope: `artifacts/newslens/` (a React app). Generated API client + OpenAPI spec live at the **monorepo root** `/NewsLens/lib/` (`api-spec/`, `api-client-react/`), **not** inside `artifacts/newslens/`.

| Element / Consultant claim | Docs/Consultant say | Reality | Status | Evidence |
|---|---|---|---|---|
| Stack | UI_SPEC §14: vanilla JS (app.js, swipe.js…) | React + Vite + **TypeScript**; Framer Motion; shadcn/ui + Tailwind; `wouter` router; Orval-generated React Query hooks | 🔀 | `src/*.tsx`; `SwipeMode.tsx:2`; `lib/api-spec/orval.config.ts` |
| `time_horizon` hardcoded | consultant bug | Renders literal `⏱ Near-term`; field **absent from the OpenAPI schema entirely** (so it's an API+UI gap, not a one-line fix) | 🟡 bug | `NewsCard.tsx:181`; `lib/api-spec/openapi.yaml` (no `time_horizon`) |
| Only `winners[0]`/`losers[0]` | consultant bug | True in the **feed** card; the **detail** page maps full arrays — the two surfaces diverged | 🟡 bug | `NewsCard.tsx:202,230`; `card-detail.tsx:77,91` |
| Saved cards dead | consultant bug | `/saved` is a hardcoded "coming soon" placeholder; right-swipe fires `POST /swipe` but there is **no retrieval endpoint/query** | 🟡 | `saved-cards.tsx`; `swipe-utils.ts:1-8` |
| Onboarding dismissable | consultant bug | Dismiss sets `onboarded=true` but **no profile** → `personal_impact` (gated on `hasProfile`) never renders. **Worse:** the `/profile` page calls the API, but the feed reads profile **only from localStorage** — the two flows are **siloed**, so profile edits never reach personal-impact | 🟡 | `feed.tsx:39,120-123`; `NewsCard.tsx:37,249`; `profile.tsx` |
| Enrichment on card | consultant bug | No enrichment/market-data field exists on the card (schema or UI) | ❌ | `openapi.yaml` Card schema; `NewsCard.tsx:31-327` |
| Fixed card height | consultant bug | `CARD_H = "min(680px, 85vh)"`; inner card `overflow:hidden` clips content on small phones (Reel mode sizes more safely) | 🟡 | `SwipeMode.tsx:14`; `NewsCard.tsx:47`; `ReelMode.tsx:55-59` |
| F5 Swipe / F6 Reel / F7 Filters | v1 | Built (filters: domain server-side, geo/confidence client-side) | ✅ | `SwipeMode.tsx`, `ReelMode.tsx`, `NLFilterBar.tsx` |
| F8 Profile + Onboarding | v1 | Partial — siloed profile flows (above) | 🟡 | `OnboardingModal.tsx`, `profile.tsx`, `feed.tsx` |
| F9 Confidence badge | v1 | Built | ✅ | `NewsCard.tsx:25-29,84-111` |

---

## LLM Strategy — Decision: Per-Step Router

**Context:** Free/cheap LLM access under a tight budget. The two LLM jobs have very different requirements, so a single global model is the wrong default.

| Step | Job | Quality bar | Decision | Rationale |
|---|---|---|---|---|
| **EXTRACT** | entities / event / numbers → strict JSON | Low (mechanical) | Cheapest reliable model. Keep DeepSeek-on-NIM for now; can downgrade to a **local Ollama** model (Qwen2.5-7B / Llama-3.1-8B) to spend $0 and save NIM credits | Mechanical NLU; quality differences barely matter here |
| **ANALYZE** | winner/loser + magnitude + angles + personal impact | **High + needs function-calling** (for upcoming Tool Use) | Best available model that **supports tool/function calling**. DeepSeek-on-NIM if it does; otherwise **Gemini 2.5 Flash** (free tier, native function calling) | This is the product's core value and the step that calls tools |
| (CLASSIFY signal) | finance sentiment | n/a | **FinBERT — optional, local, signal only.** Feed its sentiment into the importance score; never use it for EXTRACT/ANALYZE | FinBERT is a finance-*sentiment classifier*, **not generative** — it cannot emit JSON or analysis, and is finance-only (no tech/geo/env). Confirmed dead-end for the core pipeline |

**Implementation (small — the abstraction already exists):** extend `agents/llm_client.py` to accept a `step` argument and select the model from a per-step map in `config/settings.py` (e.g. `MODEL_FOR_STEP = {"extract": ..., "analyze": ...}`). "Money crunch" then becomes a config knob, not a rewrite.

**⚠️ Implication for "Upcoming Feature 1: Tool Use".** CLAUDE.md describes implementing tool use with **Gemini `FunctionDeclaration`** objects — but the code is now on the **`openai` SDK** (NIM). So Feature 1 must be implemented with **OpenAI-style `tools=[...]` function calling**, not Gemini's API. Also: whichever model runs ANALYZE **must support function calling** — verify the current NIM/DeepSeek model does before building tools; if not, route ANALYZE to Gemini 2.5 Flash.

**Open verification:** confirm `deepseek-ai/deepseek-v4-flash` (`config/settings.py:48`) is a valid model ID on the configured NIM endpoint — if it's a placeholder/typo, every LLM call 404s at runtime.

---

## Known bugs & gaps (actionable, consolidated)

**Backend**
- [ ] Concurrent extraction not implemented (CLAUDE.md Fix 3) — `extract_agent.py` sequential + `time.sleep()`.
- [ ] Reddit creds unset (CLAUDE.md Fix 2) — ingest silently skips Reddit.
- [ ] Dead Gemini deps/config to remove (`google-genai`, `GEMINI_*`, `AI_INTEGRATIONS_GEMINI_*`).
- [ ] `.env.example` wrongly says the base URL "defaults to OpenRouter" — it defaults to NVIDIA NIM.
- [ ] Verify `deepseek-ai/deepseek-v4-flash` is a real model ID on the endpoint.
- [ ] Enrichment numbers never reach a typed card field — add an `enrichment`/`market_data` field if you want them visible (this is the "make the differentiator visible" win).

**Frontend**
- [ ] `time_horizon`: add to OpenAPI schema + backend, then render it instead of the hardcoded `⏱ Near-term`.
- [ ] Feed card shows only `winners[0]`/`losers[0]` — show 2 of each (detail page already maps full arrays).
- [ ] `/saved` is a placeholder — wire a saved-cards query, or hide the Save action until it works.
- [ ] Unify the two profile flows (feed reads localStorage; `/profile` reads the API) so profile edits actually drive personal-impact.
- [ ] Card overflow clipping on small phones (`overflow:hidden` + fixed height).
- [ ] No financial disclaimer on cards (legal risk flagged in the consultant report).

---

*Maintenance: update this file whenever the build state changes. It is the reconciliation layer between the aspirational docs (`../replit prompt/`, `NewsLens_Blueprint.html`) and the code.*
