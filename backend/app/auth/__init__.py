"""
Authentication package for SSO and traditional auth.

This package provides authentication mechanisms including:
- SAML 2.0 Service Provider (SP) implementation
- OAuth2/OIDC authentication flows
- Session management
- Just-in-Time (JIT) user provisioning
- Role-based permission caching with Redis
"""

from app.auth.access_matrix import (
    AccessControlMatrix,
    PermissionAction,
    PermissionCache,
    PermissionDenied,
    PermissionContext,
    ResourceType,
    UserRole,
    get_acm,
    get_permission_cache,
    has_permission,
    invalidate_permission_cache,
    invalidate_user_role_cache,
    require_permission,
    require_role,
    warm_permission_cache,
)

__all__ = [
    "sso",
    # Permissions
    "AccessControlMatrix",
    "PermissionAction",
    "PermissionCache",
    "PermissionDenied",
    "PermissionContext",
    "ResourceType",
    "UserRole",
    "get_acm",
    "get_permission_cache",
    "has_permission",
    "invalidate_permission_cache",
    "invalidate_user_role_cache",
    "require_permission",
    "require_role",
    "warm_permission_cache",
]
