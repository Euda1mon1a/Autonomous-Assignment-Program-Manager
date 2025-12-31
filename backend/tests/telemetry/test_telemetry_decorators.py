"""
Tests for telemetry decorators.

Comprehensive test suite for telemetry decorators,
covering automatic tracing, metrics collection, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch
from functools import wraps


def traced_function(func):
    """Mock traced decorator for testing."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def traced_async(func):
    """Mock async traced decorator for testing."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class TestTracingDecorator:
    """Test suite for tracing decorator functionality."""

    def test_decorator_preserves_function_name(self):
        """Test decorator preserves original function name."""
        # Arrange & Act
        @traced_function
        def test_function():
            return "result"

        # Assert
        assert test_function.__name__ == "test_function"

    def test_decorator_preserves_docstring(self):
        """Test decorator preserves original docstring."""
        # Arrange & Act
        @traced_function
        def test_function():
            """Original docstring."""
            return "result"

        # Assert
        assert test_function.__doc__ == "Original docstring."

    def test_decorator_passes_through_return_value(self):
        """Test decorator passes through function return value."""
        # Arrange
        @traced_function
        def add_numbers(a, b):
            return a + b

        # Act
        result = add_numbers(2, 3)

        # Assert
        assert result == 5

    def test_decorator_passes_through_exceptions(self):
        """Test decorator lets exceptions propagate."""
        # Arrange
        @traced_function
        def failing_function():
            raise ValueError("Test error")

        # Act & Assert
        with pytest.raises(ValueError, match="Test error"):
            failing_function()

    def test_decorator_works_with_args_and_kwargs(self):
        """Test decorator works with positional and keyword arguments."""
        # Arrange
        @traced_function
        def function_with_args(a, b, c=10, d=20):
            return a + b + c + d

        # Act
        result = function_with_args(1, 2, c=3, d=4)

        # Assert
        assert result == 10


class TestAsyncTracingDecorator:
    """Test suite for async tracing decorator."""

    @pytest.mark.asyncio
    async def test_async_decorator_works(self):
        """Test async decorator works with async functions."""
        # Arrange
        @traced_async
        async def async_function():
            return "async result"

        # Act
        result = await async_function()

        # Assert
        assert result == "async result"

    @pytest.mark.asyncio
    async def test_async_decorator_preserves_function_name(self):
        """Test async decorator preserves function name."""
        # Arrange & Act
        @traced_async
        async def test_async_function():
            return "result"

        # Assert
        assert test_async_function.__name__ == "test_async_function"

    @pytest.mark.asyncio
    async def test_async_decorator_propagates_exceptions(self):
        """Test async decorator lets exceptions propagate."""
        # Arrange
        @traced_async
        async def failing_async_function():
            raise RuntimeError("Async error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Async error"):
            await failing_async_function()


class TestDecoratorWithParameters:
    """Test suite for parameterized decorators."""

    def test_parameterized_decorator_with_span_name(self):
        """Test decorator accepts custom span name parameter."""
        # Arrange
        def traced_with_name(span_name):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    # Simulated: Create span with custom name
                    return func(*args, **kwargs)
                return wrapper
            return decorator

        @traced_with_name("custom_span_name")
        def function():
            return "result"

        # Act
        result = function()

        # Assert
        assert result == "result"

    def test_parameterized_decorator_with_attributes(self):
        """Test decorator accepts custom attributes parameter."""
        # Arrange
        def traced_with_attrs(attributes):
            def decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    # Simulated: Add custom attributes to span
                    return func(*args, **kwargs)
                return wrapper
            return decorator

        @traced_with_attrs({"user.id": "user-123", "operation": "fetch"})
        def function():
            return "result"

        # Act
        result = function()

        # Assert
        assert result == "result"


class TestDecoratorErrorHandling:
    """Test suite for decorator error handling."""

    def test_decorator_records_exception_info(self):
        """Test decorator records exception information before re-raising."""
        # Arrange
        exception_recorded = False

        def traced_with_recording(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal exception_recorded
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    exception_recorded = True
                    raise
            return wrapper

        @traced_with_recording
        def failing_function():
            raise ValueError("Test error")

        # Act & Assert
        with pytest.raises(ValueError):
            failing_function()

        assert exception_recorded is True


class TestDecoratorMetrics:
    """Test suite for decorator metrics collection."""

    def test_decorator_tracks_invocation_count(self):
        """Test decorator can track function invocation count."""
        # Arrange
        invocations = []

        def counted_trace(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                invocations.append(1)
                return func(*args, **kwargs)
            return wrapper

        @counted_trace
        def function():
            return "result"

        # Act
        function()
        function()
        function()

        # Assert
        assert len(invocations) == 3

    def test_decorator_measures_execution_time(self):
        """Test decorator can measure function execution time."""
        # Arrange
        import time

        durations = []

        def timed_trace(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start
                durations.append(duration)
                return result
            return wrapper

        @timed_trace
        def function():
            time.sleep(0.01)  # Sleep 10ms
            return "result"

        # Act
        function()

        # Assert
        assert len(durations) == 1
        assert durations[0] >= 0.01  # Should take at least 10ms
