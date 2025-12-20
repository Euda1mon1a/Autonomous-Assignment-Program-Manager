"""Application configuration."""
import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Residency Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
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

    # File Upload Settings
    UPLOAD_STORAGE_BACKEND: str = "local"  # Storage backend: 'local' or 's3'
    UPLOAD_LOCAL_DIR: str = "/tmp/uploads"  # Local storage directory
    UPLOAD_MAX_SIZE_MB: int = 50  # Maximum file size in megabytes
    UPLOAD_ENABLE_VIRUS_SCAN: bool = False  # Enable virus scanning

    # S3 Upload Settings (used when UPLOAD_STORAGE_BACKEND='s3')
    UPLOAD_S3_BUCKET: str = "residency-scheduler-uploads"
    UPLOAD_S3_REGION: str = "us-east-1"
    UPLOAD_S3_ACCESS_KEY: str = ""
    UPLOAD_S3_SECRET_KEY: str = ""
    UPLOAD_S3_ENDPOINT_URL: str = ""  # For S3-compatible services (MinIO, etc.)

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Trusted Hosts (for TrustedHostMiddleware - prevents host header attacks)
    # Empty list disables the middleware; set in production to actual domain(s)
    TRUSTED_HOSTS: list[str] = []  # e.g., ["scheduler.hospital.org", "*.hospital.org"]

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

    # OpenTelemetry / Distributed Tracing Configuration
    TELEMETRY_ENABLED: bool = False  # Enable distributed tracing
    TELEMETRY_SERVICE_NAME: str = "residency-scheduler"
    TELEMETRY_ENVIRONMENT: str = "development"  # development, staging, production
    TELEMETRY_SAMPLING_RATE: float = 1.0  # Trace sampling rate (0.0 to 1.0)
    TELEMETRY_CONSOLE_EXPORT: bool = False  # Enable console exporter for debugging

    # Exporter Configuration
    TELEMETRY_EXPORTER_TYPE: str = "otlp_grpc"  # jaeger, zipkin, otlp_http, otlp_grpc
    TELEMETRY_EXPORTER_ENDPOINT: str = "http://localhost:4317"  # Exporter endpoint URL
    TELEMETRY_EXPORTER_INSECURE: bool = True  # Use insecure connection (no TLS)
    TELEMETRY_EXPORTER_HEADERS: dict[str, str] = {}  # Custom headers for authentication

    # Instrumentation Configuration
    TELEMETRY_TRACE_SQLALCHEMY: bool = True  # Enable SQLAlchemy tracing
    TELEMETRY_TRACE_REDIS: bool = True  # Enable Redis tracing
    TELEMETRY_TRACE_HTTP: bool = True  # Enable HTTP client tracing

    # Shadow Traffic Configuration
    SHADOW_TRAFFIC_ENABLED: bool = False  # Enable shadow traffic duplication
    SHADOW_TRAFFIC_URL: str = ""  # Shadow service base URL
    SHADOW_SAMPLING_RATE: float = 0.1  # Percentage of requests to shadow (0.0-1.0)
    SHADOW_TIMEOUT: float = 10.0  # Shadow request timeout in seconds
    SHADOW_MAX_CONCURRENT: int = 10  # Maximum concurrent shadow requests
    SHADOW_VERIFY_SSL: bool = True  # Verify SSL certificates for shadow service
    SHADOW_ALERT_ON_DIFF: bool = True  # Alert on response differences
    SHADOW_DIFF_THRESHOLD: str = "medium"  # Threshold for alerting: low, medium, high, critical
    SHADOW_RETRY_ON_FAILURE: bool = False  # Retry failed shadow requests
    SHADOW_MAX_RETRIES: int = 2  # Maximum retry attempts
    SHADOW_INCLUDE_HEADERS: bool = True  # Include original headers in shadow requests
    SHADOW_HEALTH_CHECK_INTERVAL: int = 60  # Health check interval in seconds
    SHADOW_METRICS_RETENTION_HOURS: int = 24  # Metrics retention period

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

        # Check minimum length (at least 32 characters for production secrets)
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

    # Map string threshold to enum
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
