"""Main FastAPI application."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.database import SessionLocal, engine
from app.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware import RequestContextMiddleware
from app.models import Base
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import briefs as briefs_router
from app.routers import intel as intel_router
from app.routers import users as users_router
from app.routers.auth import limiter as auth_limiter
from app.services.scheduler import get_scheduler_service, seed_admin_user

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title="Threat Intelligence Summarizer",
    description="Automated daily threat intelligence platform",
    version="1.1.0",
)

app.state.limiter = auth_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
        settings.app_base_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id"],
)

app.include_router(auth_router.router)
app.include_router(intel_router.router)
app.include_router(briefs_router.router)
app.include_router(users_router.router)
app.include_router(admin_router.router)


@app.on_event("startup")
async def startup_event() -> None:
    logger.info(
        "starting",
        llm_provider=settings.llm_provider_normalized,
        email_provider=settings.email_provider_normalized,
        aws=settings.aws_configured,
    )
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()

    scheduler = get_scheduler_service(SessionLocal)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    scheduler = get_scheduler_service(SessionLocal)
    scheduler.shutdown()
    logger.info("shutdown_complete")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "threat-intel-summarizer", "version": "1.1.0"}


@app.get("/ready")
async def readiness_check():
    checks = {
        "db": False,
        "llm_provider": settings.llm_provider_normalized,
        "email_provider": settings.email_provider_normalized,
    }
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        checks["db"] = True
    except Exception as exc:  # noqa: BLE001
        checks["db_error"] = str(exc)
    status = "ready" if checks["db"] else "degraded"
    return JSONResponse({"status": status, "checks": checks})


@app.get("/")
async def root():
    return {"message": "Threat Intelligence Summarizer API", "docs": "/docs"}


@app.get("/unsubscribe")
async def unsubscribe(request: Request, token: str):
    """One-click unsubscribe via signed token from email digests."""
    from app.services.email_service import EmailService

    db = SessionLocal()
    try:
        from app.models import User

        user_id = EmailService().verify_unsubscribe_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.receive_digest = False
            db.commit()
        return {"status": "unsubscribed"}
    except Exception:  # noqa: BLE001
        return JSONResponse({"status": "invalid_token"}, status_code=400)
    finally:
        db.close()
