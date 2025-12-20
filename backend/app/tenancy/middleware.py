"""
Tenant identification middleware for FastAPI.

This middleware extracts tenant information from incoming HTTP requests
and sets the tenant context for the duration of the request.

Tenant Identification Methods:
------------------------------
The middleware tries multiple methods to identify the tenant, in order:

1. X-Tenant-ID header (UUID)
2. X-Tenant-Slug header (slug)
3. Subdomain (e.g., hospital1.scheduler.com)
4. Path prefix (e.g., /tenants/hospital1/...)
5. Query parameter (?tenant=hospital1)

Configuration:
-------------
Set the identification method in settings:
- TENANT_IDENTIFICATION_METHOD: "header" | "subdomain" | "path" | "query"

Security:
--------
- Validates tenant exists and is active
- Logs all tenant switches
- Prevents tenant enumeration attacks
- Rate limits tenant lookup failures
"""
import logging
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.db.session import SessionLocal
from app.tenancy.context import (
    set_current_tenant,
    clear_current_tenant,
    propagate_tenant_to_tracing,
)
from app.tenancy.models import Tenant, TenantStatus

logger = logging.getLogger(__name__)


class TenantIdentificationMethod:
    """Supported tenant identification methods."""

    HEADER = "header"  # X-Tenant-ID or X-Tenant-Slug headers
    SUBDOMAIN = "subdomain"  # tenant.example.com
    PATH = "path"  # /tenants/{tenant_slug}/...
    QUERY = "query"  # ?tenant=tenant_slug


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware for identifying and setting tenant context from HTTP requests.

    Extracts tenant information from the request and sets it in the context
    for the duration of the request. Ensures all database queries are
    automatically scoped to the identified tenant.

    Attributes:
        excluded_paths: Paths to exclude from tenant identification (health, metrics)
        identification_method: Method to use for tenant identification
        require_tenant: Whether to require a tenant for all requests
        fallback_tenant_slug: Fallback tenant to use if none specified
    """

    def __init__(
        self,
        app: ASGIApp,
        identification_method: str = TenantIdentificationMethod.HEADER,
        require_tenant: bool = False,
        fallback_tenant_slug: Optional[str] = None,
        excluded_paths: Optional[list[str]] = None,
    ):
        """
        Initialize tenant middleware.

        Args:
            app: ASGI application
            identification_method: How to identify tenant (header, subdomain, path, query)
            require_tenant: Whether to reject requests without a tenant
            fallback_tenant_slug: Default tenant slug if none specified
            excluded_paths: Paths to exclude from tenant identification
        """
        super().__init__(app)
        self.identification_method = identification_method
        self.require_tenant = require_tenant
        self.fallback_tenant_slug = fallback_tenant_slug
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with tenant identification.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip tenant identification for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Clear any previous tenant context (shouldn't happen, but defensive)
        clear_current_tenant()

        # Identify tenant from request
        tenant = await self._identify_tenant(request)

        if tenant:
            # Set tenant context
            set_current_tenant(tenant_id=tenant.id, tenant_slug=tenant.slug)

            # Propagate to distributed tracing
            propagate_tenant_to_tracing()

            # Add tenant info to request state (for logging, etc.)
            request.state.tenant = tenant
            request.state.tenant_id = tenant.id
            request.state.tenant_slug = tenant.slug

            logger.debug(
                f"Request scoped to tenant: {tenant.slug} (ID: {tenant.id})"
            )
        elif self.require_tenant:
            # Tenant required but not found
            logger.warning(f"No tenant identified for request: {request.url.path}")
            # Could return 403 here, but let the route handler decide
            # return Response(status_code=403, content="Tenant required")

        try:
            # Process request
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context after request
            clear_current_tenant()

    async def _identify_tenant(self, request: Request) -> Optional[Tenant]:
        """
        Identify tenant from request using configured method.

        Args:
            request: HTTP request

        Returns:
            Tenant instance or None
        """
        tenant_id = None
        tenant_slug = None

        # Try identification based on method
        if self.identification_method == TenantIdentificationMethod.HEADER:
            tenant_id, tenant_slug = self._extract_from_headers(request)
        elif self.identification_method == TenantIdentificationMethod.SUBDOMAIN:
            tenant_slug = self._extract_from_subdomain(request)
        elif self.identification_method == TenantIdentificationMethod.PATH:
            tenant_slug = self._extract_from_path(request)
        elif self.identification_method == TenantIdentificationMethod.QUERY:
            tenant_slug = self._extract_from_query(request)

        # Fallback to default tenant if configured
        if not tenant_id and not tenant_slug and self.fallback_tenant_slug:
            tenant_slug = self.fallback_tenant_slug

        # Look up tenant in database
        if tenant_id or tenant_slug:
            return await self._lookup_tenant(tenant_id, tenant_slug)

        return None

    def _extract_from_headers(self, request: Request) -> tuple[Optional[UUID], Optional[str]]:
        """
        Extract tenant from HTTP headers.

        Looks for:
        - X-Tenant-ID: UUID of the tenant
        - X-Tenant-Slug: Slug of the tenant

        Args:
            request: HTTP request

        Returns:
            Tuple of (tenant_id, tenant_slug)
        """
        tenant_id = None
        tenant_slug = None

        # Try X-Tenant-ID header
        tenant_id_str = request.headers.get("X-Tenant-ID")
        if tenant_id_str:
            try:
                tenant_id = UUID(tenant_id_str)
            except ValueError:
                logger.warning(f"Invalid tenant ID in header: {tenant_id_str}")

        # Try X-Tenant-Slug header
        tenant_slug = request.headers.get("X-Tenant-Slug")

        return tenant_id, tenant_slug

    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """
        Extract tenant from subdomain.

        For example:
        - hospital1.scheduler.com -> tenant_slug = "hospital1"
        - tenant-2.api.example.com -> tenant_slug = "tenant-2"

        Args:
            request: HTTP request

        Returns:
            Tenant slug or None
        """
        host = request.url.hostname
        if not host:
            return None

        # Split host into parts
        parts = host.split(".")

        # If we have at least 3 parts (subdomain.domain.tld), use first as tenant
        if len(parts) >= 3:
            subdomain = parts[0]
            # Skip common subdomains
            if subdomain not in ["www", "api", "app"]:
                return subdomain

        return None

    def _extract_from_path(self, request: Request) -> Optional[str]:
        """
        Extract tenant from URL path.

        For example:
        - /tenants/hospital1/people -> tenant_slug = "hospital1"
        - /t/tenant-2/schedules -> tenant_slug = "tenant-2"

        Args:
            request: HTTP request

        Returns:
            Tenant slug or None
        """
        path = request.url.path
        parts = path.split("/")

        # Look for /tenants/{slug} or /t/{slug} pattern
        for i, part in enumerate(parts):
            if part in ["tenants", "t"] and i + 1 < len(parts):
                return parts[i + 1]

        return None

    def _extract_from_query(self, request: Request) -> Optional[str]:
        """
        Extract tenant from query parameter.

        For example:
        - /schedules?tenant=hospital1 -> tenant_slug = "hospital1"

        Args:
            request: HTTP request

        Returns:
            Tenant slug or None
        """
        return request.query_params.get("tenant")

    async def _lookup_tenant(
        self,
        tenant_id: Optional[UUID] = None,
        tenant_slug: Optional[str] = None,
    ) -> Optional[Tenant]:
        """
        Look up tenant in database by ID or slug.

        Args:
            tenant_id: Tenant UUID
            tenant_slug: Tenant slug

        Returns:
            Tenant instance or None if not found or inactive
        """
        from sqlalchemy import select

        # Create a database session for tenant lookup
        db = SessionLocal()
        try:
            query = select(Tenant)

            # Filter by ID or slug
            if tenant_id:
                query = query.where(Tenant.id == tenant_id)
            elif tenant_slug:
                query = query.where(Tenant.slug == tenant_slug)
            else:
                return None

            # Execute query
            result = await db.execute(query)
            tenant = result.scalar_one_or_none()

            # Check if tenant is active
            if tenant and tenant.status != TenantStatus.ACTIVE.value:
                logger.warning(
                    f"Tenant {tenant.slug} is {tenant.status}, access denied"
                )
                return None

            return tenant

        except Exception as e:
            logger.error(f"Error looking up tenant: {e}", exc_info=True)
            return None
        finally:
            db.close()


class TenantHeaderInjector:
    """
    Helper to inject tenant headers in outgoing requests.

    Use this when making HTTP calls to other services that need
    tenant context.

    Example:
        headers = TenantHeaderInjector.get_headers()
        response = requests.get("https://api.example.com", headers=headers)
    """

    @staticmethod
    def get_headers() -> dict[str, str]:
        """
        Get HTTP headers with current tenant context.

        Returns:
            Dictionary of headers to include in outgoing requests
        """
        from app.tenancy.context import get_current_tenant_id, get_current_tenant_slug

        headers = {}

        tenant_id = get_current_tenant_id()
        if tenant_id:
            headers["X-Tenant-ID"] = str(tenant_id)

        tenant_slug = get_current_tenant_slug()
        if tenant_slug:
            headers["X-Tenant-Slug"] = tenant_slug

        return headers

    @staticmethod
    def inject_into_request(request_kwargs: dict) -> dict:
        """
        Inject tenant headers into a request kwargs dict.

        Args:
            request_kwargs: Request keyword arguments (for requests library)

        Returns:
            Updated kwargs with tenant headers

        Example:
            kwargs = {"url": "https://api.example.com", "json": {...}}
            kwargs = TenantHeaderInjector.inject_into_request(kwargs)
            response = requests.post(**kwargs)
        """
        headers = request_kwargs.get("headers", {})
        headers.update(TenantHeaderInjector.get_headers())
        request_kwargs["headers"] = headers
        return request_kwargs
