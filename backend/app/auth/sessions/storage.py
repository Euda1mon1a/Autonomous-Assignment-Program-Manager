"""
Session storage backends.

Provides storage implementations for session data:
- RedisSessionStorage: Production-ready Redis backend
- InMemorySessionStorage: Testing/development backend

All storage backends implement the SessionStorage protocol.
"""

import logging
from datetime import datetime
from typing import Protocol

import redis.asyncio as redis

from app.auth.sessions.models import SessionData, SessionStatus
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SessionStorage(Protocol):
    """
    Protocol for session storage backends.

    All storage implementations must implement these methods.
    """

    async def create(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """
        Create a new session in storage.

        Args:
            session: Session data to store
            ttl_seconds: Optional TTL in seconds

        Returns:
            True if session was created successfully
        """
        ...

    async def get(self, session_id: str) -> SessionData | None:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found, None otherwise
        """
        ...

    async def update(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """
        Update an existing session.

        Args:
            session: Updated session data
            ttl_seconds: Optional new TTL in seconds

        Returns:
            True if session was updated successfully
        """
        ...

    async def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        ...

    async def get_user_sessions(self, user_id: str) -> list[SessionData]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active sessions for the user
        """
        ...

    async def delete_user_sessions(
        self, user_id: str, except_session_id: str | None = None
    ) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User identifier
            except_session_id: Optional session to keep (for logout-other-devices)

        Returns:
            Number of sessions deleted
        """
        ...

    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions from storage.

        Returns:
            Number of sessions removed
        """
        ...


class RedisSessionStorage:
    """
    Redis-based session storage backend.

    Uses Redis for distributed session management with:
    - Automatic TTL-based expiration
    - Efficient user-session indexing
    - Atomic operations
    - Connection pooling
    """

    def __init__(
        self, key_prefix: str = "session", user_index_prefix: str = "user_sessions"
    ):
        """
        Initialize Redis session storage.

        Args:
            key_prefix: Prefix for session keys
            user_index_prefix: Prefix for user session index keys
        """
        self.key_prefix = key_prefix
        self.user_index_prefix = user_index_prefix
        self._redis: redis.Redis | None = None
        self._settings = get_settings()

    async def _get_redis(self) -> redis.Redis:
        """
        Get or create async Redis connection.

        Returns:
            Redis client instance

        Raises:
            ConnectionError: If Redis is unavailable
        """
        if self._redis is None:
            redis_url = self._settings.redis_url_with_password
            self._redis = redis.from_url(redis_url, decode_responses=True)

        return self._redis

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session data."""
        return f"{self.key_prefix}:{session_id}"

    def _user_index_key(self, user_id: str) -> str:
        """Generate Redis key for user session index."""
        return f"{self.user_index_prefix}:{user_id}"

    async def create(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """
        Create a new session in Redis.

        Args:
            session: Session data to store
            ttl_seconds: Optional TTL in seconds (auto-calculated if None)

        Returns:
            True if session was created successfully
        """
        try:
            redis_client = await self._get_redis()
            session_key = self._session_key(session.session_id)
            user_index_key = self._user_index_key(session.user_id)

            # Calculate TTL
            if ttl_seconds is None and session.expires_at:
                ttl_seconds = int(
                    (session.expires_at - datetime.utcnow()).total_seconds()
                )
            ttl_seconds = ttl_seconds or 86400  # Default 24 hours

            # Serialize session data
            session_json = session.model_dump_json()

            # Use pipeline for atomic operations
            async with redis_client.pipeline() as pipe:
                # Store session data
                await pipe.setex(session_key, ttl_seconds, session_json)

                # Add to user's session index
                await pipe.sadd(user_index_key, session.session_id)

                # Set TTL on user index (slightly longer than max session TTL)
                await pipe.expire(user_index_key, ttl_seconds + 3600)

                await pipe.execute()

            logger.info(
                f"Created session {session.session_id} for user {session.user_id}"
            )
            return True

        except redis.RedisError as e:
            logger.error(f"Redis error creating session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    async def get(self, session_id: str) -> SessionData | None:
        """
        Retrieve a session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            SessionData if found and valid, None otherwise
        """
        try:
            redis_client = await self._get_redis()
            session_key = self._session_key(session_id)

            session_json = await redis_client.get(session_key)
            if session_json is None:
                return None

            # Deserialize session data
            session = SessionData.model_validate_json(session_json)

            # Check if expired
            if session.is_expired():
                await self.delete(session_id)
                return None

            return session

        except redis.RedisError as e:
            logger.error(f"Redis error getting session: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    async def update(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """
        Update an existing session in Redis.

        Args:
            session: Updated session data
            ttl_seconds: Optional new TTL in seconds

        Returns:
            True if session was updated successfully
        """
        try:
            redis_client = await self._get_redis()
            session_key = self._session_key(session.session_id)

            # Check if session exists
            exists = await redis_client.exists(session_key)
            if not exists:
                logger.warning(
                    f"Attempted to update non-existent session {session.session_id}"
                )
                return False

            # Calculate TTL
            if ttl_seconds is None and session.expires_at:
                ttl_seconds = int(
                    (session.expires_at - datetime.utcnow()).total_seconds()
                )

            # Serialize session data
            session_json = session.model_dump_json()

            # Update session
            if ttl_seconds:
                await redis_client.setex(session_key, ttl_seconds, session_json)
            else:
                await redis_client.set(session_key, session_json, keepttl=True)

            return True

        except redis.RedisError as e:
            logger.error(f"Redis error updating session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False

    async def delete(self, session_id: str) -> bool:
        """
        Delete a session from Redis.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        try:
            redis_client = await self._get_redis()
            session_key = self._session_key(session_id)

            # Get session to find user_id for index cleanup
            session = await self.get(session_id)
            if session:
                user_index_key = self._user_index_key(session.user_id)

                # Use pipeline for atomic operations
                async with redis_client.pipeline() as pipe:
                    await pipe.delete(session_key)
                    await pipe.srem(user_index_key, session_id)
                    await pipe.execute()
            else:
                # Session not found, just try to delete the key
                await redis_client.delete(session_key)

            logger.info(f"Deleted session {session_id}")
            return True

        except redis.RedisError as e:
            logger.error(f"Redis error deleting session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    async def get_user_sessions(self, user_id: str) -> list[SessionData]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active SessionData objects
        """
        try:
            redis_client = await self._get_redis()
            user_index_key = self._user_index_key(user_id)

            # Get all session IDs for this user
            session_ids = await redis_client.smembers(user_index_key)
            if not session_ids:
                return []

            sessions = []
            for session_id in session_ids:
                session = await self.get(session_id)
                if session and session.status == SessionStatus.ACTIVE:
                    sessions.append(session)

            return sessions

        except redis.RedisError as e:
            logger.error(f"Redis error getting user sessions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    async def delete_user_sessions(
        self, user_id: str, except_session_id: str | None = None
    ) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User identifier
            except_session_id: Optional session ID to keep

        Returns:
            Number of sessions deleted
        """
        try:
            sessions = await self.get_user_sessions(user_id)
            deleted = 0

            for session in sessions:
                if except_session_id and session.session_id == except_session_id:
                    continue

                if await self.delete(session.session_id):
                    deleted += 1

            logger.info(f"Deleted {deleted} sessions for user {user_id}")
            return deleted

        except Exception as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0

    async def cleanup_expired(self) -> int:
        """
        Remove expired sessions from Redis.

        Note: Redis automatically handles TTL expiration, but this method
        can be used to clean up sessions marked as expired in their status.

        Returns:
            Number of sessions removed
        """
        # Redis handles TTL automatically, so we don't need to do much here
        # This is mainly for sessions that were manually marked as expired
        logger.info("Redis handles TTL-based expiration automatically")
        return 0

    async def get_session_count(self) -> int:
        """
        Get total count of active sessions.

        Returns:
            Number of active sessions
        """
        try:
            redis_client = await self._get_redis()
            pattern = f"{self.key_prefix}:*"
            count = 0

            # Use SCAN for better performance with large datasets
            cursor = 0
            while True:
                cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
                count += len(keys)

                if cursor == 0:
                    break

            return count

        except Exception as e:
            logger.error(f"Error counting sessions: {e}")
            return 0


class InMemorySessionStorage:
    """
    In-memory session storage for testing and development.

    WARNING: Not suitable for production use.
    - Data lost on restart
    - Not distributed
    - Limited to single process
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._sessions: dict[str, SessionData] = {}
        self._user_index: dict[str, set[str]] = {}

    async def create(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """Create a new session in memory."""
        self._sessions[session.session_id] = session

        # Update user index
        if session.user_id not in self._user_index:
            self._user_index[session.user_id] = set()
        self._user_index[session.user_id].add(session.session_id)

        return True

    async def get(self, session_id: str) -> SessionData | None:
        """Retrieve a session from memory."""
        session = self._sessions.get(session_id)

        if session and session.is_expired():
            await self.delete(session_id)
            return None

        return session

    async def update(
        self, session: SessionData, ttl_seconds: int | None = None
    ) -> bool:
        """Update an existing session in memory."""
        if session.session_id not in self._sessions:
            return False

        self._sessions[session.session_id] = session
        return True

    async def delete(self, session_id: str) -> bool:
        """Delete a session from memory."""
        session = self._sessions.pop(session_id, None)
        if session:
            # Clean up user index
            if session.user_id in self._user_index:
                self._user_index[session.user_id].discard(session.session_id)
                if not self._user_index[session.user_id]:
                    del self._user_index[session.user_id]
            return True
        return False

    async def get_user_sessions(self, user_id: str) -> list[SessionData]:
        """Get all active sessions for a user."""
        session_ids = self._user_index.get(user_id, set())
        sessions = []

        for session_id in session_ids:
            session = await self.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)

        return sessions

    async def delete_user_sessions(
        self, user_id: str, except_session_id: str | None = None
    ) -> int:
        """Delete all sessions for a user."""
        sessions = await self.get_user_sessions(user_id)
        deleted = 0

        for session in sessions:
            if except_session_id and session.session_id == except_session_id:
                continue

            if await self.delete(session.session_id):
                deleted += 1

        return deleted

    async def cleanup_expired(self) -> int:
        """Remove expired sessions from memory."""
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired()
        ]

        for session_id in expired_ids:
            await self.delete(session_id)

        return len(expired_ids)


# Global storage instance
_storage: SessionStorage | None = None


def get_session_storage(use_redis: bool = True) -> SessionStorage:
    """
    Get session storage instance.

    Args:
        use_redis: Use Redis storage (True) or in-memory (False)

    Returns:
        SessionStorage implementation
    """
    global _storage

    if _storage is None:
        if use_redis:
            _storage = RedisSessionStorage()
        else:
            _storage = InMemorySessionStorage()

    return _storage
