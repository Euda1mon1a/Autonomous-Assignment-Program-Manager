"""
HTTP response caching package.

Provides comprehensive HTTP caching capabilities including:
- Cache-Control headers
- ETag generation and validation
- Last-Modified/If-Modified-Since support
- Conditional requests (304 Not Modified)
- Vary header support
- Cache invalidation strategies
- Redis-backed cache storage

This package implements RFC 7234 (HTTP Caching) and RFC 7232 (Conditional Requests).
"""

from app.caching.etag import ETagGenerator, generate_etag, weak_etag
from app.caching.http_cache import HTTPCache, HTTPCacheConfig, CacheDirective
from app.caching.invalidation import CacheInvalidator, InvalidationEvent
from app.caching.middleware import HTTPCacheMiddleware

__all__ = [
    "ETagGenerator",
    "generate_etag",
    "weak_etag",
    "HTTPCache",
    "HTTPCacheConfig",
    "CacheDirective",
    "CacheInvalidator",
    "InvalidationEvent",
    "HTTPCacheMiddleware",
]
