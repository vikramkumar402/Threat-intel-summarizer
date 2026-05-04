"""Scheduler service for automated daily intelligence gathering."""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Callable, List, Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    DailyBrief,
    IOC,
    IntelItem,
    JobStatus,
    Role,
    ScrapeJob,
    SourceHealth,
    User,
)
from app.schemas import IntelItem as IntelItemSchema
from app.scrapers import (
    BleepingComputerScraper,
    CISAScraper,
    KrebsScraper,
    NVDScraper,
    SchneierScraper,
    THNScraper,
    USCERTScraper,
)
from app.services import iocs as ioc_service
from app.services import mitre, severity as severity_service
from app.services.email_service import EmailService
from app.services.llm_service import LLMService

logger = structlog.get_logger()


class SchedulerService:
    """Singleton scheduler that runs the daily intel pipeline."""

    _instance: Optional["SchedulerService"] = None

    def __init__(self, db_session_factory: Callable[[], Session]):
        self.scheduler = AsyncIOScheduler()
        self.db_session_factory = db_session_factory
        self.llm_service = LLMService()
        self.email_service = EmailService()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def start(self) -> None:
        settings = get_settings()
        self._loop = asyncio.get_event_loop()
        self.scheduler.add_job(
            self.daily_intelligence_pipeline,
            "cron",
            hour=settings.daily_pipeline_hour_utc,
            minute=settings.daily_pipeline_minute_utc,
            timezone="UTC",
            id="daily_pipeline",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info("scheduler_started")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def kickoff_pipeline(self, job_id: int) -> None:
        """Schedule a one-off pipeline run tracked by `job_id`."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
        coro = self.daily_intelligence_pipeline(job_id=job_id)
        try:
            asyncio.get_running_loop().create_task(coro)
        except RuntimeError:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def daily_intelligence_pipeline(self, job_id: Optional[int] = None) -> None:
        db = self.db_session_factory()
        job: Optional[ScrapeJob] = None
        if job_id is not None:
            job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
        elif True:
            job = ScrapeJob(status=JobStatus.PENDING, progress={})
            db.add(job)
            db.commit()
            db.refresh(job)

        assert job is not None
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.progress = {"stage": "scraping"}
            db.commit()

            collected = await self._run_scrapers(db)
            job.items_collected = len(collected)
            job.progress = {"stage": "deduplicating", "collected": len(collected)}
            db.commit()

            unique = self._deduplicate(collected)
            job.progress = {"stage": "storing", "unique": len(unique)}
            db.commit()

            stored = self._store_items(db, unique)
            job.items_stored = len(stored)
            job.progress = {"stage": "summarizing", "stored": len(stored)}
            db.commit()

            recent = self._get_recent_items(db)
            brief_data = await self.llm_service.generate_daily_brief(recent)
            job.progress = {"stage": "emailing"}
            db.commit()

            await self._store_brief(db, brief_data, len(recent))
            await self._send_digests(db, brief_data)

            job.status = JobStatus.SUCCEEDED
            job.finished_at = datetime.utcnow()
            job.progress = {"stage": "done"}
            db.commit()
            logger.info("pipeline_succeeded", job_id=job.id, items_stored=job.items_stored)
        except Exception as exc:  # noqa: BLE001
            logger.error("pipeline_failed", job_id=job.id, error=str(exc), exc_info=True)
            job.status = JobStatus.FAILED
            job.finished_at = datetime.utcnow()
            job.error_message = str(exc)
            db.commit()
        finally:
            db.close()

    def _scrapers(self):
        return [
            NVDScraper(),
            CISAScraper(),
            KrebsScraper(),
            THNScraper(),
            BleepingComputerScraper(),
            SchneierScraper(),
            USCERTScraper(),
        ]

    async def _run_scrapers(self, db: Session) -> List[IntelItemSchema]:
        scrapers = self._scrapers()
        # Skip scrapers that admin has disabled.
        enabled_names = {
            r.source for r in db.query(SourceHealth).filter(SourceHealth.enabled.is_(False)).all()
        }
        active = [s for s in scrapers if s.source_name not in enabled_names]
        results = await asyncio.gather(
            *[s.scrape() for s in active], return_exceptions=True
        )

        all_items: List[IntelItemSchema] = []
        for scraper, result in zip(active, results):
            health = self._get_or_create_health(db, scraper.source_name)
            if isinstance(result, Exception):
                health.last_error_at = datetime.utcnow()
                health.last_error = str(result)
                health.consecutive_failures = (health.consecutive_failures or 0) + 1
                health.failure_count_7d = (health.failure_count_7d or 0) + 1
                if health.consecutive_failures >= 5:
                    health.enabled = False
                logger.warning(
                    "scraper_failed", source=scraper.source_name, error=str(result)
                )
            else:
                health.last_success_at = datetime.utcnow()
                health.consecutive_failures = 0
                health.success_count_7d = (health.success_count_7d or 0) + 1
                all_items.extend(result)
            db.commit()

        for s in scrapers:
            try:
                await s.close()
            except Exception:  # noqa: BLE001
                pass

        return all_items

    @staticmethod
    def _get_or_create_health(db: Session, source: str) -> SourceHealth:
        row = db.query(SourceHealth).filter(SourceHealth.source == source).first()
        if not row:
            row = SourceHealth(source=source, enabled=True)
            db.add(row)
            db.commit()
            db.refresh(row)
        return row

    @staticmethod
    def _deduplicate(items: List[IntelItemSchema]) -> List[IntelItemSchema]:
        seen: set[str] = set()
        unique: List[IntelItemSchema] = []
        for item in items:
            url_hash = hashlib.md5(item.url.encode()).hexdigest()
            if url_hash not in seen:
                seen.add(url_hash)
                unique.append(item)
        return unique

    @staticmethod
    def _store_items(db: Session, items: List[IntelItemSchema]) -> List[IntelItem]:
        stored: List[IntelItem] = []
        for item in items:
            existing = db.query(IntelItem).filter(IntelItem.url == item.url).first()
            if existing:
                continue
            normalized_severity = severity_service.from_source_signal(
                item.source, item.severity
            )
            text_for_extraction = f"{item.title}\n{item.raw_text or ''}"
            extracted = ioc_service.extract(text_for_extraction)
            techniques = mitre.tag(text_for_extraction)

            db_item = IntelItem(
                title=item.title,
                url=item.url,
                source=item.source,
                raw_text=item.raw_text,
                published_at=item.published_at,
                severity=normalized_severity,
                is_processed=False,
                iocs=extracted,
                mitre_techniques=techniques,
            )
            db.add(db_item)
            db.flush()  # get ID for IOC FK

            for ioc in extracted:
                db.add(IOC(type=ioc["type"], value=ioc["value"], item_id=db_item.id))
            stored.append(db_item)

        db.commit()
        return stored

    @staticmethod
    def _get_recent_items(db: Session) -> List[dict]:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        items = (
            db.query(IntelItem)
            .filter(IntelItem.created_at >= cutoff)
            .order_by(IntelItem.created_at.desc())
            .limit(80)
            .all()
        )
        return [
            {
                "title": i.title,
                "url": i.url,
                "source": i.source,
                "raw_text": i.raw_text,
                "published_at": str(i.published_at) if i.published_at else "",
                "severity": i.severity,
            }
            for i in items
        ]

    @staticmethod
    async def _store_brief(db: Session, brief_data: dict, item_count: int) -> None:
        telemetry = brief_data.get("_telemetry", {})
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing = db.query(DailyBrief).filter(DailyBrief.date == today).first()
        if existing:
            existing.summary_md = brief_data.get("executive_summary", "")
            existing.top_cves = brief_data.get("top_cves", [])
            existing.threat_themes = brief_data.get("threat_themes", [])
            existing.high_priority_flags = brief_data.get("high_priority_flags", [])
            existing.recommendations_md = "\n".join(brief_data.get("recommendations", []))
            existing.prompt_version = telemetry.get("prompt_version", "v1")
            existing.input_tokens = telemetry.get("input_tokens", 0)
            existing.output_tokens = telemetry.get("output_tokens", 0)
            existing.cost_usd = telemetry.get("cost_usd", 0.0)
            existing.item_count = item_count
        else:
            brief = DailyBrief(
                date=today,
                summary_md=brief_data.get("executive_summary", ""),
                top_cves=brief_data.get("top_cves", []),
                threat_themes=brief_data.get("threat_themes", []),
                high_priority_flags=brief_data.get("high_priority_flags", []),
                recommendations_md="\n".join(brief_data.get("recommendations", [])),
                prompt_version=telemetry.get("prompt_version", "v1"),
                input_tokens=telemetry.get("input_tokens", 0),
                output_tokens=telemetry.get("output_tokens", 0),
                cost_usd=telemetry.get("cost_usd", 0.0),
                item_count=item_count,
            )
            db.add(brief)
        db.commit()

    async def _send_digests(self, db: Session, brief_data: dict) -> None:
        users = (
            db.query(User)
            .filter(User.is_active.is_(True), User.receive_digest.is_(True))
            .all()
        )
        recipients = [(u.email, u.id) for u in users]
        if not recipients:
            return

        email_data = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "executive_summary": brief_data.get("executive_summary", ""),
            "top_cves": brief_data.get("top_cves", []),
            "threat_themes": brief_data.get("threat_themes", []),
            "recommendations": brief_data.get("recommendations", []),
            "high_priority_flags": brief_data.get("high_priority_flags", []),
        }
        await self.email_service.send_bulk_digests(recipients, email_data)


def get_scheduler_service(session_factory) -> SchedulerService:
    if SchedulerService._instance is None:
        SchedulerService._instance = SchedulerService(session_factory)
    return SchedulerService._instance


def seed_admin_user(db: Session) -> None:
    """Create an admin user from env vars on first boot if none exists."""
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return
    existing_admin = db.query(User).filter(User.role == Role.ADMIN).first()
    if existing_admin:
        return
    from app.routers.auth import hash_password

    user = (
        db.query(User).filter(User.email == settings.admin_email).first()
    ) or User(email=settings.admin_email, hashed_password="placeholder")
    user.hashed_password = hash_password(settings.admin_password)
    user.role = Role.ADMIN
    user.is_active = True
    user.receive_digest = True
    if user.id is None:
        db.add(user)
    db.commit()
    logger.info("admin_user_seeded", email=settings.admin_email)
