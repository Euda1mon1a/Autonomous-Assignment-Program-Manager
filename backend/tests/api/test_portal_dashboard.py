"""Tests for portal dashboard API."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User

# =============================================================================
# Helper Functions for Dashboard Queries
# =============================================================================


async def get_faculty_week_counts(
    db: Session, faculty_id: str, academic_year_start: date
) -> dict:
    """
    Calculate week counts for faculty member.

    Args:
        db: Database session
        faculty_id: Faculty person ID
        academic_year_start: Start date of academic year

    Returns:
        dict: Contains weeks_assigned, weeks_completed, weeks_remaining
    """
    from sqlalchemy import func

    # Get FMIT rotation template
    fmit_template = (
        db.query(RotationTemplate).filter(RotationTemplate.name == "FMIT").first()
    )

    if not fmit_template:
        return {"weeks_assigned": 0, "weeks_completed": 0, "weeks_remaining": 0}

    # Count total weeks assigned (grouped by week)
    # This is a simplified count - in reality would group by week_start
    total_weeks = (
        db.query(func.count(Assignment.id))
        .filter(
            Assignment.person_id == faculty_id,
            Assignment.rotation_template_id == fmit_template.id,
        )
        .scalar()
        or 0
    )

    # For simplicity, count weeks by dividing by sessions per week (14 = 7 days * 2 sessions)
    weeks_assigned = total_weeks // 14 if total_weeks > 0 else 0

    # Count completed weeks (before today)
    today = date.today()
    completed_count = (
        db.query(func.count(Assignment.id))
        .join(Block, Assignment.block_id == Block.id)
        .filter(
            Assignment.person_id == faculty_id,
            Assignment.rotation_template_id == fmit_template.id,
            Block.date < today,
        )
        .scalar()
        or 0
    )

    weeks_completed = completed_count // 14 if completed_count > 0 else 0
    weeks_remaining = max(0, weeks_assigned - weeks_completed)

    return {
        "weeks_assigned": weeks_assigned,
        "weeks_completed": weeks_completed,
        "weeks_remaining": weeks_remaining,
    }


async def get_upcoming_weeks(
    db: Session, faculty_id: str, limit: int = 4
) -> list[dict]:
    """
    Get upcoming FMIT weeks for faculty member.

    Args:
        db: Database session
        faculty_id: Faculty person ID
        limit: Number of upcoming weeks to return

    Returns:
        list: List of upcoming week info dicts
    """
    from collections import defaultdict

    # Get FMIT rotation template
    fmit_template = (
        db.query(RotationTemplate).filter(RotationTemplate.name == "FMIT").first()
    )

    if not fmit_template:
        return []

    # Get future assignments
    today = date.today()
    assignments = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .filter(
            Assignment.person_id == faculty_id,
            Assignment.rotation_template_id == fmit_template.id,
            Block.date >= today,
        )
        .order_by(Block.date)
        .limit(limit * 14)
        .all()
    )  # Rough limit

    # Group by week
    week_map = defaultdict(list)
    for assignment in assignments:
        # Get Monday of the week
        days_since_monday = assignment.block.date.weekday()
        week_start = assignment.block.date - timedelta(days=days_since_monday)
        week_map[week_start].append(assignment)

    # Convert to list and limit
    upcoming = []
    for week_start in sorted(week_map.keys())[:limit]:
        week_end = week_start + timedelta(days=6)
        upcoming.append(
            {
                "week_start": week_start,
                "week_end": week_end,
                "session_count": len(week_map[week_start]),
            }
        )

    return upcoming


async def get_recent_alerts(db: Session, faculty_id: str, days: int = 30) -> list[dict]:
    """
    Get recent conflict alerts for faculty member.

    Args:
        db: Database session
        faculty_id: Faculty person ID
        days: Number of days to look back

    Returns:
        list: List of recent alert info dicts
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    alerts = (
        db.query(ConflictAlert)
        .filter(
            ConflictAlert.faculty_id == faculty_id,
            ConflictAlert.created_at >= cutoff_date,
        )
        .order_by(ConflictAlert.created_at.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": str(alert.id),
            "description": alert.description,
            "status": alert.status.value,
            "created_at": alert.created_at,
            "fmit_week": alert.fmit_week,
        }
        for alert in alerts
    ]


async def get_pending_swaps(db: Session, faculty_id: str) -> list[dict]:
    """
    Get pending swap requests requiring response.

    Args:
        db: Database session
        faculty_id: Faculty person ID

    Returns:
        list: List of pending swap info dicts
    """
    swaps = (
        db.query(SwapRecord)
        .filter(
            SwapRecord.target_faculty_id == faculty_id,
            SwapRecord.status == SwapStatus.PENDING,
        )
        .order_by(SwapRecord.requested_at.desc())
        .all()
    )

    return [
        {
            "id": str(swap.id),
            "source_week": swap.source_week,
            "requested_at": swap.requested_at,
            "requester_name": (
                swap.source_faculty.name if swap.source_faculty else "Unknown"
            ),
        }
        for swap in swaps
    ]


# =============================================================================
# Dashboard Query Tests
# =============================================================================


class TestDashboardQueries:
    """Tests for dashboard data queries."""

    @pytest.mark.asyncio
    async def test_get_faculty_week_counts_no_template(self, db):
        """Test week count calculation with no FMIT template."""
        faculty_id = str(uuid4())

        result = await get_faculty_week_counts(
            db=db, faculty_id=faculty_id, academic_year_start=date(2025, 7, 1)
        )

        assert result["weeks_assigned"] == 0
        assert result["weeks_completed"] == 0
        assert result["weeks_remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_faculty_week_counts_with_assignments(self, db, sample_faculty):
        """Test week count calculation with assignments."""
        # Create FMIT template
        fmit_template = RotationTemplate(
            id=uuid4(), name="FMIT", rotation_type="clinic", abbreviation="FMIT"
        )
        db.add(fmit_template)
        db.commit()

        # Create blocks for 2 weeks (14 days * 2 sessions = 28 blocks)
        blocks = []
        start_date = date(2025, 6, 1)
        for i in range(14):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)
        db.commit()

        # Create assignments
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                person_id=sample_faculty.id,
                block_id=block.id,
                rotation_template_id=fmit_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = await get_faculty_week_counts(
            db=db,
            faculty_id=str(sample_faculty.id),
            academic_year_start=date(2025, 7, 1),
        )

        assert result["weeks_assigned"] == 2  # 28 blocks / 14 = 2 weeks
        assert "weeks_completed" in result
        assert "weeks_remaining" in result

    @pytest.mark.asyncio
    async def test_get_upcoming_weeks_empty(self, db, sample_faculty):
        """Test upcoming weeks with no data."""
        result = await get_upcoming_weeks(db=db, faculty_id=str(sample_faculty.id))

        assert result == []

    @pytest.mark.asyncio
    async def test_get_upcoming_weeks_with_data(self, db, sample_faculty):
        """Test upcoming weeks with future assignments."""
        # Create FMIT template
        fmit_template = RotationTemplate(
            id=uuid4(), name="FMIT", rotation_type="clinic", abbreviation="FMIT"
        )
        db.add(fmit_template)
        db.commit()

        # Create future blocks (next week)
        start_date = date.today() + timedelta(days=7)
        blocks = []
        for i in range(7):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)
        db.commit()

        # Create assignments
        for block in blocks:
            assignment = Assignment(
                id=uuid4(),
                person_id=sample_faculty.id,
                block_id=block.id,
                rotation_template_id=fmit_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = await get_upcoming_weeks(
            db=db, faculty_id=str(sample_faculty.id), limit=4
        )

        assert len(result) > 0
        assert "week_start" in result[0]
        assert "week_end" in result[0]
        assert "session_count" in result[0]

    @pytest.mark.asyncio
    async def test_get_recent_alerts_empty(self, db, sample_faculty):
        """Test recent alerts query with no alerts."""
        result = await get_recent_alerts(db=db, faculty_id=str(sample_faculty.id))

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_recent_alerts_with_data(self, db, sample_faculty):
        """Test recent alerts query with alerts."""
        # Create conflict alerts
        for i in range(3):
            alert = ConflictAlert(
                id=uuid4(),
                faculty_id=sample_faculty.id,
                fmit_week=date.today() + timedelta(days=7 * i),
                description=f"Test conflict {i}",
                status=ConflictAlertStatus.NEW,
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            db.add(alert)
        db.commit()

        result = await get_recent_alerts(
            db=db, faculty_id=str(sample_faculty.id), days=30
        )

        assert isinstance(result, list)
        assert len(result) == 3
        assert "id" in result[0]
        assert "description" in result[0]
        assert "status" in result[0]

    @pytest.mark.asyncio
    async def test_get_pending_swaps_empty(self, db, sample_faculty):
        """Test pending swaps query with no swaps."""
        result = await get_pending_swaps(db=db, faculty_id=str(sample_faculty.id))

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_pending_swaps_with_data(
        self, db, sample_faculty, sample_faculty_members
    ):
        """Test pending swaps query with pending swaps."""
        # Create swap requests targeting this faculty
        for i, other_faculty in enumerate(sample_faculty_members[:2]):
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=other_faculty.id,
                target_faculty_id=sample_faculty.id,
                source_week=date.today() + timedelta(days=7 * i),
                target_week=None,
                swap_type=SwapType.ABSORB,
                status=SwapStatus.PENDING,
                requested_at=datetime.utcnow() - timedelta(hours=i),
                reason=f"Need coverage {i}",
            )
            db.add(swap)
        db.commit()

        result = await get_pending_swaps(db=db, faculty_id=str(sample_faculty.id))

        assert isinstance(result, list)
        assert len(result) == 2
        assert "id" in result[0]
        assert "source_week" in result[0]
        assert "requested_at" in result[0]


# =============================================================================
# Dashboard Endpoint Tests
# =============================================================================


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    def test_get_dashboard_requires_auth(self, client: TestClient):
        """Test dashboard endpoint requires authentication."""
        response = client.get("/api/portal/my/dashboard")

        assert response.status_code == 401

    def test_get_dashboard_requires_faculty_profile(
        self, client: TestClient, admin_user: User, auth_headers: dict
    ):
        """Test dashboard requires linked faculty profile."""
        response = client.get("/api/portal/my/dashboard", headers=auth_headers)

        # Should return 403 if no faculty profile linked
        assert response.status_code == 403
        assert "No faculty profile" in response.json()["detail"]

    def test_get_dashboard_success(
        self, client: TestClient, db: Session, auth_headers: dict, admin_user: User
    ):
        """Test successful dashboard retrieval."""
        # Create faculty profile linked to admin user
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            type="faculty",
            email=admin_user.email,  # Link by email
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()

        response = client.get("/api/portal/my/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "faculty_id" in data
        assert "faculty_name" in data
        assert "stats" in data
        assert "upcoming_weeks" in data
        assert "recent_alerts" in data
        assert "pending_swap_decisions" in data

        # Verify stats structure
        stats = data["stats"]
        assert "weeks_assigned" in stats
        assert "weeks_completed" in stats
        assert "weeks_remaining" in stats
        assert "target_weeks" in stats
        assert "pending_swap_requests" in stats
        assert "unread_alerts" in stats

    def test_get_dashboard_with_data(
        self, client: TestClient, db: Session, auth_headers: dict, admin_user: User
    ):
        """Test dashboard with actual data."""
        # Create faculty profile
        faculty = Person(
            id=uuid4(),
            name="Dr. Test Faculty",
            type="faculty",
            email=admin_user.email,
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()

        # Create FMIT template
        fmit_template = RotationTemplate(
            id=uuid4(), name="FMIT", rotation_type="clinic", abbreviation="FMIT"
        )
        db.add(fmit_template)
        db.commit()

        # Create some assignments
        start_date = date.today() + timedelta(days=7)
        for i in range(7):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.flush()

                assignment = Assignment(
                    id=uuid4(),
                    person_id=faculty.id,
                    block_id=block.id,
                    rotation_template_id=fmit_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        response = client.get("/api/portal/my/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify faculty info
        assert data["faculty_name"] == "Dr. Test Faculty"


# =============================================================================
# Integration Tests
# =============================================================================


class TestDashboardIntegration:
    """Integration tests for dashboard functionality."""

    def test_full_dashboard_workflow(
        self, client: TestClient, db: Session, auth_headers: dict, admin_user: User
    ):
        """Test complete dashboard workflow with all components."""
        # Setup: Create faculty profile
        faculty = Person(
            id=uuid4(),
            name="Dr. Integration Test",
            type="faculty",
            email=admin_user.email,
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()

        # Create FMIT template
        fmit_template = RotationTemplate(
            id=uuid4(), name="FMIT", rotation_type="clinic", abbreviation="FMIT"
        )
        db.add(fmit_template)
        db.commit()

        # Create assignments
        start_date = date.today() + timedelta(days=14)
        for i in range(7):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.flush()

                assignment = Assignment(
                    id=uuid4(),
                    person_id=faculty.id,
                    block_id=block.id,
                    rotation_template_id=fmit_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Create conflict alert
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            fmit_week=start_date,
            description="Test conflict",
            status=ConflictAlertStatus.NEW,
            created_at=datetime.utcnow(),
        )
        db.add(alert)
        db.commit()

        # Get dashboard
        response = client.get("/api/portal/my/dashboard", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify all components present
        assert data["faculty_name"] == "Dr. Integration Test"
        assert isinstance(data["stats"], dict)
        assert isinstance(data["upcoming_weeks"], list)
        assert isinstance(data["recent_alerts"], list)
        assert isinstance(data["pending_swap_decisions"], list)
