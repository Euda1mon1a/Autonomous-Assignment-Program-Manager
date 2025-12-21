"""
Request deduplication middleware package.

Provides idempotency support for API endpoints to prevent duplicate
request processing and ensure consistent responses.

Features:
- Idempotency key extraction from headers or request body
- Duplicate request detection using Redis
- Response caching for duplicated requests
- TTL-based cleanup of cached responses
- Concurrent request handling with locking
- Endpoint-specific configuration

Example:
    from app.middleware.deduplication import DeduplicationMiddleware

    app.add_middleware(DeduplicationMiddleware)
"""

from app.middleware.deduplication.middleware import DeduplicationMiddleware
from app.middleware.deduplication.service import DeduplicationService
from app.middleware.deduplication.storage import (
    DeduplicationStorage,
    RequestRecord,
    RequestStatus,
)

__all__ = [
    "DeduplicationMiddleware",
    "DeduplicationService",
    "DeduplicationStorage",
    "RequestRecord",
    "RequestStatus",
]
