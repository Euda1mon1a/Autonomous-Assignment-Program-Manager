"""Application configuration."""
import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ***REMOVED*** Application
    APP_NAME: str = "Residency Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    ***REMOVED*** Logging
    LOG_LEVEL: str = "INFO"  ***REMOVED*** DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "text"  ***REMOVED*** json for production, text for development
    LOG_FILE: str = ""  ***REMOVED*** Optional file path for log output

    ***REMOVED*** Database
    DATABASE_URL: str = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"

    ***REMOVED*** Database Connection Pool Settings
    ***REMOVED*** See docs/ARCHITECTURE.md for connection pooling strategy
    DB_POOL_SIZE: int = 10  ***REMOVED*** Number of connections to keep open
    DB_POOL_MAX_OVERFLOW: int = 20  ***REMOVED*** Additional connections beyond pool_size
    DB_POOL_TIMEOUT: int = 30  ***REMOVED*** Seconds to wait for available connection
    DB_POOL_RECYCLE: int = 1800  ***REMOVED*** Recycle connections after 30 minutes
    DB_POOL_PRE_PING: bool = True  ***REMOVED*** Verify connections before use

    ***REMOVED*** Redis / Celery Configuration
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    @property
    def redis_url_with_password(self) -> str:
        """
        Get Redis URL with password authentication if REDIS_PASSWORD is set.

        Returns:
            str: Redis URL with password embedded if password is configured,
                 otherwise returns the base REDIS_URL.
        """
        if self.REDIS_PASSWORD:
            ***REMOVED*** Insert password into URL (format: redis://:password@host:port/db)
            return self.REDIS_URL.replace("redis://", f"redis://:{self.REDIS_PASSWORD}@")
        return self.REDIS_URL

    ***REMOVED*** Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  ***REMOVED*** 24 hours
    WEBHOOK_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS: int = 300  ***REMOVED*** 5 minutes

    ***REMOVED*** Rate Limiting (per IP address)
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  ***REMOVED*** Maximum login attempts per minute
    RATE_LIMIT_LOGIN_WINDOW: int = 60  ***REMOVED*** Time window in seconds (1 minute)
    RATE_LIMIT_REGISTER_ATTEMPTS: int = 3  ***REMOVED*** Maximum registration attempts per minute
    RATE_LIMIT_REGISTER_WINDOW: int = 60  ***REMOVED*** Time window in seconds (1 minute)
    RATE_LIMIT_ENABLED: bool = True  ***REMOVED*** Enable/disable rate limiting globally

    ***REMOVED*** Cache TTL Settings (in seconds)
    CACHE_HEATMAP_TTL: int = 300  ***REMOVED*** 5 minutes for heatmap data
    CACHE_CALENDAR_TTL: int = 600  ***REMOVED*** 10 minutes for calendar exports
    CACHE_SCHEDULE_TTL: int = 300  ***REMOVED*** 5 minutes for schedule queries

    ***REMOVED*** CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    ***REMOVED*** Trusted Hosts (for TrustedHostMiddleware - prevents host header attacks)
    ***REMOVED*** Empty list disables the middleware; set in production to actual domain(s)
    TRUSTED_HOSTS: list[str] = []  ***REMOVED*** e.g., ["scheduler.hospital.org", "*.hospital.org"]

    ***REMOVED*** Resilience Configuration (Tier 1)
    ***REMOVED*** Utilization thresholds based on queuing theory (M/M/c queue model)
    ***REMOVED*** Wait time formula: W ~ rho / (1 - rho), where rho = utilization
    ***REMOVED*** At 50% utilization: wait = 1x baseline
    ***REMOVED*** At 80% utilization: wait = 4x baseline
    ***REMOVED*** At 90% utilization: wait = 9x baseline
    ***REMOVED*** Reference: docs/RESILIENCE_FRAMEWORK.md
    RESILIENCE_WARNING_THRESHOLD: float = 0.70  ***REMOVED*** Yellow - start monitoring closely
    RESILIENCE_MAX_UTILIZATION: float = 0.80  ***REMOVED*** Orange - 80% utilization cliff (load shedding begins)
    RESILIENCE_CRITICAL_THRESHOLD: float = 0.90  ***REMOVED*** Red - crisis mode, aggressive intervention
    RESILIENCE_EMERGENCY_THRESHOLD: float = 0.95  ***REMOVED*** Black - cascade failure imminent

    ***REMOVED*** Auto-activation settings
    RESILIENCE_AUTO_ACTIVATE_DEFENSE: bool = True  ***REMOVED*** Auto-activate defense levels
    RESILIENCE_AUTO_ACTIVATE_FALLBACK: bool = False  ***REMOVED*** Require manual fallback activation (safety)
    RESILIENCE_AUTO_SHED_LOAD: bool = True  ***REMOVED*** Auto load shedding when thresholds exceeded

    ***REMOVED*** Monitoring intervals
    RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES: int = 15  ***REMOVED*** How often to run health checks
    RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS: int = 24  ***REMOVED*** N-1/N-2 analysis frequency

    ***REMOVED*** Alert settings
    RESILIENCE_ALERT_RECIPIENTS: list[str] = []  ***REMOVED*** Email addresses for alerts
    RESILIENCE_SLACK_CHANNEL: str = ""  ***REMOVED*** Slack channel for alerts (optional)

    @field_validator('SECRET_KEY', 'WEBHOOK_SECRET')
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """Validate that secrets are not using insecure default values."""
        field_name = info.field_name
        insecure_defaults = [
            "",
            "your-secret-key-change-in-production",
            "your-webhook-secret-change-in-production",
        ]

        if v in insecure_defaults:
            raise ValueError(
                f"{field_name} must be set to a secure value. "
                f"Set the {field_name} environment variable to a strong random value."
            )

        ***REMOVED*** Check minimum length (at least 32 characters for production secrets)
        if len(v) < 32:
            raise ValueError(
                f"{field_name} must be at least 32 characters long for security. "
                f"Current length: {len(v)}"
            )

        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_resilience_config():
    """Get ResilienceConfig from settings."""
    from app.resilience.defense_in_depth import DefenseLevel
    from app.resilience.service import ResilienceConfig

    settings = get_settings()
    return ResilienceConfig(
        max_utilization=settings.RESILIENCE_MAX_UTILIZATION,
        warning_threshold=settings.RESILIENCE_WARNING_THRESHOLD,
        auto_activate_defense=settings.RESILIENCE_AUTO_ACTIVATE_DEFENSE,
        auto_activate_fallback=settings.RESILIENCE_AUTO_ACTIVATE_FALLBACK,
        auto_shed_load=settings.RESILIENCE_AUTO_SHED_LOAD,
        health_check_interval_minutes=settings.RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES,
        contingency_analysis_interval_hours=settings.RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS,
        alert_recipients=settings.RESILIENCE_ALERT_RECIPIENTS,
        escalation_threshold=DefenseLevel.CONTAINMENT,
    )
