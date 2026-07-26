"""
Pipeline agent unit tests with a mocked LLM.

No network, no API key, no cost. The point of these is to pin down the two
behaviours that decide whether this pipeline is trustworthy or expensive:

  1. Garbage input is skipped BEFORE any LLM call is made (spend-aware validation).
  2. A magnitude the model did not explicitly source is never labelled as sourced.
"""
import json

import pytest


# ---------------------------------------------------------------------------
# Input validation — must not spend money on garbage
# ---------------------------------------------------------------------------

def test_short_text_is_rejected_before_llm_call():
    from agents.llm_client import validate_extract_input, InputValidationError

    with pytest.raises(InputValidationError):
        validate_extract_input("Too short.")


def test_boilerplate_is_rejected():
    from agents.llm_client import validate_extract_input, InputValidationError

    boilerplate = "Please enable cookies to continue. " * 20
    with pytest.raises(InputValidationError):
        validate_extract_input(boilerplate)


def test_real_article_text_passes_validation():
    from agents.llm_client import validate_extract_input

    text = (
        "The Reserve Bank of India held the repo rate at 6.5 percent on Friday, "
        "marking the fourth consecutive meeting without a change. Governor said "
        "inflation had moderated to 4.8 percent while growth stayed resilient at "
        "7.2 percent for the quarter."
    )
    validate_extract_input(text)  # must not raise


def test_extract_run_makes_no_llm_call_without_api_key(temp_db, monkeypatch):
    """
    With no key configured the extract station must return 0 quietly rather than
    raising — the pipeline has to survive a missing key without taking down a run.
    """
    import agents.extract_agent as ea

    calls = []
    monkeypatch.setattr(ea, "COMMANDCODE_API_KEY", "")
    monkeypatch.setattr(ea, "call_llm", lambda *a, **k: calls.append(1))

    assert ea.run() == 0
    assert calls == []


def test_extract_skips_garbage_without_calling_llm(temp_db, monkeypatch):
    """A pending row whose text is junk must be marked skipped, not sent to the LLM."""
    import uuid
    from datetime import datetime
    from db.database import get_conn, fetchone
    import agents.extract_agent as ea

    raw_id = str(uuid.uuid4())
    clean_id = str(uuid.uuid4())
    with get_conn() as conn:
        # clean_items.raw_id is a real FK — the row must exist first.
        conn.execute(
            """INSERT INTO raw_items (id, source_type, source_name, url, raw_text,
                                      metadata_json, ingested_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (raw_id, "rss", "Test Source", "https://example.com/junk",
             "404 not found", "{}", datetime.utcnow().isoformat(), "cleaned"),
        )
        conn.execute(
            """INSERT INTO clean_items (id, raw_id, clean_text, dedup_hash, language, status, cleaned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (clean_id, raw_id, "404 not found", "hash-1", "en", "pending",
             datetime.utcnow().isoformat()),
        )

    calls = []
    monkeypatch.setattr(ea, "COMMANDCODE_API_KEY", "test-key")
    monkeypatch.setattr(ea, "get_llm_client", lambda: object())
    monkeypatch.setattr(ea, "call_llm", lambda *a, **k: calls.append(1))

    assert ea.run() == 0
    assert calls == [], "garbage input must never reach the LLM"
    assert fetchone("SELECT status FROM clean_items WHERE id = ?", (clean_id,))["status"] == "skipped"


# ---------------------------------------------------------------------------
# Magnitude provenance — must fail safe
# ---------------------------------------------------------------------------

def _analysis(**overrides):
    base = {
        "summary_60w": "The central bank held rates steady.",
        "what_happened": "RBI held the repo rate at 6.5%.",
        "key_number": "6.5%",
        "winners": [{"who": "Borrowers", "why": "EMIs flat", "magnitude": "6.5%",
                     "magnitude_source": "data"}],
        "losers": [{"who": "Savers", "why": "Rates capped", "magnitude": "est. 40bps"}],
        "india_angle": "a", "usa_angle": "b", "china_angle": "c",
        "confidence": "high", "time_horizon": "short",
    }
    base.update(overrides)
    return base


def test_missing_magnitude_source_is_demoted_to_estimate():
    from agents.analyze_agent import validate_analysis_output

    data = _analysis()
    assert validate_analysis_output(data) is True
    assert data["winners"][0]["magnitude_source"] == "data"
    assert data["losers"][0]["magnitude_source"] == "estimate"


def test_bogus_magnitude_source_is_demoted_to_estimate():
    from agents.analyze_agent import validate_analysis_output

    data = _analysis(
        winners=[{"who": "X", "why": "y", "magnitude": "1", "magnitude_source": "verified"}]
    )
    assert validate_analysis_output(data) is True
    assert data["winners"][0]["magnitude_source"] == "estimate"


def test_data_label_is_preserved():
    from agents.analyze_agent import validate_analysis_output

    data = _analysis()
    validate_analysis_output(data)
    assert data["winners"][0]["magnitude_source"] == "data"


def test_invalid_enums_are_coerced_not_discarded():
    from agents.analyze_agent import validate_analysis_output

    data = _analysis(confidence="extremely high", time_horizon="forever")
    assert validate_analysis_output(data) is True
    assert data["confidence"] == "medium"
    assert data["time_horizon"] == "short"


def test_missing_required_field_fails_validation():
    from agents.analyze_agent import validate_analysis_output

    data = _analysis()
    del data["winners"]
    assert validate_analysis_output(data) is False


# ---------------------------------------------------------------------------
# Personalization cache semantics
# ---------------------------------------------------------------------------

def test_profile_hash_ignores_irrelevant_fields():
    from agents.personalize_agent import profile_hash

    a = {"user_id": "u", "city": "Pune", "updated_at": "2026-01-01"}
    b = {"user_id": "u", "city": "Pune", "updated_at": "2026-07-26"}
    assert profile_hash(a) == profile_hash(b), "updated_at must not invalidate the cache"


def test_profile_hash_changes_with_meaningful_edit():
    from agents.personalize_agent import profile_hash

    a = {"city": "Pune", "income_type": "Salaried Employee"}
    b = {"city": "Mumbai", "income_type": "Salaried Employee"}
    assert profile_hash(a) != profile_hash(b)


def test_personalize_returns_empty_without_profile(temp_db):
    from agents.personalize_agent import personalize_cards

    assert personalize_cards([{"id": "card-1"}], "nobody") == {}


def test_personalize_prompt_includes_profile_fields(temp_db):
    """The prompt must actually carry the user's details — this is the whole feature."""
    from agents.personalize_agent import build_prompt

    card = {
        "id": "c1",
        "headline": "RBI holds rates",
        "what_happened": "RBI held the repo rate at 6.5%.",
        "summary_60w": "Rates unchanged.",
        "key_number": "6.5%",
        "winners_json": json.dumps([{"who": "Borrowers", "why": "flat EMIs"}]),
        "losers_json": "[]",
        "india_angle": "Supportive for rate-sensitive sectors.",
    }
    profile = {
        "user_id": "u",
        "income_type": "Salaried Employee",
        "sector_exposure": "IT / Software",
        "investment_profile": "Mutual funds / SIPs",
        "city": "Bengaluru",
        "companies_of_interest": "Infosys",
    }

    prompt = build_prompt(card, profile)
    assert "Bengaluru" in prompt
    assert "Mutual funds / SIPs" in prompt
    assert "Infosys" in prompt
    assert "{city}" not in prompt, "template placeholder was left unreplaced"


def test_quality_gate_discards_card_with_no_winners_or_losers():
    from pipeline.quality_gate import evaluate_card

    verdict = evaluate_card({
        "confidence_badge": "high",
        "summary_60w": "A reasonably long summary that clears the twenty word floor "
                       "so the discard decision turns on the empty winners and losers.",
        "headline": "Something happened somewhere today",
        "winners_json": "[]",
        "losers_json": "[]",
    })
    assert verdict == "discard"


def test_quality_gate_approves_a_complete_card():
    from pipeline.quality_gate import evaluate_card

    verdict = evaluate_card({
        "confidence_badge": "high",
        "summary_60w": "The central bank held the repo rate steady at six point five "
                       "percent for a fourth consecutive meeting, citing moderating "
                       "inflation and resilient growth across the economy.",
        "headline": "RBI holds repo rate at 6.5 percent",
        "winners_json": json.dumps([{"who": "Borrowers", "why": "flat EMIs", "magnitude": "6.5%"}]),
        "losers_json": json.dumps([{"who": "Savers", "why": "capped returns", "magnitude": "40bps"}]),
        "key_number": "6.5%",
    })
    assert verdict == "approve"
