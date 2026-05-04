"""Users router for managing user settings."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DailyBrief, Subscription, User
from app.routers.auth import get_current_user
from app.schemas import DigestSettings, UserResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me/digest-settings", response_model=UserResponse)
async def update_digest_settings(
    settings: DigestSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.receive_digest = settings.receive_digest
    if settings.severity_threshold:
        current_user.severity_threshold = settings.severity_threshold.upper()
    if settings.subscribed_sources is not None:
        current_user.subscribed_sources = settings.subscribed_sources

    subscription = (
        db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    )
    if subscription:
        subscription.digest_time = settings.digest_time
        subscription.timezone = settings.timezone or "UTC"
    else:
        subscription = Subscription(
            user_id=current_user.id,
            digest_time=settings.digest_time,
            timezone=settings.timezone or "UTC",
        )
        db.add(subscription)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/digest-preview")
async def preview_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    brief = db.query(DailyBrief).order_by(DailyBrief.date.desc()).first()
    if not brief:
        return {"message": "No brief available"}

    email_service = EmailService()
    email_data = {
        "date": brief.date.strftime("%Y-%m-%d"),
        "executive_summary": brief.summary_md or "",
        "top_cves": brief.top_cves or [],
        "threat_themes": brief.threat_themes or [],
        "recommendations": (brief.recommendations_md or "").split("\n"),
        "high_priority_flags": brief.high_priority_flags or [],
        "unsubscribe_url": "#",
    }
    html = email_service.template.render(**email_data)
    return {"html": html}
