"""
Authentication package for SSO and traditional auth.

This package provides authentication mechanisms including:
- SAML 2.0 Service Provider (SP) implementation
- OAuth2/OIDC authentication flows
- Session management
- Just-in-Time (JIT) user provisioning
- Role-based permission caching with Redis
"""

from app.auth.permissions import (
    PermissionAction,
    PermissionCache,
    PermissionDenied,
    PermissionResolver,
    ResourceType,
    UserRole,
    get_permission_cache,
    get_permission_resolver,
    require_permission,
    warm_permission_cache,
)

__all__ = [
    "sso",
    # Permissions
    "PermissionAction",
    "PermissionCache",
    "PermissionDenied",
    "PermissionResolver",
    "ResourceType",
    "UserRole",
    "get_permission_cache",
    "get_permission_resolver",
    "require_permission",
    "warm_permission_cache",
]
