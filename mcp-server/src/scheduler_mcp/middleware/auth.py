"""
Authentication middleware for MCP tools.

This module provides authentication checking for tool execution.
"""

import logging
import os
from typing import Any, Callable

from ..tools.base import AuthenticationError

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """
    Authentication middleware for MCP tools.

    Validates API credentials before tool execution.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize auth middleware.

        Args:
            enabled: Whether authentication is enabled
        """
        self.enabled = enabled
        self._api_username = os.environ.get("API_USERNAME", "")
        self._api_password = os.environ.get("API_PASSWORD", "")

        if self.enabled and (not self._api_username or not self._api_password):
            logger.warning(
                "Auth enabled but credentials not configured. "
                "Set API_USERNAME and API_PASSWORD environment variables."
            )

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

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.enabled:
            return await next_handler(**kwargs)

        # Check if credentials are configured
        if not self._api_username or not self._api_password:
            raise AuthenticationError(
                "API credentials not configured",
                details={"tool": tool_name},
            )

        # In a real implementation, this would validate tokens
        # For now, we just check that credentials exist
        logger.debug(
            f"Auth check passed for {tool_name}",
            extra={"tool": tool_name, "username": self._api_username},
        )

        return await next_handler(**kwargs)

    def is_enabled(self) -> bool:
        """
        Check if authentication is enabled.

        Returns:
            True if enabled
        """
        return self.enabled

    def has_credentials(self) -> bool:
        """
        Check if credentials are configured.

        Returns:
            True if credentials are set
        """
        return bool(self._api_username and self._api_password)
