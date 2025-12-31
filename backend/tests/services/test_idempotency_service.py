"""Tests for IdempotencyService."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.models.idempotency import IdempotencyRequest, IdempotencyStatus
from app.services.idempotency_service import (
    DEFAULT_EXPIRATION_HOURS,
    IdempotencyService,
    extract_idempotency_params,
)


class TestIdempotencyService:
    """Test suite for IdempotencyService."""

    # ========================================================================
    # Compute Body Hash Tests
    # ========================================================================

    def test_compute_body_hash_success(self, db):
        """Test computing hash from request parameters."""
        service = IdempotencyService(db)
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "algorithm": "greedy",
        }

        result = service.compute_body_hash(params)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex chars

    def test_compute_body_hash_consistent_for_same_params(self, db):
        """Test that same params produce same hash."""
        service = IdempotencyService(db)
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "algorithm": "greedy",
        }

        hash1 = service.compute_body_hash(params)
        hash2 = service.compute_body_hash(params)

        assert hash1 == hash2

    def test_compute_body_hash_different_for_different_params(self, db):
        """Test that different params produce different hashes."""
        service = IdempotencyService(db)
        params1 = {"start_date": "2024-01-01", "end_date": "2024-01-31"}
        params2 = {"start_date": "2024-02-01", "end_date": "2024-02-28"}

        hash1 = service.compute_body_hash(params1)
        hash2 = service.compute_body_hash(params2)

        assert hash1 != hash2

    def test_compute_body_hash_order_independent(self, db):
        """Test that key order doesn't affect hash (keys are sorted)."""
        service = IdempotencyService(db)
        params1 = {"end_date": "2024-01-31", "start_date": "2024-01-01"}
        params2 = {"start_date": "2024-01-01", "end_date": "2024-01-31"}

        hash1 = service.compute_body_hash(params1)
        hash2 = service.compute_body_hash(params2)

        assert hash1 == hash2

    def test_compute_body_hash_handles_nested_data(self, db):
        """Test hashing with nested dictionaries and lists."""
        service = IdempotencyService(db)
        params = {
            "pgy_levels": [1, 2, 3],
            "rotation_template_ids": [uuid4(), uuid4()],
            "metadata": {"user": "test", "version": 1},
        }

        result = service.compute_body_hash(params)

        assert result is not None
        assert len(result) == 64

    # ========================================================================
    # Get Existing Request Tests
    # ========================================================================

    def test_get_existing_request_found(self, db):
        """Test finding an existing non-expired request."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create existing request
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=body_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        result = service.get_existing_request(key, body_hash)

        assert result is not None
        assert result.idempotency_key == key
        assert result.body_hash == body_hash

    def test_get_existing_request_not_found(self, db):
        """Test when no matching request exists."""
        service = IdempotencyService(db)
        result = service.get_existing_request("nonexistent-key", "nonexistent-hash")

        assert result is None

    def test_get_existing_request_expired(self, db):
        """Test that expired requests are not returned."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

        # Create expired request
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=body_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        result = service.get_existing_request(key, body_hash)

        assert result is None  # Expired should not be returned

    def test_get_existing_request_wrong_hash(self, db):
        """Test that wrong hash doesn't match."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create request with one hash
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=body_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        # Query with different hash
        result = service.get_existing_request(key, "different-hash")

        assert result is None

    # ========================================================================
    # Check Key Conflict Tests
    # ========================================================================

    def test_check_key_conflict_detected(self, db):
        """Test detecting key conflict (same key, different body hash)."""
        service = IdempotencyService(db)
        key = "test-key-123"
        original_hash = "abc123def456"
        different_hash = "xyz789ghi012"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create request with original hash
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=original_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        # Check for conflict with different hash
        result = service.check_key_conflict(key, different_hash)

        assert result is not None
        assert result.idempotency_key == key
        assert result.body_hash == original_hash

    def test_check_key_conflict_no_conflict(self, db):
        """Test no conflict when key and hash match."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create request
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=body_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        # Check with same hash - no conflict
        result = service.check_key_conflict(key, body_hash)

        assert result is None

    def test_check_key_conflict_expired_ignored(self, db):
        """Test that expired requests don't trigger conflicts."""
        service = IdempotencyService(db)
        key = "test-key-123"
        original_hash = "abc123def456"
        different_hash = "xyz789ghi012"
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired

        # Create expired request
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key,
            body_hash=original_hash,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        # Check for conflict - expired should be ignored
        result = service.check_key_conflict(key, different_hash)

        assert result is None

    def test_check_key_conflict_different_key_no_conflict(self, db):
        """Test that different keys don't conflict."""
        service = IdempotencyService(db)
        key1 = "test-key-123"
        key2 = "test-key-456"
        hash1 = "abc123def456"
        hash2 = "xyz789ghi012"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Create request with key1 and hash1
        existing = IdempotencyRequest(
            id=uuid4(),
            idempotency_key=key1,
            body_hash=hash1,
            request_params={"test": "data"},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=expires_at,
        )
        db.add(existing)
        db.commit()

        # Check key2 with hash2 - different keys, no conflict
        result = service.check_key_conflict(key2, hash2)

        assert result is None

    # ========================================================================
    # Create Request Tests
    # ========================================================================

    def test_create_request_success(self, db):
        """Test creating a new idempotency request."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        params = {"start_date": "2024-01-01", "end_date": "2024-01-31"}

        result = service.create_request(key, body_hash, params)

        assert result is not None
        assert result.idempotency_key == key
        assert result.body_hash == body_hash
        assert result.request_params == params
        assert result.status == IdempotencyStatus.PENDING.value
        assert result.expires_at > datetime.utcnow()

    def test_create_request_default_expiration(self, db):
        """Test that default expiration is set correctly."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        params = {"test": "data"}

        before = datetime.utcnow() + timedelta(hours=DEFAULT_EXPIRATION_HOURS)
        result = service.create_request(key, body_hash, params)
        after = datetime.utcnow() + timedelta(hours=DEFAULT_EXPIRATION_HOURS)

        # Expiration should be within a few seconds of expected
        assert before <= result.expires_at <= after + timedelta(seconds=5)

    def test_create_request_custom_expiration(self, db):
        """Test creating request with custom expiration."""
        custom_hours = 48
        service = IdempotencyService(db, expiration_hours=custom_hours)
        key = "test-key-123"
        body_hash = "abc123def456"
        params = {"test": "data"}

        before = datetime.utcnow() + timedelta(hours=custom_hours)
        result = service.create_request(key, body_hash, params)
        after = datetime.utcnow() + timedelta(hours=custom_hours)

        # Expiration should be within a few seconds of expected
        assert before <= result.expires_at <= after + timedelta(seconds=5)

    def test_create_request_persists_to_database(self, db):
        """Test that created request is persisted."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        params = {"test": "data"}

        result = service.create_request(key, body_hash, params)
        request_id = result.id

        # Query directly from database
        db_request = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.id == request_id
        ).first()

        assert db_request is not None
        assert db_request.idempotency_key == key

    def test_create_request_handles_race_condition(self, db):
        """Test that concurrent creation attempts return existing request."""
        service = IdempotencyService(db)
        key = "test-key-123"
        body_hash = "abc123def456"
        params = {"test": "data"}

        # Create first request
        first = service.create_request(key, body_hash, params)
        db.commit()

        # Attempt to create duplicate - should return existing
        second = service.create_request(key, body_hash, params)

        assert second is not None
        assert second.id == first.id

    # ========================================================================
    # Mark Completed Tests
    # ========================================================================

    def test_mark_completed_success(self, db):
        """Test marking a request as completed."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        result_ref = uuid4()
        response_body = {"schedule_run_id": str(result_ref)}

        service.mark_completed(request, result_ref, response_body, 200)

        assert request.status == IdempotencyStatus.COMPLETED.value
        assert request.completed_at is not None
        assert request.result_ref == result_ref
        assert request.response_body == response_body
        assert request.response_status_code == "200"

    def test_mark_completed_without_result_ref(self, db):
        """Test marking completed without result reference."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        service.mark_completed(request)

        assert request.status == IdempotencyStatus.COMPLETED.value
        assert request.completed_at is not None
        assert request.result_ref is None
        assert request.response_status_code == "200"

    def test_mark_completed_with_custom_status_code(self, db):
        """Test marking completed with custom status code."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        service.mark_completed(request, response_status_code=201)

        assert request.status == IdempotencyStatus.COMPLETED.value
        assert request.response_status_code == "201"

    def test_mark_completed_sets_timestamp(self, db):
        """Test that completed_at timestamp is set."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        before = datetime.utcnow()
        service.mark_completed(request)
        after = datetime.utcnow()

        assert request.completed_at is not None
        assert before <= request.completed_at <= after + timedelta(seconds=1)

    # ========================================================================
    # Mark Failed Tests
    # ========================================================================

    def test_mark_failed_success(self, db):
        """Test marking a request as failed."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        error_message = "Schedule generation failed: timeout"
        response_body = {"error": error_message}

        service.mark_failed(request, error_message, response_body, 500)

        assert request.status == IdempotencyStatus.FAILED.value
        assert request.completed_at is not None
        assert request.error_message == error_message
        assert request.response_body == response_body
        assert request.response_status_code == "500"

    def test_mark_failed_with_custom_status_code(self, db):
        """Test marking failed with custom status code."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        service.mark_failed(request, "Bad request", response_status_code=400)

        assert request.status == IdempotencyStatus.FAILED.value
        assert request.response_status_code == "400"

    def test_mark_failed_sets_timestamp(self, db):
        """Test that completed_at timestamp is set on failure."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        before = datetime.utcnow()
        service.mark_failed(request, "Error occurred")
        after = datetime.utcnow()

        assert request.completed_at is not None
        assert before <= request.completed_at <= after + timedelta(seconds=1)

    def test_mark_failed_stores_error_message(self, db):
        """Test that error message is stored correctly."""
        service = IdempotencyService(db)
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        error_message = "Detailed error message with context"
        service.mark_failed(request, error_message)

        assert request.error_message == error_message

    # ========================================================================
    # Cleanup Expired Tests
    # ========================================================================

    def test_cleanup_expired_deletes_expired_records(self, db):
        """Test that expired records are deleted."""
        service = IdempotencyService(db)

        # Create expired request
        expired = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="expired-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(expired)
        db.commit()

        count = service.cleanup_expired()

        assert count == 1
        # Verify deletion
        db_request = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == "expired-key"
        ).first()
        assert db_request is None

    def test_cleanup_expired_keeps_valid_records(self, db):
        """Test that non-expired records are not deleted."""
        service = IdempotencyService(db)

        # Create valid (non-expired) request
        valid = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="valid-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(valid)
        db.commit()

        count = service.cleanup_expired()

        assert count == 0
        # Verify still exists
        db_request = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == "valid-key"
        ).first()
        assert db_request is not None

    def test_cleanup_expired_multiple_records(self, db):
        """Test cleanup with multiple expired and valid records."""
        service = IdempotencyService(db)

        # Create 3 expired and 2 valid
        for i in range(3):
            expired = IdempotencyRequest(
                id=uuid4(),
                idempotency_key=f"expired-{i}",
                body_hash=f"hash-{i}",
                request_params={},
                status=IdempotencyStatus.COMPLETED.value,
                expires_at=datetime.utcnow() - timedelta(hours=i+1),
            )
            db.add(expired)

        for i in range(2):
            valid = IdempotencyRequest(
                id=uuid4(),
                idempotency_key=f"valid-{i}",
                body_hash=f"hash-{i}",
                request_params={},
                status=IdempotencyStatus.COMPLETED.value,
                expires_at=datetime.utcnow() + timedelta(hours=i+1),
            )
            db.add(valid)

        db.commit()

        count = service.cleanup_expired()

        assert count == 3
        # Verify correct records remain
        remaining = db.query(IdempotencyRequest).count()
        assert remaining == 2

    def test_cleanup_expired_respects_batch_size(self, db):
        """Test that cleanup respects batch size limit."""
        service = IdempotencyService(db)

        # Create 5 expired records
        for i in range(5):
            expired = IdempotencyRequest(
                id=uuid4(),
                idempotency_key=f"expired-{i}",
                body_hash=f"hash-{i}",
                request_params={},
                status=IdempotencyStatus.COMPLETED.value,
                expires_at=datetime.utcnow() - timedelta(hours=1),
            )
            db.add(expired)
        db.commit()

        # Cleanup with batch_size=3
        count = service.cleanup_expired(batch_size=3)

        assert count == 3
        # Verify 2 records remain
        remaining = db.query(IdempotencyRequest).count()
        assert remaining == 2

    def test_cleanup_expired_returns_zero_when_none_expired(self, db):
        """Test cleanup returns 0 when no records are expired."""
        service = IdempotencyService(db)

        # Create valid request
        valid = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="valid-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(valid)
        db.commit()

        count = service.cleanup_expired()

        assert count == 0

    # ========================================================================
    # Timeout Stale Pending Tests
    # ========================================================================

    def test_timeout_stale_pending_marks_stale_as_failed(self, db):
        """Test that stale pending requests are marked as failed."""
        service = IdempotencyService(db)

        # Create stale pending request (created 30 minutes ago)
        stale = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="stale-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(stale)
        db.commit()

        count = service.timeout_stale_pending(timeout_minutes=10)

        assert count == 1
        # Verify status updated
        db.refresh(stale)
        assert stale.status == IdempotencyStatus.FAILED.value
        assert stale.completed_at is not None
        assert "timed out" in stale.error_message.lower()

    def test_timeout_stale_pending_keeps_recent_pending(self, db):
        """Test that recent pending requests are not timed out."""
        service = IdempotencyService(db)

        # Create recent pending request (created 5 minutes ago)
        recent = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="recent-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            created_at=datetime.utcnow() - timedelta(minutes=5),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(recent)
        db.commit()

        count = service.timeout_stale_pending(timeout_minutes=10)

        assert count == 0
        # Verify status unchanged
        db.refresh(recent)
        assert recent.status == IdempotencyStatus.PENDING.value
        assert recent.completed_at is None

    def test_timeout_stale_pending_ignores_completed(self, db):
        """Test that completed requests are not affected."""
        service = IdempotencyService(db)

        # Create old completed request
        completed = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="completed-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.COMPLETED.value,
            created_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=50),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(completed)
        db.commit()

        count = service.timeout_stale_pending(timeout_minutes=10)

        assert count == 0
        # Verify status unchanged
        db.refresh(completed)
        assert completed.status == IdempotencyStatus.COMPLETED.value

    def test_timeout_stale_pending_ignores_already_failed(self, db):
        """Test that already failed requests are not affected."""
        service = IdempotencyService(db)

        # Create old failed request
        failed = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="failed-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.FAILED.value,
            created_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(minutes=50),
            error_message="Original error",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(failed)
        db.commit()

        count = service.timeout_stale_pending(timeout_minutes=10)

        assert count == 0
        # Verify error message unchanged
        db.refresh(failed)
        assert failed.error_message == "Original error"

    def test_timeout_stale_pending_respects_batch_size(self, db):
        """Test that timeout respects batch size limit."""
        service = IdempotencyService(db)

        # Create 5 stale pending requests
        for i in range(5):
            stale = IdempotencyRequest(
                id=uuid4(),
                idempotency_key=f"stale-{i}",
                body_hash=f"hash-{i}",
                request_params={},
                status=IdempotencyStatus.PENDING.value,
                created_at=datetime.utcnow() - timedelta(minutes=30),
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )
            db.add(stale)
        db.commit()

        # Timeout with batch_size=3
        count = service.timeout_stale_pending(timeout_minutes=10, batch_size=3)

        assert count == 3
        # Verify 2 requests still pending
        pending_count = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.status == IdempotencyStatus.PENDING.value
        ).count()
        assert pending_count == 2

    def test_timeout_stale_pending_custom_timeout(self, db):
        """Test timeout with custom timeout_minutes."""
        service = IdempotencyService(db)

        # Create request that's 15 minutes old
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            created_at=datetime.utcnow() - timedelta(minutes=15),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request)
        db.commit()

        # Should timeout with 10 minute cutoff
        count = service.timeout_stale_pending(timeout_minutes=10)
        assert count == 1

        # Create another 15 minute old request
        request2 = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key-2",
            body_hash="def456",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            created_at=datetime.utcnow() - timedelta(minutes=15),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(request2)
        db.commit()

        # Should NOT timeout with 20 minute cutoff
        count = service.timeout_stale_pending(timeout_minutes=20)
        assert count == 0

    def test_timeout_stale_pending_error_message_includes_timeout(self, db):
        """Test that timeout error message includes timeout duration."""
        service = IdempotencyService(db)

        stale = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="stale-key",
            body_hash="abc123",
            request_params={},
            status=IdempotencyStatus.PENDING.value,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(stale)
        db.commit()

        timeout_minutes = 15
        service.timeout_stale_pending(timeout_minutes=timeout_minutes)

        db.refresh(stale)
        assert str(timeout_minutes) in stale.error_message
        assert "minutes" in stale.error_message.lower()


# ============================================================================
# Standalone Function Tests
# ============================================================================


class TestExtractIdempotencyParams:
    """Test suite for extract_idempotency_params function."""

    def test_extract_basic_params(self):
        """Test extracting basic schedule generation parameters."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "algorithm": "greedy",
            "pgy_levels": [1, 2, 3],
            "rotation_template_ids": ["id1", "id2"],
        }

        result = extract_idempotency_params(request_data)

        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        assert result["algorithm"] == "greedy"
        assert result["pgy_levels"] == [1, 2, 3]
        assert result["rotation_template_ids"] == ["id1", "id2"]

    def test_extract_with_default_algorithm(self):
        """Test that default algorithm is 'greedy' when not specified."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        }

        result = extract_idempotency_params(request_data)

        assert result["algorithm"] == "greedy"

    def test_extract_sorts_pgy_levels(self):
        """Test that PGY levels are sorted for consistent hashing."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "pgy_levels": [3, 1, 2],
        }

        result = extract_idempotency_params(request_data)

        assert result["pgy_levels"] == [1, 2, 3]

    def test_extract_sorts_rotation_template_ids(self):
        """Test that rotation template IDs are sorted for consistent hashing."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "rotation_template_ids": ["id3", "id1", "id2"],
        }

        result = extract_idempotency_params(request_data)

        assert result["rotation_template_ids"] == ["id1", "id2", "id3"]

    def test_extract_handles_none_pgy_levels(self):
        """Test extraction when pgy_levels is None."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "pgy_levels": None,
        }

        result = extract_idempotency_params(request_data)

        assert result["pgy_levels"] == []

    def test_extract_handles_none_rotation_templates(self):
        """Test extraction when rotation_template_ids is None."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "rotation_template_ids": None,
        }

        result = extract_idempotency_params(request_data)

        assert result["rotation_template_ids"] == []

    def test_extract_converts_dates_to_string(self):
        """Test that date objects are converted to strings."""
        from datetime import date

        request_data = {
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 31),
        }

        result = extract_idempotency_params(request_data)

        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"

    def test_extract_converts_uuids_to_strings(self):
        """Test that UUID objects are converted to strings."""
        id1 = uuid4()
        id2 = uuid4()

        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "rotation_template_ids": [id1, id2],
        }

        result = extract_idempotency_params(request_data)

        # Should be sorted strings
        assert all(isinstance(x, str) for x in result["rotation_template_ids"])
        assert len(result["rotation_template_ids"]) == 2

    def test_extract_ignores_extra_fields(self):
        """Test that extra fields not relevant to idempotency are ignored."""
        request_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "algorithm": "greedy",
            "extra_field": "should_be_ignored",
            "user_id": "12345",
        }

        result = extract_idempotency_params(request_data)

        # Should only contain the 5 relevant fields
        assert len(result) == 5
        assert "extra_field" not in result
        assert "user_id" not in result
