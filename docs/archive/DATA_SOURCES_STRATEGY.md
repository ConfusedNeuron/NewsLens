# NewsLens — Data Sources & Multi-Platform Ingestion Strategy

**As of:** 2026-07-13. Companion to `AUDIT_2026-07-05.md` + `NEXT_STEPS.md`. Covers the plan for scraping/ingesting news from WhatsApp, Twitter/X, YouTube, Instagram + Telegram, and how to improve data sources generally.

> **Prerequisite:** the pipeline blockers in `NEXT_STEPS.md` §-1/§-0.5 (rotate key, verify DeepSeek model ID resolves, fix PUT/POST + personalization) come FIRST — none of the sources below produce visible cards until the pipeline actually generates fresh content. Also fix **DB-backed dedup** (audit finding #4) before scaling sources: more sources = more duplicates, and dedup currently resets on every restart.

> **Verify before committing:** platform API terms/pricing shift constantly. Do a fresh web check on current tier limits before building WhatsApp Cloud API or Telegram routes.

---

## Per-platform feasibility (the four asked for + Telegram)

### YouTube — EASIEST, build first
- Stub already exists (`agents/ingest/youtube_agent.py` returns 0); design already in `specs.md §3.5` (`youtube-transcript-api`, 500-word chunks → treated as articles).
- **Discovery is free via RSS** — no YouTube Data API needed: `https://www.youtube.com/feeds/videos.xml?channel_id=<ID>`. Poll for new videos, fetch transcript, feed into existing Clean station.
- Channels to consider: CNBC-TV18, ANI, finance explainers.
- **Caveat:** transcript fetching gets IP-blocked from cloud/datacenter IPs. Fallback: `yt-dlp` subtitle extraction.
- Fits the existing ingest-agent output contract — zero architectural change.

### WhatsApp — DON'T scrape; make it an INBOUND forward-bot
- No read API. Unofficial libs (whatsapp-web.js, Baileys) violate ToS + risk banning your number. Do not.
- **Flip the direction:** official **WhatsApp Business Cloud API** delivers messages sent *to* the bot via webhook.
- Product framing (turns Persona-3 Rajan's pain into the best feature): "Forward any news to NewsLens → get back a quantified impact card telling you if it's real and what it means for you." Inbound, ToS-legit, stronger portfolio story than scraping.
- Implementation: FastAPI webhook route → message text enters pipeline as `source_type: whatsapp_forward` → reply with card summary.

### Twitter/X — DEFER, not worth it
- Free API tier essentially write-only; read access starts at paid tiers that don't make sense for a portfolio project. Scraping = ToS violation + losing arms race.
- Reddit already provides the social-signal layer. If a few key accounts (RBI, ministers, analysts) are truly needed later, an RSSHub bridge can sometimes cover them.

### Instagram — SKIP
- No public API for others' content; most aggressive anti-scraping; content is images/reels (needs OCR/vision just to get text) for the lowest info-density of any source. Wrong source for finance/geopolitics signal.

### Telegram — the honest substitute for "chat-app news"
- Everything WhatsApp-group-scraping was meant to do, Telegram does legitimately: official Bot API / Telethon reads public channels. Indian finance/news channels are numerous + high-volume. ~1 day of work.

---

## How to improve data sources (ranked by value/effort)

**Key insight: more sources isn't the bottleneck — richer TEXT from existing sources is.**

1. **Full-text article fetching (DO THIS BEFORE ANYTHING ELSE).** RSS items carry only title + 2-sentence snippet; the Extract agent can't quantify what it can't see — root cause of weak cards. Add a fetch step (`trafilatura`: URL → clean article text) between Ingest and Clean. Improves *every* card from *every* existing source. This is also most of the planned `web_search` tool.
2. **Primary structured sources** — where free quantified numbers live: RBI press releases (RSS), SEBI, PIB (Press Information Bureau), NSE/BSE corporate announcements. Highest-credibility, most-quantified, perfect for the India-first thesis. Just more RSS agents.
3. **Wire the Gmail stub** (`specs.md §3.4` already designed) — Finshots/Morning Brew newsletters are pre-curated high-signal.
4. **Google News RSS queries** (`news.google.com/rss/search?q=...`) — free per-entity feeds; track companies from the user's profile rather than whole publications. GDELT is the heavier free option for global event coverage later.
5. **Close the feedback loop already present** — swipe data is recorded but never used. Per-source right-swipe rate → source credibility weight in Classify. Makes source quality self-improving; better story than any single new source.

**Architecture note:** keep every new source as an ingest agent emitting the existing common output contract, so the pipeline never knows/cares where an item came from.

---

## Recommended build order
Full-text fetching → YouTube agent → Telegram → primary-source feeds (RBI/SEBI/PIB/NSE) → WhatsApp forward-bot (as a feature, not a scraper). **Skip Instagram, defer Twitter.**
