"""
Integration tests for MCP tools.

Tests tool registration, execution, and middleware integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from scheduler_mcp.middleware import (
    AuthMiddleware,
    ErrorHandlerMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from scheduler_mcp.tools.base import BaseTool
from scheduler_mcp.tools.executor import ToolExecutor
from scheduler_mcp.tools.registry import ToolRegistry


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()

        # Create mock tool
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "test_tool"

        # Register
        registry.register(mock_tool, category="schedule")

        # Assert
        assert registry.count() == 1
        assert "test_tool" in registry.list_tools()
        assert registry.get("test_tool") == mock_tool

    def test_register_duplicate(self):
        """Test registering duplicate tool raises error."""
        registry = ToolRegistry()

        # Create mock tools
        mock_tool1 = MagicMock(spec=BaseTool)
        mock_tool1.name = "test_tool"

        mock_tool2 = MagicMock(spec=BaseTool)
        mock_tool2.name = "test_tool"

        # Register first
        registry.register(mock_tool1)

        # Register duplicate should raise
        with pytest.raises(ValueError):
            registry.register(mock_tool2)

    def test_list_by_category(self):
        """Test listing tools by category."""
        registry = ToolRegistry()

        # Create mock tools
        schedule_tool = MagicMock(spec=BaseTool)
        schedule_tool.name = "schedule_tool"

        compliance_tool = MagicMock(spec=BaseTool)
        compliance_tool.name = "compliance_tool"

        # Register
        registry.register(schedule_tool, category="schedule")
        registry.register(compliance_tool, category="compliance")

        # Assert
        assert len(registry.list_tools(category="schedule")) == 1
        assert len(registry.list_tools(category="compliance")) == 1
        assert len(registry.list_tools()) == 2


class TestToolExecutor:
    """Tests for ToolExecutor."""

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test tool execution."""
        executor = ToolExecutor()

        # Create mock tool
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "test_tool"
        mock_tool.__call__ = AsyncMock(return_value={"result": "success"})

        # Register
        executor.registry.register(mock_tool)

        # Execute
        result = await executor.execute("test_tool", param="value")

        # Assert
        assert result["result"] == "success"
        mock_tool.__call__.assert_called_once_with(param="value")

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing non-existent tool raises error."""
        executor = ToolExecutor()

        with pytest.raises(Exception):
            await executor.execute("nonexistent_tool")

    def test_get_stats(self):
        """Test execution statistics."""
        executor = ToolExecutor()

        stats = executor.get_stats()

        assert "total_executions" in stats
        assert "total_errors" in stats
        assert "error_rate" in stats
        assert "registered_tools" in stats


class TestMiddleware:
    """Tests for middleware components."""

    @pytest.mark.asyncio
    async def test_auth_middleware_enabled(self):
        """Test auth middleware when enabled."""
        middleware = AuthMiddleware(enabled=True)

        # Mock next handler
        next_handler = AsyncMock(return_value="result")

        # Execute (should fail without credentials)
        with pytest.raises(Exception):
            await middleware("test_tool", next_handler, param="value")

    @pytest.mark.asyncio
    async def test_auth_middleware_disabled(self):
        """Test auth middleware when disabled."""
        middleware = AuthMiddleware(enabled=False)

        # Mock next handler
        next_handler = AsyncMock(return_value="result")

        # Execute
        result = await middleware("test_tool", next_handler, param="value")

        # Assert
        assert result == "result"
        next_handler.assert_called_once_with(param="value")

    @pytest.mark.asyncio
    async def test_rate_limit_middleware(self):
        """Test rate limit middleware."""
        middleware = RateLimitMiddleware(enabled=True, rate=10, burst=2)

        # Mock next handler
        next_handler = AsyncMock(return_value="result")

        # Execute within rate limit
        result1 = await middleware("test_tool", next_handler)
        result2 = await middleware("test_tool", next_handler)

        # Assert both succeed
        assert result1 == "result"
        assert result2 == "result"

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Test logging middleware."""
        middleware = LoggingMiddleware(enabled=True, log_params=True)

        # Mock next handler
        next_handler = AsyncMock(return_value="result")

        # Execute
        result = await middleware("test_tool", next_handler, param="value")

        # Assert
        assert result == "result"
        next_handler.assert_called_once_with(param="value")

    @pytest.mark.asyncio
    async def test_error_handler_middleware(self):
        """Test error handler middleware."""
        middleware = ErrorHandlerMiddleware(enabled=True, include_details=True)

        # Mock next handler that raises error
        next_handler = AsyncMock(side_effect=ValueError("Test error"))

        # Execute
        result = await middleware("test_tool", next_handler)

        # Assert error response
        assert result["error"] is True
        assert "error_type" in result
        assert "message" in result
