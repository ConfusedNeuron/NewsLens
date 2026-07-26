"""User profile API routes."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.database import fetchone, get_conn
from api.models import UserProfileRequest, UserProfileResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.put("/user/profile", response_model=UserProfileResponse)
@router.post("/user/profile", response_model=UserProfileResponse)
def save_profile(profile: UserProfileRequest):
    """
    Create or update a user profile (upsert).

    Registered on BOTH verbs deliberately. The OpenAPI spec declares `put`, so the
    generated Orval client sends PUT — but only `post` was registered here, which
    meant every profile save from onboarding and from /profile returned 405, and the
    frontend mutation had no error handler to surface it. The result was that no
    profile was ever saved and `personal_impact` could never render.

    PUT is the spec-correct verb for an idempotent upsert; POST is kept so that any
    older client build keeps working. tests/test_api.py asserts both.
    """
    now = datetime.utcnow().isoformat()
    existing = fetchone("SELECT user_id FROM user_profiles WHERE user_id = ?", (profile.user_id,))

    with get_conn() as conn:
        if existing:
            conn.execute(
                """UPDATE user_profiles SET income_type=?, sector_exposure=?, investment_profile=?,
                   city=?, companies_of_interest=?, updated_at=? WHERE user_id=?""",
                (profile.income_type, profile.sector_exposure, profile.investment_profile,
                 profile.city, profile.companies_of_interest, now, profile.user_id),
            )
        else:
            conn.execute(
                """INSERT INTO user_profiles
                   (user_id, income_type, sector_exposure, investment_profile, city, companies_of_interest, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (profile.user_id, profile.income_type, profile.sector_exposure,
                 profile.investment_profile, profile.city, profile.companies_of_interest, now, now),
            )

    row = fetchone("SELECT * FROM user_profiles WHERE user_id = ?", (profile.user_id,))
    return UserProfileResponse(**row)


@router.get("/user/profile", response_model=Optional[UserProfileResponse])
def get_profile(user_id: str):
    row = fetchone("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfileResponse(**row)
