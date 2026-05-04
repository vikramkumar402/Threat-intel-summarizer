"""Admin-only management endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import NotFoundError, ValidationError
from app.models import Role, SourceHealth, User
from app.routers.auth import require_admin
from app.schemas import SourceHealthResponse, UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if role not in Role.ALL:
        raise ValidationError(f"Role must be one of {Role.ALL}.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found.")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}/active", response_model=UserResponse)
async def set_user_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found.")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/sources", response_model=List[SourceHealthResponse])
async def list_sources(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(SourceHealth).order_by(SourceHealth.source.asc()).all()


@router.put("/sources/{source}/enabled", response_model=SourceHealthResponse)
async def set_source_enabled(
    source: str,
    enabled: bool,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sh = db.query(SourceHealth).filter(SourceHealth.source == source).first()
    if not sh:
        raise NotFoundError("Source not found.")
    sh.enabled = enabled
    sh.consecutive_failures = 0 if enabled else sh.consecutive_failures
    db.commit()
    db.refresh(sh)
    return sh
