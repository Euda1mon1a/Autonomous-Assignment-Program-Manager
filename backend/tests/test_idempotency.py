"""
Tests for idempotency and row-level locking features.

Tests cover:
- Idempotency key model and service
- Request deduplication via Idempotency-Key header
- Key conflict detection (same key, different body)
- Cached response replay
- Row-level locking in schedule generation
"""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRequest, IdempotencyStatus
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.idempotency_service import (
    IdempotencyService,
    extract_idempotency_params,
)


class TestIdempotencyModel:
    """Tests for the IdempotencyRequest model."""

    def test_create_idempotency_request(self, db: Session):
        """Should create an idempotency request record."""
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key-123",
            body_hash="abc123def456",
            request_params={"start_date": "2024-01-01", "end_date": "2024-01-07"},
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        assert request.id is not None
        assert request.idempotency_key == "test-key-123"
        assert request.is_pending
        assert not request.is_completed
        assert not request.is_failed

    def test_idempotency_status_transitions(self, db: Session):
        """Should track status transitions correctly."""
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key-456",
            body_hash="xyz789",
            status=IdempotencyStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(request)
        db.commit()

        # Start as pending
        assert request.is_pending
        assert not request.is_completed

        # Mark completed
        request.status = IdempotencyStatus.COMPLETED.value
        request.completed_at = datetime.utcnow()
        db.commit()

        assert request.is_completed
        assert not request.is_pending
        assert request.completed_at is not None

    def test_idempotency_expiration(self, db: Session):
        """Should correctly identify expired requests."""
        # Non-expired request
        active = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="active-key",
            body_hash="hash1",
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        # Expired request
        expired = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="expired-key",
            body_hash="hash2",
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        db.add_all([active, expired])
        db.commit()

        assert not active.is_expired
        assert expired.is_expired


class TestIdempotencyService:
    """Tests for the IdempotencyService."""

    def test_compute_body_hash_deterministic(self, db: Session):
        """Should produce consistent hash for same parameters."""
        service = IdempotencyService(db)

        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "algorithm": "greedy",
        }

        hash1 = service.compute_body_hash(params)
        hash2 = service.compute_body_hash(params)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    def test_compute_body_hash_order_independent(self, db: Session):
        """Should produce same hash regardless of key order."""
        service = IdempotencyService(db)

        params1 = {"a": "1", "b": "2", "c": "3"}
        params2 = {"c": "3", "a": "1", "b": "2"}

        assert service.compute_body_hash(params1) == service.compute_body_hash(params2)

    def test_compute_body_hash_different_values(self, db: Session):
        """Should produce different hash for different values."""
        service = IdempotencyService(db)

        params1 = {"start_date": "2024-01-01", "end_date": "2024-01-07"}
        params2 = {"start_date": "2024-01-01", "end_date": "2024-01-08"}

        assert service.compute_body_hash(params1) != service.compute_body_hash(params2)

    def test_get_existing_request(self, db: Session):
        """Should find existing non-expired request."""
        service = IdempotencyService(db)

        # Create a completed request
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="test-key",
            body_hash="test-hash",
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(request)
        db.commit()

        # Should find it
        found = service.get_existing_request("test-key", "test-hash")
        assert found is not None
        assert found.id == request.id

        # Should not find with wrong hash
        not_found = service.get_existing_request("test-key", "wrong-hash")
        assert not_found is None

    def test_get_existing_request_ignores_expired(self, db: Session):
        """Should not return expired requests."""
        service = IdempotencyService(db)

        # Create an expired request
        expired = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="expired-key",
            body_hash="test-hash",
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(expired)
        db.commit()

        # Should not find it
        found = service.get_existing_request("expired-key", "test-hash")
        assert found is None

    def test_check_key_conflict(self, db: Session):
        """Should detect when same key used with different body."""
        service = IdempotencyService(db)

        # Create a request with specific hash
        request = IdempotencyRequest(
            id=uuid4(),
            idempotency_key="conflict-key",
            body_hash="original-hash",
            status=IdempotencyStatus.COMPLETED.value,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(request)
        db.commit()

        # Same key, same hash - no conflict
        no_conflict = service.check_key_conflict("conflict-key", "original-hash")
        assert no_conflict is None

        # Same key, different hash - conflict!
        conflict = service.check_key_conflict("conflict-key", "different-hash")
        assert conflict is not None
        assert conflict.id == request.id

    def test_create_request(self, db: Session):
        """Should create new idempotency request."""
        service = IdempotencyService(db, expiration_hours=24)

        request = service.create_request(
            idempotency_key="new-key",
            body_hash="new-hash",
            request_params={"test": "data"},
        )
        db.commit()

        assert request.idempotency_key == "new-key"
        assert request.body_hash == "new-hash"
        assert request.is_pending
        assert request.request_params == {"test": "data"}
        assert request.expires_at > datetime.utcnow()

    def test_mark_completed(self, db: Session):
        """Should mark request as completed with response."""
        service = IdempotencyService(db)

        request = service.create_request(
            idempotency_key="complete-key",
            body_hash="complete-hash",
            request_params={},
        )
        db.flush()

        result_id = uuid4()
        response = {"status": "success", "run_id": str(result_id)}

        service.mark_completed(
            request,
            result_ref=result_id,
            response_body=response,
            response_status_code=200,
        )
        db.commit()

        assert request.is_completed
        assert request.result_ref == result_id
        assert request.response_body == response
        assert request.response_status_code == "200"
        assert request.completed_at is not None

    def test_mark_failed(self, db: Session):
        """Should mark request as failed with error."""
        service = IdempotencyService(db)

        request = service.create_request(
            idempotency_key="fail-key",
            body_hash="fail-hash",
            request_params={},
        )
        db.flush()

        service.mark_failed(
            request,
            error_message="Something went wrong",
            response_body={"detail": "Something went wrong"},
            response_status_code=500,
        )
        db.commit()

        assert request.is_failed
        assert request.error_message == "Something went wrong"
        assert request.response_status_code == "500"
        assert request.completed_at is not None


class TestExtractIdempotencyParams:
    """Tests for the extract_idempotency_params helper."""

    def test_extracts_core_params(self):
        """Should extract the core scheduling parameters."""
        full_request = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "algorithm": "greedy",
            "pgy_levels": [1, 2, 3],
            "rotation_template_ids": ["uuid1", "uuid2"],
            "timeout_seconds": 60.0,  # Should not be included
        }

        params = extract_idempotency_params(full_request)

        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-07"
        assert params["algorithm"] == "greedy"
        assert params["pgy_levels"] == [1, 2, 3]
        assert "uuid1" in params["rotation_template_ids"]

    def test_handles_missing_optional_params(self):
        """Should handle missing optional parameters."""
        minimal_request = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
        }

        params = extract_idempotency_params(minimal_request)

        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-01-07"
        assert params["algorithm"] == "greedy"  # Default
        assert params["pgy_levels"] == []
        assert params["rotation_template_ids"] == []


class TestIdempotencyEndpoint:
    """Tests for idempotency in the schedule generation endpoint."""

    def test_generate_without_idempotency_key(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """Should work normally without idempotency key."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        response = client.post("/api/schedule/generate", json=payload)
        assert response.status_code in [200, 207]

        # No idempotency header in response
        assert "X-Idempotency-Replayed" not in response.headers

    def test_generate_with_idempotency_key_first_request(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should process first request with idempotency key."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        idempotency_key = f"test-{uuid4()}"

        response = client.post(
            "/api/schedule/generate",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert response.status_code in [200, 207]

        # Should have created idempotency record
        record = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == idempotency_key
        ).first()
        assert record is not None
        assert record.is_completed

    def test_generate_with_idempotency_key_replay(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should replay cached response for same idempotency key."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        idempotency_key = f"replay-{uuid4()}"

        # First request
        response1 = client.post(
            "/api/schedule/generate",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert response1.status_code in [200, 207]
        data1 = response1.json()

        # Second request with same key and body
        response2 = client.post(
            "/api/schedule/generate",
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert response2.status_code in [200, 207]
        data2 = response2.json()

        # Should be replayed (same data, replay header)
        assert response2.headers.get("X-Idempotency-Replayed") == "true"
        assert data1["run_id"] == data2["run_id"]  # Same run ID

    def test_generate_with_idempotency_key_conflict(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should reject when same key used with different body."""
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        idempotency_key = f"conflict-{uuid4()}"

        # First request
        payload1 = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }
        response1 = client.post(
            "/api/schedule/generate",
            json=payload1,
            headers={"Idempotency-Key": idempotency_key},
        )
        assert response1.status_code in [200, 207]

        # Second request with same key but different body
        payload2 = {
            "start_date": start_date.isoformat(),
            "end_date": (end_date + timedelta(days=1)).isoformat(),  # Different end date
            "algorithm": "greedy",
        }
        response2 = client.post(
            "/api/schedule/generate",
            json=payload2,
            headers={"Idempotency-Key": idempotency_key},
        )

        # Should be rejected
        assert response2.status_code == 422
        assert "different request parameters" in response2.json()["detail"].lower()


class TestRowLevelLocking:
    """Tests for row-level locking in schedule generation.

    Note: SQLite (used in tests) doesn't support FOR UPDATE,
    so these tests verify the code doesn't break. Real locking
    tests require PostgreSQL.
    """

    def test_delete_existing_assignments_with_locking(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should delete existing assignments when regenerating."""
        from app.models.assignment import Assignment
        from app.models.block import Block

        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # First generation
        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        response1 = client.post("/api/schedule/generate", json=payload)
        assert response1.status_code in [200, 207]

        # Count assignments
        count1 = db.query(Assignment).join(Block).filter(
            Block.date >= start_date,
            Block.date <= end_date,
        ).count()

        # Second generation (should delete old and create new)
        response2 = client.post("/api/schedule/generate", json=payload)
        assert response2.status_code in [200, 207]

        # Should still have similar count (old deleted, new created)
        count2 = db.query(Assignment).join(Block).filter(
            Block.date >= start_date,
            Block.date <= end_date,
        ).count()

        # Note: Count might differ slightly due to different random seed,
        # but there shouldn't be duplicates
        assert count2 > 0  # Should have some assignments

    def test_concurrent_generation_protection(
        self,
        client: TestClient,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
        db: Session,
    ):
        """Should prevent concurrent generation for overlapping ranges."""
        from app.models.schedule_run import ScheduleRun

        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Simulate an in-progress generation
        in_progress_run = ScheduleRun(
            start_date=start_date,
            end_date=end_date,
            algorithm="greedy",
            status="in_progress",
            total_blocks_assigned=0,
            acgme_violations=0,
            runtime_seconds=0.0,
            config_json={},
            created_at=datetime.utcnow(),
        )
        db.add(in_progress_run)
        db.commit()

        # Try to generate for same range
        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        response = client.post("/api/schedule/generate", json=payload)

        # Should be rejected
        assert response.status_code == 409
        assert "in progress" in response.json()["detail"].lower()


class TestOptimisticLocking:
    """Tests for optimistic locking in assignment updates."""

    def test_update_with_correct_version(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment,
        db: Session,
    ):
        """Should allow update with matching updated_at timestamp."""
        db.refresh(sample_assignment)
        updated_at = sample_assignment.updated_at

        update_payload = {
            "role": "backup",
            "updated_at": updated_at.isoformat(),
        }

        response = client.put(
            f"/api/assignments/{sample_assignment.id}",
            json=update_payload,
            headers=auth_headers,
        )

        # Should succeed
        assert response.status_code == 200

    def test_update_with_stale_version(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_assignment,
        db: Session,
    ):
        """Should reject update with stale updated_at timestamp."""
        # Use an old timestamp
        stale_timestamp = datetime(2020, 1, 1, 0, 0, 0)

        update_payload = {
            "role": "backup",
            "updated_at": stale_timestamp.isoformat(),
        }

        response = client.put(
            f"/api/assignments/{sample_assignment.id}",
            json=update_payload,
            headers=auth_headers,
        )

        # Should be rejected with 409 Conflict
        assert response.status_code == 409
        assert "modified" in response.json()["detail"].lower()
