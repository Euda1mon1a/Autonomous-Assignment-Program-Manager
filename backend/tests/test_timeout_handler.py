"""Tests for timeout handler."""

import asyncio

import pytest

from app.timeout.handler import (
    TimeoutError,
    TimeoutHandler,
    get_timeout_elapsed,
    get_timeout_remaining,
    with_timeout_wrapper,
)


class TestTimeoutHandler:
    """Test suite for TimeoutHandler context manager."""

    async def test_timeout_handler_success(self):
        """Test successful operation within timeout."""
        async with TimeoutHandler(1.0) as handler:
            await asyncio.sleep(0.1)
            remaining = handler.get_remaining_time()

            assert remaining > 0
            assert remaining < 1.0

    async def test_timeout_handler_exceeds_timeout(self):
        """Test operation that exceeds timeout."""
        with pytest.raises(TimeoutError) as exc_info:
            async with TimeoutHandler(0.1):
                await asyncio.sleep(1.0)

        assert exc_info.value.timeout == 0.1
        assert "exceeded timeout" in str(exc_info.value).lower()

    async def test_timeout_handler_custom_message(self):
        """Test custom error message."""
        custom_msg = "Custom timeout message"

        with pytest.raises(TimeoutError) as exc_info:
            async with TimeoutHandler(0.1, error_message=custom_msg):
                await asyncio.sleep(1.0)

        assert exc_info.value.message == custom_msg

    async def test_get_remaining_time(self):
        """Test remaining time calculation."""
        async with TimeoutHandler(1.0) as handler:
            await asyncio.sleep(0.2)
            remaining = handler.get_remaining_time()

            # Should have around 0.8s remaining
            assert 0.7 < remaining < 0.9

    async def test_get_elapsed_time(self):
        """Test elapsed time calculation."""
        async with TimeoutHandler(1.0) as handler:
            await asyncio.sleep(0.2)
            elapsed = handler.get_elapsed_time()

            # Should have around 0.2s elapsed
            assert 0.15 < elapsed < 0.25

    async def test_check_timeout_within_limit(self):
        """Test check_timeout doesn't raise when within limit."""
        async with TimeoutHandler(1.0) as handler:
            await asyncio.sleep(0.1)
            # Should not raise
            handler.check_timeout()

    async def test_check_timeout_exceeded(self):
        """Test check_timeout raises when exceeded."""
        with pytest.raises(TimeoutError):
            async with TimeoutHandler(0.1) as handler:
                await asyncio.sleep(0.2)
                handler.check_timeout()

    async def test_nested_timeout_uses_minimum(self):
        """Test nested timeouts use the minimum value."""
        async with TimeoutHandler(2.0) as outer, TimeoutHandler(0.5) as inner:
            # Inner timeout should be 0.5s (minimum)
            assert inner.timeout == 0.5

    async def test_context_variables_set(self):
        """Test that context variables are set correctly."""
        async with TimeoutHandler(1.0):
            remaining = get_timeout_remaining()
            elapsed = get_timeout_elapsed()

            assert remaining is not None
            assert elapsed is not None
            assert remaining > 0
            assert elapsed >= 0

    async def test_context_variables_reset(self):
        """Test that context variables are reset after exit."""
        async with TimeoutHandler(1.0):
            pass

        # Context should be cleared
        remaining = get_timeout_remaining()
        elapsed = get_timeout_elapsed()

        assert remaining is None
        assert elapsed is None


class TestTimeoutWrapper:
    """Test suite for with_timeout_wrapper function."""

    async def test_wrapper_success(self):
        """Test successful wrapped operation."""

        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await with_timeout_wrapper(quick_operation(), 1.0)
        assert result == "success"

    async def test_wrapper_timeout(self):
        """Test wrapped operation timeout."""

        async def slow_operation():
            await asyncio.sleep(1.0)
            return "too late"

        with pytest.raises(TimeoutError) as exc_info:
            await with_timeout_wrapper(slow_operation(), 0.1)

        assert exc_info.value.timeout == 0.1

    async def test_wrapper_custom_message(self):
        """Test wrapper with custom error message."""

        async def slow_operation():
            await asyncio.sleep(1.0)

        custom_msg = "Operation took too long"

        with pytest.raises(TimeoutError) as exc_info:
            await with_timeout_wrapper(slow_operation(), 0.1, error_message=custom_msg)

        assert exc_info.value.message == custom_msg

    async def test_wrapper_cancellation(self):
        """Test wrapper handles task cancellation."""

        async def cancellable_operation():
            try:
                await asyncio.sleep(10.0)
            except asyncio.CancelledError:
                raise

        with pytest.raises(TimeoutError):
            await with_timeout_wrapper(cancellable_operation(), 0.1)


class TestTimeoutContext:
    """Test suite for timeout context variable functions."""

    async def test_no_timeout_set(self):
        """Test get functions return None when no timeout set."""
        assert get_timeout_remaining() is None
        assert get_timeout_elapsed() is None

    async def test_timeout_remaining_decreases(self):
        """Test timeout remaining decreases over time."""
        async with TimeoutHandler(1.0):
            first = get_timeout_remaining()
            await asyncio.sleep(0.1)
            second = get_timeout_remaining()

            assert second < first

    async def test_timeout_elapsed_increases(self):
        """Test timeout elapsed increases over time."""
        async with TimeoutHandler(1.0):
            first = get_timeout_elapsed()
            await asyncio.sleep(0.1)
            second = get_timeout_elapsed()

            assert second > first

    async def test_multiple_nested_contexts(self):
        """Test deeply nested timeout contexts."""
        async with TimeoutHandler(5.0):
            outer_remaining = get_timeout_remaining()

            async with TimeoutHandler(2.0):
                middle_remaining = get_timeout_remaining()

                async with TimeoutHandler(1.0):
                    inner_remaining = get_timeout_remaining()

                    # Should use innermost timeout
                    assert inner_remaining < middle_remaining
                    assert middle_remaining < outer_remaining
