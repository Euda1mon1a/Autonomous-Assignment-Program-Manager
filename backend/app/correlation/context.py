"""
Correlation context management for request tracking.

Provides async-safe context management for:
- Correlation IDs (X-Correlation-ID)
- Request IDs (X-Request-ID)
- Parent request tracking for request chains
- User context propagation
- Service-to-service call tracking
"""

import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Context variables for async-safe storage
_correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_parent_id_var: ContextVar[Optional[str]] = ContextVar("parent_id", default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_request_depth_var: ContextVar[int] = ContextVar("request_depth", default=0)
_request_chain_var: ContextVar[list[str]] = ContextVar("request_chain", default=[])


@dataclass
class CorrelationContext:
    """
    Correlation context for a request.

    Attributes:
        correlation_id: Unique ID for the entire request chain (persists across services)
        request_id: Unique ID for this specific request
        parent_id: ID of the parent request (for nested calls)
        user_id: ID of the authenticated user (if any)
        depth: Depth in the request chain (0 for root request)
        chain: List of request IDs in the chain from root to current
        timestamp: When this context was created
    """

    correlation_id: str
    request_id: str
    parent_id: Optional[str] = None
    user_id: Optional[str] = None
    depth: int = 0
    chain: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """
        Convert context to dictionary for logging/serialization.

        Returns:
            dict: Context as dictionary
        """
        return {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "parent_id": self.parent_id,
            "user_id": self.user_id,
            "depth": self.depth,
            "chain_length": len(self.chain),
            "timestamp": self.timestamp.isoformat(),
        }

    def to_headers(self) -> dict[str, str]:
        """
        Convert context to HTTP headers for propagation.

        Returns:
            dict: Headers for outgoing requests
        """
        headers = {
            "X-Correlation-ID": self.correlation_id,
            "X-Request-ID": self.request_id,
            "X-Request-Depth": str(self.depth),
        }

        if self.parent_id:
            headers["X-Parent-ID"] = self.parent_id

        if self.user_id:
            headers["X-User-ID"] = self.user_id

        return headers


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.

    Returns:
        str: UUID-based correlation ID
    """
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """
    Generate a new request ID.

    Returns:
        str: UUID-based request ID
    """
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Optional[str]: Correlation ID or None if not set
    """
    return _correlation_id_var.get()


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        Optional[str]: Request ID or None if not set
    """
    return _request_id_var.get()


def get_parent_id() -> Optional[str]:
    """
    Get the parent request ID from context.

    Returns:
        Optional[str]: Parent request ID or None if not set
    """
    return _parent_id_var.get()


def get_user_id() -> Optional[str]:
    """
    Get the current user ID from context.

    Returns:
        Optional[str]: User ID or None if not set
    """
    return _user_id_var.get()


def get_request_depth() -> int:
    """
    Get the current request depth.

    Returns:
        int: Request depth (0 for root request)
    """
    return _request_depth_var.get()


def get_request_chain() -> list[str]:
    """
    Get the request chain (list of request IDs from root to current).

    Returns:
        list[str]: Request chain
    """
    return _request_chain_var.get()


def get_context() -> Optional[CorrelationContext]:
    """
    Get the current correlation context.

    Returns:
        Optional[CorrelationContext]: Current context or None if not set
    """
    correlation_id = get_correlation_id()
    request_id = get_request_id()

    if not correlation_id or not request_id:
        return None

    return CorrelationContext(
        correlation_id=correlation_id,
        request_id=request_id,
        parent_id=get_parent_id(),
        user_id=get_user_id(),
        depth=get_request_depth(),
        chain=get_request_chain(),
    )


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in context.

    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id_var.set(correlation_id)


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in context.

    Args:
        request_id: Request ID to set
    """
    _request_id_var.set(request_id)


def set_parent_id(parent_id: Optional[str]) -> None:
    """
    Set the parent request ID in context.

    Args:
        parent_id: Parent request ID to set
    """
    _parent_id_var.set(parent_id)


def set_user_id(user_id: Optional[str]) -> None:
    """
    Set the user ID in context.

    Args:
        user_id: User ID to set
    """
    _user_id_var.set(user_id)


def set_request_depth(depth: int) -> None:
    """
    Set the request depth in context.

    Args:
        depth: Request depth to set
    """
    _request_depth_var.set(depth)


def set_request_chain(chain: list[str]) -> None:
    """
    Set the request chain in context.

    Args:
        chain: Request chain to set
    """
    _request_chain_var.set(chain)


def initialize_context(
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> CorrelationContext:
    """
    Initialize correlation context for a new request.

    Args:
        correlation_id: Existing correlation ID or None to generate new
        request_id: Existing request ID or None to generate new
        parent_id: Parent request ID for nested calls
        user_id: User ID for authenticated requests

    Returns:
        CorrelationContext: Initialized context
    """
    # Generate IDs if not provided
    if not correlation_id:
        correlation_id = generate_correlation_id()

    if not request_id:
        request_id = generate_request_id()

    # Calculate depth and chain
    depth = 0
    chain = []

    if parent_id:
        # This is a nested request
        parent_depth = get_request_depth()
        depth = parent_depth + 1

        # Extend the chain
        parent_chain = get_request_chain()
        chain = parent_chain + [request_id]
    else:
        # This is a root request
        chain = [request_id]

    # Set context variables
    set_correlation_id(correlation_id)
    set_request_id(request_id)
    set_parent_id(parent_id)
    set_user_id(user_id)
    set_request_depth(depth)
    set_request_chain(chain)

    context = CorrelationContext(
        correlation_id=correlation_id,
        request_id=request_id,
        parent_id=parent_id,
        user_id=user_id,
        depth=depth,
        chain=chain,
    )

    logger.debug(
        f"Initialized correlation context: {context.to_dict()}",
        extra={"correlation_id": correlation_id, "request_id": request_id},
    )

    return context


def clear_context() -> None:
    """Clear all correlation context variables."""
    _correlation_id_var.set(None)
    _request_id_var.set(None)
    _parent_id_var.set(None)
    _user_id_var.set(None)
    _request_depth_var.set(0)
    _request_chain_var.set([])


class CorrelationContextManager:
    """
    Context manager for correlation context.

    Usage:
        with CorrelationContextManager(correlation_id="abc-123"):
            # Code here has correlation context set
            process_request()
        # Context is automatically cleared
    """

    def __init__(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize context manager.

        Args:
            correlation_id: Correlation ID
            request_id: Request ID
            parent_id: Parent request ID
            user_id: User ID
        """
        self.correlation_id = correlation_id
        self.request_id = request_id
        self.parent_id = parent_id
        self.user_id = user_id
        self.context: Optional[CorrelationContext] = None
        self._tokens: list = []

    def __enter__(self) -> CorrelationContext:
        """Enter context manager."""
        self.context = initialize_context(
            correlation_id=self.correlation_id,
            request_id=self.request_id,
            parent_id=self.parent_id,
            user_id=self.user_id,
        )
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clear context."""
        clear_context()
        return False

    async def __aenter__(self) -> CorrelationContext:
        """Enter async context manager."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        return self.__exit__(exc_type, exc_val, exc_tb)
