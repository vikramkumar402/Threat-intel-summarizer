"""Authentication router."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Request, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.errors import ConflictError, ForbiddenError, UnauthorizedError
from app.models import RefreshToken, Role, User
from app.schemas import RefreshRequest, Token, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
limiter = Limiter(key_func=get_remote_address)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(email: str, role: str) -> tuple[str, int]:
    settings = get_settings()
    expires_minutes = settings.access_token_minutes
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": email, "role": role, "type": "access", "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_minutes * 60


def issue_refresh_token(db: Session, user: User) -> str:
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(raw),
        expires_at=datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days),
    )
    db.add(rt)
    db.commit()
    return raw


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    if settings.disable_auth:
        user = db.query(User).filter(User.role == Role.ADMIN).first()
        if user is None:
            user = User(
                email="anonymous@local",
                hashed_password="!",
                role=Role.ADMIN,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    if credentials is None:
        raise UnauthorizedError("Authentication required.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type.")
        email = payload.get("sub")
        if email is None:
            raise UnauthorizedError("Invalid token.")
    except JWTError as exc:
        raise UnauthorizedError("Invalid token.") from exc

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")
    return user


def require_role(*roles: str):
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient role.")
        return current_user

    return _checker


require_admin = require_role(Role.ADMIN)
require_analyst = require_role(Role.ANALYST, Role.ADMIN)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if token present, else optionally allow anonymous access."""
    settings = get_settings()
    if not settings.disable_auth and credentials is None:
        raise UnauthorizedError("Authentication required.")
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type.")
        email = payload.get("sub")
        if email is None:
            raise UnauthorizedError("Invalid token.")
    except JWTError as exc:
        raise UnauthorizedError("Invalid token.") from exc

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")
    return user


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    user_data: UserRegister = Body(...),
    db: Session = Depends(get_db),
):
    """Register a new user (default role: viewer)."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ConflictError("Email already registered.")

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        is_active=True,
        role=Role.VIEWER,
        receive_digest=True,
        subscribed_sources=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    credentials: UserLogin = Body(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise UnauthorizedError("Invalid credentials.")
    if not user.is_active:
        raise ForbiddenError("Account inactive.")

    access_token, expires_in = create_access_token(user.email, user.role)
    refresh_token = issue_refresh_token(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)


@router.post("/refresh", response_model=Token)
async def refresh_tokens(
    request: Request,
    body: RefreshRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Rotate a refresh token: revoke the old one, issue a new pair."""
    token_hash = _hash_refresh(body.refresh_token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt is None or rt.revoked_at is not None or rt.expires_at < datetime.utcnow():
        raise UnauthorizedError("Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == rt.user_id, User.is_active.is_(True)).first()
    if user is None:
        raise UnauthorizedError("User inactive.")

    rt.revoked_at = datetime.utcnow()
    db.commit()

    access_token, expires_in = create_access_token(user.email, user.role)
    new_refresh = issue_refresh_token(db, user)
    return Token(access_token=access_token, refresh_token=new_refresh, expires_in=expires_in)


@router.post("/logout")
async def logout(
    body: RefreshRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke the supplied refresh token."""
    token_hash = _hash_refresh(body.refresh_token)
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash, RefreshToken.user_id == current_user.id)
        .first()
    )
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.utcnow()
        db.commit()
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
