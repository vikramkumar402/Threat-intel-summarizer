"""Application configuration management."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Core
    database_url: str = "sqlite:///./threatintel.db"
    environment: str = "development"
    disable_auth: bool = False
    llm_provider: str = "local"
    email_provider: str = "log"

    # AWS (required only when using bedrock/ses providers)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0"
    ses_from_email: Optional[str] = None

    # Groq (required only when using llm_provider=groq)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"

    # Auth
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # Backwards-compat with the old single-token expiry env var
    jwt_expire_minutes: Optional[int] = None

    # Admin seed (used on first boot if no admin exists)
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None

    # Scheduler
    daily_pipeline_hour_utc: int = 6
    daily_pipeline_minute_utc: int = 0

    # Public app URL (used for unsubscribe links etc.)
    app_base_url: str = "http://localhost:3000"

    @property
    def access_token_minutes(self) -> int:
        """Resolve access-token TTL with legacy env-var fallback."""
        if self.jwt_expire_minutes is not None:
            return self.jwt_expire_minutes
        return self.jwt_access_expire_minutes

    @property
    def aws_configured(self) -> bool:
        """True only when real AWS creds are present."""
        return bool(
            self.aws_access_key_id
            and self.aws_secret_access_key
            and self.aws_access_key_id != "DEMO_KEY"
        )

    @property
    def llm_provider_normalized(self) -> str:
        provider = (self.llm_provider or "local").strip().lower()
        return provider if provider in {"local", "bedrock", "groq"} else "local"

    @property
    def email_provider_normalized(self) -> str:
        provider = (self.email_provider or "log").strip().lower()
        return provider if provider in {"log", "ses"} else "log"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
