"""Tests for DistributedLock."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from app.cache.distributed_lock import DistributedLock, LockManager, get_lock_manager


class TestDistributedLock:
    """Test suite for DistributedLock."""

    # ========================================================================
    # Initialization Tests
    # ========================================================================

    def test_init_default_values(self):
        """Test initialization with default values."""
        lock = DistributedLock("test_lock")

        assert lock.name == "lock:test_lock"
        assert lock.timeout == 10
        assert lock.retry_interval == 0.1
        assert lock.identifier is not None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        lock = DistributedLock(
            "test_lock",
            timeout=30,
            retry_interval=0.5,
        )

        assert lock.timeout == 30
        assert lock.retry_interval == 0.5

    # ========================================================================
    # Acquire Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_acquire_success_blocking(self, mock_get_cache):
        """Test successful lock acquisition in blocking mode."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        acquired = await lock.acquire(blocking=True)

        assert acquired is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_acquire_success_non_blocking(self, mock_get_cache):
        """Test successful lock acquisition in non-blocking mode."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        acquired = await lock.acquire(blocking=False)

        assert acquired is True

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_acquire_fail_non_blocking(self, mock_get_cache):
        """Test failed lock acquisition in non-blocking mode."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        acquired = await lock.acquire(blocking=False)

        assert acquired is False

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_acquire_with_timeout(self, mock_get_cache):
        """Test lock acquisition with timeout."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False  # Always fails
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock", retry_interval=0.01)
        acquired = await lock.acquire(blocking=True, timeout=0.05)

        assert acquired is False

    # ========================================================================
    # Release Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_release_success(self, mock_get_cache):
        """Test successful lock release."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1  # Success
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        released = await lock.release()

        assert released is True
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_release_not_owner(self, mock_get_cache):
        """Test releasing lock when not the owner."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 0  # Not owner
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        released = await lock.release()

        assert released is False

    # ========================================================================
    # Extend Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_extend_success(self, mock_get_cache):
        """Test successfully extending lock timeout."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1  # Success
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock", timeout=10)
        extended = await lock.extend(additional_time=5)

        assert extended is True
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_extend_not_owner(self, mock_get_cache):
        """Test extending lock when not the owner."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 0  # Not owner
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        extended = await lock.extend(additional_time=5)

        assert extended is False

    # ========================================================================
    # Status Check Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_is_locked_true(self, mock_get_cache):
        """Test checking if lock is held."""
        mock_cache = AsyncMock()
        mock_cache.exists.return_value = True
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        is_locked = await lock.is_locked()

        assert is_locked is True

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_get_owner(self, mock_get_cache):
        """Test getting lock owner identifier."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = "owner-123"
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")
        owner = await lock.get_owner()

        assert owner == "owner-123"

    # ========================================================================
    # Context Manager Tests
    # ========================================================================

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_context_manager_success(self, mock_get_cache):
        """Test using lock as context manager."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock")

        async with lock():
            # Lock should be held here
            pass

        # Lock should be released after context
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_context_manager_timeout_raises(self, mock_get_cache):
        """Test context manager raises TimeoutError when lock can't be acquired."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock = DistributedLock("test_lock", retry_interval=0.01)

        with pytest.raises(TimeoutError):
            async with lock(blocking=True, timeout=0.05):
                pass


class TestLockManager:
    """Test suite for LockManager."""

    def test_get_lock_creates_new(self):
        """Test getting a lock creates it if it doesn't exist."""
        manager = LockManager()

        lock = manager.get_lock("test_lock")

        assert isinstance(lock, DistributedLock)
        assert "test_lock" in manager.locks

    def test_get_lock_returns_existing(self):
        """Test getting a lock returns existing instance."""
        manager = LockManager()

        lock1 = manager.get_lock("test_lock")
        lock2 = manager.get_lock("test_lock")

        assert lock1 is lock2

    def test_get_lock_with_custom_params(self):
        """Test creating lock with custom parameters."""
        manager = LockManager()

        lock = manager.get_lock("test_lock", timeout=30, retry_interval=0.5)

        assert lock.timeout == 30
        assert lock.retry_interval == 0.5

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_lock_context_manager(self, mock_get_cache):
        """Test using lock manager's context manager."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.eval.return_value = 1
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        manager = LockManager()

        async with manager.lock("test_resource"):
            # Lock should be held
            pass

        # Lock should be released

    def test_get_lock_manager_singleton(self):
        """Test get_lock_manager returns singleton."""
        manager1 = get_lock_manager()
        manager2 = get_lock_manager()

        assert manager1 is manager2


class TestConcurrentLocking:
    """Test concurrent lock behavior."""

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_two_locks_on_same_resource(self, mock_get_cache):
        """Test that two locks on the same resource don't both acquire."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()

        # First call succeeds, second fails
        mock_redis.set.side_effect = [True, False]
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock1 = DistributedLock("resource")
        lock2 = DistributedLock("resource")

        acquired1 = await lock1.acquire(blocking=False)
        acquired2 = await lock2.acquire(blocking=False)

        assert acquired1 is True
        assert acquired2 is False

    @pytest.mark.asyncio
    @patch("app.cache.distributed_lock.get_cache_manager")
    async def test_locks_on_different_resources(self, mock_get_cache):
        """Test that locks on different resources can both acquire."""
        mock_cache = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_cache._redis = mock_redis
        mock_cache.connect = AsyncMock()
        mock_get_cache.return_value = mock_cache

        lock1 = DistributedLock("resource1")
        lock2 = DistributedLock("resource2")

        acquired1 = await lock1.acquire(blocking=False)
        acquired2 = await lock2.acquire(blocking=False)

        assert acquired1 is True
        assert acquired2 is True
