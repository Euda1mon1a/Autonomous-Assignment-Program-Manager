"""
Session management package.

Provides comprehensive session management for the application:
- Session creation and lifecycle management
- Device tracking and multi-session support
- Activity logging and monitoring
- Redis-backed distributed storage
- FastAPI middleware integration

Usage:
    from app.auth.sessions import (
        SessionManager,
        get_session_manager,
        SessionMiddleware,
        require_session,
    )

    # In main.py
    app.add_middleware(SessionMiddleware)

    # In routes
    @router.get("/protected")
    async def protected(session: SessionData = Depends(require_session)):
        user_id = session.user_id
"""

from app.auth.sessions.manager import SessionManager, get_session_manager
from app.auth.sessions.middleware import (
    SessionMiddleware,
    SessionState,
    require_session,
)
from app.auth.sessions.models import (
    DeviceInfo,
    DeviceType,
    SessionActivity,
    SessionActivityType,
    SessionCreate,
    SessionData,
    SessionListResponse,
    SessionResponse,
    SessionStats,
    SessionStatus,
)
from app.auth.sessions.storage import (
    InMemorySessionStorage,
    RedisSessionStorage,
    SessionStorage,
    get_session_storage,
)

__all__ = [
    # Manager
    "SessionManager",
    "get_session_manager",
    # Middleware
    "SessionMiddleware",
    "SessionState",
    "require_session",
    # Models
    "DeviceInfo",
    "DeviceType",
    "SessionActivity",
    "SessionActivityType",
    "SessionCreate",
    "SessionData",
    "SessionListResponse",
    "SessionResponse",
    "SessionStats",
    "SessionStatus",
    # Storage
    "InMemorySessionStorage",
    "RedisSessionStorage",
    "SessionStorage",
    "get_session_storage",
]
