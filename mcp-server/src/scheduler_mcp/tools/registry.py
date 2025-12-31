"""
Tool registry for MCP tools.

This module manages tool registration and discovery.
"""

import logging
from typing import Any

from .base import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for MCP tools.

    Manages tool registration, discovery, and retrieval.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._tools: dict[str, BaseTool[Any, Any]] = {}
        self._categories: dict[str, list[str]] = {
            "schedule": [],
            "compliance": [],
            "swap": [],
            "resilience": [],
            "analytics": [],
            "system": [],
        }

    def register(
        self, tool: BaseTool[Any, Any], category: str = "system"
    ) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
            category: Tool category (schedule, compliance, swap, etc.)

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")

        if category not in self._categories:
            logger.warning(
                f"Unknown category '{category}', adding to system category",
                extra={"tool": tool.name, "category": category},
            )
            category = "system"

        self._tools[tool.name] = tool
        self._categories[category].append(tool.name)

        logger.info(
            f"Registered tool: {tool.name}",
            extra={"tool": tool.name, "category": category},
        )

    def get(self, name: str) -> BaseTool[Any, Any] | None:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[str]:
        """
        List all tool names, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category is None:
            return list(self._tools.keys())

        return self._categories.get(category, [])

    def list_categories(self) -> list[str]:
        """
        List all categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_tools_by_category(self, category: str) -> list[BaseTool[Any, Any]]:
        """
        Get all tools in a category.

        Args:
            category: Category name

        Returns:
            List of tool instances
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names]

    def count(self) -> int:
        """
        Get total number of registered tools.

        Returns:
            Number of tools
        """
        return len(self._tools)

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            return False

        # Remove from tools
        del self._tools[name]

        # Remove from all categories
        for category_tools in self._categories.values():
            if name in category_tools:
                category_tools.remove(name)

        logger.info(f"Unregistered tool: {name}", extra={"tool": name})
        return True


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry.

    Returns:
        Global ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
