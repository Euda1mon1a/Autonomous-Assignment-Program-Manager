"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ***REMOVED*** Application
    APP_NAME: str = "Residency Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    ***REMOVED*** Database
    DATABASE_URL: str = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"

    ***REMOVED*** Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  ***REMOVED*** 24 hours

    ***REMOVED*** CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    ***REMOVED*** Resilience Configuration (Tier 1)
    ***REMOVED*** Utilization thresholds (queuing theory)
    RESILIENCE_MAX_UTILIZATION: float = 0.80  ***REMOVED*** 80% utilization cliff
    RESILIENCE_WARNING_THRESHOLD: float = 0.70  ***REMOVED*** Yellow warning level

    ***REMOVED*** Auto-activation settings
    RESILIENCE_AUTO_ACTIVATE_DEFENSE: bool = True  ***REMOVED*** Auto-activate defense levels
    RESILIENCE_AUTO_ACTIVATE_FALLBACK: bool = False  ***REMOVED*** Require manual fallback activation
    RESILIENCE_AUTO_SHED_LOAD: bool = True  ***REMOVED*** Auto load shedding

    ***REMOVED*** Monitoring intervals
    RESILIENCE_HEALTH_CHECK_INTERVAL_MINUTES: int = 15
    RESILIENCE_CONTINGENCY_ANALYSIS_INTERVAL_HOURS: int = 24

    ***REMOVED*** Alert settings
    RESILIENCE_ALERT_RECIPIENTS: list[str] = []  ***REMOVED*** Email addresses for alerts

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
