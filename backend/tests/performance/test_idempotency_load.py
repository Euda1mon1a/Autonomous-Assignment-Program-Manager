"""
Performance tests for idempotency under concurrent load.

Tests verify that idempotency keys prevent duplicate record creation
when the same request is submitted many times concurrently, simulating
network retries, race conditions, and high-load scenarios.

Note: As of PR #240, idempotency is implemented for schedule generation.
These tests verify the idempotency framework under high concurrency.

Critical for:
- Data integrity in schedule generation
- Prevention of duplicate schedule runs
- Network retry resilience
- Race condition handling
"""
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.idempotency import IdempotencyRequest
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun
from app.services.idempotency_service import IdempotencyService


@pytest.mark.performance
class TestScheduleGenerationIdempotencyLoad:
    """Test schedule generation idempotency under concurrent load."""

    def test_schedule_generation_100_concurrent(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        100 concurrent identical schedule generation requests should create only 1 schedule run.

        Simulates network retry storm where same request is sent many times.
        Verifies:
        - Only one schedule run created
        - All responses return same run ID
        - Idempotency key prevents duplicates
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        # Same idempotency key for all requests (simulating retries)
        idempotency_key = f"schedule-gen-{uuid4()}"

        # Count schedule runs before
        initial_count = db.query(ScheduleRun).count()

        # Send 100 concurrent identical requests
        def make_request():
            return client.post(
                "/api/schedule/generate",
                json=schedule_data,
                headers={"Idempotency-Key": idempotency_key}
            )

        # Execute concurrently using thread pool (since TestClient is sync)
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            responses = [f.result() for f in futures]

        # All requests should succeed (200 or 207 for partial success)
        success_codes = [r.status_code for r in responses]
        assert all(code in [200, 207] for code in success_codes), \
            f"Some requests failed: {success_codes}"

        # All responses should return the same run ID
        run_ids = [r.json().get("run_id") for r in responses]
        unique_ids = set(run_ids)
        assert len(unique_ids) == 1, \
            f"Expected 1 unique run ID, got {len(unique_ids)}: {unique_ids}"

        # Database should have exactly 1 new schedule run
        final_count = db.query(ScheduleRun).count()
        assert final_count == initial_count + 1, \
            f"Expected 1 new schedule run, database has {final_count - initial_count}"

        # Verify idempotency record exists and is completed
        idem_record = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == idempotency_key
        ).first()
        assert idem_record is not None
        assert idem_record.is_completed

        # At least some responses should have X-Idempotency-Replayed header
        replayed_responses = [
            r for r in responses
            if r.headers.get("X-Idempotency-Replayed") == "true"
        ]
        # After the first request, all others should be replayed
        assert len(replayed_responses) >= 90, \
            f"Expected ~99 replayed responses, got {len(replayed_responses)}"

    def test_schedule_generation_network_retry_simulation(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        Simulate network retries for schedule generation with same idempotency key.

        Critical for data integrity - duplicate schedule generations could
        create conflicting assignments and violate ACGME compliance.
        """
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=6)

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        idempotency_key = f"schedule-retry-{uuid4()}"

        # Simulate network retry scenario:
        # Request 1: Initial request
        # Request 2-5: Retries due to timeout (same key)
        # Request 6-10: More retries from different connection

        responses = []

        # Initial request
        r1 = client.post(
            "/api/schedule/generate",
            json=schedule_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        responses.append(r1)
        assert r1.status_code in [200, 207]

        # Immediate retries (same connection)
        for _ in range(4):
            r = client.post(
                "/api/schedule/generate",
                json=schedule_data,
                headers={"Idempotency-Key": idempotency_key}
            )
            responses.append(r)
            assert r.status_code in [200, 207]
            # Should have replay header
            assert r.headers.get("X-Idempotency-Replayed") == "true"

        # Simulate different connection retrying (concurrent)
        from concurrent.futures import ThreadPoolExecutor

        def retry_request():
            return client.post(
                "/api/schedule/generate",
                json=schedule_data,
                headers={"Idempotency-Key": idempotency_key}
            )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(retry_request) for _ in range(5)]
            concurrent_responses = [f.result() for f in futures]
            responses.extend(concurrent_responses)

        # All requests should succeed
        assert all(r.status_code in [200, 207] for r in responses)

        # All should return same run ID
        run_ids = [r.json().get("run_id") for r in responses]
        assert len(set(run_ids)) == 1

        # Database should have exactly 1 schedule run
        schedule_runs = db.query(ScheduleRun).filter(
            ScheduleRun.start_date == start_date,
            ScheduleRun.end_date == end_date
        ).all()
        assert len(schedule_runs) == 1

    def test_schedule_generation_idempotency_key_isolation(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        Different idempotency keys should create different schedule runs.

        Verifies that idempotency keys properly isolate requests -
        different keys should result in different runs even if
        request parameters are identical.
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        # Create 3 schedule runs with different idempotency keys
        idempotency_keys = [f"schedule-{i}-{uuid4()}" for i in range(3)]

        responses = []
        for key in idempotency_keys:
            r = client.post(
                "/api/schedule/generate",
                json=schedule_data,
                headers={"Idempotency-Key": key}
            )
            responses.append(r)

        # All should succeed
        assert all(r.status_code in [200, 207] for r in responses)

        # All should have different run IDs
        run_ids = [r.json().get("run_id") for r in responses]
        assert len(set(run_ids)) == 3

        # Each idempotency key should have its own record
        for key in idempotency_keys:
            idem_record = db.query(IdempotencyRequest).filter(
                IdempotencyRequest.idempotency_key == key
            ).first()
            assert idem_record is not None
            assert idem_record.is_completed

    def test_schedule_generation_idempotency_conflict_detection(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        Same idempotency key with different request body should be rejected.

        Verifies that using the same key with different parameters
        triggers a conflict error (422).
        """
        start_date = date.today()
        idempotency_key = f"conflict-test-{uuid4()}"

        # First request: 7-day schedule
        first_request = {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=6)).isoformat(),
            "algorithm": "greedy",
        }

        r1 = client.post(
            "/api/schedule/generate",
            json=first_request,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert r1.status_code in [200, 207]

        # Second request: Same key, different end date (conflict!)
        second_request = {
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=13)).isoformat(),  # Different!
            "algorithm": "greedy",
        }

        r2 = client.post(
            "/api/schedule/generate",
            json=second_request,
            headers={"Idempotency-Key": idempotency_key}
        )

        # Should be rejected with 422 (conflict)
        assert r2.status_code == 422
        assert "different request parameters" in r2.json()["detail"].lower()

        # Only one schedule run should exist for this key
        idem_records = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == idempotency_key
        ).all()
        assert len(idem_records) == 1


@pytest.mark.performance
class TestIdempotencyExpiry:
    """Test idempotency key expiration behavior."""

    def test_schedule_generation_idempotency_expiry_allows_new_creation(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        Expired idempotency keys should allow new schedule generation.

        Simulates the scenario where the same idempotency key is reused
        after expiration (24 hours by default).
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        idempotency_key = f"expiry-test-{uuid4()}"

        # Create first schedule
        r1 = client.post(
            "/api/schedule/generate",
            json=schedule_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert r1.status_code in [200, 207]
        first_run_id = r1.json().get("run_id")

        # Manually expire the idempotency record
        idem_record = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == idempotency_key
        ).first()
        assert idem_record is not None

        # Set expiration to past
        idem_record.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()

        # Try to create another schedule with same key (should succeed after expiry)
        # Note: In production, you'd wait 24 hours. Here we manually expired it.
        # This simulates key reuse after natural expiration.

        # Modify data slightly to create different schedule
        schedule_data_2 = {
            "start_date": (start_date + timedelta(days=7)).isoformat(),
            "end_date": (start_date + timedelta(days=13)).isoformat(),
            "algorithm": "greedy",
        }

        r2 = client.post(
            "/api/schedule/generate",
            json=schedule_data_2,
            headers={"Idempotency-Key": idempotency_key}
        )

        # Should create a new schedule (idempotency key expired)
        assert r2.status_code in [200, 207]
        second_run_id = r2.json().get("run_id")

        # Should be different schedule runs
        assert first_run_id != second_run_id

        # Database should have 2 schedule runs
        schedule_runs = db.query(ScheduleRun).all()
        assert len(schedule_runs) >= 2

    def test_idempotency_cleanup_expired_records(self, db: Session):
        """
        Test cleanup of expired idempotency records.

        Verifies that the cleanup function properly removes expired records
        to prevent unbounded table growth.
        """
        service = IdempotencyService(db)

        # Create 10 expired records
        for i in range(10):
            request = IdempotencyRequest(
                idempotency_key=f"expired-{i}",
                body_hash=f"hash-{i}",
                status="completed",
                expires_at=datetime.utcnow() - timedelta(hours=1),
                request_params={}
            )
            db.add(request)

        # Create 5 active records
        for i in range(5):
            request = IdempotencyRequest(
                idempotency_key=f"active-{i}",
                body_hash=f"hash-active-{i}",
                status="completed",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                request_params={}
            )
            db.add(request)

        db.commit()

        # Verify initial counts
        total = db.query(IdempotencyRequest).count()
        assert total == 15

        # Run cleanup
        deleted_count = service.cleanup_expired(batch_size=100)

        # Should delete 10 expired records
        assert deleted_count == 10

        # Should have 5 active records remaining
        remaining = db.query(IdempotencyRequest).count()
        assert remaining == 5

        # All remaining should be active (not expired)
        active_records = db.query(IdempotencyRequest).all()
        for record in active_records:
            assert not record.is_expired


@pytest.mark.performance
class TestIdempotencyServiceConcurrency:
    """Test IdempotencyService under concurrent access."""

    def test_create_request_race_condition(self, db: Session):
        """
        Test concurrent create_request calls with same key+hash.

        Verifies that IntegrityError is handled gracefully when
        multiple threads try to create the same idempotency record.
        """
        service = IdempotencyService(db)

        idempotency_key = f"race-{uuid4()}"
        body_hash = "consistent-hash-123"
        request_params = {"test": "data"}

        created_requests = []

        def create_request():
            try:
                request = service.create_request(
                    idempotency_key=idempotency_key,
                    body_hash=body_hash,
                    request_params=request_params
                )
                db.commit()
                return request
            except Exception as e:
                db.rollback()
                # Try to get existing
                existing = service.get_existing_request(idempotency_key, body_hash)
                return existing

        # Simulate concurrent creation attempts
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed (either create or return existing)
        assert all(r is not None for r in results)

        # All should have same idempotency key
        assert all(r.idempotency_key == idempotency_key for r in results)

        # Database should have exactly 1 record
        records = db.query(IdempotencyRequest).filter(
            IdempotencyRequest.idempotency_key == idempotency_key
        ).all()
        assert len(records) == 1

    def test_concurrent_mark_completed(self, db: Session):
        """
        Test concurrent mark_completed calls on same request.

        Verifies that marking a request as completed is safe
        even when called concurrently.
        """
        service = IdempotencyService(db)

        # Create a pending request
        request = service.create_request(
            idempotency_key=f"complete-{uuid4()}",
            body_hash="hash-123",
            request_params={}
        )
        db.commit()
        db.refresh(request)

        assert request.is_pending

        result_ref = uuid4()
        response_body = {"status": "success", "id": str(result_ref)}

        def mark_complete():
            service.mark_completed(
                request,
                result_ref=result_ref,
                response_body=response_body,
                response_status_code=200
            )
            db.commit()

        # Concurrent completion attempts
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(mark_complete) for _ in range(5)]
            for f in futures:
                f.result()  # Wait for all to complete

        # Refresh from database
        db.refresh(request)

        # Should be completed
        assert request.is_completed
        assert request.result_ref == result_ref
        assert request.response_body == response_body
        assert request.completed_at is not None


@pytest.mark.performance
class TestIdempotencyHeaderPropagation:
    """Test that idempotency headers are properly propagated in responses."""

    def test_replayed_response_includes_header(
        self,
        client: TestClient,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
        sample_rotation_template: RotationTemplate,
    ):
        """
        Replayed idempotent responses should include X-Idempotency-Replayed header.

        Helps clients distinguish between new schedule generations and cached responses.
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        schedule_data = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
        }

        idempotency_key = f"replay-header-{uuid4()}"

        # First request (original)
        r1 = client.post(
            "/api/schedule/generate",
            json=schedule_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert r1.status_code in [200, 207]

        # Should NOT have replay header (or it should be "false")
        assert "X-Idempotency-Replayed" not in r1.headers or \
               r1.headers.get("X-Idempotency-Replayed") == "false"

        # Second request (replayed)
        r2 = client.post(
            "/api/schedule/generate",
            json=schedule_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        assert r2.status_code in [200, 207]

        # Should have replay header
        assert r2.headers.get("X-Idempotency-Replayed") == "true"

        # Should return same run ID
        assert r1.json().get("run_id") == r2.json().get("run_id")
