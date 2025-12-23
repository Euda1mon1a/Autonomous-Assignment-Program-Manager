"""Comprehensive tests for /api/me/dashboard endpoint."""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def person_with_user(db: Session) -> tuple[Person, User]:
    """Create a person and matching user account."""
    person = Person(
        id=uuid4(),
        name="Dr. Test User",
        type="resident",
        email="testuser@hospital.org",
        pgy_level=3,
    )
    db.add(person)

    user = User(
        id=uuid4(),
        username="testuser",
        email="testuser@hospital.org",  # Match person email
        hashed_password=get_password_hash("testpass123"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(person)
    db.refresh(user)
    return person, user


@pytest.fixture
def user_auth_headers(
    client: TestClient, person_with_user: tuple[Person, User]
) -> dict:
    """Get authentication headers for user with person profile."""
    _, user = person_with_user
    response = client.post(
        "/api/auth/login/json",
        json={"username": "testuser", "password": "testpass123"},
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def faculty_person_with_user(db: Session) -> tuple[Person, User]:
    """Create a faculty person and matching user account."""
    person = Person(
        id=uuid4(),
        name="Dr. Faculty User",
        type="faculty",
        email="faculty@hospital.org",
        performs_procedures=True,
        specialties=["Sports Medicine"],
    )
    db.add(person)

    user = User(
        id=uuid4(),
        username="facultyuser",
        email="faculty@hospital.org",  # Match person email
        hashed_password=get_password_hash("testpass123"),
        role="faculty",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(person)
    db.refresh(user)
    return person, user


@pytest.fixture
def future_blocks(db: Session) -> list[Block]:
    """Create blocks for the next 60 days."""
    blocks = []
    start_date = date.today()

    for i in range(60):
        current_date = start_date + timedelta(days=i)
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

    db.commit()
    for b in blocks:
        db.refresh(b)
    return blocks


@pytest.fixture
def rotation_templates(db: Session) -> list[RotationTemplate]:
    """Create sample rotation templates."""
    templates = [
        RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Clinic",
            activity_type="clinic",
            abbreviation="SM",
            clinic_location="Building A, Room 101",
            max_residents=4,
        ),
        RotationTemplate(
            id=uuid4(),
            name="General Medicine",
            activity_type="clinic",
            abbreviation="GM",
            clinic_location="Building B",
            max_residents=6,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Admin Time",
            activity_type="admin",
            abbreviation="ADM",
            clinic_location=None,  # No location
            max_residents=10,
        ),
    ]
    for template in templates:
        db.add(template)
    db.commit()
    for t in templates:
        db.refresh(t)
    return templates


# ============================================================================
# Success Scenarios
# ============================================================================


class TestDashboardSuccess:
    """Tests for successful dashboard retrieval scenarios."""

    def test_get_dashboard_basic(
        self,
        client: TestClient,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test basic dashboard retrieval returns correct structure."""
        person, _ = person_with_user

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check main structure
        assert "user" in data
        assert "upcoming_schedule" in data
        assert "pending_swaps" in data
        assert "absences" in data
        assert "calendar_sync_url" in data
        assert "summary" in data

        # Check user info
        assert data["user"]["id"] == str(person.id)
        assert data["user"]["name"] == person.name
        assert data["user"]["role"] == person.type
        assert data["user"]["email"] == person.email
        assert data["user"]["pgy_level"] == person.pgy_level

    def test_get_dashboard_with_schedule(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test dashboard with upcoming schedule items."""
        person, _ = person_with_user

        # Create assignments for the next week
        for i in range(5):  # 5 days
            block = future_blocks[i * 2]  # AM blocks
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation_templates[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 5 schedule items
        assert len(data["upcoming_schedule"]) == 5

        # Check first schedule item structure
        schedule_item = data["upcoming_schedule"][0]
        assert "date" in schedule_item
        assert "time_of_day" in schedule_item
        assert "activity" in schedule_item
        assert "location" in schedule_item
        assert "can_trade" in schedule_item
        assert "role" in schedule_item
        assert "assignment_id" in schedule_item

        # Check specific values
        assert schedule_item["time_of_day"] == "AM"
        assert schedule_item["role"] == "primary"
        assert schedule_item["can_trade"] is True
        assert schedule_item["location"] == rotation_templates[0].clinic_location

    def test_get_dashboard_with_pending_swaps(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty: Person,
    ):
        """Test dashboard with pending swap requests."""
        person, user = person_with_user

        # Create pending swaps where person is source
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=person.id,
            target_faculty_id=sample_faculty.id,
            source_week=date.today() + timedelta(days=14),
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )

        # Create another swap where person is target
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty.id,
            target_faculty_id=person.id,
            source_week=date.today() + timedelta(days=28),
            target_week=date.today() + timedelta(days=35),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow() - timedelta(hours=2),
        )

        db.add(swap1)
        db.add(swap2)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 2 pending swaps
        assert len(data["pending_swaps"]) == 2

        # Check swap structure
        swap_item = data["pending_swaps"][0]
        assert "swap_id" in swap_item
        assert "swap_type" in swap_item
        assert "status" in swap_item
        assert "source_week" in swap_item
        assert "target_week" in swap_item
        assert "other_party_name" in swap_item
        assert "requested_at" in swap_item

        # Check other_party_name is correct
        assert sample_faculty.name in [
            s["other_party_name"] for s in data["pending_swaps"]
        ]

    def test_get_dashboard_with_absences(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test dashboard with upcoming absences."""
        person, _ = person_with_user

        # Create future absence
        absence1 = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=14),
            absence_type="vacation",
            notes="Annual leave",
        )

        # Create another future absence
        absence2 = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=32),
            absence_type="conference",
            notes="Medical conference",
        )

        db.add(absence1)
        db.add(absence2)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 2 absences
        assert len(data["absences"]) == 2

        # Check absence structure
        absence_item = data["absences"][0]
        assert "absence_id" in absence_item
        assert "start_date" in absence_item
        assert "end_date" in absence_item
        assert "absence_type" in absence_item
        assert "notes" in absence_item

    def test_get_dashboard_past_absences_excluded(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test that past absences are not included in dashboard."""
        person, _ = person_with_user

        # Create past absence
        past_absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() - timedelta(days=14),
            absence_type="vacation",
            notes="Past vacation",
        )

        # Create current absence (ends today)
        current_absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
            absence_type="sick",
            notes="Sick leave",
        )

        db.add(past_absence)
        db.add(current_absence)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only have the current absence (ends today)
        assert len(data["absences"]) == 1
        assert data["absences"][0]["notes"] == "Sick leave"

    def test_get_dashboard_with_calendar_sync(
        self,
        client: TestClient,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test dashboard includes calendar sync URL."""
        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Calendar sync URL should be present (or None if service fails)
        assert "calendar_sync_url" in data
        # URL should be a string or None
        assert data["calendar_sync_url"] is None or isinstance(
            data["calendar_sync_url"], str
        )

    @patch("app.api.routes.me_dashboard.CalendarService.create_subscription")
    @patch("app.api.routes.me_dashboard.CalendarService.list_subscriptions")
    @patch("app.api.routes.me_dashboard.CalendarService.generate_subscription_url")
    def test_get_dashboard_calendar_sync_creates_subscription(
        self,
        mock_generate_url: MagicMock,
        mock_list: MagicMock,
        mock_create: MagicMock,
        client: TestClient,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test calendar sync URL is generated from new subscription."""
        person, user = person_with_user

        # Mock no existing subscriptions
        mock_list.return_value = []

        # Mock created subscription
        mock_subscription = MagicMock()
        mock_subscription.token = "test-token-123"
        mock_create.return_value = mock_subscription

        # Mock URL generation
        mock_generate_url.return_value = (
            "https://example.com/api/calendar/test-token-123"
        )

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify subscription was created
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["person_id"] == person.id
        assert call_kwargs["created_by_user_id"] == user.id
        assert call_kwargs["expires_days"] == 365

        # Verify URL was generated
        assert (
            data["calendar_sync_url"]
            == "https://example.com/api/calendar/test-token-123"
        )

    @patch("app.api.routes.me_dashboard.CalendarService.create_subscription")
    @patch("app.api.routes.me_dashboard.CalendarService.list_subscriptions")
    @patch("app.api.routes.me_dashboard.CalendarService.generate_subscription_url")
    def test_get_dashboard_calendar_sync_uses_existing(
        self,
        mock_generate_url: MagicMock,
        mock_list: MagicMock,
        mock_create: MagicMock,
        client: TestClient,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test calendar sync uses existing subscription."""
        # Mock existing subscription
        mock_subscription = MagicMock()
        mock_subscription.token = "existing-token"
        mock_list.return_value = [mock_subscription]

        # Mock URL generation
        mock_generate_url.return_value = (
            "https://example.com/api/calendar/existing-token"
        )

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify no new subscription was created
        mock_create.assert_not_called()

        # Verify URL was generated with existing token
        assert (
            data["calendar_sync_url"]
            == "https://example.com/api/calendar/existing-token"
        )

    @patch("app.api.routes.me_dashboard.CalendarService.create_subscription")
    def test_get_dashboard_calendar_sync_failure_continues(
        self,
        mock_create: MagicMock,
        client: TestClient,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test dashboard continues even if calendar sync fails."""
        # Mock calendar service failure
        mock_create.side_effect = Exception("Calendar service unavailable")

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Calendar sync URL should be None
        assert data["calendar_sync_url"] is None

        # Other data should still be present
        assert "user" in data
        assert "upcoming_schedule" in data
        assert "summary" in data

    def test_get_dashboard_with_full_data(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
        sample_faculty: Person,
    ):
        """Test dashboard with all sections fully populated."""
        person, _ = person_with_user

        # Add schedule assignments
        for i in range(10):
            assignment = Assignment(
                id=uuid4(),
                block_id=future_blocks[i].id,
                person_id=person.id,
                rotation_template_id=rotation_templates[i % len(rotation_templates)].id,
                role="primary" if i % 2 == 0 else "backup",
            )
            db.add(assignment)

        # Add pending swaps
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=person.id,
            target_faculty_id=sample_faculty.id,
            source_week=date.today() + timedelta(days=14),
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap)

        # Add absences
        absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            absence_type="vacation",
        )
        db.add(absence)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all sections have data
        assert len(data["upcoming_schedule"]) == 10
        assert len(data["pending_swaps"]) == 1
        assert len(data["absences"]) == 1
        assert data["summary"]["workload_next_4_weeks"] > 0
        assert data["summary"]["pending_swap_count"] == 1
        assert data["summary"]["upcoming_absences_count"] == 1


# ============================================================================
# Query Parameters
# ============================================================================


class TestDashboardQueryParameters:
    """Tests for dashboard query parameters."""

    def test_get_dashboard_default_days_ahead(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard uses default 30 days ahead."""
        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        # Default is 30 days, should work without parameter

    def test_get_dashboard_custom_days_ahead(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test dashboard with custom days_ahead parameter."""
        person, _ = person_with_user

        # Create assignments spread across 50 days
        for i in range(0, 50, 5):
            if i < len(future_blocks):
                assignment = Assignment(
                    id=uuid4(),
                    block_id=future_blocks[i].id,
                    person_id=person.id,
                    rotation_template_id=rotation_templates[0].id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Request only 7 days ahead
        response = client.get(
            "/api/me/dashboard?days_ahead=7",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include assignments within 7 days
        for item in data["upcoming_schedule"]:
            item_date = date.fromisoformat(item["date"])
            assert item_date <= date.today() + timedelta(days=7)

    def test_get_dashboard_max_days_ahead(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard with maximum days_ahead (365)."""
        response = client.get(
            "/api/me/dashboard?days_ahead=365",
            headers=user_auth_headers,
        )

        assert response.status_code == 200

    def test_get_dashboard_days_ahead_too_large(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard rejects days_ahead > 365."""
        response = client.get(
            "/api/me/dashboard?days_ahead=400",
            headers=user_auth_headers,
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get_dashboard_days_ahead_too_small(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard rejects days_ahead < 1."""
        response = client.get(
            "/api/me/dashboard?days_ahead=0",
            headers=user_auth_headers,
        )

        # Should return validation error
        assert response.status_code == 422

    def test_get_dashboard_days_ahead_negative(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard rejects negative days_ahead."""
        response = client.get(
            "/api/me/dashboard?days_ahead=-10",
            headers=user_auth_headers,
        )

        # Should return validation error
        assert response.status_code == 422


# ============================================================================
# Summary Statistics
# ============================================================================


class TestDashboardSummary:
    """Tests for dashboard summary statistics."""

    def test_dashboard_summary_next_assignment(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test next_assignment is calculated correctly."""
        person, _ = person_with_user

        # Create assignment 5 days from now
        future_date = date.today() + timedelta(days=5)
        future_block = [
            b for b in future_blocks if b.date == future_date and b.time_of_day == "AM"
        ][0]

        assignment = Assignment(
            id=uuid4(),
            block_id=future_block.id,
            person_id=person.id,
            rotation_template_id=rotation_templates[0].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Next assignment should be the one we created
        assert data["summary"]["next_assignment"] == future_date.isoformat()

    def test_dashboard_summary_workload_calculation(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test workload_next_4_weeks counts blocks correctly."""
        person, _ = person_with_user

        # Create assignments within 4 weeks
        four_weeks = date.today() + timedelta(weeks=4)
        count_within_4_weeks = 0

        for i in range(60):
            block = future_blocks[i]
            if block.date <= four_weeks:
                count_within_4_weeks += 1
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=person.id,
                    rotation_template_id=rotation_templates[0].id,
                    role="primary",
                )
                db.add(assignment)
            else:
                # Also add some beyond 4 weeks
                if i < 80:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=person.id,
                        rotation_template_id=rotation_templates[0].id,
                        role="primary",
                    )
                    db.add(assignment)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Workload should only count blocks within 4 weeks
        assert data["summary"]["workload_next_4_weeks"] == count_within_4_weeks

    def test_dashboard_summary_pending_swap_count(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty_members: list[Person],
    ):
        """Test pending_swap_count is accurate."""
        person, _ = person_with_user

        # Create multiple pending swaps
        for i in range(3):
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=person.id,
                target_faculty_id=sample_faculty_members[
                    i % len(sample_faculty_members)
                ].id,
                source_week=date.today() + timedelta(days=14 + i * 7),
                target_week=date.today() + timedelta(days=21 + i * 7),
                swap_type=SwapType.ONE_TO_ONE,
                status=SwapStatus.PENDING,
                requested_at=datetime.utcnow(),
            )
            db.add(swap)

        # Create an approved swap (should not be counted)
        approved_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=person.id,
            target_faculty_id=sample_faculty_members[0].id,
            source_week=date.today() + timedelta(days=42),
            target_week=date.today() + timedelta(days=49),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
            requested_at=datetime.utcnow(),
        )
        db.add(approved_swap)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only count pending swaps
        assert data["summary"]["pending_swap_count"] == 3

    def test_dashboard_summary_absences_count(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
    ):
        """Test upcoming_absences_count is accurate."""
        person, _ = person_with_user

        # Create future absences
        for i in range(2):
            absence = Absence(
                id=uuid4(),
                person_id=person.id,
                start_date=date.today() + timedelta(days=10 + i * 20),
                end_date=date.today() + timedelta(days=14 + i * 20),
                absence_type="vacation",
            )
            db.add(absence)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["upcoming_absences_count"] == 2

    def test_dashboard_summary_empty_schedule(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test summary with no schedule shows correct defaults."""
        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["summary"]["next_assignment"] is None
        assert data["summary"]["workload_next_4_weeks"] == 0
        assert data["summary"]["pending_swap_count"] == 0
        assert data["summary"]["upcoming_absences_count"] == 0


# ============================================================================
# Schedule Item Details
# ============================================================================


class TestDashboardScheduleDetails:
    """Tests for schedule item details and transformations."""

    def test_schedule_can_trade_primary_role(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test primary role assignments have can_trade=True."""
        person, _ = person_with_user

        assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[0].id,
            person_id=person.id,
            rotation_template_id=rotation_templates[0].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["upcoming_schedule"]) == 1
        assert data["upcoming_schedule"][0]["role"] == "primary"
        assert data["upcoming_schedule"][0]["can_trade"] is True

    def test_schedule_can_trade_other_roles(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test non-primary roles have can_trade=False."""
        person, _ = person_with_user

        # Create backup and supervising assignments
        backup_assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[0].id,
            person_id=person.id,
            rotation_template_id=rotation_templates[0].id,
            role="backup",
        )

        supervising_assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[1].id,
            person_id=person.id,
            rotation_template_id=rotation_templates[1].id,
            role="supervising",
        )

        db.add(backup_assignment)
        db.add(supervising_assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["upcoming_schedule"]) == 2

        # Find the backup and supervising items
        for item in data["upcoming_schedule"]:
            if item["role"] in ["backup", "supervising"]:
                assert item["can_trade"] is False

    def test_schedule_location_from_template(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test location comes from rotation template."""
        person, _ = person_with_user

        assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[0].id,
            person_id=person.id,
            rotation_template_id=rotation_templates[0].id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["upcoming_schedule"]) == 1
        assert (
            data["upcoming_schedule"][0]["location"]
            == rotation_templates[0].clinic_location
        )

    def test_schedule_no_location(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test schedule item with no location."""
        person, _ = person_with_user

        # Use template with no location
        assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[0].id,
            person_id=person.id,
            rotation_template_id=rotation_templates[
                2
            ].id,  # Admin template with no location
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["upcoming_schedule"]) == 1
        assert data["upcoming_schedule"][0]["location"] is None

    def test_schedule_ordered_by_date_and_time(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test schedule items are ordered by date and time_of_day."""
        person, _ = person_with_user

        # Create assignments in random order
        dates_times = [
            (date.today() + timedelta(days=5), "PM"),
            (date.today() + timedelta(days=3), "AM"),
            (date.today() + timedelta(days=5), "AM"),
            (date.today() + timedelta(days=1), "PM"),
        ]

        for dt, time in dates_times:
            block = [
                b for b in future_blocks if b.date == dt and b.time_of_day == time
            ][0]
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation_templates[0].id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ordering
        schedule = data["upcoming_schedule"]
        for i in range(len(schedule) - 1):
            current_date = date.fromisoformat(schedule[i]["date"])
            next_date = date.fromisoformat(schedule[i + 1]["date"])

            # Either next date is after current, or same date with time ordering
            if current_date == next_date:
                # If same date, AM should come before PM
                if schedule[i]["time_of_day"] == "AM":
                    assert schedule[i + 1]["time_of_day"] == "PM"
            else:
                assert next_date >= current_date


# ============================================================================
# Swap Details
# ============================================================================


class TestDashboardSwapDetails:
    """Tests for swap item details."""

    def test_swap_other_party_when_source(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty: Person,
    ):
        """Test other_party_name shows target when user is source."""
        person, _ = person_with_user

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=person.id,
            target_faculty_id=sample_faculty.id,
            source_week=date.today() + timedelta(days=14),
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["pending_swaps"]) == 1
        assert data["pending_swaps"][0]["other_party_name"] == sample_faculty.name

    def test_swap_other_party_when_target(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty: Person,
    ):
        """Test other_party_name shows source when user is target."""
        person, _ = person_with_user

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty.id,
            target_faculty_id=person.id,
            source_week=date.today() + timedelta(days=14),
            target_week=date.today() + timedelta(days=21),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["pending_swaps"]) == 1
        assert data["pending_swaps"][0]["other_party_name"] == sample_faculty.name

    def test_swap_absorb_type(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty: Person,
    ):
        """Test absorb swap type."""
        person, _ = person_with_user

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=person.id,
            target_faculty_id=sample_faculty.id,
            source_week=date.today() + timedelta(days=14),
            target_week=None,  # Absorb has no target week
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
            requested_at=datetime.utcnow(),
        )
        db.add(swap)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["pending_swaps"]) == 1
        assert data["pending_swaps"][0]["swap_type"] == "absorb"
        assert data["pending_swaps"][0]["target_week"] is None

    def test_swap_only_pending_status(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        sample_faculty: Person,
    ):
        """Test only pending swaps are shown."""
        person, _ = person_with_user

        # Create swaps with different statuses
        statuses = [
            SwapStatus.PENDING,
            SwapStatus.APPROVED,
            SwapStatus.EXECUTED,
            SwapStatus.REJECTED,
        ]

        for i, status in enumerate(statuses):
            swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=person.id,
                target_faculty_id=sample_faculty.id,
                source_week=date.today() + timedelta(days=14 + i * 7),
                target_week=date.today() + timedelta(days=21 + i * 7),
                swap_type=SwapType.ONE_TO_ONE,
                status=status,
                requested_at=datetime.utcnow(),
            )
            db.add(swap)

        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show pending swap
        assert len(data["pending_swaps"]) == 1
        assert data["pending_swaps"][0]["status"] == "pending"


# ============================================================================
# Error Scenarios
# ============================================================================


class TestDashboardErrors:
    """Tests for error scenarios."""

    def test_get_dashboard_no_person_profile(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test dashboard returns 404 when user has no person profile."""
        # Create user without matching person
        user = User(
            id=uuid4(),
            username="noperson",
            email="noperson@example.com",
            hashed_password=get_password_hash("testpass123"),
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Login
        response = client.post(
            "/api/auth/login/json",
            json={"username": "noperson", "password": "testpass123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to get dashboard
        response = client.get(
            "/api/me/dashboard",
            headers=headers,
        )

        assert response.status_code == 404
        assert "person profile" in response.json()["detail"].lower()

    def test_get_dashboard_unauthorized(
        self,
        client: TestClient,
    ):
        """Test dashboard requires authentication."""
        response = client.get("/api/me/dashboard")

        assert response.status_code == 401

    def test_get_dashboard_inactive_user(
        self,
        client: TestClient,
        db: Session,
        person_with_user: tuple[Person, User],
    ):
        """Test dashboard rejects inactive users."""
        person, user = person_with_user

        # Deactivate user
        user.is_active = False
        db.commit()

        # Try to login
        response = client.post(
            "/api/auth/login/json",
            json={"username": "testuser", "password": "testpass123"},
        )

        # Should not be able to login with inactive user
        assert response.status_code in [400, 401]


# ============================================================================
# Faculty User Tests
# ============================================================================


class TestDashboardFaculty:
    """Tests for faculty users."""

    def test_get_dashboard_faculty_user(
        self,
        client: TestClient,
        db: Session,
        faculty_person_with_user: tuple[Person, User],
    ):
        """Test dashboard works for faculty users."""
        person, user = faculty_person_with_user

        # Login as faculty
        response = client.post(
            "/api/auth/login/json",
            json={"username": "facultyuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/me/dashboard",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["user"]["id"] == str(person.id)
        assert data["user"]["role"] == "faculty"
        assert data["user"]["pgy_level"] is None  # Faculty don't have PGY level


# ============================================================================
# Edge Cases
# ============================================================================


class TestDashboardEdgeCases:
    """Tests for edge cases."""

    def test_get_dashboard_empty_results(
        self,
        client: TestClient,
        user_auth_headers: dict,
    ):
        """Test dashboard with no schedule, swaps, or absences."""
        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All lists should be empty but present
        assert data["upcoming_schedule"] == []
        assert data["pending_swaps"] == []
        assert data["absences"] == []
        assert data["summary"]["next_assignment"] is None
        assert data["summary"]["workload_next_4_weeks"] == 0

    def test_get_dashboard_assignment_without_template(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
    ):
        """Test assignment without rotation template."""
        person, _ = person_with_user

        # Create assignment without template
        assignment = Assignment(
            id=uuid4(),
            block_id=future_blocks[0].id,
            person_id=person.id,
            rotation_template_id=None,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        response = client.get(
            "/api/me/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle gracefully
        assert len(data["upcoming_schedule"]) == 1
        assert data["upcoming_schedule"][0]["location"] is None

    def test_get_dashboard_large_dataset(
        self,
        client: TestClient,
        db: Session,
        user_auth_headers: dict,
        person_with_user: tuple[Person, User],
        future_blocks: list[Block],
        rotation_templates: list[RotationTemplate],
    ):
        """Test dashboard with large number of assignments."""
        person, _ = person_with_user

        # Create many assignments
        for block in future_blocks[:100]:  # 100 assignments
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=person.id,
                rotation_template_id=rotation_templates[0].id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        response = client.get(
            "/api/me/dashboard?days_ahead=60",
            headers=user_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle large dataset
        assert len(data["upcoming_schedule"]) > 0
        assert "summary" in data
