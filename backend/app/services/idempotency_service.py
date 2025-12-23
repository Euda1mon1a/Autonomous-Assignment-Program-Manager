"""Idempotency service for preventing duplicate schedule generation requests.

This service handles:
- Computing request body hashes
- Checking for existing idempotent requests
- Creating new idempotency records
- Updating records with results
- Cleaning up expired entries
"""

import hashlib
import json
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.idempotency import IdempotencyRequest, IdempotencyStatus

logger = get_logger(__name__)

# Default expiration time for idempotency keys (24 hours)
DEFAULT_EXPIRATION_HOURS = 24


class IdempotencyService:
    """Service for managing idempotency keys and request deduplication."""

    def __init__(self, db: Session, expiration_hours: int = DEFAULT_EXPIRATION_HOURS):
        self.db = db
        self.expiration_hours = expiration_hours

    def compute_body_hash(self, request_params: dict) -> str:
        """
        Compute SHA-256 hash of request parameters.

        Args:
            request_params: Dictionary of request parameters

        Returns:
            64-character hexadecimal hash string
        """
        # Sort keys for consistent hashing
        normalized = json.dumps(request_params, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get_existing_request(
        self, idempotency_key: str, body_hash: str
    ) -> IdempotencyRequest | None:
        """
        Check for an existing non-expired idempotency request.

        Args:
            idempotency_key: Client-provided idempotency key
            body_hash: SHA-256 hash of request body

        Returns:
            Existing IdempotencyRequest if found and not expired, None otherwise
        """
        existing = (
            self.db.query(IdempotencyRequest)
            .filter(
                IdempotencyRequest.idempotency_key == idempotency_key,
                IdempotencyRequest.body_hash == body_hash,
                IdempotencyRequest.expires_at > datetime.utcnow(),
            )
            .first()
        )
        return existing

    def check_key_conflict(
        self, idempotency_key: str, body_hash: str
    ) -> IdempotencyRequest | None:
        """
        Check if the same idempotency key was used with different parameters.

        This is a security/correctness check - the same key shouldn't be reused
        with different request bodies.

        Args:
            idempotency_key: Client-provided idempotency key
            body_hash: SHA-256 hash of request body

        Returns:
            Conflicting request if found, None otherwise
        """
        conflict = (
            self.db.query(IdempotencyRequest)
            .filter(
                IdempotencyRequest.idempotency_key == idempotency_key,
                IdempotencyRequest.body_hash != body_hash,
                IdempotencyRequest.expires_at > datetime.utcnow(),
            )
            .first()
        )
        return conflict

    def create_request(
        self, idempotency_key: str, body_hash: str, request_params: dict
    ) -> IdempotencyRequest:
        """
        Create a new idempotency request record.

        Args:
            idempotency_key: Client-provided idempotency key
            body_hash: SHA-256 hash of request body
            request_params: Original request parameters

        Returns:
            Created IdempotencyRequest

        Raises:
            IntegrityError: If a duplicate key+hash combination exists
        """
        expires_at = datetime.utcnow() + timedelta(hours=self.expiration_hours)

        request = IdempotencyRequest(
            idempotency_key=idempotency_key,
            body_hash=body_hash,
            request_params=request_params,
            status=IdempotencyStatus.PENDING.value,
            expires_at=expires_at,
        )

        self.db.add(request)
        try:
            self.db.flush()  # Flush to catch integrity errors early
        except IntegrityError:
            self.db.rollback()
            # Another request with same key+hash was just created
            # Return the existing one
            existing = self.get_existing_request(idempotency_key, body_hash)
            if existing:
                return existing
            raise

        return request

    def mark_completed(
        self,
        request: IdempotencyRequest,
        result_ref: UUID | None = None,
        response_body: dict | None = None,
        response_status_code: int = 200,
    ) -> None:
        """
        Mark an idempotency request as completed.

        Args:
            request: The IdempotencyRequest to update
            result_ref: Reference to the result (e.g., schedule_run_id)
            response_body: Response body to cache for replay
            response_status_code: HTTP status code of the response
        """
        request.status = IdempotencyStatus.COMPLETED.value
        request.completed_at = datetime.utcnow()
        request.result_ref = result_ref
        request.response_body = response_body
        request.response_status_code = str(response_status_code)

    def mark_failed(
        self,
        request: IdempotencyRequest,
        error_message: str,
        response_body: dict | None = None,
        response_status_code: int = 500,
    ) -> None:
        """
        Mark an idempotency request as failed.

        Args:
            request: The IdempotencyRequest to update
            error_message: Error message describing the failure
            response_body: Response body to cache for replay
            response_status_code: HTTP status code of the response
        """
        request.status = IdempotencyStatus.FAILED.value
        request.completed_at = datetime.utcnow()
        request.error_message = error_message
        request.response_body = response_body
        request.response_status_code = str(response_status_code)

    def cleanup_expired(self, batch_size: int = 1000) -> int:
        """
        Delete expired idempotency records.

        This should be called periodically (e.g., via cron or scheduled task)
        to prevent unbounded table growth.

        Args:
            batch_size: Maximum number of records to delete per call

        Returns:
            Number of records deleted
        """
        deleted = (
            self.db.query(IdempotencyRequest)
            .filter(IdempotencyRequest.expires_at < datetime.utcnow())
            .limit(batch_size)
            .delete(synchronize_session="fetch")
        )
        self.db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired idempotency records")

        return deleted

    def timeout_stale_pending(
        self, timeout_minutes: int = 10, batch_size: int = 100
    ) -> int:
        """
        Mark stale pending requests as failed.

        Requests stuck in PENDING state for longer than timeout_minutes are
        likely orphaned (e.g., worker crashed mid-processing). This prevents
        them from blocking future requests with the same idempotency key.

        Args:
            timeout_minutes: Minutes after which pending requests are considered stale
            batch_size: Maximum number of records to update per call

        Returns:
            Number of records marked as failed
        """
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        stale_requests = (
            self.db.query(IdempotencyRequest)
            .filter(
                IdempotencyRequest.status == IdempotencyStatus.PENDING.value,
                IdempotencyRequest.created_at < cutoff,
            )
            .limit(batch_size)
            .all()
        )

        count = 0
        for request in stale_requests:
            request.status = IdempotencyStatus.FAILED.value
            request.completed_at = datetime.utcnow()
            request.error_message = f"Request timed out after {timeout_minutes} minutes"
            count += 1

        if count > 0:
            self.db.commit()
            logger.warning(f"Timed out {count} stale pending idempotency requests")

        return count


def extract_idempotency_params(request_data: dict) -> dict:
    """
    Extract the parameters that should be included in idempotency hash.

    This includes all parameters that affect the schedule generation result:
    - Date range
    - Algorithm
    - PGY levels
    - Rotation template IDs
    - Timeout (optional)

    Args:
        request_data: Full request data dictionary

    Returns:
        Dictionary of parameters for hashing
    """
    return {
        "start_date": str(request_data.get("start_date")),
        "end_date": str(request_data.get("end_date")),
        "algorithm": request_data.get("algorithm", "greedy"),
        "pgy_levels": sorted(request_data.get("pgy_levels") or []),
        "rotation_template_ids": sorted(
            str(x) for x in (request_data.get("rotation_template_ids") or [])
        ),
    }
