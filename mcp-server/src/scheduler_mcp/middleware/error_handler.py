"""
Error handling middleware for MCP tools.

This module provides centralized error handling and formatting.
"""

import logging
from typing import Any, Callable

from ..tools.base import APIError, AuthenticationError, ToolError, ValidationError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """
    Standardized error response.
    """

    def __init__(
        self,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        tool: str | None = None,
    ):
        """
        Initialize error response.

        Args:
            error_type: Type of error
            message: Error message
            details: Optional error details
            tool: Optional tool name
        """
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.tool = tool

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Error as dictionary
        """
        result: dict[str, Any] = {
            "error": True,
            "error_type": self.error_type,
            "message": self.message,
        }

        if self.tool:
            result["tool"] = self.tool

        if self.details:
            result["details"] = self.details

        return result


class ErrorHandlerMiddleware:
    """
    Error handling middleware for MCP tools.

    Catches and formats errors consistently.
    """

    def __init__(self, enabled: bool = True, include_details: bool = True):
        """
        Initialize error handler middleware.

        Args:
            enabled: Whether error handling is enabled
            include_details: Whether to include error details
        """
        self.enabled = enabled
        self.include_details = include_details

    async def __call__(
        self, tool_name: str, next_handler: Callable[..., Any], **kwargs: Any
    ) -> Any:
        """
        Middleware handler.

        Args:
            tool_name: Name of tool being executed
            next_handler: Next handler in chain
            **kwargs: Tool parameters

        Returns:
            Result from next handler or error response
        """
        if not self.enabled:
            return await next_handler(**kwargs)

        try:
            return await next_handler(**kwargs)

        except ValidationError as e:
            logger.warning(
                f"Validation error in {tool_name}: {e}",
                extra={"tool": tool_name, "error": str(e)},
            )
            return self._format_error(
                error_type="ValidationError",
                message=str(e),
                details=e.details if self.include_details else {},
                tool=tool_name,
            )

        except AuthenticationError as e:
            logger.warning(
                f"Authentication error in {tool_name}: {e}",
                extra={"tool": tool_name, "error": str(e)},
            )
            return self._format_error(
                error_type="AuthenticationError",
                message=str(e),
                details=e.details if self.include_details else {},
                tool=tool_name,
            )

        except APIError as e:
            logger.error(
                f"API error in {tool_name}: {e}",
                extra={"tool": tool_name, "error": str(e)},
            )
            return self._format_error(
                error_type="APIError",
                message=str(e),
                details=e.details if self.include_details else {},
                tool=tool_name,
            )

        except ToolError as e:
            logger.error(
                f"Tool error in {tool_name}: {e}",
                extra={"tool": tool_name, "error": str(e)},
            )
            return self._format_error(
                error_type="ToolError",
                message=str(e),
                details=e.details if self.include_details else {},
                tool=tool_name,
            )

        except Exception as e:
            logger.exception(
                f"Unexpected error in {tool_name}",
                extra={"tool": tool_name, "error": str(e)},
            )
            return self._format_error(
                error_type="InternalError",
                message="An unexpected error occurred",
                details=(
                    {"type": type(e).__name__, "message": str(e)}
                    if self.include_details
                    else {}
                ),
                tool=tool_name,
            )

    def _format_error(
        self,
        error_type: str,
        message: str,
        details: dict[str, Any],
        tool: str,
    ) -> dict[str, Any]:
        """
        Format error as dictionary.

        Args:
            error_type: Type of error
            message: Error message
            details: Error details
            tool: Tool name

        Returns:
            Formatted error
        """
        response = ErrorResponse(
            error_type=error_type,
            message=message,
            details=details,
            tool=tool,
        )
        return response.to_dict()
