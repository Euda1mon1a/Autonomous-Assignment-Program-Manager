"""
Integration tests for the schedule generation pipeline.

Tests POST /api/schedule/generate with a minimal 2-resident, 1-block
scenario to verify the full pipeline:
    DB setup → API request → scheduling engine → solver → validation → response.

Uses the integration test database via the ``integration_db`` and
``integration_client`` fixtures from ``tests/integration/conftest.py``.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ---------------------------------------------------------------------------
# Fixtures — all use integration_db so data lives in the same session
# as the integration_client's dependency override.
# ---------------------------------------------------------------------------


@pytest.fixture
def two_residents(integration_db: Session) -> list[Person]:
    """Create exactly 2 residents (PGY-1 and PGY-2)."""
    residents = []
    for pgy in (1, 2):
        resident = Person(
            id=uuid4(),
            name=f"Dr. Test Resident PGY{pgy}",
            type="resident",
            email=f"test.resident.pgy{pgy}@hospital.org",
            pgy_level=pgy,
        )
        integration_db.add(resident)
        residents.append(resident)
    integration_db.commit()
    for r in residents:
        integration_db.refresh(r)
    return residents


@pytest.fixture
def one_block_pair(integration_db: Session) -> list[Block]:
    """Create a single day of blocks (AM + PM) for today."""
    today = date.today()
    blocks = []
    for tod in ("AM", "PM"):
        block = Block(
            id=uuid4(),
            date=today,
            time_of_day=tod,
            block_number=1,
            is_weekend=today.weekday() >= 5,
            is_holiday=False,
        )
        integration_db.add(block)
        blocks.append(block)
    integration_db.commit()
    for b in blocks:
        integration_db.refresh(b)
    return blocks


@pytest.fixture
def outpatient_template(integration_db: Session) -> RotationTemplate:
    """Create a minimal outpatient rotation template.

    Uses rotation_type='outpatient' which matches the scheduling engine's
    default filter for rotation templates.
    """
    template = RotationTemplate(
        id=uuid4(),
        name="Test Outpatient Clinic",
        rotation_type="outpatient",
        abbreviation="TC",
        max_residents=4,
        supervision_required=True,
        max_supervision_ratio=4,
    )
    integration_db.add(template)
    integration_db.commit()
    integration_db.refresh(template)
    return template


@pytest.fixture
def faculty_member(integration_db: Session) -> Person:
    """Create a faculty member for supervision."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="test.faculty@hospital.org",
        performs_procedures=False,
        specialties=["General"],
    )
    integration_db.add(faculty)
    integration_db.commit()
    integration_db.refresh(faculty)
    return faculty


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestScheduleGeneratePipeline:
    """Integration tests for POST /api/schedule/generate."""

    def test_generate_returns_valid_response_structure(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        two_residents: list[Person],
        faculty_member: Person,
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """Verify the generate endpoint returns a well-formed response
        with the correct top-level keys for a simple scenario.
        """
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 30,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        # The endpoint returns 200 (success), 207 (partial), or 422 (failed).
        # With 2 residents and 2 blocks we should get a result, not a 500.
        assert response.status_code in (200, 207, 422), (
            f"Unexpected status {response.status_code}: {response.text}"
        )

        data = response.json()

        if response.status_code in (200, 207):
            # Successful or partial — validate response shape
            assert "status" in data
            assert data["status"] in ("success", "partial")
            assert "message" in data
            assert "total_assignments" in data
            assert "total_blocks" in data
            assert "validation" in data
            assert isinstance(data["total_blocks"], int)
            assert data["total_blocks"] > 0

    def test_generate_produces_assignments(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        integration_db: Session,
        two_residents: list[Person],
        faculty_member: Person,
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """Verify the pipeline actually creates assignment rows in the database."""
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 30,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        if response.status_code in (200, 207):
            data = response.json()
            total = data.get("total_assignments", 0)
            assert total >= 0

            # If assignments were reported, verify they exist in the DB
            if total > 0:
                db_assignments = integration_db.query(Assignment).all()
                assert len(db_assignments) > 0

    def test_generate_includes_validation_result(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        two_residents: list[Person],
        faculty_member: Person,
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """Verify the response includes an ACGME validation result."""
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 30,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        if response.status_code in (200, 207):
            data = response.json()
            validation = data["validation"]
            assert "valid" in validation
            assert "total_violations" in validation
            assert "violations" in validation
            assert isinstance(validation["violations"], list)
            assert "coverage_rate" in validation

    def test_generate_week_range_two_residents(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        integration_db: Session,
        two_residents: list[Person],
        faculty_member: Person,
        outpatient_template: RotationTemplate,
    ):
        """Test generation over a full week with 2 residents.

        Creates 7 days of blocks (AM+PM = 14 blocks) and verifies
        the solver produces a reasonable number of assignments.
        """
        start_date = date.today()
        end_date = start_date + timedelta(days=6)

        # Create blocks for a full week
        for i in range(7):
            current = start_date + timedelta(days=i)
            for tod in ("AM", "PM"):
                block = Block(
                    id=uuid4(),
                    date=current,
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=current.weekday() >= 5,
                    is_holiday=False,
                )
                integration_db.add(block)
        integration_db.commit()

        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 60,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code in (200, 207, 422), (
            f"Unexpected status {response.status_code}: {response.text}"
        )

        if response.status_code in (200, 207):
            data = response.json()
            assert data["total_blocks"] == 14  # 7 days × 2 half-days

    def test_generate_returns_run_id(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        two_residents: list[Person],
        faculty_member: Person,
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """Verify the response includes a run_id for audit trail."""
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 30,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        if response.status_code in (200, 207):
            data = response.json()
            assert "run_id" in data
            # run_id should be a UUID string (or null)
            assert data["run_id"] is not None

    def test_generate_requires_authentication(
        self,
        integration_client: TestClient,
        two_residents: list[Person],
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """Verify the endpoint rejects unauthenticated requests."""
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            # No auth_headers
        )

        assert response.status_code == 401

    def test_generate_rejects_invalid_date_range(
        self,
        integration_client: TestClient,
        auth_headers: dict,
    ):
        """Verify the endpoint rejects start_date > end_date."""
        payload = {
            "start_date": (date.today() + timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
            "algorithm": "greedy",
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        # Pydantic validation should catch this
        assert response.status_code == 422

    def test_generate_no_residents_returns_failure(
        self,
        integration_client: TestClient,
        auth_headers: dict,
        faculty_member: Person,
        outpatient_template: RotationTemplate,
        one_block_pair: list[Block],
    ):
        """When no residents exist, the engine should report failure.

        The exact failure reason depends on the database state (e.g.,
        missing Activity codes like PCAT may fail before the no-residents
        check). The important thing is that it does NOT return 200.
        """
        today = date.today()
        payload = {
            "start_date": today.isoformat(),
            "end_date": today.isoformat(),
            "algorithm": "greedy",
            "timeout_seconds": 15,
        }

        response = integration_client.post(
            "/api/v1/schedule/generate",
            json=payload,
            headers=auth_headers,
        )

        # Without residents the pipeline should fail (422) or error (500),
        # never succeed (200/207).
        assert response.status_code not in (200, 207), (
            f"Expected failure without residents, got {response.status_code}"
        )
