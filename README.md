# NewsLens

A personal news intelligence system for Indian professionals. It ingests news from a
dozen sources, uses an LLM to work out **who wins and who loses** from each story, and
serves the result as a swipeable card feed with an India / USA / China breakdown.

The design constraint that shaped everything: it has to run on a personal budget.

---

## How it works

```
Ingest → Clean → Extract* → Classify → Enrich → Analyze* → Format → QualityGate → live card
         (RSS,   (dedup,    (LLM #1)   (rules)  (yfinance/ (LLM #2)  (map to     (rules)
      Substack)  boilerplate)                     FRED)              card schema)
```

`*` are the only two stages that call an LLM. The other six are deterministic Python.

**Two LLM calls per article, and not one more.** Classification, enrichment, formatting
and the quality gate are all rules-based, so they cost nothing, run in milliseconds, and
can be unit-tested. Roughly 200 short calls a day keeps this in free-tier territory.

Each stage polls for `status = 'pending'` rows and writes its output to its own table.
That means a stage can crash without losing the run — the next run picks up exactly
what was dropped. It also means you can inspect what any stage produced by reading one
table.

---

## The two things worth explaining

### 1. Every figure carries its provenance

Cards attach numbers to claims — "Home loan borrowers: EMIs stay flat (6.5% repo rate
held)". Some of those numbers come from the enrichment payload; others are the model's
own inference. Presenting both the same way makes neither trustworthy.

So every winner and loser carries `magnitude_source`:

- **`data`** — the figure appears in the enrichment payload or in facts extracted from
  the article. Rendered normally.
- **`estimate`** — the model inferred it. Rendered muted, with an `est` chip and a
  tooltip saying it is not from a verified source.

Validation **fails safe**: anything unlabelled, malformed, or unrecognised is demoted to
`estimate`. An inference can never be presented as sourced, including on the cards
generated before this field existed.

The alternative — suppressing unsourced figures entirely — was rejected. While RSS
snippets are the only input, most magnitudes would become empty and the cards would be
worse, not more honest. Labelling keeps the cards full and lets the reader calibrate.
Once full-text fetching lands, more figures shift from `estimate` to `data` on their own.

### 2. Personalization happens at read time, not generation time

Cards are generated **once, globally**. The analyze station doesn't know who's reading,
and deliberately leaves `personal_impact` empty.

`GET /cards/personalized?user_id=…` fills it in on demand: for each card, look for a
cached `(card_id, user_id)` row; on a miss, one short LLM call generates it and the
result is cached against a hash of the profile that produced it. Editing your profile
changes the hash, which invalidates your rows and nobody else's.

The obvious shortcut — personalize inside the analyze station — was rejected because:

- the card is shared, so one user's impact makes it wrong for everyone else;
- cost would be `O(cards × all users)` at generation time, using the expensive
  ~1200-token analyze prompt, paid whether or not anyone ever reads the card.

Read-time is `O(cards × active users)`, paid lazily, on a ~120-token prompt. A user who
never opens the app costs nothing.

---

## Running it

```bash
# Backend
cd artifacts/newslens-backend
pip install -r requirements.txt
cp .env.example .env          # add COMMANDCODE_API_KEY
python -m api.main            # http://localhost:8000

# One pipeline run
python pipeline/orchestrator.py

# Frontend
pnpm install && pnpm --filter newslens dev   # http://localhost:5173
```

```bash
pytest tests/ -q                  # 36 tests, no network, no API key needed
python scripts/verify_feeds.py    # are all sources alive AND carrying body text?
python db/seed.py --demo          # insert demo cards (flagged is_seed)
python db/seed.py --clear         # remove them
```

`verify_feeds.py` exists because two feeds returned zero items for over two months and
nothing noticed — a dead feed and a slow news day look identical to the ingest agent.

**Demo cards are invented.** "Nifty 50 Crosses 27,000" never happened. They're flagged
`is_seed` in the database and the API, and they are never inserted automatically.

---

## Configuration

| Variable | Purpose |
|---|---|
| `COMMANDCODE_API_KEY` | LLM key. Any OpenAI-compatible provider. |
| `LLM_BASE_URL` | Defaults to NVIDIA NIM. See `config/settings.py` for alternatives. |
| `FRED_API_KEY` | Optional. Without it, cards carry no US macro data. |
| `REDDIT_CLIENT_ID` / `_SECRET` | Optional. Reddit ingest is off until both are set. |
| `CORS_ORIGINS` | Comma-separated. Defaults to localhost dev ports. |
| `ENABLE_SCHEDULER` | Set `0` to stop the 6-hourly job from starting. |

Switching model or provider is a two-line change in `config/settings.py` — nothing else
knows which model is in use.

---

## Known limitations

Stated plainly, because a reviewer will find these anyway.

- **Input is RSS snippets, not full articles.** ~50-100 words per item. This is the root
  cause of the extraction failure rate and of how often the model has to estimate rather
  than cite. `trafilatura` between Ingest and Clean is the single highest-value next
  change, and it improves every card from every source.
- **Deduplication is in-memory** and resets on restart. `dedup_hash` is written to
  `clean_items` but never read back.
- **Stock enrichment is sparse.** `COMPANY_TICKER_MAP` is a hardcoded lookup, so most
  articles match nothing and get commodities only.
- **Single-tenant.** `user_id` is hardcoded to `default_user`; there is no auth. The
  personalization architecture supports multiple users; the identity layer doesn't exist.
- **`hold` verdicts are terminal.** The quality gate can hold a card, but there is no
  review queue, so held cards stay invisible.
- **LLM calls are sequential** with a delay between them. Fine at ~30 items per run.
- **Gmail and YouTube ingest are stubs** that return 0.
- **Saved cards aren't retrievable.** Swipes are recorded but nothing reads them back.

---

## Repository layout

```
artifacts/newslens-backend/   FastAPI + the pipeline (the real system)
  agents/                     one module per station
  pipeline/                   orchestrator + quality gate
  prompts/                    extract.txt, analyze.txt, personal_impact.txt
  config/                     settings.py, sources.yaml, sop.yaml
  tests/                      pytest — mocked LLM, no network
artifacts/newslens/           React + Vite frontend
lib/api-spec/                 OpenAPI spec (source of truth for the client)
lib/api-client-react/         Orval-generated typed client
docs/archive/                 superseded audits and status docs
```

`GROUND_TRUTH.md` records what is actually built versus what the older specs claim.
`NEXT_STEPS.md` is the working backlog. If any other document disagrees with those two,
those two win.
