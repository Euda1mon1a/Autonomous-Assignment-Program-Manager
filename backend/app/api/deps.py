"""
API dependencies re-export module.

This module provides a convenient import location for common FastAPI dependencies.
"""

from app.core.security import get_current_user, get_current_active_user
from app.db.session import get_db, get_async_db


# Optional user retrieval (returns None if not authenticated)
async def get_current_user_optional() -> None:
    """Return current user or None if not authenticated."""
    # This is a placeholder - actual implementation depends on auth flow
    return None


# Re-export for backwards compatibility
async def get_user_from_token(token: str) -> dict[str, str]:
    """Extract user from JWT token."""
    from app.core.security import verify_token

    token_data = verify_token(token)
    if token_data is None:
        return {}
    return {
        "user_id": token_data.user_id or "",
        "username": token_data.username or "",
    }


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
    "get_db",
    "get_async_db",
    "get_user_from_token",
]
