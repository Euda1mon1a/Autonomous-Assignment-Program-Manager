"""
Tool execution engine with error handling and logging.

This module provides the execution layer for MCP tools.
"""

import logging
import time
from typing import Any

from .base import BaseTool, ToolError
from .registry import get_registry

logger = logging.getLogger(__name__)


class ExecutionContext:
    """
    Context for tool execution.

    Tracks execution metadata and timing.
    """

    def __init__(self, tool_name: str, request_id: str | None = None):
        """
        Initialize execution context.

        Args:
            tool_name: Name of tool being executed
            request_id: Optional request ID for tracking
        """
        self.tool_name = tool_name
        self.request_id = request_id or self._generate_request_id()
        self.start_time = time.time()
        self.end_time: float | None = None
        self.error: Exception | None = None

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        import uuid

        return str(uuid.uuid4())

    def complete(self, error: Exception | None = None) -> None:
        """
        Mark execution as complete.

        Args:
            error: Optional error that occurred
        """
        self.end_time = time.time()
        self.error = error

    @property
    def duration_ms(self) -> float:
        """
        Get execution duration in milliseconds.

        Returns:
            Duration in milliseconds
        """
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    @property
    def success(self) -> bool:
        """
        Check if execution was successful.

        Returns:
            True if no error occurred
        """
        return self.error is None


class ToolExecutor:
    """
    Executor for MCP tools.

    Provides execution with:
    - Error handling
    - Logging
    - Timing
    - Request tracking
    """

    def __init__(self) -> None:
        """Initialize the executor."""
        self.registry = get_registry()
        self._execution_count = 0
        self._error_count = 0

    async def execute(
        self, tool_name: str, request_id: str | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            request_id: Optional request ID for tracking
            **kwargs: Tool input parameters

        Returns:
            Tool response as dictionary

        Raises:
            ToolError: If tool not found or execution fails
        """
        # Get tool
        tool = self.registry.get(tool_name)
        if tool is None:
            raise ToolError(
                f"Tool '{tool_name}' not found",
                details={"tool": tool_name, "available": self.registry.list_tools()},
            )

        # Create execution context
        context = ExecutionContext(tool_name, request_id)

        try:
            # Execute tool
            logger.info(
                f"Executing tool: {tool_name}",
                extra={
                    "tool": tool_name,
                    "request_id": context.request_id,
                    "params": kwargs,
                },
            )

            result = await tool(**kwargs)

            # Mark success
            context.complete()
            self._execution_count += 1

            logger.info(
                f"Tool execution complete: {tool_name}",
                extra={
                    "tool": tool_name,
                    "request_id": context.request_id,
                    "duration_ms": context.duration_ms,
                    "success": True,
                },
            )

            return result

        except Exception as e:
            # Mark failure
            context.complete(error=e)
            self._error_count += 1

            logger.error(
                f"Tool execution failed: {tool_name}",
                extra={
                    "tool": tool_name,
                    "request_id": context.request_id,
                    "duration_ms": context.duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary with execution stats
        """
        return {
            "total_executions": self._execution_count,
            "total_errors": self._error_count,
            "error_rate": (
                self._error_count / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
            "registered_tools": self.registry.count(),
        }


# Global executor instance
_executor: ToolExecutor | None = None


def get_executor() -> ToolExecutor:
    """
    Get the global tool executor.

    Returns:
        Global ToolExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = ToolExecutor()
    return _executor
