"""
Session manager service.

Provides high-level session management operations:
- Session creation and destruction
- Session timeout and refresh
- Concurrent session limits
- Device tracking
- Force logout
- Activity logging
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Request

from app.auth.sessions.models import (
    DeviceInfo,
    DeviceType,
    SessionActivity,
    SessionActivityType,
    SessionData,
    SessionListResponse,
    SessionResponse,
    SessionStats,
    SessionStatus,
)
from app.auth.sessions.storage import SessionStorage, get_session_storage

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager for user session lifecycle.

    Handles all session operations including creation, validation,
    refresh, and cleanup. Integrates with Redis for distributed
    session management.
    """

    def __init__(
        self,
        storage: SessionStorage | None = None,
        max_sessions_per_user: int = 5,
        default_timeout_minutes: int = 1440,  # 24 hours
        activity_timeout_minutes: int = 30,
        enable_activity_logging: bool = True,
    ):
        """
        Initialize session manager.

        Args:
            storage: Session storage backend (defaults to Redis)
            max_sessions_per_user: Maximum concurrent sessions per user
            default_timeout_minutes: Default session timeout
            activity_timeout_minutes: Timeout for inactive sessions
            enable_activity_logging: Enable activity logging
        """
        self.storage = storage or get_session_storage()
        self.max_sessions_per_user = max_sessions_per_user
        self.default_timeout_minutes = default_timeout_minutes
        self.activity_timeout_minutes = activity_timeout_minutes
        self.enable_activity_logging = enable_activity_logging

    def _generate_session_id(self) -> str:
        """
        Generate a secure random session ID.

        Returns:
            URL-safe random session identifier
        """
        return secrets.token_urlsafe(32)

    def _parse_user_agent(self, user_agent: str | None) -> dict[str, str]:
        """
        Parse user agent string to extract device information.

        Args:
            user_agent: User agent string

        Returns:
            Dictionary with platform, browser, and OS information
        """
        if not user_agent:
            return {"platform": "unknown", "browser": "unknown", "os": "unknown"}

        user_agent_lower = user_agent.lower()

        # Detect platform
        if "mobile" in user_agent_lower:
            platform = "mobile"
        elif "electron" in user_agent_lower:
            platform = "desktop"
        else:
            platform = "web"

        # Detect browser
        browser = "unknown"
        if "firefox" in user_agent_lower:
            browser = "firefox"
        elif "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            browser = "chrome"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            browser = "safari"
        elif "edg" in user_agent_lower:
            browser = "edge"

        # Detect OS
        os_name = "unknown"
        if "windows" in user_agent_lower:
            os_name = "windows"
        elif "mac" in user_agent_lower:
            os_name = "macos"
        elif "linux" in user_agent_lower:
            os_name = "linux"
        elif "android" in user_agent_lower:
            os_name = "android"
        elif "ios" in user_agent_lower or "iphone" in user_agent_lower:
            os_name = "ios"

        return {"platform": platform, "browser": browser, "os": os_name}

    def _extract_device_info(self, request: Request | None) -> DeviceInfo:
        """
        Extract device information from HTTP request.

        Args:
            request: FastAPI request object

        Returns:
            DeviceInfo with parsed device details
        """
        if not request:
            return DeviceInfo()

        # Get user agent
        user_agent = request.headers.get("user-agent")

        # Get IP address (check for proxy headers)
        ip_address = request.headers.get("x-forwarded-for")
        if ip_address:
            # Take first IP if multiple (proxy chain)
            ip_address = ip_address.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        # Parse user agent
        parsed = self._parse_user_agent(user_agent)

        # Determine device type
        device_type = DeviceType.WEB
        if parsed["platform"] == "mobile":
            device_type = DeviceType.MOBILE
        elif parsed["platform"] == "desktop":
            device_type = DeviceType.DESKTOP
        elif "api" in (user_agent or "").lower():
            device_type = DeviceType.API

        return DeviceInfo(
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address,
            platform=parsed["platform"],
            browser=parsed["browser"],
            os=parsed["os"],
        )

    async def create_session(
        self,
        user_id: str | UUID,
        username: str,
        request: Request | None = None,
        jti: str | None = None,
        timeout_minutes: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionData:
        """
        Create a new session for a user.

        Enforces concurrent session limits and logs activity.

        Args:
            user_id: User identifier
            username: Username for display
            request: HTTP request for device info extraction
            jti: Optional JWT token ID
            timeout_minutes: Optional custom timeout
            metadata: Optional custom metadata

        Returns:
            Created SessionData

        Raises:
            ValueError: If max concurrent sessions exceeded
        """
        user_id_str = str(user_id)
        timeout = timeout_minutes or self.default_timeout_minutes

        # Check concurrent session limit
        existing_sessions = await self.storage.get_user_sessions(user_id_str)
        active_sessions = [
            s for s in existing_sessions if s.status == SessionStatus.ACTIVE
        ]

        if len(active_sessions) >= self.max_sessions_per_user:
            # Remove oldest session to make room
            oldest = min(active_sessions, key=lambda s: s.created_at)
            await self.revoke_session(oldest.session_id, reason="max_sessions_exceeded")
            logger.info(
                f"Removed oldest session {oldest.session_id} for user {user_id_str} "
                f"(max sessions: {self.max_sessions_per_user})"
            )

        # Generate session ID
        session_id = self._generate_session_id()

        # Extract device info
        device_info = self._extract_device_info(request)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=timeout)

        # Create session data
        session = SessionData(
            session_id=session_id,
            user_id=user_id_str,
            username=username,
            jti=jti,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            expires_at=expires_at,
            status=SessionStatus.ACTIVE,
            device_info=device_info,
            request_count=0,
            last_ip=device_info.ip_address,
            metadata=metadata or {},
        )

        # Store session
        ttl_seconds = timeout * 60
        success = await self.storage.create(session, ttl_seconds)

        if not success:
            raise RuntimeError(f"Failed to create session for user {user_id_str}")

        # Log activity
        if self.enable_activity_logging:
            await self._log_activity(
                session_id=session_id,
                user_id=user_id_str,
                activity_type=SessionActivityType.LOGIN,
                ip_address=device_info.ip_address,
                user_agent=device_info.user_agent,
            )

        logger.info(
            f"Created session {session_id} for user {user_id_str} "
            f"(device: {device_info.device_type}, expires: {expires_at})"
        )

        return session

    async def get_session(self, session_id: str) -> SessionData | None:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and valid, None otherwise
        """
        session = await self.storage.get(session_id)

        if session and session.is_expired():
            await self.expire_session(session_id)
            return None

        return session

    async def validate_session(
        self,
        session_id: str,
        update_activity: bool = True,
        ip_address: str | None = None,
    ) -> SessionData | None:
        """
        Validate a session and optionally update activity.

        Args:
            session_id: Session identifier
            update_activity: Update last activity timestamp
            ip_address: Current request IP address

        Returns:
            SessionData if valid, None if invalid or expired
        """
        session = await self.get_session(session_id)

        if not session:
            return None

        if session.status != SessionStatus.ACTIVE:
            return None

        # Check activity timeout
        if self.activity_timeout_minutes > 0:
            inactive_duration = datetime.utcnow() - session.last_activity
            if inactive_duration > timedelta(minutes=self.activity_timeout_minutes):
                await self.expire_session(session_id)
                logger.info(
                    f"Session {session_id} expired due to inactivity "
                    f"({inactive_duration.total_seconds() / 60:.1f} minutes)"
                )
                return None

        # Update activity
        if update_activity:
            session.update_activity(ip_address)
            await self.storage.update(session)

            if self.enable_activity_logging:
                await self._log_activity(
                    session_id=session_id,
                    user_id=session.user_id,
                    activity_type=SessionActivityType.ACTIVITY,
                    ip_address=ip_address,
                )

        return session

    async def refresh_session(
        self,
        session_id: str,
        extend_minutes: int | None = None,
    ) -> SessionData | None:
        """
        Refresh a session by extending its expiration time.

        Args:
            session_id: Session identifier
            extend_minutes: Minutes to extend (defaults to default_timeout)

        Returns:
            Updated SessionData if successful, None otherwise
        """
        session = await self.get_session(session_id)

        if not session or session.status != SessionStatus.ACTIVE:
            return None

        # Extend expiration
        extend = extend_minutes or self.default_timeout_minutes
        new_expiration = datetime.utcnow() + timedelta(minutes=extend)
        session.expires_at = new_expiration
        session.last_activity = datetime.utcnow()

        # Update storage with new TTL
        ttl_seconds = extend * 60
        success = await self.storage.update(session, ttl_seconds)

        if not success:
            return None

        # Log activity
        if self.enable_activity_logging:
            await self._log_activity(
                session_id=session_id,
                user_id=session.user_id,
                activity_type=SessionActivityType.REFRESH,
                metadata={"extended_minutes": extend},
            )

        logger.info(f"Refreshed session {session_id} (new expiry: {new_expiration})")

        return session

    async def logout_session(self, session_id: str) -> bool:
        """
        Logout a session (user-initiated).

        Args:
            session_id: Session identifier

        Returns:
            True if session was logged out successfully
        """
        session = await self.get_session(session_id)

        if not session:
            return False

        # Update status
        session.status = SessionStatus.LOGGED_OUT
        await self.storage.update(session)

        # Delete from storage
        await self.storage.delete(session_id)

        # Log activity
        if self.enable_activity_logging:
            await self._log_activity(
                session_id=session_id,
                user_id=session.user_id,
                activity_type=SessionActivityType.LOGOUT,
            )

        logger.info(f"User logged out session {session_id}")

        return True

    async def revoke_session(self, session_id: str, reason: str = "revoked") -> bool:
        """
        Revoke a session (admin/system-initiated).

        Args:
            session_id: Session identifier
            reason: Reason for revocation

        Returns:
            True if session was revoked successfully
        """
        session = await self.get_session(session_id)

        if not session:
            return False

        # Update status
        session.status = SessionStatus.REVOKED
        session.metadata["revoke_reason"] = reason
        await self.storage.update(session)

        # Delete from storage
        await self.storage.delete(session_id)

        # Log activity
        if self.enable_activity_logging:
            await self._log_activity(
                session_id=session_id,
                user_id=session.user_id,
                activity_type=SessionActivityType.REVOKED,
                metadata={"reason": reason},
            )

        logger.warning(f"Session {session_id} revoked: {reason}")

        return True

    async def expire_session(self, session_id: str) -> bool:
        """
        Mark a session as expired.

        Args:
            session_id: Session identifier

        Returns:
            True if session was expired successfully
        """
        session = await self.get_session(session_id)

        if not session:
            return False

        # Update status
        session.status = SessionStatus.EXPIRED
        await self.storage.update(session)

        # Delete from storage
        await self.storage.delete(session_id)

        # Log activity
        if self.enable_activity_logging:
            await self._log_activity(
                session_id=session_id,
                user_id=session.user_id,
                activity_type=SessionActivityType.EXPIRED,
            )

        return True

    async def get_user_sessions(self, user_id: str | UUID) -> SessionListResponse:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            SessionListResponse with session list and counts
        """
        user_id_str = str(user_id)
        sessions = await self.storage.get_user_sessions(user_id_str)

        active_sessions = [s for s in sessions if s.status == SessionStatus.ACTIVE]

        session_responses = [
            SessionResponse(
                session_id=s.session_id,
                user_id=s.user_id,
                username=s.username,
                created_at=s.created_at,
                last_activity=s.last_activity,
                expires_at=s.expires_at,
                status=s.status,
                device_info=s.device_info,
                request_count=s.request_count,
            )
            for s in sessions
        ]

        return SessionListResponse(
            sessions=session_responses,
            total=len(sessions),
            active_count=len(active_sessions),
        )

    async def logout_user_sessions(
        self,
        user_id: str | UUID,
        except_session_id: str | None = None,
    ) -> int:
        """
        Logout all sessions for a user.

        Args:
            user_id: User identifier
            except_session_id: Optional session to keep (logout other devices)

        Returns:
            Number of sessions logged out
        """
        user_id_str = str(user_id)

        # Get all user sessions
        sessions = await self.storage.get_user_sessions(user_id_str)

        logged_out = 0
        for session in sessions:
            if except_session_id and session.session_id == except_session_id:
                continue

            if await self.logout_session(session.session_id):
                logged_out += 1

        logger.info(f"Logged out {logged_out} sessions for user {user_id_str}")

        return logged_out

    async def force_logout_user(self, user_id: str | UUID) -> int:
        """
        Force logout all sessions for a user (admin action).

        Args:
            user_id: User identifier

        Returns:
            Number of sessions revoked
        """
        user_id_str = str(user_id)

        # Get all user sessions
        sessions = await self.storage.get_user_sessions(user_id_str)

        revoked = 0
        for session in sessions:
            if await self.revoke_session(session.session_id, reason="force_logout"):
                revoked += 1

        # Log activity
        if self.enable_activity_logging and revoked > 0:
            await self._log_activity(
                session_id="admin",
                user_id=user_id_str,
                activity_type=SessionActivityType.FORCE_LOGOUT,
                metadata={"sessions_revoked": revoked},
            )

        logger.warning(f"Force logged out {revoked} sessions for user {user_id_str}")

        return revoked

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from storage.

        Returns:
            Number of sessions cleaned up
        """
        cleaned = await self.storage.cleanup_expired()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired sessions")
        return cleaned

    async def get_session_stats(self) -> SessionStats:
        """
        Get session statistics.

        Returns:
            SessionStats with metrics
        """
        # Note: This is a simplified implementation
        # For production, you'd want to cache these stats
        # and update them periodically via a background task

        stats = SessionStats()

        # This would be expensive for large session counts
        # Consider using Redis counters or periodic aggregation
        logger.info("Session stats requested (placeholder implementation)")

        return stats

    async def _log_activity(
        self,
        session_id: str,
        user_id: str,
        activity_type: SessionActivityType,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log session activity.

        Args:
            session_id: Session identifier
            user_id: User identifier
            activity_type: Type of activity
            ip_address: Optional IP address
            user_agent: Optional user agent
            metadata: Optional metadata
        """
        activity = SessionActivity(
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        # In production, you'd store this in a database or send to an analytics service
        # For now, we just log it
        logger.debug(
            f"Session activity: {activity_type.value} "
            f"(session={session_id}, user={user_id})"
        )


# Global session manager instance
_session_manager: SessionManager | None = None


def get_session_manager(
    storage: SessionStorage | None = None,
    **kwargs,
) -> SessionManager:
    """
    Get or create global session manager instance.

    Args:
        storage: Optional custom storage backend
        **kwargs: Additional SessionManager arguments

    Returns:
        SessionManager instance
    """
    global _session_manager

    if _session_manager is None:
        _session_manager = SessionManager(storage=storage, **kwargs)

    return _session_manager
