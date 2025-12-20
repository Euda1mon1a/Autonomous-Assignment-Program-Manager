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

    ***REMOVED*** File Upload Settings
    UPLOAD_STORAGE_BACKEND: str = "local"  ***REMOVED*** Storage backend: 'local' or 's3'
    UPLOAD_LOCAL_DIR: str = "/tmp/uploads"  ***REMOVED*** Local storage directory
    UPLOAD_MAX_SIZE_MB: int = 50  ***REMOVED*** Maximum file size in megabytes
    UPLOAD_ENABLE_VIRUS_SCAN: bool = False  ***REMOVED*** Enable virus scanning

    ***REMOVED*** S3 Upload Settings (used when UPLOAD_STORAGE_BACKEND='s3')
    UPLOAD_S3_BUCKET: str = "residency-scheduler-uploads"
    UPLOAD_S3_REGION: str = "us-east-1"
    UPLOAD_S3_ACCESS_KEY: str = ""
    UPLOAD_S3_SECRET_KEY: str = ""
    UPLOAD_S3_ENDPOINT_URL: str = ""  ***REMOVED*** For S3-compatible services (MinIO, etc.)

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

    ***REMOVED*** OpenTelemetry / Distributed Tracing Configuration
    TELEMETRY_ENABLED: bool = False  ***REMOVED*** Enable distributed tracing
    TELEMETRY_SERVICE_NAME: str = "residency-scheduler"
    TELEMETRY_ENVIRONMENT: str = "development"  ***REMOVED*** development, staging, production
    TELEMETRY_SAMPLING_RATE: float = 1.0  ***REMOVED*** Trace sampling rate (0.0 to 1.0)
    TELEMETRY_CONSOLE_EXPORT: bool = False  ***REMOVED*** Enable console exporter for debugging

    ***REMOVED*** Exporter Configuration
    TELEMETRY_EXPORTER_TYPE: str = "otlp_grpc"  ***REMOVED*** jaeger, zipkin, otlp_http, otlp_grpc
    TELEMETRY_EXPORTER_ENDPOINT: str = "http://localhost:4317"  ***REMOVED*** Exporter endpoint URL
    TELEMETRY_EXPORTER_INSECURE: bool = True  ***REMOVED*** Use insecure connection (no TLS)
    TELEMETRY_EXPORTER_HEADERS: dict[str, str] = {}  ***REMOVED*** Custom headers for authentication

    ***REMOVED*** Instrumentation Configuration
    TELEMETRY_TRACE_SQLALCHEMY: bool = True  ***REMOVED*** Enable SQLAlchemy tracing
    TELEMETRY_TRACE_REDIS: bool = True  ***REMOVED*** Enable Redis tracing
    TELEMETRY_TRACE_HTTP: bool = True  ***REMOVED*** Enable HTTP client tracing

    ***REMOVED*** Shadow Traffic Configuration
    SHADOW_TRAFFIC_ENABLED: bool = False  ***REMOVED*** Enable shadow traffic duplication
    SHADOW_TRAFFIC_URL: str = ""  ***REMOVED*** Shadow service base URL
    SHADOW_SAMPLING_RATE: float = 0.1  ***REMOVED*** Percentage of requests to shadow (0.0-1.0)
    SHADOW_TIMEOUT: float = 10.0  ***REMOVED*** Shadow request timeout in seconds
    SHADOW_MAX_CONCURRENT: int = 10  ***REMOVED*** Maximum concurrent shadow requests
    SHADOW_VERIFY_SSL: bool = True  ***REMOVED*** Verify SSL certificates for shadow service
    SHADOW_ALERT_ON_DIFF: bool = True  ***REMOVED*** Alert on response differences
    SHADOW_DIFF_THRESHOLD: str = "medium"  ***REMOVED*** Threshold for alerting: low, medium, high, critical
    SHADOW_RETRY_ON_FAILURE: bool = False  ***REMOVED*** Retry failed shadow requests
    SHADOW_MAX_RETRIES: int = 2  ***REMOVED*** Maximum retry attempts
    SHADOW_INCLUDE_HEADERS: bool = True  ***REMOVED*** Include original headers in shadow requests
    SHADOW_HEALTH_CHECK_INTERVAL: int = 60  ***REMOVED*** Health check interval in seconds
    SHADOW_METRICS_RETENTION_HOURS: int = 24  ***REMOVED*** Metrics retention period

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


def get_shadow_config():
    """Get ShadowConfig from settings."""
    from app.shadow.traffic import DiffSeverity, ShadowConfig

    settings = get_settings()

    ***REMOVED*** Map string threshold to enum
    threshold_map = {
        "none": DiffSeverity.NONE,
        "low": DiffSeverity.LOW,
        "medium": DiffSeverity.MEDIUM,
        "high": DiffSeverity.HIGH,
        "critical": DiffSeverity.CRITICAL,
    }
    diff_threshold = threshold_map.get(
        settings.SHADOW_DIFF_THRESHOLD.lower(), DiffSeverity.MEDIUM
    )

    return ShadowConfig(
        enabled=settings.SHADOW_TRAFFIC_ENABLED,
        shadow_url=settings.SHADOW_TRAFFIC_URL,
        sampling_rate=settings.SHADOW_SAMPLING_RATE,
        timeout=settings.SHADOW_TIMEOUT,
        max_concurrent=settings.SHADOW_MAX_CONCURRENT,
        verify_ssl=settings.SHADOW_VERIFY_SSL,
        alert_on_diff=settings.SHADOW_ALERT_ON_DIFF,
        diff_threshold=diff_threshold,
        retry_on_failure=settings.SHADOW_RETRY_ON_FAILURE,
        max_retries=settings.SHADOW_MAX_RETRIES,
        include_headers=settings.SHADOW_INCLUDE_HEADERS,
        health_check_interval=settings.SHADOW_HEALTH_CHECK_INTERVAL,
        metrics_retention_hours=settings.SHADOW_METRICS_RETENTION_HOURS,
    )
