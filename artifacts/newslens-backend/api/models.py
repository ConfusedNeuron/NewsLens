"""Pydantic models for API request/response schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Winner(BaseModel):
    who: str
    why: str
    magnitude: str


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
    source: CardSource = CardSource(name="", url="")
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
