"""Intelligence items router."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.errors import NotFoundError
from app.models import IntelItem, JobStatus, ScrapeJob, User
from app.routers.auth import (
    get_current_user,
    get_optional_user,
    limiter,
    require_analyst,
)
from app.schemas import IntelItemResponse, ScrapeJobResponse
from app.services.scheduler import get_scheduler_service

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/items", response_model=List[IntelItemResponse])
async def get_intel_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = Query(None, description="Free-text search across title and raw_text"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get paginated intelligence items with filters."""
    query = db.query(IntelItem)

    if severity:
        query = query.filter(IntelItem.severity == severity.upper())
    if source:
        query = query.filter(IntelItem.source == source)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(IntelItem.title.ilike(like), IntelItem.raw_text.ilike(like)))

    offset = (page - 1) * limit
    return (
        query.order_by(IntelItem.created_at.desc()).offset(offset).limit(limit).all()
    )


@router.get("/items/{item_id}", response_model=IntelItemResponse)
async def get_intel_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    item = db.query(IntelItem).filter(IntelItem.id == item_id).first()
    if not item:
        raise NotFoundError("Item not found.")
    return item


@router.post("/scrape", response_model=ScrapeJobResponse, status_code=202)
@limiter.limit("10/minute")
async def trigger_scrape(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    """Trigger a scrape pipeline run. Analyst+ only. Returns a job id to poll."""
    job = ScrapeJob(
        status=JobStatus.PENDING,
        triggered_by=current_user.id,
        progress={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    scheduler = get_scheduler_service(SessionLocal)
    scheduler.kickoff_pipeline(job.id)
    return job


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise NotFoundError("Job not found.")
    return job


@router.get("/jobs", response_model=List[ScrapeJobResponse])
async def list_scrape_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(limit).all()
    )


@router.get("/sources/list")
async def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Distinct source values for filter dropdowns."""
    rows = db.query(IntelItem.source).distinct().all()
    return {"sources": sorted({r[0] for r in rows if r[0]})}


@router.get("/stats")
async def stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregate counters for the dashboard hero cards."""
    from collections import Counter
    from datetime import timedelta

    from sqlalchemy import func

    total = db.query(func.count(IntelItem.id)).scalar() or 0
    last_24h = (
        db.query(func.count(IntelItem.id))
        .filter(IntelItem.created_at >= datetime.utcnow() - timedelta(hours=24))
        .scalar()
        or 0
    )

    sev_rows = db.query(IntelItem.severity, func.count(IntelItem.id)).group_by(
        IntelItem.severity
    ).all()
    severity = {sev or "UNKNOWN": count for sev, count in sev_rows}

    src_rows = (
        db.query(IntelItem.source, func.count(IntelItem.id))
        .group_by(IntelItem.source)
        .all()
    )
    sources = sorted([{"source": s, "count": c} for s, c in src_rows], key=lambda x: -x["count"])

    last = (
        db.query(IntelItem)
        .order_by(IntelItem.created_at.desc())
        .limit(80)
        .all()
    )
    technique_counts: Counter[str] = Counter()
    for item in last:
        for t in item.mitre_techniques or []:
            technique_counts[t] += 1
    top_techniques = [
        {"technique": t, "count": c} for t, c in technique_counts.most_common(8)
    ]

    return {
        "total_items": total,
        "items_last_24h": last_24h,
        "severity": severity,
        "sources": sources,
        "top_techniques": top_techniques,
    }
