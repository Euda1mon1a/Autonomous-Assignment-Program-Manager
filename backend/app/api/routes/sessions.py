"""
Session management API routes.

Provides endpoints for:
- Viewing active sessions
- Managing user sessions
- Force logout
- Session refresh
- Session statistics

Thin routing layer following the application's layered architecture.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.auth.sessions.manager import SessionManager, get_session_manager
from app.auth.sessions.middleware import SessionState
from app.auth.sessions.models import (
    SessionListResponse,
    SessionResponse,
    SessionStats,
)
from app.core.security import get_admin_user, get_current_active_user
from app.models.user import User

router = APIRouter(tags=["sessions"])


# Response Models
class SessionRefreshResponse(BaseModel):
    """Session refresh response."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Session ID")
    expires_at: str = Field(..., description="New expiration timestamp")


class SessionLogoutResponse(BaseModel):
    """Session logout response."""

    message: str = Field(..., description="Success message")


class SessionLogoutMultipleResponse(BaseModel):
    """Multiple sessions logout response."""

    message: str = Field(..., description="Success message")
    count: int = Field(..., description="Number of sessions logged out")


class ForceLogoutResponse(BaseModel):
    """Force logout response."""

    message: str = Field(..., description="Success message")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")


class SessionRevokeResponse(BaseModel):
    """Session revoke response."""

    message: str = Field(..., description="Success message")


class CleanupResponse(BaseModel):
    """Cleanup response."""

    message: str = Field(..., description="Success message")
    count: int = Field(..., description="Number of sessions cleaned up")


@router.get(
    "/me",
    response_model=SessionListResponse,
    summary="Get My Active Sessions",
    description="List all active sessions for current user with device info and last activity",
    response_description="List of active sessions (useful for 'Where you're logged in' feature)",
)
async def get_my_sessions(
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Get all active sessions for the current user.

    Returns list of sessions with device info, last activity, etc.
    Useful for "Where you're logged in" feature.
    """
    sessions = await session_manager.get_user_sessions(current_user.id)
    return sessions


@router.get(
    "/me/current",
    response_model=SessionResponse | None,
    summary="Get Current Session Info",
    description="Get detailed information about the current active session",
    response_description="Current session details or null if no session",
)
async def get_current_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> SessionResponse | None:
    """
    Get information about the current session.

    Returns session details for the current request.
    """
    session = SessionState.get_session(request)

    if not session:
        return None

    return SessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        username=session.username,
        created_at=session.created_at,
        last_activity=session.last_activity,
        expires_at=session.expires_at,
        status=session.status,
        device_info=session.device_info,
        request_count=session.request_count,
    )


@router.post(
    "/me/refresh",
    response_model=SessionRefreshResponse,
    summary="Refresh Current Session",
    description="Extend current session expiration (for 'Stay logged in' functionality)",
    response_description="Updated session with new expiration time",
)
async def refresh_current_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionRefreshResponse:
    """
    Refresh the current session to extend its expiration.

    Useful for "Stay logged in" functionality.
    """
    session = SessionState.get_session(request)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found",
        )

    refreshed = await session_manager.refresh_session(session.session_id)

    if not refreshed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to refresh session",
        )

    return SessionRefreshResponse(
        message="Session refreshed successfully",
        session_id=refreshed.session_id,
        expires_at=str(refreshed.expires_at),
    )


@router.delete(
    "/me/{session_id}",
    response_model=SessionLogoutResponse,
    summary="Logout Specific Session",
    description="Logout from a specific device/browser (validates session ownership)",
    response_description="Confirmation that session was logged out",
)
async def logout_specific_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionLogoutResponse:
    """
    Logout a specific session.

    Allows users to logout from a specific device/browser.
    Validates that the session belongs to the current user.
    """
    # Get the session to verify ownership
    session = await session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Verify session belongs to current user
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot logout another user's session",
        )

    # Logout the session
    success = await session_manager.logout_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout session",
        )

    return SessionLogoutResponse(message="Session logged out successfully")


@router.delete(
    "/me/other",
    response_model=SessionLogoutMultipleResponse,
    summary="Logout Other Sessions",
    description="Logout all sessions except current one (for 'Logout everywhere else' feature)",
    response_description="Number of other sessions logged out",
)
async def logout_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionLogoutMultipleResponse:
    """
    Logout all other sessions except the current one.

    Useful for "Logout everywhere else" functionality.
    Keeps the current session active.
    """
    current_session = SessionState.get_session(request)
    current_session_id = current_session.session_id if current_session else None

    # Logout all sessions except current
    count = await session_manager.logout_user_sessions(
        user_id=current_user.id,
        except_session_id=current_session_id,
    )

    return SessionLogoutMultipleResponse(
        message=f"Logged out {count} other sessions",
        count=count,
    )


@router.delete(
    "/me/all",
    response_model=SessionLogoutMultipleResponse,
    summary="Logout All My Sessions",
    description="Logout from all devices (including current session, requires re-login)",
    response_description="Total count of sessions logged out",
)
async def logout_all_my_sessions(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionLogoutMultipleResponse:
    """
    Logout all sessions for the current user.

    This will log out the current session as well.
    User will need to login again.
    """
    count = await session_manager.logout_user_sessions(user_id=current_user.id)

    # Clear session cookie
    response.delete_cookie(key="session_id", path="/")

    return SessionLogoutMultipleResponse(
        message=f"Logged out all {count} sessions",
        count=count,
    )


@router.get(
    "/stats",
    response_model=SessionStats,
    summary="Get Session Statistics",
    description="Get system-wide session metrics (admin only)",
    response_description="Metrics about active sessions, concurrent users, etc.",
)
async def get_session_stats(
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Get session statistics (admin only).

    Returns metrics about active sessions, concurrent users, etc.
    """
    stats = await session_manager.get_session_stats()
    return stats


@router.get(
    "/user/{user_id}",
    response_model=SessionListResponse,
    summary="Get User Sessions (Admin)",
    description="View all sessions for any user (admin only)",
    response_description="List of sessions for the specified user",
)
async def get_user_sessions_admin(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Get all sessions for a specific user (admin only).

    Allows administrators to view sessions for any user.
    """
    sessions = await session_manager.get_user_sessions(user_id)
    return sessions


@router.delete(
    "/user/{user_id}/force-logout",
    response_model=ForceLogoutResponse,
    summary="Force Logout User (Admin)",
    description="Immediately revoke all sessions for a user (admin only, for security incidents)",
    response_description="Number of sessions revoked",
)
async def force_logout_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> ForceLogoutResponse:
    """
    Force logout all sessions for a user (admin only).

    Used for security incidents or account suspension.
    All sessions are revoked immediately.
    """
    count = await session_manager.force_logout_user(user_id)

    return ForceLogoutResponse(
        message=f"Force logged out user {user_id}",
        sessions_revoked=count,
    )


@router.delete(
    "/session/{session_id}",
    response_model=SessionRevokeResponse,
    summary="Revoke Specific Session (Admin)",
    description="Immediately invalidate a specific session (admin only, for security purposes)",
    response_description="Confirmation of session revocation",
)
async def revoke_session_admin(
    session_id: str,
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> SessionRevokeResponse:
    """
    Revoke a specific session (admin only).

    Immediately invalidates the session.
    Used for security purposes.
    """
    success = await session_manager.revoke_session(
        session_id=session_id,
        reason="admin_revocation",
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked",
        )

    return SessionRevokeResponse(message="Session revoked successfully")


@router.post(
    "/cleanup",
    response_model=CleanupResponse,
    summary="Cleanup Expired Sessions (Admin)",
    description="Manually trigger cleanup of expired sessions (admin only, mainly for manual maintenance)",
    response_description="Number of expired sessions cleaned up",
)
async def cleanup_expired_sessions(
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
) -> CleanupResponse:
    """
    Manually trigger cleanup of expired sessions (admin only).

    Note: Redis automatically handles TTL expiration,
    so this is mainly for manual maintenance.
    """
    count = await session_manager.cleanup_expired_sessions()

    return CleanupResponse(
        message="Expired sessions cleaned up",
        count=count,
    )
