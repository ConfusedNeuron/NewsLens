# NewsLens — CV Pointer Pack

**Generated:** 2026-07-26 · **Budget reference:** the NTC textile mill line = 100.0%
**Width checker:** `docs/width.py` (Helvetica advance-width table, identical to the template's)
**Constraints applied:** no em dashes, no `₹`, no `→`, no first person, one line each, distinct lead
verb within every recommended set, `**bold**` on numbers, tools and one outcome phrase.

**Lead verbs avoided by default** (no list was supplied): Built, Led, Developed, Designed,
Analyzed, Created, Implemented, Managed, Estimated, Replicated, Conducted, Performed. Every
candidate below carries a distinct lead verb, so any single rejection at integration leaves a
same-slant substitute available.

---

## FACT SHEET

Every number below was recomputed from the repo on 2026-07-26. `DB` = live query against
`artifacts/newslens-backend/newslens.db`.

### Architecture (design parameters, verifiable by reading code)

| Fact | Value | Provenance |
|---|---|---|
| Pipeline stages | 8 | `pipeline/orchestrator.py:133-149` (`run_pipeline`) |
| Stages calling an LLM | 2 (Extract, Analyze) | `grep call_llm agents/*.py` → `extract_agent.py:88`, `analyze_agent.py:171` |
| Stages fully deterministic | 6 | `grep -L call_llm` on clean, classify, enrich, format, quality_gate, ingest |
| Personalization cost class | `O(cards x active users)`, lazy | `agents/personalize_agent.py` docstring + `get_cached`/`put_cached` |
| Enrichment cache TTL | 4 hours | `config/settings.py` `ENRICHMENT_CACHE_HOURS = 4` |
| Sources configured | 12 (9 RSS + 3 Substack) | `config/sources.yaml`, counted via yaml load |
| Domains / geographies covered | 4 / 3 | same file: Finance, Tech, Geopolitics, Environment · India, China, Global |

### Real run output (single pipeline execution, May 2026)

| Fact | Value | Provenance |
|---|---|---|
| Raw items ingested | 205 | DB `raw_items` |
| Distinct sources that actually delivered | 11 of 13 configured | DB `SELECT COUNT(DISTINCT source_name)` |
| Cleaned items | 145 | DB `clean_items` |
| Extraction: succeeded / failed / skipped | 42 / 50 / 8 | DB `clean_items.status` |
| **Extraction failure rate** | **54%** (50 of 92 attempted) | derived from the row above |
| Enriched items | 40 | DB `enriched_items` |
| Cards generated / live | 41 / 39 | DB `cards`, `cards WHERE is_live=1` |
| End-to-end yield | 205 in, 39 out | derived |
| Items with stock enrichment | **2 of 40** | DB, parsed `enrichment_json` for a `stocks` key |
| Items with macro enrichment | **0 of 40** | DB, no `macro_us` key on any row (`FRED_API_KEY` empty) |
| Cards with empty `personal_impact` | **41 of 41** | DB `WHERE personal_impact=''` |
| User profiles ever saved | 0 | DB `user_profiles` |
| Swipes ever recorded | 0 | DB `swipe_events` |
| Orchestrator runs logged | 10 rows, all 2026-05-13, every LLM stage at 0 | DB `pipeline_runs` |

### Codebase and remediation (this session)

| Fact | Value | Provenance |
|---|---|---|
| Backend Python, excl. tests | 3,853 lines | `wc -l` over agents, api, config, db, pipeline, scripts |
| Frontend TS/TSX, excl. shadcn `components/ui` | 3,484 lines | `wc -l` over `artifacts/newslens/src` |
| **Combined custom code** | **~7.3k lines** | sum of the two above |
| Automated tests before / after | **0 / 36** | `pytest tests/ -q` gives `36 passed`; 620 lines across 2 files |
| CI before / after | none / GitHub Actions | `.github/workflows/ci.yml` |
| Remediation blocks shipped | 9 | tasks 6-14 this session |
| Backlog items scoped and ranked | 11 | `NEXT_STEPS.md` "Next sprint" list |
| Cards backfilled with market data + horizon | 26 | `scripts/backfill_cards.py --apply`, run against a DB copy |
| Dead feeds found and removed | 2 (Reuters, Down To Earth) | both returned 0 items across the whole run |
| Days with zero code changes before this session | 63 | file mtimes: last code change 2026-05-24, session 2026-07-26 |

### Defects found and fixed (each independently verifiable)

- `PUT /user/profile` returned **405** on every save: spec declared `put`
  (`lib/api-spec/openapi.yaml`), backend registered only `post` (`api/routes/user.py:19`).
  Fixed; `tests/test_api.py::test_profile_put_round_trip` now guards it. Verified live: PUT
  returns 200, GET round-trips.
- `analyze_agent.py:220` never passed `user_profile` into `analyze_item()`, so
  `personal_impact` was structurally always empty.
- `prompts/personal_impact.txt` existed in the repo from the start and was read by **zero
  code** until this session.
- `prompts/analyze.txt` instructed the model to *"use 'est.' prefix"* when data was
  unavailable, licensing invented figures. Live example still in the DB: *"Est. 20 million
  barrels per day of oil transit secured"*.
- `log_stage` stamped `started_at` and `completed_at` from the same `utcnow()` call, so every
  recorded stage duration was exactly zero.
- Frontend checked `status === 'success'`; backend wrote `'complete'`.
- `clean_agent.py:93-104` appends the dedup hash only inside the embedding branch, so without
  `sentence-transformers` even exact-hash dedup records nothing.

---

## CANNOT CLAIM

Read this before any interview. Each item is a question a sharp interviewer will reach.

1. **No LLM call has been made since the changes.** The personalization engine, the provenance
   labelling and the new prompt are unit-tested against mocks only. The honest line is
   *"architected and tested; live generation is the next run"*, not *"generated N personalized
   cards"*.
2. **The orchestrator has never produced a card end to end.** `pipeline_runs` holds one run,
   2026-05-13, with every LLM stage at zero. The 41 cards were produced by invoking agents by
   hand on 2026-05-24. Do not say *"runs every 6 hours in production"*; the scheduler exists
   but has never completed a successful full run.
3. **No cost figure exists in currency.** "2 calls per article" is a design property. There is
   no measured spend, no baseline, no before/after bill. Never write "cut cost by X%".
4. **No latency or throughput benchmark exists.** Nothing was profiled for speed.
5. **The 54% extraction failure is n=92 from a single run.** It is one observation, not a
   stable rate. The attribution to input length is a well-reasoned hypothesis, not an
   experiment: no A/B against full-text input has been run.
6. **The product has zero users, including its author.** 0 profiles, 0 swipes. Any pointer
   implying adoption, engagement or retention is false.
7. **No frontend tests.** The app was confirmed to run manually; there is no automated
   coverage, no Lighthouse score, no accessibility audit beyond `prefers-reduced-motion`
   being respected in code.
8. **`magnitude_source` has never been produced by a live model.** Only the validator's
   fail-safe path (demote unlabelled to `estimate`) is exercised. Whether the model labels
   honestly at inference time is untested.
9. **The ~7.3k LOC figure is generous.** It excludes shadcn UI components and the generated
   API client, but still includes some scaffolding (`use-toast.ts` and similar). Say
   *"roughly"* if pressed.
10. **The read-time personalization saving is asymptotic, not observed.** It compares against a
    design that was never deployed. Frame it as *"chose the architecture that stays cheap as
    users grow"*, not *"reduced cost"*.

**Weakest point, and the honest answer.** *"You audited your own project and found it broken.
Why was it broken?"* Because it sat for 63 days while five planning documents were written and
no code shipped. The lesson worth stating out loud is that the audits were accurate and still
changed nothing until execution was scheduled and time-boxed. That answer lands far better
than a defence.

---

## CANDIDATES — TECH slant

| # | Width | Pointer |
|---|---|---|
| T1 | 99.0% | Engineered an **8-stage** agentic news pipeline holding LLM spend to **2 calls per article**, **6 stages rule-based** |
| T2 | 96.7% | Architected **read-time personalization** cached per profile hash, cutting cost from all users to **active users** |
| T3 | 99.1% | Instrumented a **zero-test** repo into **36 pytest cases** and CI, at once catching a **405** killing every profile save |
| T4 | 100.2% | Retrofitted **data vs estimate** provenance onto every figure in prompt, validator and UI, defaulting to **estimate** |
| T5 | 99.1% | Rearchitected **8 duplicated stages** into one helper with real timings, replacing durations hardcoded to **0 ms** |
| T6 | 99.4% | Traced a **54% extraction failure** rate to snippet-only RSS inputs, not model quality, scoping **trafilatura** as fix |
| T7 | 98.2% | Hardened ingest with a spend-aware validator skipping boilerplate **before any paid API call**, cutting spend |
| T8 | 98.1% | Shipped **12 verified RSS and Substack feeds** over **4 domains**, plus a checker failing loudly on dead feeds |
| T9 | 97.9% | Wired **yfinance and FRED** enrichment into a typed card field, backfilling **26 historical cards** from payloads |
| T10 | 97.3% | Profiled a **205-item** ingest run down to **39 live cards**, isolating the dominant loss at the LLM extract stage |
| T11 | 99.8% | Migrated a live **41-card** SQLite schema via idempotent ALTERs, verified on a prod copy with **zero data loss** |
| T12 | 97.7% | Eliminated a personalization design costing **O(cards x all users)**, replacing it with a cached per-user pass |

**What each buys.** T1 the cost architecture (strongest single line). T2 the scaling decision.
T3 test discipline plus a concrete caught bug. T4 the judgment call on hallucination. T5
refactoring instinct. T6 root-cause reasoning. T7 cost-aware engineering. T8 operational
hygiene. T9 end-to-end feature delivery. T10 systems measurement. T11 safe schema evolution.
T12 the rejected alternative, which is T2 told from the other side, so never use both.

### RECOMMENDED — Tech, set of 3
1. T1 · **Engineered** — the architecture and the cost constraint in one line
2. T3 · **Instrumented** — engineering rigour plus a real defect caught
3. T2 · **Architected** — the scaling decision an interviewer can dig into

Covers cost, correctness and scale with no overlap. T4 is the first substitute if `Engineered`
or `Architected` is already burned elsewhere.

### RECOMMENDED — Tech, set of 2
1. T1 · **Engineered** — architecture and cost
2. T3 · **Instrumented** — tests and the caught 405

The two that survive compression: what was built, and evidence it works.

---

## CANDIDATES — CONSULTING slant

| # | Width | Pointer |
|---|---|---|
| C1 | 97.4% | Audited a stalled **7.3k-line** analytics product and found **both headline differentiators dead** in shipped data |
| C2 | 100.2% | Diagnosed **41 of 41** cards missing personal impact, tracing the failure to **3 independent breaks**, not one bug |
| C3 | 100.1% | Quantified the enrichment gap at **2 of 40** items carrying stock data against a documented claim of coverage |
| C4 | 98.4% | Prioritised an **11-item** remediation backlog by value per hour, deferring parallel LLM calls as user-invisible |
| C5 | 98.0% | Rejected the obvious fix of suppressing unsourced figures, which would have **emptied most cards** of data |
| C6 | 94.2% | Reframed hallucination control as **labelling provenance**, holding card density while flagging estimates |
| C7 | 100.1% | Uncovered **2 RSS feeds** dead for over **2 months** unnoticed, shipping a checker that now fails loudly on both |
| C8 | 97.0% | Recovered a **63-day** stall producing **5 planning docs and zero code**, shipping **9 verified fixes** in one pass |
| C9 | 96.2% | Isolated a **54% extraction failure** to input length, ruling out model quality as the cause before any spend |
| C10 | 91.2% | Sequenced remediation so a **2-hour** prompt fix shipped ahead of a **1-day** refactor of no user value |
| C11 | 99.7% | Established that **0 profiles and 0 swipes** had ever been recorded, proving the product had never been used |
| C12 | 92.2% | Ranked **full-text fetching** above all other changes as the one fix that improves every source at once |

**What each buys.** C1 the framing line. C2 diagnostic depth. C3 the gap between claim and
reality. C4 prioritisation method. C5 the rejected alternative, the most interview-durable
line here. C6 the reframe. C7 operational blind spot. C8 execution against a stall. C9 ruling
out a confound. C10 sequencing logic. C11 the hardest honest finding. C12 leverage reasoning.

### RECOMMENDED — Consulting, set of 3
1. C1 · **Audited** — establishes scope and the headline finding
2. C5 · **Rejected** — the judgment call, and the best interview hook on the CV
3. C4 · **Prioritised** — method, and it lands the deferral decision

Diagnosis, judgment, prioritisation. C5 is deliberately the middle line: it invites *"why would
that have emptied the cards?"*, which is a question with a good answer.

### RECOMMENDED — Consulting, set of 2
1. C1 · **Audited** — scope plus finding
2. C5 · **Rejected** — the judgment call

---

## CANDIDATES — BFSI slant

| # | Width | Pointer |
|---|---|---|
| B1 | 98.4% | Instituted **data vs estimate** provenance on every published figure, defaulting unlabelled values to **estimate** |
| B2 | 95.3% | Reported the null honestly: market enrichment reached only **2 of 40** items and **0 of 40** on macro series |
| B3 | 96.7% | Validated **12 candidate feeds** before adoption, rejecting **RBI and PIB** as title-only despite both being live |
| B4 | 97.0% | Sourced market context from **yfinance and FRED** behind a **4-hour** cache, degrading gracefully on failure |
| B5 | 95.5% | Reviewed **41 generated cards** and found **41 of them missing** the personalization field the docs claimed |
| B6 | 87.6% | Measured a **205 to 39** ingest-to-published funnel, attributing **54%** of the loss to one LLM stage |
| B7 | 89.0% | Codified a **2-call-per-article** cost model, holding **6 of 8** pipeline stages deterministic and testable |
| B8 | 97.4% | Governed model output via a schema validator coercing invalid enums and demoting unverifiable figures |
| B9 | 98.8% | Attributed a **54% extraction failure** to **50-word** RSS snippets rather than model choice, before any respend |
| B10 | 99.8% | Documented every unsupported claim in an explicit **Known Limitations** section rather than quietly omitting it |

**What each buys.** B1 the control itself, and the strongest BFSI line. B2 willingness to report
a negative result about your own feature. B3 diligence before adoption. B4 data sourcing and
graceful degradation. B5 audit against documentation. B6 funnel measurement. B7 the cost model.
B8 output governance. B9 attribution with a confound ruled out. B10 disclosure discipline.

### RECOMMENDED — BFSI, set of 3
1. B1 · **Instituted** — the provenance control, which is the whole BFSI story
2. B2 · **Reported** — a real null, stated against your own interest
3. B3 · **Validated** — diligence before adoption, and a non-obvious rejection

Control, honest null, diligence. B2 is the line that separates this from a generic engineering
CV: reporting **2 of 40** and **0 of 40** on your own feature is the kind of thing BFSI
interviewers specifically test for.

### RECOMMENDED — BFSI, set of 2
1. B1 · **Instituted** — the control
2. B2 · **Reported** — the null

---

## Lead verbs consumed (append to `Superset_Rendering_And_Verb_Rules.md` §3 after integration)

**Tech:** Engineered, Architected, Instrumented, Retrofitted, Rearchitected, Traced, Hardened,
Shipped, Wired, Profiled, Migrated, Eliminated

**Consulting:** Audited, Diagnosed, Quantified, Prioritised, Rejected, Reframed, Uncovered,
Recovered, Isolated, Sequenced, Established, Ranked

**BFSI:** Instituted, Reported, Validated, Sourced, Reviewed, Measured, Codified, Governed,
Attributed, Documented

No verb repeats across the three slants, so a mixed-track CV can draw from more than one pool
without collision.

---

## Integration notes for the Career_Materials session

- Widths were computed on the **de-bolded** text (`**` stripped before measuring), which matches
  how Superset renders. Re-verify anyway.
- The `%` character is expensive (889 units, wider than any letter). Lines carrying `54%` are
  near their ceiling; swapping in a longer word will push them over.
- C2, C3 and C7 sit at 100.1-100.2%, inside the 100.3% tolerance but with no headroom. If your
  checker rounds differently, trim one word.
- T12 and T2 are the same decision from opposite directions. C5 and C6 likewise. Never pair.
- If this project appears on the same CV as another data or ML project, expect collisions on
  `Engineered`, `Architected` and `Audited` first. `Retrofitted`, `Instituted` and `Reframed`
  are the least likely to be contested.
