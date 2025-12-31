"""
Logging middleware for MCP tools.

This module provides request/response logging.
"""

import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Logging middleware for MCP tools.

    Logs all tool executions with timing and parameters.
    """

    def __init__(self, enabled: bool = True, log_params: bool = True):
        """
        Initialize logging middleware.

        Args:
            enabled: Whether logging is enabled
            log_params: Whether to log input parameters
        """
        self.enabled = enabled
        self.log_params = log_params

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
            Result from next handler
        """
        if not self.enabled:
            return await next_handler(**kwargs)

        start_time = time.time()

        # Log request
        log_extra = {"tool": tool_name, "timestamp": start_time}
        if self.log_params:
            # Sanitize params for logging
            safe_params = self._sanitize_params(kwargs)
            log_extra["params"] = safe_params

        logger.info(f"Tool request: {tool_name}", extra=log_extra)

        try:
            # Execute
            result = await next_handler(**kwargs)

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Tool success: {tool_name}",
                extra={
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "success": True,
                },
            )

            return result

        except Exception as e:
            # Log failure
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Tool error: {tool_name}",
                extra={
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            raise

    def _sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize parameters for logging.

        Removes sensitive data.

        Args:
            params: Raw parameters

        Returns:
            Sanitized parameters
        """
        safe_params = {}

        # List of sensitive parameter names
        sensitive_keys = {
            "password",
            "token",
            "secret",
            "api_key",
            "authorization",
        }

        for key, value in params.items():
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_params[key] = "[REDACTED]"
            elif isinstance(value, dict):
                safe_params[key] = self._sanitize_params(value)
            elif isinstance(value, str) and len(value) > 1000:
                # Truncate very long strings
                safe_params[key] = value[:1000] + "... [TRUNCATED]"
            else:
                safe_params[key] = value

        return safe_params
