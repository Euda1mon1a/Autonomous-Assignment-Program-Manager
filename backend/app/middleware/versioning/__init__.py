"""
API Versioning Middleware Package.

This package provides comprehensive API versioning capabilities including:
- URL path versioning (/api/v1/, /api/v2/)
- Header versioning (Accept-Version header)
- Query parameter versioning (?version=2)
- Deprecation warnings with Sunset headers
- Version negotiation and fallback
- Response transformation for version compatibility
- Version changelog tracking

Usage:
    from app.middleware.versioning import VersioningMiddleware, APIVersion

    app.add_middleware(VersioningMiddleware)
"""

from app.middleware.versioning.deprecation import (
    DeprecationManager,
    DeprecationWarning,
    VersionStatus,
)
from app.middleware.versioning.middleware import (
    APIVersion,
    VersioningMiddleware,
    get_api_version,
)
from app.middleware.versioning.router import VersionedAPIRouter
from app.middleware.versioning.transformers import (
    ResponseTransformer,
    TransformRegistry,
    register_transformer,
)

__all__ = [
    # Core versioning
    "VersioningMiddleware",
    "APIVersion",
    "get_api_version",
    # Router
    "VersionedAPIRouter",
    # Deprecation
    "DeprecationManager",
    "DeprecationWarning",
    "VersionStatus",
    # Transformers
    "ResponseTransformer",
    "TransformRegistry",
    "register_transformer",
]
