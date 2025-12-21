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

from app.auth.sessions.manager import SessionManager, get_session_manager
from app.auth.sessions.middleware import SessionState
from app.auth.sessions.models import (
    SessionListResponse,
    SessionResponse,
    SessionStats,
)
from app.core.security import get_admin_user, get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=SessionListResponse)
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


@router.get("/me/current", response_model=SessionResponse | None)
async def get_current_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
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


@router.post("/me/refresh")
async def refresh_current_session(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
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

    return {
        "message": "Session refreshed successfully",
        "session_id": refreshed.session_id,
        "expires_at": refreshed.expires_at,
    }


@router.delete("/me/{session_id}")
async def logout_specific_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
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

    return {"message": "Session logged out successfully"}


@router.delete("/me/other")
async def logout_other_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
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

    return {
        "message": f"Logged out {count} other sessions",
        "count": count,
    }


@router.delete("/me/all")
async def logout_all_my_sessions(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Logout all sessions for the current user.

    This will log out the current session as well.
    User will need to login again.
    """
    count = await session_manager.logout_user_sessions(user_id=current_user.id)

    # Clear session cookie
    response.delete_cookie(key="session_id", path="/")

    return {
        "message": f"Logged out all {count} sessions",
        "count": count,
    }


@router.get("/stats", response_model=SessionStats)
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


@router.get("/user/{user_id}", response_model=SessionListResponse)
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


@router.delete("/user/{user_id}/force-logout")
async def force_logout_user(
    user_id: str,
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Force logout all sessions for a user (admin only).

    Used for security incidents or account suspension.
    All sessions are revoked immediately.
    """
    count = await session_manager.force_logout_user(user_id)

    return {
        "message": f"Force logged out user {user_id}",
        "sessions_revoked": count,
    }


@router.delete("/session/{session_id}")
async def revoke_session_admin(
    session_id: str,
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
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

    return {"message": "Session revoked successfully"}


@router.post("/cleanup")
async def cleanup_expired_sessions(
    current_user: User = Depends(get_admin_user),
    session_manager: SessionManager = Depends(get_session_manager),
):
    """
    Manually trigger cleanup of expired sessions (admin only).

    Note: Redis automatically handles TTL expiration,
    so this is mainly for manual maintenance.
    """
    count = await session_manager.cleanup_expired_sessions()

    return {
        "message": "Expired sessions cleaned up",
        "count": count,
    }
