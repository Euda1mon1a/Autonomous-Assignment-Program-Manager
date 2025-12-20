"""
Request deduplication middleware for FastAPI.

Implements idempotency for API endpoints by detecting duplicate
requests and returning cached responses.
"""
import logging
from typing import Callable, Optional

import redis.asyncio as redis
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.middleware.deduplication.service import DeduplicationService
from app.middleware.deduplication.storage import DeduplicationStorage, RequestRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class DeduplicationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request deduplication and idempotency.

    Features:
    - Automatic idempotency key extraction from headers or body
    - Duplicate request detection using Redis
    - Response caching for completed requests
    - Concurrent request handling (wait for first to complete)
    - TTL-based cleanup of cached responses
    - Endpoint-specific configuration

    Usage:
        app = FastAPI()
        app.add_middleware(DeduplicationMiddleware)

        # Client sends request with idempotency key
        POST /api/v1/schedules
        Headers:
            Idempotency-Key: unique-key-123

        # Duplicate request returns cached response
        POST /api/v1/schedules
        Headers:
            Idempotency-Key: unique-key-123
            X-Idempotent-Replayed: true
    """

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        enabled: bool = True,
    ):
        """
        Initialize deduplication middleware.

        Args:
            app: FastAPI application
            redis_client: Optional Redis client (creates new if not provided)
            enabled: Enable/disable middleware globally
        """
        super().__init__(app)
        self.enabled = enabled

        # Initialize Redis connection
        if redis_client is None:
            try:
                redis_url = settings.redis_url_with_password
                self.redis = redis.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                logger.info("Deduplication middleware connected to Redis")
            except Exception as e:
                logger.error(f"Deduplication middleware: Redis connection failed: {e}")
                self.redis = None
                self.enabled = False
        else:
            self.redis = redis_client

        # Initialize storage and service
        self.storage = DeduplicationStorage(redis_client=self.redis)
        self.service = DeduplicationService(storage=self.storage)

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request with deduplication.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response (cached or fresh)
        """
        # Skip if middleware disabled
        if not self.enabled:
            return await call_next(request)

        # Read body once and store in request state
        # (so it can be consumed by both middleware and endpoint)
        await self._store_body(request)

        # Extract idempotency key
        idempotency_key = self.service.extract_idempotency_key(request)

        # If no idempotency key, process normally
        if not idempotency_key:
            return await call_next(request)

        # Check for duplicate request
        is_duplicate, existing_record = await self.service.check_duplicate(
            idempotency_key
        )

        if is_duplicate and existing_record:
            # Handle duplicate request
            return await self._handle_duplicate(
                request,
                idempotency_key,
                existing_record,
            )

        # Start processing new request
        started, lock_id = await self.service.start_processing(idempotency_key)

        if not started:
            # Failed to acquire lock - another request is processing
            # Wait for it to complete
            logger.info(
                f"Concurrent request detected, waiting: {idempotency_key}"
            )
            existing_record = await self.storage.wait_for_completion(
                idempotency_key,
                timeout=self.service.config.MAX_WAIT_TIME,
            )

            if existing_record:
                return await self._handle_duplicate(
                    request,
                    idempotency_key,
                    existing_record,
                )
            else:
                # Timeout - return error
                return JSONResponse(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    content={
                        "error": "Request timeout",
                        "message": "Timeout waiting for concurrent request",
                    },
                )

        # Process request
        try:
            # Add idempotency info to request state
            request.state.idempotency_key = idempotency_key
            request.state.dedup_lock_id = lock_id

            # Call next middleware/endpoint
            response = await call_next(request)

            # Cache response if successful
            if 200 <= response.status_code < 300:
                await self._cache_response(
                    idempotency_key,
                    lock_id,
                    response,
                )
            else:
                # Mark as failed for non-2xx responses
                await self.service.fail_processing(
                    idempotency_key,
                    lock_id,
                    f"Request failed with status {response.status_code}",
                )

            # Add deduplication headers
            response.headers["X-Idempotency-Key"] = idempotency_key
            response.headers["X-Idempotent-Replayed"] = "false"

            return response

        except Exception as e:
            # Mark as failed on exception
            await self.service.fail_processing(
                idempotency_key,
                lock_id,
                str(e),
            )
            raise

    async def _store_body(self, request: Request) -> None:
        """
        Read and store request body in request state.

        Args:
            request: FastAPI request
        """
        try:
            body_bytes = await request.body()
            request.state.body_bytes = body_bytes
        except Exception as e:
            logger.warning(f"Failed to read request body: {e}")
            request.state.body_bytes = b""

    async def _handle_duplicate(
        self,
        request: Request,
        idempotency_key: str,
        record: RequestRecord,
    ) -> Response:
        """
        Handle duplicate request by returning cached response.

        Args:
            request: FastAPI request
            idempotency_key: Idempotency key
            record: Existing request record

        Returns:
            Cached response or error response
        """
        logger.info(
            f"Returning cached response for duplicate request: {idempotency_key}"
        )

        # If request still processing, wait for completion
        if record.is_processing():
            completed_record = await self.storage.wait_for_completion(
                idempotency_key,
                timeout=self.service.config.MAX_WAIT_TIME,
            )

            if completed_record:
                record = completed_record
            else:
                # Timeout
                return JSONResponse(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    content={
                        "error": "Request timeout",
                        "message": "Timeout waiting for concurrent request",
                    },
                )

        # If request failed, return error
        if record.is_failed():
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Previous request failed",
                    "message": record.error_message or "Unknown error",
                },
                headers={
                    "X-Idempotency-Key": idempotency_key,
                    "X-Idempotent-Replayed": "true",
                },
            )

        # Return cached response
        if record.response_body is not None:
            # Build response headers
            headers = dict(record.response_headers or {})
            headers["X-Idempotency-Key"] = idempotency_key
            headers["X-Idempotent-Replayed"] = "true"

            return Response(
                content=record.response_body,
                status_code=record.response_status or 200,
                headers=headers,
            )

        # No cached response (shouldn't happen)
        logger.warning(f"No cached response for completed request: {idempotency_key}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "No cached response",
                "message": "Request completed but response not cached",
            },
        )

    async def _cache_response(
        self,
        idempotency_key: str,
        lock_id: Optional[str],
        response: Response,
    ) -> None:
        """
        Cache response for future duplicate requests.

        Args:
            idempotency_key: Idempotency key
            lock_id: Lock identifier
            response: Response to cache
        """
        try:
            # Read response body
            response_body = b""
            if hasattr(response, "body"):
                response_body = response.body
            elif hasattr(response, "body_iterator"):
                # For streaming responses, collect chunks
                chunks = []
                async for chunk in response.body_iterator:
                    chunks.append(chunk)
                response_body = b"".join(chunks)

                # Replace iterator with single chunk
                async def body_iterator():
                    yield response_body

                response.body_iterator = body_iterator()

            # Filter headers to cache (exclude hop-by-hop headers)
            headers_to_cache = {}
            skip_headers = {
                "connection",
                "keep-alive",
                "proxy-authenticate",
                "proxy-authorization",
                "te",
                "trailers",
                "transfer-encoding",
                "upgrade",
            }

            for key, value in response.headers.items():
                if key.lower() not in skip_headers:
                    headers_to_cache[key] = value

            # Complete processing with cached response
            await self.service.complete_processing(
                idempotency_key=idempotency_key,
                lock_id=lock_id,
                response_status=response.status_code,
                response_headers=headers_to_cache,
                response_body=response_body,
            )

        except Exception as e:
            logger.error(f"Failed to cache response: {e}", exc_info=True)
            # Don't fail the request, just log the error
            await self.service.fail_processing(
                idempotency_key,
                lock_id,
                f"Failed to cache response: {str(e)}",
            )

    async def cleanup(self):
        """Clean up expired request records."""
        if self.enabled:
            cleaned = await self.service.cleanup_expired()
            if cleaned > 0:
                logger.info(
                    f"Deduplication cleanup: removed {cleaned} expired records"
                )
