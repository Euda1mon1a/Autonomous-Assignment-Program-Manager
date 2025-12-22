"""
Request deduplication service.

Provides high-level API for request deduplication with idempotency
key management, duplicate detection, and response caching.
"""
import hashlib
import json
import logging
import re
from typing import Any, Optional

import redis.asyncio as redis
from fastapi import Request

from app.core.config import get_settings
from app.middleware.deduplication.storage import (
    DeduplicationStorage,
    RequestRecord,
    RequestStatus,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DeduplicationConfig:
    """
    Configuration for request deduplication behavior.

    Defines which endpoints support idempotency and how to
    extract idempotency keys.
    """

    # HTTP methods that support idempotency
    IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Header name for idempotency key
    IDEMPOTENCY_HEADER = "Idempotency-Key"

    # Endpoints that support deduplication (regex patterns)
    DEDUP_ENDPOINTS = [
        r"^/api/v1/schedules/generate$",
        r"^/api/v1/schedules/\d+$",
        r"^/api/v1/assignments/?$",
        r"^/api/v1/swaps/?$",
        r"^/api/v1/swaps/\d+/execute$",
        r"^/api/v1/leaves/?$",
        r"^/api/v1/persons/?$",
    ]

    # Endpoints that are excluded from deduplication
    EXCLUDE_ENDPOINTS = [
        r"^/health$",
        r"^/metrics$",
        r"^/docs",
        r"^/openapi.json$",
        r"^/redoc",
        r"^/static/",
    ]

    # Default TTL for cached responses (5 minutes)
    DEFAULT_TTL = 300

    # Maximum wait time for concurrent requests (30 seconds)
    MAX_WAIT_TIME = 30.0

    @classmethod
    def is_endpoint_supported(cls, path: str, method: str) -> bool:
        """
        Check if endpoint supports deduplication.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            True if endpoint supports deduplication
        """
        # Check method
        if method not in cls.IDEMPOTENT_METHODS:
            return False

        # Check exclusions first
        for pattern in cls.EXCLUDE_ENDPOINTS:
            if re.match(pattern, path):
                return False

        # Check if endpoint is in supported list
        for pattern in cls.DEDUP_ENDPOINTS:
            if re.match(pattern, path):
                return True

        return False


class DeduplicationService:
    """
    Service for request deduplication and idempotency.

    Handles idempotency key extraction, duplicate detection,
    response caching, and concurrent request coordination.
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        storage: Optional[DeduplicationStorage] = None,
        config: Optional[DeduplicationConfig] = None,
    ):
        """
        Initialize deduplication service.

        Args:
            redis_client: Optional Redis client
            storage: Optional storage instance
            config: Optional configuration instance
        """
        self.config = config or DeduplicationConfig()

        # Initialize storage
        if storage:
            self.storage = storage
        else:
            self.storage = DeduplicationStorage(redis_client=redis_client)

    def extract_idempotency_key(self, request: Request) -> Optional[str]:
        """
        Extract idempotency key from request.

        Tries to extract from:
        1. Idempotency-Key header
        2. Request body (if JSON with 'idempotency_key' field)
        3. Auto-generated from request fingerprint

        Args:
            request: FastAPI request

        Returns:
            Idempotency key or None if not applicable
        """
        # Check if endpoint supports deduplication
        if not self.config.is_endpoint_supported(
            request.url.path, request.method
        ):
            return None

        # 1. Try to get from header
        header_key = request.headers.get(self.config.IDEMPOTENCY_HEADER)
        if header_key:
            logger.debug(f"Idempotency key from header: {header_key}")
            return header_key

        # 2. Try to get from request body (if available in state)
        # Note: Body is consumed by middleware, stored in request.state
        if hasattr(request.state, "body_bytes"):
            try:
                body = request.state.body_bytes
                if body:
                    body_json = json.loads(body.decode("utf-8"))
                    if isinstance(body_json, dict):
                        body_key = body_json.get("idempotency_key")
                        if body_key:
                            logger.debug(f"Idempotency key from body: {body_key}")
                            return body_key
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                pass

        # 3. Auto-generate from request fingerprint
        # (only for specific endpoints where it's safe)
        if self._should_auto_generate(request):
            fingerprint = self._generate_request_fingerprint(request)
            logger.debug(f"Auto-generated idempotency key: {fingerprint}")
            return fingerprint

        return None

    def _should_auto_generate(self, request: Request) -> bool:
        """
        Check if idempotency key should be auto-generated.

        Auto-generation is only safe for specific endpoints where
        request content uniquely identifies the operation.

        Args:
            request: FastAPI request

        Returns:
            True if should auto-generate
        """
        # Only auto-generate for specific safe endpoints
        auto_generate_patterns = [
            r"^/api/v1/schedules/generate$",  # Safe: schedule params are unique
        ]

        for pattern in auto_generate_patterns:
            if re.match(pattern, request.url.path):
                return True

        return False

    def _generate_request_fingerprint(self, request: Request) -> str:
        """
        Generate a fingerprint from request content.

        Creates a hash of method, path, query params, and body
        to uniquely identify the request.

        Args:
            request: FastAPI request

        Returns:
            SHA256 hash as hexadecimal string
        """
        # Collect request components
        components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]

        # Add body if available
        if hasattr(request.state, "body_bytes"):
            components.append(request.state.body_bytes.decode("utf-8", errors="ignore"))

        # Generate hash
        fingerprint_data = "|".join(components)
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode("utf-8")).hexdigest()

        return f"auto:{fingerprint_hash[:32]}"

    async def check_duplicate(
        self,
        idempotency_key: str,
    ) -> tuple[bool, Optional[RequestRecord]]:
        """
        Check if request is a duplicate.

        Args:
            idempotency_key: Idempotency key to check

        Returns:
            Tuple of (is_duplicate, record) where:
                - is_duplicate: True if request already exists
                - record: Existing RequestRecord or None
        """
        record = await self.storage.get_record(idempotency_key)

        if record is None:
            return False, None

        # Check if record is still valid
        if record.is_expired():
            await self.storage.delete_record(idempotency_key)
            return False, None

        logger.info(
            f"Duplicate request detected: {idempotency_key} "
            f"(status={record.status.value})"
        )

        return True, record

    async def handle_duplicate(
        self,
        idempotency_key: str,
        record: RequestRecord,
    ) -> Optional[RequestRecord]:
        """
        Handle a duplicate request.

        If request is still processing, waits for completion.
        If completed, returns cached response.

        Args:
            idempotency_key: Idempotency key
            record: Existing request record

        Returns:
            Completed RequestRecord with cached response or None if timeout
        """
        # If request is still processing, wait for completion
        if record.is_processing():
            logger.info(
                f"Waiting for concurrent request to complete: {idempotency_key}"
            )

            completed_record = await self.storage.wait_for_completion(
                idempotency_key,
                timeout=self.config.MAX_WAIT_TIME,
            )

            if completed_record is None:
                logger.warning(
                    f"Timeout waiting for concurrent request: {idempotency_key}"
                )
                return None

            return completed_record

        # Request already completed, return cached record
        return record

    async def start_processing(
        self,
        idempotency_key: str,
        ttl: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Start processing a new request.

        Acquires lock and creates request record.

        Args:
            idempotency_key: Idempotency key
            ttl: Time-to-live for request record

        Returns:
            Tuple of (started, lock_id) where:
                - started: True if processing started
                - lock_id: Lock identifier for release
        """
        ttl = ttl or self.config.DEFAULT_TTL

        # Acquire lock
        acquired, lock_id = await self.storage.acquire_lock(idempotency_key)

        if not acquired:
            logger.warning(f"Failed to acquire lock: {idempotency_key}")
            return False, None

        # Create processing record
        try:
            await self.storage.create_record(idempotency_key, ttl=ttl)
            logger.debug(f"Started processing: {idempotency_key}")
            return True, lock_id

        except Exception as e:
            # Release lock if record creation fails
            await self.storage.release_lock(idempotency_key, lock_id)
            logger.error(f"Failed to create record: {e}")
            return False, None

    async def complete_processing(
        self,
        idempotency_key: str,
        lock_id: Optional[str],
        response_status: int,
        response_headers: dict[str, str],
        response_body: bytes,
    ) -> bool:
        """
        Complete request processing with success.

        Updates record and releases lock.

        Args:
            idempotency_key: Idempotency key
            lock_id: Lock identifier from start_processing
            response_status: HTTP status code
            response_headers: Response headers to cache
            response_body: Response body to cache

        Returns:
            True if completed successfully
        """
        try:
            # Update record with response
            updated = await self.storage.update_record(
                idempotency_key=idempotency_key,
                status=RequestStatus.COMPLETED,
                response_status=response_status,
                response_headers=response_headers,
                response_body=response_body,
            )

            if not updated:
                logger.warning(f"Failed to update record: {idempotency_key}")

            logger.debug(
                f"Completed processing: {idempotency_key} "
                f"(status={response_status})"
            )

            return updated

        finally:
            # Always release lock
            await self.storage.release_lock(idempotency_key, lock_id)

    async def fail_processing(
        self,
        idempotency_key: str,
        lock_id: Optional[str],
        error_message: str,
    ) -> bool:
        """
        Mark request processing as failed.

        Updates record and releases lock.

        Args:
            idempotency_key: Idempotency key
            lock_id: Lock identifier from start_processing
            error_message: Error message

        Returns:
            True if updated successfully
        """
        try:
            # Update record with error
            updated = await self.storage.update_record(
                idempotency_key=idempotency_key,
                status=RequestStatus.FAILED,
                error_message=error_message,
            )

            if not updated:
                logger.warning(f"Failed to update record: {idempotency_key}")

            logger.debug(
                f"Failed processing: {idempotency_key} "
                f"(error={error_message})"
            )

            return updated

        finally:
            # Always release lock
            await self.storage.release_lock(idempotency_key, lock_id)

    async def get_stats(self) -> dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with statistics
        """
        return await self.storage.get_stats()

    async def cleanup_expired(self) -> int:
        """
        Clean up expired request records.

        Returns:
            Number of records cleaned up
        """
        return await self.storage.cleanup_expired()
