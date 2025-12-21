"""Application configuration."""
import logging
import secrets
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Known weak/default passwords that should never be used in production
WEAK_PASSWORDS = {
    "",
    "password",
    "admin",
    "123456",
    "12345678",
    "123456789",
    "test",
    "guest",
    "root",
    "toor",
    "letmein",
    "welcome",
    "monkey",
    "dragon",
    "master",
    "sunshine",
    "qwerty",
    "abc123",
    "default",
    "changeme",
    # Common defaults from .env.example files
    "scheduler",
    "your_redis_password_here",
    "your_secure_database_password_here",
    "your-secret-key-change-in-production",
    "your-webhook-secret-change-in-production",
    "your_secret_key_here_generate_a_random_64_char_string",
    "your_redis_password_here_generate_a_random_string",
    "dev_only_password",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Residency Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "text"  # json for production, text for development
    LOG_FILE: str = ""  # Optional file path for log output

    # Database
    DATABASE_URL: str = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"

    # Database Connection Pool Settings
    # See docs/ARCHITECTURE.md for connection pooling strategy
    DB_POOL_SIZE: int = 10  # Number of connections to keep open
    DB_POOL_MAX_OVERFLOW: int = 20  # Additional connections beyond pool_size
    DB_POOL_TIMEOUT: int = 30  # Seconds to wait for available connection
    DB_POOL_RECYCLE: int = 1800  # Recycle connections after 30 minutes
    DB_POOL_PRE_PING: bool = True  # Verify connections before use

    # Redis / Celery Configuration
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
            # Insert password into URL (format: redis://:password@host:port/db)
            return self.REDIS_URL.replace("redis://", f"redis://:{self.REDIS_PASSWORD}@")
        return self.REDIS_URL

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes (security: reduced from 24 hours)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    REFRESH_TOKEN_ROTATE: bool = True  # Issue new refresh token on each use
    WEBHOOK_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS: int = 300  # 5 minutes

    # Rate Limiting (per IP address)
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # Maximum login attempts per minute
    RATE_LIMIT_LOGIN_WINDOW: int = 60  # Time window in seconds (1 minute)
    RATE_LIMIT_REGISTER_ATTEMPTS: int = 3  # Maximum registration attempts per minute
    RATE_LIMIT_REGISTER_WINDOW: int = 60  # Time window in seconds (1 minute)
    RATE_LIMIT_ENABLED: bool = True  # Enable/disable rate limiting globally

    # Cache TTL Settings (in seconds)
    CACHE_HEATMAP_TTL: int = 300  # 5 minutes for heatmap data
    CACHE_CALENDAR_TTL: int = 600  # 10 minutes for calendar exports
    CACHE_SCHEDULE_TTL: int = 300  # 5 minutes for schedule queries

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_ORIGINS_REGEX: str = ""  # Optional regex pattern for flexible origin matching

    # Trusted Hosts (for TrustedHostMiddleware - prevents host header attacks)
    # Empty list disables the middleware; set in production to actual domain(s)
    TRUSTED_HOSTS: list[str] = []  # e.g., ["scheduler.hospital.org", "*.hospital.org"]

    # Trusted Proxies (for X-Forwarded-For header validation - prevents rate limit bypass)
    # Only trust X-Forwarded-For from these IPs; empty list uses direct client IP
    TRUSTED_PROXIES: list[str] = []  # e.g., ["10.0.0.1", "10.0.0.2", "172.16.0.0/12"]

    # Resilience Configuration (Tier 1)
    # Utilization thresholds based on queuing theory (M/M/c queue model)
    # Wait time formula: W ~ rho / (1 - rho), where rho = utilization
    # At 50% utilization: wait = 1x baseline
    # At 80% utilization: wait = 4x baseline
    # At 90% utilization: wait = 9x baseline
    # Reference: docs/RESILIENCE_FRAMEWORK.md
    RESILIENCE_WARNING_THRESHOLD: float = 0.70  # Yellow - start monitoring closely
    RESILIENCE_MAX_UTILIZATION: float = 0.80  # Orange - 80% utilization cliff (load shedding begins)
    RESILIENCE_CRITICAL_THRESHOLD: float = 0.90  # Red - crisis mode, aggressive intervention
    RESILIENCE_EMERGENCY_THRESHOLD: float = 0.95  # Black - cascade failure imminent

    # Auto-activation settings
    RESILIENCE_AUTO_ACTIVATE_DEFENSE: bool = True  # Auto-activate defense levels
    RESILIENCE_AUTO_ACTIVATE_FALLBACK: bool = False  # Require manual fallback activation (safety)
    RESILIENCE_AUTO_SHED_LOAD: bool = True  # Auto load shedding when thresholds exceeded

    # Monitoring intervals
    RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES: int = 15  # How often to run health checks
    RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS: int = 24  # N-1/N-2 analysis frequency

    # Alert settings
    RESILIENCE_ALERT_RECIPIENTS: list[str] = []  # Email addresses for alerts
    RESILIENCE_SLACK_CHANNEL: str = ""  # Slack channel for alerts (optional)

    @field_validator('SECRET_KEY', 'WEBHOOK_SECRET')
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """
        Validate that secrets are not using insecure default values.

        In production (DEBUG=False): Raises errors for weak/default secrets.
        In development (DEBUG=True): Logs warnings but allows weak secrets.
        """
        field_name = info.field_name
        debug_mode = info.data.get('DEBUG', False)

        # Check against known weak passwords
        if v.lower() in WEAK_PASSWORDS or v in WEAK_PASSWORDS:
            error_msg = (
                f"{field_name} is using a known weak/default value. "
                f"Set the {field_name} environment variable to a strong random value. "
                f"Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
            if debug_mode:
                logger.warning(
                    f"[SECURITY WARNING] {error_msg} "
                    "(Acceptable in DEBUG mode but MUST be changed for production)"
                )
            else:
                raise ValueError(error_msg)

        # Check minimum length (at least 32 characters for production secrets)
        if len(v) < 32:
            error_msg = (
                f"{field_name} must be at least 32 characters long for security. "
                f"Current length: {len(v)}. "
                f"Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
            if debug_mode:
                logger.warning(
                    f"[SECURITY WARNING] {error_msg} "
                    "(Acceptable in DEBUG mode but MUST be changed for production)"
                )
            else:
                raise ValueError(error_msg)

        return v

    @field_validator('REDIS_PASSWORD')
    @classmethod
    def validate_redis_password(cls, v: str, info) -> str:
        """
        Validate Redis password security.

        In production (DEBUG=False): Requires strong password.
        In development (DEBUG=True): Allows empty/weak passwords with warning.
        """
        debug_mode = info.data.get('DEBUG', False)

        # Allow empty in development (Redis running without auth)
        if not v:
            if debug_mode:
                logger.info(
                    "[SECURITY INFO] REDIS_PASSWORD not set. "
                    "Redis will be accessed without authentication (acceptable in DEBUG mode only)."
                )
                return v
            else:
                raise ValueError(
                    "REDIS_PASSWORD must be set in production. "
                    "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )

        # Check against known weak passwords
        if v.lower() in WEAK_PASSWORDS or v in WEAK_PASSWORDS:
            error_msg = (
                f"REDIS_PASSWORD is using a known weak/default value. "
                f"Use a strong random value. "
                f"Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            if debug_mode:
                logger.warning(
                    f"[SECURITY WARNING] {error_msg} "
                    "(Acceptable in DEBUG mode but MUST be changed for production)"
                )
            else:
                raise ValueError(error_msg)

        # Check minimum length (at least 16 characters for Redis)
        if len(v) < 16:
            error_msg = (
                f"REDIS_PASSWORD must be at least 16 characters long for security. "
                f"Current length: {len(v)}. "
                f"Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
            if debug_mode:
                logger.warning(
                    f"[SECURITY WARNING] {error_msg} "
                    "(Acceptable in DEBUG mode but MUST be changed for production)"
                )
            else:
                raise ValueError(error_msg)

        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """
        Validate database URL to ensure password is not using weak/default values.

        In production (DEBUG=False): Rejects weak database passwords.
        In development (DEBUG=True): Allows weak passwords with warning.
        """
        debug_mode = info.data.get('DEBUG', False)

        try:
            parsed = urlparse(v)
            db_password = parsed.password

            # If no password in URL, that's a critical error
            if db_password is None:
                raise ValueError(
                    "DATABASE_URL must include a password. "
                    "Format: postgresql://user:password@host:port/dbname"
                )

            # Check against known weak passwords
            if db_password.lower() in WEAK_PASSWORDS or db_password in WEAK_PASSWORDS:
                error_msg = (
                    f"DATABASE_URL contains a known weak/default password: '{db_password}'. "
                    f"Use a strong random password for the database user."
                )
                if debug_mode:
                    logger.warning(
                        f"[SECURITY WARNING] {error_msg} "
                        "(Acceptable in DEBUG mode but MUST be changed for production)"
                    )
                else:
                    raise ValueError(error_msg)

            # Check password length (at least 12 characters for databases)
            if len(db_password) < 12:
                error_msg = (
                    f"DATABASE_URL password must be at least 12 characters long. "
                    f"Current length: {len(db_password)}."
                )
                if debug_mode:
                    logger.warning(
                        f"[SECURITY WARNING] {error_msg} "
                        "(Acceptable in DEBUG mode but MUST be changed for production)"
                    )
                else:
                    raise ValueError(error_msg)

        except Exception as e:
            # If we can't parse the URL, let it through but warn
            if "DATABASE_URL must include a password" in str(e) or "weak/default password" in str(e) or "must be at least" in str(e):
                raise  # Re-raise our validation errors
            logger.warning(f"Unable to parse DATABASE_URL for validation: {e}")

        return v

    @field_validator('CORS_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v: list[str], info) -> list[str]:
        """
        Validate CORS origins to prevent overly permissive configuration in production.

        Security requirements:
        - In production (DEBUG=False), wildcard "*" is forbidden
        - Warns about overly permissive configurations
        - Allows localhost origins for development flexibility
        """
        # Get DEBUG value from field values being validated
        # Note: field_validator runs during model initialization, so we can access other fields
        debug_mode = info.data.get('DEBUG', False)

        # Check for wildcard "*" - forbidden in production
        if "*" in v:
            if not debug_mode:
                raise ValueError(
                    "CORS_ORIGINS cannot contain wildcard '*' in production. "
                    "Specify explicit allowed origins (e.g., ['https://scheduler.hospital.org']) "
                    "or use CORS_ORIGINS_REGEX for pattern matching."
                )
            else:
                # Development mode: warn but allow
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "CORS wildcard '*' detected in DEBUG mode. "
                    "This is acceptable for development but MUST NOT be used in production."
                )

        # Warn about multiple overly broad origins in production
        if not debug_mode and len(v) > 10:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"CORS_ORIGINS contains {len(v)} origins. "
                "Consider using CORS_ORIGINS_REGEX for pattern matching if appropriate."
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
