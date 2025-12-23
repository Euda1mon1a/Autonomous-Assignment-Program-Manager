"""
Request throttling middleware.

Implements comprehensive request throttling with:
- Concurrent request limiting
- Request queue management
- Priority-based throttling
- Endpoint-specific limits
- User-based throttling
- Graceful degradation
- Backpressure handling
"""

import asyncio
import logging
import time
import uuid
from collections.abc import Callable

import redis.asyncio as redis
from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.security import ALGORITHM
from app.middleware.throttling.config import (
    DEFAULT_THROTTLE_CONFIG,
    get_endpoint_config,
    get_priority_for_endpoint,
    get_role_config,
)
from app.middleware.throttling.storage import ThrottleStorage
from app.middleware.throttling.strategies import (
    AdaptiveThrottleStrategy,
    PriorityThrottleStrategy,
    QueuedThrottleStrategy,
    SimpleThrottleStrategy,
    ThrottleAction,
    ThrottleStrategy,
    create_throttle_response,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class ThrottlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request throttling and concurrent request management.

    Features:
    - Concurrent request limiting (max N requests at a time)
    - Request queue management (queue when capacity reached)
    - Priority-based throttling (critical > high > normal > low > background)
    - Endpoint-specific limits (e.g., /schedules/generate limited to 5 concurrent)
    - User-based throttling (different limits per user role)
    - Graceful degradation (adaptive behavior under load)
    - Backpressure handling (reject low priority when under stress)

    Unlike rate limiting (requests per time period), throttling controls
    concurrent requests and provides queuing with timeout.
    """

    def __init__(
        self,
        app,
        redis_client: redis.Redis | None = None,
        strategy: str = "adaptive",
    ):
        """
        Initialize throttling middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client (creates new if not provided)
            strategy: Throttling strategy ("simple", "queued", "priority", "adaptive")
        """
        super().__init__(app)

        # Initialize Redis storage
        if redis_client is None:
            try:
                redis_url = settings.redis_url_with_password
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                logger.info("Throttling middleware connected to Redis")
            except Exception as e:
                logger.error(f"Throttling middleware: Redis connection failed: {e}")
                self.redis = None
        else:
            self.redis = redis_client

        # Initialize storage
        self.storage = ThrottleStorage(self.redis)

        # Initialize strategy
        self.strategy = self._create_strategy(strategy)

        # Track request IDs for cleanup
        self._active_requests: set[str] = set()

    def _create_strategy(self, strategy_name: str) -> ThrottleStrategy:
        """
        Create throttling strategy instance.

        Args:
            strategy_name: Strategy name

        Returns:
            ThrottleStrategy instance
        """
        strategies = {
            "simple": SimpleThrottleStrategy,
            "queued": QueuedThrottleStrategy,
            "priority": PriorityThrottleStrategy,
            "adaptive": AdaptiveThrottleStrategy,
        }

        strategy_class = strategies.get(strategy_name, AdaptiveThrottleStrategy)
        return strategy_class(self.storage)

    def _extract_user_info(self, request: Request) -> tuple[str | None, str | None]:
        """
        Extract user ID and role from JWT token.

        Args:
            request: FastAPI request

        Returns:
            Tuple of (user_id, role) or (None, None) if not authenticated
        """
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Check for token in cookie
            cookie = request.cookies.get("access_token")
            if cookie and cookie.startswith("Bearer "):
                token = cookie.split(" ")[1]

        if not token:
            return None, None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            role = payload.get("role")
            return user_id, role
        except JWTError:
            return None, None

    def _should_skip_throttling(self, request: Request) -> bool:
        """
        Check if request should skip throttling.

        Args:
            request: FastAPI request

        Returns:
            True if should skip
        """
        # Skip certain endpoints
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
        ]

        if request.url.path in skip_paths:
            return True

        # Skip static files
        if request.url.path.startswith("/static/"):
            return True

        return False

    def _get_client_identifier(self, request: Request, user_id: str | None) -> str:
        """
        Get unique identifier for client.

        Args:
            request: FastAPI request
            user_id: User ID from token (if authenticated)

        Returns:
            Unique identifier
        """
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        if request.client:
            return f"ip:{request.client.host}"

        return "ip:unknown"

    async def _wait_for_slot(
        self,
        request_id: str,
        timeout: float,
    ) -> bool:
        """
        Wait for a request slot to become available.

        Args:
            request_id: Request identifier
            timeout: Maximum time to wait

        Returns:
            True if slot acquired, False if timed out
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Try to acquire slot
            acquired, _ = await self.storage.acquire_slot(
                request_id=request_id,
                user_id=None,  # Will be set by caller
                endpoint="",  # Will be set by caller
                priority="normal",
                max_concurrent=100,  # Default
                timeout=timeout,
            )

            if acquired:
                return True

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        return False

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with throttling.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response with throttling headers
        """
        # Skip if should not throttle
        if self._should_skip_throttling(request):
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract user information
        user_id, role = self._extract_user_info(request)
        client_id = self._get_client_identifier(request, user_id)

        # Get endpoint and priority
        endpoint = request.url.path
        priority = get_priority_for_endpoint(endpoint)

        # Get throttling configuration
        endpoint_config = get_endpoint_config(endpoint)
        if endpoint_config:
            max_concurrent = endpoint_config.max_concurrent
            max_queue_size = endpoint_config.max_queue_size
            timeout = endpoint_config.queue_timeout
            config = DEFAULT_THROTTLE_CONFIG
        else:
            config = get_role_config(role)
            max_concurrent = config.max_concurrent_requests
            max_queue_size = config.max_queue_size
            timeout = config.queue_timeout_seconds

        # Get current metrics
        metrics = await self.storage.get_metrics(max_concurrent, max_queue_size)

        # Make throttling decision
        decision = await self.strategy.decide(request, config, metrics, priority)

        # Handle decision
        if decision.action == ThrottleAction.REJECT:
            logger.warning(
                f"Throttle REJECT: {request.method} {endpoint} "
                f"(priority={priority.value}, utilization={metrics.utilization:.2f})"
            )
            return create_throttle_response(decision)

        elif decision.action == ThrottleAction.QUEUE:
            # Try to enqueue
            enqueued, reason = await self.storage.enqueue_request(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                priority=priority.value,
                max_queue_size=max_queue_size,
                timeout=timeout,
            )

            if not enqueued:
                logger.warning(
                    f"Throttle QUEUE FULL: {request.method} {endpoint} "
                    f"(reason={reason})"
                )
                return create_throttle_response(decision)

            # Wait for slot
            logger.info(
                f"Throttle QUEUED: {request.method} {endpoint} "
                f"(priority={priority.value}, queue_size={metrics.queued_requests})"
            )

            # Wait for slot to become available
            slot_acquired = await self._wait_for_slot(request_id, timeout)

            # Remove from queue
            await self.storage.dequeue_request(request_id)

            if not slot_acquired:
                logger.warning(
                    f"Throttle TIMEOUT: {request.method} {endpoint} (waited {timeout}s)"
                )
                decision.reason = "Request timed out in queue"
                decision.retry_after = 10
                return create_throttle_response(decision)

        # Try to acquire slot (for ALLOW action or after queue)
        acquired, reason = await self.storage.acquire_slot(
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint,
            priority=priority.value,
            max_concurrent=max_concurrent,
            timeout=timeout,
        )

        if not acquired:
            logger.warning(
                f"Throttle SLOT UNAVAILABLE: {request.method} {endpoint} "
                f"(reason={reason})"
            )
            decision.action = ThrottleAction.REJECT
            decision.reason = reason or "Unable to acquire request slot"
            decision.retry_after = 5
            return create_throttle_response(decision)

        # Track active request
        self._active_requests.add(request_id)

        # Process request
        start_time = time.time()
        try:
            logger.debug(
                f"Throttle ALLOW: {request.method} {endpoint} "
                f"(priority={priority.value}, active={metrics.active_requests})"
            )

            # Add throttling info to request state
            request.state.throttle_request_id = request_id
            request.state.throttle_priority = priority.value
            request.state.throttle_queued = decision.action == ThrottleAction.QUEUE

            response = await call_next(request)

            # Add throttling headers
            processing_time = time.time() - start_time
            response.headers["X-Throttle-Request-ID"] = request_id
            response.headers["X-Throttle-Priority"] = priority.value
            response.headers["X-Throttle-Active-Requests"] = str(
                metrics.active_requests
            )
            response.headers["X-Throttle-Queued-Requests"] = str(
                metrics.queued_requests
            )
            response.headers["X-Throttle-Utilization"] = f"{metrics.utilization:.2f}"
            response.headers["X-Throttle-Processing-Time"] = f"{processing_time:.3f}"

            if decision.action == ThrottleAction.QUEUE:
                response.headers["X-Throttle-Was-Queued"] = "true"
                response.headers["X-Throttle-Queue-Time"] = f"{decision.wait_time:.2f}"

            return response

        except Exception as e:
            logger.error(f"Error processing throttled request: {e}", exc_info=True)
            raise

        finally:
            # Release slot
            await self.storage.release_slot(request_id)
            self._active_requests.discard(request_id)

            # Log completion
            total_time = time.time() - start_time
            logger.debug(
                f"Throttle COMPLETE: {request.method} {endpoint} "
                f"(total_time={total_time:.3f}s)"
            )

    async def cleanup(self):
        """Clean up expired requests and release resources."""
        if self.storage:
            active_cleaned, queue_cleaned = await self.storage.cleanup_expired()
            if active_cleaned > 0 or queue_cleaned > 0:
                logger.info(
                    f"Throttle cleanup: removed {active_cleaned} active, "
                    f"{queue_cleaned} queued expired requests"
                )
