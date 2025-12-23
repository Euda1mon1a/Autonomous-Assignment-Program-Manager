"""Database connection pool configuration.

This module provides configuration management for the database connection pool,
including dynamic sizing, timeout settings, and health check parameters.
"""

from pydantic import BaseModel, Field, field_validator


class PoolConfig(BaseModel):
    """Configuration for database connection pool.

    Attributes:
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum additional connections beyond pool_size
        timeout: Seconds to wait for an available connection
        recycle: Seconds before recycling a connection
        pre_ping: Whether to ping connections before use
        echo_pool: Whether to log pool events
        pool_reset_on_return: How to reset connections when returned
        query_timeout: Default query timeout in seconds
        connect_timeout: Connection establishment timeout in seconds
        enable_monitoring: Whether to collect pool metrics
        health_check_interval: Seconds between health checks
        reconnect_attempts: Number of reconnection attempts
        reconnect_delay: Delay between reconnection attempts in seconds
    """

    # Core pool settings
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    timeout: int = Field(default=30, ge=1, le=300)
    recycle: int = Field(default=1800, ge=300, le=7200)
    pre_ping: bool = Field(default=True)
    echo_pool: bool = Field(default=False)
    pool_reset_on_return: str = Field(default="rollback")

    # Timeout settings
    query_timeout: int | None = Field(default=60, ge=1, le=600)
    connect_timeout: int = Field(default=10, ge=1, le=60)

    # Monitoring settings
    enable_monitoring: bool = Field(default=True)
    health_check_interval: int = Field(default=60, ge=10, le=3600)

    # Reconnection settings
    reconnect_attempts: int = Field(default=3, ge=1, le=10)
    reconnect_delay: float = Field(default=1.0, ge=0.1, le=10.0)

    # Dynamic sizing
    enable_dynamic_sizing: bool = Field(default=True)
    min_pool_size: int = Field(default=5, ge=1, le=50)
    max_pool_size: int = Field(default=50, ge=10, le=200)
    scale_up_threshold: float = Field(default=0.8, ge=0.5, le=1.0)
    scale_down_threshold: float = Field(default=0.3, ge=0.1, le=0.5)

    @field_validator("max_overflow")
    @classmethod
    def validate_max_overflow(cls, v: int, info) -> int:
        """Ensure max_overflow makes sense relative to pool_size."""
        if "pool_size" in info.data:
            pool_size = info.data["pool_size"]
            if v > pool_size * 5:
                raise ValueError(
                    f"max_overflow ({v}) should not exceed 5x pool_size ({pool_size})"
                )
        return v

    @field_validator("scale_down_threshold")
    @classmethod
    def validate_scale_thresholds(cls, v: float, info) -> float:
        """Ensure scale_down is less than scale_up threshold."""
        if "scale_up_threshold" in info.data:
            scale_up = info.data["scale_up_threshold"]
            if v >= scale_up:
                raise ValueError(
                    f"scale_down_threshold ({v}) must be less than "
                    f"scale_up_threshold ({scale_up})"
                )
        return v

    @field_validator("max_pool_size")
    @classmethod
    def validate_pool_size_range(cls, v: int, info) -> int:
        """Ensure max_pool_size is greater than min_pool_size."""
        if "min_pool_size" in info.data:
            min_size = info.data["min_pool_size"]
            if v <= min_size:
                raise ValueError(
                    f"max_pool_size ({v}) must be greater than min_pool_size ({min_size})"
                )
        return v

    @field_validator("pool_reset_on_return")
    @classmethod
    def validate_pool_reset(cls, v: str) -> str:
        """Validate pool_reset_on_return value."""
        valid_values = {"rollback", "commit", None}
        if v not in valid_values:
            raise ValueError(
                f"pool_reset_on_return must be one of {valid_values}, got {v}"
            )
        return v

    class Config:
        """Pydantic model configuration."""

        frozen = False  # Allow updates for dynamic configuration


def get_pool_config_from_settings() -> PoolConfig:
    """Create PoolConfig from application settings.

    Returns:
        PoolConfig: Pool configuration instance populated from environment
    """
    from app.core.config import get_settings

    settings = get_settings()

    return PoolConfig(
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_POOL_MAX_OVERFLOW,
        timeout=settings.DB_POOL_TIMEOUT,
        recycle=settings.DB_POOL_RECYCLE,
        pre_ping=settings.DB_POOL_PRE_PING,
        echo_pool=settings.DEBUG,
        enable_monitoring=True,
        enable_dynamic_sizing=True,
    )
