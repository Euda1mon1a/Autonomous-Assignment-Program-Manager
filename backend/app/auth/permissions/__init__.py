"""
DEPRECATED: PermissionResolver-based system has been archived.

Use `app.auth` (AccessControlMatrix) exports instead.
"""

from __future__ import annotations

import warnings

from app.auth import (
    PermissionAction,
    PermissionCache,
    PermissionContext,
    PermissionDenied,
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

warnings.warn(
    "app.auth.permissions is deprecated; use app.auth instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "PermissionAction",
    "PermissionCache",
    "PermissionContext",
    "PermissionDenied",
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
