"""Tests for distributed locking for schedule generation."""

from unittest.mock import MagicMock, patch

import pytest

from app.scheduling.locking import (
    DEFAULT_LOCK_ACQUISITION_TIMEOUT,
    INITIAL_RETRY_DELAY_SECONDS,
    LOCK_TIMEOUT_SECONDS,
    MAX_RETRY_DELAY_SECONDS,
    LockAcquisitionError,
    ScheduleGenerationLock,
)


# ==================== Constants ====================


class TestConstants:
    def test_lock_timeout(self):
        assert LOCK_TIMEOUT_SECONDS == 600

    def test_default_acquisition_timeout(self):
        assert DEFAULT_LOCK_ACQUISITION_TIMEOUT == 30

    def test_initial_retry_delay(self):
        assert INITIAL_RETRY_DELAY_SECONDS == 0.1

    def test_max_retry_delay(self):
        assert MAX_RETRY_DELAY_SECONDS == 2.0

    def test_timeout_ordering(self):
        assert INITIAL_RETRY_DELAY_SECONDS < MAX_RETRY_DELAY_SECONDS


# ==================== LockAcquisitionError ====================


class TestLockAcquisitionError:
    def test_is_exception(self):
        assert issubclass(LockAcquisitionError, Exception)

    def test_message(self):
        e = LockAcquisitionError("Lock failed")
        assert str(e) == "Lock failed"

    def test_can_be_raised(self):
        with pytest.raises(LockAcquisitionError, match="test"):
            raise LockAcquisitionError("test")


# ==================== ScheduleGenerationLock init ====================


def _mock_redis():
    """Create a mock Redis client with register_script."""
    client = MagicMock()
    client.register_script = MagicMock(return_value=MagicMock())
    return client


class TestScheduleGenerationLockInit:
    def test_custom_redis_client(self):
        client = _mock_redis()
        lock = ScheduleGenerationLock(redis_client=client)
        assert lock.redis is client

    def test_lock_timeout_set(self):
        client = _mock_redis()
        lock = ScheduleGenerationLock(redis_client=client)
        assert lock.lock_timeout == LOCK_TIMEOUT_SECONDS

    def test_release_script_registered(self):
        client = _mock_redis()
        ScheduleGenerationLock(redis_client=client)
        client.register_script.assert_called_once()

    def test_release_script_content(self):
        """The Lua script checks key ownership before deleting."""
        assert "get" in ScheduleGenerationLock.RELEASE_SCRIPT
        assert "del" in ScheduleGenerationLock.RELEASE_SCRIPT


# ==================== acquire context manager ====================


class TestAcquireContextManager:
    def test_acquire_success(self):
        """Lock acquired on first attempt, context entered and exited."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        lock = ScheduleGenerationLock(redis_client=client)

        with lock.acquire(year_id="2024"):
            pass  # Just verify we enter the context

        # Lock should have been set with nx=True and ex=timeout
        client.set.assert_called_once()
        call_kwargs = client.set.call_args[1]
        assert call_kwargs["nx"] is True
        assert call_kwargs["ex"] == LOCK_TIMEOUT_SECONDS

    def test_acquire_key_format(self):
        """Lock key includes year_id."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        lock = ScheduleGenerationLock(redis_client=client)

        with lock.acquire(year_id="2024"):
            pass

        call_args = client.set.call_args[0]
        assert call_args[0] == "lock:schedule_generation:2024"

    def test_acquire_releases_on_exit(self):
        """Lock is released after context exits."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        release_script = MagicMock(return_value=1)
        client.register_script = MagicMock(return_value=release_script)
        lock = ScheduleGenerationLock(redis_client=client)

        with lock.acquire(year_id="2024"):
            pass

        release_script.assert_called_once()

    def test_acquire_releases_on_exception(self):
        """Lock is released even if code in context raises."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        release_script = MagicMock(return_value=1)
        client.register_script = MagicMock(return_value=release_script)
        lock = ScheduleGenerationLock(redis_client=client)

        with pytest.raises(ValueError, match="boom"):
            with lock.acquire(year_id="2024"):
                raise ValueError("boom")

        release_script.assert_called_once()

    @patch("app.scheduling.locking.time")
    def test_acquire_timeout(self, mock_time):
        """LockAcquisitionError raised when timeout expires."""
        client = _mock_redis()
        client.set = MagicMock(return_value=False)  # Never acquired
        lock = ScheduleGenerationLock(redis_client=client)

        # Simulate time passing beyond timeout
        mock_time.time = MagicMock(side_effect=[0, 0, 31])
        mock_time.sleep = MagicMock()

        with pytest.raises(LockAcquisitionError, match="Could not acquire lock"):
            with lock.acquire(year_id="2024", timeout=30):
                pass

    def test_acquire_custom_timeout(self):
        """Custom timeout passed to acquire."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        lock = ScheduleGenerationLock(redis_client=client)

        with lock.acquire(year_id="2024", timeout=60):
            pass


# ==================== _try_acquire ====================


class TestTryAcquire:
    def test_immediate_success(self):
        """Lock acquired on first attempt returns True."""
        client = _mock_redis()
        client.set = MagicMock(return_value=True)
        lock = ScheduleGenerationLock(redis_client=client)

        result = lock._try_acquire("key", "value", timeout=30)
        assert result is True
        assert client.set.call_count == 1

    @patch("app.scheduling.locking.time")
    def test_retry_then_success(self, mock_time):
        """Lock acquired after retries."""
        client = _mock_redis()
        # Fail first, succeed second
        client.set = MagicMock(side_effect=[False, True])
        lock = ScheduleGenerationLock(redis_client=client)

        mock_time.time = MagicMock(side_effect=[0, 0.1])
        mock_time.sleep = MagicMock()

        result = lock._try_acquire("key", "value", timeout=30)
        assert result is True
        assert client.set.call_count == 2

    @patch("app.scheduling.locking.time")
    def test_timeout_returns_false(self, mock_time):
        """Returns False when timeout expires."""
        client = _mock_redis()
        client.set = MagicMock(return_value=False)
        lock = ScheduleGenerationLock(redis_client=client)

        mock_time.time = MagicMock(side_effect=[0, 31])
        mock_time.sleep = MagicMock()

        result = lock._try_acquire("key", "value", timeout=30)
        assert result is False


# ==================== _release ====================


class TestRelease:
    def test_release_success(self):
        """Release returns True when we own the lock."""
        client = _mock_redis()
        release_script = MagicMock(return_value=1)
        client.register_script = MagicMock(return_value=release_script)
        lock = ScheduleGenerationLock(redis_client=client)

        result = lock._release("key", "value")
        assert result is True

    def test_release_not_owner(self):
        """Release returns False when we don't own the lock."""
        client = _mock_redis()
        release_script = MagicMock(return_value=0)
        client.register_script = MagicMock(return_value=release_script)
        lock = ScheduleGenerationLock(redis_client=client)

        result = lock._release("key", "value")
        assert result is False

    def test_release_redis_error(self):
        """Release returns False on RedisError."""
        import redis as redis_lib

        client = _mock_redis()
        release_script = MagicMock(side_effect=redis_lib.RedisError("down"))
        client.register_script = MagicMock(return_value=release_script)
        lock = ScheduleGenerationLock(redis_client=client)

        result = lock._release("key", "value")
        assert result is False


# ==================== is_locked ====================


class TestIsLocked:
    def test_locked(self):
        client = _mock_redis()
        client.exists = MagicMock(return_value=1)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.is_locked("2024") is True
        client.exists.assert_called_with("lock:schedule_generation:2024")

    def test_not_locked(self):
        client = _mock_redis()
        client.exists = MagicMock(return_value=0)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.is_locked("2024") is False

    def test_redis_error_returns_false(self):
        """On Redis failure, assume not locked (degraded mode)."""
        import redis as redis_lib

        client = _mock_redis()
        client.exists = MagicMock(side_effect=redis_lib.RedisError("down"))
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.is_locked("2024") is False


# ==================== get_lock_ttl ====================


class TestGetLockTtl:
    def test_positive_ttl(self):
        client = _mock_redis()
        client.ttl = MagicMock(return_value=300)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.get_lock_ttl("2024") == 300

    def test_no_key_returns_none(self):
        """TTL returns -2 when key doesn't exist."""
        client = _mock_redis()
        client.ttl = MagicMock(return_value=-2)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.get_lock_ttl("2024") is None

    def test_no_expiry_returns_none(self):
        """TTL returns -1 when key has no expiry."""
        client = _mock_redis()
        client.ttl = MagicMock(return_value=-1)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.get_lock_ttl("2024") is None

    def test_redis_error_returns_none(self):
        import redis as redis_lib

        client = _mock_redis()
        client.ttl = MagicMock(side_effect=redis_lib.RedisError("down"))
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.get_lock_ttl("2024") is None

    def test_key_format(self):
        client = _mock_redis()
        client.ttl = MagicMock(return_value=100)
        lock = ScheduleGenerationLock(redis_client=client)

        lock.get_lock_ttl("2025")
        client.ttl.assert_called_with("lock:schedule_generation:2025")


# ==================== force_release ====================


class TestForceRelease:
    def test_success(self):
        client = _mock_redis()
        client.delete = MagicMock(return_value=1)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.force_release("2024") is True
        client.delete.assert_called_with("lock:schedule_generation:2024")

    def test_no_lock_exists(self):
        client = _mock_redis()
        client.delete = MagicMock(return_value=0)
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.force_release("2024") is False

    def test_redis_error(self):
        import redis as redis_lib

        client = _mock_redis()
        client.delete = MagicMock(side_effect=redis_lib.RedisError("down"))
        lock = ScheduleGenerationLock(redis_client=client)

        assert lock.force_release("2024") is False
