"""Pydantic schemas for request/response validation."""
from datetime import datetime, time
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_active: bool
    role: str
    receive_digest: bool
    severity_threshold: Optional[str] = "LOW"
    subscribed_sources: Optional[List[str]] = None


class IntelItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    source: str
    raw_text: Optional[str] = None
    published_at: Optional[datetime] = None
    severity: Optional[str] = None
    is_processed: bool
    iocs: Optional[List[Any]] = None
    mitre_techniques: Optional[List[str]] = None
    created_at: datetime


class CVEEntry(BaseModel):
    cve_id: str
    cvss_score: Optional[float] = None
    severity: Optional[str] = None
    affected_products: Optional[str] = ""
    impact_summary: Optional[str] = ""
    exploitation_status: Optional[str] = None


class DailyBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    summary_md: Optional[str] = None
    top_cves: Optional[Any] = None
    threat_themes: Optional[Any] = None
    high_priority_flags: Optional[Any] = None
    recommendations_md: Optional[str] = None
    prompt_version: Optional[str] = None
    item_count: Optional[int] = None
    created_at: datetime


class DigestSettings(BaseModel):
    receive_digest: bool
    digest_time: Optional[time] = None
    timezone: Optional[str] = "UTC"
    severity_threshold: Optional[str] = None
    subscribed_sources: Optional[List[str]] = None


class IntelItem(BaseModel):
    """Normalized intelligence item produced by scrapers."""

    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    raw_text: str
    severity: Optional[str] = "UNKNOWN"


class ScrapeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    items_collected: int
    items_stored: int
    error_message: Optional[str] = None
    progress: Optional[Any] = None
    created_at: datetime


class SourceHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int
    success_count_7d: int
    failure_count_7d: int
    enabled: bool


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict
