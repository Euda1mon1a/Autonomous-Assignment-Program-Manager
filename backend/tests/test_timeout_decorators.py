"""Tests for timeout decorators."""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.timeout.decorators import db_timeout, timeout_remaining, with_timeout
from app.timeout.handler import TimeoutError, TimeoutHandler


class TestWithTimeoutDecorator:
    """Test suite for @with_timeout decorator."""

    async def test_decorator_success(self):
        """Test decorated function completes successfully."""

        @with_timeout(1.0)
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await quick_operation()
        assert result == "success"

    async def test_decorator_timeout(self):
        """Test decorated function times out."""

        @with_timeout(0.1)
        async def slow_operation():
            await asyncio.sleep(1.0)
            return "too late"

        with pytest.raises(TimeoutError) as exc_info:
            await slow_operation()

        assert exc_info.value.timeout == 0.1

    async def test_decorator_custom_message(self):
        """Test decorator with custom error message."""
        custom_msg = "Operation took too long"

        @with_timeout(0.1, error_message=custom_msg)
        async def slow_operation():
            await asyncio.sleep(1.0)

        with pytest.raises(TimeoutError) as exc_info:
            await slow_operation()

        assert exc_info.value.message == custom_msg

    async def test_decorator_with_args(self):
        """Test decorator on function with arguments."""

        @with_timeout(1.0)
        async def operation_with_args(x, y):
            await asyncio.sleep(0.1)
            return x + y

        result = await operation_with_args(5, 3)
        assert result == 8

    async def test_decorator_with_kwargs(self):
        """Test decorator on function with keyword arguments."""

        @with_timeout(1.0)
        async def operation_with_kwargs(a=1, b=2):
            await asyncio.sleep(0.1)
            return a * b

        result = await operation_with_kwargs(a=3, b=4)
        assert result == 12

    async def test_decorator_respects_existing_timeout(self):
        """Test decorator respects existing timeout from context."""

        @with_timeout(5.0)
        async def long_timeout_operation():
            await asyncio.sleep(0.5)
            return "success"

        # Context has shorter timeout, should use that
        with pytest.raises(TimeoutError):
            async with TimeoutHandler(0.1):
                await long_timeout_operation()

    async def test_decorator_uses_minimum_timeout(self):
        """Test decorator uses minimum of decorator and context timeout."""

        @with_timeout(0.5)
        async def operation():
            await asyncio.sleep(1.0)

        # Context has longer timeout, should use decorator's shorter timeout
        with pytest.raises(TimeoutError) as exc_info:
            async with TimeoutHandler(2.0):
                await operation()

        # Should timeout around 0.5s (decorator timeout)
        assert exc_info.value.timeout <= 0.5


class TestTimeoutRemainingDecorator:
    """Test suite for @timeout_remaining decorator."""

    async def test_decorator_with_time_remaining(self):
        """Test decorator allows execution when time remains."""

        @timeout_remaining
        async def operation():
            return "success"

        async with TimeoutHandler(1.0):
            result = await operation()
            assert result == "success"

    async def test_decorator_no_time_remaining(self):
        """Test decorator raises when no time remaining."""

        @timeout_remaining
        async def operation():
            return "should not execute"

        with pytest.raises(TimeoutError):
            async with TimeoutHandler(0.1):
                await asyncio.sleep(0.2)
                await operation()

    async def test_decorator_without_timeout_context(self):
        """Test decorator works when no timeout context exists."""

        @timeout_remaining
        async def operation():
            return "success"

        # Should work fine without timeout context
        result = await operation()
        assert result == "success"


class TestDbTimeoutDecorator:
    """Test suite for @db_timeout decorator."""

    async def test_db_timeout_async_success(self, db: Session):
        """Test async database operation completes within timeout."""

        @db_timeout(5.0)
        async def quick_query(db_session: Session):
            result = db_session.execute(text("SELECT 1"))
            return result.scalar()

        result = await quick_query(db)
        assert result == 1

    async def test_db_timeout_async_exceeded(self, db: Session):
        """Test async database operation timeout."""

        @db_timeout(0.1)
        async def slow_query(db_session: Session):
            # pg_sleep sleeps for specified seconds
            db_session.execute(text("SELECT pg_sleep(5)"))

        with pytest.raises(TimeoutError) as exc_info:
            await slow_query(db)

        assert "database query" in str(exc_info.value).lower()

    def test_db_timeout_sync_success(self, db: Session):
        """Test sync database operation completes within timeout."""

        @db_timeout(5.0)
        def quick_query(db_session: Session):
            result = db_session.execute(text("SELECT 1"))
            return result.scalar()

        result = quick_query(db)
        assert result == 1

    def test_db_timeout_sync_exceeded(self, db: Session):
        """Test sync database operation timeout."""

        @db_timeout(0.1)
        def slow_query(db_session: Session):
            db_session.execute(text("SELECT pg_sleep(5)"))

        with pytest.raises(TimeoutError) as exc_info:
            slow_query(db)

        assert "database query" in str(exc_info.value).lower()

    async def test_db_timeout_no_session(self):
        """Test decorator with no database session."""

        @db_timeout(1.0)
        async def no_db_operation():
            await asyncio.sleep(0.1)
            return "success"

        # Should work but log warning about no session
        result = await no_db_operation()
        assert result == "success"

    async def test_db_timeout_session_in_kwargs(self, db: Session):
        """Test decorator finds session in kwargs."""

        @db_timeout(5.0)
        async def query_with_kwargs(*, db: Session):
            result = db.execute(text("SELECT 1"))
            return result.scalar()

        result = await query_with_kwargs(db=db)
        assert result == 1

    async def test_db_timeout_resets_on_success(self, db: Session):
        """Test timeout is reset after successful query."""

        @db_timeout(5.0)
        async def query_with_timeout(db_session: Session):
            db_session.execute(text("SELECT 1"))

        await query_with_timeout(db)

        # Timeout should be reset - subsequent queries should work
        result = db.execute(text("SELECT 2"))
        assert result.scalar() == 2

    async def test_db_timeout_resets_on_error(self, db: Session):
        """Test timeout is reset even on error."""

        @db_timeout(5.0)
        async def failing_query(db_session: Session):
            # Invalid SQL to trigger error
            db_session.execute(text("SELECT invalid_function()"))

        with pytest.raises(Exception):
            await failing_query(db)

        # Timeout should be reset - subsequent queries should work
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.fixture
def db():
    """
    Mock database session for testing.

    In a real test suite, this would be replaced with an actual
    database fixture from conftest.py.
    """
    from unittest.mock import MagicMock

    mock_db = MagicMock(spec=Session)

    # Mock execute to return a result
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_db.execute.return_value = mock_result

    return mock_db
