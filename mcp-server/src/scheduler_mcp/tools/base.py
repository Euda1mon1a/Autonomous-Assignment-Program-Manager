"""
Base tool class for MCP tools with validation and error handling.

This module provides the foundation for all MCP tools, including:
- Input validation
- Error handling
- Logging
- API client integration
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from ..api_client import SchedulerAPIClient

logger = logging.getLogger(__name__)

# Type variables for request and response
TRequest = TypeVar("TRequest", bound=BaseModel)
TResponse = TypeVar("TResponse", bound=BaseModel)


class ToolError(Exception):
    """Base exception for tool errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(ToolError):
    """Input validation error."""

    pass


class APIError(ToolError):
    """API communication error."""

    pass


class AuthenticationError(ToolError):
    """Authentication error."""

    pass


class BaseTool(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all MCP tools.

    Provides common functionality:
    - Input validation via Pydantic
    - Error handling and logging
    - API client access
    - Response formatting
    """

    def __init__(self, api_client: SchedulerAPIClient | None = None):
        """
        Initialize the tool.

        Args:
            api_client: Optional API client instance. If not provided,
                       tool must handle API calls differently.
        """
        self.api_client = api_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for registration."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for MCP."""
        pass

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """
        Execute the tool's main functionality.

        Args:
            request: Validated request object

        Returns:
            Response object

        Raises:
            ToolError: If execution fails
        """
        pass

    async def __call__(self, **kwargs: Any) -> dict[str, Any]:
        """
        Call the tool with keyword arguments.

        This is the main entry point from FastMCP.

        Args:
            **kwargs: Raw input parameters

        Returns:
            Response as dictionary

        Raises:
            ValidationError: If input validation fails
            ToolError: If execution fails
        """
        try:
            # Validate input
            request = self.validate_input(**kwargs)

            # Execute
            self.logger.info(
                f"Executing {self.name}",
                extra={"tool": self.name, "request": request.model_dump()},
            )
            response = await self.execute(request)

            # Return as dict
            return response.model_dump()

        except ValidationError as e:
            self.logger.error(
                f"Validation error in {self.name}: {e}",
                extra={"tool": self.name, "error": str(e)},
            )
            raise

        except ToolError as e:
            self.logger.error(
                f"Tool error in {self.name}: {e}",
                extra={"tool": self.name, "error": str(e), "details": e.details},
            )
            raise

        except Exception as e:
            self.logger.exception(
                f"Unexpected error in {self.name}",
                extra={"tool": self.name, "error": str(e)},
            )
            raise ToolError(
                f"Unexpected error in {self.name}: {e}",
                details={"type": type(e).__name__, "message": str(e)},
            )

    @abstractmethod
    def validate_input(self, **kwargs: Any) -> TRequest:
        """
        Validate and parse input parameters.

        Args:
            **kwargs: Raw input parameters

        Returns:
            Validated request object

        Raises:
            ValidationError: If validation fails
        """
        pass

    def _require_api_client(self) -> SchedulerAPIClient:
        """
        Get API client or raise error.

        Returns:
            API client instance

        Raises:
            ToolError: If API client not configured
        """
        if self.api_client is None:
            raise ToolError(
                f"{self.name} requires API client but none configured",
                details={"tool": self.name},
            )
        return self.api_client
