"""Daily briefs router."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import NotFoundError, ValidationError
from app.models import DailyBrief, User
from app.routers.auth import get_optional_user
from app.schemas import DailyBriefResponse

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("/latest", response_model=DailyBriefResponse)
async def get_latest_brief(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    brief = db.query(DailyBrief).order_by(DailyBrief.date.desc()).first()
    if not brief:
        raise NotFoundError("No brief available.")
    return brief


@router.get("", response_model=List[DailyBriefResponse])
@router.get("/", response_model=List[DailyBriefResponse], include_in_schema=False)
async def list_briefs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    offset = (page - 1) * limit
    return (
        db.query(DailyBrief)
        .order_by(DailyBrief.date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{brief_date}", response_model=DailyBriefResponse)
async def get_brief_by_date(
    brief_date: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get brief for a specific date (YYYY-MM-DD).

    Bug fix: previously the filter was `date >= X AND date < X`, which is
    impossible. The brief is stored at `datetime(date)`, so we match the
    full UTC calendar day [day, day+1).
    """
    try:
        target = datetime.strptime(brief_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD.") from exc

    next_day = target + timedelta(days=1)
    brief = (
        db.query(DailyBrief)
        .filter(DailyBrief.date >= target, DailyBrief.date < next_day)
        .first()
    )
    if not brief:
        raise NotFoundError("Brief not found for this date.")
    return brief
