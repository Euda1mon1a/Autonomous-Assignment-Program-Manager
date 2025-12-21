"""
API Deprecation Management.

Handles deprecation warnings, sunset dates, and version lifecycle management.
Provides automatic warnings for deprecated endpoints and versions.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class VersionStatus(str, Enum):
    """
    API version lifecycle status.

    Represents the current state of an API version in its lifecycle.
    """
    DEVELOPMENT = "development"  # Under active development, unstable
    BETA = "beta"  # Feature complete but not production-ready
    STABLE = "stable"  # Production-ready and actively maintained
    DEPRECATED = "deprecated"  # Still available but not recommended
    SUNSET = "sunset"  # Scheduled for removal
    RETIRED = "retired"  # No longer available


@dataclass
class DeprecationWarning:
    """
    Deprecation warning information.

    Contains all metadata about a deprecated API endpoint or version.
    """
    endpoint: str
    version: str
    status: VersionStatus
    sunset_date: Optional[datetime] = None
    replacement: Optional[str] = None
    message: Optional[str] = None
    documentation_url: Optional[str] = None

    def to_header_value(self) -> str:
        """
        Format deprecation warning for HTTP header.

        Returns warning string suitable for Deprecation and Sunset headers.

        Returns:
            Formatted deprecation warning
        """
        parts = [f'version="{self.version}"']

        if self.sunset_date:
            # RFC 3339 format for Sunset header
            parts.append(f'sunset="{self.sunset_date.isoformat()}"')

        if self.replacement:
            parts.append(f'replacement="{self.replacement}"')

        return "; ".join(parts)

    def days_until_sunset(self) -> Optional[int]:
        """
        Calculate days remaining until sunset.

        Returns:
            Number of days until sunset, or None if no sunset date
        """
        if not self.sunset_date:
            return None

        delta = self.sunset_date - datetime.now()
        return max(0, delta.days)

    def is_past_sunset(self) -> bool:
        """
        Check if sunset date has passed.

        Returns:
            True if past sunset date, False otherwise
        """
        if not self.sunset_date:
            return False
        return datetime.now() > self.sunset_date


class DeprecationManager:
    """
    Manages API deprecation warnings and sunset schedules.

    Tracks deprecated endpoints and versions, provides warnings,
    and enforces sunset policies.
    """

    def __init__(self):
        """Initialize deprecation manager with default warnings."""
        self._deprecations: dict[str, DeprecationWarning] = {}
        self._version_status: dict[str, VersionStatus] = {
            "v1": VersionStatus.STABLE,
            "v2": VersionStatus.STABLE,
            "v3": VersionStatus.BETA,
        }

        # Register default deprecations
        self._register_defaults()

    def _register_defaults(self):
        """Register default deprecation warnings."""
        # Example: Deprecate legacy swap endpoint
        self.register_deprecation(
            endpoint="/api/v1/swaps/legacy",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2025, 6, 1),
            replacement="/api/v2/swaps",
            message="Legacy swap endpoint is deprecated. Use v2 swap API for better performance.",
        )

        # Example: Deprecate old assignment format
        self.register_deprecation(
            endpoint="/api/v1/assignments/bulk",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2025, 3, 1),
            replacement="/api/v2/assignments/batch",
            message="Bulk assignment endpoint replaced with batch operations in v2.",
        )

    def register_deprecation(
        self,
        endpoint: str,
        version: str,
        status: VersionStatus,
        sunset_date: Optional[datetime] = None,
        replacement: Optional[str] = None,
        message: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """
        Register a deprecated endpoint or version.

        Args:
            endpoint: API endpoint path
            version: API version
            status: Version status
            sunset_date: Date when endpoint will be removed
            replacement: Recommended replacement endpoint
            message: Custom deprecation message
            documentation_url: Link to migration documentation
        """
        warning = DeprecationWarning(
            endpoint=endpoint,
            version=version,
            status=status,
            sunset_date=sunset_date,
            replacement=replacement,
            message=message,
            documentation_url=documentation_url,
        )

        self._deprecations[endpoint] = warning

        logger.info(
            f"Registered deprecation: {endpoint} (version {version}, "
            f"status {status.value})"
        )

    def get_deprecation(self, endpoint: str) -> Optional[DeprecationWarning]:
        """
        Get deprecation warning for an endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            DeprecationWarning if endpoint is deprecated, None otherwise
        """
        return self._deprecations.get(endpoint)

    def is_deprecated(self, endpoint: str) -> bool:
        """
        Check if an endpoint is deprecated.

        Args:
            endpoint: API endpoint path

        Returns:
            True if endpoint is deprecated
        """
        return endpoint in self._deprecations

    def get_version_status(self, version: str) -> VersionStatus:
        """
        Get status of an API version.

        Args:
            version: API version (e.g., "v1")

        Returns:
            VersionStatus for the version
        """
        return self._version_status.get(version, VersionStatus.STABLE)

    def set_version_status(self, version: str, status: VersionStatus):
        """
        Update status of an API version.

        Args:
            version: API version
            status: New status
        """
        old_status = self._version_status.get(version)
        self._version_status[version] = status

        logger.info(
            f"Version {version} status changed: {old_status} -> {status.value}"
        )

    def add_deprecation_headers(
        self,
        response: Response,
        request: Request,
    ) -> Response:
        """
        Add deprecation headers to response if applicable.

        Adds the following headers for deprecated endpoints:
        - Deprecation: true (RFC 8594)
        - Sunset: <date> (RFC 8594)
        - Warning: <message> (RFC 7234)
        - Link: <replacement>; rel="alternate"

        Args:
            response: HTTP response
            request: HTTP request

        Returns:
            Response with deprecation headers added
        """
        path = request.url.path
        deprecation = self.get_deprecation(path)

        if not deprecation:
            return response

        # Deprecation header (RFC 8594)
        response.headers["Deprecation"] = "true"

        # Sunset header with date (RFC 8594)
        if deprecation.sunset_date:
            # HTTP date format: Sun, 06 Nov 1994 08:49:37 GMT
            sunset_str = deprecation.sunset_date.strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
            response.headers["Sunset"] = sunset_str

            # Add days remaining in custom header
            days = deprecation.days_until_sunset()
            if days is not None:
                response.headers["X-Days-Until-Sunset"] = str(days)

        # Warning header (RFC 7234)
        if deprecation.message:
            warning_msg = (
                f'299 - "Deprecated API" "{deprecation.message}"'
            )
            response.headers["Warning"] = warning_msg

        # Link to replacement (RFC 8288)
        if deprecation.replacement:
            response.headers["Link"] = (
                f'<{deprecation.replacement}>; rel="alternate"; '
                f'title="Replacement API"'
            )

        # Documentation link
        if deprecation.documentation_url:
            link_header = response.headers.get("Link", "")
            if link_header:
                link_header += ", "
            link_header += (
                f'<{deprecation.documentation_url}>; rel="documentation"; '
                f'title="Migration Guide"'
            )
            response.headers["Link"] = link_header

        # Custom header with structured data
        response.headers["X-API-Deprecation"] = deprecation.to_header_value()

        # Log the deprecation access for monitoring
        logger.warning(
            f"Deprecated endpoint accessed: {path} "
            f"(version {deprecation.version}, "
            f"days until sunset: {deprecation.days_until_sunset()})"
        )

        return response

    def check_sunset_enforcement(self, request: Request) -> Optional[dict]:
        """
        Check if request should be blocked due to sunset.

        Args:
            request: HTTP request

        Returns:
            Error dict if blocked, None if allowed
        """
        path = request.url.path
        deprecation = self.get_deprecation(path)

        if not deprecation:
            return None

        # Block if past sunset date
        if deprecation.is_past_sunset():
            error = {
                "detail": (
                    f"This endpoint has been retired as of "
                    f"{deprecation.sunset_date.strftime('%Y-%m-%d')}."
                ),
                "endpoint": path,
                "version": deprecation.version,
                "status": "retired",
            }

            if deprecation.replacement:
                error["replacement"] = deprecation.replacement

            if deprecation.documentation_url:
                error["documentation"] = deprecation.documentation_url

            return error

        return None

    def get_all_deprecations(self) -> list[dict]:
        """
        Get all registered deprecations.

        Returns:
            List of deprecation information dicts
        """
        result = []
        for endpoint, warning in self._deprecations.items():
            result.append({
                "endpoint": endpoint,
                "version": warning.version,
                "status": warning.status.value,
                "sunset_date": (
                    warning.sunset_date.isoformat()
                    if warning.sunset_date
                    else None
                ),
                "days_until_sunset": warning.days_until_sunset(),
                "replacement": warning.replacement,
                "message": warning.message,
                "documentation_url": warning.documentation_url,
            })

        # Sort by sunset date (soonest first)
        result.sort(
            key=lambda x: x["sunset_date"] if x["sunset_date"] else "9999"
        )

        return result

    def get_version_lifecycle(self) -> dict:
        """
        Get lifecycle information for all API versions.

        Returns:
            Dictionary mapping versions to lifecycle info
        """
        return {
            version: {
                "status": status.value,
                "description": self._get_status_description(status),
            }
            for version, status in self._version_status.items()
        }

    def _get_status_description(self, status: VersionStatus) -> str:
        """Get human-readable description of version status."""
        descriptions = {
            VersionStatus.DEVELOPMENT: "Under active development, not stable",
            VersionStatus.BETA: "Feature complete, testing in progress",
            VersionStatus.STABLE: "Production-ready and actively maintained",
            VersionStatus.DEPRECATED: "Still available but not recommended for new projects",
            VersionStatus.SUNSET: "Scheduled for removal, migrate soon",
            VersionStatus.RETIRED: "No longer available",
        }
        return descriptions.get(status, "Unknown status")


# Global deprecation manager instance
_deprecation_manager: Optional[DeprecationManager] = None


def get_deprecation_manager() -> DeprecationManager:
    """
    Get global deprecation manager instance.

    Returns:
        Singleton DeprecationManager instance
    """
    global _deprecation_manager
    if _deprecation_manager is None:
        _deprecation_manager = DeprecationManager()
    return _deprecation_manager
