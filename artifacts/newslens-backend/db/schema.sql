-- Raw ingested items
CREATE TABLE IF NOT EXISTS raw_items (
    id TEXT PRIMARY KEY,
    source_type TEXT,
    source_name TEXT,
    url TEXT UNIQUE,
    raw_text TEXT,
    metadata_json TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- After cleaning + dedup
CREATE TABLE IF NOT EXISTS clean_items (
    id TEXT PRIMARY KEY,
    raw_id TEXT REFERENCES raw_items(id),
    clean_text TEXT,
    language TEXT,
    word_count INTEGER,
    dedup_hash TEXT,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- After LLM extraction
CREATE TABLE IF NOT EXISTS extracted_items (
    id TEXT PRIMARY KEY,
    clean_id TEXT REFERENCES clean_items(id),
    headline TEXT,
    entities_json TEXT,
    event_type TEXT,
    numbers_mentioned TEXT,
    geography_primary TEXT,
    sectors TEXT,
    time_horizon TEXT,
    source_credibility TEXT,
    confidence TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- After classification
CREATE TABLE IF NOT EXISTS classified_items (
    id TEXT PRIMARY KEY,
    extracted_id TEXT REFERENCES extracted_items(id),
    domain_tags TEXT,
    geo_tags TEXT,
    importance_score REAL,
    is_cross_domain BOOLEAN DEFAULT FALSE,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- After enrichment
CREATE TABLE IF NOT EXISTS enriched_items (
    id TEXT PRIMARY KEY,
    classified_id TEXT REFERENCES classified_items(id),
    enrichment_json TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- Final cards
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    enriched_id TEXT,
    headline TEXT,
    summary_60w TEXT,
    what_happened TEXT,
    key_number TEXT,
    winners_json TEXT,
    losers_json TEXT,
    india_angle TEXT,
    usa_angle TEXT,
    china_angle TEXT,
    personal_impact TEXT,
    domain_tags TEXT,
    geo_tags TEXT,
    confidence_badge TEXT,
    -- immediate | short | long. Produced by both the extract and analyze stations
    -- but never propagated to the card until 2026-07-26, which is why the UI showed
    -- a hardcoded "Near-term" on every card regardless of content.
    time_horizon TEXT,
    -- JSON snapshot of the enrichment payload (yfinance / FRED) that the analyze
    -- station saw. Stored on the card so the numbers behind an analysis can be shown
    -- and audited, rather than only existing inside the prompt.
    market_data TEXT,
    source_name TEXT,
    source_url TEXT,
    is_live BOOLEAN DEFAULT FALSE,
    -- TRUE for demo/seed rows. Seed cards are invented, not real news; without this
    -- flag they were indistinguishable from pipeline output in the API and the UI.
    is_seed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles (session-based, no full auth)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    income_type TEXT,
    sector_exposure TEXT,
    investment_profile TEXT,
    city TEXT,
    companies_of_interest TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Swipe feedback
CREATE TABLE IF NOT EXISTS swipe_events (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    card_id TEXT,
    direction TEXT,
    swiped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline run log
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id TEXT PRIMARY KEY,
    stage TEXT,
    items_processed INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT DEFAULT 'running',
    error_log TEXT
);

-- Enrichment cache
CREATE TABLE IF NOT EXISTS enrichment_cache (
    key TEXT PRIMARY KEY,
    value_json TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Per-user personalization of a global card.
--
-- Cards are generated ONCE, globally, by the analyze station. Personalization is a
-- separate, much cheaper pass keyed by (card, user) and produced lazily the first
-- time a user actually requests that card, then cached here forever.
--
-- This is deliberately not done inside the analyze station. Baking one user's profile
-- into the shared card would make the card wrong for everyone else and would cost one
-- expensive analyze call per user per article. Here the cost is:
--     O(cards)                        for the global analysis, plus
--     O(cards x ACTIVE users), lazily for personalization
-- so a user who never opens the app costs nothing.
CREATE TABLE IF NOT EXISTS card_personalizations (
    card_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    personal_impact TEXT,
    -- Hash of the profile that produced this text. When the user edits their profile
    -- the hash changes and the row is regenerated instead of serving stale impact.
    profile_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (card_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_card_personalizations_user ON card_personalizations(user_id);

CREATE INDEX IF NOT EXISTS idx_raw_items_url ON raw_items(url);
CREATE INDEX IF NOT EXISTS idx_raw_items_status ON raw_items(status);
CREATE INDEX IF NOT EXISTS idx_clean_items_raw_id ON clean_items(raw_id);
CREATE INDEX IF NOT EXISTS idx_cards_is_live ON cards(is_live);
CREATE INDEX IF NOT EXISTS idx_cards_created_at ON cards(created_at);
CREATE INDEX IF NOT EXISTS idx_cards_domain_tags ON cards(domain_tags);
CREATE INDEX IF NOT EXISTS idx_cards_geo_tags ON cards(geo_tags);
CREATE INDEX IF NOT EXISTS idx_enrichment_cache_expires ON enrichment_cache(expires_at);
