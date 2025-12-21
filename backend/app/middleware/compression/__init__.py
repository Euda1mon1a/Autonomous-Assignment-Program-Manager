"""
Response compression middleware package.

Provides automatic compression of API responses using gzip or brotli.

Features:
- Content-type aware compression
- Minimum size threshold
- Accept-Encoding negotiation
- Streaming compression support
- Performance statistics tracking
- Configurable compression levels

Usage:
    from app.middleware.compression import CompressionMiddleware, CompressionConfig

    ***REMOVED*** Default configuration
    app.add_middleware(CompressionMiddleware)

    ***REMOVED*** Custom configuration
    config = CompressionConfig(
        min_size=2048,
        gzip_level=9,
        brotli_quality=11,
    )
    app.add_middleware(CompressionMiddleware, config=config)

    ***REMOVED*** Production configuration
    from app.middleware.compression import PRODUCTION_CONFIG
    app.add_middleware(CompressionMiddleware, config=PRODUCTION_CONFIG)
"""
from app.middleware.compression.config import (
    CompressionConfig,
    DEFAULT_CONFIG,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    get_compression_config,
    is_compressible_content_type,
    should_exclude_path,
)
from app.middleware.compression.encoders import (
    BrotliEncoder,
    CompressionEncoder,
    EncoderFactory,
    GzipEncoder,
)
from app.middleware.compression.middleware import (
    CompressionMiddleware,
    CompressionStats,
)

__all__ = [
    ***REMOVED*** Middleware
    "CompressionMiddleware",
    "CompressionStats",
    ***REMOVED*** Configuration
    "CompressionConfig",
    "DEFAULT_CONFIG",
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG",
    "get_compression_config",
    "is_compressible_content_type",
    "should_exclude_path",
    ***REMOVED*** Encoders
    "CompressionEncoder",
    "GzipEncoder",
    "BrotliEncoder",
    "EncoderFactory",
]
