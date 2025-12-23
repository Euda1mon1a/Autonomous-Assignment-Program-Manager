"""Idempotency request model - prevents duplicate schedule generation requests.

This model stores request hashes to ensure identical schedule generation requests
return cached results instead of creating duplicate schedules.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Index, String, Text

from app.db.base import Base
from app.db.types import GUID, JSONType


class IdempotencyStatus(str, Enum):
    """Status of an idempotent request."""

    PENDING = "pending"  # Request received, processing
    COMPLETED = "completed"  # Request completed successfully
    FAILED = "failed"  # Request failed


class IdempotencyRequest(Base):
    """
    Stores idempotency keys for schedule generation requests.

    Purpose:
    - Prevents duplicate schedule generations from identical requests
    - Allows returning cached results for repeated requests
    - Provides audit trail of generation attempts

    Usage:
    1. Client sends request with Idempotency-Key header
    2. Server computes body_hash from request parameters
    3. If (idempotency_key, body_hash) exists and completed, return cached result
    4. If exists but pending, return 409 (request in progress)
    5. If not exists, create new entry and process request

    Keys expire after 24 hours to prevent unbounded table growth.
    """

    __tablename__ = "idempotency_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Idempotency key provided by client (or auto-generated)
    idempotency_key = Column(String(255), nullable=False)

    # SHA-256 hash of request body (algorithm, date range, seed, etc.)
    body_hash = Column(String(64), nullable=False)

    # Request parameters (for debugging/audit)
    request_params = Column(JSONType())

    # Processing status
    status = Column(String(20), nullable=False, default=IdempotencyStatus.PENDING.value)

    # Reference to the result (schedule_run_id if successful)
    result_ref = Column(GUID(), nullable=True)

    # Error message if failed
    error_message = Column(Text, nullable=True)

    # Response body (cached for replay)
    response_body = Column(JSONType(), nullable=True)
    response_status_code = Column(String(3), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        # Composite unique constraint - same key must have same body hash
        Index("idx_idempotency_key_hash", "idempotency_key", "body_hash", unique=True),
        # Index for cleanup of expired entries
        Index("idx_idempotency_expires", "expires_at"),
        # Index for status lookups
        Index("idx_idempotency_status", "status"),
    )

    def __repr__(self):
        return f"<IdempotencyRequest(key='{self.idempotency_key[:8]}...', status='{self.status}')>"

    @property
    def is_pending(self) -> bool:
        """Check if request is still processing."""
        return self.status == IdempotencyStatus.PENDING.value

    @property
    def is_completed(self) -> bool:
        """Check if request completed successfully."""
        return self.status == IdempotencyStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if request failed."""
        return self.status == IdempotencyStatus.FAILED.value

    @property
    def is_expired(self) -> bool:
        """Check if the cached result has expired."""
        return datetime.utcnow() > self.expires_at
