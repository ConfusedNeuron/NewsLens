"""Pydantic models for API request/response schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Winner(BaseModel):
    who: str
    why: str
    magnitude: str
    # Provenance of `magnitude`: "data" = taken from the enrichment payload or from
    # facts extracted out of the article; "estimate" = the model's own inference.
    # Defaults to "estimate" so an unlabelled figure can never be mistaken for a
    # sourced one. See prompts/analyze.txt MAGNITUDE RULES.
    magnitude_source: str = "estimate"


class CardAngles(BaseModel):
    india: Optional[str] = None
    usa: Optional[str] = None
    china: Optional[str] = None


class CardTags(BaseModel):
    domain: list[str] = []
    geo: list[str] = []


class CardSource(BaseModel):
    name: str
    url: str


class MarketQuote(BaseModel):
    """One instrument's snapshot, flattened for display."""
    label: str
    symbol: Optional[str] = None
    price: Optional[float] = None
    pct_change_1d: Optional[float] = None
    currency: Optional[str] = None


class CardResponse(BaseModel):
    id: str
    headline: str
    summary: str
    key_number: Optional[str] = None
    winners: list[Winner] = []
    losers: list[Winner] = []
    personal_impact: Optional[str] = None
    angles: CardAngles = CardAngles()
    tags: CardTags = CardTags()
    confidence: str = "medium"
    # immediate | short | long — was hardcoded to "Near-term" in the UI because it
    # never made it out of the pipeline.
    time_horizon: Optional[str] = None
    # The enrichment snapshot the analysis was anchored to. Lets the UI show the
    # actual numbers instead of leaving them buried in prose.
    market_data: list[MarketQuote] = []
    source: CardSource = CardSource(name="", url="")
    # True for demo rows inserted by db/seed.py. Clients should label these; they are
    # invented examples, not real news.
    is_seed: bool = False
    created_at: str


class CardListResponse(BaseModel):
    cards: list[CardResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class SwipeRequest(BaseModel):
    direction: str = Field(..., pattern="^(left|right)$")
    user_id: Optional[str] = None


class UserProfileRequest(BaseModel):
    user_id: str
    income_type: Optional[str] = None
    sector_exposure: Optional[str] = None
    investment_profile: Optional[str] = None
    city: Optional[str] = None
    companies_of_interest: Optional[str] = None


class UserProfileResponse(BaseModel):
    user_id: str
    income_type: Optional[str] = None
    sector_exposure: Optional[str] = None
    investment_profile: Optional[str] = None
    city: Optional[str] = None
    companies_of_interest: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SourceStatus(BaseModel):
    name: str
    source_type: str
    last_run: Optional[str] = None
    items_today: int = 0
    status: str = "unknown"


class PipelineRunLog(BaseModel):
    id: str
    stage: str
    items_processed: int = 0
    items_failed: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str
    error_log: Optional[str] = None
