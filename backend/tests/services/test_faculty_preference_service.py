"""Test suite for faculty preference service."""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.services.faculty_preference_service import FacultyPreferenceService


class TestFacultyPreferenceService:
    """Test suite for faculty preference service."""

    @pytest.fixture
    def pref_service(self, db: Session) -> FacultyPreferenceService:
        """Create a faculty preference service instance."""
        return FacultyPreferenceService(db)

    @pytest.fixture
    def faculty(self, db: Session) -> Person:
        """Create a faculty member."""
        person = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
            performs_procedures=True,
        )
        db.add(person)
        db.commit()
        db.refresh(person)
        return person

    def test_service_initialization(self, db: Session):
        """Test FacultyPreferenceService initialization."""
        service = FacultyPreferenceService(db)

        assert service.db is db

    def test_get_preferences(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting faculty preferences."""
        preferences = pref_service.get_preferences(faculty.id)

        assert isinstance(preferences, (dict, type(None)))

    def test_set_preferences(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting faculty preferences."""
        prefs = {
            "preferred_days": ["Monday", "Wednesday", "Friday"],
            "preferred_times": ["AM"],
            "max_shifts_per_week": 3,
        }

        result = pref_service.set_preferences(faculty.id, prefs)

        assert isinstance(result, bool)

    def test_get_preferred_days(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting preferred days."""
        days = pref_service.get_preferred_days(faculty.id)

        assert isinstance(days, list)

    def test_get_preferred_times(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting preferred times."""
        times = pref_service.get_preferred_times(faculty.id)

        assert isinstance(times, list)

    def test_get_preferred_rotations(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting preferred rotations."""
        rotations = pref_service.get_preferred_rotations(faculty.id)

        assert isinstance(rotations, list)

    def test_set_preferred_days(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting preferred days."""
        result = pref_service.set_preferred_days(
            faculty.id,
            ["Monday", "Tuesday", "Wednesday"],
        )

        assert isinstance(result, bool)

    def test_set_preferred_times(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting preferred times."""
        result = pref_service.set_preferred_times(
            faculty.id,
            ["AM", "PM"],
        )

        assert isinstance(result, bool)

    def test_set_preferred_rotations(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting preferred rotations."""
        result = pref_service.set_preferred_rotations(
            faculty.id,
            ["clinic", "procedure"],
        )

        assert isinstance(result, bool)

    def test_get_availability_window(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting availability window."""
        availability = pref_service.get_availability(faculty.id)

        assert isinstance(availability, (dict, tuple, type(None)))

    def test_set_availability_window(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting availability window."""
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=90)

        result = pref_service.set_availability(faculty.id, start_date, end_date)

        assert isinstance(result, bool)

    def test_get_blackout_dates(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting blackout dates."""
        dates = pref_service.get_blackout_dates(faculty.id)

        assert isinstance(dates, list)

    def test_set_blackout_date(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting a blackout date."""
        blackout_date = date.today() + timedelta(days=60)

        result = pref_service.set_blackout_date(faculty.id, blackout_date)

        assert isinstance(result, bool)

    def test_remove_blackout_date(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test removing a blackout date."""
        blackout_date = date.today() + timedelta(days=60)

        result = pref_service.remove_blackout_date(faculty.id, blackout_date)

        assert isinstance(result, bool)

    def test_get_max_shifts_per_week(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting max shifts per week."""
        max_shifts = pref_service.get_max_shifts(faculty.id)

        assert isinstance(max_shifts, (int, type(None)))

    def test_set_max_shifts_per_week(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test setting max shifts per week."""
        result = pref_service.set_max_shifts(faculty.id, 3)

        assert isinstance(result, bool)

    def test_match_schedule_to_preferences(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test matching schedule to preferences."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        schedule = pref_service.match_schedule(faculty.id, start_date, end_date)

        assert isinstance(schedule, list)

    def test_calculate_preference_satisfaction(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test calculating preference satisfaction score."""
        score = pref_service.get_satisfaction_score(faculty.id)

        assert isinstance(score, (float, int, type(None)))

    def test_get_preference_conflict_count(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting preference conflict count."""
        conflicts = pref_service.get_conflicts(faculty.id)

        assert isinstance(conflicts, int)

    def test_reset_preferences_to_default(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test resetting preferences to default."""
        result = pref_service.reset_to_default(faculty.id)

        assert isinstance(result, bool)

    def test_export_preferences(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test exporting preferences."""
        export_data = pref_service.export(faculty.id)

        assert isinstance(export_data, (dict, str))

    def test_import_preferences(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test importing preferences."""
        import_data = {
            "preferred_days": ["Monday", "Wednesday"],
            "preferred_times": ["AM"],
        }

        result = pref_service.import_data(faculty.id, import_data)

        assert isinstance(result, bool)

    def test_get_preference_change_history(
        self,
        pref_service: FacultyPreferenceService,
        faculty: Person,
    ):
        """Test getting preference change history."""
        history = pref_service.get_history(faculty.id)

        assert isinstance(history, list)
