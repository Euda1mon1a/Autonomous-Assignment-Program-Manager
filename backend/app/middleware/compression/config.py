"""
Compression configuration for API response compression.

Provides configuration settings for compression middleware including:
- Compression algorithms (gzip, brotli)
- Minimum size threshold
- Content-type filtering
- Quality levels
- Statistics tracking
"""
from dataclasses import dataclass, field
from typing import Set


@dataclass
class CompressionConfig:
    """
    Configuration for response compression.

    Controls when and how responses should be compressed.

    Attributes:
        enabled: Whether compression is enabled globally
        min_size: Minimum response size (bytes) to compress
        gzip_enabled: Enable gzip compression
        gzip_level: Gzip compression level (1-9, higher = better compression)
        brotli_enabled: Enable brotli compression (if available)
        brotli_quality: Brotli quality level (0-11, higher = better compression)
        compressible_types: Content-Type patterns to compress
        exclude_paths: URL paths to exclude from compression
        track_stats: Enable compression statistics tracking
    """
    enabled: bool = True
    min_size: int = 1024  # 1KB minimum
    gzip_enabled: bool = True
    gzip_level: int = 6  # Balance speed/compression (1-9)
    brotli_enabled: bool = True
    brotli_quality: int = 4  # Balance speed/compression (0-11)
    compressible_types: Set[str] = field(default_factory=lambda: {
        # Text formats
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "text/xml",
        "text/csv",
        # Application formats
        "application/json",
        "application/javascript",
        "application/xml",
        "application/x-javascript",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
        "application/vnd.api+json",
        "application/ld+json",
        "application/graphql+json",
        # Other compressible formats
        "image/svg+xml",
        "font/ttf",
        "font/otf",
        "font/woff",
        "font/woff2",
        "font/eot",
    })
    exclude_paths: Set[str] = field(default_factory=lambda: {
        "/metrics",  # Prometheus metrics - often scraped frequently
        "/health",   # Health checks - minimal overhead
        "/docs",     # API docs - static files
        "/redoc",    # ReDoc - static files
        "/openapi.json",  # OpenAPI spec
    })
    track_stats: bool = True


# Default configuration
DEFAULT_CONFIG = CompressionConfig()


# Production configuration - higher compression
PRODUCTION_CONFIG = CompressionConfig(
    gzip_level=9,
    brotli_quality=11,
    min_size=512,  # Compress smaller responses in production
)


# Development configuration - faster compression
DEVELOPMENT_CONFIG = CompressionConfig(
    gzip_level=1,  # Fast compression for development
    brotli_quality=1,
    min_size=2048,  # Only compress larger responses
    track_stats=True,
)


def get_compression_config(
    environment: str = "default"
) -> CompressionConfig:
    """
    Get compression configuration for environment.

    Args:
        environment: Environment name (default, production, development)

    Returns:
        CompressionConfig instance for the environment
    """
    configs = {
        "default": DEFAULT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "development": DEVELOPMENT_CONFIG,
    }
    return configs.get(environment.lower(), DEFAULT_CONFIG)


def is_compressible_content_type(content_type: str, config: CompressionConfig) -> bool:
    """
    Check if content type is compressible.

    Args:
        content_type: Response Content-Type header value
        config: Compression configuration

    Returns:
        True if content type should be compressed
    """
    if not content_type:
        return False

    # Extract base content type (before ';' for charset/boundary)
    base_type = content_type.split(";")[0].strip().lower()

    # Check against configured compressible types
    return base_type in config.compressible_types


def should_exclude_path(path: str, config: CompressionConfig) -> bool:
    """
    Check if path should be excluded from compression.

    Args:
        path: Request URL path
        config: Compression configuration

    Returns:
        True if path should be excluded
    """
    return path in config.exclude_paths
