"""Comprehensive tests for FacultyPreferenceService."""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.swap import SwapApproval, SwapRecord, SwapStatus, SwapType
from app.services.faculty_preference_service import FacultyPreferenceService


@pytest.fixture
def faculty_preference_service(db: Session) -> FacultyPreferenceService:
    """Create a FacultyPreferenceService instance with test db."""
    return FacultyPreferenceService(db)


@pytest.fixture
def faculty_member(db: Session) -> Person:
    """Create a single faculty member for testing."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="test.faculty@hospital.org",
        performs_procedures=True,
        specialties=["General"],
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@pytest.fixture
def multiple_faculty(db: Session) -> list[Person]:
    """Create multiple faculty members for testing."""
    faculty_list = []
    for i in range(5):
        faculty = Person(
            id=uuid4(),
            name=f"Dr. Faculty {i+1}",
            type="faculty",
            email=f"faculty{i+1}@hospital.org",
            performs_procedures=True,
            specialties=["General"],
        )
        db.add(faculty)
        faculty_list.append(faculty)
    db.commit()
    for f in faculty_list:
        db.refresh(f)
    return faculty_list


@pytest.fixture
def existing_preference(db: Session, faculty_member: Person) -> FacultyPreference:
    """Create an existing preference record for testing."""
    preference = FacultyPreference(
        id=uuid4(),
        faculty_id=faculty_member.id,
        preferred_weeks=["2025-01-06", "2025-01-13"],
        blocked_weeks=["2025-02-03", "2025-02-10"],
        max_weeks_per_month=3,
        max_consecutive_weeks=2,
        min_gap_between_weeks=1,
        target_weeks_per_year=8,
        notify_swap_requests=True,
        notify_schedule_changes=True,
        notify_conflict_alerts=True,
        notify_reminder_days=7,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


class TestGetOrCreatePreferences:
    """Tests for get_or_create_preferences method."""

    def test_get_existing_preferences(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test retrieving existing preferences."""
        result = faculty_preference_service.get_or_create_preferences(faculty_member.id)

        assert result.id == existing_preference.id
        assert result.faculty_id == faculty_member.id
        assert result.max_weeks_per_month == 3
        assert result.preferred_weeks == ["2025-01-06", "2025-01-13"]
        assert result.blocked_weeks == ["2025-02-03", "2025-02-10"]

    def test_create_new_preferences_default_values(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test creating new preferences with default values."""
        result = faculty_preference_service.get_or_create_preferences(faculty_member.id)

        assert result.faculty_id == faculty_member.id
        assert result.preferred_weeks == []
        assert result.blocked_weeks == []
        assert result.max_weeks_per_month == 2
        assert result.max_consecutive_weeks == 1
        assert result.min_gap_between_weeks == 2
        assert result.target_weeks_per_year == 6
        assert result.notify_swap_requests is True
        assert result.notify_schedule_changes is True
        assert result.notify_conflict_alerts is True
        assert result.notify_reminder_days == 7

    def test_create_new_preferences_persists_to_db(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test that newly created preferences are saved to database."""
        result = faculty_preference_service.get_or_create_preferences(faculty_member.id)

        # Verify it's persisted by querying directly
        saved = db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_member.id
        ).first()

        assert saved is not None
        assert saved.id == result.id
        assert saved.faculty_id == faculty_member.id

    def test_create_preferences_for_nonexistent_faculty(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
    ):
        """Test that creating preferences for non-existent faculty raises error."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match=f"Faculty {fake_id} not found"):
            faculty_preference_service.get_or_create_preferences(fake_id)

    def test_create_preferences_for_non_faculty_person(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
    ):
        """Test that creating preferences for non-faculty person raises error."""
        # Create a resident instead of faculty
        resident = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=2,
        )
        db.add(resident)
        db.commit()

        with pytest.raises(ValueError, match=f"Faculty {resident.id} not found"):
            faculty_preference_service.get_or_create_preferences(resident.id)


class TestUpdatePreferences:
    """Tests for update_preferences method."""

    def test_update_preferred_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating preferred weeks."""
        new_weeks = ["2025-03-03", "2025-03-10", "2025-03-17"]

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            preferred_weeks=new_weeks,
        )

        assert result.preferred_weeks == new_weeks
        # Verify other fields unchanged
        assert result.blocked_weeks == existing_preference.blocked_weeks
        assert result.max_weeks_per_month == existing_preference.max_weeks_per_month

    def test_update_blocked_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating blocked weeks."""
        new_weeks = ["2025-04-07", "2025-04-14"]

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            blocked_weeks=new_weeks,
        )

        assert result.blocked_weeks == new_weeks
        # Verify other fields unchanged
        assert result.preferred_weeks == existing_preference.preferred_weeks

    def test_update_max_weeks_per_month(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating max weeks per month."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            max_weeks_per_month=4,
        )

        assert result.max_weeks_per_month == 4

    def test_update_max_consecutive_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating max consecutive weeks."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            max_consecutive_weeks=3,
        )

        assert result.max_consecutive_weeks == 3

    def test_update_min_gap_between_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating minimum gap between weeks."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            min_gap_between_weeks=3,
        )

        assert result.min_gap_between_weeks == 3

    def test_update_notification_preferences(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating notification preferences."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            notify_swap_requests=False,
            notify_schedule_changes=False,
            notify_conflict_alerts=False,
            notify_reminder_days=14,
        )

        assert result.notify_swap_requests is False
        assert result.notify_schedule_changes is False
        assert result.notify_conflict_alerts is False
        assert result.notify_reminder_days == 14

    def test_update_notes(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating notes field."""
        notes_text = "I prefer morning sessions and avoid Fridays when possible."

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            notes=notes_text,
        )

        assert result.notes == notes_text

    def test_update_multiple_fields_simultaneously(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating multiple fields at once."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            preferred_weeks=["2025-05-05"],
            blocked_weeks=["2025-06-02"],
            max_weeks_per_month=5,
            notify_swap_requests=False,
            notes="Updated multiple fields",
        )

        assert result.preferred_weeks == ["2025-05-05"]
        assert result.blocked_weeks == ["2025-06-02"]
        assert result.max_weeks_per_month == 5
        assert result.notify_swap_requests is False
        assert result.notes == "Updated multiple fields"

    def test_update_none_values_do_not_change_fields(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test that passing None doesn't update fields."""
        original_weeks = existing_preference.preferred_weeks.copy()
        original_max = existing_preference.max_weeks_per_month

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            preferred_weeks=None,
            max_weeks_per_month=None,
        )

        assert result.preferred_weeks == original_weeks
        assert result.max_weeks_per_month == original_max

    def test_update_creates_preferences_if_not_exists(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test that update creates preferences if they don't exist."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            max_weeks_per_month=4,
        )

        assert result.faculty_id == faculty_member.id
        assert result.max_weeks_per_month == 4
        # Should have default values for other fields
        assert result.preferred_weeks == []
        assert result.blocked_weeks == []

    def test_update_updates_timestamp(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test that update modifies the updated_at timestamp."""
        original_updated_at = existing_preference.updated_at

        # Wait a tiny bit to ensure timestamp difference
        import time
        time.sleep(0.01)

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            max_weeks_per_month=5,
        )

        assert result.updated_at > original_updated_at


class TestAddPreferredWeek:
    """Tests for add_preferred_week method."""

    def test_add_preferred_week_to_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test adding a preferred week to an empty list."""
        week_date = date(2025, 7, 7)

        result = faculty_preference_service.add_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert result.preferred_weeks == ["2025-07-07"]

    def test_add_preferred_week_to_existing_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding a preferred week to existing list."""
        week_date = date(2025, 7, 14)

        result = faculty_preference_service.add_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-07-14" in result.preferred_weeks
        assert "2025-01-06" in result.preferred_weeks  # Original weeks still there
        assert "2025-01-13" in result.preferred_weeks

    def test_add_duplicate_preferred_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding a week that's already in preferred list."""
        week_date = date(2025, 1, 6)  # Already in list
        original_count = len(existing_preference.preferred_weeks)

        result = faculty_preference_service.add_preferred_week(
            faculty_member.id,
            week_date,
        )

        # Should not duplicate
        assert len(result.preferred_weeks) == original_count
        assert result.preferred_weeks.count("2025-01-06") == 1

    def test_add_preferred_week_removes_from_blocked(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test that adding a preferred week removes it from blocked list."""
        week_date = date(2025, 2, 3)  # In blocked list

        result = faculty_preference_service.add_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-02-03" in result.preferred_weeks
        assert "2025-02-03" not in result.blocked_weeks

    def test_add_preferred_week_handles_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding preferred week when list is None."""
        # Set preferred_weeks to None
        existing_preference.preferred_weeks = None
        db.commit()

        week_date = date(2025, 8, 4)

        result = faculty_preference_service.add_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert result.preferred_weeks == ["2025-08-04"]


class TestAddBlockedWeek:
    """Tests for add_blocked_week method."""

    def test_add_blocked_week_to_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test adding a blocked week to an empty list."""
        week_date = date(2025, 9, 1)

        result = faculty_preference_service.add_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert result.blocked_weeks == ["2025-09-01"]

    def test_add_blocked_week_to_existing_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding a blocked week to existing list."""
        week_date = date(2025, 9, 8)

        result = faculty_preference_service.add_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-09-08" in result.blocked_weeks
        assert "2025-02-03" in result.blocked_weeks  # Original weeks still there
        assert "2025-02-10" in result.blocked_weeks

    def test_add_duplicate_blocked_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding a week that's already in blocked list."""
        week_date = date(2025, 2, 3)  # Already in list
        original_count = len(existing_preference.blocked_weeks)

        result = faculty_preference_service.add_blocked_week(
            faculty_member.id,
            week_date,
        )

        # Should not duplicate
        assert len(result.blocked_weeks) == original_count
        assert result.blocked_weeks.count("2025-02-03") == 1

    def test_add_blocked_week_removes_from_preferred(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test that adding a blocked week removes it from preferred list."""
        week_date = date(2025, 1, 6)  # In preferred list

        result = faculty_preference_service.add_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-01-06" in result.blocked_weeks
        assert "2025-01-06" not in result.preferred_weeks

    def test_add_blocked_week_handles_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test adding blocked week when list is None."""
        # Set blocked_weeks to None
        existing_preference.blocked_weeks = None
        db.commit()

        week_date = date(2025, 10, 6)

        result = faculty_preference_service.add_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert result.blocked_weeks == ["2025-10-06"]


class TestRemovePreferredWeek:
    """Tests for remove_preferred_week method."""

    def test_remove_existing_preferred_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing an existing preferred week."""
        week_date = date(2025, 1, 6)  # In the list

        result = faculty_preference_service.remove_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-01-06" not in result.preferred_weeks
        assert "2025-01-13" in result.preferred_weeks  # Other week still there

    def test_remove_nonexistent_preferred_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing a week that's not in the list."""
        week_date = date(2025, 11, 3)  # Not in list
        original_weeks = existing_preference.preferred_weeks.copy()

        result = faculty_preference_service.remove_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert result.preferred_weeks == original_weeks

    def test_remove_preferred_week_from_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test removing from empty preferred list."""
        # Create preferences with empty list
        faculty_preference_service.get_or_create_preferences(faculty_member.id)

        week_date = date(2025, 11, 10)

        result = faculty_preference_service.remove_preferred_week(
            faculty_member.id,
            week_date,
        )

        assert result.preferred_weeks == []

    def test_remove_preferred_week_from_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing from None preferred list."""
        existing_preference.preferred_weeks = None
        db.commit()

        week_date = date(2025, 11, 17)

        result = faculty_preference_service.remove_preferred_week(
            faculty_member.id,
            week_date,
        )

        # Should not error, just no change
        assert result.preferred_weeks is None


class TestRemoveBlockedWeek:
    """Tests for remove_blocked_week method."""

    def test_remove_existing_blocked_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing an existing blocked week."""
        week_date = date(2025, 2, 3)  # In the list

        result = faculty_preference_service.remove_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert "2025-02-03" not in result.blocked_weeks
        assert "2025-02-10" in result.blocked_weeks  # Other week still there

    def test_remove_nonexistent_blocked_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing a week that's not in the blocked list."""
        week_date = date(2025, 12, 1)  # Not in list
        original_weeks = existing_preference.blocked_weeks.copy()

        result = faculty_preference_service.remove_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert result.blocked_weeks == original_weeks

    def test_remove_blocked_week_from_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test removing from empty blocked list."""
        # Create preferences with empty list
        faculty_preference_service.get_or_create_preferences(faculty_member.id)

        week_date = date(2025, 12, 8)

        result = faculty_preference_service.remove_blocked_week(
            faculty_member.id,
            week_date,
        )

        assert result.blocked_weeks == []

    def test_remove_blocked_week_from_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing from None blocked list."""
        existing_preference.blocked_weeks = None
        db.commit()

        week_date = date(2025, 12, 15)

        result = faculty_preference_service.remove_blocked_week(
            faculty_member.id,
            week_date,
        )

        # Should not error, just no change
        assert result.blocked_weeks is None


class TestIsWeekBlocked:
    """Tests for is_week_blocked method."""

    def test_week_is_blocked(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking a week that is blocked."""
        week_date = date(2025, 2, 3)  # In blocked list

        result = faculty_preference_service.is_week_blocked(
            faculty_member.id,
            week_date,
        )

        assert result is True

    def test_week_is_not_blocked(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking a week that is not blocked."""
        week_date = date(2025, 1, 6)  # Not in blocked list

        result = faculty_preference_service.is_week_blocked(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_blocked_no_preferences(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test checking blocked week when no preferences exist."""
        week_date = date(2025, 3, 3)

        result = faculty_preference_service.is_week_blocked(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_blocked_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking blocked week with empty blocked list."""
        existing_preference.blocked_weeks = []
        db.commit()

        week_date = date(2025, 3, 10)

        result = faculty_preference_service.is_week_blocked(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_blocked_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking blocked week with None blocked list."""
        existing_preference.blocked_weeks = None
        db.commit()

        week_date = date(2025, 3, 17)

        result = faculty_preference_service.is_week_blocked(
            faculty_member.id,
            week_date,
        )

        assert result is False


class TestIsWeekPreferred:
    """Tests for is_week_preferred method."""

    def test_week_is_preferred(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking a week that is preferred."""
        week_date = date(2025, 1, 6)  # In preferred list

        result = faculty_preference_service.is_week_preferred(
            faculty_member.id,
            week_date,
        )

        assert result is True

    def test_week_is_not_preferred(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking a week that is not preferred."""
        week_date = date(2025, 2, 3)  # Not in preferred list

        result = faculty_preference_service.is_week_preferred(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_preferred_no_preferences(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test checking preferred week when no preferences exist."""
        week_date = date(2025, 4, 7)

        result = faculty_preference_service.is_week_preferred(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_preferred_empty_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking preferred week with empty preferred list."""
        existing_preference.preferred_weeks = []
        db.commit()

        week_date = date(2025, 4, 14)

        result = faculty_preference_service.is_week_preferred(
            faculty_member.id,
            week_date,
        )

        assert result is False

    def test_is_week_preferred_none_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test checking preferred week with None preferred list."""
        existing_preference.preferred_weeks = None
        db.commit()

        week_date = date(2025, 4, 21)

        result = faculty_preference_service.is_week_preferred(
            faculty_member.id,
            week_date,
        )

        assert result is False


class TestGetFacultyWithPreferenceForWeek:
    """Tests for get_faculty_with_preference_for_week method."""

    def test_get_faculty_with_preference_for_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty who prefer a specific week."""
        target_week = date(2025, 5, 5)
        target_week_str = target_week.isoformat()

        # Set up preferences for multiple faculty
        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[target_week_str, "2025-05-12"],
            blocked_weeks=[],
        )
        pref2 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[1].id,
            preferred_weeks=["2025-06-02"],  # Different week
            blocked_weeks=[],
        )
        pref3 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[2].id,
            preferred_weeks=[target_week_str, "2025-05-19"],
            blocked_weeks=[],
        )

        db.add_all([pref1, pref2, pref3])
        db.commit()

        result = faculty_preference_service.get_faculty_with_preference_for_week(
            target_week
        )

        assert len(result) == 2
        assert multiple_faculty[0].id in result
        assert multiple_faculty[2].id in result
        assert multiple_faculty[1].id not in result

    def test_get_faculty_with_preference_excludes_specific_faculty(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty with preference while excluding specific IDs."""
        target_week = date(2025, 6, 9)
        target_week_str = target_week.isoformat()

        # All three faculty prefer this week
        for i in range(3):
            pref = FacultyPreference(
                id=uuid4(),
                faculty_id=multiple_faculty[i].id,
                preferred_weeks=[target_week_str],
                blocked_weeks=[],
            )
            db.add(pref)
        db.commit()

        # Exclude first faculty
        result = faculty_preference_service.get_faculty_with_preference_for_week(
            target_week,
            exclude_faculty_ids=[multiple_faculty[0].id],
        )

        assert len(result) == 2
        assert multiple_faculty[0].id not in result
        assert multiple_faculty[1].id in result
        assert multiple_faculty[2].id in result

    def test_get_faculty_with_preference_no_matches(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when none prefer the week."""
        target_week = date(2025, 7, 7)

        # Set up preferences that don't include target week
        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=["2025-08-04", "2025-08-11"],
            blocked_weeks=[],
        )
        db.add(pref1)
        db.commit()

        result = faculty_preference_service.get_faculty_with_preference_for_week(
            target_week
        )

        assert len(result) == 0

    def test_get_faculty_with_preference_empty_preferred_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when they have empty preferred lists."""
        target_week = date(2025, 8, 11)

        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=[],
        )
        db.add(pref1)
        db.commit()

        result = faculty_preference_service.get_faculty_with_preference_for_week(
            target_week
        )

        assert len(result) == 0

    def test_get_faculty_with_preference_none_preferred_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when preferred list is None."""
        target_week = date(2025, 9, 8)

        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=None,
            blocked_weeks=[],
        )
        db.add(pref1)
        db.commit()

        result = faculty_preference_service.get_faculty_with_preference_for_week(
            target_week
        )

        assert len(result) == 0


class TestGetFacultyWithoutBlocksForWeek:
    """Tests for get_faculty_without_blocks_for_week method."""

    def test_get_faculty_without_blocks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty without blocks for a specific week."""
        target_week = date(2025, 10, 6)
        target_week_str = target_week.isoformat()

        # Set up preferences
        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=[target_week_str],  # Blocked
        )
        pref2 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[1].id,
            preferred_weeks=[],
            blocked_weeks=["2025-11-03"],  # Not blocked
        )
        pref3 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[2].id,
            preferred_weeks=[],
            blocked_weeks=[],  # Not blocked
        )

        db.add_all([pref1, pref2, pref3])
        db.commit()

        result = faculty_preference_service.get_faculty_without_blocks_for_week(
            target_week
        )

        assert len(result) == 2
        assert multiple_faculty[0].id not in result
        assert multiple_faculty[1].id in result
        assert multiple_faculty[2].id in result

    def test_get_faculty_without_blocks_excludes_specific_faculty(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding available faculty while excluding specific IDs."""
        target_week = date(2025, 11, 10)

        # All three faculty are available (no blocks)
        for i in range(3):
            pref = FacultyPreference(
                id=uuid4(),
                faculty_id=multiple_faculty[i].id,
                preferred_weeks=[],
                blocked_weeks=[],
            )
            db.add(pref)
        db.commit()

        # Exclude first two faculty
        result = faculty_preference_service.get_faculty_without_blocks_for_week(
            target_week,
            exclude_faculty_ids=[multiple_faculty[0].id, multiple_faculty[1].id],
        )

        assert len(result) == 1
        assert multiple_faculty[0].id not in result
        assert multiple_faculty[1].id not in result
        assert multiple_faculty[2].id in result

    def test_get_faculty_without_blocks_all_blocked(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when all have blocks."""
        target_week = date(2025, 12, 8)
        target_week_str = target_week.isoformat()

        # All faculty block this week
        for i in range(3):
            pref = FacultyPreference(
                id=uuid4(),
                faculty_id=multiple_faculty[i].id,
                preferred_weeks=[],
                blocked_weeks=[target_week_str],
            )
            db.add(pref)
        db.commit()

        result = faculty_preference_service.get_faculty_without_blocks_for_week(
            target_week
        )

        assert len(result) == 0

    def test_get_faculty_without_blocks_none_blocked_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when blocked list is None."""
        target_week = date(2026, 1, 12)

        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=None,  # None means not blocked
        )
        db.add(pref1)
        db.commit()

        result = faculty_preference_service.get_faculty_without_blocks_for_week(
            target_week
        )

        assert len(result) == 1
        assert multiple_faculty[0].id in result

    def test_get_faculty_without_blocks_empty_blocked_list(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding faculty when blocked list is empty."""
        target_week = date(2026, 2, 9)

        pref1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=[],  # Empty means not blocked
        )
        db.add(pref1)
        db.commit()

        result = faculty_preference_service.get_faculty_without_blocks_for_week(
            target_week
        )

        assert len(result) == 1
        assert multiple_faculty[0].id in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_concurrent_updates_to_same_preference(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test handling concurrent updates (basic test)."""
        # Simulate two updates in sequence
        service1 = FacultyPreferenceService(db)
        service2 = FacultyPreferenceService(db)

        result1 = service1.update_preferences(
            faculty_member.id,
            max_weeks_per_month=5,
        )

        result2 = service2.update_preferences(
            faculty_member.id,
            max_weeks_per_month=6,
        )

        # Last update should win
        assert result2.max_weeks_per_month == 6

    def test_add_week_with_special_date_formats(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test adding weeks with various date values."""
        # Test with different dates
        dates_to_test = [
            date(2025, 1, 1),  # New Year
            date(2025, 12, 31),  # Year end
            date(2024, 2, 29),  # Leap year
        ]

        for test_date in dates_to_test:
            result = faculty_preference_service.add_preferred_week(
                faculty_member.id,
                test_date,
            )
            assert test_date.isoformat() in result.preferred_weeks

    def test_remove_all_weeks_from_lists(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test removing all weeks from both lists."""
        # Remove all preferred weeks
        for week_str in existing_preference.preferred_weeks.copy():
            week_date = date.fromisoformat(week_str)
            faculty_preference_service.remove_preferred_week(
                faculty_member.id,
                week_date,
            )

        # Remove all blocked weeks
        for week_str in existing_preference.blocked_weeks.copy():
            week_date = date.fromisoformat(week_str)
            faculty_preference_service.remove_blocked_week(
                faculty_member.id,
                week_date,
            )

        result = faculty_preference_service.get_or_create_preferences(faculty_member.id)
        assert result.preferred_weeks == []
        assert result.blocked_weeks == []

    def test_update_with_empty_lists(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test updating with explicitly empty lists."""
        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            preferred_weeks=[],
            blocked_weeks=[],
        )

        assert result.preferred_weeks == []
        assert result.blocked_weeks == []

    def test_large_number_of_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        faculty_member: Person,
    ):
        """Test handling a large number of preferred weeks."""
        # Add 52 weeks (full year)
        large_week_list = []
        start_date = date(2025, 1, 6)
        for i in range(52):
            week_date = start_date + timedelta(weeks=i)
            large_week_list.append(week_date.isoformat())

        result = faculty_preference_service.update_preferences(
            faculty_member.id,
            preferred_weeks=large_week_list,
        )

        assert len(result.preferred_weeks) == 52

    def test_service_with_different_db_sessions(
        self,
        db: Session,
        faculty_member: Person,
        existing_preference: FacultyPreference,
    ):
        """Test that service works correctly with different session instances."""
        service1 = FacultyPreferenceService(db)
        service2 = FacultyPreferenceService(db)

        # Update using service1
        result1 = service1.update_preferences(
            faculty_member.id,
            max_weeks_per_month=7,
        )

        # Read using service2
        result2 = service2.get_or_create_preferences(faculty_member.id)

        assert result2.max_weeks_per_month == 7


class TestSwapAutoMatching:
    """Tests for swap auto-matching functionality."""

    @pytest.fixture
    def swap_requests(self, db: Session, multiple_faculty: list[Person]) -> list[SwapRecord]:
        """Create multiple swap requests for testing."""
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 6, 2),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 6, 9),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[1].id,
            source_week=date(2025, 6, 9),
            target_faculty_id=multiple_faculty[0].id,
            target_week=date(2025, 6, 2),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap3 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[2].id,
            source_week=date(2025, 6, 16),
            target_faculty_id=multiple_faculty[3].id,
            target_week=date(2025, 6, 23),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add_all([swap1, swap2, swap3])
        db.commit()
        for swap in [swap1, swap2, swap3]:
            db.refresh(swap)
        return [swap1, swap2, swap3]

    def test_find_best_matches_perfect_mutual_match(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        swap_requests: list[SwapRecord],
    ):
        """Test finding a perfect mutual match between two swap requests."""
        # swap1 and swap2 are perfect mutual matches
        matches = faculty_preference_service.find_best_matches(swap_requests[0].id)

        assert len(matches) >= 1
        assert matches[0]["swap_id"] == swap_requests[1].id
        assert matches[0]["compatibility_score"] > 0.5  # Should be high score
        assert "swap_id" in matches[0]
        assert "compatibility_score" in matches[0]
        assert "reason" in matches[0]

    def test_find_best_matches_no_matches(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test finding matches when no viable matches exist."""
        # Create a swap with no matching counterpart
        solo_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 12, 1),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 12, 8),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(solo_swap)
        db.commit()
        db.refresh(solo_swap)

        matches = faculty_preference_service.find_best_matches(solo_swap.id)

        assert len(matches) == 0

    def test_find_best_matches_nonexistent_swap(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
    ):
        """Test finding matches for a non-existent swap request."""
        fake_id = uuid4()

        with pytest.raises(ValueError, match=f"Swap request {fake_id} not found"):
            faculty_preference_service.find_best_matches(fake_id)

    def test_find_best_matches_respects_limit(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test that find_best_matches respects the limit parameter."""
        # Create multiple swap requests
        base_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 7, 7),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 7, 14),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(base_swap)

        # Create several potential matches
        for i in range(5):
            match_swap = SwapRecord(
                id=uuid4(),
                source_faculty_id=multiple_faculty[i % 4 + 1].id,
                source_week=date(2025, 7, 14 + i * 7),
                target_faculty_id=multiple_faculty[0].id,
                target_week=date(2025, 7, 7),
                swap_type=SwapType.ONE_TO_ONE,
                status=SwapStatus.PENDING,
            )
            db.add(match_swap)

        db.commit()
        db.refresh(base_swap)

        matches = faculty_preference_service.find_best_matches(base_swap.id, limit=3)

        assert len(matches) <= 3


class TestCalculateCompatibilityScore:
    """Tests for calculate_compatibility_score method."""

    def test_perfect_match_score(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test score for perfect mutual match."""
        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 8, 4),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 8, 11),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[1].id,
            source_week=date(2025, 8, 11),
            target_faculty_id=multiple_faculty[0].id,
            target_week=date(2025, 8, 4),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = faculty_preference_service.calculate_compatibility_score(swap_a, swap_b)

        # Should be high score due to perfect mutual alignment
        assert 0.5 <= score <= 1.0
        assert isinstance(score, float)

    def test_incompatible_blocked_weeks(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test score when one party has blocked the week they would receive."""
        # Set up blocking preferences
        pref_a = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=["2025-09-08"],  # Blocks the week they would get from swap_b
        )
        db.add(pref_a)
        db.commit()

        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 9, 1),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 9, 8),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[1].id,
            source_week=date(2025, 9, 8),
            target_faculty_id=multiple_faculty[0].id,
            target_week=date(2025, 9, 1),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )

        score = faculty_preference_service.calculate_compatibility_score(swap_a, swap_b)

        # Should be 0 or very low due to blocking constraint
        assert score < 0.3  # Blocking accounts for 30% of score

    def test_score_with_preference_alignment(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test score when preferences align but not perfectly mutual."""
        # Set up preferences
        pref_a = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=["2025-10-06"],  # Wants the week swap_b has
            blocked_weeks=[],
        )
        pref_b = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[1].id,
            preferred_weeks=["2025-09-29"],  # Wants the week swap_a has
            blocked_weeks=[],
        )
        db.add_all([pref_a, pref_b])
        db.commit()

        swap_a = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 9, 29),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 10, 6),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        swap_b = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[1].id,
            source_week=date(2025, 10, 6),
            target_faculty_id=multiple_faculty[0].id,
            target_week=None,  # No specific target, just wants to give up this week
            swap_type=SwapType.ABSORB,
            status=SwapStatus.PENDING,
        )

        score = faculty_preference_service.calculate_compatibility_score(swap_a, swap_b)

        # Should have a reasonable score due to preference alignment
        assert 0.3 <= score <= 1.0


class TestAutoSuggestSwaps:
    """Tests for auto_suggest_swaps method."""

    @pytest.fixture
    def blocks_and_assignments(
        self,
        db: Session,
        multiple_faculty: list[Person],
    ) -> tuple[list[Block], list[Assignment]]:
        """Create blocks and assignments for testing."""
        blocks = []
        assignments = []

        # Create future blocks for next 4 weeks
        for i in range(4):
            block = Block(
                id=uuid4(),
                name=f"Week {i+1}",
                start_date=date.today() + timedelta(weeks=i+1),
                end_date=date.today() + timedelta(weeks=i+1, days=6),
            )
            blocks.append(block)
            db.add(block)

        db.commit()
        for block in blocks:
            db.refresh(block)

        # Create assignments for faculty
        assignment1 = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=multiple_faculty[0].id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=blocks[1].id,
            person_id=multiple_faculty[1].id,
            role="primary",
        )
        assignments.extend([assignment1, assignment2])
        db.add_all(assignments)
        db.commit()
        for assignment in assignments:
            db.refresh(assignment)

        return blocks, assignments

    def test_auto_suggest_swaps_with_blocked_week(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
        blocks_and_assignments: tuple[list[Block], list[Assignment]],
    ):
        """Test auto-suggesting swaps when person has a blocked week."""
        blocks, assignments = blocks_and_assignments

        # Person 0 has blocks[0] but wants to avoid it
        # Person 1 has blocks[1] and person 0 prefers it
        pref_0 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[blocks[1].start_date.isoformat()],
            blocked_weeks=[blocks[0].start_date.isoformat()],
        )
        pref_1 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[1].id,
            preferred_weeks=[blocks[0].start_date.isoformat()],
            blocked_weeks=[],
        )
        db.add_all([pref_0, pref_1])
        db.commit()

        suggestions = faculty_preference_service.auto_suggest_swaps(multiple_faculty[0].id)

        # Should suggest swapping with person 1
        assert len(suggestions) >= 1
        assert "assignment_id" in suggestions[0]
        assert "benefit_score" in suggestions[0]
        assert "reason" in suggestions[0]
        assert suggestions[0]["suggested_partner_id"] == multiple_faculty[1].id

    def test_auto_suggest_swaps_no_suggestions(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
        blocks_and_assignments: tuple[list[Block], list[Assignment]],
    ):
        """Test auto-suggesting swaps when no good suggestions exist."""
        blocks, assignments = blocks_and_assignments

        # Person 0 has no blocks or preferences
        pref_0 = FacultyPreference(
            id=uuid4(),
            faculty_id=multiple_faculty[0].id,
            preferred_weeks=[],
            blocked_weeks=[],
        )
        db.add(pref_0)
        db.commit()

        suggestions = faculty_preference_service.auto_suggest_swaps(multiple_faculty[0].id)

        # Should have no suggestions
        assert len(suggestions) == 0

    def test_auto_suggest_swaps_respects_limit(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
        blocks_and_assignments: tuple[list[Block], list[Assignment]],
    ):
        """Test that auto_suggest_swaps respects the limit parameter."""
        suggestions = faculty_preference_service.auto_suggest_swaps(
            multiple_faculty[0].id,
            limit=2
        )

        assert len(suggestions) <= 2


class TestLearnFromSwapHistory:
    """Tests for learn_from_swap_history method."""

    def test_learn_from_swap_history_with_data(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test learning from swap history with actual data."""
        # Create swap history
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 5, 5),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2025, 5, 12),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
            requested_at=datetime.utcnow() - timedelta(days=30),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 6, 2),
            target_faculty_id=multiple_faculty[2].id,
            target_week=date(2025, 6, 9),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
            requested_at=datetime.utcnow() - timedelta(days=60),
        )
        db.add_all([swap1, swap2])
        db.commit()

        # Create approval records
        approval1 = SwapApproval(
            id=uuid4(),
            swap_id=swap1.id,
            faculty_id=multiple_faculty[0].id,
            role="source",
            approved=True,
            responded_at=datetime.utcnow() - timedelta(days=30),
        )
        approval2 = SwapApproval(
            id=uuid4(),
            swap_id=swap2.id,
            faculty_id=multiple_faculty[0].id,
            role="source",
            approved=True,
            responded_at=datetime.utcnow() - timedelta(days=60),
        )
        db.add_all([approval1, approval2])
        db.commit()

        insights = faculty_preference_service.learn_from_swap_history(multiple_faculty[0].id)

        assert "acceptance_rate" in insights
        assert "commonly_desired_weeks" in insights
        assert "commonly_avoided_weeks" in insights
        assert "preferred_partners" in insights
        assert "rejection_rate" in insights
        assert "total_swaps" in insights
        assert insights["total_swaps"] == 2
        assert insights["acceptance_rate"] == 1.0  # Both approved

    def test_learn_from_swap_history_no_data(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test learning from swap history with no data."""
        insights = faculty_preference_service.learn_from_swap_history(multiple_faculty[0].id)

        assert insights["acceptance_rate"] == 0.5  # Neutral default
        assert insights["commonly_desired_weeks"] == []
        assert insights["commonly_avoided_weeks"] == []
        assert insights["preferred_partners"] == []
        assert insights["rejection_rate"] == 0.5
        assert insights["total_swaps"] == 0

    def test_learn_from_swap_history_with_rejections(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test learning from swap history including rejections."""
        # Create swap history
        swap1 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[1].id,
            source_week=date(2025, 4, 7),
            target_faculty_id=multiple_faculty[0].id,
            target_week=date(2025, 4, 14),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.REJECTED,
            requested_at=datetime.utcnow() - timedelta(days=20),
        )
        swap2 = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2025, 4, 21),
            target_faculty_id=multiple_faculty[2].id,
            target_week=date(2025, 4, 28),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
            requested_at=datetime.utcnow() - timedelta(days=40),
        )
        db.add_all([swap1, swap2])
        db.commit()

        # Create approval records (one rejected, one approved)
        approval1 = SwapApproval(
            id=uuid4(),
            swap_id=swap1.id,
            faculty_id=multiple_faculty[0].id,
            role="target",
            approved=False,  # Rejected
            responded_at=datetime.utcnow() - timedelta(days=20),
        )
        approval2 = SwapApproval(
            id=uuid4(),
            swap_id=swap2.id,
            faculty_id=multiple_faculty[0].id,
            role="source",
            approved=True,
            responded_at=datetime.utcnow() - timedelta(days=40),
        )
        db.add_all([approval1, approval2])
        db.commit()

        insights = faculty_preference_service.learn_from_swap_history(multiple_faculty[0].id)

        assert insights["total_swaps"] == 2
        assert insights["acceptance_rate"] == 0.5  # 1 approved, 1 rejected
        assert insights["rejection_rate"] == 0.5

    def test_learn_from_swap_history_respects_lookback_period(
        self,
        db: Session,
        faculty_preference_service: FacultyPreferenceService,
        multiple_faculty: list[Person],
    ):
        """Test that learning respects the lookback period."""
        # Create old swap (outside lookback period)
        old_swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=multiple_faculty[0].id,
            source_week=date(2024, 1, 1),
            target_faculty_id=multiple_faculty[1].id,
            target_week=date(2024, 1, 8),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
            requested_at=datetime.utcnow() - timedelta(days=400),  # More than 365 days ago
        )
        db.add(old_swap)
        db.commit()

        insights = faculty_preference_service.learn_from_swap_history(
            multiple_faculty[0].id,
            lookback_days=365
        )

        # Should not include the old swap
        assert insights["total_swaps"] == 0
