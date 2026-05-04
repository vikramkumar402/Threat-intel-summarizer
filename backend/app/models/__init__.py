"""SQLAlchemy database models."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Role:
    """User role string constants (kept as strings for portable enums)."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"

    ALL = (VIEWER, ANALYST, ADMIN)


class JobStatus:
    """Scrape-job status string constants."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IntelItem(Base):
    """Raw intelligence item from scrapers."""

    __tablename__ = "intel_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    raw_text = Column(Text)
    published_at = Column(DateTime, index=True)
    severity = Column(String(20), index=True)
    is_processed = Column(Boolean, default=False, index=True)
    iocs = Column(JSON, default=list)
    mitre_techniques = Column(JSON, default=list)
    simhash = Column(String(32), index=True, nullable=True)
    duplicate_of_id = Column(Integer, ForeignKey("intel_items.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())


class IOC(Base):
    """Extracted indicator-of-compromise (searchable across items)."""

    __tablename__ = "iocs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)
    value = Column(String(500), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("intel_items.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("type", "value", "item_id", name="uq_ioc_type_value_item"),)


class DailyBrief(Base):
    """Daily threat intelligence brief."""

    __tablename__ = "daily_briefs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, nullable=False, index=True)
    summary_md = Column(Text)
    top_cves = Column(JSON)
    threat_themes = Column(JSON)
    high_priority_flags = Column(JSON, default=list)
    recommendations_md = Column(Text)
    prompt_version = Column(String(20), default="v1")
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class User(Base):
    """User account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default=Role.VIEWER, nullable=False, index=True)
    receive_digest = Column(Boolean, default=True)
    severity_threshold = Column(String(20), default="LOW")
    subscribed_sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=func.now())

    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    subscription = relationship("Subscription", back_populates="user", uselist=False)


class Subscription(Base):
    """User digest subscription settings."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    digest_time = Column(Time)
    timezone = Column(String(50), default="UTC")

    user = relationship("User", back_populates="subscription")


class RefreshToken(Base):
    """Persisted refresh token for rotation + revocation."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class ScrapeJob(Base):
    """Tracking record for a manual or scheduled scrape pipeline run."""

    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default=JobStatus.PENDING, nullable=False, index=True)
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    items_collected = Column(Integer, default=0)
    items_stored = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    progress = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())


class SourceHealth(Base):
    """Rolling health metrics per scraper source."""

    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), unique=True, nullable=False, index=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    success_count_7d = Column(Integer, default=0)
    failure_count_7d = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


__all__ = [
    "Base",
    "Role",
    "JobStatus",
    "IntelItem",
    "IOC",
    "DailyBrief",
    "User",
    "Subscription",
    "RefreshToken",
    "ScrapeJob",
    "SourceHealth",
]
