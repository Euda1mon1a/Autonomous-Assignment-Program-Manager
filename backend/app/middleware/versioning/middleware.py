"""
API Versioning Middleware.

Handles automatic version detection from multiple sources:
1. URL path (e.g., /api/v2/users)
2. Accept-Version header
3. Query parameter (?version=2)

Stores detected version in request.state for downstream use.
"""

import logging
import re
from contextvars import ContextVar
from enum import Enum
from typing import Optional

from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variable for current API version (thread-safe)
_current_api_version: ContextVar[Optional["APIVersion"]] = ContextVar(
    "current_api_version", default=None
)


class APIVersion(str, Enum):
    """
    Supported API versions.

    Each version represents a major API contract. Breaking changes
    require a new version.
    """

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

    @classmethod
    def from_string(cls, version: str) -> Optional["APIVersion"]:
        """
        Parse version string to APIVersion enum.

        Args:
            version: Version string (e.g., "v1", "1", "2.0")

        Returns:
            APIVersion enum or None if invalid
        """
        if not version:
            return None

        # Normalize: remove 'v' prefix and get major version
        version = version.lower().strip()
        if version.startswith("v"):
            version = version[1:]

        # Extract major version number
        major = version.split(".")[0]

        # Map to enum
        version_map = {
            "1": cls.V1,
            "2": cls.V2,
            "3": cls.V3,
        }

        return version_map.get(major)

    @property
    def numeric(self) -> int:
        """Get numeric version number."""
        return int(self.value[1:])  # Remove 'v' prefix

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __lt__(self, other: "APIVersion") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, APIVersion):
            return NotImplemented
        return self.numeric < other.numeric

    def __le__(self, other: "APIVersion") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, APIVersion):
            return NotImplemented
        return self.numeric <= other.numeric


# Default version when none specified
DEFAULT_VERSION = APIVersion.V1

# Latest stable version
LATEST_VERSION = APIVersion.V2


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API version detection and negotiation.

    Detects API version from multiple sources (in priority order):
    1. URL path: /api/v2/endpoint
    2. Accept-Version header: Accept-Version: v2
    3. Query parameter: ?version=2
    4. Default to v1 if not specified

    The detected version is stored in:
    - request.state.api_version (APIVersion enum)
    - Context variable for access in services
    """

    def __init__(
        self,
        app,
        default_version: APIVersion = DEFAULT_VERSION,
        latest_version: APIVersion = LATEST_VERSION,
    ):
        """
        Initialize versioning middleware.

        Args:
            app: FastAPI application
            default_version: Version to use when none specified
            latest_version: Latest stable API version
        """
        super().__init__(app)
        self.default_version = default_version
        self.latest_version = latest_version

        # URL pattern for version detection
        self.url_pattern = re.compile(r"/api/(v\d+)/")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Detect API version and add to request state.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response with version headers
        """
        # Detect version from request
        version = self._detect_version(request)

        # Store in request state
        request.state.api_version = version

        # Store in context variable (for non-request contexts)
        token = _current_api_version.set(version)

        try:
            # Log version for tracking
            if request.url.path.startswith("/api/"):
                logger.debug(
                    f"API request: version={version.value}, "
                    f"method={request.method}, path={request.url.path}"
                )

            # Process request
            response = await call_next(request)

            # Add version information to response headers
            response.headers["X-API-Version"] = version.value
            response.headers["X-API-Latest-Version"] = self.latest_version.value

            return response

        finally:
            # Clean up context
            _current_api_version.reset(token)

    def _detect_version(self, request: Request) -> APIVersion:
        """
        Detect API version from request.

        Priority order:
        1. URL path (/api/v2/...)
        2. Accept-Version header
        3. Query parameter (?version=2)
        4. Default version

        Args:
            request: HTTP request

        Returns:
            Detected APIVersion
        """
        # 1. Check URL path
        url_version = self._extract_from_url(request.url.path)
        if url_version:
            return url_version

        # 2. Check Accept-Version header
        header_version = self._extract_from_header(request.headers)
        if header_version:
            return header_version

        # 3. Check query parameter
        query_version = self._extract_from_query(request.query_params)
        if query_version:
            return query_version

        # 4. Default version
        return self.default_version

    def _extract_from_url(self, path: str) -> APIVersion | None:
        """
        Extract version from URL path.

        Examples:
            /api/v1/users -> v1
            /api/v2/schedules -> v2

        Args:
            path: URL path

        Returns:
            APIVersion or None
        """
        match = self.url_pattern.search(path)
        if match:
            version_str = match.group(1)
            return APIVersion.from_string(version_str)
        return None

    def _extract_from_header(self, headers: Headers) -> APIVersion | None:
        """
        Extract version from Accept-Version header.

        Examples:
            Accept-Version: v1
            Accept-Version: 2
            Accept-Version: 2.0

        Args:
            headers: Request headers

        Returns:
            APIVersion or None
        """
        version_header = headers.get("Accept-Version")
        if version_header:
            return APIVersion.from_string(version_header)
        return None

    def _extract_from_query(self, query_params) -> APIVersion | None:
        """
        Extract version from query parameter.

        Examples:
            ?version=1
            ?version=v2
            ?api_version=2

        Args:
            query_params: Query parameters

        Returns:
            APIVersion or None
        """
        # Check both 'version' and 'api_version' params
        for param in ["version", "api_version"]:
            version_param = query_params.get(param)
            if version_param:
                return APIVersion.from_string(version_param)
        return None


def get_api_version() -> APIVersion:
    """
    Get current API version from context.

    This function can be called from anywhere in the request lifecycle
    to get the detected API version.

    Returns:
        Current APIVersion (defaults to V1 if not set)

    Usage:
        version = get_api_version()
        if version >= APIVersion.V2:
            # Use v2 behavior
            pass
    """
    version = _current_api_version.get()
    return version or DEFAULT_VERSION


def require_version(min_version: APIVersion):
    """
    Decorator to require minimum API version for an endpoint.

    Args:
        min_version: Minimum required API version

    Returns:
        Decorator function

    Usage:
        @require_version(APIVersion.V2)
        async def new_feature_endpoint():
            pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            current = get_api_version()
            if current < min_version:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail=f"This endpoint requires API version {min_version.value} or higher. "
                    f"Current version: {current.value}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def version_changelog() -> dict:
    """
    Get API version changelog.

    Returns comprehensive changelog documenting all API versions,
    their release dates, breaking changes, and deprecations.

    Returns:
        Dictionary mapping version to changelog data
    """
    return {
        "v1": {
            "version": "1.0.0",
            "released": "2024-01-01",
            "status": "stable",
            "description": "Initial API release",
            "features": [
                "Schedule management",
                "Assignment CRUD operations",
                "ACGME compliance validation",
                "Swap request management",
                "User authentication",
            ],
            "breaking_changes": [],
        },
        "v2": {
            "version": "2.0.0",
            "released": "2024-06-01",
            "status": "stable",
            "description": "Enhanced API with performance improvements",
            "features": [
                "Batch operations for assignments",
                "Advanced filtering and pagination",
                "WebSocket support for real-time updates",
                "GraphQL endpoint",
                "Resilience framework integration",
                "Enhanced analytics endpoints",
            ],
            "breaking_changes": [
                {
                    "endpoint": "/api/v2/assignments",
                    "change": "Response format changed to include metadata",
                    "migration": "Access data via response.data instead of response",
                },
                {
                    "endpoint": "/api/v2/schedules/{id}",
                    "change": "Date format changed to ISO 8601",
                    "migration": "Update date parsing to handle ISO 8601 format",
                },
            ],
            "deprecations": [
                {
                    "endpoint": "/api/v1/swaps/legacy",
                    "sunset_date": "2025-01-01",
                    "replacement": "/api/v2/swaps",
                },
            ],
        },
        "v3": {
            "version": "3.0.0",
            "released": "2024-12-01",
            "status": "beta",
            "description": "Next-generation API with AI integration",
            "features": [
                "AI-powered schedule optimization",
                "Predictive conflict detection",
                "Advanced resilience with ML-based forecasting",
                "Multi-tenant support",
                "Enhanced security with OAuth2",
            ],
            "breaking_changes": [
                {
                    "endpoint": "/api/v3/auth",
                    "change": "OAuth2 required, JWT-only auth deprecated",
                    "migration": "Migrate to OAuth2 authentication flow",
                },
            ],
            "deprecations": [],
            "notes": [
                "Beta release - subject to changes",
                "Not recommended for production use yet",
            ],
        },
    }
