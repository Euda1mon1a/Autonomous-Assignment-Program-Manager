"""
Version-Aware API Router.

Extends FastAPI's APIRouter with version-awareness, allowing endpoints
to be defined for specific API versions with automatic deprecation handling.
"""

import logging
from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.middleware.versioning.deprecation import get_deprecation_manager
from app.middleware.versioning.middleware import APIVersion, get_api_version

logger = logging.getLogger(__name__)


class VersionedRoute(APIRoute):
    """
    API Route with version awareness and deprecation handling.

    Extends FastAPI's APIRoute to:
    - Enforce version requirements
    - Add deprecation headers automatically
    - Block access to retired endpoints
    """

    def __init__(
        self,
        path: str,
        endpoint: Callable,
        *,
        min_version: APIVersion | None = None,
        max_version: APIVersion | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize versioned route.

        Args:
            path: Route path
            endpoint: Endpoint function
            min_version: Minimum required API version
            max_version: Maximum allowed API version (for sunset)
            **kwargs: Additional APIRoute arguments
        """
        super().__init__(path, endpoint, **kwargs)
        self.min_version = min_version
        self.max_version = max_version

    def get_route_handler(self) -> Callable:
        """
        Get route handler with version checking.

        Returns:
            Wrapped handler function
        """
        original_handler = super().get_route_handler()

        async def versioned_handler(request: Request) -> Response:
            """
            Handle request with version checking.

            Args:
                request: HTTP request

            Returns:
                HTTP response

            Raises:
                HTTPException: If version requirements not met
            """
            # Get current API version
            current_version = get_api_version()

            # Check minimum version requirement
            if self.min_version and current_version < self.min_version:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"This endpoint requires API version "
                        f"{self.min_version.value} or higher. "
                        f"Current version: {current_version.value}"
                    ),
                )

                # Check maximum version (sunset)
            if self.max_version and current_version > self.max_version:
                raise HTTPException(
                    status_code=410,  # Gone
                    detail=(
                        f"This endpoint is not available in API version "
                        f"{current_version.value}. "
                        f"Maximum supported version: {self.max_version.value}"
                    ),
                )

                # Check for retired endpoints
            deprecation_mgr = get_deprecation_manager()
            sunset_error = deprecation_mgr.check_sunset_enforcement(request)
            if sunset_error:
                raise HTTPException(
                    status_code=410,  # Gone
                    detail=sunset_error["detail"],
                )

                # Process request
            response = await original_handler(request)

            # Add deprecation headers if applicable
            if isinstance(response, Response):
                response = deprecation_mgr.add_deprecation_headers(response, request)

            return response

        return versioned_handler


class VersionedAPIRouter(APIRouter):
    """
    API Router with built-in version management.

    Extends FastAPI's APIRouter to support:
    - Version-specific routes
    - Automatic deprecation warnings
    - Version negotiation
    - Backward compatibility helpers
    """

    def __init__(
        self,
        *,
        min_version: APIVersion | None = None,
        max_version: APIVersion | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize versioned router.

        Args:
            min_version: Minimum API version for all routes in this router
            max_version: Maximum API version for all routes in this router
            **kwargs: Additional APIRouter arguments
        """
        # Use custom route class
        kwargs.setdefault("route_class", VersionedRoute)
        super().__init__(**kwargs)

        self.min_version = min_version
        self.max_version = max_version

    def add_api_route(
        self,
        path: str,
        endpoint: Callable,
        *,
        min_version: APIVersion | None = None,
        max_version: APIVersion | None = None,
        **kwargs,
    ):
        """
        Add API route with version requirements.

        Args:
            path: Route path
            endpoint: Endpoint function
            min_version: Minimum required version (overrides router default)
            max_version: Maximum allowed version (overrides router default)
            **kwargs: Additional route arguments
        """
        # Use router's version requirements if not specified
        if min_version is None:
            min_version = self.min_version
        if max_version is None:
            max_version = self.max_version

            # Pass version requirements to route
        if self.route_class == VersionedRoute:
            kwargs["min_version"] = min_version
            kwargs["max_version"] = max_version

        return super().add_api_route(path, endpoint, **kwargs)

    def version_endpoint(
        self,
        versions: list[APIVersion],
        path: str,
        **route_kwargs,
    ):
        """
        Decorator for version-specific endpoints.

        Creates separate route handlers for different API versions,
        allowing different implementations per version.

        Args:
            versions: List of API versions this endpoint supports
            path: Route path
            **route_kwargs: Additional route arguments

        Returns:
            Decorator function

        Usage:
            @router.version_endpoint([APIVersion.V1, APIVersion.V2], "/users")
            def get_users_v1():
                # V1 implementation
                pass

            @router.version_endpoint([APIVersion.V2], "/users")
            def get_users_v2():
                # V2 implementation with different response format
                pass
        """

        def decorator(func: Callable):
            # Determine min/max versions from list
            min_ver = min(versions)
            max_ver = max(versions)

            # Add route with version constraints
            self.add_api_route(
                path,
                func,
                min_version=min_ver,
                max_version=max_ver,
                **route_kwargs,
            )

            return func

        return decorator

        # Utility functions for version-aware routing


def version_route(
    versions: list[APIVersion],
    router: VersionedAPIRouter | None = None,
):
    """
    Decorator for creating version-specific route handlers.

    Args:
        versions: Supported API versions
        router: Router to add route to (if provided)

    Returns:
        Decorator function

    Usage:
        @version_route([APIVersion.V1])
        async def legacy_endpoint():
            return {"format": "old"}

        @version_route([APIVersion.V2, APIVersion.V3])
        async def modern_endpoint():
            return {"format": "new", "metadata": {...}}
    """

    def decorator(func: Callable):
        # Store version metadata on function
        func.__api_versions__ = versions
        func.__min_version__ = min(versions)
        func.__max_version__ = max(versions)

        # If router provided, add route automatically
        if router:
            router.add_api_route(
                path=f"/{func.__name__}",
                endpoint=func,
                min_version=func.__min_version__,
                max_version=func.__max_version__,
            )

        return func

    return decorator


def create_version_router(
    version: APIVersion,
    prefix: str = "",
    **kwargs,
) -> VersionedAPIRouter:
    """
    Create a router for a specific API version.

    Args:
        version: API version for this router
        prefix: URL prefix (e.g., "/api/v2")
        **kwargs: Additional router arguments

    Returns:
        VersionedAPIRouter configured for the specified version

    Usage:
        v2_router = create_version_router(APIVersion.V2, prefix="/api/v2")

        @v2_router.get("/users")
        async def get_users():
            return {"users": [...]}
    """
    return VersionedAPIRouter(
        prefix=prefix,
        min_version=version,
        max_version=version,
        **kwargs,
    )


def version_dispatch(handlers: dict[APIVersion, Callable]):
    """
    Dispatch to different handlers based on API version.

    Args:
        handlers: Dictionary mapping versions to handler functions

    Returns:
        Dispatcher function

    Usage:
        async def handle_v1(request):
            return {"format": "v1"}

        async def handle_v2(request):
            return {"format": "v2", "enhanced": True}

        @app.get("/endpoint")
        async def endpoint(request: Request):
            return await version_dispatch({
                APIVersion.V1: handle_v1,
                APIVersion.V2: handle_v2,
            })(request)
    """

    async def dispatcher(*args, **kwargs):
        current_version = get_api_version()

        # Find exact match first
        if current_version in handlers:
            handler = handlers[current_version]
            return await handler(*args, **kwargs)

            # Fall back to highest version <= current
        compatible_versions = [v for v in handlers if v <= current_version]

        if compatible_versions:
            best_version = max(compatible_versions)
            handler = handlers[best_version]
            logger.debug(
                f"Version dispatch: {current_version.value} -> {best_version.value}"
            )
            return await handler(*args, **kwargs)

            # No compatible handler found
        raise HTTPException(
            status_code=400,
            detail=f"No handler available for API version {current_version.value}",
        )

    return dispatcher

    # Deprecation route utilities


async def deprecated_endpoint_handler(
    request: Request,
    replacement: str,
    message: str | None = None,
) -> JSONResponse:
    """
    Standard handler for deprecated endpoints.

    Returns 410 Gone with migration information.

    Args:
        request: HTTP request
        replacement: Replacement endpoint URL
        message: Custom deprecation message

    Returns:
        JSON response with deprecation info
    """
    default_message = (
        f"This endpoint has been deprecated. Please use {replacement} instead."
    )

    return JSONResponse(
        status_code=410,  # Gone
        content={
            "detail": message or default_message,
            "deprecated_endpoint": str(request.url.path),
            "replacement": replacement,
            "documentation": "/api/v1/deprecations",
        },
        headers={
            "Deprecation": "true",
            "Link": f'<{replacement}>; rel="alternate"',
        },
    )
