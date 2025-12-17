"""FastAPI dependencies for API routes."""

from app.api.dependencies.role_filter import (
    apply_role_filter,
    check_endpoint_access,
    filter_response,
    get_current_user_role,
    get_role_filter_service,
    require_admin,
    require_resource_access,
)

__all__ = [
    "get_role_filter_service",
    "require_resource_access",
    "require_admin",
    "apply_role_filter",
    "filter_response",
    "get_current_user_role",
    "check_endpoint_access",
]
