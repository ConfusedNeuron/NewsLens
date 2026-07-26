# NewsLens — Next Steps

**As of:** 2026-07-26. The working backlog. `GROUND_TRUTH.md` records what is built;
this records what to do next. Superseded audits are in `docs/archive/`.

---

## Blocked on you — nothing below can be verified until these are done

| # | Action | Where | Time |
|---|---|---|---|
| 1 | **Rotate the `nvapi-` key.** It sat in plaintext since May. Verified never committed, `.gitignore` now covers it — rotate anyway. | build.nvidia.com | 5 min |
| 2 | **Check remaining NIM credit.** Unverified since May. If exhausted, switch provider first — `config/settings.py` documents OpenRouter / Groq / Together as two-line swaps. | build.nvidia.com | 2 min |
| 3 | **Commit and push.** The working tree holds the only copy of `llm_client.py`, `personalize_agent.py`, and the whole test suite. On the remote: `git rm --cached artifacts/newslens-backend/newslens.db`. | GitHub | 5 min |
| 4 | Optional: FRED key (free). Without it no card carries US macro data. | fred.stlouisfed.org | 3 min |
| 5 | Optional: Reddit client id/secret, or leave the source disabled. | reddit.com/prefs/apps | 5 min |

---

## Verify (do these first, in order)

- [ ] `python testapi.py --list-models` — confirm `deepseek-ai/deepseek-v4-flash` still
      resolves. Everything downstream assumes it does and nobody has checked since May.
- [ ] `python scripts/verify_feeds.py` — all feeds alive and carrying body text.
- [ ] `pytest tests/ -q` — expect 36 passing, no network or API key needed.
- [ ] `python pipeline/orchestrator.py` — **the orchestrator has never produced a card.**
      `pipeline_runs` shows one run, 2026-05-13, with every LLM stage at zero; the 41
      cards in the DB were made by running agents by hand. This is the single most
      important unverified claim in the project.
- [ ] Complete onboarding in the UI → confirm the profile persists across a hard refresh
      and that cards show a `personal_impact` paragraph naming your sector or city.

---

## Next sprint, in value order

1. **Full-text fetching** (~1 day). `trafilatura` between Ingest and Clean. RSS snippets
   are 50-100 words, which is why extraction fails ~50% of the time and why the model
   has to estimate rather than cite. Improves every card from every source, and shifts
   magnitudes from `estimate` to `data` with no other change.
2. **Add RBI + PIB feeds** — same day as (1), not before. Both verified live on
   2026-07-26 but title-only, so they are useless until full text is fetched. URLs are
   in `config/sources.yaml` as comments. Press releases are the densest source of free
   quantified data available, and directly on-thesis for India-first.
3. **DB-backed dedup** (~2 hrs). `clean_agent.py` keeps hashes in a module-level list
   that resets on restart and never reads `clean_items.dedup_hash` back. Also move the
   hash append above the `model is None` return at `:93-104`, or exact-hash dedup
   records nothing when sentence-transformers is absent.
4. **Saved cards** (~half day). Swipes are recorded and never read. Either wire
   `GET /cards/saved` or hide the action. Right-swipe rate per source is also the
   feedback loop that would make source credibility self-improving.
5. **Rebalance the importance score.** `classify_agent.py:38-43` — sector count
   contributes up to 0.8 while source credibility spans only 0.12–0.4, so a
   low-credibility item tagged with four sectors outranks a high-credibility one. In a
   trust product, credibility should dominate.
6. **Resolve `hold` verdicts.** The quality gate can hold a card but there is no status
   column, review route, or UI, so held cards are invisible forever. Two are sitting in
   the DB from May. Either build the queue or collapse hold into approve/discard.
7. **Concurrency** (~half day). `asyncio.gather` with a cap for extract and analyze.
   Low priority — ~30 items per run means this saves minutes, not hours.
8. **Card lifecycle.** No expiry or archival; `cards` grows unboundedly and a stale feed
   looks identical to a fresh one.
9. **Auth.** `user_id` is hardcoded `default_user`. The personalization architecture
   already supports multiple users; the identity layer does not exist.
10. **Regenerate the API client.** `pnpm orval` — the checked-in output was hand-patched
    for `magnitude_source`, `market_data`, `time_horizon` and `is_seed`, and the
    `/cards/personalized` hook in `src/api.ts` is hand-written pending regen.
11. **Then**: per-step LLM router → tool use (OpenAI-style `tools=[...]`, not Gemini
    `FunctionDeclaration`) → SSE streaming.

---

## Deliberately not doing

- **Instagram ingest** — no public API, image-first, lowest information density of any
  candidate source.
- **Twitter/X ingest** — free tier is effectively write-only; paid tiers don't make
  sense here. Reddit already covers the social-signal layer.
- **WhatsApp scraping** — ToS violation and a ban risk. If WhatsApp happens it should be
  an inbound forward-bot via the Business Cloud API ("forward any news, get back a
  quantified card"), which is a better feature than scraping anyway.

---

## Process

One rule, because it's the one that was broken: **every session ends with a commit, not
a document.** The project spent 63 days producing five planning files and zero code
changes. `GROUND_TRUTH.md` and this file are the only two live documents; everything
else belongs in `docs/archive/`.
