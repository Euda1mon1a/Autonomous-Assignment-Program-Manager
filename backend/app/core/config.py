"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


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
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_resilience_config():
    """Get ResilienceConfig from settings."""
    from app.resilience.service import ResilienceConfig
    from app.resilience.defense_in_depth import DefenseLevel

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
