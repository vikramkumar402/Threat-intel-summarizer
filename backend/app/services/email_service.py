"""Email service for sending daily digests via AWS SES."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import structlog
from itsdangerous import URLSafeSerializer
from jinja2 import Template

from app.config import get_settings

logger = structlog.get_logger()

UNSUBSCRIBE_SALT = "digest-unsubscribe"


class EmailService:
    """Service for sending email digests via AWS SES."""

    def __init__(self) -> None:
        self.settings = get_settings()
        requested_provider = self.settings.email_provider_normalized
        self.provider = requested_provider
        if requested_provider == "ses" and not self.settings.aws_configured:
            logger.warning(
                "email_provider_fallback",
                requested=requested_provider,
                selected="log",
                reason="aws_not_configured",
            )
            self.provider = "log"
        self.from_email = self.settings.ses_from_email or "noreply@example.com"
        self.template = self._load_template()
        self._client = None
        self._serializer = URLSafeSerializer(self.settings.jwt_secret, salt=UNSUBSCRIBE_SALT)

    @property
    def client(self):
        if self._client is None and self.provider == "ses":
            import boto3

            self._client = boto3.client(
                "ses",
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region,
            )
        return self._client

    def _load_template(self) -> Template:
        path = Path(__file__).parent.parent / "templates" / "digest_email.html"
        return Template(path.read_text())

    def make_unsubscribe_url(self, user_id: int) -> str:
        token = self._serializer.dumps({"uid": user_id})
        return f"{self.settings.app_base_url.rstrip('/')}/unsubscribe?token={token}"

    def verify_unsubscribe_token(self, token: str) -> int:
        data = self._serializer.loads(token)
        return int(data["uid"])

    async def send_daily_digest(self, to_email: str, user_id: int, brief_data: dict) -> None:
        html_body = self.template.render(
            **brief_data,
            unsubscribe_url=self.make_unsubscribe_url(user_id),
        )
        subject = f"Daily Threat Intelligence Brief - {brief_data['date']}"

        if self.provider == "log":
            logger.info("email_log_provider", to=to_email, subject=subject, html_bytes=len(html_body))
            return

        try:
            self.client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": html_body}},
                },
            )
        except Exception as exc:  # noqa: BLE001 — SES surfaces many error types
            logger.error("email_send_failed", to=to_email, error=str(exc))

    async def send_bulk_digests(
        self, recipients: Iterable[Tuple[str, int]], brief_data: dict
    ) -> None:
        for email, uid in recipients:
            await self.send_daily_digest(email, uid, brief_data)
