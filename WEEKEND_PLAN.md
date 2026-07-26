# NewsLens — Weekend Execution Plan

**Budget:** 12–16 focused hours. **Goal:** portfolio-ready now, without foreclosing the daily-product path.
**Rule for the weekend:** every block ends in a commit and a working tree. No block starts before the previous one is committed.

---

## The one design change from `REVIEW_2026-07-26.md`

I recommended making `magnitude` null when there's no source data. **Don't do that** — I was wrong about the interaction.

Right now the model invents magnitudes because it only sees 50-word RSS snippets and has no real numbers to anchor to. If you null those out *before* adding full-text fetching, most magnitudes become empty and the cards get visibly worse. You'd be trading a credibility problem for an emptiness problem.

**Do provenance labelling instead.** Every winner/loser gets a `magnitude_source: "data" | "estimate"` field. The model must mark which one it is. The UI renders `"data"` magnitudes normally and `"estimate"` ones muted with an "est." chip and a tooltip: *"Model estimate — not from a verified data source."*

This is cheaper (~2 hrs vs a day), keeps the cards full, and is a far better interview answer than either hiding estimates or suppressing them: **"I don't hide the model's guesses, I label their provenance."** It also gets *better automatically* once full-text fetching lands, because more magnitudes shift from `estimate` to `data` with no further work.

---

## Block 0 — Unblock (45 min) · BLOCKED ON YOU

1. Rotate the `nvapi-` key at build.nvidia.com. Paste into `.env`.
2. **Check remaining NIM credit while you're there.** Nobody has verified this since May. If the free credit is exhausted, blocks 1–3 don't run and you need a different provider first — `settings.py` already documents OpenRouter/Groq/Together as drop-in swaps (change `LLM_BASE_URL` + `ACTIVE_MODEL`, nothing else).
3. `python testapi.py --list-models` — confirm `deepseek-ai/deepseek-v4-flash` still resolves.
4. `git add -A && git commit -m "Working tree: NIM migration, llm_client, validation layer"` then push. `.gitignore` already protects `.env` and `*.db`. On the remote: `git rm --cached artifacts/newslens-backend/newslens.db`.

**Exit test:** a fresh clone contains `llm_client.py`, and `testapi.py` prints a model list.

---

## Block 1 — Prove the pipeline end-to-end (1.5 hr)

This has never been demonstrated. `pipeline_runs` has 10 rows, all from 13 May, every LLM stage reading zero. Your 26 real cards were made by running agents by hand.

1. `config/sources.yaml`: delete Reuters (`feeds.reuters.com` — discontinued) and Down To Earth (returns 0). Replace with **PIB** (`https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3`) and **RBI press releases** — primary sources, high credibility, dense with real numbers, and directly on-thesis for India-first. Comment out Reddit unless you've set credentials.
2. Fix the fake telemetry: `orchestrator.py:24-26` writes `started_at == completed_at`. Capture a real start time and pass it through.
3. Fix the status-string mismatch: backend writes `'complete'`, `pipeline.tsx:15` checks `'success'` — the pipeline page renders the failure icon on every successful stage.
4. Run `python pipeline/orchestrator.py`. Watch it. Fix what breaks.

**Exit test:** `pipeline_runs` has today's rows with non-zero `items_processed` at every stage, and `cards` has rows with today's `created_at`. Commit.

---

## Block 2 — Magnitude provenance + disclaimer (2 hr)

1. `prompts/analyze.txt` — replace the `"use 'est.' prefix"` rule. New instruction:
   > Each winner/loser must include `magnitude_source`: `"data"` if the number appears in MARKET & MACRO DATA or EXTRACTED FACTS, `"estimate"` if it is your own inference. Never mark an inference as `"data"`.
2. `analyze_agent.py` — add `magnitude_source` to `validate_analysis_output()`; default to `"estimate"` when absent (fail safe, not fail open).
3. `NewsCard.tsx` — render `"estimate"` magnitudes in muted text with an "est." chip + tooltip.
4. Add a one-line financial disclaimer to the card footer. This is flagged as a legal risk in your own consultant report and costs you ten minutes.

**Exit test:** regenerate a handful of cards; at least one shows a muted `est.` magnitude and one shows a clean data-backed one. Commit.

---

## Block 3 — Personalization, built the right way (4–5 hr) · THE CENTREPIECE

This kills the #1 dead differentiator *and* uses the architecture that scales past one user, so you don't rebuild it later.

**The design:** cards stay global. Personalization is a cheap, cached, read-time pass.

1. **Fix the 405** — add `@router.put("/user/profile")` in `api/routes/user.py` alongside the existing POST (keep both; PUT matches the spec, POST keeps any old client working).
2. **Pick one profile vocabulary.** `OnboardingModal.tsx` ("Salaried Employee", "Mutual funds / SIPs", Indian city dropdown) and `profile.tsx` ("salary", "conservative", "e.g. San Francisco") currently write mutually unintelligible data to the same columns. Keep the OnboardingModal vocabulary — it's the India-first one — and rewrite `profile.tsx` to match.
3. **New table:**
   ```sql
   CREATE TABLE card_personalizations (
     card_id TEXT NOT NULL,
     user_id TEXT NOT NULL,
     personal_impact TEXT,
     created_at TEXT,
     PRIMARY KEY (card_id, user_id)
   );
   ```
4. **New agent function** `agents/personalize_agent.py` — one cheap LLM call using `prompts/personal_impact.txt`, **the file that already exists and is currently read by zero code.** Input: the card's `summary_60w` + `winners` + `losers` + the user profile. Output: two sentences. Write to `card_personalizations`.
5. **Wire `GET /cards/personalized`** — for each returned card, look up the row; on miss, generate and cache. Also fix `cards.py:132-136`, which uses only `sectors[0]` and ignores the rest of the user's declared exposure.
6. **Kill the localStorage silo** — `feed.tsx` reads the profile from localStorage while `/profile` reads the API. Make the API the single source of truth; keep localStorage as a cache only.

**Why this is the good interview answer:** cost is O(cards) globally plus O(cards × *active* users) generated lazily and cached — not O(cards × all users) eagerly. Say that sentence out loud; it's the strongest architectural point in the project.

**Exit test:** complete onboarding → the profile persists across a hard refresh → cards show a `personal_impact` paragraph that names your sector or city → reload is instant (cache hit, no second LLM call). Commit.

---

## Block 4 — Two tests and a CI file (2 hr)

Not optional. Blocks 1–3 all touch code paths that have silently broken before, and "zero tests" is the first thing an engineering reviewer greps for.

1. `tests/test_api.py` — FastAPI `TestClient`: seed → `GET /cards` returns >0 → `PUT /user/profile` returns 200 → `GET /user/profile` round-trips the same data. **This one test permanently kills the entire 405 class of bug.**
2. `tests/test_extract.py` — `extract_agent` with a mocked LLM: valid JSON → parsed correctly; malformed JSON → retried once then marked failed; short input → skipped without any LLM call (assert the mock was never called — that's the spend-aware behaviour you'll want to talk about).
3. `.github/workflows/ci.yml` — ten lines: checkout, setup-python, `pip install -r requirements.txt`, `pytest`.

**Exit test:** green check on GitHub. Commit.

---

## Block 5 — Surface enrichment (2 hr, if time remains)

Enrichment is thinner than any audit said: **2/40** items got stock data, **40/40** got the same commodity blob, and **0/40** got macro data because `FRED_API_KEY` is empty.

1. Get a free FRED key (instant) and set it — `macro_us` starts populating immediately, no code change.
2. Add a `market_data` TEXT column to `cards`; have `format_agent.py` map the enrichment payload into it (it currently maps **zero** enrichment fields).
3. Add it to `openapi.yaml`, regenerate the client, render a chip: `USD/INR 95.68 ▼0.5%`.

Skip the `COMPANY_TICKER_MAP` problem this weekend — sparse stock coverage is fine once commodities and macro are visible.

---

## Block 6 — Close it out (1 hr)

1. Delete the 15 fabricated seed cards ("Nifty 50 Crosses 27,000", "GST Collections Cross ₹2 Lakh Crore"), which currently ship as `is_live=TRUE` and indistinguishable from real ones. Move `seed_if_empty()` behind an explicit `--demo` flag so it can never silently re-enter after an LLM outage.
2. Rewrite `README.md` as the demo narrative: what it does, the 2-LLM-call cost architecture, the read-time personalization design, the provenance labelling, one screenshot, and an honest **Known Limitations** section.
3. Collapse the docs. `GROUND_TRUTH.md` + `NEXT_STEPS.md` survive; move `AUDIT_2026-07-05.md`, `REVIEW_2026-07-26.md`, `STATUS.md`, `replit.md`, `CLAUDE.md`, `DATA_SOURCES_STRATEGY.md` and both HTML reports into `docs/archive/`. Eleven markdown files is the single loudest signal of analysis paralysis in the repo.
4. Tag it: `git tag v0.1-portfolio`.

---

## Explicitly NOT this weekend

| Deferred | Why |
|---|---|
| Full-text fetching (`trafilatura`) | Highest-value next item, but a full day. Provenance labelling makes it *upgrade* the product later rather than being a prerequisite. **Do this first next sprint.** |
| Async / `asyncio.gather` extraction | You process ~30 items per 6-hour run. Sequential costs minutes and is invisible to any reviewer. |
| DB-backed dedup | Real bug (`clean_agent.py:93-104` — the hash is appended only inside the embedding branch), but invisible in a demo. Put it in Known Limitations. |
| Importance-score rebalance | Sector count contributes up to 0.8, credibility only 0.12–0.4. Wrong, but not demo-visible. |
| Tool use, SSE streaming, Telegram/YouTube/WhatsApp | New features on a base that isn't proven yet. |
| `time_horizon` full-stack plumbing | Cosmetic; the hardcoded `"⏱ Near-term"` is survivable. |
| Auth / multi-user | `default_user` is a defensible single-tenant demo. Block 3's design is what makes multi-user *possible* later — that's enough. |

---

## Realistic total

| Block | Hours |
|---|---|
| 0 · Unblock | 0.75 |
| 1 · Prove the pipeline | 1.5 |
| 2 · Magnitude provenance | 2 |
| 3 · Personalization | 4.5 |
| 4 · Tests + CI | 2 |
| 5 · Enrichment (optional) | 2 |
| 6 · Close out | 1 |
| **Total** | **13.75** |

If you run short, **cut Block 5, not Block 4.** A reviewer who sees zero tests forms a conclusion about you; one who sees no market-data chip just sees a smaller feature set.

---

## Blockers on you

### Hard — nothing starts without these

| # | What | Where | Time |
|---|---|---|---|
| 1 | Rotate the `nvapi-` key | build.nvidia.com | 5 min |
| 2 | **Confirm remaining NIM credit** — unverified since May; if it's gone, the whole weekend is blocked until you pick a provider | build.nvidia.com | 2 min |
| 3 | Push access to `ConfusedNeuron/NewsLens` | GitHub | 5 min |

### Soft — block one block each

| # | What | Blocks | Note |
|---|---|---|---|
| 4 | FRED API key (free, instant) | Block 5 macro data | `FRED_API_KEY` is empty — **no card has ever had macro data** |
| 5 | Reddit client ID + secret | Reddit ingest | reddit.com/prefs/apps, 5 min. Or drop the source — it has never once produced an item |
| 6 | Confirm `sentence-transformers` installs in your env | dedup accuracy | It's pinned in `requirements.txt` but absent from at least one environment I checked |

### Decisions only you can make — settle these before Saturday

7. **Does the demo run live, or from a snapshot?** If a reviewer might open it, you need a hosted URL and the pipeline running on a schedule — that's an extra half-day not in this plan. If you'll always drive it on your laptop, ignore.
8. **Profile vocabulary** — I've assumed OnboardingModal's wins. Say so if you prefer the other.
9. **Seed cards: delete or flag?** I've assumed delete + `--demo` flag. Flagging is safer if you want a guaranteed-populated demo when the LLM is down.
10. **Is `ConfusedNeuron/NewsLens` staying public?** It has `newslens.db` committed. Public + a rotated key is fine, but decide deliberately rather than by default.

### Not blockers, despite appearances

- The unrotated key is **not** currently leaked — verified never committed, and `.gitignore` now covers it. Rotate anyway; it's five minutes and it's been on three consecutive to-do lists.
- Zero tests does not block any block. It blocks *trusting* every block, which is why it's #4 and not #7.
